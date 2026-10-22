"""
YATB - Textvorbereitung für die Übersetzung

* Platzhalter für alles, was nicht übersetzt werden darf: Mentions, Emojis, Zeitstempel, Slash-Befehle,
  URLs/Link-Ziele, @everyone/@here, Escapes (\\*), "LLAP" und ECHTER Code.
* Code-Erkennung: ```-Blöcke und Inline-`…` werden auf den Servern auch als Formatierung benutzt (Tabellen,
  Regeln, Hervorhebung) - mit und ohne Sprachangabe. looks_like_code() entscheidet selbst; die Sprachangabe ist
  nur ein Hinweis. Text wird übersetzt (nur der Rahmen ``` bzw. ` wird geschützt), Code bleibt unverändert.
  Im Zweifel gilt der Inhalt als Code (eine übersetzte Code-Zeile ist kaputt, eine unübersetzte Tabelle nur unschön).
* Zierelemente ohne Buchstaben bekommt die Übersetzung nie zu sehen: Zeilen wie "# ------" am Anfang/Ende werden
  abgetrennt und unverändert wieder angefügt, in der Mitte durch Platzhalter ersetzt; formatierte Marker wie
  "***(1)***" oder "**2.**" (Fußnoten, Verweise) werden Platzhalter. Sonst lassen KIs sie gern weg oder ändern sie.
* Leerzeichen um Platzhalter werden beim Zurücksetzen nach dem Vorbild des Originals wiederhergestellt
  (manche Engines liefern "<@123>bitte" statt "<@123> bitte").
* Für Google/Azure/Libre wird Inline-Markdown in HTML-Tags umgewandelt (md_to_html/html_to_md): Diese Dienste
  lassen Tags im HTML-Modus stehen und übersetzen nur den Text dazwischen. Die KI bekommt Markdown direkt.
"""
import html
import re
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

TOKEN_FMT = "__DISCORD_TOKEN_{}__"
TOKEN_RE = re.compile(r"__DISCORD_TOKEN_(\d+)__")

FENCE_RE = re.compile(r"(?<!\\)```([^\n`]*)(\n?)([\s\S]*?)```")
INLINE_CODE_RE = re.compile(r"(?<![`\\])`([^`\n]+?)(?<!\\)`(?!`)")  # \` (Escape) ist kein Code

# Alles, was nie übersetzt wird (Code wird vorher gesondert behandelt)
PROTECT_RE = re.compile(
    r"(?P<link>\]\(<?https?://[^\s)>]*>?\))"   # Ziel eines Markdown-Links: ](https://...) oder ](<https://...>)
    r"|<https?://[^\s>]+>"                      # <https://...> (ohne Vorschau)
    r"|https?://[^\s<>]*[^\s<>.,;:!?)\]]"       # URLs (ohne abschließende Satzzeichen)
    r"|<@[!&]?\d+>|<#\d+>"                      # User-/Rollen-/Kanal-Mentions
    r"|<a?:[a-zA-Z0-9_~]+:\d+>"                 # Custom Emojis
    r"|</[a-zA-Z0-9_ -]+:\d+>"                  # Slash-Command-Mentions
    r"|<t:-?\d+(?::[tTdDfFR])?>"                # Zeitstempel
    r"|@everyone|@here"
    r"|\\[*_~|`>#\\-]"                          # Escapes: \* \_ \~ \| \` \> \# \\ \-
    r"|\bLLAP\b"                                # Gruß/Signatur der Spielfirma - nie übersetzen
    r"|(?P<so>~~(?=[^\s~](?:[^\n]*?[^\s~])?~~))"  # öffnendes ~~ (nur die Markierung, der Text wird übersetzt)
    r"|(?P<sc>(?<=[^\s~])~~)"                     # schließendes ~~
)

# Zeile ganz am Anfang, die nur aus @everyone/@here/Mentions besteht: manche Engines lassen sie samt Platzhalter
# weg - sie wird abgetrennt und danach unverändert wieder vorangestellt (nur wenn danach noch Text folgt).
_LEAD_MENTION = r"(?:@everyone|@here|<@[!&]?\d+>)"
LEAD_LINE_RE = re.compile(rf"^([ \t]*{_LEAD_MENTION}(?:[ \t]+{_LEAD_MENTION})*[ \t]*\n+)(?=[\s\S]*\S)")

# Formatierter Marker ohne Buchstaben: ***(1)***, **(2)**, *3*, __4.__, ||5|| - Inhalt höchstens 12 Zeichen
MARKER_RE = re.compile(r"(?<![*_~|\\\w])(\*{1,3}|_{1,2}|~~|\|\|)(?=\S)([^\n*_~|]{1,12}?)(?<=\S)\1(?![*_~|\w])")
LETTER_RE = re.compile(r"[^\W\d_]")


def _decorative(line: str) -> bool:
    """Zeile ohne Buchstaben, aber mit sichtbarem Inhalt (Trennlinie, Nummer, Zeichen): wird nicht übersetzt."""
    if not line.strip() or "```" in line:           # Code-Rahmen gehören zum Codeblock, nie abtrennen
        return False
    return not LETTER_RE.search(re.sub(r"<a?:[a-zA-Z0-9_~]+:\d+>", "", line))


def _split_edges(text: str) -> Tuple[str, str, str]:
    """(Kopf, Mitte, Ende): Zierzeilen (und Leerzeilen) am Anfang und Ende abtrennen, solange in der Mitte Text bleibt."""
    lines = text.split("\n")
    start, end = 0, len(lines)
    while start < end and (not lines[start].strip() or _decorative(lines[start])):
        start += 1
    while end > start and (not lines[end - 1].strip() or _decorative(lines[end - 1])):
        end -= 1
    if start == end:
        return "", text, ""
    head = "\n".join(lines[:start]) + ("\n" if start else "")
    tail = ("\n" if end < len(lines) else "") + "\n".join(lines[end:])
    return head, "\n".join(lines[start:end]), tail


# ----------------- Code-Erkennung -----------------
CODE_LANGS = {
    "py", "python", "js", "javascript", "ts", "typescript", "json", "sql", "sh", "bash", "zsh", "shell", "console",
    "powershell", "ps1", "bat", "cmd", "c", "h", "cpp", "c++", "cs", "csharp", "java", "kotlin", "kt", "go", "rs",
    "rust", "php", "rb", "ruby", "lua", "swift", "html", "xml", "yaml", "yml", "toml", "ini", "cfg", "dockerfile",
    "regex", "lisp", "r", "perl", "pl", "scala", "dart", "vb", "asm",
}
_KEYWORD_RE = re.compile(
    r"\b(def|return|function|const|let|var|import|class|public|private|static|void|elif|lambda|async|await|"
    r"None|null|undefined|nullptr|SELECT|INSERT|UPDATE|DELETE|WHERE|printf?|console\.log|sudo|pip|npm|git|docker|"
    r"chmod|curl|echo|#include|namespace|struct|interface|foreach|elseif|endif|fn|impl)\b"
)
_CODE_SIGNALS = (
    re.compile(r"[;{}]\s*$", re.M),                              # Zeilenende ; { }
    re.compile(r'"[\w.-]+"\s*:'),                                # JSON-Schlüssel
    re.compile(r"==|!=|=>|->|::|&&|\+\+|:=|\+=|-=|<=|>="),       # Operatoren
    re.compile(r"\b[a-zA-Z_][\w.]*\([^()\n]*\)"),                # Funktionsaufruf name(...)
    re.compile(r"\b0x[0-9a-fA-F]{2,}\b"),                        # Hex-Werte / Fehlercodes
    re.compile(r"^\s*[\w.\[\]]+\s*=\s*\S", re.M),                # Zuweisung am Zeilenanfang
    re.compile(r"(?m)(^(?: {4}|\t)\S.*\n){2,}"),                 # mehrere eingerückte Zeilen
    re.compile(r"\b[\w/-]+\.(?:py|js|ts|json|exe|dll|log|cfg|ini|ya?ml|sh|cs|cpp|h|java|php|sql|toml)\b"),  # Dateien
    re.compile(r"\b[a-z]+_[a-z_]+\b|\b[a-z]+[A-Z][a-zA-Z]+\b"),  # snake_case / camelCase
)
_WORD_RE = re.compile(r"[^\W\d_]{3,}")
_SHORT_WORD_RE = re.compile(r"[^\W\d_]{2,}")


def _code_signals(text: str) -> int:
    return len(_KEYWORD_RE.findall(text)) + sum(1 for rx in _CODE_SIGNALS if rx.search(text))


def _prose(text: str) -> Tuple[int, float]:
    """(Anzahl Wörter mit >= 3 Buchstaben, Anteil der Buchstaben dieser Wörter an allen Nicht-Leerzeichen)."""
    words = _WORD_RE.findall(text)
    nonspace = len(re.sub(r"\s", "", text)) or 1
    return len(words), sum(len(w) for w in words) / nonspace


def looks_like_code(content: str, lang: str = "", inline: bool = False) -> bool:
    """True = Inhalt ist (vermutlich) Code und bleibt unverändert; False = Text, wird übersetzt."""
    text = content.strip()
    if not text:
        return True
    signals = _code_signals(text)
    words, ratio = _prose(text)
    if inline:
        if not re.search(r"\s", text) or text[0] in "/!$.#>-" or signals:
            return True                          # einzelnes Wort, Befehl, Name, Dateiname, Code-Zeichen
        short = _SHORT_WORD_RE.findall(text)  # kurze Wörter zählen hier mit ("be online at 20 ST")
        short_ratio = sum(len(w) for w in short) / (len(re.sub(r"\s", "", text)) or 1)
        return not (len(short) >= 2 and short_ratio >= 0.6)
    if lang.strip().lower() in CODE_LANGS:
        signals += 1                             # Sprachangabe ist nur ein Hinweis
    if signals == 0:
        return not (words >= 3 and ratio >= 0.35)
    if signals == 1:
        return not (words >= 6 and ratio >= 0.6)
    return True


# ----------------- Platzhalter -----------------
@dataclass
class Placeholder:
    original: str
    glue_before: bool = False   # künstliches Leerzeichen davor wieder entfernen ("Text ~~" -> "Text~~")
    glue_after: bool = False    # künstliches Leerzeichen danach wieder entfernen ("~~ Text" -> "~~Text")
    space_before: bool = False  # im Original stand ein Leerzeichen davor
    space_after: bool = False   # im Original stand ein Leerzeichen danach
    marker: bool = False        # Fußnoten-/Verweis-Marker wie ***(1)*** - darf notfalls ans Zeilenende wandern


@dataclass
class Prepared:
    masked: str
    placeholders: Dict[str, Placeholder] = field(default_factory=dict)
    lead: str = ""
    tail: str = ""

    def has_text(self) -> bool:
        return bool(re.search(r"[^\W\d_]", TOKEN_RE.sub("", self.masked)))


def prepare(text: str) -> Prepared:
    """Ersetzt alles Unübersetzbare durch Platzhalter __DISCORD_TOKEN_n__."""
    phs: Dict[str, Placeholder] = {}
    lead = ""
    if (m := LEAD_LINE_RE.match(text)):
        lead, text = m.group(1), text[m.end():]
    head, text, tail = _split_edges(text)
    lead += head

    def add(original: str, glue_before: bool = False, glue_after: bool = False, marker: bool = False) -> str:
        token = TOKEN_FMT.format(len(phs))
        phs[token] = Placeholder(original, glue_before, glue_after, marker=marker)
        return (" " if glue_before else "") + token + (" " if glue_after else "")

    def fence(m: re.Match) -> str:
        lang, nl, body = m.group(1), m.group(2), m.group(3)
        if looks_like_code(body, lang, inline=False):
            return add(m.group(0))
        # Formatierungs-Block: Rahmen schützen, Inhalt übersetzen
        return add("```" + lang, glue_after=not nl) + nl + body + add("```", glue_before=not body.endswith("\n"))

    def inline(m: re.Match) -> str:
        if looks_like_code(m.group(1), inline=True):
            return add(m.group(0))
        return add("`", glue_after=True) + m.group(1) + add("`", glue_before=True)

    def protect(m: re.Match) -> str:
        if m.group("so"):
            return add(m.group(0), glue_after=True)
        if m.group("sc"):
            return add(m.group(0), glue_before=True)
        if m.group("link"):
            return add(m.group(0), glue_before=True)
        return add(m.group(0))

    def marker(m: re.Match) -> str:
        return m.group(0) if LETTER_RE.search(m.group(2)) else add(m.group(0), marker=True)

    masked = FENCE_RE.sub(fence, text)
    masked = INLINE_CODE_RE.sub(inline, masked)
    masked = PROTECT_RE.sub(protect, masked)
    masked = MARKER_RE.sub(marker, masked)
    # Zierzeilen in der Mitte (ohne Buchstaben, ohne vorhandene Platzhalter) als Ganzes schützen
    masked = "\n".join(add(line) if _decorative(line) and not TOKEN_RE.search(line) else line
                        for line in masked.split("\n"))
    for tm in TOKEN_RE.finditer(masked):  # Leerzeichen-Vorbild merken (künstliche Leerzeichen zählen nicht)
        ph = phs[tm.group(0)]
        ph.space_before = not ph.glue_before and tm.start() > 0 and masked[tm.start() - 1] in " \t"
        ph.space_after = not ph.glue_after and tm.end() < len(masked) and masked[tm.end()] in " \t"
    return Prepared(masked, phs, lead, tail)


# Markdown-Präfix einer Zeile: Einrückung, Zitate (>), Listen (- * + •), Nummern (1.), Überschriften (#), Subtext (-#)
LINE_PREFIX_RE = re.compile(r"^(?:[ \t]*(?:>+[ \t]?|-#[ \t]+|[-*+•][ \t]+|\d{1,3}[.)][ \t]+|#{1,3}[ \t]+))*[ \t]*")


def repair_structure(masked: str, out: str, prep: Prepared) -> Tuple[str, bool]:
    """
    KI-Antwort (noch mit Platzhaltern) an den Zeilenaufbau des Originals angleichen - nur wenn sich die Zeilen
    eindeutig zuordnen lassen (gleich viele nicht-leere Zeilen). Übernommen werden die Zeilenpräfixe (> ## - 1.) und
    die Leerzeilen des Originals; ein verlorener Fußnoten-Marker kommt ans Ende seiner Zeile. Der übersetzte Text
    selbst bleibt unangetastet. Rückgabe: (Text, ob repariert wurde).
    """
    src_lines = masked.split("\n")
    out_lines = [ln for ln in out.strip("\n").split("\n") if ln.strip()]
    if len(out_lines) != sum(1 for ln in src_lines if ln.strip()):
        return out, False
    markers = [t for t, ph in prep.placeholders.items() if ph.marker]
    rebuilt, it = [], iter(out_lines)
    for line in src_lines:
        if not line.strip():
            rebuilt.append(line)
            continue
        got = next(it)
        body = got[LINE_PREFIX_RE.match(got).end():]
        for token in markers:
            if token in line and token not in got:
                body = body.rstrip() + " " + token
        rebuilt.append(LINE_PREFIX_RE.match(line).group(0) + body)
    text = "\n".join(rebuilt)
    return text, text != out


def restore(text: str, prep: Prepared) -> Tuple[str, bool]:
    """Setzt die Originale wieder ein. ok = False, wenn eine Engine einen Platzhalter zerstört hat."""
    ok = True
    for token, ph in prep.placeholders.items():
        before = r"[ \t]*" if ph.glue_before else ""
        after = r"[ \t]*" if ph.glue_after else ""
        idx = token[len("__DISCORD_TOKEN_"):-2]
        exact = re.compile(before + re.escape(token) + after)
        tolerant = re.compile(before + rf"_*\s*DISCORD[\s_]*TOKEN[\s_]*{idx}(?!\d)\s*_*" + after, re.IGNORECASE)

        def repl(m: re.Match, ph=ph) -> str:
            s, start, end = m.string, m.start(), m.end()
            pre = " " if ph.space_before and start > 0 and (s[start - 1].isalnum() or s[start - 1] in ":,;") else ""
            post = " " if ph.space_after and end < len(s) and s[end].isalnum() else ""
            return pre + ph.original + post

        n = 0
        if ph.original.startswith("]("):
            # KI "repariert" Links: "[Text](TOKEN)" bzw. "[Text]( TOKEN )" -> Klammern gehören zum Platzhalter
            text, n = re.subn(r"\]?\(\s*" + re.escape(token) + r"\s*\)", lambda _m, o=ph.original: o, text)
        if n == 0:
            text, n = exact.subn(repl, text)
        if n == 0:
            text, n = tolerant.subn(repl, text)
        if n == 0:
            ok = False
    return prep.lead + text + prep.tail, ok


# ----------------- Markdown <-> HTML (für Google, Azure, Libre) -----------------
_MD_TO_HTML = (
    (re.compile(r"\*\*\*(?=\S)(.+?)(?<=\S)\*\*\*"), r"<b><i>\1</i></b>"),
    (re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*"), r"<b>\1</b>"),
    (re.compile(r"__(?=\S)(.+?)(?<=\S)__"), r"<u>\1</u>"),
    (re.compile(r"\|\|(?=\S)(.+?)(?<=\S)\|\|"), r"<mark>\1</mark>"),
    (re.compile(r"(?<![*\w])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![*\w])"), r"<i>\1</i>"),
    (re.compile(r"(?<![\w_])_(?=[^\s_])(.+?)(?<=[^\s_])_(?![\w_])"), r"<em>\1</em>"),
)
_HTML_TO_MD = (("b", "**"), ("i", "*"), ("em", "_"), ("u", "__"), ("mark", "||"))
_TAG_NAMES = "|".join(t for t, _ in _HTML_TO_MD)


_LINK_RE = re.compile(r"\[([^\[\]\n]*?)\s*(__DISCORD_TOKEN_\d+__)")
_A_RE = re.compile(r'<\s*a\s+id\s*=\s*"\s*(__DISCORD_TOKEN_\d+__)\s*"\s*>(.*?)<\s*/\s*a\s*>', re.I | re.S)


def link_tokens(prep: "Prepared") -> set:
    """Platzhalter, die ein Link-Ziel "](url)" vertreten."""
    return {t for t, ph in prep.placeholders.items() if ph.original.startswith("](")}


def md_to_html(line: str, links: Optional[set] = None) -> str:
    """Eine Zeile Markdown (mit Platzhaltern) -> HTML für Engines im HTML-Modus.
    links: Platzhalter von Link-Zielen - "[Text TOKEN" wird zu <a id="TOKEN">Text</a>, sonst hängen manche
    Engines (Libre) ein "]" ans Satzende, weil sie das "[" für eine offene Klammer halten."""
    if links:
        line = _LINK_RE.sub(lambda m: f'\x01{m.group(2)}\x02{m.group(1)}\x03' if m.group(2) in links else m.group(0), line)
    tokens = []

    def hide(m: re.Match) -> str:  # Platzhalter enthalten "__" - vor der Umwandlung verstecken
        tokens.append(m.group(0))
        return f"\x00{len(tokens) - 1}\x00"

    text = html.escape(TOKEN_RE.sub(hide, line), quote=False)
    for rx, repl in _MD_TO_HTML:
        text = rx.sub(repl, text)
    text = re.sub(r"\x01(\x00\d+\x00)\x02(.*?)\x03", r'<a id="\1">\2</a>', text)
    return re.sub(r"\x00(\d+)\x00", lambda m: tokens[int(m.group(1))], text)


def html_to_md(text: str) -> str:
    """Antwort einer Engine im HTML-Modus -> Markdown."""
    text = _A_RE.sub(lambda m: "[" + m.group(2).strip() + " " + m.group(1), text)   # Link -> "[Text TOKEN"
    # Leerzeichen innerhalb der Tags nach außen schieben ("<b> Text </b>" -> " <b>Text</b> "), aber nie doppelt
    text = re.sub(rf"(\s*)<\s*({_TAG_NAMES})\s*>\s+", lambda m: " <" + m.group(2) + ">", text, flags=re.I)
    text = re.sub(rf"\s+<\s*/\s*({_TAG_NAMES})\s*>(\s*)", lambda m: "</" + m.group(1) + "> ", text, flags=re.I)
    for tag, md in _HTML_TO_MD:
        text = re.sub(rf"<\s*/?\s*{tag}\s*>", md, text, flags=re.I)
    return html.unescape(text).strip()
