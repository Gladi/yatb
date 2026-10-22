"""
YATB - Prüfung einer Übersetzung (nach dem Zurücksetzen der Platzhalter)

problems(original, übersetzung) liefert die Gründe, warum eine Übersetzung verworfen werden sollte (leer = ok).
Fällt eine Engine durch, geht die Nachricht an die nächste Stufe der Kette. Abgeleitet aus den Fehlern im
Benchmark: Die KI-Fehler waren fast immer strukturell (Links, Fettdruck, Listen, Absätze, "LLAP").
Unübersetzbares (Mentions, URLs, Code, LLAP, ...) schützen schon die Platzhalter - geht einer verloren, verwirft
markup.restore() das Ergebnis vorher.

Die Gründe sind kurze Kennungen (für stats.db und das Testskript): empty, commentary, length, fences, links,
urls, everyone, llap, bold, underline, strike, spoiler, italic, lists, numbered, quotes, headers, subtext, paragraphs.
"""
import re
from typing import List

FENCE_RE = re.compile(r"(?<!\\)```[^\n`]*\n?[\s\S]*?```")
INLINE_CODE_RE = re.compile(r"(?<![`\\])`[^`\n]+?(?<!\\)`(?!`)")
ESCAPE_RE = re.compile(r"\\[*_~|`>#\\-]")
URL_RE = re.compile(r"https?://[^\s)>]+")
BROKEN_LINK_RE = re.compile(r"\]\(\s*\]\(|\[\]\(|\(\s*\]\(")   # "](](", "[](", "((](" - kaputte Link-Syntax
COMMENTARY_RE = re.compile(
    r"</?(?:think|text|context|previous_translation)>"
    r"|^\s*(?:here is|here's|sure[,!]|translation|übersetzung|traduction|traducción|traduzione|перевод)\b[^\n]{0,40}:",
    re.IGNORECASE,
)
TOKENS = {
    "bold": r"\*\*", "underline": r"__", "strike": r"~~", "spoiler": r"\|\|", "links": r"\]\(<?https?://",
    "everyone": r"@(?:everyone|here)",
}
LINES = {
    "quotes": r"^>{1,3} ", "headers": r"^#{1,3} ", "subtext": r"^-# ", "lists": r"^\s*[-*•] ", "numbered": r"^\s*\d{1,3}[.)] ",
}


def _plain(text: str) -> str:
    """Code und Escapes entfernen - deren Inhalt ist kein Markdown."""
    return ESCAPE_RE.sub("", INLINE_CODE_RE.sub("", FENCE_RE.sub("", text)))


def _italics(text: str) -> int:
    t = re.sub(r"(?m)^\s*\* ", "", text)                                   # Listenpunkte "* "
    stars = len(re.findall(r"(?<!\*)\*(?!\*)", t.replace("***", "*").replace("**", "")))
    unders = len(re.findall(r"(?<![\w_])_(?=[^\s_])[^_\n]+?(?<=[^\s_])_(?![\w_])", t))
    return stars + unders


# Bei stark formatierten Nachrichten (ab TOLERANCE_MIN_PAIRS Paaren) darf eine Betonung mehr oder weniger sein - wenn
# jede Zeile ausgeglichen bleibt (keine sichtbaren Einzel-Sternchen). Spoiler, Links und Platzhalter bleiben streng.
TOLERANT = {"bold", "underline", "strike"}
TOLERANCE_MIN_PAIRS = 4


def _balanced(text: str, rx: str) -> bool:
    return all(len(re.findall(rx, line)) % 2 == 0 for line in text.split("\n"))


def _close(src_n: int, out_n: int, per_pair: int = 2) -> bool:
    return src_n >= TOLERANCE_MIN_PAIRS * per_pair and abs(src_n - out_n) <= per_pair


def _paragraphs(text: str) -> int:
    return len([p for p in re.split(r"\n\s*\n", FENCE_RE.sub("CODE", text).strip()) if p.strip()])


def problems(src: str, out: str, strict: bool = True) -> List[str]:
    """Gründe gegen die Übersetzung. strict=False (letzte Stufe, Libre): nur leer/Kommentar prüfen."""
    if not out or not out.strip():
        return ["empty"]
    found: List[str] = []
    if COMMENTARY_RE.search(out) and not COMMENTARY_RE.search(src):
        found.append("commentary")
    if not strict:
        return found
    if len(src) >= 20 and not 0.3 <= len(out) / len(src) <= 3.0:
        found.append("length")
    if len(FENCE_RE.findall(src)) != len(FENCE_RE.findall(out)):
        found.append("fences")
    if sorted(URL_RE.findall(src)) != sorted(URL_RE.findall(out)):
        found.append("urls")
    if BROKEN_LINK_RE.search(out) and not BROKEN_LINK_RE.search(src):
        found.append("links")
    if "LLAP" in src and "LLAP" not in out:
        found.append("llap")
    s, o = _plain(src), _plain(out)
    for reason, rx in TOKENS.items():
        src_n, out_n = len(re.findall(rx, s)), len(re.findall(rx, o))
        if src_n != out_n and not (reason in TOLERANT and _close(src_n, out_n) and _balanced(o, rx)):
            found.append(reason)
    src_i, out_i = _italics(s), _italics(o)
    if src_i != out_i and not (_close(src_i, out_i) and all(_italics(line) % 2 == 0 for line in o.split("\n"))):
        found.append("italic")
    for reason, rx in LINES.items():
        if len(re.findall(rx, s, re.M)) != len(re.findall(rx, o, re.M)):
            found.append(reason)
    if abs(_paragraphs(src) - _paragraphs(out)) > 1:
        found.append("paragraphs")
    return found
