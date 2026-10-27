"""
Tests für die Website (site/): Ausgabe aktuell, Texte vollständig in allen Sprachen, Links gültig,
keine externen Ressourcen, jeder Anbieter aus der Config beschrieben.
"""
import os
import re
import sys
import unittest
from html.parser import HTMLParser

from _testenv import BOT_DIR

sys.path.insert(0, os.path.join(BOT_DIR, "site"))
import build  # noqa: E402
import locales  # noqa: E402

TAG_RE = re.compile(r"</?([a-z0-9]+)")
HREF_RE = re.compile(r'href="([^"]*)"')
FIELD_RE = re.compile(r"\{(\w+)\}")
VOID = {"br", "img", "meta", "link", "input"}
# Schlüssel mit Beispieltext in der jeweiligen Zielsprache: Tags gleich, Inhalt frei
FREE_TEXT = {"lang_name", "home_example_tgt_channel"}


class Balance(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"</{tag}> bei {self.stack[-3:]}")
        else:
            self.stack.pop()


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = build.render()
        cls.pages = {rel: data.decode("utf-8") for rel, data in cls.files.items() if rel.endswith(".html")}

    def test_public_is_up_to_date(self):
        public = build.PUBLIC
        on_disk = {p.relative_to(public).as_posix() for p in public.rglob("*") if p.is_file()}
        self.assertEqual(sorted(on_disk ^ set(self.files)), [], "public/ veraltet: python site/build.py ausführen")
        stale = [rel for rel, data in self.files.items() if (public / rel).read_bytes() != data]
        self.assertEqual(stale, [], "public/ veraltet: python site/build.py ausführen")

    def test_every_language_complete_and_consistent(self):
        en = build.EN
        for lang in build.LANGS[1:]:
            texts = build.TEXTS[lang]
            with self.subTest(lang=lang):
                self.assertEqual(sorted(set(en) - set(texts)), [], "fehlende Texte")
                self.assertEqual(sorted(set(texts) - set(en)), [], "Texte, die es auf Englisch nicht gibt")
            for key, text in texts.items():
                with self.subTest(lang=lang, key=key):
                    self.assertEqual(TAG_RE.findall(text), TAG_RE.findall(en[key]), "HTML-Tags")
                    self.assertEqual(HREF_RE.findall(text), HREF_RE.findall(en[key]), "Links")
                    self.assertEqual(sorted(FIELD_RE.findall(text)), sorted(FIELD_RE.findall(en[key])), "Platzhalter")
                    self.assertEqual(text.count("<code>"), en[key].count("<code>"))
                    if key not in FREE_TEXT:
                        self.assertTrue(text.strip())

    def test_code_and_commands_unchanged_in_translations(self):
        code = lambda t: re.findall(r"<code>(.*?)</code>", t)  # noqa: E731
        for lang in build.LANGS[1:]:
            for key, text in build.TEXTS[lang].items():
                with self.subTest(lang=lang, key=key):
                    self.assertEqual(code(text), code(build.EN[key]))

    def test_html_is_balanced(self):
        for rel, text in self.pages.items():
            parser = Balance()
            parser.feed(text)
            with self.subTest(page=rel):
                self.assertEqual(parser.errors, [])
                self.assertEqual(parser.stack, [])

    def test_internal_links_resolve(self):
        for rel, text in self.pages.items():
            base = rel.rsplit("/", 1)[0] if "/" in rel else ""
            for href in HREF_RE.findall(text):
                if href.startswith(("http://", "https://", "#")):
                    continue
                if href.startswith("/app/"):            # Dashboard: eigener Dienst (yatb-web), nicht die statische Seite
                    self.assertRegex(href, r"^/app/\?lang=[a-z]{2}$")
                    continue
                path = href.split("#")[0].split("?")[0]
                if not path.startswith("/"):
                    path = f"/{base}/{path}" if base else f"/{path}"
                target = path.lstrip("/")
                candidates = [target, f"{target}.html", f"{target}index.html", f"{target}/index.html"]
                with self.subTest(page=rel, href=href):
                    self.assertTrue(any(c in self.files for c in candidates), target)

    def test_no_external_resources_or_scripts(self):
        for rel, text in self.pages.items():
            with self.subTest(page=rel):
                self.assertNotIn("<script", text)
                self.assertNotIn("style=", text)        # CSP: keine Inline-Styles
                self.assertEqual(re.findall(r'src="(https?:[^"]*)"', text), [])
                self.assertEqual(re.findall(r'<link rel="(?:stylesheet|icon|apple-touch-icon)" href="(https?:[^"]*)"', text), [])

    def test_every_provider_documented(self):
        for pid, name, kind, _ in build.load_providers():
            with self.subTest(provider=pid):
                self.assertIn(pid, build.PROVIDER_LINKS)
                self.assertIn(f"prov_{pid}", build.EN)
                self.assertIn(name, self.pages["en/privacy.html"])
                if pid != "libre":
                    self.assertIn(f"guide_{pid}", locales.MESSAGES["en"])
                    self.assertIn(f'id="{pid}"', self.pages["en/keys.html"])

    def test_every_command_listed(self):
        facts = build.bot_facts()
        self.assertGreaterEqual(len(facts["commands"]), 15)
        for cmd, _ in facts["commands"]:
            self.assertIn(f"<code>{cmd}</code>", self.pages["de/admins.html"])
        self.assertEqual(facts["map_days"], "7")


if __name__ == "__main__":
    unittest.main()
