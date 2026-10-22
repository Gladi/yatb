"""
Tests für locales.py / locales_mt.py: Vollständigkeit, Platzhalter, Befehlsbeschreibungen.
"""
import os
import re
import string
import unittest

from _testenv import BOT_DIR

import locales  # noqa: E402

LANGS = ("en", "de", "fr", "es", "it", "ru", "nl")


def fields(text: str):
    return sorted(f for _, f, _, _ in string.Formatter().parse(text) if f)


class LocaleTests(unittest.TestCase):
    def setUp(self):
        self.src = open(os.path.join(BOT_DIR, "bot.py"), encoding="utf-8").read()

    def test_all_languages_present(self):
        for lang in LANGS:
            self.assertIn(lang, locales.MESSAGES, lang)
            self.assertGreater(len(locales.MESSAGES[lang]), 100, lang)

    def test_placeholders_match_english(self):
        en = locales.MESSAGES["en"]
        for lang in LANGS[1:]:
            for key, text in locales.MESSAGES[lang].items():
                with self.subTest(lang=lang, key=key):
                    self.assertIn(key, en, "Schlüssel gibt es auf Englisch nicht")
                    self.assertEqual(fields(text), fields(en[key]))
                    self.assertEqual(text.count("`"), en[key].count("`"))

    def test_keys_used_in_code_exist(self):
        used = set(re.findall(r'tx\([^,()]+(?:\([^)]*\))?,\s*"([a-z0-9_]+)"', self.src))
        used |= set(re.findall(r"tx\([^,()]+,\s*'([a-z0-9_]+)'", self.src))
        used |= {f"guide_{p}" for p in ("gemini", "mistral", "groq", "novita", "google_translate", "azure")}
        used |= {f"info_f{i}_{x}" for i in range(1, 6) for x in ("name", "val")}
        used |= {f"channels_type_{k}" for k in ("text", "news", "voice", "stage", "forum", "media", "category")}
        used = {k for k in used if not k.endswith("_")}   # dynamische Präfixe ("channels_type_" + k)
        missing = sorted(k for k in used if k not in locales.MESSAGES["en"])
        self.assertEqual(missing, [])

    def test_every_command_description_is_translated(self):
        descs = {d for d in re.findall(r'description="([^"]+)"', self.src) if len(d) > 3}
        for block in re.findall(r"@app_commands\.describe\((.*?)\)\n", self.src, re.S):
            descs |= set(re.findall(r'=\s*"([^"]+)"', block))
        for lang in LANGS[1:]:
            with self.subTest(lang=lang):
                self.assertEqual(sorted(d for d in descs if locales.command_text(lang, d) is None), [])
                self.assertTrue(all(len(t) <= 100 for t in locales.COMMANDS[lang].values()))

    def test_lookup_and_fallback(self):
        self.assertEqual(locales.get_text("de", "keys_on"), "an")
        self.assertEqual(locales.get_text("en-US", "keys_on"), "on")
        self.assertEqual(locales.get_text("ja", "keys_on"), "on")              # unbekannte Sprache -> Englisch
        self.assertEqual(locales.get_text("de", "keys_removed", desc="X"), "🗑️ Key entfernt: X.")
        self.assertIsNone(locales.command_text("ja", "Key to change"))


if __name__ == "__main__":
    unittest.main()
