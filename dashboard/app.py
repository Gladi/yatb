"""
YATB-Dashboard unter yatb.gladi.de/app - eigener Container "yatb-web" (gleiches Image wie der Bot).

* Kein Zugriff auf die Haupt-DB, den Master-Schlüssel oder API-Keys: Alles läuft über die interne API des Bots
  (internal_api.py), die selbst prüft, ob jemand Administrator ist.
* Anmeldung mit Discord OAuth2, nur Berechtigung "identify". Der Discord-Token wird sofort nach dem Abruf von
  ID und Namen widerrufen und nie gespeichert.
* Sitzung: ein Cookie (HttpOnly, Secure, SameSite=Lax, 7 Tage), serverseitig nur als Hash gespeichert.
  Jedes Formular trägt ein CSRF-Token; zusätzlich muss der Origin-Header passen.
* Kein JavaScript; Seiten werden auf dem Server erzeugt (render.py).

Start: python -u -m dashboard.app   (Einstellungen siehe load_config)
"""
import hmac
import logging
import os
import secrets
from typing import NamedTuple, Optional, Tuple
from urllib.parse import urlencode, urlparse

import aiohttp
from aiohttp import web

from dashboard import render
from dashboard.sessions import SESSION_DAYS, Session, SessionStore

log = logging.getLogger("yatb.web")

COOKIE = "yatb_session"
STATE_COOKIE = "yatb_oauth_state"
AUTHORIZE_URL = "https://discord.com/oauth2/authorize"


class Config(NamedTuple):
    base_url: str          # https://yatb.gladi.de (für Redirect-URI und Origin-Prüfung)
    prefix: str            # /app
    bot_api: str           # http://discord-bot:8081
    token: str             # gemeinsames Geheimnis mit dem Bot
    client_id: str         # Discord-Anwendung (öffentlich)
    client_secret: str
    db_path: str
    discord_api: str       # https://discord.com/api/v10 (in Tests: Schein-Server)


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read().strip()


def load_config() -> Config:
    return Config(
        base_url=os.getenv("YATB_BASE_URL", "https://yatb.gladi.de").rstrip("/"),
        prefix=os.getenv("YATB_APP_PREFIX", "/app").rstrip("/"),
        bot_api=os.getenv("YATB_BOT_API", "http://discord-bot:8081").rstrip("/"),
        token=_read(os.getenv("YATB_INTERNAL_TOKEN_FILE", "/run/secrets/yatb_internal_token")),
        client_id=os.environ["YATB_CLIENT_ID"],
        client_secret=_read(os.getenv("YATB_CLIENT_SECRET_FILE", "/run/secrets/yatb_discord_client_secret")),
        db_path=os.getenv("YATB_WEB_DB", "/app/web-data/sessions.db"),
        discord_api=os.getenv("YATB_DISCORD_API", "https://discord.com/api/v10").rstrip("/"),
    )


CONFIG = web.AppKey("config", Config)
STORE = web.AppKey("store", SessionStore)
HTTP = web.AppKey("http", aiohttp.ClientSession)


class BotUnavailable(Exception):
    pass


async def bot_call(app: web.Application, method: str, path: str, body: Optional[dict] = None) -> Tuple[int, dict]:
    cfg = app[CONFIG]
    try:
        async with app[HTTP].request(method, cfg.bot_api + path, json=body, timeout=aiohttp.ClientTimeout(total=15),
                                     headers={"Authorization": f"Bearer {cfg.token}"}) as resp:
            return resp.status, await resp.json(content_type=None)
    except (aiohttp.ClientError, TimeoutError, ValueError) as exc:
        log.warning("Bot-API %s %s nicht erreichbar: %s", method, path, type(exc).__name__)
        raise BotUnavailable() from exc


# ----------------- Hilfen -----------------
def _session(request: web.Request) -> Tuple[Optional[str], Optional[Session]]:
    token = request.cookies.get(COOKIE)
    return token, request.app[STORE].get(token)


def _lang(request: web.Request, token: Optional[str], session: Optional[Session]) -> str:
    wanted = request.query.get("lang")
    if wanted in render.LANGS:
        if session is not None:
            request.app[STORE].set_lang(token, wanted)
        return wanted
    if session is not None and session.lang in render.LANGS:
        return session.lang
    return render.pick_lang(request.headers.get("Accept-Language", ""))


def _page(text: str, status: int = 200) -> web.Response:
    return web.Response(text=text, status=status, content_type="text/html", charset="utf-8")


def _redirect(location: str) -> web.Response:
    return web.Response(status=303, headers={"Location": location})


async def _check_form(request: web.Request, session: Optional[Session]) -> Optional[dict]:
    """POST-Formular mit gültigem CSRF-Token und passender Herkunft, sonst None."""
    if session is None:
        return None
    origin = request.headers.get("Origin")
    if origin and origin.rstrip("/") != request.app[CONFIG].base_url:
        return None
    form = await request.post()
    if not hmac.compare_digest(str(form.get("csrf", "")), session.csrf):
        return None
    return dict(form)


# ----------------- Seiten -----------------
async def healthz(request: web.Request):
    return web.Response(text="ok")


async def index(request: web.Request):
    cfg, (token, session) = request.app[CONFIG], _session(request)
    lang = _lang(request, token, session)
    if session is None:
        return _page(render.login_page(lang, cfg.prefix, failed=request.query.get("login") == "failed"))
    try:
        _st, guilds = await bot_call(request.app, "GET", f"/v1/guilds?actor_id={session.user_id}")
        _st, privacy = await bot_call(request.app, "GET", f"/v1/users/{session.user_id}/privacy")
    except BotUnavailable:
        return _page(render.error_page(lang, "error_bot", cfg.prefix, session.name, session.csrf), 503)
    return _page(render.home_page(lang, session.name, session.csrf, bool(privacy.get("local_only")),
                                  guilds if isinstance(guilds, list) else [], cfg.prefix, request.query.get("saved") == "1"))


async def login(request: web.Request):
    cfg = request.app[CONFIG]
    state = secrets.token_urlsafe(24)
    query = urlencode({"response_type": "code", "client_id": cfg.client_id, "scope": "identify", "state": state,
                       "redirect_uri": f"{cfg.base_url}{cfg.prefix}/callback", "prompt": "none"})
    resp = _redirect(f"{AUTHORIZE_URL}?{query}")
    resp.set_cookie(STATE_COOKIE, state, max_age=600, path=cfg.prefix, secure=True, httponly=True, samesite="Lax")
    return resp


async def callback(request: web.Request):
    cfg = request.app[CONFIG]
    failed = _redirect(f"{cfg.prefix}/?login=failed")
    failed.del_cookie(STATE_COOKIE, path=cfg.prefix)
    state, expected, code = request.query.get("state", ""), request.cookies.get(STATE_COOKIE, ""), request.query.get("code")
    if not code or not expected or not hmac.compare_digest(state, expected):
        return failed
    auth = aiohttp.BasicAuth(cfg.client_id, cfg.client_secret)
    http = request.app[HTTP]
    try:
        async with http.post(f"{cfg.discord_api}/oauth2/token", auth=auth, data={
            "grant_type": "authorization_code", "code": code, "redirect_uri": f"{cfg.base_url}{cfg.prefix}/callback",
        }, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            access = (await resp.json(content_type=None)).get("access_token") if resp.status == 200 else None
        if not access:
            log.warning("OAuth: Code-Tausch fehlgeschlagen.")
            return failed
        async with http.get(f"{cfg.discord_api}/users/@me", headers={"Authorization": f"Bearer {access}"},
                            timeout=aiohttp.ClientTimeout(total=15)) as resp:
            me = await resp.json(content_type=None) if resp.status == 200 else {}
        # Token sofort widerrufen - wir brauchen ihn nicht mehr und speichern ihn nie
        async with http.post(f"{cfg.discord_api}/oauth2/token/revoke", auth=auth,
                             data={"token": access, "token_type_hint": "access_token"},
                             timeout=aiohttp.ClientTimeout(total=15)):
            pass
    except (aiohttp.ClientError, TimeoutError, ValueError) as exc:
        log.warning("OAuth: Discord nicht erreichbar (%s).", type(exc).__name__)
        return failed
    if not str(me.get("id", "")).isdigit():
        return failed
    name = me.get("global_name") or me.get("username") or "?"
    token = request.app[STORE].create(int(me["id"]), name, render.pick_lang(request.headers.get("Accept-Language", "")))
    resp = _redirect(f"{cfg.prefix}/")
    resp.set_cookie(COOKIE, token, max_age=SESSION_DAYS * 86400, path=cfg.prefix, secure=True, httponly=True,
                    samesite="Lax")
    resp.del_cookie(STATE_COOKIE, path=cfg.prefix)
    log.info("Dashboard: Anmeldung von %s.", me["id"])
    return resp


async def logout(request: web.Request):
    cfg, (token, session) = request.app[CONFIG], _session(request)
    if await _check_form(request, session) is not None:
        request.app[STORE].delete(token)
    resp = _redirect(f"{cfg.prefix}/")
    resp.del_cookie(COOKIE, path=cfg.prefix)
    return resp


async def privacy(request: web.Request):
    cfg, (token, session) = request.app[CONFIG], _session(request)
    lang = _lang(request, token, session)
    form = await _check_form(request, session)
    if form is None or form.get("choice") not in ("standard", "local"):
        return _page(render.error_page(lang, "error_csrf", cfg.prefix), 400)
    try:
        status, _data = await bot_call(request.app, "PUT", f"/v1/users/{session.user_id}/privacy",
                                       {"local_only": form["choice"] == "local"})
    except BotUnavailable:
        status = 503
    if status != 200:
        return _page(render.error_page(lang, "error_bot", cfg.prefix, session.name, session.csrf), 503)
    return _redirect(f"{cfg.prefix}/?saved=1")


async def _load_guild(request: web.Request):
    """(lang, session, gid, overview, guilds) oder eine fertige Fehler-/Weiterleitungs-Antwort."""
    cfg, (token, session) = request.app[CONFIG], _session(request)
    lang = _lang(request, token, session)
    if session is None:
        return _redirect(f"{cfg.prefix}/")
    gid = request.match_info["guild_id"]
    if not gid.isdigit():
        return _page(render.error_page(lang, "error_not_found", cfg.prefix, session.name, session.csrf), 404)
    try:
        status, data = await bot_call(request.app, "GET", f"/v1/guilds/{gid}?actor_id={session.user_id}")
        _st, guilds = await bot_call(request.app, "GET", f"/v1/guilds?actor_id={session.user_id}")
    except BotUnavailable:
        return _page(render.error_page(lang, "error_bot", cfg.prefix, session.name, session.csrf), 503)
    if status != 200:
        key, code = {403: ("error_forbidden", 403), 404: ("error_not_found", 404)}.get(status, ("error_bot", 503))
        return _page(render.error_page(lang, key, cfg.prefix, session.name, session.csrf), code)
    return lang, session, gid, data, guilds if isinstance(guilds, list) else []


async def guild(request: web.Request):
    loaded = await _load_guild(request)
    if isinstance(loaded, web.Response):
        return loaded
    lang, session, _gid, data, guilds = loaded
    notice = {"saved": "saved_notice", "deleted": "deleted_notice"}.get(request.query.get("done", ""))
    return _page(render.guild_page(lang, session.name, session.csrf, data, guilds, request.app[CONFIG].prefix, notice))


async def order(request: web.Request):
    """↑/↓ verschiebt einen Key in der aktuell gültigen Reihenfolge; "reset" = Standard."""
    loaded = await _load_guild(request)
    if isinstance(loaded, web.Response):
        return loaded
    lang, session, gid, data, _guilds = loaded
    cfg = request.app[CONFIG]
    form = await _check_form(request, session)
    if form is None:
        return _page(render.error_page(lang, "error_csrf", cfg.prefix, session.name, session.csrf), 400)
    ids = [s["key_id"] for s in data["chain"] if s.get("key_id") is not None]
    move = form.get("move")
    if move == "reset":
        new_ids = None
    else:
        try:
            i = ids.index(int(form.get("key_id", "")))
        except ValueError:
            return _page(render.error_page(lang, "err_invalid_order", cfg.prefix, session.name, session.csrf), 400)
        j = i - 1 if move == "up" else i + 1 if move == "down" else -1
        if not 0 <= j < len(ids):
            return _redirect(f"{cfg.prefix}/g/{gid}")
        ids[i], ids[j] = ids[j], ids[i]
        new_ids = ids
    try:
        status, _data = await bot_call(request.app, "PUT", f"/v1/guilds/{gid}/order",
                                       {"actor_id": session.user_id, "key_ids": new_ids})
    except BotUnavailable:
        status = 503
    if status != 200:
        key = {403: "error_forbidden", 400: "err_invalid_order"}.get(status, "error_bot")
        return _page(render.error_page(lang, key, cfg.prefix, session.name, session.csrf), status if status < 500 else 503)
    return _redirect(f"{cfg.prefix}/g/{gid}")


def _find_key(data: dict, request: web.Request) -> Optional[dict]:
    kid = request.match_info["key_id"]
    return next((k for k in data["keys"] if str(k["id"]) == kid), None) if kid.isdigit() else None


async def edit_key(request: web.Request):
    loaded = await _load_guild(request)
    if isinstance(loaded, web.Response):
        return loaded
    lang, session, _gid, data, _guilds = loaded
    cfg = request.app[CONFIG]
    key = _find_key(data, request)
    if key is None:
        return _page(render.error_page(lang, "err_key_not_found", cfg.prefix, session.name, session.csrf), 404)
    if request.method == "GET":
        return _page(render.edit_page(lang, session.name, session.csrf, data, key, cfg.prefix))
    form = await _check_form(request, session)
    if form is None:
        return _page(render.error_page(lang, "error_csrf", cfg.prefix, session.name, session.csrf), 400)
    values = {k: str(form.get(k, "")).strip() for k in ("label", "tier", "budget", "currency", "region", "limit")}
    body = {"actor_id": session.user_id, "label": values["label"] or None, "tier": values["tier"],
            "currency": values["currency"], "limit_enabled": values["limit"] != "off",
            "confirm_limit_off": form.get("confirm_limit_off") == "1"}
    if key.get("needs_region"):
        body["region"] = values["region"]
    error = None
    if values["budget"]:
        try:
            body["budget"] = float(values["budget"].replace(",", "."))
        except ValueError:
            error = "invalid_budget"
    else:
        body["budget"] = None
    if error is None:
        try:
            status, result = await bot_call(request.app, "PATCH", f"/v1/guilds/{data['id']}/keys/{key['id']}", body)
        except BotUnavailable:
            return _page(render.error_page(lang, "error_bot", cfg.prefix, session.name, session.csrf), 503)
        if status == 200:
            return _redirect(f"{cfg.prefix}/g/{data['id']}?done=saved")
        if status == 403:
            return _page(render.error_page(lang, "error_forbidden", cfg.prefix, session.name, session.csrf), 403)
        error = result.get("error") if isinstance(result, dict) else None
        if f"err_{error}" not in render.EN:
            return _page(render.error_page(lang, "error_bot", cfg.prefix, session.name, session.csrf), 503)
    return _page(render.edit_page(lang, session.name, session.csrf, data, key, cfg.prefix, error=error, values=values), 400)


async def delete_key(request: web.Request):
    loaded = await _load_guild(request)
    if isinstance(loaded, web.Response):
        return loaded
    lang, session, gid, data, _guilds = loaded
    cfg = request.app[CONFIG]
    key = _find_key(data, request)
    if key is None:
        return _page(render.error_page(lang, "err_key_not_found", cfg.prefix, session.name, session.csrf), 404)
    form = await _check_form(request, session)
    if form is None:
        return _page(render.error_page(lang, "error_csrf", cfg.prefix, session.name, session.csrf), 400)
    typed = str(form.get("confirm", "")).strip().casefold()
    if typed not in {render.t(lang, "delete_word").casefold(), render.EN["delete_word"].casefold()}:
        return _page(render.edit_page(lang, session.name, session.csrf, data, key, cfg.prefix, delete_error=True), 400)
    try:
        status, _result = await bot_call(request.app, "DELETE", f"/v1/guilds/{gid}/keys/{key['id']}",
                                         {"actor_id": session.user_id})
    except BotUnavailable:
        status = 503
    if status != 200:
        key_txt = {403: "error_forbidden", 404: "err_key_not_found"}.get(status, "error_bot")
        return _page(render.error_page(lang, key_txt, cfg.prefix, session.name, session.csrf), status if status < 500 else 503)
    return _redirect(f"{cfg.prefix}/g/{gid}?done=deleted")


async def guild_stats(request: web.Request):
    loaded = await _load_guild(request)
    if isinstance(loaded, web.Response):
        return loaded
    lang, session, gid, data, guilds = loaded
    cfg = request.app[CONFIG]
    days = request.query.get("days", "30")
    days = int(days) if days in ("7", "30", "90") else 30
    try:
        status, report = await bot_call(request.app, "GET", f"/v1/guilds/{gid}/stats?days={days}&actor_id={session.user_id}")
    except BotUnavailable:
        status = 503
    if status != 200:
        return _page(render.error_page(lang, "error_bot", cfg.prefix, session.name, session.csrf), 503)
    currency = {k["provider"]: k["currency"] for k in data["keys"]}
    return _page(render.stats_page(lang, session.name, session.csrf, data, guilds, report, days, currency, cfg.prefix))


@web.middleware
async def _headers(request: web.Request, handler):
    resp = await handler(request)
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex"
    return resp


def create_app(cfg: Config) -> web.Application:
    app = web.Application(middlewares=[_headers], client_max_size=32 * 1024)
    app[CONFIG], app[STORE] = cfg, SessionStore(cfg.db_path)
    p = cfg.prefix
    app.router.add_get(f"{p}/healthz", healthz)
    async def to_index(request: web.Request):
        return _redirect(f"{p}/")

    app.router.add_get(p, to_index)
    app.router.add_get(f"{p}/", index)
    app.router.add_get(f"{p}/login", login)
    app.router.add_get(f"{p}/callback", callback)
    app.router.add_post(f"{p}/logout", logout)
    app.router.add_post(f"{p}/privacy", privacy)
    app.router.add_get(f"{p}/g/{{guild_id}}", guild)
    app.router.add_post(f"{p}/g/{{guild_id}}/order", order)
    app.router.add_get(f"{p}/g/{{guild_id}}/k/{{key_id}}", edit_key)
    app.router.add_post(f"{p}/g/{{guild_id}}/k/{{key_id}}", edit_key)
    app.router.add_post(f"{p}/g/{{guild_id}}/k/{{key_id}}/delete", delete_key)
    app.router.add_get(f"{p}/g/{{guild_id}}/stats", guild_stats)
    if os.getenv("YATB_SERVE_STATIC") == "1" and render.STATIC_DIR:   # nur lokale Tests ohne Caddy
        app.router.add_static("/static", render.STATIC_DIR)

    async def http_session(app_):
        app_[HTTP] = aiohttp.ClientSession()
        yield
        await app_[HTTP].close()

    app.cleanup_ctx.append(http_session)
    return app


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = load_config()
    if urlparse(cfg.base_url).scheme != "https" and not cfg.base_url.startswith("http://localhost"):
        raise SystemExit("YATB_BASE_URL muss https sein")
    log.info("Dashboard startet: %s%s (Bot-API %s)", cfg.base_url, cfg.prefix, cfg.bot_api)
    web.run_app(create_app(cfg), host="0.0.0.0", port=int(os.getenv("YATB_WEB_PORT", "8080")), access_log=None,
                print=None)


if __name__ == "__main__":
    main()
