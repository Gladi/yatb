"""
Tests für internal_api.py (interne API für das Dashboard) mit Schein-Bot und Schein-Servern, ohne Netzwerk.
"""
import asyncio
import json
import unittest

from _testenv import BOT_DIR  # noqa: F401

import discord  # noqa: E402
from aiohttp.test_utils import TestClient, TestServer  # noqa: E402

import chain  # noqa: E402
import database as db  # noqa: E402
import internal_api  # noqa: E402
import locales  # noqa: E402
import stats  # noqa: E402

GUILD = 515151515151515151
ADMIN, MEMBER = 1001, 1002
TOKEN = "t" * 40
SECRETS = ["mistral-secret-key-0000000001", "gemini-secret-key-0000000002", "AIzaGoogleSecret00000000003"]


class FakeMember:
    def __init__(self, admin: bool):
        self.guild_permissions = discord.Permissions(administrator=admin)


class FakeChannel:
    def __init__(self, name):
        self.name = name


class FakeGuild:
    def __init__(self):
        self.id, self.name, self.icon, self.owner_id, self.preferred_locale = GUILD, "Testserver", None, 999, "en-US"

    def get_member(self, user_id):
        return {ADMIN: FakeMember(True), MEMBER: FakeMember(False)}.get(user_id)

    async def fetch_member(self, user_id):
        return None

    def get_channel(self, channel_id):
        return FakeChannel(f"chan-{channel_id}")


class FakeBot:
    def __init__(self):
        self.guilds = [FakeGuild()]

    def get_guild(self, guild_id):
        return next((g for g in self.guilds if g.id == guild_id), None)


class InternalApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        with db._conn() as conn:
            for table in ("api_keys", "engine_order", "bridge_channels"):
                conn.execute(f"DELETE FROM {table} WHERE guild_id = ?", (GUILD,))
        db._reload_guilds()
        db._reload_channels()
        internal_api._admin_cache.clear()
        chain._breakers.clear()
        self.reports = []

        async def report(guild, message):
            self.reports.append(message)

        hooks = internal_api.Hooks(FakeBot(), report, lambda info: f"#{info.id} {info.provider}")
        self.client = TestClient(TestServer(internal_api.create_app(hooks, TOKEN)))
        await self.client.start_server()
        self.mistral = (await db.add_api_key(GUILD, "mistral", SECRETS[0], "paid", "Haupt"))[1]
        self.gemini = (await db.add_api_key(GUILD, "gemini", SECRETS[1], "paid"))[1]
        self.google = (await db.add_api_key(GUILD, "google_translate", SECRETS[2], "free"))[1]
        await db.add_bridge_channel(11, GUILD, "chat", "en")
        await db.add_bridge_channel(12, GUILD, "chat", "de")

    async def asyncTearDown(self):
        await self.client.close()

    async def call(self, method, path, body=None, token=TOKEN):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = await self.client.request(method, path, json=body, headers=headers)
        return resp.status, json.loads(await resp.text())

    async def test_token_required(self):
        self.assertEqual((await self.call("GET", "/v1/guilds", token=None))[0], 401)
        self.assertEqual((await self.call("GET", "/v1/guilds", token="x" * 40))[0], 401)
        status, data = await self.call("GET", "/v1/guilds")
        self.assertEqual((status, data), (200, [{"id": str(GUILD), "name": "Testserver", "icon": None}]))
        self.assertEqual((await self.call("GET", f"/v1/guilds?actor_id={ADMIN}"))[1][0]["id"], str(GUILD))
        self.assertEqual(await self.call("GET", f"/v1/guilds?actor_id={MEMBER}"), (200, []))

    async def test_overview_only_for_admins_and_never_contains_keys(self):
        self.assertEqual((await self.call("GET", f"/v1/guilds/{GUILD}?actor_id={MEMBER}"))[0], 403)
        self.assertEqual((await self.call("GET", f"/v1/guilds/{GUILD}?actor_id=4711"))[0], 403)   # kein Mitglied
        self.assertEqual((await self.call("GET", f"/v1/guilds/42?actor_id={ADMIN}"))[0], 404)
        resp = await self.client.get(f"/v1/guilds/{GUILD}?actor_id={ADMIN}", headers={"Authorization": f"Bearer {TOKEN}"})
        text = await resp.text()
        for secret in SECRETS:
            self.assertNotIn(secret, text)
        data = json.loads(text)
        self.assertEqual([s["provider"] for s in data["chain"]], ["gemini", "mistral", "google_translate", "libre"])
        self.assertEqual(data["bridges"], [{"bridge": "chat", "channels": [
            {"id": "11", "name": "chan-11", "language": "en"}, {"id": "12", "name": "chan-12", "language": "de"}]}])
        mistral = next(k for k in data["keys"] if k["id"] == self.mistral.id)
        self.assertEqual((mistral["label"], mistral["last4"], mistral["in_chain"]), ("Haupt", SECRETS[0][-4:], True))
        self.assertFalse(next(k for k in data["keys"] if k["provider"] == "gemini")["free_allowed"])

    async def test_edit_key_same_rules_as_form(self):
        path = f"/v1/guilds/{GUILD}/keys/{self.mistral.id}"
        status, data = await self.call("PATCH", path, {"actor_id": ADMIN, "label": "Neu", "tier": "paid", "budget": 7.5,
                                                       "currency": "EUR", "limit_enabled": True})
        self.assertEqual(status, 200)
        self.assertEqual((data["label"], data["budget"], data["currency"]), ("Neu", 7.5, "EUR"))
        self.assertEqual(len(self.reports), 1)
        self.assertIn(f"<@{ADMIN}> (Dashboard)", self.reports[0])
        bad = [({"tier": "gratis"}, "invalid_tier"), ({"budget": 5000}, "invalid_budget"), ({"budget": True}, "invalid_budget"),
               ({"currency": "GBP"}, "invalid_currency"), ({"label": "x" * 40}, "invalid_label")]
        for extra, code in bad:
            self.assertEqual(await self.call("PATCH", path, {"actor_id": ADMIN, **extra}), (400, {"error": code}))
        gemini = f"/v1/guilds/{GUILD}/keys/{self.gemini.id}"
        self.assertEqual(await self.call("PATCH", gemini, {"actor_id": ADMIN, "tier": "free"}), (400, {"error": "invalid_tier"}))
        self.assertEqual((await self.call("PATCH", path, {"actor_id": MEMBER, "label": "x"}))[0], 403)
        # nicht gesendete Felder bleiben, null leert
        status, data = await self.call("PATCH", path, {"actor_id": ADMIN, "tier": "paid"})
        self.assertEqual((data["label"], data["budget"], data["currency"]), ("Neu", 7.5, "EUR"))
        status, data = await self.call("PATCH", path, {"actor_id": ADMIN, "label": None, "budget": None})
        self.assertEqual((status, data["label"], data["budget"]), (200, None, None))
        self.assertEqual(await self.call("PATCH", path, {"actor_id": ADMIN, "label": 5}), (400, {"error": "invalid_label"}))

    async def test_limit_off_needs_confirmation(self):
        path = f"/v1/guilds/{GUILD}/keys/{self.mistral.id}"
        body = {"actor_id": ADMIN, "limit_enabled": False}
        self.assertEqual(await self.call("PATCH", path, body), (409, {"error": "confirm_limit_off"}))
        self.assertTrue(db.get_guild_keys(GUILD)[0].limit_enabled)
        status, data = await self.call("PATCH", path, {**body, "confirm_limit_off": True})
        self.assertEqual((status, data["limit_enabled"]), (200, False))
        self.assertEqual(len(self.reports), 2)   # geändert + Limit aus

    async def test_delete_key(self):
        path = f"/v1/guilds/{GUILD}/keys/{self.google.id}"
        self.assertEqual((await self.call("DELETE", path, {"actor_id": MEMBER}))[0], 403)
        self.assertEqual(await self.call("DELETE", path, {"actor_id": ADMIN}), (200, {"removed": self.google.id}))
        self.assertEqual(await self.call("DELETE", path, {"actor_id": ADMIN}), (404, {"error": "key_not_found"}))
        self.assertNotIn("google_translate", [s.id for s in chain.build_chain(GUILD)])
        self.assertIn("removed an API key", self.reports[0])

    async def test_engine_order(self):
        path = f"/v1/guilds/{GUILD}/order"
        status, data = await self.call("PUT", path, {"actor_id": ADMIN, "key_ids": [self.google.id, self.mistral.id]})
        self.assertEqual(status, 200)
        self.assertTrue(data["custom_order"])
        self.assertEqual([s["provider"] for s in data["chain"]], ["google_translate", "mistral", "gemini", "libre"])
        self.assertIn("Google Translate → Mistral \"Haupt\" → Google Gemini → LibreTranslate", self.reports[0])
        for bad in ([999999], ["1"], [True], "1,2"):
            self.assertEqual(await self.call("PUT", path, {"actor_id": ADMIN, "key_ids": bad}), (400, {"error": "invalid_order"}))
        self.assertEqual((await self.call("PUT", path, {"actor_id": MEMBER, "key_ids": None}))[0], 403)
        status, data = await self.call("PUT", path, {"actor_id": ADMIN, "key_ids": None})
        self.assertEqual((status, data["custom_order"]), (200, False))
        self.assertEqual([s["provider"] for s in data["chain"]], ["gemini", "mistral", "google_translate", "libre"])

    async def test_stats_report(self):
        stats.init()
        with stats._conn() as conn:
            conn.execute("DELETE FROM calls WHERE guild_id = ?", (GUILD,))
        import time as _t
        now = _t.time()
        for i, (outcome, ms) in enumerate([("ok", 100), ("ok", 300), ("validator_rejected", 200), ("timeout", 9000),
                                           ("limit", 0)]):
            stats.record(guild_id=GUILD, provider="mistral", model="m", outcome=outcome, duration_ms=ms, chars=10,
                         tokens_in=5, tokens_out=5, cost=0.01, fell_through=outcome != "ok", ts=now - i)
        stats.record(guild_id=GUILD, provider="libre", model="libre", outcome="ok", duration_ms=50, ts=now)
        stats.record(guild_id=GUILD + 1, provider="mistral", model="m", outcome="ok", ts=now)   # anderer Server
        self.assertEqual((await self.call("GET", f"/v1/guilds/{GUILD}/stats?days=30&actor_id={MEMBER}"))[0], 403)
        self.assertEqual(await self.call("GET", f"/v1/guilds/{GUILD}/stats?days=12&actor_id={ADMIN}"), (400, {"error": "invalid_days"}))
        status, data = await self.call("GET", f"/v1/guilds/{GUILD}/stats?days=7&actor_id={ADMIN}")
        self.assertEqual((status, len(data["days"])), (200, 7))
        mistral = next(p for p in data["providers"] if p["provider"] == "mistral")
        self.assertEqual((mistral["calls"], mistral["ok"], mistral["limit_skips"], mistral["fell_through"]), (4, 2, 1, 2))
        self.assertEqual((mistral["ok_rate"], mistral["structure_rate"]), (0.5, round(2 / 3, 4)))
        self.assertEqual((mistral["p50_ms"], mistral["p95_ms"]), (100, 300))
        self.assertEqual((mistral["provider_name"], mistral["group"], mistral["per_day"][-1]), ("Mistral", "B", 4))
        self.assertEqual(next(p for p in data["providers"] if p["provider"] == "libre")["provider_name"], "LibreTranslate")

    async def test_privacy(self):
        path = f"/v1/users/{MEMBER}/privacy"
        self.assertEqual(await self.call("PUT", path, {"local_only": "ja"}), (400, {"error": "invalid_local_only"}))
        self.assertEqual(await self.call("PUT", path, {"local_only": True}), (200, {"local_only": True}))
        self.assertEqual(await self.call("GET", path), (200, {"local_only": True}))
        self.assertTrue(db.is_local_only(MEMBER))
        self.assertEqual(await self.call("PUT", path, {"local_only": False}), (200, {"local_only": False}))

    async def test_report_texts_exist_in_all_languages(self):
        for lang in ("en", "de", "fr", "es", "it", "ru", "nl"):
            for key in ("rep_order_set", "rep_order_reset", "rep_key_edited", "rep_key_removed", "rep_key_limit"):
                self.assertIn("{user}", locales.MESSAGES["en"][key])
                self.assertNotEqual(locales.get_text(lang, key, user="u", order="o", desc="d", state="s"), key)


if __name__ == "__main__":
    unittest.main()
