"""
Tests für markup.py: Code-Erkennung, Platzhalter (inkl. Leerzeichen), Markdown <-> HTML.
    python -m unittest discover -s tests -v
"""
import unittest

from _testenv import BOT_DIR  # noqa: F401  (setzt Umgebung vor den Bot-Imports)

import e2e_messages  # noqa: E402
import markup as mu  # noqa: E402

CODE_BLOCKS = [  # (Inhalt, Sprachangabe) -> muss als Code erkannt werden
    ('{"error": "0x8007", "server": "EU-3", "retry": true}', "json"),
    ('{"error": "0x8007", "server": "EU-3"}', ""),                           # JSON ohne Sprachangabe
    ("def reward(level):\n    if level > 60:\n        return 50\n    return 0", ""),
    ("for (let i = 0; i < 10; i++) {\n  console.log(i);\n}", ""),
    ("SELECT name, power FROM players WHERE alliance = 'NOVA';", ""),
    ("pip install discord.py\npython bot.py", ""),
    ("x = 5\ny = x * 2", ""),
    ("Traceback (most recent call last):\n  File \"bot.py\", line 12, in <module>\n    main()", ""),
    ("docker compose up -d --build bot", "sh"),
    ("#include <stdio.h>\nint main() { return 0; }", "c"),
    ("<div class=\"title\">Hello</div>", "html"),
    ("player_power = base_power * multiplier", ""),
    ("", ""),
]
TEXT_BLOCKS = [  # Formatierung -> muss als Text erkannt (übersetzt) werden
    ("PLAYER COUNCIL - VOTING RESULTS\n\nTotal: 1,214 votes\n\n 1. Kael [S12]            - 231 votes (19.0%)\n"
     " 2. Mirra (S40 Ops70)     - 198 votes (16.3%)\n\nThe top 3 join the council next month.\n", ""),
    ("ALLIANCE RULES\n1. Be respectful to everyone.\n2. Join the armada when you are online.\n3. Never hit allied miners.\n", ""),
    ("Welcome to the alliance! Please read the rules and say hi in chat.", ""),
    ("+ Armada reward increased\n- Mining speed reduced for level 40 and below\n", "diff"),   # Farb-Trick
    ("IMPORTANT: Maintenance starts tomorrow at noon. Please log out before.", "fix"),       # Farb-Trick
    ("Weekly schedule\nMonday: armada training\nWednesday: territory defense\nSunday: mining event", ""),
    ("Thanks everyone for the great season, see you all in the next one!", "yaml"),        # Tag ist nur ein Hinweis
]
CODE_INLINE = ["/redeem SPACE2026", "SPACE2026", "config.json", "git pull origin main", "x = 5", "!help",
               "player_power", "0x8007", "/yatb keys add", "print(level)"]
TEXT_INLINE = ["read the rules first", "Double XP weekend", "be online at 20 ST", "this is important"]


class CodeDetectionTests(unittest.TestCase):
    def test_code_blocks(self):
        for content, lang in CODE_BLOCKS:
            with self.subTest(content=content[:40], lang=lang):
                self.assertTrue(mu.looks_like_code(content, lang))

    def test_text_blocks(self):
        for content, lang in TEXT_BLOCKS:
            with self.subTest(content=content[:40], lang=lang):
                self.assertFalse(mu.looks_like_code(content, lang))

    def test_matches_e2e_expectations(self):
        """Die Code-Erkennung muss die festen Erwartungen der e2e-Testnachrichten erfüllen."""
        for entry in e2e_messages.MESSAGES:
            if len(entry) < 4:
                continue
            name, _kind, text, expect = entry
            blocks = list(mu.FENCE_RE.finditer(text))
            for want, m in zip(expect.get("blocks", []), blocks):
                with self.subTest(name=name, block=m.group(3)[:30]):
                    self.assertEqual(mu.looks_like_code(m.group(3), m.group(1)), want == "keep")
            inline = list(mu.INLINE_CODE_RE.finditer(mu.FENCE_RE.sub("", text)))
            for want, m in zip(expect.get("inline", []), inline):
                with self.subTest(name=name, inline=m.group(1)):
                    self.assertEqual(mu.looks_like_code(m.group(1), inline=True), want == "keep")

    def test_inline(self):
        for content in CODE_INLINE:
            with self.subTest(code=content):
                self.assertTrue(mu.looks_like_code(content, inline=True))
        for content in TEXT_INLINE:
            with self.subTest(text=content):
                self.assertFalse(mu.looks_like_code(content, inline=True))


class PrepareRestoreTests(unittest.TestCase):
    def test_round_trip_all_test_messages(self):
        """Ohne Übersetzung muss jede Nachricht exakt wiederhergestellt werden."""
        texts = [e[2] for e in e2e_messages.MESSAGES] + [e2e_messages.LIMIT_LONG] + e2e_messages.LIMIT_SHORT
        for text in texts:
            with self.subTest(text=text[:40]):
                prep = mu.prepare(text)
                out, ok = mu.restore(prep.masked, prep)
                self.assertTrue(ok)
                self.assertEqual(out, text)

    def test_protected_elements(self):
        text = ("@everyone <@123> in <#456> at <t:1893456000:F> use </yatb info:789> <:yatb:111> "
                "see [notes](https://example.com/a) <https://example.com/b> https://example.com/c \\*not\\* LLAP")
        prep = mu.prepare(text)
        self.assertFalse(prep.has_text() and any(x in prep.masked for x in ("<@", "<#", "<t:", "http", "LLAP", "\\*")))
        self.assertIn("notes", prep.masked)  # Link-Text wird übersetzt, nur das Ziel ist geschützt

    def test_prose_code_block_is_translated_code_block_is_not(self):
        text = "Rules:\n```\nBe nice to everyone.\nJoin the armada daily.\n```\nand\n```json\n{\"a\": 1}\n```"
        prep = mu.prepare(text)
        self.assertIn("Be nice to everyone.", prep.masked)
        self.assertNotIn('"a": 1', prep.masked)
        translated = prep.masked.replace("Be nice to everyone.", "Seid nett zu allen.").replace("Join the armada daily.", "Macht täglich bei der Armada mit.")
        out, ok = mu.restore(translated, prep)
        self.assertTrue(ok)
        self.assertIn("```\nSeid nett zu allen.\nMacht täglich bei der Armada mit.\n```", out)
        self.assertIn('```json\n{"a": 1}\n```', out)

    def test_inline_prose_and_command(self):
        prep = mu.prepare("Type `/redeem SPACE2026` and `read the rules first` please")
        self.assertIn("read the rules first", prep.masked)
        self.assertNotIn("/redeem", prep.masked)
        out, ok = mu.restore(prep.masked.replace("read the rules first", "lies zuerst die Regeln"), prep)
        self.assertTrue(ok)
        self.assertEqual(out, "Type `/redeem SPACE2026` and `lies zuerst die Regeln` please")

    def test_lost_spaces_are_restored(self):
        prep = mu.prepare("<@123> please run `/reset` before <t:1893456000:t> and read [notes](https://e.com/x) now")
        tok = {ph.original: t for t, ph in prep.placeholders.items()}
        # Engine (z. B. Libre) verschluckt alle Leerzeichen um die Platzhalter
        engine = (f"{tok['<@123>']}bitte{tok['`/reset`']}vor{tok['<t:1893456000:t>']}ausführen "
                  f"und lies [Notizen{tok['](https://e.com/x)']}jetzt")
        out, ok = mu.restore(engine, prep)
        self.assertTrue(ok)
        self.assertEqual(out, "<@123> bitte `/reset` vor <t:1893456000:t> ausführen und lies [Notizen](https://e.com/x) jetzt")

    def test_ai_wrapped_link_placeholder_in_brackets(self):
        prep = mu.prepare("Read the [patch notes](https://example.com/p) now")
        tok = next(t for t, ph in prep.placeholders.items() if ph.original.startswith("]("))
        for engine in (f"Lee las [notas del parche]({tok}) ahora", f"Lee las [notas del parche]( {tok} ) ahora",
                       f"Lee las [notas del parche {tok} ahora"):
            with self.subTest(engine=engine):
                out, ok = mu.restore(engine, prep)
                self.assertTrue(ok)
                self.assertEqual(out, "Lee las [notas del parche](https://example.com/p) ahora")

    def test_no_space_added_before_punctuation(self):
        prep = mu.prepare("Thanks <@123> !")
        out, ok = mu.restore(prep.masked.replace("Thanks", "Danke").replace(" !", ", danke!"), prep)
        self.assertEqual(out, "Danke <@123>, danke!")

    def test_lost_placeholder_is_detected(self):
        prep = mu.prepare("hi <@123> there")
        self.assertFalse(mu.restore("hallo da", prep)[1])

    def test_lead_mention_line(self):
        prep = mu.prepare("@everyone\n\nCommanders, the event starts!")
        self.assertNotIn("everyone", prep.masked)
        out, ok = mu.restore(prep.masked.replace("Commanders, the event starts!", "Commander, das Event beginnt!"), prep)
        self.assertEqual(out, "@everyone\n\nCommander, das Event beginnt!")


class DecorationTests(unittest.TestCase):
    """Trennlinien und Fußnoten-Marker (Regel-Posts) bekommt die Übersetzung nicht zu sehen."""
    RULES = ("**Everyone** must follow these rules.\n# --------------\n> ## 1. Basics\n"
             "> - Remove names from ***(1)*** **All** screenshots.\n>   -  ***(1)*** Except for reports.\n"
             "# --------------\n> ## 2. Warnings\n> - The **(2)** action depends on *the case*.\n\n# --------------")

    def test_edges_inner_lines_and_markers(self):
        prep = mu.prepare(self.RULES)
        self.assertEqual(prep.tail, "\n\n# --------------")
        self.assertNotIn("----", prep.masked)                 # innere Trennlinie ist Platzhalter
        self.assertNotIn("(1)", prep.masked)
        self.assertNotIn("(2)", prep.masked)
        self.assertIn("**All**", prep.masked)                # normale Formatierung mit Text bleibt sichtbar
        self.assertIn("*the case*", prep.masked)
        self.assertEqual(mu.restore(prep.masked, prep), (self.RULES, True))

    def test_lead_decoration_and_mentions(self):
        text = "@everyone\n=====\n**News** today\n====="
        prep = mu.prepare(text)
        self.assertEqual((prep.lead, prep.tail), ("@everyone\n=====\n", "\n====="))
        self.assertEqual(prep.masked, "**News** today")
        self.assertEqual(mu.restore("**Neuigkeiten** heute", prep)[0], "@everyone\n=====\n**Neuigkeiten** heute\n=====")

    def test_not_markers(self):
        for text in ("a_1_b and snake_1_case", "Use **bold** here", "Price is 5*3* units", "the **v2** build"):
            with self.subTest(text=text):
                self.assertNotIn("TOKEN", mu.prepare(text).masked)

    def test_repair_structure(self):
        src = "> ## 3. Spam\n> - Do **not** spam.\n\n> > - Open a ticket ***(1)*** now.\n> > - We reply soon."
        prep = mu.prepare(src)
        ai = ("## 3. Spam\n- **Kein** Spam.\n> - Öffne jetzt ein Ticket.\n\n> - Wir antworten bald.")   # Präfixe weg, Marker weg
        fixed, changed = mu.repair_structure(prep.masked, ai, prep)
        out, ok = mu.restore(fixed, prep)
        self.assertTrue(changed and ok)
        self.assertEqual(out, "> ## 3. Spam\n> - **Kein** Spam.\n\n> > - Öffne jetzt ein Ticket. ***(1)***\n> > - Wir antworten bald.")
        self.assertEqual(mu.repair_structure(prep.masked, "nur eine Zeile", prep), ("nur eine Zeile", False))

    def test_code_fence_is_never_split(self):
        text = "Run:\n```\n----\n```"
        prep = mu.prepare(text)
        self.assertEqual((prep.lead, prep.tail), ("", ""))
        self.assertEqual(mu.restore(prep.masked, prep), (text, True))

    def test_only_decoration_stays_untranslatable(self):
        prep = mu.prepare("# ------\n12345")
        self.assertFalse(prep.has_text())


class HtmlTests(unittest.TestCase):
    def test_round_trip(self):
        lines = ["**Double XP** starts *Friday* and ***boosters*** are __free__ ||secret|| _soon_",
                 "a < b & c > d", "Fuel 5__DISCORD_TOKEN_0__3 __DISCORD_TOKEN_1__ text"]
        for line in lines:
            with self.subTest(line=line):
                self.assertEqual(mu.html_to_md(mu.md_to_html(line)), line)

    def test_tags(self):
        self.assertEqual(mu.md_to_html("**a** *b* __c__ ||d|| _e_ ***f***"),
                         "<b>a</b> <i>b</i> <u>c</u> <mark>d</mark> <em>e</em> <b><i>f</i></b>")
        self.assertEqual(mu.md_to_html("__DISCORD_TOKEN_3__ und __x__"), "__DISCORD_TOKEN_3__ und <u>x</u>")

    def test_links_as_anchor_round_trip(self):
        prep = mu.prepare("Full details are in the [patch notes](https://example.com/p) and FAQ: <https://example.com/f>")
        links = mu.link_tokens(prep)
        html_line = mu.md_to_html(prep.masked, links)
        self.assertIn('<a id="', html_line)
        self.assertNotIn("[", html_line)
        # Engine übersetzt den Text, lässt das Tag stehen und verschluckt das Leerzeichen nach dem Doppelpunkt
        engine = html_line.replace("Full details are in the", "Alle Details stehen in den").replace("patch notes", "Patchnotes")
        engine = engine.replace("and FAQ: ", "und FAQ:")
        out, ok = mu.restore(mu.html_to_md(engine), prep)
        self.assertTrue(ok)
        self.assertEqual(out, "Alle Details stehen in den [Patchnotes](https://example.com/p) und FAQ: <https://example.com/f>")

    def test_engine_whitespace_inside_tags(self):
        self.assertEqual(mu.html_to_md("Das ist <b> wichtig </b>!"), "Das ist **wichtig** !")
        self.assertEqual(mu.html_to_md("Das ist <b>wichtig</b>!"), "Das ist **wichtig**!")
        self.assertEqual(mu.html_to_md("Es ist <B>neu</B> &amp; gut"), "Es ist **neu** & gut")


if __name__ == "__main__":
    unittest.main()
