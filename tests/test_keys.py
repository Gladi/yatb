"""
Tests für Paket 2 (API-Keys, enc2-Verschlüsselung, Migration).

Läuft ohne Netzwerk und ohne Discord-Token, mit Wegwerf-Master-Schlüssel und Wegwerf-DB:
    python -m unittest discover -s tests -v
"""
import asyncio
import base64
import hashlib
import logging
import os
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import unittest

from _testenv import BOT_DIR, MASTER_FILE, TMP  # noqa: F401  (setzt Umgebung vor den Bot-Imports)
from cryptography.fernet import Fernet  # noqa: E402

import database as db  # noqa: E402
import key_crypto  # noqa: E402

GOOGLE_KEY = "AIzaTESTkey0123456789abcdefghijklmnopq"   # Dummy im Format eines Google-Keys  gitleaks:allow
OTHER_KEY = "sk-test-0123456789abcdefghijklmnopqrstuv"   # Dummy  gitleaks:allow
G1, G2 = 111111111111111111, 222222222222222222


def run(coro):
    return asyncio.run(coro)


def new_crypto() -> key_crypto.KeyCrypto:
    return key_crypto.KeyCrypto(os.urandom(32))


class _CaptureLogs(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())

    def __enter__(self):
        root = logging.getLogger()
        self._old_level = root.level
        root.setLevel(logging.DEBUG)
        root.addHandler(self)
        return self

    def __exit__(self, *exc):
        root = logging.getLogger()
        root.removeHandler(self)
        root.setLevel(self._old_level)


# ---------------------------------------------------------------------------
class CryptoTests(unittest.TestCase):
    def setUp(self):
        self.c = new_crypto()

    def test_roundtrip(self):
        token = self.c.encrypt(GOOGLE_KEY, G1, "google_translate")
        self.assertTrue(token.startswith("enc2:" + self.c.kid + ":"))
        self.assertNotIn(GOOGLE_KEY, token)
        self.assertEqual(self.c.decrypt(token, G1, "google_translate"), GOOGLE_KEY)

    def test_wrong_guild_fails(self):
        token = self.c.encrypt(GOOGLE_KEY, G1, "google_translate")
        with self.assertRaises(key_crypto.KeyCryptoError):
            self.c.decrypt(token, G2, "google_translate")

    def test_wrong_provider_fails(self):
        token = self.c.encrypt(GOOGLE_KEY, G1, "google_translate")
        with self.assertRaises(key_crypto.KeyCryptoError):
            self.c.decrypt(token, G1, "gemini")

    def test_wrong_master_fails_with_kid_message(self):
        token = self.c.encrypt(GOOGLE_KEY, G1, "mistral")
        with self.assertRaises(key_crypto.KeyCryptoError) as ctx:
            new_crypto().decrypt(token, G1, "mistral")
        self.assertIn("Master", str(ctx.exception))

    def test_tampered_ciphertext_fails(self):
        token = self.c.encrypt(GOOGLE_KEY, G1, "mistral")
        prefix, payload = token.rsplit(":", 1)
        raw = bytearray(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        raw[20] ^= 0x01
        bad = prefix + ":" + base64.urlsafe_b64encode(bytes(raw)).decode().rstrip("=")
        with self.assertRaises(key_crypto.KeyCryptoError):
            self.c.decrypt(bad, G1, "mistral")
        for broken in ("enc2:", "enc2:" + self.c.kid, "enc2:" + self.c.kid + ":!!!", "enc:abc", ""):
            with self.assertRaises(key_crypto.KeyCryptoError):
                self.c.decrypt(broken, G1, "mistral")

    def test_nonce_unique(self):
        a = self.c.encrypt(GOOGLE_KEY, G1, "google_translate")
        b = self.c.encrypt(GOOGLE_KEY, G1, "google_translate")
        self.assertNotEqual(a, b)

    def test_fingerprint(self):
        fp = self.c.fingerprint("mistral", OTHER_KEY)
        self.assertEqual(fp, self.c.fingerprint("mistral", OTHER_KEY))       # gleicher Key -> gleicher Zähler
        self.assertNotEqual(fp, self.c.fingerprint("mistral", OTHER_KEY + "x"))
        self.assertNotEqual(fp, self.c.fingerprint("groq", OTHER_KEY))       # Anbieter gehört dazu
        self.assertNotEqual(fp, new_crypto().fingerprint("mistral", OTHER_KEY))  # hängt vom Master ab
        self.assertNotEqual(fp, hashlib.sha256(OTHER_KEY.encode()).hexdigest())
        self.assertNotIn(OTHER_KEY, fp)

    def test_repr_has_no_key_material(self):
        self.assertEqual(repr(self.c), f"<KeyCrypto kid={self.c.kid}>")

    def test_load_master(self):
        missing = os.path.join(TMP, "does_not_exist")
        self.assertIsNone(key_crypto.load_master(missing))
        bad = os.path.join(TMP, "bad_master")
        for content in ("not base64 !!!", base64.b64encode(os.urandom(16)).decode()):
            with open(bad, "w") as fh:
                fh.write(content)
            self.assertIsNone(key_crypto.load_master(bad))
        self.assertEqual(len(key_crypto.load_master(MASTER_FILE)), 32)


# ---------------------------------------------------------------------------
class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.crypto = new_crypto()
        fd, self.path = tempfile.mkstemp(suffix=".db", dir=TMP)
        os.close(fd)
        self.conn = sqlite3.connect(self.path)
        db._create_schema(self.conn)

    def tearDown(self):
        self.conn.close()

    def _legacy(self, guild_id, stored, usage_chars=None, warn_90=0):
        self.conn.execute("INSERT INTO guild_configs (guild_id, google_api_key, is_configured) VALUES (?, ?, 1)",
                          (guild_id, stored))
        if usage_chars is not None:
            self.conn.execute(
                "INSERT INTO google_api_usage (key_hash, year_month, chars_used, warn_90) VALUES (?, '2026-10', ?, ?)",
                (db._legacy_hash(GOOGLE_KEY), usage_chars, warn_90),
            )

    def _keys(self):
        return self.conn.execute(
            "SELECT guild_id, provider, label, tier, limit_enabled, secret_enc, last4, fingerprint FROM api_keys"
        ).fetchall()

    def test_plaintext(self):
        self._legacy(G1, GOOGLE_KEY, usage_chars=1234, warn_90=1)
        self._legacy(G2, None)
        self.assertEqual(db._migrate_legacy_keys(self.conn, self.crypto, None), 1)
        rows = self._keys()
        self.assertEqual(len(rows), 1)
        gid, provider, label, tier, limit_enabled, enc, last4, fp = rows[0]
        self.assertEqual((gid, provider, label, tier, limit_enabled, last4),
                         (G1, "google_translate", "migrated", "free", 1, GOOGLE_KEY[-4:]))
        self.assertEqual(self.crypto.decrypt(enc, G1, "google_translate"), GOOGLE_KEY)
        self.assertEqual(fp, self.crypto.fingerprint("google_translate", GOOGLE_KEY))
        self.assertIsNone(self.conn.execute("SELECT google_api_key FROM guild_configs WHERE guild_id = ?", (G1,)).fetchone()[0])
        usage = self.conn.execute("SELECT key_hash, chars_used, warn_90 FROM google_api_usage").fetchall()
        self.assertEqual(usage, [(fp, 1234, 1)])  # Zähler übernommen, alter Hash weg

    def test_enc_with_secret(self):
        fernet = Fernet(base64.urlsafe_b64encode(hashlib.sha256(b"old-secret").digest()))
        self._legacy(G1, "enc:" + fernet.encrypt(GOOGLE_KEY.encode()).decode())
        self.assertEqual(db._migrate_legacy_keys(self.conn, self.crypto, fernet), 1)
        enc = self._keys()[0][5]
        self.assertEqual(self.crypto.decrypt(enc, G1, "google_translate"), GOOGLE_KEY)

    def test_enc_without_or_wrong_secret_keeps_row(self):
        fernet = Fernet(base64.urlsafe_b64encode(hashlib.sha256(b"old-secret").digest()))
        stored = "enc:" + fernet.encrypt(GOOGLE_KEY.encode()).decode()
        self._legacy(G1, stored)
        wrong = Fernet(base64.urlsafe_b64encode(hashlib.sha256(b"wrong").digest()))
        for legacy in (None, wrong):
            with self.assertLogs("yatb.db", level="ERROR"):
                self.assertEqual(db._migrate_legacy_keys(self.conn, self.crypto, legacy), 0)
        self.assertEqual(self._keys(), [])
        self.assertEqual(self.conn.execute("SELECT google_api_key FROM guild_configs").fetchone()[0], stored)

    def test_idempotent(self):
        self._legacy(G1, GOOGLE_KEY, usage_chars=10)
        self.assertEqual(db._migrate_legacy_keys(self.conn, self.crypto, None), 1)
        self.assertEqual(db._migrate_legacy_keys(self.conn, self.crypto, None), 0)
        self.assertEqual(len(self._keys()), 1)
        self.assertEqual(self.conn.execute("SELECT SUM(chars_used) FROM google_api_usage").fetchone()[0], 10)

    def test_same_key_on_two_guilds_shares_counter(self):
        self._legacy(G1, GOOGLE_KEY, usage_chars=500)
        self._legacy(G2, " " + GOOGLE_KEY + " ")  # alte Daten evtl. mit Leerzeichen
        self.assertEqual(db._migrate_legacy_keys(self.conn, self.crypto, None), 2)
        fps = {r[7] for r in self._keys()}
        self.assertEqual(len(fps), 1)
        self.assertEqual(self.conn.execute("SELECT key_hash, chars_used FROM google_api_usage").fetchall(),
                         [(fps.pop(), 500)])

    def test_unexpected_enc2_in_legacy_column_is_skipped(self):
        self._legacy(G1, self.crypto.encrypt(GOOGLE_KEY, G1, "google_translate"))
        with self.assertLogs("yatb.db", level="ERROR"):
            self.assertEqual(db._migrate_legacy_keys(self.conn, self.crypto, None), 0)

    def test_no_key_in_logs(self):
        self._legacy(G1, GOOGLE_KEY, usage_chars=1)
        with _CaptureLogs() as cap:
            db._migrate_legacy_keys(self.conn, self.crypto, None)
        self.assertTrue(cap.messages)
        self.assertFalse(any(GOOGLE_KEY in m for m in cap.messages))


# ---------------------------------------------------------------------------
class ApiKeyStoreTests(unittest.TestCase):
    """Die öffentlichen DB-Funktionen, wie der Bot sie aufruft (Modul-DB mit Test-Master)."""

    def setUp(self):
        with db._conn() as conn:
            conn.execute("DELETE FROM api_keys")
            conn.execute("DELETE FROM guild_configs")
            conn.execute("DELETE FROM google_api_usage")
            conn.execute("DELETE FROM key_usage")
        db._reload_guilds()

    def test_crypto_loaded(self):
        self.assertTrue(db.crypto_available())

    def test_add_list_and_google_key_in_cache(self):
        status, info = run(db.add_api_key(G1, "google_translate", "  " + GOOGLE_KEY + "\n", created_by=42))
        self.assertEqual(status, "ok")
        self.assertEqual((info.provider, info.tier, info.limit_enabled, info.last4, info.shared),
                         ("google_translate", "free", True, GOOGLE_KEY[-4:], False))
        self.assertNotIn(GOOGLE_KEY, repr(info))
        self.assertEqual(db.get_guild_config(G1)[0], GOOGLE_KEY)  # Bot nutzt den Key wie bisher
        with db._conn() as conn:
            stored = conn.execute("SELECT secret_enc FROM api_keys").fetchone()[0]
        self.assertTrue(stored.startswith("enc2:"))
        self.assertEqual([i.id for i in run(db.list_api_keys(G1))], [info.id])
        self.assertEqual(run(db.list_api_keys(G2)), [])

    def test_duplicate_same_guild_rejected(self):
        run(db.add_api_key(G1, "mistral", OTHER_KEY, label="main"))
        status, info = run(db.add_api_key(G1, "mistral", OTHER_KEY))
        self.assertEqual(status, "duplicate")
        self.assertEqual(info.label, "main")

    def test_same_key_other_guild_is_shared(self):
        _, a = run(db.add_api_key(G1, "mistral", OTHER_KEY))
        status, b = run(db.add_api_key(G2, "mistral", OTHER_KEY, tier="paid"))
        self.assertEqual(status, "ok")
        self.assertTrue(b.shared)
        self.assertTrue(run(db.list_api_keys(G1))[0].shared)
        self.assertEqual(b.tier, "paid")  # Tier bleibt pro Server

    def test_max_keys(self):
        for n in range(db.MAX_KEYS_PER_GUILD):
            self.assertEqual(run(db.add_api_key(G1, "groq", f"gsk_{n:02d}_0123456789abcdef"))[0], "ok")
        self.assertEqual(run(db.add_api_key(G1, "groq", "gsk_extra_0123456789abcdef"))[0], "too_many")

    def test_remove_and_limit(self):
        _, info = run(db.add_api_key(G1, "google_translate", GOOGLE_KEY))
        self.assertIsNone(run(db.set_api_key_limit(G2, info.id, False)))  # fremder Server
        self.assertFalse(run(db.set_api_key_limit(G1, info.id, False)).limit_enabled)
        self.assertIsNone(run(db.remove_api_key(G2, info.id)))
        self.assertEqual(run(db.remove_api_key(G1, info.id)).id, info.id)
        self.assertIsNone(db.get_guild_config(G1)[0])

    def test_clear_guild_data_removes_keys(self):
        run(db.add_api_key(G1, "google_translate", GOOGLE_KEY))
        run(db.add_api_key(G2, "google_translate", GOOGLE_KEY))
        run(db.clear_guild_data(G1))
        self.assertEqual(run(db.list_api_keys(G1)), [])
        self.assertEqual(len(run(db.list_api_keys(G2))), 1)

    def test_google_runtime_key_and_usage_id(self):
        _, info = run(db.add_api_key(G1, "google_translate", GOOGLE_KEY, tier="paid"))
        rt = db.get_google_key(G1)
        self.assertEqual((rt.key_id, rt.tier, rt.limit_enabled, rt.secret), (info.id, "paid", True, GOOGLE_KEY))
        self.assertEqual(rt.fingerprint, db.usage_id(" " + GOOGLE_KEY))  # Zähler-ID = Fingerprint
        self.assertEqual(rt.fingerprint, info.fingerprint)
        self.assertNotIn(GOOGLE_KEY, repr(rt))
        run(db.set_api_key_limit(G1, info.id, False))
        self.assertFalse(db.get_google_key(G1).limit_enabled)  # Cache wird aktualisiert
        run(db.set_api_key_budget(G1, info.id, 2.5))
        self.assertEqual(db.get_google_key(G1).budget, 2.5)
        run(db.set_api_key_tier(G1, info.id, "free"))
        self.assertEqual(db.get_google_key(G1).tier, "free")
        self.assertEqual(run(db.guilds_for_fingerprint(info.fingerprint)), [G1])

    def test_no_key_in_logs(self):
        with _CaptureLogs() as cap:
            run(db.add_api_key(G1, "google_translate", GOOGLE_KEY))
            with db._conn() as conn:  # kaputter Ciphertext -> Fehler wird geloggt, aber ohne Key
                conn.execute("UPDATE api_keys SET guild_id = ?", (G2,))
            db._reload_guilds()
        self.assertTrue(any("nicht entschlüsselbar" in m for m in cap.messages))
        self.assertFalse(any(GOOGLE_KEY in m for m in cap.messages))


# ---------------------------------------------------------------------------
class WithoutMasterKeyTests(unittest.TestCase):
    """Ohne Master-Schlüssel: Bot startet, alter Google-Key läuft weiter, DB bleibt unverändert."""

    def test_legacy_mode(self):
        path = os.path.join(TMP, "legacy.db")
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE guild_configs (guild_id INTEGER PRIMARY KEY, google_api_key TEXT, "
                     "report_channel_id INTEGER, is_configured INTEGER DEFAULT 0)")
        conn.execute("INSERT INTO guild_configs VALUES (?, ?, NULL, 1)", (G1, GOOGLE_KEY))
        conn.commit()
        conn.close()
        script = textwrap.dedent(f"""
            import asyncio, sys
            sys.path.insert(0, {BOT_DIR!r})
            import database as db
            assert not db.crypto_available()
            assert db.get_guild_config({G1})[0] == {GOOGLE_KEY!r}
            assert asyncio.run(db.add_api_key({G1}, "mistral", "x" * 20))[0] == "no_crypto"
            assert db.usage_id({GOOGLE_KEY!r}) == db._legacy_hash({GOOGLE_KEY!r})
            print("OK")
        """)
        env = dict(os.environ, YATB_DB_FILE=path, YATB_MASTER_KEY_FILE=os.path.join(TMP, "missing"))
        res = subprocess.run([sys.executable, "-c", script], env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(res.returncode, 0, res.stderr[-2000:])
        self.assertIn("OK", res.stdout)
        self.assertNotIn(GOOGLE_KEY, res.stderr)
        conn = sqlite3.connect(path)
        self.assertEqual(conn.execute("SELECT google_api_key FROM guild_configs").fetchone()[0], GOOGLE_KEY)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM api_keys").fetchone()[0], 0)
        conn.close()


if __name__ == "__main__":
    unittest.main()
