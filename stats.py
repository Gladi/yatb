"""
YATB - Aufruf-Statistik (stats.db, Paket 3)

Eigene Datei, getrennt von der Daten-DB mit den verschlüsselten Keys: Das spätere Dashboard bekommt nur
diesen Ordner (schreibgeschützt). Gespeichert werden nur Metadaten - KEIN Nachrichtentext, keine Nutzer.

* calls: ein Eintrag pro Engine-Aufruf (Zeit, Server, Anbieter/Modell, Sprachpaar, Zeichen/Tokens, Dauer,
  Ergebnisklasse, HTTP-Status, ging weiter an nächste Stufe, Kostenschätzung, Key-Fingerprint gekürzt).
  Aufbewahrung RAW_KEEP_DAYS Tage.
* daily: Tageswerte pro Server/Anbieter/Modell (dauerhaft), werden aus calls gebildet, bevor diese verfallen.

Geschrieben wird gesammelt im Hintergrund (alle FLUSH_SECONDS), damit SQLite den Bot nie ausbremst.
"""
import asyncio
import contextlib
import datetime
import json
import logging
import math
import os
import sqlite3
import time
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

log = logging.getLogger("yatb.stats")

STATS_DIR = os.getenv("YATB_STATS_DIR") or (
    "/app/stats" if os.path.isdir("/app/stats") else os.path.join(os.path.dirname(os.path.abspath(__file__)), "stats")
)
RAW_KEEP_DAYS = 90
FLUSH_SECONDS = 5.0
FP_PREFIX = 16  # gekürzter Key-Fingerprint (reicht zum Zusammenzählen, nicht umkehrbar)

OUTCOMES = {
    "ok", "rate_limited", "quota", "timeout", "server_error", "auth", "bad_request", "model_not_found",
    "network", "bad_response", "empty", "validator_rejected", "error",
    "limit",  # kein Aufruf: eigenes Limit (Minute/Tag/Monat) hat die Anfrage zur nächsten Engine geschickt
}

_COLUMNS = (
    "ts", "day", "guild_id", "provider", "model", "src_lang", "tgt_lang", "chars", "tokens_in", "tokens_out",
    "duration_ms", "outcome", "http_status", "fell_through", "cost", "key_fp", "detail",
)
_pending: List[Tuple[Any, ...]] = []
_task: Optional[asyncio.Task] = None
_ready = False


def stats_file() -> str:
    return os.path.join(STATS_DIR, "stats.db")


@contextlib.contextmanager
def _conn():
    conn = sqlite3.connect(stats_file(), timeout=10.0)
    try:
        conn.execute("PRAGMA busy_timeout=10000;")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init():
    """Legt Ordner und Tabellen an (idempotent)."""
    global _ready
    os.makedirs(STATS_DIR, exist_ok=True)
    with _conn() as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                day TEXT NOT NULL,
                guild_id INTEGER,
                provider TEXT NOT NULL,
                model TEXT,
                src_lang TEXT,
                tgt_lang TEXT,
                chars INTEGER NOT NULL DEFAULT 0,
                tokens_in INTEGER NOT NULL DEFAULT 0,
                tokens_out INTEGER NOT NULL DEFAULT 0,
                duration_ms INTEGER NOT NULL DEFAULT 0,
                outcome TEXT NOT NULL,
                http_status INTEGER,
                fell_through INTEGER NOT NULL DEFAULT 0,
                cost REAL NOT NULL DEFAULT 0,
                key_fp TEXT
            )
        """)
        if "detail" not in {r[1] for r in conn.execute("PRAGMA table_info(calls)")}:
            conn.execute("ALTER TABLE calls ADD COLUMN detail TEXT")  # Grund, z. B. Prüfregel oder Limit
        conn.execute("CREATE INDEX IF NOT EXISTS idx_calls_day ON calls (day);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_calls_guild_day ON calls (guild_id, day);")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily (
                day TEXT NOT NULL,
                guild_id INTEGER NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                calls INTEGER NOT NULL,
                ok INTEGER NOT NULL,
                fell_through INTEGER NOT NULL,
                outcomes TEXT NOT NULL,          -- JSON {Ergebnisklasse: Anzahl}
                chars INTEGER NOT NULL,
                tokens_in INTEGER NOT NULL,
                tokens_out INTEGER NOT NULL,
                cost REAL NOT NULL,
                p50_ms INTEGER,                  -- Latenz nur erfolgreicher Aufrufe
                p95_ms INTEGER,
                PRIMARY KEY (day, guild_id, provider, model)
            )
        """)
    _ready = True


def record(
    *, guild_id: Optional[int], provider: str, model: Optional[str], outcome: str, src_lang: Optional[str] = None,
    tgt_lang: Optional[str] = None, chars: int = 0, tokens_in: int = 0, tokens_out: int = 0, duration_ms: int = 0,
    http_status: Optional[int] = None, fell_through: bool = False, cost: float = 0.0, key_fp: Optional[str] = None,
    ts: Optional[float] = None, detail: Optional[str] = None,
):
    """Merkt einen Aufruf vor (wird beim nächsten flush() geschrieben). Kein Text, nur Zahlen/Kennungen."""
    if outcome not in OUTCOMES:
        outcome = "error"
    ts = time.time() if ts is None else ts
    day = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d")
    _pending.append((
        ts, day, guild_id, provider, model or "", src_lang, tgt_lang, int(chars), int(tokens_in), int(tokens_out),
        int(duration_ms), outcome, http_status, int(bool(fell_through)), float(cost), (key_fp or "")[:FP_PREFIX] or None,
        (detail or "")[:200] or None,
    ))


def _write(rows: Sequence[Tuple[Any, ...]]):
    if not _ready:
        init()
    with _conn() as conn:
        conn.executemany(
            f"INSERT INTO calls ({', '.join(_COLUMNS)}) VALUES ({', '.join('?' * len(_COLUMNS))})", rows
        )


async def flush():
    if not _pending:
        return
    rows = _pending[:]
    del _pending[:len(rows)]
    try:
        await asyncio.to_thread(_write, rows)
    except Exception as exc:  # Statistik darf den Bot nie stören
        log.warning("Statistik konnte nicht geschrieben werden (%d Einträge verworfen): %s", len(rows), type(exc).__name__)


async def _loop():
    while True:
        await asyncio.sleep(FLUSH_SECONDS)
        await flush()


def start():
    global _task
    try:
        init()
    except Exception as exc:
        log.error("Statistik-DB %s nicht nutzbar: %s", stats_file(), exc)
    if _task is None or _task.done():
        _task = asyncio.create_task(_loop())


async def stop():
    if _task is not None:
        _task.cancel()
    await flush()


# ----------------- Tageswerte und Aufbewahrung -----------------
def _percentile(values: List[int], p: float) -> Optional[int]:
    if not values:
        return None
    values = sorted(values)
    rank = max(1, math.ceil(p * len(values)))  # Nearest-Rank-Methode
    return values[rank - 1]


def aggregate(today: Optional[str] = None, keep_days: int = RAW_KEEP_DAYS) -> Tuple[int, int]:
    """Bildet Tageswerte für abgeschlossene Tage (vor heute, UTC) und löscht Rohdaten älter als keep_days.
    Gibt (neue Tageszeilen, gelöschte Rohzeilen) zurück. Idempotent."""
    if not _ready:
        init()
    today = today or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    cutoff = (datetime.date.fromisoformat(today) - datetime.timedelta(days=keep_days)).isoformat()
    added = 0
    with _conn() as conn:
        days = [r[0] for r in conn.execute("""
            SELECT DISTINCT c.day FROM calls c
            WHERE c.day < ? AND NOT EXISTS (SELECT 1 FROM daily d WHERE d.day = c.day)
        """, (today,))]
        for day in days:
            groups: Dict[Tuple, Dict[str, Any]] = defaultdict(lambda: {
                "calls": 0, "ok": 0, "fell": 0, "outcomes": Counter(), "chars": 0, "tin": 0, "tout": 0, "cost": 0.0, "ms": [],
            })
            for gid, prov, model, outcome, fell, chars, tin, tout, cost, ms in conn.execute("""
                SELECT COALESCE(guild_id, 0), provider, model, outcome, fell_through, chars, tokens_in, tokens_out, cost, duration_ms
                FROM calls WHERE day = ?
            """, (day,)):
                g = groups[(gid, prov, model)]
                g["calls"] += 1
                g["ok"] += outcome == "ok"
                g["fell"] += fell
                g["outcomes"][outcome] += 1
                g["chars"] += chars
                g["tin"] += tin
                g["tout"] += tout
                g["cost"] += cost
                if outcome == "ok":
                    g["ms"].append(ms)
            for (gid, prov, model), g in groups.items():
                conn.execute("""
                    INSERT OR IGNORE INTO daily (day, guild_id, provider, model, calls, ok, fell_through, outcomes,
                                                 chars, tokens_in, tokens_out, cost, p50_ms, p95_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (day, gid, prov, model, g["calls"], g["ok"], g["fell"], json.dumps(dict(g["outcomes"]), sort_keys=True),
                      g["chars"], g["tin"], g["tout"], round(g["cost"], 6),
                      _percentile(g["ms"], 0.50), _percentile(g["ms"], 0.95)))
                added += 1
        deleted = conn.execute("DELETE FROM calls WHERE day < ?", (cutoff,)).rowcount
    return added, deleted


# ----------------- Auswertung fürs Dashboard -----------------
def guild_report(guild_id: int, days: int, today: Optional[str] = None) -> Dict[str, Any]:
    """
    Kennzahlen eines Servers für die letzten `days` Tage (inkl. heute, UTC) aus den Rohdaten (max. RAW_KEEP_DAYS).
    "limit" ist kein echter Aufruf (eigenes Limit hat weitergeschickt) und zählt deshalb nicht als Fehler.
    Strukturquote = Antworten, die die Prüfung (Erwähnungen, Links, Formatierung) bestanden, / alle Antworten.
    """
    if not _ready:
        init()
    days = max(1, min(int(days), RAW_KEEP_DAYS))
    end = datetime.date.fromisoformat(today) if today else datetime.datetime.now(datetime.timezone.utc).date()
    day_list = [(end - datetime.timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]
    per: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "calls": 0, "ok": 0, "fell_through": 0, "limit_skips": 0, "outcomes": Counter(), "chars": 0,
        "tokens_in": 0, "tokens_out": 0, "cost": 0.0, "ms": [], "per_day": Counter(),
    })
    with _conn() as conn:
        rows = conn.execute("""
            SELECT day, provider, outcome, fell_through, chars, tokens_in, tokens_out, cost, duration_ms
            FROM calls WHERE guild_id = ? AND day >= ? AND day <= ?
        """, (guild_id, day_list[0], day_list[-1])).fetchall()
    for day, prov, outcome, fell, chars, tin, tout, cost, ms in rows:
        p = per[prov]
        if outcome == "limit":
            p["limit_skips"] += 1
            continue
        p["calls"] += 1
        p["per_day"][day] += 1
        p["ok"] += outcome == "ok"
        p["fell_through"] += fell
        p["outcomes"][outcome] += 1
        p["chars"] += chars
        p["tokens_in"] += tin
        p["tokens_out"] += tout
        p["cost"] += cost
        if outcome == "ok":
            p["ms"].append(ms)
    providers = []
    for prov, p in sorted(per.items(), key=lambda kv: -kv[1]["calls"]):
        answers = p["ok"] + p["outcomes"]["validator_rejected"]
        providers.append({
            "provider": prov, "calls": p["calls"], "ok": p["ok"], "fell_through": p["fell_through"],
            "limit_skips": p["limit_skips"], "outcomes": dict(p["outcomes"]), "chars": p["chars"],
            "tokens_in": p["tokens_in"], "tokens_out": p["tokens_out"], "cost": round(p["cost"], 4),
            "p50_ms": _percentile(p["ms"], 0.50), "p95_ms": _percentile(p["ms"], 0.95),
            "ok_rate": round(p["ok"] / p["calls"], 4) if p["calls"] else None,
            "structure_rate": round(p["ok"] / answers, 4) if answers else None,
            "per_day": [p["per_day"][d] for d in day_list],
        })
    return {"days": day_list, "providers": providers}
