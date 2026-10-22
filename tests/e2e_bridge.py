"""
Ende-zu-Ende-Test der Bridge gegen den Test-Bot (nur Test-Server!).

Der "Tester"-Bot (YATB_TEST_DRIVER_TOKEN) postet die Nachrichten aus tests/e2e_messages.py in den Quellkanal,
der Test-Bot (BRIDGE_BOTS=1) überträgt sie. Das Skript prüft per Discord-REST-API, ob die Übersetzungen in allen
anderen Kanälen der Bridge ankommen, die Discord-Formatierung erhalten bleibt und Antworten/Edits/Löschungen
synchron sind.

Die Testnachrichten bleiben in den Kanälen. Jeder Lauf beginnt und endet mit einem START-/STOP-Marker
(Laufnummer, Code-Version, optional Commit). Gelöscht wird nur eine eigene Lösch-Probe.

Läuft im Test-Container (dort liegen Token und Test-DB):
    docker exec discord-bot-test python tests/e2e_bridge.py [--only chat|ann|markdown] [--label <commit>]
    docker exec discord-bot-test python tests/e2e_bridge.py --limit-test [--label <commit>]

Exit-Code 0 = alle Bridge-Prüfungen bestanden. Struktur-Abweichungen werden als WARN gemeldet,
weil sie von der Engine abhängen.
"""
import argparse
import asyncio
import datetime
import glob
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
import tomllib
import urllib.parse
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import aiohttp

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Bot-Module (validator)
import e2e_messages as msgs  # noqa: E402
import validator  # noqa: E402

API = "https://discord.com/api/v10"
APP_DIR = "/app" if os.path.isdir("/app") else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.environ.get("YATB_DB_FILE") or os.path.join(APP_DIR, "data", "bridge_bot.db")
RUNS_FILE = os.path.join(os.path.dirname(DB_FILE), "e2e_runs.json")
TAG_RE = re.compile(r"\s(\[[^\]]+\])$")
WAIT = 60.0          # Sekunden pro Nachricht und Zielkanal
CHUNK_WAIT = 2.5     # danach noch auf Folgeteile langer Nachrichten warten
NO_PINGS = {"parse": []}  # @everyone/Mentions im Test nie wirklich auslösen


class Discord:
    def __init__(self, session: aiohttp.ClientSession, token: str):
        self.s, self.h = session, {"Authorization": f"Bot {token}"}

    async def req(self, method: str, path: str, **kw):
        for _ in range(6):
            async with self.s.request(method, API + path, headers=self.h, **kw) as r:
                if r.status == 429:
                    await asyncio.sleep(float((await r.json()).get("retry_after", 1.0)) + 0.2)
                    continue
                data = await r.json() if r.content_type == "application/json" else None
                return r.status, data
        return 429, None


@dataclass
class Case:
    name: str
    kind: str
    text: str
    expect: Dict[str, List[str]]


def build_cases(only: Optional[str], me: str, role: str, channel: str, emoji: str = ":yatb:") -> List[Case]:
    out = []
    for entry in msgs.MESSAGES:
        name, kind, text = entry[:3]
        if only and kind != only:
            continue
        text = text.replace("{ME}", me).replace("{ROLE}", role).replace("{CHANNEL}", channel).replace("{EMOJI}", emoji)
        out.append(Case(name, kind, text, entry[3] if len(entry) > 3 else {}))
    return out


# ----------------- Laufnummer und Version -----------------
def code_version() -> str:
    h = hashlib.sha256()
    for path in sorted(glob.glob(os.path.join(APP_DIR, "*.py")) + glob.glob(os.path.join(APP_DIR, "config", "*.toml"))):
        with open(path, "rb") as fh:
            h.update(os.path.basename(path).encode() + fh.read())
    return h.hexdigest()[:8]


def next_run_number() -> int:
    try:
        with open(RUNS_FILE, encoding="utf-8") as fh:
            last = int(json.load(fh).get("last_run", 0))
    except (OSError, ValueError):
        last = 0
    with open(RUNS_FILE, "w", encoding="utf-8") as fh:
        json.dump({"last_run": last + 1}, fh)
    return last + 1


# ----------------- Strukturprüfungen -----------------
FENCE_RE = re.compile(r"```([^\n`]*)\n?([\s\S]*?)```")
INLINE_CODE_RE = re.compile(r"(?<!`)`[^`\n]+`(?!`)")
URL_RE = re.compile(r"https?://[^\s)>]+")
EMOJI_RE = re.compile(r"<a?:\w+:\d+>")
_SPECIAL_RE = re.compile(r"<@[!&]?\d+>|<#\d+>|<t:\d+(?::\w)?>|`[^`\n]+`|\]\(<?https?://[^)\s]+\)|<?https?://[^\s>)]+>?")


def _strip_fences(text: str) -> str:
    return FENCE_RE.sub("CODE", text)


def code_expectation_problems(case: "Case", out: str) -> List[str]:
    """Pro ```-Block und Inline-`…` (in Reihenfolge): "keep" = unverändert, "translate" = Inhalt übersetzt."""
    problems = []
    a, b = FENCE_RE.findall(case.text), FENCE_RE.findall(out)
    if len(a) != len(b):
        return [f"Code-Blöcke {len(a)}->{len(b)}"]
    for n, (want, (lang_a, body_a), (lang_b, body_b)) in enumerate(zip(case.expect.get("blocks", []), a, b), 1):
        same = (lang_a.strip(), body_a.strip()) == (lang_b.strip(), body_b.strip())
        if want == "keep" and not same:
            problems.append(f"Code-Block {n} verändert (ist Code)")
        if want == "translate" and body_a.strip() == body_b.strip():
            problems.append(f"Code-Block {n} nicht übersetzt (ist Text)")
    ia, ib = INLINE_CODE_RE.findall(_strip_fences(case.text)), INLINE_CODE_RE.findall(_strip_fences(out))
    if len(ia) == len(ib):
        for n, (want, x, y) in enumerate(zip(case.expect.get("inline", []), ia, ib), 1):
            if want == "keep" and x != y:
                problems.append(f"Inline-Code {n} verändert (ist Code)")
            if want == "translate" and x == y:
                problems.append(f"Inline-Code {n} nicht übersetzt (ist Text)")
    return problems


def spacing_problems(src: str, out: str) -> List[str]:
    """Leerzeichen vor/nach Mentions, Code, Zeitstempeln und Links bleiben erhalten (z. B. nicht ')und')."""
    lost = []
    s, o = _strip_fences(src), _strip_fences(out)
    for m in _SPECIAL_RE.finditer(s):
        token = m.group(0)
        pos = o.find(token)
        if pos < 0:
            continue
        before_src = m.start() > 0 and s[m.start() - 1].isspace()
        after_src = m.end() < len(s) and s[m.end()].isspace()
        before_out = pos > 0 and o[pos - 1].isspace()
        after_out = pos + len(token) < len(o) and o[pos + len(token)].isspace()
        if (before_src and not before_out) or (after_src and not after_out):
            lost.append(short(token, 25))
    return [f"Leerzeichen verloren um {', '.join(lost)}"] if lost else []


def structure_problems(case: "Case", out: str) -> List[str]:
    """Dieselben Prüfregeln wie der Bot (validator.py) plus Code-Erwartung, Emojis und Leerzeichen."""
    problems = validator.problems(case.text, out)
    a, b = len(EMOJI_RE.findall(case.text)), len(EMOJI_RE.findall(out))
    if a != b:
        problems.append(f"Custom-Emojis {a}->{b}")
    return problems + code_expectation_problems(case, out) + spacing_problems(case.text, out)


# ----------------- Discord-Hilfen -----------------
def load_bridge(source_name: str, channels: Dict[str, dict]) -> Dict[str, str]:
    """{channel_id: language} der Bridge des Quellkanals (aus der Test-DB, nur lesend)."""
    src = next((c for c in channels.values() if c["name"] == source_name), None)
    if src is None:
        sys.exit(f"Quellkanal #{source_name} nicht gefunden.")
    db = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
    row = db.execute("SELECT guild_id, bridge_id FROM bridge_channels WHERE channel_id = ?", (int(src["id"]),)).fetchone()
    if row is None:
        sys.exit(f"#{source_name} ist keiner Bridge zugeordnet (/yatb add).")
    rows = db.execute("SELECT channel_id, language FROM bridge_channels WHERE guild_id = ? AND bridge_id = ?", row).fetchall()
    return {str(cid): lang for cid, lang in rows}


async def collect_mirror(d: Discord, channel_id: str, after_id: str, deadline: float) -> Optional[Tuple[dict, str]]:
    """(erste Spiegel-Nachricht, zusammengesetzter Inhalt aller Teile) im Zielkanal nach after_id."""
    while time.monotonic() < deadline:
        st, found = await d.req("GET", f"/channels/{channel_id}/messages", params={"after": after_id, "limit": 50})
        if st == 200 and any(m.get("webhook_id") for m in found or []):
            await asyncio.sleep(CHUNK_WAIT)
            _, found = await d.req("GET", f"/channels/{channel_id}/messages", params={"after": after_id, "limit": 50})
            hooks = sorted((m for m in found or [] if m.get("webhook_id")), key=lambda m: int(m["id"]))
            return hooks[0], "\n".join(m.get("content", "") for m in hooks)
        await asyncio.sleep(1.0)
    return None


def tag_of(msg: dict) -> str:
    m = TAG_RE.search(msg["author"]["username"])
    return m.group(1) if m else "?"


def short(text: str, n: int = 90) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


class Report:
    def __init__(self):
        self.fails = self.warns = 0
        self.by_tag: Dict[str, Counter] = {}
        self.problem_types: Counter = Counter()

    def line(self, status: str, case: str, target: str, info: str = ""):
        if status == "FAIL":
            self.fails += 1
        elif status == "WARN":
            self.warns += 1
        print(f"  [{status:4}] {case:<24} -> #{target:<9} {info}")


async def post(d: Discord, channel_id: str, content: str, reply_to: Optional[str] = None) -> Tuple[int, Optional[dict]]:
    body = {"content": content, "allowed_mentions": NO_PINGS}
    if reply_to:
        body["message_reference"] = {"message_id": reply_to}
    return await d.req("POST", f"/channels/{channel_id}/messages", json=body)


async def post_and_wait(d: Discord, src_id: str, targets: List[str], text: str) -> Tuple[Optional[dict], Dict[str, Optional[Tuple[dict, str]]]]:
    t0 = time.monotonic()
    st, msg = await post(d, src_id, text)
    if st != 200:
        return None, {}
    return msg, {t: await collect_mirror(d, t, msg["id"], t0 + WAIT) for t in targets}


async def setup(d: Discord, source: str):
    _, me = await d.req("GET", "/users/@me")
    _, guilds = await d.req("GET", "/users/@me/guilds")
    if len(guilds) != 1:
        sys.exit(f"Tester muss auf genau einem Server sein (ist auf {len(guilds)}).")
    _, chans = await d.req("GET", f"/guilds/{guilds[0]['id']}/channels")
    channels = {c["id"]: c for c in chans if c.get("type") == 0}
    bridge = load_bridge(source, channels)
    src_id = next(cid for cid in bridge if channels.get(cid, {}).get("name") == source)
    targets = [cid for cid in bridge if cid != src_id]
    return me, guilds[0], channels, bridge, src_id, targets


# ----------------- Haupttest -----------------
async def main(args) -> int:
    token = os.environ.get("YATB_TEST_DRIVER_TOKEN")
    if not token:
        sys.exit("YATB_TEST_DRIVER_TOKEN fehlt (.env.test).")
    run_no, version = next_run_number(), code_version()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    what = "limit test" if args.limit_test else (args.only or "full")
    label = f" · commit {args.label}" if args.label else ""
    async with aiohttp.ClientSession() as s:
        d = Discord(s, token)
        me, guild, channels, bridge, src_id, targets = await setup(d, args.source)
        print(f"Testlauf #{run_no} ({what}) · Code {version}{label} · {stamp}")
        print(f"Server '{guild['name']}', Quelle #{args.source} ({bridge[src_id]}), "
              f"Ziele: {', '.join('#' + channels[t]['name'] + ' (' + bridge[t] + ')' for t in targets)}\n")
        await post_and_wait(d, src_id, targets, f"🧪 **YATB test START** · run #{run_no} ({what}) · code {version}{label} · {stamp}")
        if args.limit_test:
            ok = await limit_test(d, channels, src_id, targets, args)
            result = "OK" if ok else "FAILED"
            rc = 0 if ok else 1
        else:
            rep = await bridge_test(d, me, guild, channels, src_id, targets, args)
            result = f"{rep.fails} failures, {rep.warns} warnings"
            rc = 1 if rep.fails else 0
        await post_and_wait(d, src_id, targets, f"🧪 **YATB test STOP** · run #{run_no} ({what}) · {result}")
    if args.limit_test:  # erst nach dem STOP-Marker aufräumen, damit die nächste Prüfung die Meldungen neu auslöst
        _google_limit_state(reset_flags=True)
        print("Warnstufen des Test-Keys zurückgesetzt. Jetzt chars_month in data/config-test wieder auf den Normalwert setzen.")
    return rc


async def bridge_test(d: Discord, me, guild, channels, src_id, targets, args) -> Report:
    rep = Report()
    _, emojis = await d.req("GET", f"/guilds/{guild['id']}/emojis")
    yatb = next((e for e in emojis or [] if e.get("name") == "yatb"), None)
    emoji = f"<{'a' if yatb and yatb.get('animated') else ''}:yatb:{yatb['id']}>" if yatb else ":yatb:"
    cases = build_cases(args.only, me["id"], guild["id"], targets[0], emoji)
    print(f"{len(cases)} Nachrichten\n")
    first_id: Optional[str] = None
    for case in cases:
        t0 = time.monotonic()
        msg, mirrors = await post_and_wait(d, src_id, targets, case.text)
        if msg is None:
            rep.line("FAIL", case.name, "-", "Senden fehlgeschlagen")
            continue
        first_id = first_id or msg["id"]
        for t, got in mirrors.items():
            name = channels[t]["name"]
            if got is None:
                rep.line("FAIL", case.name, name, f"keine Übertragung nach {WAIT:.0f}s")
                continue
            first, content = got
            tag = tag_of(first)
            problems = structure_problems(case, content)
            if tag == "[Raw]":
                problems.insert(0, "unübersetzt [Raw]")
            if args.expect_tag and tag not in (args.expect_tag, "[Raw]", "[Direct]"):  # [Raw] = Rückfall, auch ohne Dritte
                rep.line("FAIL", case.name, name, f"Tag {tag} statt {args.expect_tag}")
                continue
            rep.by_tag.setdefault(tag, Counter())["WARN" if problems else "OK"] += 1
            rep.problem_types.update(p.split(" ")[0] for p in problems)
            info = f"{time.monotonic() - t0:4.1f}s {tag:<9} " + ("!! " + "; ".join(problems) if problems else short(content, 70))
            rep.line("WARN" if problems else "OK", case.name, name, info)

    if first_id:
        await sync_tests(d, rep, channels, src_id, targets, first_id)

    print(f"\nErgebnis: {rep.fails} Fehler, {rep.warns} Warnungen.")
    for tag, cnt in sorted(rep.by_tag.items()):
        print(f"  {tag:<9} OK {cnt['OK']:>3} | WARN {cnt['WARN']:>3}")
    if rep.problem_types:
        print("  Häufigste Abweichungen: " + ", ".join(f"{k} ({v})" for k, v in rep.problem_types.most_common(10)))
    return rep


async def sync_tests(d: Discord, rep: Report, channels, src_id, targets, first_id: str):
    print("\nAntwort, Edit, Löschen:")
    t0 = time.monotonic()
    st, reply = await post(d, src_id, msgs.REPLY_TEXT, reply_to=first_id)
    if st == 200:
        for t in targets:
            got = await collect_mirror(d, t, reply["id"], t0 + WAIT)
            name = channels[t]["name"]
            if got is None:
                rep.line("FAIL", "reply", name, "keine Übertragung")
            elif "↩️" in got[1] and "discord.com/channels/" in got[1]:
                rep.line("OK", "reply", name, "Antwort-Kopf mit Link vorhanden")
            else:
                rep.line("FAIL", "reply", name, "Antwort-Kopf fehlt: " + short(got[1]))

    probe, mirrors = await post_and_wait(d, src_id, targets, msgs.EDIT_PROBE)
    if probe:
        await d.req("PATCH", f"/channels/{src_id}/messages/{probe['id']}", json={"content": msgs.EDIT_TEXT, "allowed_mentions": NO_PINGS})
        for t, got in mirrors.items():
            name, deadline, edited = channels[t]["name"], time.monotonic() + WAIT, None
            while got and time.monotonic() < deadline:
                st, cur = await d.req("GET", f"/channels/{t}/messages/{got[0]['id']}")
                if st == 200 and cur.get("edited_timestamp") and cur.get("content") != got[0].get("content"):
                    edited = cur
                    break
                await asyncio.sleep(1.0)
            rep.line("OK" if edited else "FAIL", "edit", name, short(edited["content"], 80) if edited else "Spiegel nicht bearbeitet")

    await reaction_tests(d, rep, channels, src_id, targets)

    probe, mirrors = await post_and_wait(d, src_id, targets, msgs.DELETE_PROBE)
    if probe:
        await d.req("DELETE", f"/channels/{src_id}/messages/{probe['id']}")
        for t, got in mirrors.items():
            name, deadline, gone = channels[t]["name"], time.monotonic() + WAIT, False
            while got and time.monotonic() < deadline:
                st, _ = await d.req("GET", f"/channels/{t}/messages/{got[0]['id']}")
                if st == 404:
                    gone = True
                    break
                await asyncio.sleep(1.0)
            rep.line("OK" if gone else "FAIL", "delete", name, "Spiegel gelöscht" if gone else "Spiegel noch da")


async def _reaction_counts(d: Discord, channel_id: str, message_id: str) -> Dict[str, int]:
    st, cur = await d.req("GET", f"/channels/{channel_id}/messages/{message_id}")
    return {r["emoji"]["name"]: r["count"] for r in (cur.get("reactions") or [])} if st == 200 else {}


async def _wait_reactions(d: Discord, places, emoji: str, present: bool) -> Dict[str, bool]:
    """{kanal: erfüllt} - wartet, bis emoji auf allen Nachrichten da (present) bzw. weg ist."""
    deadline, done = time.monotonic() + WAIT, {}
    while time.monotonic() < deadline:
        for ch, mid in places:
            done[ch] = (emoji in await _reaction_counts(d, ch, mid)) == present
        if all(done.values()):
            break
        await asyncio.sleep(1.5)
    return done


async def reaction_tests(d: Discord, rep: Report, channels, src_id, targets):
    """Reaktion auf das Original und auf eine Übersetzung -> überall sichtbar; zurücknehmen -> überall weg."""
    probe, mirrors = await post_and_wait(d, src_id, targets, msgs.REACT_PROBE)
    if not probe or not all(mirrors.values()):
        rep.line("FAIL", "reaction", "-", "Testnachricht nicht gespiegelt")
        return
    copies = [(src_id, probe["id"])] + [(t, got[0]["id"]) for t, got in mirrors.items()]
    for emoji, (ch, mid) in (("👍", copies[0]), ("🎉", copies[1])):
        enc = urllib.parse.quote(emoji)
        await d.req("PUT", f"/channels/{ch}/messages/{mid}/reactions/{enc}/@me")
        others = [c for c in copies if c != (ch, mid)]
        for place, ok in (await _wait_reactions(d, others, emoji, True)).items():
            rep.line("OK" if ok else "FAIL", f"reaction {emoji} add", channels[place]["name"],
                     "gespiegelt" if ok else "nicht gespiegelt")
        await d.req("DELETE", f"/channels/{ch}/messages/{mid}/reactions/{enc}/@me")
        for place, ok in (await _wait_reactions(d, others, emoji, False)).items():
            rep.line("OK" if ok else "FAIL", f"reaction {emoji} remove", channels[place]["name"],
                     "wieder entfernt" if ok else "Spiegel-Reaktion noch da")


# ----------------- Opt-out des Tester-Bots (nur Test-DB) -----------------
async def set_privacy(local: bool) -> int:
    async with aiohttp.ClientSession() as s:
        _, me = await Discord(s, os.environ["YATB_TEST_DRIVER_TOKEN"]).req("GET", "/users/@me")
    db = sqlite3.connect(DB_FILE, timeout=10)
    db.execute("""INSERT INTO user_privacy (user_id, local_only) VALUES (?, ?)
                  ON CONFLICT(user_id) DO UPDATE SET local_only = excluded.local_only""", (int(me["id"]), int(local)))
    db.commit()
    print(f"Tester-Bot: Opt-out 'nur lokal' = {local}. Test-Bot jetzt neu starten (lädt den Status beim Start).")
    return 0


# ----------------- Limit-Test (Google) -----------------
def _google_limit_state(reset_flags: bool) -> Tuple[str, int, int, str]:
    """(fingerprint, Verbrauch diesen Monat, Monatslimit laut Config, Stufe). Setzt auf Wunsch die Warnstufen zurück."""
    month = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m")
    with open(os.path.join(APP_DIR, "config", "providers.toml"), "rb") as fh:
        limit = int(tomllib.load(fh)["providers"]["google_translate"]["limits"]["free"]["chars_month"])
    db = sqlite3.connect(DB_FILE, timeout=10)
    row = db.execute("SELECT fingerprint, tier FROM api_keys WHERE provider = 'google_translate' ORDER BY id LIMIT 1").fetchone()
    if row is None:
        sys.exit("Kein Google-Key auf dem Test-Server (/yatb keys add).")
    fp, tier = row
    used = db.execute("SELECT COALESCE(chars, 0) FROM key_usage WHERE fingerprint = ? AND period = ?", (fp, month)).fetchone()
    if reset_flags:  # nur Test-DB: Warnstufen des Monats zurücksetzen, damit der Test sie neu auslösen kann
        db.execute("UPDATE key_usage SET warn_90 = 0, warn_95 = 0, warn_100 = 0 WHERE fingerprint = ? AND period = ?", (fp, month))
        db.commit()
    db.close()
    return fp, int(used[0]) if used else 0, limit, tier


async def limit_test(d: Discord, channels, src_id, targets, args) -> bool:
    """
    Szenario "noch etwas Luft": Rest ca. 800 Zeichen.
      1. kurze Nachricht            -> Google
      2. lange Nachricht            -> passt nicht mehr -> andere Engine, KEINE Meldung "Limit erreicht"
      3. zwei kurze Nachrichten     -> wieder Google (Rest wird genutzt)
      4. kurze Nachrichten, bis Google nicht mehr genutzt wird -> Meldung "Limit erreicht" (< 1 % Rest)
      5. eine weitere kurze         -> nicht Google (Key bis Monatsende erschöpft)
    Vorbereitung: data/config-test/providers.toml google_translate.limits.free.chars_month = Verbrauch + 800,
    Test-Bot neu starten.
    """
    log_ch = next((c for c in channels.values() if c["name"] == args.log_channel), None)
    if log_ch is None:
        sys.exit(f"Log-Kanal #{args.log_channel} nicht gefunden.")
    _fp, used, limit, tier = _google_limit_state(reset_flags=True)
    rest = limit - used
    long_need = len(msgs.LIMIT_LONG) * len(targets)
    print(f"Google-Key: Stufe {tier}, Verbrauch {used:,} / Limit {limit:,} -> Rest {rest:,} Zeichen "
          f"(lange Nachricht braucht ca. {long_need:,})")
    if tier != "free" or not (300 <= rest < long_need):
        print(f"  Vorbereitung passt nicht: chars_month in data/config-test/providers.toml auf {used + 800} setzen "
              f"und den Test-Bot neu starten.")
        return False

    _, last = await d.req("GET", f"/channels/{log_ch['id']}/messages", params={"limit": 1})
    log_after = last[0]["id"] if last else "0"

    async def send(label: str, text: str) -> List[str]:
        _msg, mirrors = await post_and_wait(d, src_id, targets, text)
        tags = [tag_of(g[0]) if g else "FEHLT" for g in mirrors.values()]
        print(f"  {label:<26} {short(text, 40):<40} -> {', '.join(tags)}")
        return tags

    async def full_reported() -> bool:
        _, logs = await d.req("GET", f"/channels/{log_ch['id']}/messages", params={"after": log_after, "limit": 50})
        return any("🚫" in m.get("content", "") for m in logs or [])

    checks: List[Tuple[str, bool]] = []
    shorts = iter(msgs.LIMIT_SHORT)
    checks.append(("1. kurze Nachricht nutzt Google", all(t == "[Google]" for t in await send("1. kurz", next(shorts)))))
    tags = await send("2. lang (passt nicht)", msgs.LIMIT_LONG)
    checks.append(("2. lange Nachricht weicht aus", all(t != "[Google]" for t in tags)))
    await asyncio.sleep(2)
    checks.append(("2. keine Meldung 'Limit erreicht'", not await full_reported()))
    for i in range(2):
        checks.append((f"3.{i + 1} kurze Nachricht nutzt den Rest", all(t == "[Google]" for t in await send(f"3. kurz", next(shorts)))))
    switched = False
    for text in shorts:
        if all(t != "[Google]" for t in await send("4. kurz bis Rest leer", text)):
            switched = True
            break
    await asyncio.sleep(2)
    checks.append(("4. Rest aufgebraucht -> Wechsel", switched))
    checks.append(("4. Meldung 'Limit erreicht' im Log", await full_reported()))
    tags = await send("5. danach", "Still here, anyone around?")
    checks.append(("5. Key bleibt bis Monatsende pausiert", all(t != "[Google]" for t in tags)))

    _, logs = await d.req("GET", f"/channels/{log_ch['id']}/messages", params={"after": log_after, "limit": 50})
    print(f"\n  Meldungen in #{args.log_channel}:")
    for m in sorted(logs or [], key=lambda m: int(m["id"])):
        print(f"    {short(m.get('content', ''), 150)}")
    print()
    for label, ok in checks:
        print(f"  [{'OK' if ok else 'FAIL':4}] {label}")
    ok = all(ok for _, ok in checks)
    print(f"\nErgebnis Limit-Test: {'OK' if ok else 'FEHLER'}")
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default="english", help="Name des Quellkanals (Standard: english)")
    ap.add_argument("--only", choices=["chat", "ann", "markdown"], help="nur eine Art von Nachrichten")
    ap.add_argument("--label", help="zusätzliche Kennung für die Marker, z. B. der Git-Commit")
    ap.add_argument("--limit-test", action="store_true", help="Google-Limit testen statt der Bridge-Prüfungen")
    ap.add_argument("--log-channel", default="log", help="Name des Log-Kanals für --limit-test")
    ap.add_argument("--expect-tag", help="jede Übersetzung muss dieses Tag tragen, z. B. [Libre] (Opt-out-Test)")
    ap.add_argument("--privacy", choices=["local", "standard"],
                    help="Opt-out des Tester-Bots in der Test-DB setzen und beenden (danach Test-Bot neu starten)")
    args = ap.parse_args()
    if args.privacy:
        sys.exit(asyncio.run(set_privacy(args.privacy == "local")))
    sys.exit(asyncio.run(main(args)))
