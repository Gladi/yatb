"""
YATB - Limit-Engine (Paket 3)

Verbrauch wird pro Key-Fingerprint gezählt, also gemeinsam über alle Server mit demselben Key.
Stufe (free/paid), Limit-Schalter und Budget gelten dagegen pro Server-Eintrag.

* Minute (rpm, tpm): gleitendes 60-Sekunden-Fenster im Speicher (übersteht keinen Neustart - unkritisch).
* Tag (rpd, tpd): key_usage-Zeile 'YYYY-MM-DD', Wechsel um 00:00 UTC.
* Monat (chars_month, budget_month): key_usage-Zeile 'YYYY-MM', Wechsel am 1. um 00:00 UTC.
* Warnstufen 90/95/100 % gibt es nur für Monatslimits (Tageslimits würden täglich Meldungen erzeugen).
* Passt eine (lange) Nachricht nicht mehr ins Monatslimit, weicht nur sie aus - kürzere nutzen den Rest weiter.
  Erst wenn weniger als EXHAUSTED_REMAINING (1 %) übrig ist, gilt der Key als erschöpft: Meldung "Limit erreicht"
  (einmal pro Monat) und keine Nutzung mehr - bis zum Monatswechsel oder bis das Limit/Budget erhöht wird.
* Kosten werden nur für Bezahl-Keys berechnet; Gratis-Keys kosten 0.

Ablauf pro Aufruf: check() mit einer Schätzung vor dem Aufruf, record() mit den echten Werten danach.
Parallele Aufrufe können ein Limit minimal überschreiten (Schätzung vs. echte Werte) - bewusst in Kauf genommen.
"""
import datetime
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional, Tuple

import database as db
from providers import Provider

WARN_LEVELS = (("warn_90", 0.90), ("warn_95", 0.95), ("warn_100", 1.0))
EXHAUSTED_REMAINING = 0.01  # weniger Rest als 1 % des Monatslimits = erschöpft


@dataclass
class Usage:
    requests: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    chars: int = 0

    @property
    def tokens(self) -> int:
        return self.tokens_in + self.tokens_out


@dataclass
class MonthlyStatus:
    kind: str                 # "chars" oder "cost"
    used: float
    limit: float

    @property
    def ratio(self) -> float:
        return self.used / self.limit if self.limit else 1.0


def periods(now: Optional[datetime.datetime] = None) -> Tuple[str, str]:
    """(Tag, Monat) in UTC, z. B. ('2026-10-19', '2026-10')."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    now = now.astimezone(datetime.timezone.utc)
    return now.strftime("%Y-%m-%d"), now.strftime("%Y-%m")


# ----------------- Minutenfenster (im Speicher) -----------------
_window: Dict[str, Deque[Tuple[float, int, int]]] = defaultdict(deque)  # fp -> (Zeit, Anfragen, Tokens)


def _minute(fingerprint: str, now: float) -> Tuple[int, int]:
    q = _window[fingerprint]
    while q and now - q[0][0] >= 60.0:
        q.popleft()
    return sum(e[1] for e in q), sum(e[2] for e in q)


def reset_window():
    """Nur für Tests."""
    _window.clear()


# ----------------- Limits -----------------
def monthly_limit(provider: Provider, tier: str, budget: Optional[float]) -> Optional[Tuple[str, float]]:
    """('cost', Budget) für Bezahl-Keys, ('chars', Zeichen) für zeichenbasierte Gratis-Kontingente, sonst None."""
    lim = provider.limits(tier)
    if tier == "paid":
        value = budget if budget is not None else lim.budget_month
        if value is not None:
            return "cost", float(value)
    if lim.chars_month is not None:
        return "chars", float(lim.chars_month)
    return None


def cost_of(provider: Provider, tier: str, usage: Usage) -> float:
    if tier != "paid":
        return 0.0
    return provider.cost(usage.tokens_in, usage.tokens_out, usage.chars)


async def check(key: db.KeyRuntime, provider: Provider, est: Usage, now: Optional[datetime.datetime] = None) -> Optional[str]:
    """
    None = Aufruf erlaubt, sonst der Grund: 'rpm', 'tpm', 'rpd', 'tpd', 'month_exhausted' (Key bis Monatsende
    erschöpft) oder 'chars_month'/'budget_month' (nur diese Anfrage passt nicht mehr - danach on_blocked() aufrufen).
    """
    if not key.limit_enabled:
        return None
    lim = provider.limits(key.tier)
    req_min, tok_min = _minute(key.fingerprint, time.monotonic())
    if lim.rpm is not None and req_min + est.requests > lim.rpm:
        return "rpm"
    if lim.tpm is not None and tok_min + est.tokens > lim.tpm:
        return "tpm"
    day, month = periods(now)
    u_day, u_month = await db.get_key_usage(key.fingerprint, day, month)
    if lim.rpd is not None and u_day.requests + est.requests > lim.rpd:
        return "rpd"
    if lim.tpd is not None and u_day.tokens_in + u_day.tokens_out + est.tokens > lim.tpd:
        return "tpd"
    ml = monthly_limit(provider, key.tier, key.budget)
    if ml is not None:
        kind, value = ml
        used = u_month.chars if kind == "chars" else u_month.cost
        # aus dem AKTUELLEN Limit berechnet (kein Merker): erhöht ein Admin das Budget, ist der Key sofort wieder frei
        if value - used <= value * EXHAUSTED_REMAINING:
            return "month_exhausted"
        if kind == "chars" and used + est.chars > value:
            return "chars_month"
        if kind == "cost" and used + cost_of(provider, key.tier, est) > value:
            return "budget_month"
    return None


async def record(
    key: db.KeyRuntime, provider: Provider, used: Usage, now: Optional[datetime.datetime] = None,
) -> List[str]:
    """Verbucht den echten Verbrauch. Gibt die neu erreichten Warnstufen zurück (jede einmal pro Monat)."""
    if used.requests <= 0 and used.tokens <= 0 and used.chars <= 0:
        return []
    _window[key.fingerprint].append((time.monotonic(), used.requests, used.tokens))
    day, month = periods(now)
    row = await db.add_key_usage(
        key.fingerprint, day, month, used.requests, used.tokens_in, used.tokens_out, used.chars,
        cost_of(provider, key.tier, used),
    )
    ml = monthly_limit(provider, key.tier, key.budget)
    if ml is None:
        return []
    status = MonthlyStatus(ml[0], row.chars if ml[0] == "chars" else row.cost, ml[1])
    done = {"warn_90": row.warn_90, "warn_95": row.warn_95, "warn_100": row.warn_100}
    crossed = [flag for flag, level in WARN_LEVELS if status.ratio >= level and not done[flag]]
    if crossed:
        await db.set_key_usage_flags(key.fingerprint, month, crossed)
    return crossed


async def on_blocked(key: db.KeyRuntime, provider: Provider, reason: str, now: Optional[datetime.datetime] = None) -> List[str]:
    """
    Nach einer Ablehnung: Bei 'month_exhausted' (weniger als 1 % übrig) die fehlenden Warnstufen setzen und
    zurückgeben -> Meldung "Limit erreicht" (einmal pro Monat). Bei 'chars_month'/'budget_month' passte nur diese
    Anfrage nicht mehr; kürzere nutzen den Rest weiter - keine Meldung. Andere Gründe (Minute/Tag) nie melden.
    """
    if reason != "month_exhausted":
        return []
    return await mark_exhausted(key, now)


async def mark_exhausted(key: db.KeyRuntime, now: Optional[datetime.datetime] = None) -> List[str]:
    """
    Das Monatslimit hat einen Aufruf blockiert. Weil check() vorher prüft, erreicht der Zähler die 100 % selbst
    oft nie - deshalb hier die noch fehlenden Warnstufen setzen (einmal pro Monat) und zurückgeben.
    """
    day, month = periods(now)
    _u_day, u_month = await db.get_key_usage(key.fingerprint, day, month)
    done = {"warn_90": u_month.warn_90, "warn_95": u_month.warn_95, "warn_100": u_month.warn_100}
    crossed = [flag for flag, _level in WARN_LEVELS if not done[flag]]
    if crossed:
        await db.set_key_usage_flags(key.fingerprint, month, crossed)
    return crossed


async def monthly_status(
    fingerprint: str, provider: Provider, tier: str, budget: Optional[float], now: Optional[datetime.datetime] = None,
) -> Tuple[db.UsageRow, db.UsageRow, Optional[MonthlyStatus]]:
    """(heute, Monat, Monatslimit-Status oder None) für Anzeigen."""
    day, month = periods(now)
    u_day, u_month = await db.get_key_usage(fingerprint, day, month)
    ml = monthly_limit(provider, tier, budget)
    if ml is None:
        return u_day, u_month, None
    return u_day, u_month, MonthlyStatus(ml[0], u_month.chars if ml[0] == "chars" else u_month.cost, ml[1])
