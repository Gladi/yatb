"""
YATB-Dashboard - HTML-Ausgabe (ohne Template-Bibliothek, ohne JavaScript).

Alles, was von Discord oder vom Bot kommt (Namen, Bezeichnungen), wird mit esc() maskiert. Texte aus dashboard/texts
sind eigenes HTML. Inline-Styles sind tabu (CSP style-src 'self'), Balken daher als <progress>.
"""
import hashlib
import html
import os
from typing import Dict, List, Optional

import locales
from dashboard.texts.de import TEXTS as DE
from dashboard.texts.en import TEXTS as EN
from dashboard.texts.mt import TEXTS_MT

LANGS = ("en", "de", "fr", "es", "it", "ru", "nl")
LANG_NAMES = {"en": "English", "de": "Deutsch", "fr": "Français", "es": "Español", "it": "Italiano", "ru": "Русский", "nl": "Nederlands"}
TEXTS = {"en": EN, "de": DE, **TEXTS_MT}
STATIC_DIR = os.getenv("YATB_STATIC_DIR", "")
_versions: Dict[str, tuple] = {}
CURRENT = ' aria-current="true"'


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def t(lang: str, key: str, **values) -> str:
    text = TEXTS.get(lang, {}).get(key) or EN[key]
    for name, value in values.items():
        text = text.replace("{" + name + "}", str(value))
    return text


def bot_text(lang: str, key: str) -> str:
    """Texte des Bots (z. B. Namen der Datenschutz-Optionen) - schon in 6 Sprachen vorhanden."""
    return esc(locales.get_text(lang, key))


def pick_lang(accept: str) -> str:
    for part in (accept or "").split(","):
        code = part.split(";")[0].strip().lower()[:2]
        if code in LANGS:
            return code
    return "en"


def asset(name: str) -> str:
    """/static/<name>?v=<hash> - Hash aus der gebauten Website (Caddy cached /static/ ein Jahr)."""
    path = os.path.join(STATIC_DIR, name) if STATIC_DIR else ""
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return f"/static/{name}"
    cached = _versions.get(name)
    if cached is None or cached[0] != mtime:
        with open(path, "rb") as fh:
            cached = (mtime, hashlib.sha256(fh.read()).hexdigest()[:10])
        _versions[name] = cached
    return f"/static/{name}?v={cached[1]}"


def shell(lang: str, title: str, body: str, *, path: str, user: Optional[str] = None, csrf: str = "",
          prefix: str = "/app") -> str:
    langs = "".join(f'<li><a href="{esc(path)}?lang={lg}" hreflang="{lg}" lang="{lg}"'
                    f'{CURRENT if lg == lang else ""}>{LANG_NAMES[lg]}</a></li>' for lg in LANGS)
    account = ""
    if user:
        account = (f'<form class="logout" method="post" action="{prefix}/logout"><input type="hidden" name="csrf" value="{esc(csrf)}">'
                   f'<span class="who">{esc(user)}</span> <button type="submit">{t(lang, "logout")}</button></form>')
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="robots" content="noindex">
<title>{esc(title)} · YATB</title>
<link rel="icon" href="{asset("img/favicon-32.png")}" type="image/png" sizes="32x32">
<link rel="stylesheet" href="{asset("style.css")}">
<link rel="stylesheet" href="{asset("app.css")}">
<script src="{asset("app.js")}" defer></script>
</head>
<body class="app">
<header class="top">
<div class="wrap bar">
<a class="brand" href="/{lang}/"><img src="{asset("img/mark-96.webp")}" width="40" height="40" alt=""><span>YATB</span></a>
<nav class="nav app-nav"><ul><li><a href="{prefix}/" aria-current="page">{t(lang, "nav_dashboard")}</a></li><li><a href="/{lang}/">{t(lang, "nav_site")}</a></li></ul></nav>
<details class="langs"><summary aria-label="{t(lang, "nav_language")}"><span aria-hidden="true">🌐</span> {lang.upper()}</summary><ul>{langs}</ul></details>
{account}
</div>
</header>
<main class="wrap">
{body}
</main>
</body>
</html>
"""


# ----------------- Seiten -----------------
def login_page(lang: str, prefix: str, failed: bool = False) -> str:
    error = f'<p class="placeholder">{t(lang, "login_failed")}</p>' if failed else ""
    return shell(lang, t(lang, "login_title"), f"""
<section class="hero app-hero">
<img class="hero-logo" src="{asset("img/logo-256.webp")}" width="160" height="160" alt="YATB">
<div>
<h1>{t(lang, "login_title")}</h1>
<p class="lead">{t(lang, "login_lead")}</p>
{error}
<p><a class="button discord" href="{prefix}/login">{t(lang, "login_button")}</a></p>
<p class="muted">{t(lang, "login_data")}</p>
</div>
</section>""", path=f"{prefix}/", prefix=prefix)


def privacy_card(lang: str, local_only: bool, csrf: str, prefix: str, saved: bool = False) -> str:
    options = []
    for value, name_key, desc_key, active in (("standard", "privacy_standard_name", "privacy_standard_desc", not local_only),
                                              ("local", "privacy_local_name", "privacy_local_desc", local_only)):
        action = (f'<span class="badge current">{t(lang, "privacy_current")} ✓</span>' if active else
                  f'<form method="post" action="{prefix}/privacy"><input type="hidden" name="csrf" value="{esc(csrf)}">'
                  f'<input type="hidden" name="choice" value="{value}"><button type="submit">{t(lang, "privacy_use")}</button></form>')
        options.append(f'<div class="option{" chosen" if active else ""}"><h3>{bot_text(lang, name_key)}</h3>'
                       f'<p>{bot_text(lang, desc_key)}</p>{action}</div>')
    note = f'<p class="saved" role="status">{t(lang, "privacy_saved")}</p>' if saved else ""
    return (f'<section class="card"><h2>{t(lang, "privacy_title")}</h2><p class="muted">{t(lang, "privacy_lead")}</p>'
            f'{note}<div class="options">{"".join(options)}</div></section>')


def servers_card(lang: str, guilds: List[dict], prefix: str) -> str:
    if not guilds:
        return f'<section class="card"><h2>{t(lang, "servers_title")}</h2><p>{t(lang, "servers_none")}</p></section>'
    items = "".join(f'<li><a class="server" href="{prefix}/g/{esc(g["id"])}"><span class="initial" aria-hidden="true">'
                    f'{esc((g["name"] or "?")[:1].upper())}</span><span>{esc(g["name"])}</span>'
                    f'<span class="go">{t(lang, "server_open")} →</span></a></li>' for g in guilds)
    return (f'<section class="card"><h2>{t(lang, "servers_title")}</h2><p class="muted">{t(lang, "servers_lead")}</p>'
            f'<ul class="servers">{items}</ul></section>')


def home_page(lang: str, user: str, csrf: str, local_only: bool, guilds: List[dict], prefix: str, saved: bool) -> str:
    body = (f'<h1>{t(lang, "hello", name=esc(user))}</h1>' + servers_card(lang, guilds, prefix)
            + privacy_card(lang, local_only, csrf, prefix, saved))
    return shell(lang, t(lang, "title"), body, path=f"{prefix}/", user=user, csrf=csrf, prefix=prefix)


DECIMAL = {"en": ".", "de": ",", "fr": ",", "es": ",", "it": ",", "ru": ",", "nl": ","}
GROUP = {"en": ",", "de": ".", "fr": "\u202f", "es": ".", "it": ".", "ru": "\u202f", "nl": "."}
SYMBOL = {"EUR": "€", "USD": "$"}


def fmt_num(lang: str, value: float, decimals: int = 0) -> str:
    """Zahl im Format der Sprache: 18.900 / 18,900 / 0,06."""
    raw = f"{value:,.{decimals}f}"
    return raw.replace(",", "\0").replace(".", DECIMAL.get(lang, ".")).replace("\0", GROUP.get(lang, ","))


def fmt_money(lang: str, amount: float, currency: str) -> str:
    symbol = SYMBOL.get(currency, currency)
    if 0 < amount < 0.01:
        return "< " + fmt_money(lang, 0.01, currency)
    num = fmt_num(lang, amount, 2)
    return f"{symbol}{num}" if lang == "en" else f"{num}\u00a0{symbol}"


def _usage_table(lang: str, usage: dict, key: dict) -> str:
    """Heute / dieser Monat als kleine Tabelle: Zahlen ohne Pluralformen, sauber untereinander."""
    ai = key.get("kind") == "openai"
    cols = [("col_requests", lambda r: fmt_num(lang, r.get("requests", 0)))]
    if ai:
        cols.append(("col_tokens", lambda r: fmt_num(lang, r.get("tokens_in", 0) + r.get("tokens_out", 0))))
    else:
        cols.append(("col_chars", lambda r: fmt_num(lang, r.get("chars", 0))))
    if key["tier"] == "paid":
        cols.append(("col_cost", lambda r: fmt_money(lang, r.get("cost", 0.0), key["currency"])))
    head = "".join(f"<th>{t(lang, c)}</th>" for c, _ in cols)
    rows = "".join(f'<tr><th scope="row">{t(lang, label)}</th>' + "".join(f"<td>{fn(usage.get(period) or {})}</td>" for _, fn in cols)
                   + "</tr>" for label, period in (("today", "day"), ("this_month", "month")))
    return f'<table class="usage-table"><thead><tr><td></td>{head}</tr></thead><tbody>{rows}</tbody></table>'


def _hidden(csrf: str, **fields) -> str:
    return f'<input type="hidden" name="csrf" value="{esc(csrf)}">' + "".join(
        f'<input type="hidden" name="{esc(k)}" value="{esc(v)}">' for k, v in fields.items())


def key_card(lang: str, key: dict, edit_url: str = "") -> str:
    usage = key.get("usage") or {}
    badges = [f'<span class="badge">{t(lang, key["tier"])}</span>',
              f'<span class="badge{"" if key["limit_enabled"] else " warn"}">'
              f'{t(lang, "limit_on" if key["limit_enabled"] else "limit_off")}</span>']
    edit = f' <a class="edit" href="{esc(edit_url)}">{t(lang, "edit")}</a>' if edit_url else ""
    head = (f'<h3>{esc(key["provider_name"])} <code>…{esc(key["last4"])}</code>'
            f'{" <em>" + esc(key["label"]) + "</em>" if key.get("label") else ""} {"".join(badges)}{edit}</h3>')
    if key.get("shared"):
        head += f'<p class="muted">{t(lang, "shared")}</p>'
    meter = ""
    limit = usage.get("limit")
    if limit and limit.get("limit"):
        used, total = float(limit["used"]), float(limit["limit"])
        pct = min(100, round(used / total * 100))
        level = "crit" if pct >= 90 else "warn" if pct >= 75 else "ok"
        if limit["kind"] == "cost":
            label, amount = t(lang, "budget_month"), t(lang, "of", used=fmt_money(lang, used, key["currency"]),
                                                       limit=fmt_money(lang, total, key["currency"]))
            left = fmt_money(lang, max(0.0, total - used), key["currency"])
        else:
            label, amount = t(lang, "quota_month"), t(lang, "of_chars", used=fmt_num(lang, used), limit=fmt_num(lang, total))
            left = t(lang, "n_chars", n=fmt_num(lang, max(0.0, total - used)))
        meter = (f'<div class="meter"><div class="meter-head"><span>{label}</span> <strong>{amount}</strong></div>'
                 f'<progress class="usage {level}" value="{pct}" max="100">{pct} %</progress>'
                 f'<div class="muted">{t(lang, "used_left", pct=pct, left=left)}</div></div>')
    return f'<article class="key-card">{head}{meter}{_usage_table(lang, usage, key)}</article>'


def _notice(lang: str, key: Optional[str]) -> str:
    return f'<p class="saved" role="status">{t(lang, key)}</p>' if key else ""


def _picker(lang: str, guild: dict, guilds: List[dict], prefix: str) -> str:
    items = "".join(f'<li><a href="{prefix}/g/{esc(g["id"])}"{" aria-current=page" if g["id"] == guild["id"] else ""}>'
                    f'{esc(g["name"])}</a></li>' for g in guilds)
    return f'<nav class="picker" aria-label="{t(lang, "servers_title")}"><ul>{items}</ul></nav>'


def _guild_tabs(lang: str, gid: str, prefix: str, active: str) -> str:
    tabs = (("overview", f"{prefix}/g/{gid}", "overview_title"), ("stats", f"{prefix}/g/{gid}/stats", "stats_link"))
    return '<nav class="tabs"><ul>' + "".join(
        f'<li><a href="{url}"{" aria-current=page" if name == active else ""}>{t(lang, label)}</a></li>'
        for name, url, label in tabs) + "</ul></nav>"


def _chain_card(lang: str, guild: dict, csrf: str, prefix: str) -> str:
    gid = esc(guild["id"])
    movable = [s for s in guild["chain"] if s.get("key_id") is not None]
    items = []
    for s in guild["chain"]:
        name = (f'<span class="stage-name">{esc(s["provider_name"])}'
                f'{" <em>" + esc(s["label"]) + "</em>" if s.get("label") else ""}</span>'
                f'{" <span class=badge>" + t(lang, s["tier"]) + "</span>" if s.get("tier") else ""}'
                f' <span class="state {esc(s["state"])}">{t(lang, "state_" + s["state"])}</span>')
        buttons = ""
        if s.get("key_id") is not None and len(movable) > 1:
            i = movable.index(s)
            for direction, arrow, label, disabled in (("up", "↑", "order_up", i == 0),
                                                      ("down", "↓", "order_down", i == len(movable) - 1)):
                buttons += (f'<form method="post" action="{prefix}/g/{gid}/order">{_hidden(csrf, key_id=s["key_id"], move=direction)}'
                            f'<button type="submit" title="{t(lang, label)}" aria-label="{t(lang, label)}"'
                            f'{" disabled" if disabled else ""}>{arrow}</button></form>')
        items.append(f'<li><span class="stage">{name}</span><span class="moves">{buttons}</span></li>')
    reset = ""
    if guild["custom_order"]:
        reset = (f'<form method="post" action="{prefix}/g/{gid}/order">{_hidden(csrf, move="reset")}'
                 f'<button type="submit">{t(lang, "order_reset")}</button></form>')
    order_note = t(lang, "chain_custom" if guild["custom_order"] else "chain_default")
    hint = f'<p class="muted">{t(lang, "order_hint")}</p>' if len(movable) > 1 else ""
    return (f'<section class="card"><h2>{t(lang, "chain_title")} <span class="badge">{order_note}</span></h2>'
            f'<p class="muted">{t(lang, "chain_lead")}</p><ol class="chain-list">{"".join(items)}</ol>{hint}{reset}</section>')


def guild_page(lang: str, user: str, csrf: str, guild: dict, guilds: List[dict], prefix: str,
               notice: Optional[str] = None) -> str:
    gid = esc(guild["id"])
    if guild["bridges"]:
        rows = "".join(f'<tr><td><code>{esc(b["bridge"])}</code></td><td>' + ", ".join(
            f'#{esc(c["name"] or c["id"])} <span class="muted">({esc(c["language"])})</span>' for c in b["channels"])
            + "</td></tr>" for b in guild["bridges"])
        bridges = f'<div class="table-wrap"><table><tbody>{rows}</tbody></table></div>'
    else:
        bridges = f'<p>{t(lang, "bridges_none")}</p>'
    log = guild.get("log_channel")
    log_html = f'#{esc(log["name"] or log["id"])}' if log else t(lang, "log_none")
    if guild["keys"]:
        keys = "".join(key_card(lang, k, f"{prefix}/g/{gid}/k/{k['id']}") for k in guild["keys"])
    else:
        keys = f'<p>{t(lang, "keys_none")}</p>'
    body = f"""
{_picker(lang, guild, guilds, prefix)}
<h1>{esc(guild["name"])}</h1>
{_guild_tabs(lang, gid, prefix, "overview")}
{_notice(lang, notice)}
{_chain_card(lang, guild, csrf, prefix)}
<section class="card"><h2>{t(lang, "keys_title")}</h2>{keys}<p class="muted">{t(lang, "keys_add_hint")}</p></section>
<section class="card"><h2>{t(lang, "bridges_title")}</h2>{bridges}<h3>{t(lang, "log_title")}</h3><p>{log_html}</p></section>
<p><a href="{prefix}/">← {t(lang, "back")}</a></p>"""
    return shell(lang, guild["name"], body, path=f"{prefix}/g/{gid}", user=user, csrf=csrf, prefix=prefix)


def edit_page(lang: str, user: str, csrf: str, guild: dict, key: dict, prefix: str, *, error: Optional[str] = None,
              values: Optional[dict] = None, delete_error: bool = False) -> str:
    """Formular für die Einstellungen eines Keys (nie der Key selbst) und das Entfernen mit Bestätigungswort."""
    gid, kid = esc(guild["id"]), esc(key["id"])
    v = {"label": key.get("label") or "", "tier": key["tier"], "currency": key["currency"],
         "budget": "" if key.get("budget") is None else fmt_num(lang, key["budget"], 2).replace(GROUP.get(lang, ","), ""),
         "region": key.get("region") or "",
         "limit": "on" if key["limit_enabled"] else "off", **(values or {})}
    tiers = [("paid", t(lang, "paid"))] + ([("free", t(lang, "free"))] if key.get("free_allowed") else [])
    tier_opts = "".join(f'<option value="{val}"{" selected" if v["tier"] == val else ""}>{label}</option>' for val, label in tiers)
    cur_opts = "".join(f'<option value="{c}"{" selected" if v["currency"] == c else ""}>{c}</option>'
                       for c in guild.get("currencies", ["USD", "EUR"]))
    default = key.get("budget_default")
    default_txt = fmt_money(lang, default, key["currency"]) if default is not None else "-"
    region = ""
    if key.get("needs_region"):
        region = (f'<label for="f-region">{t(lang, "field_region")}</label><input id="f-region" name="region" required '
                  f'maxlength="32" pattern="[a-zA-Z0-9]{{2,32}}" value="{esc(v["region"])}">'
                  f'<p class="hint">{t(lang, "field_region_hint")}</p>')
    limit = "".join(f'<label class="radio"><input type="radio" name="limit" value="{val}"{" checked" if v["limit"] == val else ""}> '
                    f'{t(lang, text)}</label>' for val, text in (("on", "limit_on_long"), ("off", "limit_off_long")))
    err = f'<p class="placeholder" role="alert">{t(lang, "err_" + error)}</p>' if error else ""
    word = t(lang, "delete_word")
    del_err = f'<p class="placeholder" role="alert">{t(lang, "delete_wrong", word=esc(word))}</p>' if delete_error else ""
    body = f"""
<h1>{t(lang, "edit_title")}</h1>
<p class="lead">{esc(guild["name"])} · {esc(key["provider_name"])} <code>…{esc(key["last4"])}</code></p>
<section class="card"><form class="settings" method="post" action="{prefix}/g/{gid}/k/{kid}">{_hidden(csrf)}
{err}
<label for="f-label">{t(lang, "field_label")}</label><input id="f-label" name="label" maxlength="32" value="{esc(v["label"])}">
<p class="hint">{t(lang, "field_label_hint")}</p>
<label for="f-tier">{t(lang, "field_tier")}</label><select id="f-tier" name="tier">{tier_opts}</select>
<div class="row"><div><label for="f-budget">{t(lang, "field_budget")}</label>
<input id="f-budget" name="budget" inputmode="decimal" maxlength="8" value="{esc(v["budget"])}" placeholder="{esc(fmt_num(lang, default, 2) if default is not None else "")}"></div>
<div><label for="f-currency">{t(lang, "field_currency")}</label><select id="f-currency" name="currency">{cur_opts}</select></div></div>
<p class="hint">{t(lang, "field_budget_hint", default=default_txt)}</p>
{region}
<fieldset><legend>{t(lang, "field_limit")}</legend>{limit}
<label class="check"><input type="checkbox" name="confirm_limit_off" value="1"> {t(lang, "confirm_limit_off")}</label></fieldset>
<p class="actions"><button type="submit" class="primary">{t(lang, "save")}</button> <a href="{prefix}/g/{gid}">{t(lang, "cancel")}</a></p>
</form></section>
<section class="card danger"><h2>{t(lang, "delete_title")}</h2>
<form method="post" action="{prefix}/g/{gid}/k/{kid}/delete">{_hidden(csrf)}
<p>{t(lang, "delete_text", word=esc(word))}</p>{del_err}
<p class="actions"><input name="confirm" autocomplete="off" aria-label="{esc(word)}" placeholder="{esc(word)}">
<button type="submit" class="danger">{t(lang, "delete_button")}</button></p></form></section>"""
    return shell(lang, t(lang, "edit_title"), body, path=f"{prefix}/g/{gid}/k/{kid}", user=user, csrf=csrf, prefix=prefix)


PALETTE = ("#2f7de1", "#e8833a", "#2fa36b", "#9b59b6", "#d3362d", "#14a3b8", "#8a6d3b")


def _chart(lang: str, report: dict) -> str:
    """Gestapelte Balken (Aufrufe pro Tag und Dienst) als SVG - nur Attribute, kein Inline-CSS."""
    days, provs = report["days"], report["providers"]
    totals = [sum(p["per_day"][i] for p in provs) for i in range(len(days))]
    top = max(totals) or 1
    w, h, pad = 700, 180, 24
    bw = (w - pad) / len(days)
    bars = []
    for i, day in enumerate(days):
        y = h - pad
        for j, p in enumerate(provs):
            n = p["per_day"][i]
            if not n:
                continue
            bh = n / top * (h - 2 * pad)
            y -= bh
            bars.append(f'<rect x="{pad + i * bw + bw * 0.12:.1f}" y="{y:.1f}" width="{bw * 0.76:.1f}" height="{bh:.1f}" '
                        f'fill="{PALETTE[j % len(PALETTE)]}"><title>{esc(day)} · {esc(p["provider_name"])}: {n}</title></rect>')
    anchor = lambda i: "start" if i == 0 else "end" if i == len(days) - 1 else "middle"  # noqa: E731
    xpos = lambda i: pad if i == 0 else w if i == len(days) - 1 else pad + i * bw + bw / 2  # noqa: E731
    ticks = "".join(f'<text x="{xpos(i):.1f}" y="{h - 6}" text-anchor="{anchor(i)}" class="tick">{esc(days[i][5:])}</text>'
                    for i in sorted({0, len(days) // 2, len(days) - 1}))
    axis = (f'<text x="2" y="{pad - 6}" class="tick">{fmt_num(lang, top)}</text>'
            f'<line x1="{pad}" y1="{h - pad}" x2="{w}" y2="{h - pad}" class="axis"/>')
    legend = "".join(f'<li><span class="swatch s{j % len(PALETTE)}"></span>{esc(p["provider_name"])}</li>'
                     for j, p in enumerate(provs))
    return (f'<figure class="chart"><svg viewBox="0 0 {w} {h}" role="img" aria-label="{t(lang, "stats_chart")}">'
            f'{axis}{"".join(bars)}{ticks}</svg><figcaption><ul class="legend">{legend}</ul></figcaption></figure>')


def _pct(lang: str, value) -> str:
    return "-" if value is None else f"{fmt_num(lang, value * 100)} %"


def _ms(lang: str, value) -> str:
    if value is None:
        return "-"
    return f"{fmt_num(lang, value / 1000, 1)} s" if value >= 1000 else f"{fmt_num(lang, value)} ms"


def stats_page(lang: str, user: str, csrf: str, guild: dict, guilds: List[dict], report: dict, days: int,
               currency_by_provider: Dict[str, str], prefix: str) -> str:
    gid = esc(guild["id"])
    periods = "".join(f'<li><a href="{prefix}/g/{gid}/stats?days={n}"{" aria-current=page" if n == days else ""}>'
                      f'{t(lang, "period", n=n)}</a></li>' for n in (7, 30, 90))
    provs = report["providers"]
    if not provs:
        content = f'<p>{t(lang, "stats_none")}</p>'
    else:
        rows = []
        for p in provs:
            group = f' <span class="badge">{t(lang, "stats_group", g=esc(p["group"]))}</span>' if p.get("group") else ""
            tokens = p["tokens_in"] + p["tokens_out"]
            volume = (t(lang, "n_tokens", n=fmt_num(lang, tokens)) if tokens else
                      t(lang, "n_chars", n=fmt_num(lang, p["chars"])))
            cost = fmt_money(lang, p["cost"], currency_by_provider.get(p["provider"], "USD")) if p["cost"] else "-"
            rows.append(f'<tr><th scope="row">{esc(p["provider_name"])}{group}</th><td>{fmt_num(lang, p["calls"])}</td>'
                        f'<td>{_pct(lang, p["ok_rate"])}</td><td>{_pct(lang, p["structure_rate"])}</td>'
                        f'<td>{fmt_num(lang, p["fell_through"])}</td><td>{fmt_num(lang, p["limit_skips"])}</td>'
                        f'<td>{_ms(lang, p["p50_ms"])} · {_ms(lang, p["p95_ms"])}</td><td>{volume}</td><td>{cost}</td></tr>')
        cols = "".join(f"<th>{t(lang, c)}</th>" for c in ("stats_col_calls", "stats_col_ok", "stats_col_structure",
                                                         "stats_col_fell", "stats_col_limit", "stats_col_latency",
                                                         "stats_col_volume", "stats_col_cost"))
        content = (f'<h3>{t(lang, "stats_chart")}</h3>{_chart(lang, report)}'
                   f'<div class="table-wrap"><table class="stats"><thead><tr><th></th>{cols}</tr></thead>'
                   f'<tbody>{"".join(rows)}</tbody></table></div>')
    body = f"""
{_picker(lang, guild, guilds, prefix)}
<h1>{esc(guild["name"])}</h1>
{_guild_tabs(lang, gid, prefix, "stats")}
<section class="card"><h2>{t(lang, "stats_title")}</h2><p class="muted">{t(lang, "stats_lead")}</p>
<nav class="periods"><ul>{periods}</ul></nav>{content}</section>
<section class="card">{t(lang, "stats_explain")}</section>"""
    return shell(lang, t(lang, "stats_title"), body, path=f"{prefix}/g/{gid}/stats", user=user, csrf=csrf, prefix=prefix)


def error_page(lang: str, key: str, prefix: str, user: Optional[str] = None, csrf: str = "") -> str:
    body = (f'<h1>{t(lang, "error_title")}</h1><p>{t(lang, key)}</p>'
            f'<p><a href="{prefix}/">← {t(lang, "back")}</a></p>')
    return shell(lang, t(lang, "error_title"), body, path=f"{prefix}/", user=user, csrf=csrf, prefix=prefix)
