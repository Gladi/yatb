"""
YATB: übersetzt eine Textdatei (Standard: site/content/en.py) nach fr/es/it/ru mit Google Gemini -> mt.py.
Auch für das Dashboard: --src dashboard/texts/en.py --out dashboard/texts/mt.py

Nur neue oder geänderte englische Texte werden übersetzt (Hash je Text in mt.py). Jede Antwort wird geprüft:
HTML-Tags, Links, Platzhalter und <code>-Inhalte müssen gleich bleiben, sonst wird der Text verworfen (-> Englisch).
Key: Umgebungsvariable GOOGLE_AI_KEY (Gemini-Key aus .env.tools), nur diese eine Variable in den Container geben
(ohne GOOGLE_AI_KEY, aber mit MISTRAL_API_KEY übersetzt Mistral Small):

    docker run --rm -v $PWD/yatb:/src -w /src --env-file <(grep '^GOOGLE_AI_KEY=' .env.tools) \
      discord-bot-bot python site/translate.py [--all]

Danach: python site/build.py und Tests. Der Key wird nie ausgegeben.
"""
import asyncio
import hashlib
import json
import pprint
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE.parent))
sys.path.insert(0, str(SITE))

import os  # noqa: E402

import aiohttp  # noqa: E402

import locales  # noqa: E402
import importlib.util  # noqa: E402


def _arg(name: str, default: str) -> Path:
    return Path(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else SITE.parent / default


SRC, OUT = _arg("--src", "site/content/en.py"), _arg("--out", "site/content/mt.py")


def _load(path: Path, *names):
    spec = importlib.util.spec_from_file_location(f"_yatb_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return [getattr(module, n) for n in names]


EN = _load(SRC, "TEXTS")[0]

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"   # wie config/providers.toml (gemini)
MISTRAL_URL, MISTRAL_MODEL = "https://api.mistral.ai/v1", "mistral-small-2603"   # Ausweichweg mit MISTRAL_API_KEY

LANGS = {"fr": "French", "es": "Spanish (Spain)", "it": "Italian", "ru": "Russian", "nl": "Dutch"}
OWN_NAME = {"fr": "français", "es": "español", "it": "italiano", "ru": "русский", "nl": "nederlands"}
LANG_NAMES = {"fr": "Français", "es": "Español", "it": "Italiano", "ru": "Русский", "nl": "Nederlands"}
DELETE_WORD = {"fr": "supprimer", "es": "eliminar", "it": "elimina", "ru": "удалить", "nl": "verwijderen"}   # Dashboard: Bestätigungswort
FIXED = ("lang_name", "home_example_tgt_channel", "delete_word")
SYSTEM = (
    "You localize the website of YATB, a Discord translation bot, from English into {lang}. Translate the JSON "
    "values. Rules: keep every JSON key; keep all HTML tags and attributes exactly (same tags in the same order, "
    "href values unchanged); keep placeholders in curly braces like {{date}} unchanged; keep everything inside "
    "<code>...</code> unchanged; keep product and service names (YATB, Discord, LibreTranslate, Google Gemini, "
    "Google Translate, Mistral, Groq, Novita, Azure Translator, Oracle Cloud, Let's Encrypt, Ko-fi). Square brackets: "
    "keep a tag like [AI] or [Raw] ONLY where the English text has it in brackets; never add brackets elsewhere - "
    "the plain word AI in a sentence is translated normally (e.g. IA, ИИ). Use exactly these names of the bot's "
    "privacy options: Standard = \"{standard}\", Local only = \"{local}\". The key home_example_tgt is a gaming "
    "chat message: translate it naturally into {lang} (e.g. 20 h / 20:00). "
    "Keep the word Bridge for a group of linked channels. Address the reader "
    "informally and consistently (tu / tú / tu / ты / je - never vous, usted, Lei, вы or u). Legal texts (privacy policy, terms): translate precisely and use the usual legal terms "
    "of the language (e.g. GDPR article citations in local style). Natural, concise wording. "
    "Return ONLY one JSON object with the same keys."
)
TAG_RE = re.compile(r"</?([a-z0-9]+)")
HREF_RE = re.compile(r'href="([^"]*)"')
FIELD_RE = re.compile(r"\{(\w+)\}")
CODE_RE = re.compile(r"<code>(.*?)</code>")
# Anrede wie im Bot: informell. Förmliche Formen führen zur Neuanfrage (Beispielnachricht ausgenommen).
FORMAL_RE = {
    "ru": re.compile(r"(?<![\w-])(вы|вас|вам|вами|ваш\w*)(?![\w-])", re.I),
    "fr": re.compile(r"(?<![\w-])(vous|votre|vos)(?![\w-])", re.I),
    "es": re.compile(r"(?<![\w-])(usted|ustedes|vosotros|vuestr\w*)(?![\w-])", re.I),
    "it": re.compile(r"(?<![\w-])(Lei|voi|vostr\w*)(?![\w-])"),
    "nl": re.compile(r"(?<![\w-])(u|uw)(?![\w-])", re.I),
}


def source_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def valid(src: str, out, code: str = "", key: str = "") -> bool:
    if isinstance(out, str) and code in FORMAL_RE and key != "home_example_tgt" and FORMAL_RE[code].search(out):
        return False
    return (isinstance(out, str) and out.strip() != ""
            and TAG_RE.findall(out) == TAG_RE.findall(src) and HREF_RE.findall(out) == HREF_RE.findall(src)
            and sorted(FIELD_RE.findall(out)) == sorted(FIELD_RE.findall(src))
            and CODE_RE.findall(out) == CODE_RE.findall(src)
            and out.count("[") == src.count("[") and out.count("]") == src.count("]"))


def load_existing():
    try:
        return tuple(_load(OUT, "TEXTS_MT", "SOURCE_HASH"))
    except (OSError, AttributeError):
        return {lang: {} for lang in LANGS}, {}


async def main():
    secret = os.environ.get("GOOGLE_AI_KEY", "").strip()
    base_url = BASE_URL
    model = re.search(r'^model = "([^"]+)"', (SITE.parent / "config" / "providers.toml").read_text(encoding="utf-8")
                      .split("[providers.gemini]")[1], re.M).group(1)
    if not secret and os.environ.get("MISTRAL_API_KEY", "").strip():   # Ausweichweg, z. B. wenn das Gemini-Limit erreicht ist
        secret, base_url, model = os.environ["MISTRAL_API_KEY"].strip(), MISTRAL_URL, MISTRAL_MODEL
    if not secret:
        sys.exit("GOOGLE_AI_KEY (oder MISTRAL_API_KEY) fehlt")
    old, old_hash = load_existing()
    hashes = {k: source_hash(v) for k, v in EN.items()}
    # Beispielnachricht: in die jeweilige Sprache aus dem englischen Original, Kanalname fest
    sources = {k: v for k, v in EN.items() if k not in FIXED}
    if "home_example_tgt" in EN:   # Website: Beispielnachricht aus dem englischen Original übersetzen
        sources["home_example_tgt"] = EN["home_example_src"]
    force = "--all" in sys.argv          # alles neu übersetzen (z. B. nach Änderung des Prompts)
    changed = {k for k in sources if force or old_hash.get(k) != hashes[k]}
    print(f"{len(changed)} von {len(sources)} Texten geändert", file=sys.stderr)

    async with aiohttp.ClientSession() as session:
        async def ask(code: str, obj: dict) -> dict:
            system = SYSTEM.format(lang=LANGS[code], standard=locales.get_text(code, "privacy_standard_name"),
                                   local=locales.get_text(code, "privacy_local_name"))
            payload = {"model": model, "temperature": 0.1, "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(obj, ensure_ascii=False)}]}
            async with session.post(f"{base_url}/chat/completions", json=payload,
                                    headers={"Authorization": f"Bearer {secret}"},
                                    timeout=aiohttp.ClientTimeout(total=240)) as resp:
                body = await resp.json(content_type=None)
            text = body["choices"][0]["message"]["content"].strip()
            return json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", text))

        result = {}
        for code in LANGS:
            have = old.get(code, {})
            todo = {k: v for k, v in sources.items() if k in changed or k not in have}   # geändert oder fehlt (neue Sprache)
            texts = {k: v for k, v in have.items() if k in EN and k not in todo}
            items = list(todo.items())
            for i in range(0, len(items), 25):
                chunk = dict(items[i:i + 25])
                try:
                    res = await ask(code, chunk)
                except Exception as exc:  # noqa: BLE001 - einzelner Block darf scheitern, Rest weiter
                    print(f"{code}: Block {i // 25} fehlgeschlagen ({type(exc).__name__})", file=sys.stderr)
                    res = {}
                for k, src in chunk.items():
                    out = res.get(k)
                    if not valid(src, out, code, k):   # einmal einzeln nachfragen
                        try:
                            out = (await ask(code, {k: src})).get(k)
                        except Exception:  # noqa: BLE001
                            out = None
                    if k == "home_example_tgt" and out == src:   # Beispiel muss übersetzt sein
                        out = None
                    if valid(src, out, code, k):
                        texts[k] = out
                    else:
                        print(f"{code}: verworfen {k}", file=sys.stderr)
            if "lang_name" in EN:
                texts["lang_name"] = LANG_NAMES[code]
            if "home_example_tgt_channel" in EN:
                texts["home_example_tgt_channel"] = OWN_NAME[code]
            if "delete_word" in EN:
                texts["delete_word"] = DELETE_WORD[code]
            result[code] = dict(sorted(texts.items()))
            print(f"{code}: {len(texts)}/{len(EN)} Texte", file=sys.stderr)

    done = {k: h for k, h in hashes.items() if all(k in result[c] for c in LANGS)}
    out = OUT
    out.write_text(
        f'"""\nYATB - MASCHINELL ÜBERSETZTE Texte (fr, es, it, ru), erzeugt mit site/translate.py aus {SRC.name}\n'
        "(Google Gemini). NICHT von Muttersprachlern geprüft. Nicht von Hand ändern - sonst beim nächsten Lauf\n"
        'überschrieben; Korrekturen in en.py bzw. per Neuübersetzung. SOURCE_HASH = Stand des englischen Textes.\n"""\n\n'
        f"TEXTS_MT = {pprint.pformat(result, width=120, sort_dicts=True)}\n\n"
        f"SOURCE_HASH = {pprint.pformat(done, width=120, sort_dicts=True)}\n",
        encoding="utf-8")
    print(f"geschrieben: {out}", file=sys.stderr)


asyncio.run(main())
