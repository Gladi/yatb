"""
Tests für das Dashboard (dashboard/) gegen einen Schein-Discord und eine Schein-Bot-API - ohne Netzwerk.
"""
import os
import re
import tempfile
import unittest
from urllib.parse import parse_qs, urlparse

from _testenv import BOT_DIR  # noqa: F401

from aiohttp import web  # noqa: E402
from aiohttp.test_utils import TestClient, TestServer  # noqa: E402

from dashboard import app as dash  # noqa: E402
from dashboard import render  # noqa: E402

USER_ID, OTHER_ID = 100000000000000001, 4711
EVIL = '<img src=x onerror=alert(1)>'
TAG_RE = re.compile(r"</?([a-z0-9]+)")


class FakeUpstream:
    """Discord (OAuth) und die interne Bot-API in einem Schein-Server."""

    def __init__(self):
        self.calls, self.local_only, self.down = [], {}, False
        self.app = web.Application()
        r = self.app.router
        r.add_post("/discord/oauth2/token", self.token)
        r.add_get("/discord/users/@me", self.me)
        r.add_post("/discord/oauth2/token/revoke", self.revoke)
        r.add_get("/bot/v1/guilds", self.guilds)
        r.add_get("/bot/v1/guilds/{gid}", self.overview)
        r.add_get("/bot/v1/users/{uid}/privacy", self.get_privacy)
        r.add_put("/bot/v1/users/{uid}/privacy", self.put_privacy)
        r.add_put("/bot/v1/guilds/{gid}/order", self.put_order)
        r.add_patch("/bot/v1/guilds/{gid}/keys/{kid}", self.patch_key)
        r.add_delete("/bot/v1/guilds/{gid}/keys/{kid}", self.delete_key)
        r.add_get("/bot/v1/guilds/{gid}/stats", self.stats)
        self.patch_answer = (200, {})

    async def token(self, request):
        form = await request.post()
        self.calls.append(("token", request.headers.get("Authorization", "")[:6], form.get("code"), form.get("redirect_uri")))
        ok = form.get("code") == "good"
        return web.json_response({"access_token": "acc-123"} if ok else {"error": "invalid_grant"}, status=200 if ok else 400)

    async def me(self, request):
        self.calls.append(("me", request.headers.get("Authorization")))
        return web.json_response({"id": str(USER_ID), "username": "tester", "global_name": f"Tester {EVIL}"})

    async def revoke(self, request):
        self.calls.append(("revoke", (await request.post()).get("token")))
        return web.json_response({})

    def _auth(self, request):
        if self.down:
            raise web.HTTPServiceUnavailable()
        assert request.headers.get("Authorization") == "Bearer " + "k" * 40

    async def guilds(self, request):
        self._auth(request)
        actor = int(request.query.get("actor_id", 0))
        return web.json_response([{"id": "42", "name": EVIL, "icon": None}] if actor == USER_ID else [])

    async def overview(self, request):
        self._auth(request)
        if int(request.query["actor_id"]) != USER_ID:
            return web.json_response({"error": "not_admin"}, status=403)
        return web.json_response({
            "id": "42", "name": EVIL, "icon": None, "custom_order": False,
            "bridges": [{"bridge": "chat", "channels": [{"id": "1", "name": "english", "language": "en"}]}],
            "log_channel": None,
            "chain": [{"kind": "ai", "provider": "mistral", "provider_name": "Mistral", "key_id": 4, "label": EVIL,
                       "tier": "paid", "state": "active"},
                      {"kind": "google", "provider": "google_translate", "provider_name": "Google Translate", "key_id": 5,
                       "label": None, "tier": "free", "state": "paused"},
                      {"kind": "libre", "provider": "libre", "provider_name": "LibreTranslate", "key_id": None, "state": "active"}],
            "keys": [{"id": 4, "provider": "mistral", "provider_name": "Mistral", "kind": "openai", "label": EVIL,
                      "tier": "paid", "limit_enabled": True, "budget": None, "budget_default": 8.5, "currency": "EUR",
                      "region": None, "needs_region": False, "free_allowed": True, "last4": "v2JX", "shared": False,
                      "created_at": "2026-10-20", "in_chain": True,
                      "usage": {"day": {"requests": 3, "chars": 10, "tokens_in": 1, "tokens_out": 1, "cost": 0.01},
                                "month": {"requests": 9, "chars": 99, "tokens_in": 1, "tokens_out": 1, "cost": 0.5},
                                "limit": {"kind": "cost", "used": 0.5, "limit": 8.5}}}],
            "currencies": ["USD", "EUR"],
        })

    async def put_order(self, request):
        self._auth(request)
        self.calls.append(("order", await request.json()))
        return web.json_response({"custom_order": True, "chain": []})

    async def patch_key(self, request):
        self._auth(request)
        self.calls.append(("patch", request.match_info["kid"], await request.json()))
        return web.json_response(self.patch_answer[1], status=self.patch_answer[0])

    async def delete_key(self, request):
        self._auth(request)
        self.calls.append(("delete", request.match_info["kid"], await request.json()))
        return web.json_response({"removed": int(request.match_info["kid"])})

    async def stats(self, request):
        self._auth(request)
        self.calls.append(("stats", request.query.get("days")))
        return web.json_response({"days": ["2026-10-19", "2026-10-20"], "providers": [
            {"provider": "mistral", "provider_name": EVIL, "group": "B", "calls": 12, "ok": 11, "fell_through": 1,
             "limit_skips": 2, "outcomes": {"ok": 11, "timeout": 1}, "chars": 0, "tokens_in": 900, "tokens_out": 800,
             "cost": 0.12, "p50_ms": 840, "p95_ms": 2300, "ok_rate": 0.9167, "structure_rate": 1.0, "per_day": [5, 7]}]})

    async def get_privacy(self, request):
        self._auth(request)
        return web.json_response({"local_only": self.local_only.get(request.match_info["uid"], False)})

    async def put_privacy(self, request):
        self._auth(request)
        body = await request.json()
        self.local_only[request.match_info["uid"]] = body["local_only"]
        return web.json_response({"local_only": body["local_only"]})


class DashboardTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.up = FakeUpstream()
        self.up_server = TestServer(self.up.app)
        await self.up_server.start_server()
        base = str(self.up_server.make_url("")).rstrip("/")
        self.tmp = tempfile.mkdtemp(prefix="yatb_web_")
        cfg = dash.Config(base_url="https://yatb.example", prefix="/app", bot_api=base + "/bot", token="k" * 40,
                          client_id="1549763645481689139", client_secret="s" * 32,
                          db_path=os.path.join(self.tmp, "sessions.db"), discord_api=base + "/discord")
        self.client = TestClient(TestServer(dash.create_app(cfg)))
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()
        await self.up_server.close()

    async def get(self, path, cookie=None, **kw):
        headers = {"Cookie": cookie} if cookie else {}
        return await self.client.get(path, headers={**headers, **kw.pop("headers", {})}, allow_redirects=False, **kw)

    async def post(self, path, data, cookie, origin="https://yatb.example"):
        headers = {"Cookie": cookie, **({"Origin": origin} if origin else {})}
        return await self.client.post(path, data=data, headers=headers, allow_redirects=False)

    async def login(self):
        resp = await self.get("/app/login")
        state = parse_qs(urlparse(resp.headers["Location"]).query)["state"][0]
        resp = await self.get(f"/app/callback?code=good&state={state}", cookie=f"{dash.STATE_COOKIE}={state}")
        token = resp.cookies[dash.COOKIE].value
        return resp, f"{dash.COOKIE}={token}"

    async def csrf(self, cookie):
        html = await (await self.get("/app/", cookie=cookie)).text()
        return re.search(r'name="csrf" value="([^"]+)"', html).group(1)

    async def test_login_page_for_anonymous(self):
        resp = await self.get("/app/", headers={"Accept-Language": "de-DE,de"})
        text = await resp.text()
        self.assertEqual(resp.status, 200)
        self.assertIn("Mit Discord anmelden", text)
        self.assertEqual((resp.headers["Cache-Control"], resp.headers["X-Robots-Tag"]), ("no-store", "noindex"))
        self.assertEqual(re.findall(r"<script[^>]*>", text), [re.search(r'<script src="/static/app.js[^"]*" defer>', text).group(0)])

    async def test_login_flow_identify_only_and_token_revoked(self):
        resp = await self.get("/app/login")
        loc = urlparse(resp.headers["Location"])
        q = parse_qs(loc.query)
        self.assertEqual((resp.status, loc.netloc, q["scope"], q["redirect_uri"]),
                         (303, "discord.com", ["identify"], ["https://yatb.example/app/callback"]))
        state_cookie = resp.cookies[dash.STATE_COOKIE]
        self.assertTrue(state_cookie["httponly"] and state_cookie["secure"])
        resp, cookie = await self.login()
        self.assertEqual((resp.status, resp.headers["Location"]), (303, "/app/"))
        session = resp.cookies[dash.COOKIE]
        self.assertTrue(session["httponly"] and session["secure"])
        self.assertEqual((session["samesite"], session["max-age"], session["path"]), ("Lax", "604800", "/app"))
        self.assertIn(("revoke", "acc-123"), self.up.calls)                  # Discord-Token sofort widerrufen
        self.assertEqual(self.up.calls[0][1:], ("Basic ", "good", "https://yatb.example/app/callback"))
        with open(os.path.join(self.tmp, "sessions.db"), "rb") as fh:
            raw = fh.read()
        self.assertNotIn(cookie.split("=", 1)[1].encode(), raw)               # nur der Hash liegt in der DB
        self.assertNotIn(b"acc-123", raw)

    async def test_bad_state_or_code_fails(self):
        resp = await self.get("/app/callback?code=good&state=a", cookie=f"{dash.STATE_COOKIE}=b")
        self.assertEqual(resp.headers["Location"], "/app/?login=failed")
        self.assertNotIn(dash.COOKIE, resp.cookies)
        resp = await self.get("/app/login")
        state = parse_qs(urlparse(resp.headers["Location"]).query)["state"][0]
        resp = await self.get(f"/app/callback?code=bad&state={state}", cookie=f"{dash.STATE_COOKIE}={state}")
        self.assertEqual(resp.headers["Location"], "/app/?login=failed")
        self.assertIn("fehlgeschlagen", await (await self.get("/app/?login=failed", headers={"Accept-Language": "de"})).text())

    async def test_home_escapes_discord_names(self):
        _resp, cookie = await self.login()
        text = await (await self.get("/app/", cookie=cookie)).text()
        self.assertIn("Tester &lt;img src=x onerror=alert(1)&gt;", text)
        self.assertNotIn(EVIL, text)
        self.assertIn('href="/app/g/42"', text)

    async def test_privacy_needs_csrf_and_origin(self):
        _resp, cookie = await self.login()
        token = await self.csrf(cookie)
        self.assertEqual((await self.post("/app/privacy", {"choice": "local"}, cookie)).status, 400)
        self.assertEqual((await self.post("/app/privacy", {"choice": "local", "csrf": token}, cookie,
                                          origin="https://evil.example")).status, 400)
        self.assertEqual(self.up.local_only, {})
        resp = await self.post("/app/privacy", {"choice": "local", "csrf": token}, cookie)
        self.assertEqual((resp.status, resp.headers["Location"]), (303, "/app/?saved=1"))
        self.assertEqual(self.up.local_only, {str(USER_ID): True})
        self.assertEqual((await self.post("/app/privacy", {"choice": "x", "csrf": token}, cookie)).status, 400)

    async def test_guild_page(self):
        _resp, cookie = await self.login()
        resp = await self.get("/app/g/42?lang=de", cookie=cookie)
        text = await resp.text()
        self.assertEqual(resp.status, 200)
        self.assertNotIn(EVIL, text)
        self.assertIn("…v2JX", text)
        self.assertIn('<progress class="usage ok" value="6" max="100">', text)
        self.assertIn("0,50\u00a0€ von 8,50\u00a0€", text)                     # deutsches Format (Accept-Language)
        self.assertIn("6 % genutzt · 8,00\u00a0€ übrig", text)
        self.assertEqual((await self.get("/app/g/abc", cookie=cookie)).status, 404)
        self.assertEqual((await self.get("/app/g/42")).headers["Location"], "/app/")   # ohne Anmeldung

    async def test_logout(self):
        _resp, cookie = await self.login()
        token = await self.csrf(cookie)
        resp = await self.post("/app/logout", {"csrf": token}, cookie)
        self.assertEqual(resp.status, 303)
        self.assertIn("Log in with Discord", await (await self.get("/app/", cookie=cookie)).text())

    async def test_bot_down(self):
        _resp, cookie = await self.login()
        self.up.down = True
        resp = await self.get("/app/", cookie=cookie, headers={"Accept-Language": "en"})
        self.assertEqual(resp.status, 503)
        self.assertIn("not reachable", await resp.text())

    async def test_order_buttons(self):
        _resp, cookie = await self.login()
        token = await self.csrf(cookie)
        text = await (await self.get("/app/g/42", cookie=cookie)).text()
        self.assertEqual(text.count('name="move" value="up"'), 2)
        self.assertEqual(await self._status_post("/app/g/42/order", {"move": "down", "key_id": "4"}, cookie), 400)  # ohne CSRF
        resp = await self.post("/app/g/42/order", {"move": "down", "key_id": "4", "csrf": token}, cookie)
        self.assertEqual((resp.status, resp.headers["Location"]), (303, "/app/g/42"))
        self.assertEqual(self.up.calls[-1], ("order", {"actor_id": USER_ID, "key_ids": [5, 4]}))
        await self.post("/app/g/42/order", {"move": "reset", "csrf": token}, cookie)
        self.assertEqual(self.up.calls[-1], ("order", {"actor_id": USER_ID, "key_ids": None}))
        calls = len(self.up.calls)
        await self.post("/app/g/42/order", {"move": "up", "key_id": "4", "csrf": token}, cookie)   # schon ganz oben
        self.assertEqual(len(self.up.calls), calls)

    async def _status_post(self, path, data, cookie):
        return (await self.post(path, data, cookie)).status

    async def test_edit_key(self):
        _resp, cookie = await self.login()
        token = await self.csrf(cookie)
        resp = await self.get("/app/g/42/k/4?lang=de", cookie=cookie)
        text = await resp.text()
        self.assertEqual(resp.status, 200)
        self.assertNotIn(EVIL, text)
        self.assertIn('name="budget"', text)
        self.assertNotIn("v2JX" + "0", text)
        self.assertEqual((await self.get("/app/g/42/k/99", cookie=cookie)).status, 404)
        form = {"csrf": token, "label": "Haupt", "tier": "paid", "budget": "8,5", "currency": "EUR", "limit": "on"}
        resp = await self.post("/app/g/42/k/4", form, cookie)
        self.assertEqual((resp.status, resp.headers["Location"]), (303, "/app/g/42?done=saved"))
        self.assertEqual(self.up.calls[-1], ("patch", "4", {"actor_id": USER_ID, "label": "Haupt", "tier": "paid",
                                                            "currency": "EUR", "limit_enabled": True,
                                                            "confirm_limit_off": False, "budget": 8.5}))
        calls = len(self.up.calls)
        resp = await self.post("/app/g/42/k/4", {**form, "budget": "acht"}, cookie)
        self.assertEqual(resp.status, 400)
        self.assertEqual(len(self.up.calls), calls)                       # gar nicht erst an den Bot
        self.up.patch_answer = (409, {"error": "confirm_limit_off"})
        resp = await self.post("/app/g/42/k/4?lang=de", {**form, "limit": "off"}, cookie)
        text = await resp.text()
        self.assertEqual(resp.status, 400)
        self.assertIn("Häkchen", text)
        self.assertIn('value="off" checked', text)                         # Eingaben bleiben erhalten
        self.assertIn("Saved. The change was reported", await (await self.get("/app/g/42?done=saved&lang=en", cookie=cookie)).text())

    async def test_delete_key_needs_word(self):
        _resp, cookie = await self.login()
        token = await self.csrf(cookie)
        resp = await self.post("/app/g/42/k/4/delete?lang=de", {"csrf": token, "confirm": "ja"}, cookie)
        self.assertEqual(resp.status, 400)
        self.assertIn("löschen", await resp.text())
        self.assertNotIn("delete", [c[0] for c in self.up.calls])
        resp = await self.post("/app/g/42/k/4/delete?lang=de", {"csrf": token, "confirm": " Löschen "}, cookie)
        self.assertEqual((resp.status, resp.headers["Location"]), (303, "/app/g/42?done=deleted"))
        self.assertEqual(self.up.calls[-1], ("delete", "4", {"actor_id": USER_ID}))
        resp = await self.post("/app/g/42/k/4/delete", {"csrf": token, "confirm": "delete"}, cookie)  # Englisch geht immer
        self.assertEqual(resp.status, 303)

    async def test_stats_page(self):
        _resp, cookie = await self.login()
        resp = await self.get("/app/g/42/stats?days=7&lang=de", cookie=cookie)
        text = await resp.text()
        self.assertEqual(resp.status, 200)
        self.assertEqual(self.up.calls[-1], ("stats", "7"))
        self.assertNotIn(EVIL, text)
        self.assertIn("<svg", text)
        self.assertIn("92 %", text)                                         # 0.9167 -> ganze Prozent
        self.assertIn("1.700 Tokens", text)
        self.assertIn("840 ms", text)
        self.assertIn("2,3 s", text)
        self.assertNotIn("style=", text)
        await self.get("/app/g/42/stats?days=13", cookie=cookie)
        self.assertEqual(self.up.calls[-1], ("stats", "30"))                # ungültig -> 30 Tage

    def test_number_formats(self):
        self.assertEqual(render.fmt_money("en", 1234.5, "USD"), "$1,234.50")
        self.assertEqual(render.fmt_money("de", 1234.5, "EUR"), "1.234,50\u00a0€")
        self.assertEqual(render.fmt_money("de", 0.004, "EUR"), "< 0,01\u00a0€")
        self.assertEqual(render.fmt_num("fr", 500000), "500\u202f000")

    async def test_texts_complete_in_all_languages(self):
        en = render.EN
        for lang in render.LANGS[1:]:
            texts = render.TEXTS[lang]
            with self.subTest(lang=lang):
                self.assertEqual(sorted(set(en) ^ set(texts)), [])
                for key, text in texts.items():
                    self.assertEqual(TAG_RE.findall(text), TAG_RE.findall(en[key]), key)


if __name__ == "__main__":
    unittest.main()
