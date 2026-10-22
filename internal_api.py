"""
YATB - interne API für das Dashboard (Container yatb-web).

* Läuft im Bot-Prozess auf Port 8081, nur im Docker-Netz erreichbar (Port wird nicht veröffentlicht).
* Jede Anfrage braucht das gemeinsame Geheimnis (Docker-Secret yatb_internal_token) als Bearer-Token.
  Fehlt die Datei, startet die API nicht (z. B. Test-Bot).
* Der Bot bleibt der einzige, der die Haupt-DB schreibt; API-Keys verlassen den Bot nie (nur Anzeigedaten wie
  Bezeichnung und die letzten 4 Zeichen).
* Schreibende Anfragen nennen den handelnden Discord-Nutzer (actor_id). Der Bot prüft selbst, ob dieser auf dem
  Server Administrator ist, wendet dieselben Regeln wie die Discord-Formulare an und meldet jede Änderung im
  Log-Kanal des Servers.
"""
import asyncio
import hmac
import logging
import os
import re
import time
from typing import Any, Awaitable, Callable, Dict, List, NamedTuple, Optional, Tuple

import discord
from aiohttp import web

import chain
import database as db
import limits
import locales
import providers
import stats

log = logging.getLogger("yatb.api")

TOKEN_FILE = os.getenv("YATB_INTERNAL_TOKEN_FILE", "/run/secrets/yatb_internal_token")
PORT = int(os.getenv("YATB_INTERNAL_PORT", "8081"))
CURRENCIES = ("USD", "EUR")
LABEL_MAX = 32
BUDGET_MAX = 1000.0
ADMIN_CACHE_SECONDS = 60.0
_REGION_RE = re.compile(r"^[a-z0-9]{2,32}$")


class Hooks(NamedTuple):
    """Was die API vom Bot braucht (verhindert einen Import-Kreis mit bot.py)."""
    bot: Any                                                    # discord.Client
    report: Callable[[discord.Guild, str], Awaitable[None]]     # Meldung im Log-Kanal
    key_desc: Callable[[db.ApiKeyInfo], str]                    # "`#3` Mistral "Haupt""


HOOKS = web.AppKey("hooks", Hooks)
TOKEN = web.AppKey("token", str)


class ApiError(Exception):
    def __init__(self, status: int, code: str):
        super().__init__(code)
        self.status, self.code = status, code


def load_token() -> Optional[str]:
    try:
        with open(TOKEN_FILE, encoding="utf-8") as fh:
            token = fh.read().strip()
    except OSError:
        return None
    return token if len(token) >= 32 else None


# ----------------- Prüfungen -----------------
_admin_cache: Dict[Tuple[int, int], Tuple[float, bool]] = {}


async def is_admin(guild: discord.Guild, user_id: int) -> bool:
    """Echter Discord-Administrator (Recht "Administrator" oder Eigentümer), kurz zwischengespeichert."""
    key, now = (guild.id, user_id), time.monotonic()
    hit = _admin_cache.get(key)
    if hit and now - hit[0] < ADMIN_CACHE_SECONDS:
        return hit[1]
    member = guild.get_member(user_id)
    if member is None:
        try:
            member = await guild.fetch_member(user_id)
        except (discord.NotFound, discord.Forbidden):
            member = None
    result = member is not None and (member.guild_permissions.administrator or guild.owner_id == user_id)
    _admin_cache[key] = (now, result)
    return result


def _int(value: Any, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ApiError(400, f"invalid_{field}") from None


async def _admin_guild(request: web.Request, actor_id: int) -> discord.Guild:
    hooks: Hooks = request.app[HOOKS]
    guild = hooks.bot.get_guild(_int(request.match_info["guild_id"], "guild"))
    if guild is None:
        raise ApiError(404, "guild_not_found")
    if not await is_admin(guild, actor_id):
        raise ApiError(403, "not_admin")
    return guild


def _parse_settings(body: dict, info: db.ApiKeyInfo, provider: providers.Provider) -> dict:
    """
    Gleiche Regeln wie das Discord-Formular (KeyForm). Nicht gesendete Felder behalten ihren Wert; label/budget = null
    leert das Feld (budget null = Standard aus der Config). Wirft ApiError(400, ...) bei ungültigen Werten.
    """
    label = body["label"] if "label" in body else info.label
    if label is not None and not isinstance(label, str):
        raise ApiError(400, "invalid_label")
    label = (label or "").strip() or None
    if label is not None and len(label) > LABEL_MAX:
        raise ApiError(400, "invalid_label")
    tier = body.get("tier", info.tier)
    if tier not in ("free", "paid") or (tier == "free" and not providers.free_allowed(provider)):
        raise ApiError(400, "invalid_tier")
    budget = body["budget"] if "budget" in body else info.budget
    if budget is not None:
        if isinstance(budget, bool) or not isinstance(budget, (int, float)) or not 0 <= budget <= BUDGET_MAX:
            raise ApiError(400, "invalid_budget")
        budget = round(float(budget), 2)
    currency = body.get("currency") or info.currency or provider.currency
    if currency not in CURRENCIES:
        raise ApiError(400, "invalid_currency")
    region = None
    if provider.needs_region:
        region = (body.get("region") or info.region or "").strip().lower()
        if not _REGION_RE.match(region):
            raise ApiError(400, "invalid_region")
    limit_enabled = body.get("limit_enabled", info.limit_enabled)
    if not isinstance(limit_enabled, bool):
        raise ApiError(400, "invalid_limit")
    return {"label": label, "tier": tier, "budget": budget, "currency": currency if currency != provider.currency else None,
            "limit_enabled": limit_enabled, "region": region}


# ----------------- Antwortdaten -----------------
def _usage(row: db.UsageRow) -> dict:
    return {"requests": row.requests, "chars": row.chars, "tokens_in": row.tokens_in, "tokens_out": row.tokens_out,
            "cost": round(row.cost, 4)}


async def _key_data(info: db.ApiKeyInfo, active_ids: set) -> dict:
    provider = providers.PROVIDERS.get(info.provider)
    data = {
        "id": info.id, "provider": info.provider, "provider_name": provider.name if provider else info.provider,
        "kind": provider.kind if provider else None, "label": info.label, "tier": info.tier,
        "limit_enabled": info.limit_enabled, "budget": info.budget,
        "budget_default": provider.limits_paid.budget_month if provider else None,
        "currency": info.currency or (provider.currency if provider else "USD"),
        "region": info.region, "needs_region": bool(provider and provider.needs_region),
        "free_allowed": bool(provider and providers.free_allowed(provider)),
        "last4": info.last4, "shared": info.shared, "created_at": info.created_at, "in_chain": info.id in active_ids,
        "usage": None,
    }
    if provider is not None and info.fingerprint:
        u_day, u_month, ms = await limits.monthly_status(info.fingerprint, provider, info.tier, info.budget)
        data["usage"] = {"day": _usage(u_day), "month": _usage(u_month),
                         "limit": {"kind": ms.kind, "used": ms.used, "limit": ms.limit} if ms else None}
    return data


async def _stage_data(spec: chain.Spec) -> dict:
    if spec.key is None:
        return {"kind": "libre", "provider": "libre", "provider_name": "LibreTranslate", "key_id": None, "state": "active"}
    state = "active" if chain.breaker(spec).allow() else "paused"
    _d, _m, ms = await limits.monthly_status(spec.key.fingerprint, spec.provider, spec.key.tier, spec.key.budget)
    if ms is not None and spec.key.limit_enabled and (ms.limit - ms.used) <= ms.limit * limits.EXHAUSTED_REMAINING:
        state = "exhausted"
    return {"kind": spec.kind, "provider": spec.provider.id, "provider_name": spec.provider.name, "key_id": spec.key.key_id,
            "label": spec.key.label, "tier": spec.key.tier, "state": state}


def _guild_summary(guild: discord.Guild) -> dict:
    return {"id": str(guild.id), "name": guild.name, "icon": guild.icon.url if guild.icon else None}


# ----------------- Endpunkte -----------------
routes = web.RouteTableDef()


@routes.get("/v1/guilds")
async def list_guilds(request: web.Request):
    """Server mit YATB; mit ?actor_id= nur die, auf denen dieser Nutzer Administrator ist (Serverauswahl)."""
    guilds = list(request.app[HOOKS].bot.guilds)
    if "actor_id" in request.query:
        actor = _int(request.query["actor_id"], "actor")
        guilds = [g for g in guilds if await is_admin(g, actor)]
    return web.json_response([_guild_summary(g) for g in sorted(guilds, key=lambda g: g.name.lower())])


@routes.get("/v1/guilds/{guild_id}")
async def guild_overview(request: web.Request):
    guild = await _admin_guild(request, _int(request.query.get("actor_id"), "actor"))
    stages = chain.build_chain(guild.id)
    bridges: Dict[str, List[dict]] = {}
    for channel_id, bridge_id, language in db.list_guild_bridges(guild.id):
        ch = guild.get_channel(channel_id)
        bridges.setdefault(bridge_id, []).append({"id": str(channel_id), "name": ch.name if ch else None,
                                                  "language": language})
    _key, report_id, _conf = db.get_guild_config(guild.id)
    report_ch = guild.get_channel(report_id) if report_id else None
    active = {s.key.key_id for s in stages if s.key is not None}
    return web.json_response({
        **_guild_summary(guild),
        "bridges": [{"bridge": b, "channels": chs} for b, chs in sorted(bridges.items())],
        "log_channel": {"id": str(report_id), "name": report_ch.name if report_ch else None} if report_id else None,
        "chain": [await _stage_data(s) for s in stages],
        "custom_order": bool(db.get_engine_order(guild.id)),
        "keys": [await _key_data(i, active) for i in await db.list_api_keys(guild.id)],
        "currencies": list(CURRENCIES),
    })


@routes.get("/v1/guilds/{guild_id}/stats")
async def guild_stats(request: web.Request):
    """Kennzahlen pro Dienst für 7/30/90 Tage (stats.guild_report) plus Anzeigenamen und Qualitätsgruppe."""
    guild = await _admin_guild(request, _int(request.query.get("actor_id"), "actor"))
    days = _int(request.query.get("days", "30"), "days")
    if days not in (7, 30, 90):
        raise ApiError(400, "invalid_days")
    await stats.flush()   # gerade erst gemessene Aufrufe mitzählen
    report = await asyncio.to_thread(stats.guild_report, guild.id, days)
    for row in report["providers"]:
        prov = providers.PROVIDERS.get(row["provider"])
        row["provider_name"] = prov.name if prov else {"libre": "LibreTranslate"}.get(row["provider"], row["provider"])
        row["group"] = prov.group if prov else None
    return web.json_response(report)


@routes.patch("/v1/guilds/{guild_id}/keys/{key_id}")
async def edit_key(request: web.Request):
    body = await _json(request)
    actor = _int(body.get("actor_id"), "actor")
    guild = await _admin_guild(request, actor)
    key_id = _int(request.match_info["key_id"], "key")
    info = next((i for i in await db.list_api_keys(guild.id) if i.id == key_id), None)
    provider = providers.PROVIDERS.get(info.provider) if info else None
    if info is None or provider is None:
        raise ApiError(404, "key_not_found")
    values = _parse_settings(body, info, provider)
    turn_off = info.limit_enabled and not values["limit_enabled"]
    if turn_off and body.get("confirm_limit_off") is not True:   # Kosten liegen beim Admin -> ausdrücklich bestätigen
        raise ApiError(409, "confirm_limit_off")
    updated = await db.update_api_key(guild.id, key_id, **values)
    if updated is None:
        raise ApiError(404, "key_not_found")
    hooks: Hooks = request.app[HOOKS]
    loc, user = guild.preferred_locale, _actor(actor)
    await hooks.report(guild, locales.get_text(loc, "rep_key_edited", user=user, desc=hooks.key_desc(updated)))
    if turn_off:
        await hooks.report(guild, locales.get_text(loc, "rep_key_limit", user=user, desc=hooks.key_desc(updated),
                                                   state=locales.get_text(loc, "keys_off")))
    log.info("Dashboard: Key %s auf Guild %s geändert.", key_id, guild.id)
    return web.json_response(await _key_data(updated, {s.key.key_id for s in chain.build_chain(guild.id) if s.key}))


@routes.delete("/v1/guilds/{guild_id}/keys/{key_id}")
async def delete_key(request: web.Request):
    body = await _json(request)
    actor = _int(body.get("actor_id"), "actor")
    guild = await _admin_guild(request, actor)
    removed = await db.remove_api_key(guild.id, _int(request.match_info["key_id"], "key"))
    if removed is None:
        raise ApiError(404, "key_not_found")
    hooks: Hooks = request.app[HOOKS]
    await hooks.report(guild, locales.get_text(guild.preferred_locale, "rep_key_removed", user=_actor(actor),
                                               desc=hooks.key_desc(removed)))
    log.info("Dashboard: Key %s auf Guild %s entfernt.", removed.id, guild.id)
    return web.json_response({"removed": removed.id})


@routes.put("/v1/guilds/{guild_id}/order")
async def set_order(request: web.Request):
    """{"actor_id": ..., "key_ids": [3, 1, 2]} oder "key_ids": null = Standardreihenfolge."""
    body = await _json(request)
    actor = _int(body.get("actor_id"), "actor")
    guild = await _admin_guild(request, actor)
    raw = body.get("key_ids")
    if raw is not None and (not isinstance(raw, list) or not all(isinstance(i, int) and not isinstance(i, bool) for i in raw)):
        raise ApiError(400, "invalid_order")
    try:
        saved = await db.set_engine_order(guild.id, raw, user_id=actor)
    except ValueError:
        raise ApiError(400, "invalid_order") from None
    stages = chain.build_chain(guild.id)
    loc = guild.preferred_locale
    order = " → ".join(f"{s.provider.name}" + (f' "{s.key.label}"' if s.key.label else "") if s.key else "LibreTranslate"
                       for s in stages)
    key = "rep_order_set" if saved else "rep_order_reset"
    await request.app[HOOKS].report(guild, locales.get_text(loc, key, user=_actor(actor), order=order))
    log.info("Dashboard: Reihenfolge auf Guild %s %s.", guild.id, "gesetzt" if saved else "zurückgesetzt")
    return web.json_response({"custom_order": bool(saved), "chain": [await _stage_data(s) for s in stages]})


@routes.get("/v1/users/{user_id}/privacy")
async def get_privacy(request: web.Request):
    return web.json_response({"local_only": db.is_local_only(_int(request.match_info["user_id"], "user"))})


@routes.put("/v1/users/{user_id}/privacy")
async def put_privacy(request: web.Request):
    """Die eigene Wahl des angemeldeten Nutzers (das Dashboard prüft die Anmeldung)."""
    body = await _json(request)
    if not isinstance(body.get("local_only"), bool):
        raise ApiError(400, "invalid_local_only")
    user_id = _int(request.match_info["user_id"], "user")
    await db.set_local_only(user_id, body["local_only"])
    return web.json_response({"local_only": db.is_local_only(user_id)})


def _actor(user_id: int) -> str:
    return f"<@{user_id}> (Dashboard)"


async def _json(request: web.Request) -> dict:
    try:
        body = await request.json()
    except ValueError:
        raise ApiError(400, "invalid_json") from None
    if not isinstance(body, dict):
        raise ApiError(400, "invalid_json")
    return body


# ----------------- Server -----------------
@web.middleware
async def _guard(request: web.Request, handler):
    expected = request.app[TOKEN]
    given = request.headers.get("Authorization", "")
    if not hmac.compare_digest(given.encode(), f"Bearer {expected}".encode()):
        return web.json_response({"error": "unauthorized"}, status=401)
    try:
        return await handler(request)
    except ApiError as exc:
        return web.json_response({"error": exc.code}, status=exc.status)
    except web.HTTPException:
        raise
    except Exception:  # noqa: BLE001 - nie Details (oder Eingaben) nach außen geben
        log.exception("Interne API: Fehler bei %s %s", request.method, request.path)
        return web.json_response({"error": "internal"}, status=500)


def create_app(hooks: Hooks, token: str) -> web.Application:
    app = web.Application(middlewares=[_guard], client_max_size=64 * 1024)
    app[HOOKS], app[TOKEN] = hooks, token
    app.add_routes(routes)
    return app


async def start(hooks: Hooks) -> Optional[web.AppRunner]:
    token = load_token()
    if token is None:
        log.info("Interne API aus (kein Token unter %s).", TOKEN_FILE)
        return None
    runner = web.AppRunner(create_app(hooks, token), access_log=None)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    log.info("Interne API für das Dashboard auf Port %s.", PORT)
    return runner
