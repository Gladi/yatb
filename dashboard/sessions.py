"""
YATB-Dashboard - Sitzungen (eigene kleine SQLite-Datei, getrennt von den Bot-Daten).

Der Browser bekommt ein zufälliges Token im Cookie; gespeichert wird nur dessen SHA-256-Hash. Wer die Datei liest,
kann sich damit nicht anmelden. Gespeichert werden außerdem nur Discord-ID, Anzeigename, Sprache und das
CSRF-Token der Sitzung - kein Discord-Token, keine E-Mail.
"""
import contextlib
import hashlib
import os
import secrets
import sqlite3
import time
from typing import NamedTuple, Optional

SESSION_DAYS = 7


class Session(NamedTuple):
    user_id: int
    name: str
    lang: Optional[str]
    csrf: str
    expires: int


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class SessionStore:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,          -- SHA-256 des Cookie-Tokens
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    lang TEXT,
                    csrf TEXT NOT NULL,
                    created INTEGER NOT NULL,
                    expires INTEGER NOT NULL
                )
            """)

    @contextlib.contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.path, timeout=5.0, isolation_level=None)   # autocommit
        try:
            yield conn
        finally:
            conn.close()

    def create(self, user_id: int, name: str, lang: Optional[str] = None) -> str:
        token, now = secrets.token_urlsafe(32), int(time.time())
        with self._conn() as conn:
            conn.execute("DELETE FROM sessions WHERE expires < ?", (now,))
            conn.execute("INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (_hash(token), user_id, name[:64], lang, secrets.token_urlsafe(24), now, now + SESSION_DAYS * 86400))
        return token

    def get(self, token: Optional[str]) -> Optional[Session]:
        if not token or len(token) > 100:
            return None
        with self._conn() as conn:
            row = conn.execute("SELECT user_id, name, lang, csrf, expires FROM sessions WHERE id = ? AND expires >= ?",
                               (_hash(token), int(time.time()))).fetchone()
        return Session(*row) if row else None

    def set_lang(self, token: str, lang: str):
        with self._conn() as conn:
            conn.execute("UPDATE sessions SET lang = ? WHERE id = ?", (lang, _hash(token)))

    def delete(self, token: Optional[str]):
        if token:
            with self._conn() as conn:
                conn.execute("DELETE FROM sessions WHERE id = ?", (_hash(token),))
