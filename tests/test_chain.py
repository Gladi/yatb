"""
Tests für translator.py (Engines gegen einen lokalen Schein-Server) und chain.py (Kette mit Engine-Attrappen).
Kein Netzwerk, keine echten Keys.
"""
import asyncio
import json
import re
import time
import unittest

from _testenv import BOT_DIR  # noqa: F401

from aiohttp import web  # noqa: E402

import chain  # noqa: E402
import database as db  # noqa: E402
import limits  # noqa: E402
import providers as pv  # noqa: E402
import stats  # noqa: E402
import translator as tr  # noqa: E402

GUILD = 424242424242424242


def run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
class FakeServer:
    """Kleiner HTTP-Server auf 127.0.0.1, dessen Antworten jeder Test vorgibt."""

    def __init__(self):
        self.responses = []   # Liste von (status, body, headers)
        self.requests = []    # empfangene JSON-Bodies

    async def handler(self, request: web.Request):
        self.requests.append(await request.json())
        status, body, headers = self.responses.pop(0) if self.responses else (200, "{}", {})
        return web.Response(status=status, text=body if isinstance(body, str) else json.dumps(body), headers=headers,
                            content_type="application/json")

    async def __aenter__(self):
        app = web.Application()
        app.router.add_route("POST", "/{tail:.*}", self.handler)
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, "127.0.0.1", 0)
        await site.start()
        self.url = f"http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}"
        return self

    async def __aexit__(self, *exc):
        await self.runner.cleanup()


def ai_provider(url: str, extra=None) -> pv.Provider:
    return pv.Provider("fakeai", "Fake AI", "openai", group="A", base_url=url + "/v1", model="m1", extra=extra or {})


def completion(content: str, finish: str = "stop", tin: int = 120, tout: int = 30) -> dict:
    return {"choices": [{"message": {"content": content}, "finish_reason": finish}],
            "usage": {"prompt_tokens": tin, "completion_tokens": tout}}


class EngineTests(unittest.TestCase):
    def test_ai_ok_and_prompt(self):
        async def go():
            import aiohttp
            async with FakeServer() as srv, aiohttp.ClientSession() as s:
                srv.responses = [(200, completion("<think>hmm</think>Hallo zusammen!"), {})]
                out, call = await tr.ai_translate(s, ai_provider(srv.url), "k", "Hello everyone!", "en", "de", ["A: hi"])
                return out, call, srv.requests[0]
        out, call, req = run(go())
        self.assertEqual(out, "Hallo zusammen!")
        self.assertEqual((call.outcome, call.tokens_in, call.tokens_out), ("ok", 120, 30))
        self.assertEqual(req["model"], "m1")
        self.assertEqual(req["temperature"], 0.1)
        self.assertRegex(req["messages"][-1]["content"], r"<text-([0-9a-f]+)>\nHello everyone!\n</text-\1>")
        self.assertIn("<context-", req["messages"][-1]["content"])
        self.assertEqual(len(req["messages"]), 2 + 2 * len(tr.AI_EXAMPLES))
        self.assertIn("FORM OF ADDRESS", req["messages"][0]["content"])

    def test_ai_cached_tokens_are_read(self):
        async def go():
            import aiohttp
            body = completion("Hallo")
            body["usage"]["prompt_tokens_details"] = {"cached_tokens": 64}
            async with FakeServer() as srv, aiohttp.ClientSession() as s:
                srv.responses = [(200, body, {})]
                return await tr.ai_translate(s, ai_provider(srv.url), "k", "Hello", "en", "de")
        out, call = run(go())
        self.assertEqual((out, call.tokens_in, call.tokens_cached), ("Hallo", 120, 64))

    def test_ai_error_classes(self):
        cases = [
            ((429, {"error": "Rate limit reached: tokens per day exceeded"}, {}), "quota", None),
            ((429, {"error": "too many requests per minute"}, {"Retry-After": "7"}), "rate_limited", 7.0),
            ((404, {"error": "The model m1 does not exist"}, {}), "model_not_found", None),
            ((401, {"error": "bad key"}, {}), "auth", None),
            ((402, {"message": "Workspace monthly spending limit reached."}, {}), "spend_limit", None),
            ((503, {"error": "overloaded"}, {}), "server_error", None),
            ((200, completion(""), {}), "empty", None),
            ((200, completion("Hallo", finish="length"), {}), "validator_rejected", None),
            ((200, "not json", {}), "bad_response", None),
        ]
        for response, outcome, retry in cases:
            async def go(response=response):
                import aiohttp
                async with FakeServer() as srv, aiohttp.ClientSession() as s:
                    srv.responses = [response]
                    return await tr.ai_translate(s, ai_provider(srv.url), "k", "Hello", "en", "de")
            with self.subTest(outcome=outcome):
                out, call = run(go())
                self.assertIsNone(out)
                self.assertEqual(call.outcome, outcome)
                self.assertEqual(call.retry_after, retry)

    def test_ai_extra_params_rejected_are_dropped_and_remembered(self):
        async def go():
            import aiohttp
            async with FakeServer() as srv, aiohttp.ClientSession() as s:
                p = ai_provider(srv.url, extra={"reasoning_effort": "none"})
                srv.responses = [(400, {"error": "unknown parameter"}, {}), (200, completion("Hallo"), {}),
                                 (200, completion("Hallo"), {})]
                first = await tr.ai_translate(s, p, "k", "Hello", "en", "de")
                second = await tr.ai_translate(s, p, "k", "Hello", "en", "de")
                return first, second, srv.requests
        tr._EXTRA_REJECTED.discard("fakeai")
        (out1, _), (out2, _), reqs = run(go())
        self.assertEqual((out1, out2), ("Hallo", "Hallo"))
        self.assertIn("reasoning_effort", reqs[0])
        self.assertNotIn("reasoning_effort", reqs[1])
        self.assertNotIn("reasoning_effort", reqs[2])   # gemerkt: nicht nochmal versucht
        tr._EXTRA_REJECTED.discard("fakeai")

    def test_google_and_azure_parsing(self):
        async def go():
            import aiohttp
            async with FakeServer() as srv, aiohttp.ClientSession() as s:
                tr.GOOGLE_URL, tr.AZURE_URL = srv.url + "/google", srv.url + "/azure"
                srv.responses = [
                    (200, {"data": {"translations": [{"translatedText": "<b>Hallo</b> &amp; tsch&#39;"}]}}, {}),
                    (200, [{"translations": [{"text": "<i>Hola</i>", "to": "es"}]}], {}),
                    (403, '{"error": {"code": 403001, "message": "quota"}}', {}),
                ]
                g = await tr.google_translate(s, "k", ["<b>Hello</b>"], "en", "de")
                a = await tr.azure_translate(s, "k", "westeurope", ["<i>Hello</i>"], "en", "es")
                q = await tr.azure_translate(s, "k", "westeurope", ["x"], "en", "es")
                return g, a, q, srv.requests
        orig = (tr.GOOGLE_URL, tr.AZURE_URL)
        try:
            (g_out, g_call), (a_out, a_call), (q_out, q_call), reqs = run(go())
        finally:
            tr.GOOGLE_URL, tr.AZURE_URL = orig
        self.assertEqual(g_out, ["<b>Hallo</b> &amp; tsch&#39;"])
        self.assertEqual((g_call.outcome, g_call.chars), ("ok", len("<b>Hello</b>")))
        self.assertEqual(reqs[0]["format"], "html")
        self.assertEqual(a_out, ["<i>Hola</i>"])
        self.assertEqual(reqs[1], [{"Text": "<i>Hello</i>"}])
        self.assertEqual((q_out, q_call.outcome), (None, "quota"))


# ---------------------------------------------------------------------------
class ChainTests(unittest.TestCase):
    """Kette mit Attrappen statt echter Engines."""

    def setUp(self):
        with db._conn() as conn:
            conn.execute("DELETE FROM api_keys WHERE guild_id = ?", (GUILD,))
            conn.execute("DELETE FROM engine_order WHERE guild_id = ?", (GUILD,))
            conn.execute("DELETE FROM key_usage")
        db._reload_guilds()
        chain._breakers.clear()
        chain._cache.clear()
        limits.reset_window()
        stats._pending.clear()
        self.orig = (tr.ai_translate, tr.google_translate, tr.azure_translate, tr.libre_translate, chain.CHAIN_BUDGET)
        self.calls = []

        async def ai(session, provider, key, text, source, target, context=None, timeout=None, hint=None):
            self.calls.append(provider.id)
            self.models.append(provider.model)
            self.hints.append(hint)
            behaviour = self.ai_behaviour.get(provider.id, "ok")
            if behaviour == "broken_once":
                behaviour = "broken" if hint is None else "ok"
            if behaviour == "ok":
                return text.replace("Hello", "Hallo"), tr.Call("ok", 200, 5, len(text), 100, 20)
            if behaviour == "broken":
                return text.replace("**", ""), tr.Call("ok", 200, 5, len(text), 100, 20)
            if behaviour == "drop_token":
                return re.sub(r"__DISCORD_TOKEN_\d+__", "", text), tr.Call("ok", 200, 5, len(text), 100, 20)
            return None, tr.Call(behaviour, 401 if behaviour == "auth" else None, 5)

        async def google(session, key, texts, source, target, fmt="html"):
            self.calls.append("google")
            return [t.replace("Hello", "Hallo") for t in texts], tr.Call("ok", 200, 5, sum(map(len, texts)))

        async def azure(session, key, region, texts, source, target, fmt="html"):
            self.calls.append(f"azure:{region}")
            return None, tr.Call("server_error", 503, 5, sum(map(len, texts)))

        async def libre(session, texts, source, target, fmt="html"):
            self.calls.append(f"libre:{fmt}")
            return [t.replace("Hello", "Hallo") for t in texts], tr.Call("ok", 200, 5, sum(map(len, texts)))

        self.ai_behaviour = {}
        self.hints = []
        self.models = []
        tr.ai_translate, tr.google_translate, tr.azure_translate, tr.libre_translate = ai, google, azure, libre

    def tearDown(self):
        tr.ai_translate, tr.google_translate, tr.azure_translate, tr.libre_translate, chain.CHAIN_BUDGET = self.orig

    def add(self, provider, secret, tier="paid", meta=None):
        status, info = run(db.add_api_key(GUILD, provider, secret, tier=tier, meta=meta))
        self.assertEqual(status, "ok")
        return info

    def translate(self, text="**Hello** Commanders <@123>", local_only=False):
        return run(chain.translate(None, GUILD, [text], "en", "de", local_only=local_only))

    def test_chain_order(self):
        self.add("mistral", "mistral-key-000000000000", "paid")
        self.add("gemini", "gemini-free-key-00000000", "free")     # Gratis-Gemini: im EWR nicht zulässig
        self.add("gemini", "gemini-paid-key-00000000", "paid")
        self.add("groq", "gsk_groq_free_key_00000000", "free")
        self.add("google_translate", "AIzaGoogleKey000000000000", "free")
        self.add("azure", "azure-key-0000000000000000", "free", meta='{"region": "westeurope"}')
        order = [(s.id, s.key.tier if s.key else None) for s in chain.build_chain(GUILD)]
        self.assertEqual(order, [("gemini", "paid"), ("groq", "free"), ("mistral", "paid"),
                                 ("google_translate", "free"), ("azure", "free"), ("libre", None)])
        self.assertEqual([s.id for s in chain.build_chain(GUILD, local_only=True)], ["libre"])

    def test_custom_engine_order(self):
        mistral = self.add("mistral", "mistral-key-000000000000", "paid")
        gemini = self.add("gemini", "gemini-paid-key-00000000", "paid")
        google = self.add("google_translate", "AIzaGoogleKey000000000000", "free")
        default = [s.id for s in chain.build_chain(GUILD)]
        self.assertEqual(default, ["gemini", "mistral", "google_translate", "libre"])
        # Google zuerst, dann Mistral; Gemini nicht genannt -> folgt dahinter, Libre bleibt letzter Rückfall
        self.assertEqual(run(db.set_engine_order(GUILD, [google.id, mistral.id, google.id], user_id=7)),
                         [google.id, mistral.id])
        self.assertEqual([s.id for s in chain.build_chain(GUILD)], ["google_translate", "mistral", "gemini", "libre"])
        self.assertEqual([s.id for s in chain.build_chain(GUILD, local_only=True)], ["libre"])  # Opt-out geht vor
        self.translate()
        self.assertEqual(self.calls[0], "google")
        # entfernter Key wird ignoriert, fremde IDs werden abgelehnt, None = zurück zum Standard
        run(db.remove_api_key(GUILD, google.id))
        self.assertEqual([s.id for s in chain.build_chain(GUILD)], ["mistral", "gemini", "libre"])
        with self.assertRaises(ValueError):
            run(db.set_engine_order(GUILD, [gemini.id, 999999]))
        self.assertIsNone(run(db.set_engine_order(GUILD, None)))
        self.assertEqual([s.id for s in chain.build_chain(GUILD)], ["gemini", "mistral", "libre"])
        self.assertEqual(db.get_engine_order(GUILD), [])

    def test_ai_ok(self):
        self.add("mistral", "mistral-key-000000000000")
        res = self.translate()
        self.assertEqual((res.texts[0], res.engines), ("**Hallo** Commanders <@123>", ["[AI]"]))
        rt = db.get_guild_keys(GUILD)[0]
        _d, month, _ms = run(limits.monthly_status(rt.fingerprint, pv.PROVIDERS["mistral"], "paid", None))
        self.assertEqual((month.requests, month.tokens_in, month.tokens_out), (1, 100, 20))
        self.assertGreater(month.cost, 0)
        rec = [r for r in stats._pending if r[3] == "mistral"][0]
        self.assertEqual(rec[11], "ok")   # outcome

    def test_rejected_answer_falls_through_to_next_ai(self):
        self.add("gemini", "gemini-paid-key-00000000")
        self.add("mistral", "mistral-key-000000000000")
        self.ai_behaviour = {"gemini": "broken"}
        res = self.translate()
        self.assertEqual(res.engines, ["[AI]"])
        self.assertEqual(self.calls, ["gemini", "gemini", "mistral"])   # 2. Versuch mit Hinweis, dann nächste KI
        gem = [r for r in stats._pending if r[3] == "gemini"]
        self.assertEqual([(g[11], g[13], g[16]) for g in gem],
                         [("validator_rejected", 0, "bold;retry"), ("validator_rejected", 1, "retry:bold")])
        self.assertIn("bold **", self.hints[1])

    def test_formatting_fallback_to_stronger_model(self):
        self.add("mistral", "mistral-key-000000000000")
        self.ai_behaviour = {"mistral": "broken_once"}
        res = self.translate()
        self.assertEqual((res.engines, self.calls), (["[AI]"], ["mistral", "mistral"]))
        mistral = pv.PROVIDERS["mistral"]
        self.assertEqual(self.models, [mistral.model, mistral.fallback_model])
        self.assertIn("**Hallo**", res.texts[0])
        rows = [r for r in stats._pending if r[3] == "mistral"]
        self.assertEqual([(r[4], r[16]) for r in rows],
                         [(mistral.model, "bold;fallback"), (mistral.fallback_model, "fallback")])
        self.assertGreater(rows[1][14], rows[0][14] * 5)    # zweiter Versuch zum (höheren) Preis des Ersatzmodells
        self.assertIn("bold **", self.hints[1])

    def test_fallback_for_any_rejection_then_next_stage(self):
        self.add("mistral", "mistral-key-000000000000")
        self.ai_behaviour = {"mistral": "drop_token"}
        res = self.translate()
        self.assertEqual(self.calls.count("mistral"), 2)      # Small, dann Medium - beide verworfen
        self.assertIsNone(self.hints[1])                    # kein Formatierungshinweis bei verlorenen Platzhaltern
        self.assertNotEqual(res.engines, ["[AI]"])

    def test_same_model_retry_without_fallback_model(self):
        self.add("groq", "gsk_groqkey0000000000000000")
        self.ai_behaviour = {"groq": "broken_once"}
        res = self.translate()
        self.assertEqual((res.engines, self.calls), (["[AI]"], ["groq", "groq"]))
        self.assertEqual(len(set(self.models)), 1)
        self.assertEqual([r[16] for r in stats._pending if r[3] == "groq"], ["bold;retry", "retry"])

    def test_no_retry_for_lost_placeholders_without_fallback_model(self):
        self.add("groq", "gsk_groqkey0000000000000000")
        self.ai_behaviour = {"groq": "drop_token"}
        res = self.translate()
        self.assertEqual(self.calls.count("groq"), 1)
        self.assertNotEqual(res.engines, ["[AI]"])

    def test_auth_error_trips_breaker_and_notifies(self):
        self.add("mistral", "mistral-key-000000000000")
        self.ai_behaviour = {"mistral": "auth"}
        res = self.translate()
        self.assertEqual(res.engines, ["[Libre]"])
        self.assertEqual([n.kind for n in res.notices], ["key_rejected"])
        self.calls.clear()
        res = self.translate("**Hello** again")   # Breaker offen: Mistral wird übersprungen
        self.assertNotIn("mistral", self.calls)

    def test_google_html_then_azure_then_libre(self):
        self.add("google_translate", "AIzaGoogleKey000000000000", "free")
        res = self.translate("Hello ||secret|| __under__ <@123>")
        self.assertEqual(res.engines, ["[Google]"])
        self.assertEqual(res.texts[0], "Hallo ||secret|| __under__ <@123>")

    def test_failing_azure_goes_to_libre(self):
        self.add("azure", "azure-key-0000000000000000", "free", meta='{"region": "westeurope"}')
        res = self.translate()
        self.assertEqual(res.engines, ["[Libre]"])
        self.assertEqual(self.calls, ["azure:westeurope", "libre:html"])

    def test_local_only(self):
        self.add("mistral", "mistral-key-000000000000")
        res = self.translate(local_only=True)
        self.assertEqual((res.engines, self.calls), (["[Libre]"], ["libre:html"]))

    def test_exhausted_budget_skips_key_and_reports_once(self):
        info = self.add("mistral", "mistral-key-000000000000", "paid")
        run(db.set_api_key_budget(GUILD, info.id, 0.0))
        res = self.translate()
        self.assertEqual(res.engines, ["[Libre]"])
        self.assertNotIn("mistral", self.calls)
        self.assertEqual([(n.kind, n.crossed) for n in res.notices], [("usage", ["warn_90", "warn_95", "warn_100"])])
        self.assertEqual(self.translate("**Hello** twice").notices, [])
        self.assertTrue(any(r[3] == "mistral" and r[11] == "limit" for r in stats._pending))

    def test_time_budget_skips_paid_engines(self):
        self.add("mistral", "mistral-key-000000000000")
        chain.CHAIN_BUDGET = 0
        res = self.translate()
        self.assertEqual((res.engines, self.calls), (["[Libre]"], ["libre:html"]))

    def test_raw_when_everything_fails(self):
        async def broken(session, texts, source, target, fmt="html"):
            return None, tr.Call("network", None, 1)
        tr.libre_translate = broken
        res = self.translate()
        self.assertEqual((res.texts[0], res.engines), ("**Hello** Commanders <@123>", ["[Raw]"]))

    def test_nothing_to_translate_and_same_language(self):
        res = run(chain.translate(None, GUILD, ["<@123> 👍", "", "Hello"], "en", "de"))
        self.assertEqual(res.engines, ["[Direct]", "[Direct]", "[Libre]"])
        res = run(chain.translate(None, GUILD, ["Hello"], "en", "en"))
        self.assertEqual((res.engines, self.calls), (["[Direct]"], ["libre:html"]))

    def test_cache_per_guild_not_for_ai(self):
        self.translate("Hello there")                 # Libre -> Cache
        self.calls.clear()
        self.assertEqual(self.translate("Hello there").engines, ["[Libre]"])
        self.assertEqual(self.calls, [])               # aus dem Cache
        other = run(chain.translate(None, GUILD + 1, ["Hello there"], "en", "de"))
        self.assertEqual(self.calls, ["libre:html"])   # anderer Server: eigener Cache
        self.add("mistral", "mistral-key-000000000000")
        self.calls.clear()
        self.translate("Hello AI")
        self.translate("Hello AI")
        self.assertEqual(self.calls.count("mistral"), 2)  # KI-Ergebnisse werden nicht gecacht


if __name__ == "__main__":
    unittest.main()
