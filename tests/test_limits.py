"""
Tests: Anbieter-Konfiguration, Limit-Engine, Aufruf-Statistik.

Läuft ohne Netzwerk (Engines werden durch Attrappen ersetzt):
    python -m unittest discover -s tests -v
"""
import asyncio
import datetime
import json
import os
import sqlite3
import tempfile
import time
import unittest

from _testenv import TMP  # noqa: F401  (setzt Umgebung vor den Bot-Imports)

import database as db  # noqa: E402
import limits  # noqa: E402
import providers as pv  # noqa: E402
import stats  # noqa: E402

UTC = datetime.timezone.utc


def run(coro):
    return asyncio.run(coro)


def key(fp: str, tier: str = "free", limit_enabled: bool = True, budget=None, key_id: int = 1) -> db.KeyRuntime:
    return db.KeyRuntime(key_id, "test", "secret-not-used", fp, tier, limit_enabled, budget, None)


AI = pv.Provider(
    "groq", "Groq", "openai", base_url="https://example.invalid/v1", model="m",
    price_in=1.0, price_out=2.0, currency="USD",
    limits_free=pv.Limits(rpm=2, rpd=3, tpm=100, tpd=150),
    limits_paid=pv.Limits(budget_month=1.0),
)
CHARS = pv.Provider(
    "google_translate", "Google Translate", "google", price_chars=20.0,
    limits_free=pv.Limits(chars_month=1000), limits_paid=pv.Limits(budget_month=5.0),
)


# ---------------------------------------------------------------------------
class ConfigTests(unittest.TestCase):
    def _cfg(self, **over):
        entry = {"name": "Mistral", "kind": "openai", "group": "B", "base_url": "https://api.mistral.ai/v1",
                 "model": "m", "price_in": 1.5, "price_out": 7.5, "limits": {"free": {"rpm": 10}, "paid": {"budget_month": 8.5}}}
        entry.update(over)
        return {"providers": {"mistral": entry}}

    def test_repo_config_is_valid(self):
        """Die mitgelieferte config/providers.toml muss fehlerfrei sein."""
        import tomllib
        with open(pv.CONFIG_FILE, "rb") as fh:
            providers, errors = pv.parse_config(tomllib.load(fh))
        self.assertEqual(errors, [])
        self.assertTrue({"gemini", "mistral", "groq", "novita", "google_translate", "azure"} <= set(providers))
        self.assertEqual(providers["google_translate"].limits_free.chars_month, 500000)
        self.assertFalse(providers["novita"].free_available)
        self.assertFalse(providers["gemini"].eea_free_allowed)
        self.assertEqual(providers["groq"].extra, {"reasoning_effort": "none"})

    def test_valid_entry(self):
        providers, errors = pv.parse_config(self._cfg())
        self.assertEqual(errors, [])
        p = providers["mistral"]
        self.assertEqual((p.group, p.limits_free.rpm, p.limits_paid.budget_month), ("B", 10, 8.5))
        self.assertAlmostEqual(p.cost(tokens_in=1_000_000, tokens_out=1_000_000), 9.0)

    def test_invalid_entries_are_skipped(self):
        cases = [
            {"kind": "magic"},                              # unbekannte Art
            {"name": ""},                                   # Name fehlt
            {"base_url": None},                             # Pflicht bei openai
            {"base_url": "http://unsicher.example"},        # kein https
            {"price_in": -1},                               # negative Zahl
            {"price_in": "1.5"},                            # Text statt Zahl
            {"group": "Z"},
            {"limits": {"free": {"rpm": 1.5}}},             # keine ganze Zahl
            {"limits": {"free": {"foo": 1}}},               # unbekanntes Limit
            {"limits": {"gold": {}}},                       # unbekannte Stufe
            {"typo_field": 1},                              # unbekanntes Feld
            {"enabled": "yes"},
        ]
        for over in cases:
            with self.subTest(over=over):
                cfg = self._cfg(**over)
                if over.get("base_url", "x") is None:
                    del cfg["providers"]["mistral"]["base_url"]
                providers, errors = pv.parse_config(cfg)
                self.assertNotIn("mistral", providers)
                self.assertTrue(errors)

    def test_broken_or_missing_file_falls_back_to_builtin(self):
        path = os.path.join(TMP, "broken.toml")
        with open(path, "w") as fh:
            fh.write("[providers.x\nname = ")
        for p in (path, os.path.join(TMP, "missing.toml")):
            with self.assertLogs("yatb.providers", level="ERROR"):
                providers = pv.load_providers(p)
            self.assertEqual(set(providers), {"google_translate", "azure"})
            self.assertEqual(providers["google_translate"].limits_free.chars_month, 500000)


# ---------------------------------------------------------------------------
class CachedPriceTests(unittest.TestCase):
    def test_cached_tokens_use_cached_price(self):
        p = pv.Provider("x", "X", "openai", price_in=1.0, price_cached=0.1, price_out=2.0)
        self.assertAlmostEqual(p.cost(tokens_in=1000, tokens_out=100), (1000 * 1.0 + 100 * 2.0) / 1e6)
        self.assertAlmostEqual(p.cost(tokens_in=1000, tokens_out=100, tokens_cached=600),
                               (400 * 1.0 + 600 * 0.1 + 100 * 2.0) / 1e6)
        self.assertAlmostEqual(p.cost(tokens_in=100, tokens_cached=500), 100 * 0.1 / 1e6)   # nie mehr als tokens_in

    def test_without_cached_price_cached_tokens_cost_full(self):
        p = pv.Provider("x", "X", "openai", price_in=1.0, price_out=2.0)
        self.assertAlmostEqual(p.cost(tokens_in=1000, tokens_cached=600), 1000 * 1.0 / 1e6)

    def test_usage_passes_cached_tokens(self):
        p = pv.Provider("x", "X", "openai", price_in=1.0, price_cached=0.1)
        self.assertAlmostEqual(limits.cost_of(p, "paid", limits.Usage(tokens_in=1000, tokens_cached=1000)), 0.0001)
        self.assertEqual(limits.cost_of(p, "free", limits.Usage(tokens_in=1000, tokens_cached=1000)), 0.0)

    def test_config_reads_price_cached(self):
        provs, errors = pv.parse_config({"providers": {"mistral": {"name": "M", "kind": "openai", "group": "B",
                                         "base_url": "https://x", "model": "m", "price_in": 0.1275,
                                         "price_cached": 0.01275, "price_out": 0.51, "currency": "EUR"}}})
        self.assertEqual(errors, [])
        self.assertEqual((provs["mistral"].price_cached, provs["mistral"].currency), (0.01275, "EUR"))


class LimitTests(unittest.TestCase):
    def setUp(self):
        limits.reset_window()

    def test_periods_are_utc(self):
        berlin_0130 = datetime.datetime(2026, 10, 20, 1, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=2)))
        self.assertEqual(limits.periods(berlin_0130), ("2026-10-19", "2026-10"))  # = 23:30 UTC am 19.

    def test_rpm_and_tpm(self):
        k = key("fp-rpm")
        self.assertIsNone(run(limits.check(k, AI, limits.Usage(requests=1, tokens_in=10))))
        run(limits.record(k, AI, limits.Usage(requests=2, tokens_in=50)))
        self.assertEqual(run(limits.check(k, AI, limits.Usage(requests=1))), "rpm")
        limits.reset_window()
        run(limits.record(key("fp-tpm"), AI, limits.Usage(requests=1, tokens_in=90)))
        self.assertEqual(run(limits.check(key("fp-tpm"), AI, limits.Usage(requests=1, tokens_in=20))), "tpm")

    def test_daily_limits_reset_at_utc_midnight(self):
        k = key("fp-rpd")
        late = datetime.datetime(2026, 10, 19, 23, 59, tzinfo=UTC)
        run(limits.record(k, AI, limits.Usage(requests=3, tokens_in=10), now=late))
        limits.reset_window()
        self.assertEqual(run(limits.check(k, AI, limits.Usage(requests=1), now=late)), "rpd")
        # 01:30 Berliner Zeit am 20. ist noch der 19. in UTC -> weiter gesperrt
        berlin = datetime.datetime(2026, 10, 20, 1, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=2)))
        self.assertEqual(run(limits.check(k, AI, limits.Usage(requests=1), now=berlin)), "rpd")
        self.assertIsNone(run(limits.check(k, AI, limits.Usage(requests=1), now=late + datetime.timedelta(minutes=1))))

    def test_tpd(self):
        k = key("fp-tpd")
        now = datetime.datetime(2026, 10, 19, 12, tzinfo=UTC)
        run(limits.record(k, AI, limits.Usage(requests=1, tokens_in=70, tokens_out=70), now=now))
        limits.reset_window()
        self.assertEqual(run(limits.check(k, AI, limits.Usage(requests=1, tokens_in=20), now=now)), "tpd")

    def test_chars_month_and_warnings_once(self):
        k = key("fp-chars")
        now = datetime.datetime(2026, 10, 19, 12, tzinfo=UTC)
        self.assertEqual(run(limits.record(k, CHARS, limits.Usage(requests=1, chars=899), now=now)), [])
        self.assertEqual(run(limits.record(k, CHARS, limits.Usage(requests=1, chars=2), now=now)), ["warn_90"])
        self.assertEqual(run(limits.record(k, CHARS, limits.Usage(requests=1, chars=49), now=now)), ["warn_95"])
        self.assertEqual(run(limits.record(k, CHARS, limits.Usage(requests=1, chars=50), now=now)), ["warn_100"])
        self.assertEqual(run(limits.record(k, CHARS, limits.Usage(requests=1, chars=5), now=now)), [])  # nur einmal
        self.assertEqual(run(limits.check(k, CHARS, limits.Usage(chars=1), now=now)), "month_exhausted")
        # neuer Monat: wieder frei, Warnstufen neu
        nov = datetime.datetime(2026, 11, 1, 0, 0, tzinfo=UTC)
        self.assertIsNone(run(limits.check(k, CHARS, limits.Usage(chars=1), now=nov)))
        self.assertEqual(run(limits.record(k, CHARS, limits.Usage(requests=1, chars=950), now=nov)), ["warn_90", "warn_95"])

    def test_long_message_falls_back_short_ones_keep_using_the_rest(self):
        """10 % Rest: die lange Nachricht weicht aus (keine Meldung), kurze nutzen den Key weiter."""
        k = key("fp-rest")
        now = datetime.datetime(2026, 10, 19, 12, tzinfo=UTC)
        run(limits.record(k, CHARS, limits.Usage(requests=1, chars=900), now=now))      # 90 %
        reason = run(limits.check(k, CHARS, limits.Usage(chars=300), now=now))
        self.assertEqual(reason, "chars_month")
        self.assertEqual(run(limits.on_blocked(k, CHARS, reason, now=now)), [])           # kein "Limit erreicht"
        self.assertIsNone(run(limits.check(k, CHARS, limits.Usage(chars=60), now=now)))  # kurze Nachricht: Key nutzen
        run(limits.record(k, CHARS, limits.Usage(requests=1, chars=60), now=now))

    def test_exhausted_below_one_percent_reports_once_and_blocks(self):
        k = key("fp-exhausted")
        now = datetime.datetime(2026, 10, 19, 12, tzinfo=UTC)
        run(limits.record(k, CHARS, limits.Usage(requests=1, chars=995), now=now))      # 0,5 % Rest
        reason = run(limits.check(k, CHARS, limits.Usage(chars=1), now=now))
        self.assertEqual(reason, "month_exhausted")                                       # auch die kleinste Anfrage
        self.assertEqual(run(limits.on_blocked(k, CHARS, reason, now=now)), ["warn_100"])  # 90/95 schon bei record()
        self.assertEqual(run(limits.on_blocked(k, CHARS, reason, now=now)), [])            # nur einmal pro Monat
        self.assertEqual(run(limits.check(k, CHARS, limits.Usage(chars=1), now=now)), "month_exhausted")
        self.assertEqual(run(limits.on_blocked(k, CHARS, "rpm", now=now)), [])              # Minutenlimit: nie melden
        self.assertEqual(run(limits.on_blocked(k, CHARS, "chars_month", now=now)), [])      # nur diese Anfrage zu groß
        nov = datetime.datetime(2026, 11, 1, tzinfo=UTC)
        self.assertIsNone(run(limits.check(k, CHARS, limits.Usage(chars=1), now=nov)))      # neuer Monat: frei

    def test_several_levels_in_one_step(self):
        crossed = run(limits.record(key("fp-jump"), CHARS, limits.Usage(requests=1, chars=5000)))
        self.assertEqual(crossed, ["warn_90", "warn_95", "warn_100"])

    def test_paid_budget(self):
        now = datetime.datetime(2026, 10, 19, 12, tzinfo=UTC)
        k = key("fp-paid", tier="paid")
        run(limits.record(k, AI, limits.Usage(requests=1, tokens_in=400_000, tokens_out=250_000), now=now))  # 0.9 USD
        _d, month, ms = run(limits.monthly_status("fp-paid", AI, "paid", None, now=now))
        self.assertAlmostEqual(month.cost, 0.9)
        self.assertEqual((ms.kind, ms.limit), ("cost", 1.0))
        self.assertEqual(run(limits.check(k, AI, limits.Usage(requests=1, tokens_in=200_000), now=now)), "budget_month")
        own_budget = key("fp-paid", tier="paid", budget=10.0)  # eigenes Budget pro Server
        self.assertIsNone(run(limits.check(own_budget, AI, limits.Usage(requests=1, tokens_in=200_000), now=now)))

    def test_raising_the_budget_unpauses_the_key(self):
        """Erschöpft ist kein Merker: erhöht der Admin das Budget, ist der Key sofort wieder nutzbar."""
        now = datetime.datetime(2026, 10, 19, 12, tzinfo=UTC)
        k = key("fp-raise", tier="paid")
        run(limits.record(k, AI, limits.Usage(requests=1, tokens_in=1_000_000), now=now))  # 1.0 von 1.0 USD
        reason = run(limits.check(k, AI, limits.Usage(requests=1, tokens_in=10), now=now))
        self.assertEqual(reason, "month_exhausted")
        run(limits.on_blocked(k, AI, reason, now=now))                                       # Warnstufen gesetzt
        raised = key("fp-raise", tier="paid", budget=5.0)
        self.assertIsNone(run(limits.check(raised, AI, limits.Usage(requests=1, tokens_in=10), now=now)))

    def test_free_costs_nothing(self):
        now = datetime.datetime(2026, 10, 19, 12, tzinfo=UTC)
        run(limits.record(key("fp-free-cost"), AI, limits.Usage(requests=1, tokens_in=1000), now=now))
        _d, month, _ms = run(limits.monthly_status("fp-free-cost", AI, "free", None, now=now))
        self.assertEqual((month.requests, month.tokens_in, month.cost), (1, 1000, 0.0))

    def test_limit_off_never_blocks(self):
        k = key("fp-off", limit_enabled=False)
        run(limits.record(k, CHARS, limits.Usage(requests=1, chars=5000)))
        self.assertIsNone(run(limits.check(k, CHARS, limits.Usage(chars=1))))

    def test_shared_key_counts_together(self):
        now = datetime.datetime(2026, 10, 19, 12, tzinfo=UTC)
        server_a, server_b = key("fp-shared", key_id=1), key("fp-shared", key_id=2)
        run(limits.record(server_a, AI, limits.Usage(requests=3, tokens_in=10), now=now))
        limits.reset_window()
        self.assertEqual(run(limits.check(server_b, AI, limits.Usage(requests=1), now=now)), "rpd")
        # Stufe gilt pro Server: als Bezahl-Key gibt es kein Tageslimit
        self.assertIsNone(run(limits.check(key("fp-shared", tier="paid", key_id=2), AI, limits.Usage(requests=1), now=now)))

    def test_cleanup_keeps_month_rows(self):
        old = datetime.datetime.now(UTC) - datetime.timedelta(days=60)
        run(limits.record(key("fp-clean"), AI, limits.Usage(requests=1), now=old))
        run(db.cleanup_key_usage(40))
        with db._conn() as conn:
            periods = [r[0] for r in conn.execute("SELECT period FROM key_usage WHERE fingerprint = 'fp-clean'")]
        self.assertEqual(periods, [old.strftime("%Y-%m")])


class UsageMigrationTests(unittest.TestCase):
    def test_google_usage_migrated_once(self):
        fd, path = tempfile.mkstemp(suffix=".db", dir=TMP)
        os.close(fd)
        conn = sqlite3.connect(path)
        db._create_schema(conn)
        conn.execute("INSERT INTO google_api_usage (key_hash, year_month, chars_used, warn_90) VALUES ('fp-old', '2026-10', 31226, 0)")
        self.assertEqual(db._migrate_google_usage(conn), 1)
        self.assertEqual(conn.execute("SELECT fingerprint, period, chars, requests FROM key_usage").fetchall(),
                         [("fp-old", "2026-10", 31226, 0)])
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], db.SCHEMA_VERSION)
        conn.execute("UPDATE google_api_usage SET chars_used = 99999")
        self.assertEqual(db._migrate_google_usage(conn), 0)  # nur einmal
        self.assertEqual(conn.execute("SELECT chars FROM key_usage").fetchone()[0], 31226)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM google_api_usage").fetchone()[0], 1)  # bleibt für Rollback
        conn.close()


# ---------------------------------------------------------------------------
class StatsTests(unittest.TestCase):
    def setUp(self):
        stats.init()
        with stats._conn() as conn:
            conn.execute("DELETE FROM calls")
            conn.execute("DELETE FROM daily")

    def test_no_text_columns(self):
        with stats._conn() as conn:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(calls)")}
        self.assertFalse(cols & {"text", "content", "message", "user", "user_id", "author"})
        self.assertEqual(cols - {"id"}, set(stats._COLUMNS))

    def test_record_flush_aggregate_retention(self):
        today = datetime.date(2026, 10, 19)
        yesterday = datetime.datetime(2026, 10, 18, 12, tzinfo=UTC).timestamp()
        ancient = datetime.datetime(2026, 7, 1, 12, tzinfo=UTC).timestamp()
        for ms in (100, 200, 300, 400, 1000):
            stats.record(guild_id=1, provider="google_translate", model="translate-v2", outcome="ok",
                         chars=10, duration_ms=ms, key_fp="a" * 64, ts=yesterday)
        stats.record(guild_id=1, provider="google_translate", model="translate-v2", outcome="rate_limited",
                     fell_through=True, duration_ms=5, ts=yesterday)
        stats.record(guild_id=1, provider="libre", model="libretranslate", outcome="weird", ts=yesterday)
        stats.record(guild_id=2, provider="libre", model="libretranslate", outcome="ok", duration_ms=50, ts=ancient)
        run(stats.flush())
        self.assertEqual(stats._pending, [])
        with stats._conn() as conn:
            fps = {r[0] for r in conn.execute("SELECT key_fp FROM calls WHERE key_fp IS NOT NULL")}
            outcomes = {r[0] for r in conn.execute("SELECT outcome FROM calls")}
        self.assertEqual(fps, {"a" * stats.FP_PREFIX})       # Fingerprint gekürzt
        self.assertIn("error", outcomes)                       # unbekannte Klasse -> error

        added, deleted = stats.aggregate(today=today.isoformat())
        self.assertEqual((added, deleted), (3, 1))             # 2 Gruppen gestern + 1 Gruppe im Juli; Juli-Rohdaten weg
        with stats._conn() as conn:
            row = conn.execute("""SELECT calls, ok, fell_through, outcomes, chars, p50_ms, p95_ms FROM daily
                                  WHERE day = '2026-10-18' AND provider = 'google_translate'""").fetchone()
            self.assertEqual(row[:3], (6, 5, 1))
            self.assertEqual(json.loads(row[3]), {"ok": 5, "rate_limited": 1})
            self.assertEqual((row[4], row[5], row[6]), (50, 300, 1000))
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM daily WHERE day = '2026-07-01'").fetchone()[0], 1)
        self.assertEqual(stats.aggregate(today=today.isoformat()), (0, 0))  # idempotent

    def test_today_is_not_aggregated(self):
        stats.record(guild_id=1, provider="libre", model="x", outcome="ok")
        run(stats.flush())
        self.assertEqual(stats.aggregate()[0], 0)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    unittest.main()
