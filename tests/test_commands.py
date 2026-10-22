"""
Tests für die Befehle in bot.py ohne Discord-Verbindung: Budget-Eingabe, Formularfelder pro Anbieter,
Opt-out (Speicherung + Kontext), Währung pro Key.
"""
import asyncio
import os
import sqlite3
import tempfile
import unittest

from _testenv import TMP

os.environ.setdefault("DISCORD_TOKEN", "")
import bot  # noqa: E402
import database as db  # noqa: E402
import providers as pv  # noqa: E402

GUILD = 515151515151515151


def run(coro):
    return asyncio.run(coro)


class BudgetParsingTests(unittest.TestCase):
    def test_valid(self):
        cases = {
            "8.50 EUR": (8.5, "EUR"), "8,5 €": (8.5, "EUR"), "€8,50": (8.5, "EUR"), "10 usd": (10.0, "USD"),
            "$10": (10.0, "USD"), "7": (7.0, "USD"), " 12.3 ": (12.3, "USD"), "": (None, None), "  ": (None, None),
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(bot.parse_budget(text, "USD"), expected)

    def test_default_currency(self):
        self.assertEqual(bot.parse_budget("5", "EUR"), (5.0, "EUR"))

    def test_invalid(self):
        for text in ("abc", "5 GBP", "1.234", "-5", "5000", "5 EUR EUR 3"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    bot.parse_budget(text, "USD")


class KeyFormTests(unittest.TestCase):
    def _form(self, pid, info=None):
        async def make():
            return bot.KeyForm(pv.PROVIDERS[pid], "en", info)
        return run(make())

    def _labels(self, form):
        return [child.text for child in form.children]

    def test_field_count_and_fields_per_provider(self):
        for pid in pv.PROVIDERS:
            with self.subTest(provider=pid):
                form = self._form(pid)
                self.assertLessEqual(len(form.children), 5)
                labels = self._labels(form)
                self.assertIn("API key", labels)
                self.assertEqual("Plan" in labels, pv.free_allowed(pv.PROVIDERS[pid]))
                self.assertEqual("Azure region" in labels, pid == "azure")

    def test_gemini_has_no_free_option(self):
        self.assertNotIn("Plan", self._labels(self._form("gemini")))

    def test_edit_form_has_no_key_field_but_limit(self):
        info = db.ApiKeyInfo(1, "azure", "main", "paid", True, "abcd", "2026-10-20", False, 8.5, "fp", "EUR", "westeurope")
        form = self._form("azure", info)
        labels = self._labels(form)
        self.assertNotIn("API key", labels)
        self.assertIn("Usage limit", labels)
        self.assertLessEqual(len(form.children), 5)
        budget = next(c for c in form.children if c.text.startswith("Monthly budget"))
        self.assertEqual(budget.component.default, "8.50 EUR")


class PrivacyTests(unittest.TestCase):
    def test_set_and_context_filter(self):
        run(db.set_local_only(111, True))
        run(db.set_local_only(222, False))
        self.assertTrue(db.is_local_only(111))
        self.assertFalse(db.is_local_only(222))
        self.assertFalse(db.is_local_only(None))
        buf = bot.ContextBuffer()
        key = (1, "chat", 0)
        buf.add(key, 10, "Alice: hello", 111)
        buf.add(key, 11, "Bob: hi", 222)
        buf.add(key, 12, "Alice: again", 111)
        self.assertEqual(buf.recent(key, 99, 222), ["Bob: hi"])
        self.assertEqual(buf.recent(key, 99, 111), [])              # Opt-out-Nutzer nie im KI-Kontext
        run(db.set_local_only(111, False))
        self.assertEqual(buf.recent(key, 99, 111), ["Alice: hello", "Alice: again"])   # nur eigene Nachrichten
        self.assertEqual(buf.recent(key, 12, 111), ["Alice: hello"])                   # nur frühere


class CurrencyTests(unittest.TestCase):
    def test_migration_sets_eur_for_operator_keys_once(self):
        fd, path = tempfile.mkstemp(suffix=".db", dir=TMP)
        os.close(fd)
        conn = sqlite3.connect(path)
        db._create_schema(conn)
        conn.execute("PRAGMA user_version = 3")
        for prov in ("mistral", "gemini", "google_translate"):
            conn.execute("INSERT INTO api_keys (guild_id, provider, secret_enc, fingerprint) VALUES (1, ?, 'x', ?)", (prov, prov))
        self.assertEqual(db._migrate_currency(conn), 2)
        rows = dict(conn.execute("SELECT provider, currency FROM api_keys"))
        self.assertEqual(rows, {"mistral": "EUR", "gemini": "EUR", "google_translate": None})
        conn.execute("UPDATE api_keys SET currency = 'USD' WHERE provider = 'mistral'")
        self.assertEqual(db._migrate_currency(conn), 0)               # nur einmal
        self.assertEqual(conn.execute("SELECT currency FROM api_keys WHERE provider='mistral'").fetchone()[0], "USD")
        conn.close()

    def test_key_with_currency_round_trip(self):
        with db._conn() as conn:
            conn.execute("DELETE FROM api_keys WHERE guild_id = ?", (GUILD,))
        status, info = run(db.add_api_key(GUILD, "mistral", "mistral-key-000000000000", "paid", "main", None, 1, 8.5, "EUR"))
        self.assertEqual((status, info.budget, info.currency), ("ok", 8.5, "EUR"))
        self.assertEqual(db.get_guild_keys(GUILD)[0].currency, "EUR")
        updated = run(db.update_api_key(GUILD, info.id, label="x", tier="paid", budget=None, currency=None, limit_enabled=False))
        self.assertEqual((updated.label, updated.budget, updated.currency, updated.limit_enabled), ("x", None, None, False))
        self.assertIn("EUR", bot._budget_text(info, pv.PROVIDERS["mistral"], "en"))



class ReactionCopiesTests(unittest.TestCase):
    """Zu jeder Fassung (Original oder Übersetzung) findet der Bot alle anderen - je Zielkanal den ersten Teil."""

    def test_copies_from_source_and_from_translation(self):
        gid, src, src_ch = 777, 9001, 501
        for target_msg, target_ch, thread, chunk in ((9101, 601, None, 0), (9102, 601, None, 1), (9201, 602, 7602, 0)):
            asyncio.run(db.save_message_mapping(src, src_ch, src_ch, target_msg, target_ch, thread, chunk, gid, "h"))
        expected = [(501, 9001), (601, 9101), (7602, 9201)]
        self.assertEqual(asyncio.run(bot.reaction_copies(src_ch, src)), expected)
        self.assertEqual(asyncio.run(bot.reaction_copies(601, 9102)), expected)    # Reaktion auf Teil 2 einer Übersetzung
        self.assertEqual(asyncio.run(bot.reaction_copies(7602, 9201)), expected)
        self.assertEqual(asyncio.run(bot.reaction_copies(501, 123)), [])            # nicht gespiegelt

    def test_add_reactions_is_a_required_permission(self):
        self.assertIn("add_reactions", bot.REQUIRED_PERMS)



class ChannelCountTests(unittest.TestCase):
    def test_counts_by_type(self):
        from unittest.mock import MagicMock

        def ch(cls, **flags):
            m = MagicMock(spec=cls)
            for name, value in flags.items():
                getattr(m, name).return_value = value
            return m
        guild = MagicMock()
        guild.channels = [ch(bot.discord.TextChannel, is_news=False), ch(bot.discord.TextChannel, is_news=True),
                          ch(bot.discord.VoiceChannel), ch(bot.discord.StageChannel), ch(bot.discord.CategoryChannel),
                          ch(bot.discord.ForumChannel, is_media=False), ch(bot.discord.ForumChannel, is_media=True)]
        self.assertEqual(bot.channel_counts(guild), {"text": 1, "news": 1, "voice": 1, "stage": 1, "forum": 1,
                                                     "media": 1, "category": 1})
        self.assertEqual(bot.CHANNEL_LIMIT, 500)



class ForumTagLinkTests(unittest.TestCase):
    def test_links_work_in_both_directions_and_are_replaced(self):
        run = asyncio.run
        run(db.save_tag_link(1, 100, 11, 200, 21))
        self.assertEqual(run(db.get_tag_link(100, 11, 200)), 21)
        self.assertEqual(run(db.get_tag_link(200, 21, 100)), 11)          # Rückrichtung
        self.assertIsNone(run(db.get_tag_link(100, 11, 300)))
        run(db.save_tag_link(1, 200, 21, 100, 12))                         # neu zugeordnet (Tag umbenannt/neu)
        self.assertEqual(run(db.get_tag_link(200, 21, 100)), 12)
        self.assertEqual(run(db.get_tag_link(100, 12, 200)), 21)

    def test_group_threads(self):
        run = asyncio.run
        run(db.register_thread(501, 100, 501, 1, "forum"))
        run(db.register_thread(502, 200, 501, 1, "forum"))
        self.assertEqual(sorted(run(db.group_threads(501))), [(501, 100), (502, 200)])

    def test_forum_and_text_are_bridgeable(self):
        self.assertTrue(bot.is_forum(bot.discord.utils.MISSING) is False)
        self.assertIn(bot.discord.ForumChannel, bot.BRIDGEABLE)


if __name__ == "__main__":
    unittest.main()
