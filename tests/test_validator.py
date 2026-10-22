"""
Tests für validator.py: echte Fehlerbilder aus Benchmark und Markdown-Tests müssen erkannt werden,
korrekte Übersetzungen dürfen nicht verworfen werden.
"""
import unittest

from _testenv import BOT_DIR  # noqa: F401

import e2e_messages  # noqa: E402
import validator as v  # noqa: E402

GOOD = [
    ("**Double XP weekend** starts *Friday*!", "**Doppel-XP-Wochenende** startet am *Freitag*!"),
    ("# Season 12\n## What's new\n- Faster mining\n- New ships\n\nLLAP\nThe Dev Team",
     "# Saison 12\n## Was ist neu\n- Schnelleres Mining\n- Neue Schiffe\n\nLLAP\nDas Dev-Team"),
    ("Read the [patch notes](https://example.com/p) now", "Lies jetzt die [Patchnotes](https://example.com/p)"),
    ("~~Old reward~~ new reward ||secret||", "~~Alte Belohnung~~ neue Belohnung ||Geheimnis||"),
    ("gg", "gg"),
    ("Fuel costs 5\\*3, \\*not italic\\*", "Treibstoff kostet 5\\*3, \\*nicht kursiv\\*"),
    ("> Quote\n> second line\n\nText", "> Zitat\n> zweite Zeile\n\nText"),
]
BAD = [  # (Original, kaputte Übersetzung, erwarteter Grund)
    ("**Important:** read this", "Wichtig: lies das", "bold"),
    ("Read the [notes](https://example.com/a)", "Lies die [](https://example.com/a) Notizen [x](https://example.com/a)", "links"),
    ("The ||boss|| spawns", "Der Boss erscheint", "spoiler"),
    ("__Don't__ forget", "Vergiss nicht", "underline"),
    ("Fuel \\*not italic\\*", "Treibstoff *nicht kursiv*", "italic"),
    ("- one\n- two\n- three", "- eins\n- zwei drei", "lists"),
    ("1. one\n2. two", "1. eins zwei", "numbered"),
    ("LLAP\nThe Dev Team", "Lebe lang und in Frieden\nDas Dev-Team", "llap"),
    ("Hello everyone", "", "empty"),
    ("Hello everyone, nice day", "Here is the translation: Hallo zusammen, schöner Tag", "commentary"),
    ("Hello everyone, nice day", "<think>hmm</think>Hallo zusammen", "commentary"),
    ("A long message about the next armada and the territory rules.", "Hallo", "length"),
    ("Para one.\n\nPara two.\n\nPara three.\n\nPara four.", "Absatz eins. Absatz zwei. Absatz drei. Absatz vier.", "paragraphs"),
    ("> quote", "Zitat", "quotes"),
    ("# Title\ntext", "Titel\nText", "headers"),
    ("Text\n```\nrules\n```", "Text\nRegeln", "fences"),
    ("See https://example.com/x", "Siehe https://example.com/y", "urls"),
    ("Read [notes](https://e.com/a)", "Lies [Notizen](](https://e.com/a))", "links"),
]


class ValidatorTests(unittest.TestCase):
    def test_good_translations_pass(self):
        for src, out in GOOD:
            with self.subTest(src=src[:30]):
                self.assertEqual(v.problems(src, out), [])

    def test_bad_translations_are_rejected(self):
        for src, out, reason in BAD:
            with self.subTest(reason=reason):
                self.assertIn(reason, v.problems(src, out))

    def test_identity_passes_for_all_test_messages(self):
        for name, _kind, text, *_ in e2e_messages.MESSAGES:
            with self.subTest(name=name):
                self.assertEqual(v.problems(text, text), [])

    def test_one_emphasis_tolerated_only_in_heavily_formatted_messages(self):
        many = "\n".join(f"- Rule {i}: be **nice** always." for i in range(5))   # 5 Fettungen
        dropped = many.replace("**nice**", "nice", 1)
        self.assertEqual(v.problems(many, dropped), [])
        self.assertIn("bold", v.problems(many, many.replace("**nice**", "nice", 2)))   # zwei fehlen
        self.assertIn("bold", v.problems(many, many.replace("**nice**", "**nice", 1)))  # unausgeglichen
        few = "Be **nice** and **calm**."
        self.assertIn("bold", v.problems(few, "Sei nett und **ruhig**."))           # wenige: streng
        spoil = "\n".join(f"- Tip {i}: ||secret|| here." for i in range(5))
        self.assertIn("spoiler", v.problems(spoil, spoil.replace("||secret||", "secret", 1)))

    def test_lenient_mode_for_last_engine(self):
        self.assertEqual(v.problems("**Important:** read", "Wichtig: lies", strict=False), [])
        self.assertEqual(v.problems("Hello", "  ", strict=False), ["empty"])


if __name__ == "__main__":
    unittest.main()
