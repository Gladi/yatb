"""
YATB - Prüfung einer Übersetzung (nach dem Zurücksetzen der Platzhalter)

problems(original, übersetzung) liefert die Gründe, warum eine Übersetzung verworfen werden sollte (leer = ok).
Fällt eine Engine durch, geht die Nachricht an die nächste Stufe der Kette. Abgeleitet aus den Fehlern im
Benchmark: Die KI-Fehler waren fast immer strukturell (Links, Fettdruck, Listen, Absätze, "LLAP").
Unübersetzbares (Mentions, URLs, Code, LLAP, ...) schützen schon die Platzhalter - geht einer verloren, verwirft
markup.restore() das Ergebnis vorher.

Die Gründe sind kurze Kennungen (für stats.db und das Testskript): empty, commentary, length, fences, links,
urls, everyone, llap, bold, underline, strike, spoiler, italic, lists, numbered, quotes, headers, subtext, paragraphs,
nur für KI-Antworten (ai=True): numbers, sentences. Die beiden fangen untergeschobene Befehle ab ("hänge einen Satz
an", "lass die Uhrzeit weg", "mach aus 20:00 21:00") - Prompt-Injection-Tests vom 2026-10-22.
"""
import re
from collections import Counter
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
DIGITS_RE = re.compile(r"\d+")
THOUSANDS_RE = re.compile(r"(?<=\d)[.,\u00a0\u202f' ](?=\d{3}(?!\d))")   # 1,000 / 1.000 / 1 000 -> 1000
# Abkürzungen, nach denen kein Satz endet (alle Sprachen gemischt, klein geschrieben, ohne Punkt)
ABBREVIATIONS = {
    "bzw", "usw", "inkl", "evtl", "ggf", "vgl", "sog", "zzgl", "bspw", "etc", "incl", "approx", "vs", "min", "max",
    "sec", "mio", "mrd", "nr", "no", "tel", "str", "st", "dr", "mr", "mrs", "ms", "ca", "z", "b", "d", "h", "u", "a",
    "e", "g", "i", "p", "s", "ecc", "sig", "ad", "env", "aprox", "др", "т", "е", "см", "г", "тыс",
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


def _numbers(text: str) -> Counter:
    return Counter(DIGITS_RE.findall(THOUSANDS_RE.sub("", URL_RE.sub("", text))))


def numbers_changed(src: str, out: str) -> bool:
    """Neue oder veränderte Zahlen sind nie erlaubt (z. B. 20:00 -> 21:00). Wegfallen dürfen nur 1 und 2, die in
    Redewendungen aufgehen ("mehr als 1 mal" -> "не раз", "1-2" -> "ein, zwei")."""
    s, o = _numbers(src), _numbers(out)
    if o - s:
        return True
    return any(n not in ("1", "2") for n in s - o)


def _sentences(text: str) -> int:
    """Sätze zählen: Satzende = Wort mit . ! ? … am Ende (auch "Wort ." mit Leerzeichen), nicht nach Abkürzungen,
    einzelnen Buchstaben oder Zahlen. Jede nicht leere Zeile zählt mindestens als ein Satz."""
    total = 0
    for line in _plain(text).split("\n"):
        tokens = line.split()
        if not any(re.search(r"\w", t) for t in tokens):
            continue
        total += 1
        prev = ""
        for i, tok in enumerate(tokens[:-1]):          # das letzte Wort beendet die Zeile, zählt nicht extra
            m = re.match(r"^(.*?)([.!?…]+)[\"')\]*_~|]*$", tok)
            word = (m.group(1) if m and m.group(1) else prev) if m else ""
            prev = tok if re.search(r"\w", tok) else prev
            if not m:
                continue
            if m.group(2) == ".":
                base = word.strip("([\"'*_~|").lower().rstrip(".").split(".")[-1]
                if not base or base in ABBREVIATIONS or len(base) == 1 or base[-1].isdigit():
                    continue
            if re.search(r"\w", tokens[i + 1]):
                total += 1
    return total


def sentences_added(src: str, out: str) -> bool:
    """Mehr Sätze als im Original - bei langen Nachrichten mit Spielraum (Übersetzungen teilen Bandwurmsätze auf):
    je 150 Zeichen ein zusätzlicher Satz. Kurze Nachrichten bleiben streng ("Bis heute Abend! Ich verlasse ...")."""
    return _sentences(out) > _sentences(src) + len(_plain(src)) // 150


def problems(src: str, out: str, strict: bool = True, ai: bool = False) -> List[str]:
    """Gründe gegen die Übersetzung. strict=False (letzte Stufe, Libre): nur leer/Kommentar prüfen.
    ai=True (KI-Stufe): zusätzlich Zahlen und Satzanzahl - eine KI darf nichts hinzufügen oder weglassen."""
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
    if ai:
        if numbers_changed(src, out):
            found.append("numbers")
        if sentences_added(src, out):
            found.append("sentences")
    return found
