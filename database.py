"""
YATB - Datenbank-Schicht (SQLite)

Aufbau:
* Konfiguration (Bridge-Kanäle, Guild-Config) wird beim Start in den Speicher
  geladen und bei jeder Änderung neu geladen. Die "heißen" Lesefunktionen
  (get_bridge_channel_info, get_bridge_targets, get_guild_config, ...) sind
  deshalb normale, synchrone Funktionen ohne Datenbankzugriff.
* Alle anderen Funktionen sind ``async`` und laufen in einem Thread
  (asyncio.to_thread), damit der Event-Loop des Bots nie von SQLite
  blockiert wird.
* API-Keys der Server (BYOK) liegen verschlüsselt (enc2, siehe key_crypto.py) in
  der Tabelle api_keys. Ohne Master-Schlüssel können keine Keys hinterlegt werden;
  der Bot läuft dann mit dem alten Google-Key aus guild_configs weiter.
* Alte Google-Keys (Klartext oder "enc:" mit KEY_ENCRYPTION_SECRET) werden beim
  Start automatisch nach api_keys migriert, sobald der Master-Schlüssel vorhanden ist.
"""
import asyncio
import base64
import contextlib
import datetime
import functools
import hashlib
import json
import logging
import os
import sqlite3
import threading
from typing import Dict, Iterable, List, NamedTuple, Optional, Tuple

import key_crypto

log = logging.getLogger("yatb.db")

DB_DIR = "/app/data" if os.path.exists("/app/data") else os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.environ.get("YATB_DB_FILE") or os.path.join(DB_DIR, "bridge_bot.db")

USAGE_FLAGS = {"warn_90", "warn_95", "warn_100"}
GOOGLE_PROVIDER = "google_translate"
MAX_KEYS_PER_GUILD = 10

# ----------------- Verschlüsselung der API-Keys -----------------
# Neu (enc2): Master-Schlüssel als Docker-Secret, siehe key_crypto.py
_crypto: Optional[key_crypto.KeyCrypto] = key_crypto.load_crypto()

# Alt (enc:): Fernet mit SHA-256(KEY_ENCRYPTION_SECRET) - nur noch zum Lesen und Migrieren
_legacy_fernet = None
_secret = os.getenv("KEY_ENCRYPTION_SECRET", "")
if _secret:
    from cryptography.fernet import Fernet
    _legacy_fernet = Fernet(base64.urlsafe_b64encode(hashlib.sha256(_secret.encode()).digest()))
del _secret


def _legacy_decrypt(value: Optional[str], fernet) -> Optional[str]:
    """Alter Google-Key aus guild_configs: Klartext oder 'enc:' (Fernet)."""
    if not value or not value.startswith("enc:"):
        return value
    if fernet is None:
        log.error("Verschlüsselter Google-Key (enc:) in der DB, aber KEY_ENCRYPTION_SECRET fehlt.")
        return None
    try:
        return fernet.decrypt(value[4:].encode()).decode()
    except Exception:
        log.error("Google-Key (enc:) konnte nicht entschlüsselt werden (falsches KEY_ENCRYPTION_SECRET?).")
        return None


def crypto_available() -> bool:
    return _crypto is not None


# ----------------- Verbindung -----------------
@contextlib.contextmanager
def _conn():
    """Eigene Verbindung pro Aufruf: Commit bei Erfolg, Rollback bei Fehler, immer schließen."""
    conn = sqlite3.connect(DB_FILE, timeout=10.0)
    try:
        conn.execute("PRAGMA busy_timeout=10000;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _async(fn):
    """Führt eine synchrone DB-Funktion in einem Worker-Thread aus."""
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(fn, *args, **kwargs)
    return wrapper


def _columns(conn: sqlite3.Connection, table: str) -> set:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def _add_column(conn: sqlite3.Connection, table: str, column: str, ddl: str):
    if column not in _columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


# ----------------- Schema -----------------
def init_db():
    with _conn() as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        _create_schema(conn)

        if _crypto is not None:
            _migrate_legacy_keys(conn, _crypto, _legacy_fernet)
        elif conn.execute(
            "SELECT COUNT(*) FROM guild_configs WHERE google_api_key IS NOT NULL AND google_api_key != ''"
        ).fetchone()[0]:
            log.warning("Kein Master-Schlüssel (%s): alte Google-Keys bleiben unverschlüsselt/unmigriert.",
                        key_crypto.MASTER_KEY_FILE)
        _migrate_google_usage(conn)
        _migrate_currency(conn)


SCHEMA_VERSION = 3  # 3 = key_usage eingeführt
CURRENCY_SCHEMA_VERSION = 4  # 4 = Währung pro Key


def _migrate_currency(conn: sqlite3.Connection) -> int:
    """
    Einmalig: Bisher stand die Währung in der Anbieter-Config (Mistral/Gemini = EUR, Konto des Betreibers).
    Jetzt hat jeder Key seine eigene Währung - bestehende Mistral-/Gemini-Keys behalten EUR, alle anderen
    nutzen die Listenwährung des Anbieters (currency = NULL).
    """
    if conn.execute("PRAGMA user_version").fetchone()[0] >= CURRENCY_SCHEMA_VERSION:
        return 0
    n = conn.execute("UPDATE api_keys SET currency = 'EUR' WHERE provider IN ('mistral', 'gemini') AND currency IS NULL").rowcount
    conn.execute(f"PRAGMA user_version = {CURRENCY_SCHEMA_VERSION}")
    if n:
        log.info("%d Key(s) auf Währung EUR gesetzt.", n)
    return n


def _migrate_google_usage(conn: sqlite3.Connection) -> int:
    """
    Übernimmt die alten Google-Monatszähler (google_api_usage) einmalig nach key_usage.
    Die alte Tabelle bleibt bis zur Abnahme stehen (Rollback auf den alten Code bleibt möglich).
    """
    if conn.execute("PRAGMA user_version").fetchone()[0] >= SCHEMA_VERSION:
        return 0
    cur = conn.execute("""
        INSERT OR IGNORE INTO key_usage (fingerprint, period, chars, warn_90, warn_95, warn_100)
        SELECT key_hash, year_month, chars_used, warn_90, warn_95, warn_100 FROM google_api_usage
    """)
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    if cur.rowcount:
        log.info("%d Google-Monatszähler nach key_usage übernommen.", cur.rowcount)
    return cur.rowcount


def _create_schema(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS guild_configs (
            guild_id INTEGER PRIMARY KEY,
            google_api_key TEXT,
            report_channel_id INTEGER,
            is_configured INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bridge_channels (
            channel_id INTEGER PRIMARY KEY,
            guild_id INTEGER,
            bridge_id TEXT,
            language TEXT
        )
    """)
    _add_column(conn, "bridge_channels", "guild_id", "INTEGER")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bridge_guild ON bridge_channels (guild_id, bridge_id);")

    # Altes Thread-Schema (nur Paare, ohne Eltern-Kanal) ist für >2 Kanäle unbrauchbar -> ersetzt.
    conn.execute("DROP TABLE IF EXISTS bridge_threads")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS thread_links (
            thread_id INTEGER PRIMARY KEY,
            parent_id INTEGER NOT NULL,
            group_id  INTEGER NOT NULL,
            guild_id  INTEGER NOT NULL,
            bridge_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_thread_group ON thread_links (group_id, parent_id);")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS google_api_usage (
            key_hash TEXT,
            year_month TEXT,
            chars_used INTEGER DEFAULT 0,
            warn_90 INTEGER DEFAULT 0,
            warn_95 INTEGER DEFAULT 0,
            warn_100 INTEGER DEFAULT 0,
            PRIMARY KEY (key_hash, year_month)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS message_mappings (
            source_message_id INTEGER,
            target_message_id INTEGER,
            target_channel_id INTEGER,
            guild_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (source_message_id, target_message_id)
        )
    """)
    _add_column(conn, "message_mappings", "source_channel_id", "INTEGER")
    _add_column(conn, "message_mappings", "source_parent_id", "INTEGER")
    _add_column(conn, "message_mappings", "target_thread_id", "INTEGER")
    _add_column(conn, "message_mappings", "chunk_index", "INTEGER DEFAULT 0")
    _add_column(conn, "message_mappings", "src_hash", "TEXT")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_map_source ON message_mappings (source_message_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_map_target ON message_mappings (target_message_id);")
    conn.execute("DELETE FROM message_mappings WHERE created_at < datetime('now', '-7 days');")

    # API-Keys der Server (BYOK). Der Key selbst liegt nur verschlüsselt in secret_enc (enc2).
    # fingerprint = HMAC (key_crypto), damit derselbe Key serverübergreifend gemeinsam gezählt wird.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            provider TEXT NOT NULL,
            label TEXT,
            tier TEXT NOT NULL DEFAULT 'free' CHECK (tier IN ('free', 'paid')),
            limit_enabled INTEGER NOT NULL DEFAULT 1,
            secret_enc TEXT NOT NULL,
            last4 TEXT,
            fingerprint TEXT NOT NULL,
            meta TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (guild_id, fingerprint)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_fp ON api_keys (fingerprint);")
    _add_column(conn, "api_keys", "budget", "REAL")  # Monatsbudget eines Bezahl-Keys (NULL = Standard aus der Config)
    _add_column(conn, "api_keys", "currency", "TEXT")  # Abrechnungswährung des Kontos (NULL = Listenwährung des Anbieters)

    # Nutzer-Opt-out "nur lokal" - global (gilt auf allen Servern), bleibt auch beim Entfernen eines Servers erhalten
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_privacy (
            user_id INTEGER PRIMARY KEY,
            local_only INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Foren-Bridges: Tag in Forum A <-> Tag in Forum B (in beide Richtungen gültig), von YATB angelegt oder zugeordnet
    conn.execute("""
        CREATE TABLE IF NOT EXISTS forum_tag_links (
            guild_id INTEGER NOT NULL,
            forum_a INTEGER NOT NULL,
            tag_a INTEGER NOT NULL,
            forum_b INTEGER NOT NULL,
            tag_b INTEGER NOT NULL,
            PRIMARY KEY (forum_a, tag_a, forum_b)
        )
    """)

    # Eigene Reihenfolge der Übersetzer pro Server (Dashboard): JSON-Liste von api_keys.id. Nicht genannte Keys
    # folgen in der Standardreihenfolge, LibreTranslate bleibt immer der letzte Rückfall (siehe chain.build_chain).
    conn.execute("""
        CREATE TABLE IF NOT EXISTS engine_order (
            guild_id INTEGER PRIMARY KEY,
            key_ids TEXT NOT NULL,
            updated_by INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Verbrauch pro Key-Fingerprint (serverübergreifend), je Tag ('YYYY-MM-DD') und Monat ('YYYY-MM'), UTC.
    # Warnstufen gelten nur für Monatszeilen.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS key_usage (
            fingerprint TEXT NOT NULL,
            period TEXT NOT NULL,
            requests INTEGER NOT NULL DEFAULT 0,
            tokens_in INTEGER NOT NULL DEFAULT 0,
            tokens_out INTEGER NOT NULL DEFAULT 0,
            chars INTEGER NOT NULL DEFAULT 0,
            cost REAL NOT NULL DEFAULT 0,
            warn_90 INTEGER NOT NULL DEFAULT 0,
            warn_95 INTEGER NOT NULL DEFAULT 0,
            warn_100 INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (fingerprint, period)
        )
    """)


# ----------------- Migration alter Google-Keys -> api_keys (enc2) -----------------
def _legacy_hash(api_key: str) -> str:
    """Alte Zähler-ID (ungesalzener Hash) - nur noch für die Migration und den Betrieb ohne Master-Schlüssel."""
    return hashlib.sha256(api_key.strip().encode()).hexdigest()[:16]


def usage_id(api_key: str) -> str:
    """Zähler-ID eines Google-Keys: Fingerprint (HMAC), ohne Master-Schlüssel der alte Hash."""
    key = api_key.strip()
    return _crypto.fingerprint(GOOGLE_PROVIDER, key) if _crypto is not None else _legacy_hash(key)


def _last4(secret: str) -> str:
    return secret[-4:] if len(secret) >= 16 else ""


def _move_usage(conn: sqlite3.Connection, old_id: str, new_id: str):
    """Verbrauchszähler von der alten auf die neue Zähler-ID umschlüsseln (Monate werden zusammengeführt)."""
    if old_id == new_id:
        return
    conn.execute("""
        INSERT INTO google_api_usage (key_hash, year_month, chars_used, warn_90, warn_95, warn_100)
        SELECT ?, year_month, chars_used, warn_90, warn_95, warn_100 FROM google_api_usage WHERE key_hash = ?
        ON CONFLICT(key_hash, year_month) DO UPDATE SET
            chars_used = chars_used + excluded.chars_used,
            warn_90 = MAX(warn_90, excluded.warn_90),
            warn_95 = MAX(warn_95, excluded.warn_95),
            warn_100 = MAX(warn_100, excluded.warn_100)
    """, (new_id, old_id))
    conn.execute("DELETE FROM google_api_usage WHERE key_hash = ?", (old_id,))
    conn.execute("""
        INSERT INTO key_usage (fingerprint, period, requests, tokens_in, tokens_out, chars, cost, warn_90, warn_95, warn_100)
        SELECT ?, period, requests, tokens_in, tokens_out, chars, cost, warn_90, warn_95, warn_100
        FROM key_usage WHERE fingerprint = ?
        ON CONFLICT(fingerprint, period) DO UPDATE SET
            requests = requests + excluded.requests, tokens_in = tokens_in + excluded.tokens_in,
            tokens_out = tokens_out + excluded.tokens_out, chars = chars + excluded.chars, cost = cost + excluded.cost,
            warn_90 = MAX(warn_90, excluded.warn_90),
            warn_95 = MAX(warn_95, excluded.warn_95),
            warn_100 = MAX(warn_100, excluded.warn_100)
    """, (new_id, old_id))
    conn.execute("DELETE FROM key_usage WHERE fingerprint = ?", (old_id,))


def _migrate_legacy_keys(conn: sqlite3.Connection, crypto: key_crypto.KeyCrypto, legacy_fernet) -> int:
    """
    Übernimmt die alten Google-Keys aus guild_configs (Klartext oder 'enc:') nach api_keys (enc2).
    Idempotent: migrierte Zeilen werden in guild_configs auf NULL gesetzt. Schlägt ein Schritt fehl,
    bleibt die alte Zeile unverändert (der Bot nutzt sie dann weiter).
    """
    rows = conn.execute(
        "SELECT guild_id, google_api_key FROM guild_configs WHERE google_api_key IS NOT NULL AND google_api_key != ''"
    ).fetchall()
    migrated = 0
    for guild_id, stored in rows:
        if stored.startswith(key_crypto.PREFIX):
            log.error("Guild %s: unerwartetes enc2-Format in guild_configs - nicht migriert.", guild_id)
            continue
        secret = _legacy_decrypt(stored, legacy_fernet)
        if not secret or not secret.strip():
            continue  # Fehler wurde geloggt, Zeile bleibt unverändert
        secret = secret.strip()
        enc = crypto.encrypt(secret, guild_id, GOOGLE_PROVIDER)
        if crypto.decrypt(enc, guild_id, GOOGLE_PROVIDER) != secret:  # Round-Trip vor dem Löschen des Altwerts
            log.error("Guild %s: Round-Trip der Verschlüsselung fehlgeschlagen - nicht migriert.", guild_id)
            continue
        fp = crypto.fingerprint(GOOGLE_PROVIDER, secret)
        conn.execute("""
            INSERT INTO api_keys (guild_id, provider, label, tier, limit_enabled, secret_enc, last4, fingerprint)
            VALUES (?, ?, 'migrated', 'free', 1, ?, ?, ?)
            ON CONFLICT(guild_id, fingerprint) DO NOTHING
        """, (guild_id, GOOGLE_PROVIDER, enc, _last4(secret), fp))
        _move_usage(conn, _legacy_hash(secret), fp)
        conn.execute("UPDATE guild_configs SET google_api_key = NULL WHERE guild_id = ?", (guild_id,))
        migrated += 1
    if migrated:
        log.info("%d alte(r) Google-Key(s) nach api_keys (enc2) migriert.", migrated)
    return migrated


# ----------------- In-Memory-Caches (synchron lesbar) -----------------
_cache_lock = threading.Lock()
_channels: Dict[int, Tuple[int, str, str]] = {}            # channel_id -> (guild_id, bridge_id, language)
_guilds: Dict[int, Tuple[Optional[str], Optional[int], bool]] = {}  # guild_id -> (key, report_channel_id, configured)


class KeyRuntime(NamedTuple):
    """Ein entschlüsselter Key für die Übersetzung - nur im Speicher, nie loggen."""
    key_id: int                 # 0 = alter Key aus guild_configs (Betrieb ohne Master-Schlüssel)
    provider: str
    secret: str
    fingerprint: str            # Zähler-ID (gemeinsam über alle Server)
    tier: str
    limit_enabled: bool
    budget: Optional[float]     # None = Standard aus der Anbieter-Config
    label: Optional[str]
    region: Optional[str] = None  # Azure: Region der Translator-Ressource
    currency: Optional[str] = None  # Abrechnungswährung (None = Listenwährung des Anbieters)

    def __repr__(self) -> str:
        return f"<KeyRuntime #{self.key_id} {self.provider} {self.tier}>"


_guild_keys: Dict[int, List[KeyRuntime]] = {}  # guild_id -> alle entschlüsselbaren Keys (nach id sortiert)
_google_keys: Dict[int, KeyRuntime] = {}       # guild_id -> erster nutzbarer Google-Key
_engine_order: Dict[int, List[int]] = {}       # guild_id -> eigene Reihenfolge (Key-IDs), fehlt = Standard


def _reload_channels():
    global _channels
    with _cache_lock:
        with _conn() as conn:
            rows = conn.execute(
                "SELECT channel_id, guild_id, bridge_id, language FROM bridge_channels WHERE guild_id IS NOT NULL"
            ).fetchall()
        _channels = {r[0]: (r[1], r[2], r[3]) for r in rows}


def _parse_order(raw: Optional[str]) -> List[int]:
    try:
        ids = json.loads(raw) if raw else []
    except ValueError:
        return []
    return [i for i in ids if isinstance(i, int)] if isinstance(ids, list) else []


def _meta_region(meta: Optional[str]) -> Optional[str]:
    try:
        return (json.loads(meta) or {}).get("region") if meta else None
    except (ValueError, AttributeError):
        return None


def _reload_guilds():
    global _guilds, _google_keys, _guild_keys, _engine_order
    with _cache_lock:
        with _conn() as conn:
            rows = conn.execute(
                "SELECT guild_id, google_api_key, report_channel_id, is_configured FROM guild_configs"
            ).fetchall()
            key_rows = conn.execute("""
                SELECT id, guild_id, provider, secret_enc, fingerprint, tier, limit_enabled, budget, label, meta, currency
                FROM api_keys ORDER BY id
            """).fetchall() if _crypto is not None else []
            order_rows = conn.execute("SELECT guild_id, key_ids FROM engine_order").fetchall()
        keys: Dict[int, List[KeyRuntime]] = {}
        google: Dict[int, KeyRuntime] = {}
        for key_id, gid, provider, enc, fp, tier, limit_enabled, budget, label, meta, currency in key_rows:
            try:
                secret = _crypto.decrypt(enc, gid, provider)
            except key_crypto.KeyCryptoError as exc:
                log.error("API-Key %s (Guild %s) nicht entschlüsselbar: %s", key_id, gid, exc)
                continue
            rt = KeyRuntime(key_id, provider, secret, fp, tier, bool(limit_enabled), budget, label, _meta_region(meta),
                            currency)
            keys.setdefault(gid, []).append(rt)
            if provider == GOOGLE_PROVIDER and gid not in google:  # erster entschlüsselbarer Google-Key
                google[gid] = rt
        for gid, stored, _rep, _conf in rows:  # Betrieb ohne Master-Schlüssel: alter Key aus guild_configs
            if gid not in google and (secret := _legacy_decrypt(stored, _legacy_fernet)):
                secret = secret.strip()
                google[gid] = KeyRuntime(0, GOOGLE_PROVIDER, secret, usage_id(secret), "free", True, None, None)
                keys.setdefault(gid, []).append(google[gid])
        _google_keys = google
        _guild_keys = keys
        _engine_order = {gid: ids for gid, raw in order_rows if (ids := _parse_order(raw))}
        _guilds = {r[0]: (google[r[0]].secret if r[0] in google else None, r[2], bool(r[3])) for r in rows}


init_db()
_reload_channels()
_reload_guilds()


# ----------------- Hilfsfunktionen -----------------
def get_current_month() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m")


def get_google_key(guild_id: int) -> Optional[KeyRuntime]:
    return _google_keys.get(guild_id)


def get_guild_keys(guild_id: int) -> List[KeyRuntime]:
    """Alle nutzbaren Keys des Servers (KI, Google, Azure), nach Hinterlegungsreihenfolge."""
    return list(_guild_keys.get(guild_id, []))


def get_engine_order(guild_id: int) -> List[int]:
    """Eigene Reihenfolge der Übersetzer (Key-IDs); leer = Standardreihenfolge."""
    return list(_engine_order.get(guild_id, []))


# ----------------- Synchrone Lesefunktionen (aus dem Speicher) -----------------
def get_guild_config(guild_id: int) -> Tuple[Optional[str], Optional[int], bool]:
    """(google_api_key, report_channel_id, is_configured)"""
    return _guilds.get(guild_id, (None, None, False))


def get_bridge_channel_info(channel_id: int) -> Optional[Tuple[int, str, str]]:
    """(guild_id, bridge_id, language) oder None"""
    return _channels.get(channel_id)


def is_bridged(channel_id: int) -> bool:
    return channel_id in _channels


def get_bridge_targets(guild_id: int, bridge_id: str, exclude_channel_id: int) -> List[Tuple[int, str]]:
    """[(channel_id, language), ...] aller anderen Kanäle der Bridge."""
    return [
        (cid, lang)
        for cid, (gid, bid, lang) in _channels.items()
        if gid == guild_id and bid == bridge_id and cid != exclude_channel_id
    ]


def list_guild_bridges(guild_id: int) -> List[Tuple[int, str, str]]:
    """[(channel_id, bridge_id, language), ...] sortiert nach bridge_id."""
    rows = [(cid, bid, lang) for cid, (gid, bid, lang) in _channels.items() if gid == guild_id]
    return sorted(rows, key=lambda r: (r[1], r[0]))


def get_bridge_ids(guild_id: int) -> List[str]:
    return sorted({bid for (gid, bid, _l) in _channels.values() if gid == guild_id})


# ----------------- API-Keys der Server (BYOK) -----------------
class ApiKeyInfo(NamedTuple):
    """Anzeigbare Daten eines Keys - enthält nie den Key selbst."""
    id: int
    provider: str
    label: Optional[str]
    tier: str
    limit_enabled: bool
    last4: str
    created_at: str
    shared: bool  # derselbe Key ist auch auf einem anderen Server hinterlegt
    budget: Optional[float] = None  # None = Standard aus der Anbieter-Config
    fingerprint: str = ""           # Zähler-ID (HMAC, nicht umkehrbar)
    currency: Optional[str] = None  # None = Listenwährung des Anbieters
    region: Optional[str] = None


_KEY_INFO_SQL = """
    SELECT k.id, k.provider, k.label, k.tier, k.limit_enabled, COALESCE(k.last4, ''), k.created_at,
           EXISTS(SELECT 1 FROM api_keys o WHERE o.fingerprint = k.fingerprint AND o.guild_id != k.guild_id),
           k.budget, k.fingerprint, k.currency, k.meta
    FROM api_keys k
"""


def _key_info(row) -> ApiKeyInfo:
    return ApiKeyInfo(row[0], row[1], row[2], row[3], bool(row[4]), row[5], row[6], bool(row[7]), row[8], row[9],
                      row[10], _meta_region(row[11]))


@_async
def add_api_key(
    guild_id: int, provider: str, secret: str, tier: str = "free", label: Optional[str] = None,
    meta: Optional[str] = None, created_by: Optional[int] = None, budget: Optional[float] = None,
    currency: Optional[str] = None,
) -> Tuple[str, Optional[ApiKeyInfo]]:
    """Status 'ok' | 'no_crypto' | 'duplicate' (mit dem vorhandenen Eintrag) | 'too_many'."""
    if _crypto is None:
        return "no_crypto", None
    secret = secret.strip()
    fp = _crypto.fingerprint(provider, secret)
    with _conn() as conn:
        dup = conn.execute(_KEY_INFO_SQL + " WHERE k.guild_id = ? AND k.fingerprint = ?", (guild_id, fp)).fetchone()
        if dup:
            return "duplicate", _key_info(dup)
        count = conn.execute("SELECT COUNT(*) FROM api_keys WHERE guild_id = ?", (guild_id,)).fetchone()[0]
        if count >= MAX_KEYS_PER_GUILD:
            return "too_many", None
        cur = conn.execute("""
            INSERT INTO api_keys (guild_id, provider, label, tier, limit_enabled, secret_enc, last4, fingerprint, meta,
                                  created_by, budget, currency)
            VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?)
        """, (guild_id, provider, label, tier, _crypto.encrypt(secret, guild_id, provider), _last4(secret), fp, meta,
              created_by, budget, currency))
        conn.execute("""
            INSERT INTO guild_configs (guild_id, is_configured) VALUES (?, 1)
            ON CONFLICT(guild_id) DO UPDATE SET is_configured = 1
        """, (guild_id,))
        row = conn.execute(_KEY_INFO_SQL + " WHERE k.id = ?", (cur.lastrowid,)).fetchone()
    _reload_guilds()
    return "ok", _key_info(row)


@_async
def list_api_keys(guild_id: int) -> List[ApiKeyInfo]:
    with _conn() as conn:
        rows = conn.execute(_KEY_INFO_SQL + " WHERE k.guild_id = ? ORDER BY k.provider, k.id", (guild_id,)).fetchall()
    return [_key_info(r) for r in rows]


@_async
def remove_api_key(guild_id: int, key_id: int) -> Optional[ApiKeyInfo]:
    with _conn() as conn:
        row = conn.execute(_KEY_INFO_SQL + " WHERE k.guild_id = ? AND k.id = ?", (guild_id, key_id)).fetchone()
        if row is None:
            return None
        conn.execute("DELETE FROM api_keys WHERE guild_id = ? AND id = ?", (guild_id, key_id))
    _reload_guilds()
    return _key_info(row)


_KEY_SETTINGS = {"limit_enabled", "tier", "budget", "currency", "label", "meta"}


def _update_key(guild_id: int, key_id: int, column: str, value) -> Optional[ApiKeyInfo]:
    return _update_key_settings(guild_id, key_id, {column: value})


def _update_key_settings(guild_id: int, key_id: int, values: Dict[str, object]) -> Optional[ApiKeyInfo]:
    assert values and set(values) <= _KEY_SETTINGS  # nur feste Spaltennamen -> keine SQL-Injection
    sets = ", ".join(f"{col} = ?" for col in values)
    with _conn() as conn:
        cur = conn.execute(
            f"UPDATE api_keys SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE guild_id = ? AND id = ?",
            (*values.values(), guild_id, key_id),
        )
        if cur.rowcount == 0:
            return None
        row = conn.execute(_KEY_INFO_SQL + " WHERE k.id = ?", (key_id,)).fetchone()
    _reload_guilds()
    return _key_info(row)


@_async
def update_api_key(
    guild_id: int, key_id: int, *, label: Optional[str], tier: str, budget: Optional[float], currency: Optional[str],
    limit_enabled: bool, region: Optional[str] = None,
) -> Optional[ApiKeyInfo]:
    """Alle Einstellungen eines Keys auf einmal (Formular /yatb keys edit, später Website). Nie der Key selbst."""
    if tier not in ("free", "paid"):
        raise ValueError("tier muss 'free' oder 'paid' sein")
    values: Dict[str, object] = {"label": label, "tier": tier, "budget": budget, "currency": currency,
                                 "limit_enabled": int(limit_enabled)}
    if region is not None:
        values["meta"] = json.dumps({"region": region})
    return _update_key_settings(guild_id, key_id, values)


@_async
def set_engine_order(guild_id: int, key_ids: Optional[List[int]], user_id: Optional[int] = None) -> Optional[List[int]]:
    """
    Eigene Reihenfolge speichern (Key-IDs dieses Servers, ohne Doppelte); None oder [] = zurück zum Standard.
    Unbekannte IDs -> ValueError. Rückgabe: gespeicherte Liste (None = Standard).
    """
    ids = list(dict.fromkeys(key_ids or []))
    with _conn() as conn:
        if not ids:
            conn.execute("DELETE FROM engine_order WHERE guild_id = ?", (guild_id,))
        else:
            known = {r[0] for r in conn.execute("SELECT id FROM api_keys WHERE guild_id = ?", (guild_id,))}
            if not set(ids) <= known:
                raise ValueError("unbekannte Key-ID")
            conn.execute("""
                INSERT INTO engine_order (guild_id, key_ids, updated_by, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(guild_id) DO UPDATE SET key_ids = excluded.key_ids, updated_by = excluded.updated_by,
                                                    updated_at = CURRENT_TIMESTAMP
            """, (guild_id, json.dumps(ids), user_id))
    _reload_guilds()
    return ids or None


# ----------------- Nutzer-Opt-out "nur lokal" -----------------
_local_only: set = set()


def _reload_privacy():
    global _local_only
    with _conn() as conn:
        _local_only = {r[0] for r in conn.execute("SELECT user_id FROM user_privacy WHERE local_only = 1")}


def is_local_only(user_id: Optional[int]) -> bool:
    """Opt-out des Nutzers: seine Nachrichten nur lokal (Libre) übersetzen, nichts an Dritte."""
    return user_id is not None and user_id in _local_only


@_async
def set_local_only(user_id: int, enabled: bool):
    with _conn() as conn:
        conn.execute("""
            INSERT INTO user_privacy (user_id, local_only, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET local_only = excluded.local_only, updated_at = CURRENT_TIMESTAMP
        """, (user_id, int(enabled)))
    _reload_privacy()


_reload_privacy()


@_async
def set_api_key_limit(guild_id: int, key_id: int, enabled: bool) -> Optional[ApiKeyInfo]:
    return _update_key(guild_id, key_id, "limit_enabled", int(enabled))


@_async
def set_api_key_tier(guild_id: int, key_id: int, tier: str) -> Optional[ApiKeyInfo]:
    if tier not in ("free", "paid"):
        raise ValueError("tier muss 'free' oder 'paid' sein")
    return _update_key(guild_id, key_id, "tier", tier)


@_async
def set_api_key_budget(guild_id: int, key_id: int, budget: Optional[float]) -> Optional[ApiKeyInfo]:
    """budget = None setzt auf den Standard der Anbieter-Config zurück."""
    if budget is not None and budget < 0:
        raise ValueError("budget muss >= 0 sein")
    return _update_key(guild_id, key_id, "budget", budget)


@_async
def guilds_for_fingerprint(fingerprint: str) -> List[int]:
    """Alle Server, auf denen derselbe Key hinterlegt ist (für Warnungen an alle Nutzer des Keys)."""
    with _conn() as conn:
        return [r[0] for r in conn.execute(
            "SELECT DISTINCT guild_id FROM api_keys WHERE fingerprint = ?", (fingerprint,)
        ).fetchall()]


# ----------------- Guild-Konfiguration -----------------

@_async
def set_guild_report_channel(guild_id: int, channel_id: Optional[int]):
    with _conn() as conn:
        conn.execute("""
            INSERT INTO guild_configs (guild_id, report_channel_id, is_configured) VALUES (?, ?, 1)
            ON CONFLICT(guild_id) DO UPDATE SET report_channel_id = excluded.report_channel_id, is_configured = 1
        """, (guild_id, channel_id))
    _reload_guilds()


@_async
def clear_guild_data(guild_id: int):
    with _conn() as conn:
        conn.execute("DELETE FROM guild_configs WHERE guild_id = ?", (guild_id,))
        conn.execute("DELETE FROM api_keys WHERE guild_id = ?", (guild_id,))
        conn.execute("DELETE FROM engine_order WHERE guild_id = ?", (guild_id,))
        conn.execute("DELETE FROM forum_tag_links WHERE guild_id = ?", (guild_id,))
        conn.execute("DELETE FROM bridge_channels WHERE guild_id = ?", (guild_id,))
        conn.execute("DELETE FROM thread_links WHERE guild_id = ?", (guild_id,))
        conn.execute("DELETE FROM message_mappings WHERE guild_id = ?", (guild_id,))
    _reload_channels()
    _reload_guilds()


# ----------------- Bridge-Kanäle -----------------
@_async
def add_bridge_channel(channel_id: int, guild_id: int, bridge_id: str, language: str):
    with _conn() as conn:
        conn.execute("""
            INSERT INTO bridge_channels (channel_id, guild_id, bridge_id, language) VALUES (?, ?, ?, ?)
            ON CONFLICT(channel_id) DO UPDATE SET
                guild_id = excluded.guild_id, bridge_id = excluded.bridge_id, language = excluded.language
        """, (channel_id, guild_id, bridge_id, language))
        conn.execute("""
            INSERT INTO guild_configs (guild_id, is_configured) VALUES (?, 1)
            ON CONFLICT(guild_id) DO UPDATE SET is_configured = 1
        """, (guild_id,))
    _reload_channels()
    _reload_guilds()


@_async
def remove_bridge_channel(channel_id: int, guild_id: int) -> Optional[Tuple[str, str]]:
    """Gibt (bridge_id, language) des entfernten Kanals zurück, sonst None."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT bridge_id, language FROM bridge_channels WHERE channel_id = ? AND guild_id = ?",
            (channel_id, guild_id),
        ).fetchone()
        if row is None:
            return None
        conn.execute("DELETE FROM bridge_channels WHERE channel_id = ? AND guild_id = ?", (channel_id, guild_id))
    _reload_channels()
    return (row[0], row[1])


@_async
def get_stats(guild_id: int) -> Tuple[int, int, int]:
    """(Anzahl Bridges, Anzahl Kanäle, Anzahl Nachrichten-Mappings)"""
    with _conn() as conn:
        bridges, channels = conn.execute(
            "SELECT COUNT(DISTINCT bridge_id), COUNT(*) FROM bridge_channels WHERE guild_id = ?", (guild_id,)
        ).fetchone()
        mappings = conn.execute(
            "SELECT COUNT(*) FROM message_mappings WHERE guild_id = ?", (guild_id,)
        ).fetchone()[0]
    return bridges, channels, mappings


# ----------------- Verbrauch pro Key (Limit-Engine, siehe limits.py) -----------------
class UsageRow(NamedTuple):
    requests: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    chars: int = 0
    cost: float = 0.0
    warn_90: bool = False
    warn_95: bool = False
    warn_100: bool = False


def _usage(conn: sqlite3.Connection, fingerprint: str, period: str) -> UsageRow:
    row = conn.execute("""
        SELECT requests, tokens_in, tokens_out, chars, cost, warn_90, warn_95, warn_100
        FROM key_usage WHERE fingerprint = ? AND period = ?
    """, (fingerprint, period)).fetchone()
    if row is None:
        return UsageRow()
    return UsageRow(row[0], row[1], row[2], row[3], row[4], bool(row[5]), bool(row[6]), bool(row[7]))


@_async
def get_key_usage(fingerprint: str, day: str, month: str) -> Tuple[UsageRow, UsageRow]:
    """(Verbrauch heute, Verbrauch diesen Monat) - über alle Server mit demselben Key."""
    with _conn() as conn:
        return _usage(conn, fingerprint, day), _usage(conn, fingerprint, month)


@_async
def add_key_usage(
    fingerprint: str, day: str, month: str,
    requests: int = 0, tokens_in: int = 0, tokens_out: int = 0, chars: int = 0, cost: float = 0.0,
) -> UsageRow:
    """Addiert atomar auf Tages- und Monatszeile, gibt die Monatszeile danach zurück."""
    with _conn() as conn:
        for period in (day, month):
            conn.execute("""
                INSERT INTO key_usage (fingerprint, period, requests, tokens_in, tokens_out, chars, cost)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(fingerprint, period) DO UPDATE SET
                    requests = requests + excluded.requests, tokens_in = tokens_in + excluded.tokens_in,
                    tokens_out = tokens_out + excluded.tokens_out, chars = chars + excluded.chars,
                    cost = cost + excluded.cost
            """, (fingerprint, period, requests, tokens_in, tokens_out, chars, cost))
        return _usage(conn, fingerprint, month)


@_async
def set_key_usage_flags(fingerprint: str, month: str, flags: Iterable[str]):
    flags = [f for f in flags if f in USAGE_FLAGS]
    if not flags:
        return
    with _conn() as conn:
        conn.execute("INSERT OR IGNORE INTO key_usage (fingerprint, period) VALUES (?, ?)", (fingerprint, month))
        for flag in flags:  # nur Whitelist-Spalten -> kein SQL-Injection-Risiko
            conn.execute(f"UPDATE key_usage SET {flag} = 1 WHERE fingerprint = ? AND period = ?", (fingerprint, month))


@_async
def cleanup_key_usage(keep_days: int = 40) -> int:
    """Tageszeilen älter als keep_days löschen (Monatszeilen bleiben)."""
    cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=int(keep_days))).strftime("%Y-%m-%d")
    with _conn() as conn:
        return conn.execute(
            "DELETE FROM key_usage WHERE length(period) = 10 AND period < ?", (cutoff,)
        ).rowcount


# ----------------- Threads -----------------
# Alle Threads, die zusammengehören (Original + Spiegel in den anderen Kanälen),
# teilen sich eine group_id. So funktionieren auch Bridges mit mehr als 2 Kanälen.
@_async
def get_thread_link(thread_id: int) -> Optional[Tuple[int, int]]:
    """(group_id, parent_id) oder None"""
    with _conn() as conn:
        row = conn.execute("SELECT group_id, parent_id FROM thread_links WHERE thread_id = ?", (thread_id,)).fetchone()
    return (row[0], row[1]) if row else None


@_async
def lookup_target_thread(source_thread_id: int, target_parent_id: int) -> Optional[int]:
    with _conn() as conn:
        row = conn.execute("""
            SELECT t2.thread_id
            FROM thread_links t1
            JOIN thread_links t2 ON t2.group_id = t1.group_id AND t2.parent_id = ?
            WHERE t1.thread_id = ?
            LIMIT 1
        """, (target_parent_id, source_thread_id)).fetchone()
    return row[0] if row else None


@_async
def register_thread(thread_id: int, parent_id: int, group_id: int, guild_id: int, bridge_id: str):
    with _conn() as conn:
        # pro Gruppe und Eltern-Kanal darf es nur einen Thread geben (alte/tote Einträge ersetzen)
        conn.execute(
            "DELETE FROM thread_links WHERE group_id = ? AND parent_id = ? AND thread_id != ?",
            (group_id, parent_id, thread_id),
        )
        conn.execute(
            "INSERT OR REPLACE INTO thread_links (thread_id, parent_id, group_id, guild_id, bridge_id) VALUES (?, ?, ?, ?, ?)",
            (thread_id, parent_id, group_id, guild_id, bridge_id),
        )


@_async
def group_threads(group_id: int) -> List[Tuple[int, int]]:
    """Alle Threads einer Gesprächsgruppe (Original + Spiegel): [(thread_id, parent_id), ...]"""
    with _conn() as conn:
        return conn.execute("SELECT thread_id, parent_id FROM thread_links WHERE group_id = ?", (group_id,)).fetchall()


# ----------------- Foren-Tags (Zuordnung zwischen den Foren einer Bridge) -----------------
@_async
def get_tag_link(forum_from: int, tag_id: int, forum_to: int) -> Optional[int]:
    """Gegenstück eines Tags im anderen Forum (Zuordnung gilt in beide Richtungen) oder None."""
    with _conn() as conn:
        row = conn.execute("""
            SELECT tag_b FROM forum_tag_links WHERE forum_a = ? AND tag_a = ? AND forum_b = ?
            UNION ALL
            SELECT tag_a FROM forum_tag_links WHERE forum_b = ? AND tag_b = ? AND forum_a = ?
            LIMIT 1
        """, (forum_from, tag_id, forum_to, forum_from, tag_id, forum_to)).fetchone()
    return row[0] if row else None


@_async
def save_tag_link(guild_id: int, forum_a: int, tag_a: int, forum_b: int, tag_b: int):
    with _conn() as conn:
        conn.execute("DELETE FROM forum_tag_links WHERE forum_a = ? AND tag_a = ? AND forum_b = ?", (forum_b, tag_b, forum_a))
        conn.execute("INSERT OR REPLACE INTO forum_tag_links VALUES (?, ?, ?, ?, ?)", (guild_id, forum_a, tag_a, forum_b, tag_b))


@_async
def delete_thread_link(thread_id: int):
    with _conn() as conn:
        conn.execute("DELETE FROM thread_links WHERE thread_id = ?", (thread_id,))


# ----------------- Nachrichten-Mappings (Edit / Delete / Replies) -----------------
@_async
def save_message_mapping(
    source_message_id: int, source_channel_id: int, source_parent_id: int,
    target_message_id: int, target_channel_id: int, target_thread_id: Optional[int],
    chunk_index: int, guild_id: int, src_hash: Optional[str],
):
    with _conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO message_mappings
                (source_message_id, source_channel_id, source_parent_id, target_message_id,
                 target_channel_id, target_thread_id, chunk_index, guild_id, src_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (source_message_id, source_channel_id, source_parent_id, target_message_id,
              target_channel_id, target_thread_id, chunk_index, guild_id, src_hash))


@_async
def get_message_mappings(source_message_id: int) -> List[Tuple[int, int, Optional[int], int, Optional[str]]]:
    """[(target_message_id, target_channel_id, target_thread_id, chunk_index, src_hash), ...]"""
    with _conn() as conn:
        return conn.execute("""
            SELECT target_message_id, target_channel_id, target_thread_id, COALESCE(chunk_index, 0), src_hash
            FROM message_mappings WHERE source_message_id = ?
            ORDER BY target_channel_id, chunk_index
        """, (source_message_id,)).fetchall()


@_async
def find_origin(target_message_id: int) -> Optional[Tuple[int, int, int]]:
    """Zu einer gespiegelten Nachricht: (source_message_id, source_channel_id, source_parent_id)."""
    with _conn() as conn:
        row = conn.execute("""
            SELECT source_message_id, source_channel_id, source_parent_id
            FROM message_mappings WHERE target_message_id = ? LIMIT 1
        """, (target_message_id,)).fetchone()
    if row is None or row[1] is None or row[2] is None:
        return None
    return (row[0], row[1], row[2])


@_async
def find_mirror(source_message_id: int, target_channel_id: int) -> Optional[Tuple[int, int]]:
    """Zur Original-Nachricht: (target_message_id, ort_id) im Ziel-Kanal (ort_id = Thread oder Kanal)."""
    with _conn() as conn:
        row = conn.execute("""
            SELECT target_message_id, COALESCE(target_thread_id, target_channel_id)
            FROM message_mappings
            WHERE source_message_id = ? AND target_channel_id = ?
            ORDER BY chunk_index LIMIT 1
        """, (source_message_id, target_channel_id)).fetchone()
    return (row[0], row[1]) if row else None


@_async
def update_mapping_hash(source_message_id: int, src_hash: str):
    with _conn() as conn:
        conn.execute("UPDATE message_mappings SET src_hash = ? WHERE source_message_id = ?", (src_hash, source_message_id))


@_async
def delete_mapping_rows(source_message_id: int, target_message_ids: Iterable[int]):
    ids = list(target_message_ids)
    if not ids:
        return
    with _conn() as conn:
        conn.executemany(
            "DELETE FROM message_mappings WHERE source_message_id = ? AND target_message_id = ?",
            [(source_message_id, tid) for tid in ids],
        )


@_async
def delete_message_mappings(source_message_id: int):
    with _conn() as conn:
        conn.execute("DELETE FROM message_mappings WHERE source_message_id = ?", (source_message_id,))


@_async
def cleanup_old_mappings(days: int = 7) -> int:
    with _conn() as conn:
        cur = conn.execute("DELETE FROM message_mappings WHERE created_at < datetime('now', ?)", (f"-{int(days)} days",))
        return cur.rowcount