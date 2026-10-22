"""
YATB - Übersetzungskette pro Server und Zielsprache

Reihenfolge: KI-Keys des Servers (Qualitätsgruppe A vor B, innerhalb einer Gruppe Gratis- vor Bezahl-Key, dann in
Hinterlegungsreihenfolge) -> Google -> Azure (je falls der Server einen Key hat) -> LibreTranslate (lokal) -> Original
mit Tag [Raw]. Ein Request pro Discord-Feld (Nachricht, Embed-Beschreibung, ...) und Zielsprache, kein Aufteilen.

Jede Antwort wird geprüft (Platzhalter vollständig, validator.problems); fällt sie durch, geht das Feld an die
nächste Stufe. Übersprungen wird eine Stufe, wenn der Anbieter abgeschaltet ist, ihr Circuit-Breaker offen ist,
ihr Limit erreicht ist oder das Zeitbudget der Kette (CHAIN_BUDGET) aufgebraucht ist (dann nur noch Libre).

Verbrauch (limits.py) und Statistik (stats.py) werden hier verbucht. Was der Bot melden soll (Warnstufen,
abgelehnter Key, Modell nicht gefunden), steht in TranslationResult.notices.
"""
import asyncio
import datetime
import logging
import os
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

import aiohttp

import database as db
import limits
import markup
import providers
import stats
import translator as tr
import validator

log = logging.getLogger("yatb.chain")

CHAIN_BUDGET = float(os.getenv("CHAIN_BUDGET", "30"))   # Sekunden für alle bezahlten/KI-Stufen zusammen
AI_CONCURRENCY_PER_KEY = 4
CACHE_MAX, CACHE_TEXT_LEN = 1000, 300
PROMPT_OVERHEAD_TOKENS = (len(tr.AI_SYSTEM) + sum(len(u) + len(r) for u, r in tr.AI_EXAMPLES)) // 3 + 120
TAGS = {"ai": "[AI]", "google": "[Google]", "azure": "[Azure]", "libre": "[Libre]"}
MODELS = {"google": "translate-v2", "azure": "translator-v3", "libre": "libretranslate"}


@dataclass
class Notice:
    kind: str                         # "usage", "key_rejected", "model_missing", "provider_quota"
    provider: providers.Provider
    key: Optional[db.KeyRuntime]
    crossed: List[str] = field(default_factory=list)
    status: str = ""


@dataclass
class TranslationResult:
    texts: List[str]
    engines: List[str]
    notices: List[Notice] = field(default_factory=list)

    @property
    def main_engine(self) -> str:
        """Engine-Tag für den Anzeigenamen (erste echte Engine, sonst [Direct])."""
        for tag in self.engines:
            if tag != "[Direct]":
                return tag
        return "[Direct]"


@dataclass
class Spec:
    kind: str                                  # "ai", "google", "azure", "libre"
    provider: Optional[providers.Provider]
    key: Optional[db.KeyRuntime]

    @property
    def id(self) -> str:
        return self.provider.id if self.provider else "libre"

    @property
    def tag(self) -> str:
        return TAGS[self.kind]

    @property
    def model(self) -> str:
        return self.provider.model if self.kind == "ai" else MODELS[self.kind]


# ----------------- Circuit-Breaker pro Anbieter und Key -----------------
class Breaker:
    def __init__(self, threshold: int = 3, cooldown: float = 60.0):
        self.threshold, self.cooldown = threshold, cooldown
        self.failures, self.open_until = 0, 0.0

    def allow(self) -> bool:
        return time.monotonic() >= self.open_until

    def success(self):
        self.failures = 0

    def failure(self):
        self.failures += 1
        if self.failures >= self.threshold:
            self.open_until = time.monotonic() + self.cooldown
            self.failures = 0

    def trip(self, seconds: float):
        self.open_until = max(self.open_until, time.monotonic() + seconds)


_breakers: Dict[Tuple[str, str], Breaker] = {}


def breaker(spec: Spec) -> Breaker:
    k = (spec.id, spec.key.fingerprint if spec.key else "")
    if k not in _breakers:
        _breakers[k] = Breaker()
    return _breakers[k]


def _seconds_to_utc_midnight() -> float:
    now = datetime.datetime.now(datetime.timezone.utc)
    tomorrow = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return (tomorrow - now).total_seconds()


def _on_failure(spec: Spec, call: tr.Call, notices: List[Notice]):
    """Fehlerklasse -> Pause der Stufe (und ggf. Meldung an die Admins)."""
    b, oc = breaker(spec), call.outcome
    if oc == "rate_limited":
        b.trip(min(call.retry_after or 30.0, 600.0))
    elif oc == "auth":
        b.trip(3600)
        if spec.provider:
            notices.append(Notice("key_rejected", spec.provider, spec.key, status=str(call.http_status or "")))
    elif oc == "model_not_found":
        b.trip(6 * 3600)
        if spec.provider:
            notices.append(Notice("model_missing", spec.provider, spec.key))
    elif oc == "quota":
        b.trip(_seconds_to_utc_midnight())
        if spec.provider:
            notices.append(Notice("provider_quota", spec.provider, spec.key))
    elif oc != "validator_rejected":
        b.failure()


# ----------------- Kette aufbauen -----------------
def build_chain(guild_id: int, local_only: bool = False) -> List[Spec]:
    """local_only: Nutzer-Opt-out "nur lokal" - nichts an Dritte, nur Libre."""
    if local_only:
        return [Spec("libre", None, None)]
    ai: List[Spec] = []
    google = azure = None
    for key in db.get_guild_keys(guild_id):
        p = providers.PROVIDERS.get(key.provider)
        if p is None or not p.enabled:
            continue
        if p.kind == "openai":
            if key.tier == "free" and not p.eea_free_allowed:
                continue  # z. B. Gemini Free: im EWR nicht zulässig
            ai.append(Spec("ai", p, key))
        elif p.kind == "google" and google is None:
            google = Spec("google", p, key)
        elif p.kind == "azure" and azure is None:
            azure = Spec("azure", p, key)
    ai.sort(key=lambda s: (s.provider.group, s.key.tier != "free", s.key.key_id))
    stages = ai + [s for s in (google, azure) if s]
    order = db.get_engine_order(guild_id)
    if order:  # eigene Reihenfolge (Dashboard); nicht genannte Stufen behalten ihre Standardfolge dahinter
        pos = {key_id: i for i, key_id in enumerate(order)}
        stages.sort(key=lambda s: pos.get(s.key.key_id, len(pos)))
    return stages + [Spec("libre", None, None)]


# ----------------- Statistik -----------------
def _record_stat(guild_id: int, spec: Spec, call: tr.Call, source: str, target: str, outcome: str,
                 fell_through: bool, detail: str = ""):
    cost = 0.0
    if spec.key is not None and spec.provider is not None:
        cost = limits.cost_of(spec.provider, spec.key.tier,
                              limits.Usage(tokens_in=call.tokens_in, tokens_out=call.tokens_out,
                                           chars=call.chars if spec.kind != "ai" else 0))
    stats.record(
        guild_id=guild_id, provider=spec.id, model=spec.model, outcome=outcome, src_lang=source, tgt_lang=target,
        chars=call.chars, tokens_in=call.tokens_in, tokens_out=call.tokens_out, duration_ms=call.duration_ms,
        http_status=call.http_status, fell_through=fell_through, cost=cost,
        key_fp=spec.key.fingerprint if spec.key else None, detail=detail,
    )


async def _limit_ok(guild_id: int, spec: Spec, est: limits.Usage, notices: List[Notice]) -> bool:
    if spec.key is None:
        return True
    reason = await limits.check(spec.key, spec.provider, est)
    if reason is None:
        return True
    stats.record(guild_id=guild_id, provider=spec.id, model=spec.model, outcome="limit", chars=est.chars,
                 tokens_in=est.tokens_in, fell_through=True, key_fp=spec.key.fingerprint, detail=reason)
    crossed = await limits.on_blocked(spec.key, spec.provider, reason)
    if crossed:
        notices.append(Notice("usage", spec.provider, spec.key, crossed))
    return False


async def _account(spec: Spec, used: limits.Usage, notices: List[Notice]):
    if spec.key is None or (used.requests <= 0 and used.tokens <= 0 and used.chars <= 0):
        return
    crossed = await limits.record(spec.key, spec.provider, used)
    if crossed:
        notices.append(Notice("usage", spec.provider, spec.key, crossed))


# ----------------- Stufen -----------------
_key_sems: Dict[str, asyncio.Semaphore] = {}


# Ablehnungsgründe, bei denen sich ein zweiter Versuch mit Hinweis lohnt (reine Formatierung, Text war brauchbar)
RETRY_REASONS = {"bold", "italic", "underline", "strike", "spoiler", "headers", "quotes", "lists", "numbered", "subtext",
                 "paragraphs", "links"}
_HINT_NAMES = {"bold": "bold **", "italic": "italic * or _", "underline": "underline __", "strike": "strikethrough ~~",
               "spoiler": "spoiler ||", "headers": "headings (#)", "quotes": "quote lines (>)", "lists": "list items (-)",
               "numbered": "numbered items", "subtext": "subtext lines (-#)", "paragraphs": "blank lines between paragraphs",
               "links": "links [text](...)"}


def retry_hint(reasons) -> str:
    names = ", ".join(_HINT_NAMES[r] for r in reasons if r in _HINT_NAMES)
    return ("IMPORTANT: A previous translation of this message lost or changed formatting (" + names + "). "
            "Translate again and keep exactly the same Markdown markers in the same places as in the original: "
            "every line keeps its prefix (>, #, -, numbering), every ** * __ ~~ || pair stays around the matching "
            "translated words, no line is added or dropped.")


def _est_tokens(text: str) -> int:
    return max(1, len(text) // 3)


async def _run_ai(session, guild_id: int, spec: Spec, segments: Sequence[str], preps: Dict[int, markup.Prepared],
                  pending: List[int], source: str, target: str, context, result: TranslationResult,
                  deadline: float) -> Set[int]:
    sem = _key_sems.setdefault(spec.key.fingerprint, asyncio.Semaphore(AI_CONCURRENCY_PER_KEY))
    ctx_tokens = sum(len(c) for c in (context or [])[-tr.AI_CONTEXT_LINES:]) // 3

    async def one(i: int) -> bool:
        prep = preps[i]
        if not breaker(spec).allow() or time.monotonic() >= deadline:
            return False
        tin = _est_tokens(prep.masked)
        est = limits.Usage(requests=1, tokens_in=tin + PROMPT_OVERHEAD_TOKENS + ctx_tokens, tokens_out=int(tin * 1.3) + 10)
        if not await _limit_ok(guild_id, spec, est, result.notices):
            return False
        async with sem:
            timeout = max(2.0, min(tr.AI_TIMEOUT, deadline - time.monotonic()))
            out, call = await tr.ai_translate(session, spec.provider, spec.key.secret, prep.masked, source, target,
                                              context, timeout)
        await _account(spec, limits.Usage(requests=1, tokens_in=call.tokens_in, tokens_out=call.tokens_out), result.notices)
        if out is None:
            _on_failure(spec, call, result.notices)
            _record_stat(guild_id, spec, call, source, target, call.outcome, True)
            return False
        breaker(spec).success()
        text, ok = markup.restore(markup.repair_structure(prep.masked, out, prep)[0], prep)
        reasons = ([] if ok else ["placeholders"]) + validator.problems(segments[i], text, ai=True)
        retry = bool(reasons) and set(reasons) <= RETRY_REASONS and deadline - time.monotonic() > 5
        _record_stat(guild_id, spec, call, source, target, "validator_rejected" if reasons else "ok",
                     bool(reasons) and not retry, ",".join(reasons) + (";retry" if retry else ""))
        if retry:  # nur Formatierung verloren: einmal mit konkretem Hinweis nachfragen, bevor die nächste Stufe dran ist
            if not await _limit_ok(guild_id, spec, est, result.notices):
                return False
            async with sem:
                timeout = max(2.0, min(tr.AI_TIMEOUT, deadline - time.monotonic()))
                out, call = await tr.ai_translate(session, spec.provider, spec.key.secret, prep.masked, source, target,
                                                  context, timeout, hint=retry_hint(reasons))
            await _account(spec, limits.Usage(requests=1, tokens_in=call.tokens_in, tokens_out=call.tokens_out),
                           result.notices)
            if out is None:
                _on_failure(spec, call, result.notices)
                _record_stat(guild_id, spec, call, source, target, call.outcome, True, "retry")
                return False
            text, ok = markup.restore(markup.repair_structure(prep.masked, out, prep)[0], prep)
            reasons = ([] if ok else ["placeholders"]) + validator.problems(segments[i], text, ai=True)
            _record_stat(guild_id, spec, call, source, target, "validator_rejected" if reasons else "ok",
                         bool(reasons), "retry:" + ",".join(reasons) if reasons else "retry")
        if reasons:
            return False
        result.texts[i], result.engines[i] = text, spec.tag
        return True

    done = await asyncio.gather(*(one(i) for i in pending))
    return {i for i, ok in zip(pending, done) if ok}


async def _call_batch(session, spec: Spec, lines: List[str], source: str, target: str, fmt: str):
    if spec.kind == "google":
        return await tr.google_translate(session, spec.key.secret, lines, source, target, fmt)
    if spec.kind == "azure":
        return await tr.azure_translate(session, spec.key.secret, spec.key.region, lines, source, target, fmt)
    return await tr.libre_translate(session, lines, source, target, fmt)


async def _run_batch(session, guild_id: int, spec: Spec, segments: Sequence[str], preps: Dict[int, markup.Prepared],
                     pending: List[int], source: str, target: str, result: TranslationResult,
                     fmt: str = "html") -> Set[int]:
    """Google/Azure/Libre: alle offenen Felder zeilenweise in einem Aufruf (Layout bleibt über die Zeilen erhalten)."""
    if not breaker(spec).allow():
        return set()
    parts = {i: tr.extract_line_structure(preps[i].masked) for i in pending}
    lines = [line for i in pending for line in parts[i][0]]
    if not lines:
        return set()
    if fmt == "html":
        send = [markup.md_to_html(line, markup.link_tokens(preps[i])) for i in pending for line in parts[i][0]]
    else:
        send = lines
    est = limits.Usage(requests=1, chars=sum(len(x) for x in send))
    if not await _limit_ok(guild_id, spec, est, result.notices):
        return set()
    out, call = await _call_batch(session, spec, send, source, target, fmt)
    await _account(spec, limits.Usage(requests=call.requests, chars=call.chars if out is not None else 0), result.notices)
    if out is None:
        _on_failure(spec, call, result.notices)
        _record_stat(guild_id, spec, call, source, target, call.outcome, True)
        return set()
    breaker(spec).success()
    done: Set[int] = set()
    reasons_all: List[str] = []
    pos = 0
    strict = spec.kind != "libre"
    for i in pending:
        n = len(parts[i][0])
        translated = out[pos:pos + n]
        pos += n
        if fmt == "html":
            translated = [markup.html_to_md(x) for x in translated]
        text, ok = markup.restore(tr.reconstruct_line_structure(translated, parts[i][1]), preps[i])
        reasons = ([] if ok else ["placeholders"]) + validator.problems(segments[i], text, strict=strict)
        if reasons:
            reasons_all.extend(reasons)
            continue
        result.texts[i], result.engines[i] = text, spec.tag
        done.add(i)
    rejected = len(pending) - len(done)
    outcome = "validator_rejected" if rejected == len(pending) else "ok"
    _record_stat(guild_id, spec, call, source, target, outcome, bool(rejected), ",".join(sorted(set(reasons_all))))
    return done


# ----------------- Cache (pro Server, nur ohne KI-Kontext) -----------------
_cache: "OrderedDict[Tuple[int, str, str, str], Tuple[str, str]]" = OrderedDict()


def _cache_get(key):
    hit = _cache.get(key)
    if hit is not None:
        _cache.move_to_end(key)
    return hit


def _cache_put(key, value):
    _cache[key] = value
    _cache.move_to_end(key)
    while len(_cache) > CACHE_MAX:
        _cache.popitem(last=False)


# ----------------- Einstieg -----------------
async def translate(
    session: aiohttp.ClientSession, guild_id: int, segments: Sequence[str], source: str, target: str,
    context: Optional[Sequence[str]] = None, local_only: bool = False,
) -> TranslationResult:
    """Übersetzt mehrere unabhängige Felder einer Nachricht in eine Zielsprache. Reihenfolge bleibt erhalten."""
    result = TranslationResult(texts=list(segments), engines=["[Direct]"] * len(segments))
    if source == target:
        return result
    preps: Dict[int, markup.Prepared] = {}
    for i, text in enumerate(segments):
        if not text or not text.strip():
            continue
        ck = (guild_id, text, source, target)
        if len(text) <= CACHE_TEXT_LEN and not local_only and (hit := _cache_get(ck)):
            result.texts[i], result.engines[i] = hit
            continue
        prep = markup.prepare(text)
        if prep.has_text():
            preps[i] = prep
    pending = sorted(preps)
    deadline = time.monotonic() + CHAIN_BUDGET
    for spec in build_chain(guild_id, local_only):
        if not pending:
            break
        if spec.kind != "libre" and time.monotonic() >= deadline:
            continue  # Zeitbudget aufgebraucht: nur noch die lokale Stufe
        try:
            if spec.kind == "ai":
                done = await _run_ai(session, guild_id, spec, segments, preps, pending, source, target, context,
                                     result, deadline)
            else:
                done = await _run_batch(session, guild_id, spec, segments, preps, pending, source, target, result)
                if spec.kind == "libre" and len(done) < len(pending):  # HTML-Modus gescheitert -> Libre als Text
                    rest = [i for i in pending if i not in done]
                    done |= await _run_batch(session, guild_id, spec, segments, preps, rest, source, target, result,
                                             fmt="text")
        except Exception as exc:  # eine kaputte Stufe darf die Kette nie abbrechen
            log.error("Stufe %s fehlgeschlagen: %s", spec.id, type(exc).__name__)
            done = set()
        pending = [i for i in pending if i not in done]
    for i in pending:
        result.texts[i], result.engines[i] = segments[i], "[Raw]"
    for i in preps:
        if result.engines[i] in ("[Google]", "[Azure]", "[Libre]") and len(segments[i]) <= CACHE_TEXT_LEN and not local_only:
            _cache_put((guild_id, segments[i], source, target), (result.texts[i], result.engines[i]))
    return result
