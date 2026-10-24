"""
YATB - Unterstützte Anbieter für Server-eigene API-Keys (BYOK)

Die Anbieter stehen in config/providers.toml (Pfad über YATB_PROVIDERS_FILE änderbar). Admins wählen
nur einen Anbieter aus der Liste, eigene Endpunkt-URLs gibt es nicht.
Ist die Datei fehlerhaft, startet der Bot trotzdem: fehlerhafte Einträge werden übersprungen,
Google Translate und Azure fallen notfalls auf eingebaute Standardwerte zurück.
"""
import asyncio
import logging
import os
import re
import tomllib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

import translator as tr

log = logging.getLogger("yatb.providers")

CONFIG_FILE = os.getenv("YATB_PROVIDERS_FILE") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "config", "providers.toml"
)
AZURE_URL = "https://api.cognitive.microsofttranslator.com/translate"
KINDS = {"openai", "google", "azure"}
GROUPS = {"A", "B", "C"}
TIERS = ("free", "paid")

# Status, bei denen der Key sicher ungültig ist (Gemini meldet ungültige Keys mit 400)
REJECT_STATUSES = {"HTTP_400", "HTTP_401", "HTTP_403"}


@dataclass(frozen=True)
class Limits:
    rpm: Optional[int] = None           # Anfragen pro Minute
    rpd: Optional[int] = None           # Anfragen pro Tag (UTC)
    tpm: Optional[int] = None           # Tokens pro Minute
    tpd: Optional[int] = None           # Tokens pro Tag (UTC)
    chars_month: Optional[int] = None   # Zeichen pro Monat (Google, Azure)
    budget_month: Optional[float] = None  # Kosten pro Monat (Bezahl-Keys)


_LIMIT_TYPES = {"rpm": int, "rpd": int, "tpm": int, "tpd": int, "chars_month": int, "budget_month": float}


@dataclass(frozen=True)
class Provider:
    id: str
    name: str
    kind: str                         # "openai" (OpenAI-kompatibel), "google", "azure"
    group: str = "C"
    enabled: bool = True
    base_url: Optional[str] = None
    model: Optional[str] = None
    verify_url: Optional[str] = None  # kostenloser Endpunkt, der den Key prüft
    extra: Dict[str, Any] = field(default_factory=dict, hash=False, compare=False)
    free_available: bool = True
    eea_free_allowed: bool = True
    price_in: float = 0.0             # je 1 Mio. Tokens
    price_out: float = 0.0
    price_cached: Optional[float] = None  # je 1 Mio. Tokens aus dem Prompt-Cache des Anbieters (None = wie price_in)
    price_chars: float = 0.0          # je 1 Mio. Zeichen
    currency: str = "USD"
    privacy_free: str = ""
    privacy_paid: str = ""
    limits_free: Limits = Limits()
    limits_paid: Limits = Limits()

    @property
    def needs_region(self) -> bool:
        return self.kind == "azure"

    def limits(self, tier: str) -> Limits:
        return self.limits_paid if tier == "paid" else self.limits_free

    def privacy(self, tier: str) -> str:
        return self.privacy_paid if tier == "paid" else self.privacy_free

    def cost(self, tokens_in: int = 0, tokens_out: int = 0, chars: int = 0, tokens_cached: int = 0) -> float:
        cached = min(max(tokens_cached, 0), tokens_in)   # gecachte Tokens sind Teil von tokens_in
        p_cached = self.price_in if self.price_cached is None else self.price_cached
        return ((tokens_in - cached) * self.price_in + cached * p_cached + tokens_out * self.price_out
                + chars * self.price_chars) / 1_000_000


# Rückfall, falls die Konfigurationsdatei fehlt oder diese Einträge fehlerhaft sind
BUILTIN: Dict[str, Provider] = {p.id: p for p in (
    Provider("google_translate", "Google Translate", "google", price_chars=20.0,
             limits_free=Limits(chars_month=500_000), limits_paid=Limits(budget_month=5.0)),
    Provider("azure", "Azure Translator", "azure", price_chars=10.0,
             limits_free=Limits(chars_month=2_000_000), limits_paid=Limits(budget_month=5.0)),
)}

_ID_RE = re.compile(r"^[a-z0-9_]{2,32}$")
_FIELDS = {
    "name", "kind", "group", "enabled", "base_url", "model", "verify_url", "extra", "free_available",
    "eea_free_allowed", "price_in", "price_out", "price_cached", "price_chars", "currency", "privacy_free", "privacy_paid", "limits",
}


def _num(value: Any, typ: type, where: str, errors: List[str]):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        errors.append(f"{where}: muss eine Zahl >= 0 sein")
        return None
    if typ is int and not float(value).is_integer():
        errors.append(f"{where}: muss eine ganze Zahl sein")
        return None
    return typ(value)


def _parse_limits(raw: Any, where: str, errors: List[str]) -> Limits:
    if raw is None:
        return Limits()
    if not isinstance(raw, dict):
        errors.append(f"{where}: muss eine Tabelle sein")
        return Limits()
    values = {}
    for key, value in raw.items():
        if key not in _LIMIT_TYPES:
            errors.append(f"{where}.{key}: unbekanntes Limit")
            continue
        values[key] = _num(value, _LIMIT_TYPES[key], f"{where}.{key}", errors)
    return Limits(**{k: v for k, v in values.items() if v is not None})


def _parse_provider(pid: str, raw: Any) -> Tuple[Optional[Provider], List[str]]:
    errors: List[str] = []
    if not _ID_RE.match(pid):
        return None, [f"{pid}: ungültige ID (a-z, 0-9, _)"]
    if not isinstance(raw, dict):
        return None, [f"{pid}: muss eine Tabelle sein"]
    for key in raw:
        if key not in _FIELDS:
            errors.append(f"{pid}.{key}: unbekanntes Feld")
    kind = raw.get("kind")
    if kind not in KINDS:
        errors.append(f"{pid}.kind: muss einer von {sorted(KINDS)} sein")
    name = raw.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append(f"{pid}.name: fehlt")
    group = raw.get("group", "C")
    if group not in GROUPS:
        errors.append(f"{pid}.group: muss A, B oder C sein")
    if kind == "openai":
        for key in ("base_url", "model"):
            if not isinstance(raw.get(key), str) or not raw.get(key):
                errors.append(f"{pid}.{key}: fehlt (Pflicht bei kind = openai)")
        if isinstance(raw.get("base_url"), str) and not raw["base_url"].startswith("https://"):
            errors.append(f"{pid}.base_url: muss mit https:// beginnen")
    if raw.get("verify_url") is not None and not str(raw["verify_url"]).startswith("https://"):
        errors.append(f"{pid}.verify_url: muss mit https:// beginnen")
    for key in ("enabled", "free_available", "eea_free_allowed"):
        if key in raw and not isinstance(raw[key], bool):
            errors.append(f"{pid}.{key}: muss true oder false sein")
    if "extra" in raw and not isinstance(raw["extra"], dict):
        errors.append(f"{pid}.extra: muss eine Tabelle sein")
    prices = {k: _num(raw[k], float, f"{pid}.{k}", errors) for k in ("price_in", "price_out", "price_cached", "price_chars") if k in raw}
    limits = raw.get("limits") or {}
    if not isinstance(limits, dict) or set(limits) - set(TIERS):
        errors.append(f"{pid}.limits: nur [limits.free] und [limits.paid] erlaubt")
        limits = {}
    lim_free = _parse_limits(limits.get("free"), f"{pid}.limits.free", errors)
    lim_paid = _parse_limits(limits.get("paid"), f"{pid}.limits.paid", errors)
    if errors:
        return None, errors
    return Provider(
        id=pid, name=name.strip(), kind=kind, group=group, enabled=raw.get("enabled", True),
        base_url=(raw.get("base_url") or "").rstrip("/") or None, model=raw.get("model"),
        verify_url=raw.get("verify_url"), extra=dict(raw.get("extra") or {}),
        free_available=raw.get("free_available", True), eea_free_allowed=raw.get("eea_free_allowed", True),
        price_in=prices.get("price_in") or 0.0, price_out=prices.get("price_out") or 0.0,
        price_cached=prices.get("price_cached"),
        price_chars=prices.get("price_chars") or 0.0, currency=str(raw.get("currency", "USD")),
        privacy_free=str(raw.get("privacy_free", "")), privacy_paid=str(raw.get("privacy_paid", "")),
        limits_free=lim_free, limits_paid=lim_paid,
    ), []


def parse_config(data: Dict[str, Any]) -> Tuple[Dict[str, Provider], List[str]]:
    """Gültige Anbieter + Fehlerliste. Fehlerhafte Einträge werden übersprungen."""
    providers: Dict[str, Provider] = {}
    errors: List[str] = []
    section = data.get("providers")
    if not isinstance(section, dict):
        return {}, ["[providers] fehlt"]
    for pid, raw in section.items():
        provider, errs = _parse_provider(pid, raw)
        errors.extend(errs)
        if provider is not None:
            providers[pid] = provider
    return providers, errors


def load_providers(path: str = CONFIG_FILE) -> Dict[str, Provider]:
    try:
        with open(path, "rb") as fh:
            providers, errors = parse_config(tomllib.load(fh))
    except FileNotFoundError:
        providers, errors = {}, [f"{path} nicht gefunden"]
    except (tomllib.TOMLDecodeError, OSError) as exc:
        providers, errors = {}, [f"{path} nicht lesbar: {exc}"]
    for err in errors:
        log.error("Anbieter-Konfiguration: %s", err)
    for pid, builtin in BUILTIN.items():
        if pid not in providers:
            log.warning("Anbieter %s: eingebaute Standardwerte aktiv.", pid)
            providers[pid] = builtin
    log.info("Anbieter geladen: %s", ", ".join(f"{p.id}{'' if p.enabled else ' (aus)'}" for p in providers.values()))
    return providers


PROVIDERS: Dict[str, Provider] = load_providers()


def free_allowed(provider: Provider) -> bool:
    """Darf ein Key dieses Anbieters als Gratis-Stufe genutzt werden? Gemini Free: nicht für Nutzer im EWR/CH/UK."""
    return provider.free_available and provider.eea_free_allowed


async def _status(session: aiohttp.ClientSession, method: str, url: str, **kwargs) -> str:
    """Nur der Status zählt; Antworttexte werden nicht gelesen oder geloggt."""
    try:
        async with session.request(method, url, timeout=aiohttp.ClientTimeout(total=10), **kwargs) as resp:
            return "OK" if resp.status == 200 else f"HTTP_{resp.status}"
    except asyncio.TimeoutError:
        return "TIMEOUT"
    except aiohttp.ClientError as exc:
        return f"NETWORK_{type(exc).__name__}"


async def verify_key(session: aiohttp.ClientSession, provider: Provider, secret: str, region: Optional[str] = None) -> str:
    """Prüft einen Key ohne Kosten (bzw. mit 5 Zeichen). Status: OK, HTTP_4xx, TIMEOUT, ..."""
    if provider.kind == "google":
        return await tr.check_google_key(session, secret)
    if provider.kind == "azure":
        headers = {"Ocp-Apim-Subscription-Key": secret}
        if region:
            headers["Ocp-Apim-Subscription-Region"] = region
        return await _status(
            session, "POST", AZURE_URL, headers=headers, json=[{"Text": "hello"}],
            params={"api-version": "3.0", "from": "en", "to": "de"},
        )
    url = provider.verify_url or f"{provider.base_url}/models"
    return await _status(session, "GET", url, headers={"Authorization": f"Bearer {secret}"})
