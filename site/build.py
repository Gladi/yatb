"""
YATB-Website: erzeugt die statischen Seiten (7 Sprachen) nach site/public/ - nur Python-Standardbibliothek.

    python site/build.py                  # -> site/public/ (= LIVE, Caddy liest den Ordner direkt)
    python site/build.py --out /tmp/vorschau   # Vorschau woanders hin bauen, ohne live zu ändern

Quellen: Texte in site/content/ (en.py, de.py von Hand, mt.py maschinell), Einstellungen in site/site.toml,
Befehle und Rechte aus bot.py, Key-Anleitungen aus locales.py, Anbieter aus config/providers.toml.
public/ wird mit eingecheckt; tests/test_site.py prüft, dass es zum aktuellen Stand passt.
Caddy liefert public/ schreibgeschützt aus (/ leitet je nach Browsersprache auf /<lang>/ weiter).
"""
import ast
import hashlib
import html
import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import urlparse

SITE = Path(__file__).resolve().parent
REPO = SITE.parent
PUBLIC = SITE / "public"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(SITE))

import locales  # noqa: E402
from content.de import TEXTS as DE  # noqa: E402
from content.en import TEXTS as EN  # noqa: E402
from content.mt import TEXTS_MT  # noqa: E402

LANGS = ("en", "de", "fr", "es", "it", "ru", "nl")
TEXTS = {"en": EN, "de": DE, **TEXTS_MT}
PAGES = ("index", "members", "admins", "keys", "privacy", "terms")
CURRENT_PAGE, CURRENT_LANG = ' aria-current="page"', ' aria-current="true"'
LANG_NAMES = {"en": "English", "de": "Deutsch", "fr": "Français", "es": "Español", "it": "Italiano", "ru": "Русский", "nl": "Nederlands"}

# Konsole + Datenschutzquelle je Anbieter (Stand der Prüfung: legal_date in site.toml)
PROVIDER_LINKS = {
    "gemini": ("https://aistudio.google.com", "https://ai.google.dev/gemini-api/terms"),
    "mistral": ("https://console.mistral.ai", "https://legal.mistral.ai/terms/commercial-terms-of-service"),
    "groq": ("https://console.groq.com", "https://console.groq.com/docs/your-data"),
    "novita": ("https://novita.ai", "https://novita.ai/legal/terms-of-service"),
    "google_translate": ("https://console.cloud.google.com", "https://docs.cloud.google.com/translate/data-usage"),
    "azure": ("https://portal.azure.com",
              "https://learn.microsoft.com/azure/ai-foundry/responsible-ai/translator/data-privacy-security"),
    "libre": (None, None),   # eigener Server - keine Anbieterquelle
}


# ----------------- Quellen aus dem Bot -----------------
def load_settings() -> dict:
    return tomllib.loads((SITE / "site.toml").read_text(encoding="utf-8"))


def load_providers() -> list:
    """[(id, name, kind, free_allowed)] in Config-Reihenfolge, nur aktive; LibreTranslate am Ende."""
    cfg = tomllib.loads((REPO / "config" / "providers.toml").read_text(encoding="utf-8"))["providers"]
    # "free" wie im Bot (providers.free_allowed): Gratis-Stufe vorhanden UND im EWR zulässig
    out = [(pid, p["name"], p["kind"], p.get("free_available", True) and p.get("eea_free_allowed", True))
           for pid, p in cfg.items() if p.get("enabled", True)]
    return out + [("libre", "LibreTranslate", "libre", True)]


def bot_facts() -> dict:
    """Befehle, Rechte und Aufbewahrungsfristen direkt aus dem Code, damit die Seite nicht veraltet."""
    src = (REPO / "bot.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    kw = lambda call, name: next((k.value.value for k in call.keywords if k.arg == name), None)  # noqa: E731
    groups, commands, perms = {}, [], {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            func = node.value.func
            target = node.targets[0].id if isinstance(node.targets[0], ast.Name) else None
            if isinstance(func, ast.Attribute) and func.attr == "Group" and target:
                parent = next((k.value.id for k in node.value.keywords if k.arg == "parent"), None)
                groups[target] = (groups[parent] + " " if parent else "/") + kw(node.value, "name")
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "REQUIRED_PERMS":
            perms = ast.literal_eval(node.value)
        if isinstance(node, ast.AsyncFunctionDef):
            for dec in node.decorator_list:
                if (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr == "command"
                        and isinstance(dec.func.value, ast.Name) and dec.func.value.id in groups):
                    commands.append((f"{groups[dec.func.value.id]} {kw(dec, 'name')}", kw(dec, "description")))
    db_src = (REPO / "database.py").read_text(encoding="utf-8")
    tr_src = (REPO / "translator.py").read_text(encoding="utf-8")
    st_src = (REPO / "stats.py").read_text(encoding="utf-8")
    return {
        "commands": commands,
        "perms": list(perms.values()),
        "map_days": re.search(r"message_mappings WHERE created_at < datetime\('now', '-(\d+) days'\)", db_src).group(1),
        "context_lines": re.search(r'AI_CONTEXT_LINES = int\(os.getenv\("AI_CONTEXT_LINES", "(\d+)"\)\)', tr_src).group(1),
        "raw_days": re.search(r"^RAW_KEEP_DAYS = (\d+)", st_src, re.M).group(1),
    }


def discord_md(text: str) -> str:
    """Discord-Markdown der Key-Anleitungen -> HTML (nummerierte Zeilen werden eine Liste)."""
    def inline(s):
        s = html.escape(s, quote=False)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        return re.sub(r"(?<![\w./])((?:[a-z0-9-]+\.)+(?:com|ai|de))(?![\w/])",
                      r'<a href="https://\1" rel="noopener">\1</a>', s)
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if all(re.match(r"\d+\.\s", ln) for ln in lines):
        items = [inline(re.sub(r"^\d+\.\s*", "", ln)) for ln in lines]
        return "<ol>" + "".join(f"<li>{item}</li>" for item in items) + "</ol>"
    return "".join(f"<p>{inline(ln)}</p>" for ln in lines)


# ----------------- Seitenbau -----------------
class Page:
    def __init__(self, lang, slug, settings, facts, assets):
        self.lang, self.slug, self.s, self.f, self.assets = lang, slug, settings, facts, assets

    def t(self, key: str, **values) -> str:
        text = TEXTS[self.lang].get(key) or EN[key]
        values = {"date": self.s["legal_date"], **{k: self.f[k] for k in ("map_days", "context_lines", "raw_days")},
                  **values}
        return re.sub(r"\{(\w+)\}", lambda m: str(values.get(m.group(1), m.group(0))), text)

    def asset(self, name: str) -> str:
        return f"/static/{name}?v={self.assets[name]}"

    def url(self, slug: str, lang: str = None) -> str:
        lang = lang or self.lang
        return f"/{lang}/" if slug == "index" else f"/{lang}/{slug}"

    def shell(self, title: str, body: str) -> str:
        t, base = self.t, self.s["base_url"]
        full_title = f"YATB - {title}" if self.slug == "index" else f"{title} · YATB"
        alternates = "".join(f'<link rel="alternate" hreflang="{lg}" href="{base}{self.url(self.slug, lg)}">'
                             for lg in LANGS)
        alternates += f'<link rel="alternate" hreflang="x-default" href="{base}{self.url(self.slug, "en")}">'
        nav = "".join(f'<li><a href="{self.url(p)}"{CURRENT_PAGE if p == self.slug else ""}>{t("nav_" + p)}</a></li>'
                      for p in ("members", "admins", "keys"))
        langs = "".join(f'<li><a href="{self.url(self.slug, lg)}" hreflang="{lg}" lang="{lg}"'
                        f'{CURRENT_LANG if lg == self.lang else ""}>{LANG_NAMES[lg]}</a></li>'
                        for lg in LANGS)
        foot = [f'<a href="{self.url("privacy")}">{t("nav_privacy")}</a>', f'<a href="{self.url("terms")}">{t("nav_terms")}</a>']
        if self.s.get("imprint_html"):
            foot.append(f'<a href="{self.url("imprint")}">{t("nav_imprint")}</a>')
        if self.s.get("home"):
            foot.append(f'<a href="{html.escape(self.s["home"])}">{t("nav_more")}</a>')
        if self.s.get("source"):   # Markenname, in allen Sprachen gleich
            foot.append(f'<a href="{html.escape(self.s["source"])}" target="_blank" rel="noopener noreferrer">GitHub</a>')
        kofi = (f'<a class="kofi" href="https://ko-fi.com/{html.escape(self.s["kofi"])}" target="_blank" rel="noopener noreferrer">'
                f'<span aria-hidden="true">☕</span> {t("kofi")}</a>') if self.s.get("kofi") else ""
        return f"""<!doctype html>
<html lang="{self.lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{full_title}</title>
<meta name="description" content="{html.escape(t("site_desc"))}">
<link rel="canonical" href="{base}{self.url(self.slug)}">
{alternates}
<meta property="og:title" content="{html.escape(full_title)}">
<meta property="og:description" content="{html.escape(t("site_desc"))}">
<meta property="og:image" content="{base}{self.asset("img/og.jpg")}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#0b1220">
<link rel="icon" href="{self.asset("img/favicon-32.png")}" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="{self.asset("img/apple-touch-icon.png")}">
<link rel="stylesheet" href="{self.asset("style.css")}">
</head>
<body>
<header class="top">
<div class="wrap bar">
<a class="brand" href="{self.url("index")}"><img src="{self.asset("img/mark-96.webp")}" width="40" height="40" alt=""><span>YATB</span></a>
<input type="checkbox" id="menu-toggle" class="menu-toggle">
<label for="menu-toggle" class="menu-button">{t("nav_menu")}</label>
<nav class="nav" aria-label="{t("nav_menu")}"><ul>{nav}</ul></nav>
<details class="langs"><summary aria-label="{t("nav_language")}"><span aria-hidden="true">🌐</span> {self.lang.upper()}</summary><ul>{langs}</ul></details>
</div>
</header>
<main class="wrap">
{body}
</main>
<footer class="foot">
<div class="wrap">
<p class="foot-links">{" · ".join(foot)}</p>
{kofi}
<p class="muted">{t("footer_note")}</p>
</div>
</footer>
</body>
</html>
"""

    # --- einzelne Seiten
    def index(self) -> str:
        t = self.t
        feats = "".join(f'<div class="card"><h3>{t(f"feat_{k}_title")}</h3><p>{t(f"feat_{k}_text")}</p></div>'
                        for k in ("natural", "format", "mirror", "privacy", "keys", "fallback"))
        support = (f'<section class="support"><h2>{t("home_support_title")}</h2><p>{t("home_support_text")}</p>'
                   f'<a class="kofi" href="https://ko-fi.com/{html.escape(self.s["kofi"])}" target="_blank" rel="noopener noreferrer">'
                   f'<span aria-hidden="true">☕</span> {t("kofi")}</a></section>') if self.s.get("kofi") else ""
        msg = lambda channel, text, tag: (  # noqa: E731
            f'<div class="chan"><div class="chan-name"># {channel}</div><div class="msg"><div class="avatar" aria-hidden="true">M</div>'
            f'<div><div class="author">Mia{f" <span class=tag>{tag}</span>" if tag else ""}</div>'
            f'<div class="text">{text}</div></div></div></div>')
        example = (f'<figure class="example">{msg("english", t("home_example_src"), "")}<div class="arrow" aria-hidden="true">→</div>'
                   f'{msg(t("home_example_tgt_channel"), t("home_example_tgt"), "[AI]")}'
                   f'<figcaption>{t("home_example_note")}</figcaption></figure>')
        return self.shell(t("home_title"), f"""
<section class="hero">
<img class="hero-logo" src="{self.asset("img/logo-512.webp")}" width="256" height="256" alt="YATB">
<div>
<h1>{t("home_title")}</h1>
<p class="lead">{t("home_lead")}</p>
<ul class="badges"><li>{t("home_badge_langs")}</li><li>{t("home_badge_storage")}</li><li>{t("home_badge_private")}</li></ul>
</div>
</section>
{example}
<section><h2>{t("home_features_title")}</h2><div class="grid">{feats}</div></section>
<section><h2>{t("home_how_title")}</h2><ol class="steps"><li>{t("how_1")}</li><li>{t("how_2")}</li><li>{t("how_3")}</li></ol></section>
<section class="note"><h2>{t("home_private_title")}</h2><p>{t("home_private_text")}</p></section>
{support}""")

    def members(self) -> str:
        t = self.t
        tags = "".join(f"<tr><td><code>[{name}]</code></td><td>{t(key)}</td></tr>" for name, key in
                       (("AI", "tag_ai"), ("Google", "tag_google"), ("Azure", "tag_azure"), ("Libre", "tag_libre"), ("Raw", "tag_raw")))
        faq = "".join(f"<details><summary>{t(f'faq_{k}_q')}</summary><p>{t(f'faq_{k}_a')}</p></details>"
                      for k in ("wrong", "off", "dm"))
        return self.shell(t("members_title"), f"""
<h1>{t("members_title")}</h1>
<p class="lead">{t("members_lead")}</p>
<section><h2>{t("members_how_title")}</h2>{t("members_how")}</section>
<section><h2>{t("members_tags_title")}</h2><p>{t("members_tags_intro")}</p><table class="tags"><tbody>{tags}</tbody></table></section>
<section><h2>{t("members_data_title")}</h2>{t("members_data")}</section>
<section class="note"><h2>{t("members_choice_title")}</h2><ul><li>{t("members_choice_standard")}</li><li>{t("members_choice_local")}</li></ul><p>{t("members_choice_note")}</p></section>
<section><h2>{t("members_faq_title")}</h2>{faq}</section>""")

    def admins(self) -> str:
        t = self.t
        perms = ", ".join(f"<em>{html.escape(p)}</em>" for p in self.f["perms"])
        rows = "".join(f"<tr><td><code>{html.escape(cmd)}</code></td>"
                       f"<td>{html.escape(locales.command_text(self.lang, desc) or desc)}</td></tr>"
                       for cmd, desc in self.f["commands"])
        steps = "".join(f"<li>{t(f'setup_{i}', perms=perms)}</li>" for i in range(1, 5))
        return self.shell(t("admins_title"), f"""
<h1>{t("admins_title")}</h1>
<p class="lead">{t("admins_lead")}</p>
<section><h2>{t("admins_setup_title")}</h2>
<ol class="steps">{steps}<li>{t("setup_5")}<blockquote class="rule">{t("setup_rule")}</blockquote></li></ol>
<p>{t("setup_check")}</p></section>
<section><h2>{t("admins_chain_title")}</h2><p>{t("admins_chain_intro")}</p>
<ol class="chain">{"".join(f"<li>{t(f'chain_{i}')}</li>" for i in range(1, 6))}</ol><p>{t("admins_chain_note")}</p></section>
<section><h2>{t("admins_limits_title")}</h2>{t("admins_limits")}</section>
<section><h2>{t("admins_forum_title")}</h2>{t("admins_forum")}{t("admins_forum_perms")}</section>
<section class="note"><h2>{t("admins_security_title")}</h2><p>{t("admins_security")}</p></section>
<section><h2>{t("admins_commands_title")}</h2><div class="table-wrap"><table><thead><tr><th>{t("admins_col_command")}</th><th>{t("admins_col_desc")}</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section><h2>{t("admins_remove_title")}</h2><p>{t("admins_remove")}</p></section>""")

    def keys(self) -> str:
        t = self.t
        cards = []
        for pid, name, kind, free in load_providers():
            if pid == "libre":
                continue
            console, source = PROVIDER_LINKS[pid]
            plan = locales.get_text(self.lang, "guide_plan_free_paid" if free else "guide_plan_paid_only")
            badge = t("keys_kind_ai") if kind == "openai" else t("keys_kind_mt")
            cards.append(f"""<article class="card provider" id="{pid}">
<h2>{html.escape(name)} <span class="badge">{badge}</span></h2>
<h3>{t("keys_steps")}</h3>{discord_md(locales.get_text(self.lang, f"guide_{pid}"))}
<h3>{t("keys_plan")}</h3><p>{html.escape(plan)}</p>
<h3>{t("keys_privacy")}</h3><p>{t(f"prov_{pid}")} <a href="{source}" rel="noopener">{t("keys_source")}</a></p>
<p><a class="button" href="{console}" rel="noopener">{t("keys_open")} →</a></p>
</article>""")
        toc = "".join(f'<li><a href="#{pid}">{html.escape(name)}</a></li>' for pid, name, _, _ in load_providers() if pid != "libre")
        return self.shell(t("keys_title"), f"""
<h1>{t("keys_title")}</h1>
<p class="lead">{t("keys_lead")}</p>
<section class="note">{t("keys_tips")}</section>
<nav class="toc"><ul>{toc}</ul></nav>
{"".join(cards)}
<p class="muted">{t("keys_menu_note")}</p>""")

    def legal_footer(self) -> str:
        return f'<p class="muted">{self.t("legal_updated")}<br>{self.t("legal_binding")}</p>'

    def privacy(self) -> str:
        t = self.t
        controller = self.s.get("controller_html") or f'<p class="placeholder">{t("privacy_controller_missing")}</p>'
        rows = "".join(f"<tr><td>{t(f'pd_{k}_what')}</td><td>{t(f'pd_{k}_why')}</td><td>{t(f'pd_{k}_how_long')}</td></tr>"
                       for k in ("text", "map", "choice", "stats", "config", "backup"))
        source = lambda pid: (f' <a href="{PROVIDER_LINKS[pid][1]}" rel="noopener">{t("keys_source")}</a>'  # noqa: E731
                              if PROVIDER_LINKS[pid][1] else "")
        services = "".join(f'<tr><td>{html.escape(name)}</td><td>{t(f"prov_{pid}")}{source(pid)}</td></tr>'
                           for pid, name, _, _ in load_providers())
        return self.shell(t("privacy_title"), f"""
<h1>{t("privacy_title")}</h1>
<p class="lead">{t("privacy_lead")}</p>
<section><h2>{t("privacy_controller_title")}</h2>{controller}</section>
<section><h2>{t("privacy_web_title")}</h2>{t("privacy_web")}<h3>{t("privacy_dash_title")}</h3>{t("privacy_dash")}</section>
<section><h2>{t("privacy_bot_title")}</h2><p>{t("privacy_bot_intro")}</p>
<div class="table-wrap"><table><thead><tr><th>{t("privacy_col_what")}</th><th>{t("privacy_col_why")}</th><th>{t("privacy_col_how_long")}</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section><h2>{t("privacy_services_title")}</h2><p>{t("privacy_services_intro")}</p>
<div class="table-wrap"><table><thead><tr><th>{t("privacy_col_service")}</th><th>{t("privacy_col_note")}</th></tr></thead><tbody>{services}</tbody></table></div></section>
<section><h2>{t("privacy_discord_title")}</h2><p>{t("privacy_discord")}</p></section>
<section><h2>{t("privacy_basis_title")}</h2><p>{t("privacy_basis")}</p></section>
<section><h2>{t("privacy_rights_title")}</h2><p>{t("privacy_rights")}</p></section>
{self.legal_footer()}""")

    def terms(self) -> str:
        t = self.t
        block = lambda text: text if text.startswith("<") else f"<p>{text}</p>"  # noqa: E731
        parts = "".join(f"<section><h2>{t(f'terms_{i}_title')}</h2>{block(t(f'terms_{i}'))}</section>" for i in range(1, 7))
        return self.shell(t("terms_title"), f"""
<h1>{t("terms_title")}</h1>
<p class="lead">{t("terms_lead")}</p>
{parts}
{self.legal_footer()}""")

    def imprint(self) -> str:
        return self.shell(self.t("imprint_title"),
                          f'<h1>{self.t("imprint_title")}</h1><div class="imprint">{self.s["imprint_html"]}</div>')

    def not_found(self) -> str:
        return self.shell(self.t("not_found_title"), f'<h1>{self.t("not_found_title")}</h1><p>{self.t("not_found_text")}</p>')


# ----------------- Ausgabe -----------------
_A_TAG = re.compile(r"<a\s[^>]*>")


def external_new_tab(page: str, base_url: str) -> str:
    """Links nach außerhalb der eigenen Domain (base_url und ihre Subdomains, z. B. *.gladi.de) öffnen in einem neuen
    Tab - mit rel="noopener noreferrer". Links, die schon ein target haben, bleiben, wie sie sind."""
    base = urlparse(base_url).hostname or ""
    domain = base.split(".", 1)[1] if base.count(".") >= 2 else base

    def fix(match):
        tag = match.group(0)
        href = re.search(r'href="(https?://[^"]+)"', tag)
        if not href or "target=" in tag:
            return tag
        host = urlparse(href.group(1)).hostname or ""
        if host == domain or host.endswith("." + domain):
            return tag
        return re.sub(r'\srel="[^"]*"', "", tag)[:-1] + ' target="_blank" rel="noopener noreferrer">'
    return _A_TAG.sub(fix, page)


def render() -> dict:
    """Alle Dateien als {relativer Pfad: bytes} (deterministisch, ohne Zeitstempel)."""
    settings, facts = load_settings(), bot_facts()
    static = {p.relative_to(SITE / "static").as_posix(): p.read_bytes()
              for p in sorted((SITE / "static").rglob("*")) if p.is_file()}
    assets = {name: hashlib.sha256(data).hexdigest()[:10] for name, data in static.items()}
    files = {f"static/{name}": data for name, data in static.items()}
    files["favicon.ico"] = static["img/favicon.ico"]
    pages = PAGES + (("imprint",) if settings.get("imprint_html") else ())
    for lang in LANGS:
        for slug in pages:
            page = Page(lang, slug, settings, facts, assets)
            files[f"{lang}/{slug}.html"] = external_new_tab(getattr(page, slug)(), settings["base_url"]).encode("utf-8")
    files["404.html"] = external_new_tab(Page("en", "index", settings, facts, assets).not_found(),
                                         settings["base_url"]).encode("utf-8")
    # Rückfall, falls die Weiterleitung nach Browsersprache nicht greift
    links = "".join(f'<li><a href="/{lg}/" hreflang="{lg}" lang="{lg}">{LANG_NAMES[lg]}</a></li>' for lg in LANGS)
    files["index.html"] = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" '
                           f'content="width=device-width, initial-scale=1"><title>YATB</title>'
                           f'<link rel="stylesheet" href="/static/style.css?v={assets["style.css"]}"></head>'
                           f'<body><main class="wrap"><h1>YATB</h1><ul>{links}</ul></main></body></html>\n').encode("utf-8")
    files["robots.txt"] = f"User-agent: *\nAllow: /\nSitemap: {settings['base_url']}/sitemap.xml\n".encode()
    urls = "".join(f"<url><loc>{settings['base_url']}{Page(lg, s, settings, facts, assets).url(s)}</loc></url>"
                   for lg in LANGS for s in pages)
    files["sitemap.xml"] = (f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/'
                            f'sitemap/0.9">{urls}</urlset>\n').encode("utf-8")
    return files


def main():
    out = Path(sys.argv[sys.argv.index("--out") + 1]).resolve() if "--out" in sys.argv else PUBLIC
    files = render()
    written = 0
    for rel, data in files.items():
        path = out / rel
        if not path.exists() or path.read_bytes() != data:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            written += 1
    stale = [p for p in out.rglob("*") if p.is_file() and p.relative_to(out).as_posix() not in files]
    for p in stale:
        p.unlink()
    print(f"{len(files)} Dateien, {written} geschrieben, {len(stale)} entfernt -> {out}")


if __name__ == "__main__":
    main()
