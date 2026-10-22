"""
Ende-zu-Ende-Test für Foren-Bridges auf dem Test-Server (läuft im Container discord-bot-test).

    docker exec discord-bot-test python -u tests/e2e_forum.py --source <Forum-ID EN> --target <Forum-ID DE>

Voraussetzung: beide Foren sind in derselben Bridge (Test-DB) und das Quell-Forum hat mindestens zwei Tags.
Der Tester-Bot (YATB_TEST_DRIVER_TOKEN) erstellt einen Beitrag mit Tag, antwortet, benennt um, wechselt den Tag und
schließt den Beitrag; geprüft wird jeweils der Spiegel-Beitrag im Ziel-Forum (Titel übersetzt, Tag zugeordnet bzw.
von YATB angelegt, Antwort gespiegelt, Änderungen übernommen). Beiträge bleiben zur Ansicht im Forum.
"""
import argparse
import asyncio
import os
import sys
import time

import aiohttp

API = "https://discord.com/api/v10"
WAIT = 60


class Discord:
    def __init__(self, session: aiohttp.ClientSession, token: str):
        self.s, self.h = session, {"Authorization": f"Bot {token}"}

    async def req(self, method: str, path: str, **kw):
        for _ in range(5):
            async with self.s.request(method, API + path, headers=self.h, **kw) as r:
                if r.status == 429:
                    await asyncio.sleep(float((await r.json()).get("retry_after", 1)) + 0.2)
                    continue
                return r.status, (await r.json() if r.content_type == "application/json" else None)
        return 429, None


async def wait_for(check, timeout: float = WAIT):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        got = await check()
        if got:
            return got
        await asyncio.sleep(2)
    return None


async def main(args) -> int:
    fails = 0

    def line(ok: bool, step: str, detail: str):
        nonlocal fails
        fails += not ok
        print(f"  [{'OK  ' if ok else 'FAIL'}] {step:<22} {detail}")

    async with aiohttp.ClientSession() as s:
        drv = Discord(s, os.environ["YATB_TEST_DRIVER_TOKEN"])
        bot = Discord(s, os.environ["DISCORD_TOKEN"])
        _, src = await bot.req("GET", f"/channels/{args.source}")
        _, guild = await bot.req("GET", f"/channels/{args.target}")
        gid = guild["guild_id"]
        tags = src.get("available_tags", [])
        if len(tags) < 2:
            print("Quell-Forum braucht mindestens zwei Tags.")
            return 2
        stamp = time.strftime("%H:%M:%S")
        st, post = await drv.req("POST", f"/channels/{args.source}/threads", json={
            "name": f"Armada tonight at 20 ST ({stamp})",
            "message": {"content": "Who is joining the **armada** tonight? Bring *repair kits* please!"},
            "applied_tags": [tags[0]["id"]],
        })
        if st not in (200, 201):
            print("Beitrag konnte nicht erstellt werden:", st, post)
            return 2
        print(f"Beitrag im Quell-Forum: {post['name']} (Tag {tags[0]['name']})")

        async def mirror():
            _, active = await bot.req("GET", f"/guilds/{gid}/threads/active")
            for t in (active or {}).get("threads", []):
                if t["parent_id"] == str(args.target) and stamp in t["name"]:
                    return t
            return None

        m = await wait_for(mirror)
        line(m is not None, "Beitrag gespiegelt", m["name"] if m else "kein Spiegel-Beitrag")
        if m is None:
            return 1
        _, target = await bot.req("GET", f"/channels/{args.target}")
        names = {t["id"]: t["name"] for t in target.get("available_tags", [])}
        mt = [names.get(t, t) for t in m.get("applied_tags", [])]
        line(bool(mt), "Tag zugeordnet", f"{tags[0]['name']} -> {mt}")
        line("Armada" in m["name"] and m["name"] != post["name"], "Titel übersetzt", m["name"])
        _, msgs = await bot.req("GET", f"/channels/{m['id']}/messages?limit=5")
        starter = msgs[-1]["content"] if msgs else ""
        line("**" in starter and starter != "Who is joining the **armada** tonight? Bring *repair kits* please!",
             "Starter übersetzt", starter[:80])

        await drv.req("POST", f"/channels/{post['id']}/messages", json={"content": "I am in, see you at the gate!"})

        async def reply():
            _, ms = await bot.req("GET", f"/channels/{m['id']}/messages?limit=5")
            return next((x for x in ms or [] if x["id"] != msgs[-1]["id"] and x.get("webhook_id")), None)
        r = await wait_for(reply)
        line(r is not None, "Antwort gespiegelt", r["content"][:80] if r else "keine Antwort im Spiegel")

        await drv.req("PATCH", f"/channels/{post['id']}", json={"name": f"Armada moved to 21 ST ({stamp})",
                                                                "applied_tags": [tags[1]["id"]]})

        async def renamed():
            _, t = await bot.req("GET", f"/channels/{m['id']}")
            return t if t and "21" in t["name"] and t.get("applied_tags") != m.get("applied_tags") else None
        t = await wait_for(renamed)
        if t:
            _, target = await bot.req("GET", f"/channels/{args.target}")
            names = {x["id"]: x["name"] for x in target.get("available_tags", [])}
        line(t is not None, "Titel+Tag geändert",
             f"{t['name']} / {[names.get(x, x) for x in t['applied_tags']]}" if t else "Spiegel nicht aktualisiert")

        await drv.req("PATCH", f"/channels/{post['id']}", json={"archived": True})

        async def archived():
            _, t = await bot.req("GET", f"/channels/{m['id']}")
            return t if t and t.get("thread_metadata", {}).get("archived") else None
        line(await wait_for(archived) is not None, "geschlossen", "Spiegel-Beitrag geschlossen")

        print(f"\nErgebnis: {fails} Fehler. Tags im Ziel-Forum: {sorted(names.values())}")
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--target", required=True)
    sys.exit(asyncio.run(main(ap.parse_args())))
