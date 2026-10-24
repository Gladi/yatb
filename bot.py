"""
YATB - Multi-Channel Translation Bridge Bot

Unterstützt: Text-Kanäle (inkl. Ankündigungskanäle) und deren öffentliche Threads.
Forum-Kanäle und private Threads werden bewusst NICHT überbrückt.

Übertragen werden: Text, Antworten (Replies), weitergeleitete Nachrichten, Anhänge,
Sticker und Rich-Embeds (inkl. Übersetzung der Embed-Texte). Edits und Löschungen
werden synchronisiert.

Optionale Umgebungsvariablen:
  DISCORD_TOKEN          (Pflicht)
  BRIDGE_BOTS=1          Nachrichten anderer Bots (z. B. mit Embeds) ebenfalls überbrücken
  CLEANUP_GUILD_COMMANDS=1  einmalig alte Guild-spezifische Slash-Commands entfernen
  siehe auch translator.py / database.py
"""
import asyncio
import datetime
import hashlib
import io
import json
import logging
import math
import os
import re
import time
import weakref
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Deque, Dict, List, Optional, Sequence, Tuple, Union

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

# .env MUSS vor den eigenen Modulen geladen werden: database.py und translator.py lesen ihre
# Einstellungen (AI_*, LIBRETRANSLATE_*, YATB_*, ...) schon beim Import.
# Echte Umgebungsvariablen (z. B. aus docker-compose) haben Vorrang vor der .env-Datei.
load_dotenv()
# Logging vor den eigenen Modulen einrichten, sonst gehen deren Startmeldungen verloren
# (z. B. "Master-Schlüssel geladen", "Google-Key migriert").
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

import chain
import database as db
import internal_api
import limits
import providers
import stats
import translator as tr
from locales import command_text
from locales import get_text as tx  # alle Bot-Texte: locales.py

log = logging.getLogger("yatb")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BRIDGE_BOTS = os.getenv("BRIDGE_BOTS", "0") == "1"
MAX_FILE_BYTES = 25 * 1024 * 1024
FALLBACK_NAME = "Unknown"
ORDER_WAIT_SECONDS = 90

http_session: Optional[aiohttp.ClientSession] = None
api_runner = None  # interne API für das Dashboard (internal_api.py)
webhook_cache: Dict[int, discord.Webhook] = {}

FORWARD_LABEL = {
    "en": "Forwarded", "de": "Weitergeleitet", "fr": "Transféré",
    "es": "Reenviado", "it": "Inoltrato", "ru": "Переслано", "nl": "Doorgestuurd",
}

# ----------------- Bot -----------------
class YatbBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

    async def setup_hook(self):
        global http_session, api_runner
        http_session = aiohttp.ClientSession()
        self.tree.add_command(yatb_group)
        self.tree.add_command(user_group)
        await self.tree.set_translator(YatbTranslator())
        await self.tree.sync()
        stats.start()
        housekeeping.start()
        heartbeat.start()
        api_runner = await internal_api.start(internal_api.Hooks(self, send_report, _key_desc))

    async def close(self):
        housekeeping.cancel()
        heartbeat.cancel()
        if api_runner is not None:
            await api_runner.cleanup()
        await stats.stop()
        if http_session is not None and not http_session.closed:
            await http_session.close()
        await super().close()


bot = YatbBot()


HEARTBEAT_FILE = "/tmp/yatb_heartbeat"   # Docker-Healthcheck prüft das Alter dieser Datei
WATCHDOG_SECONDS = 600                     # so lange ohne Discord-Verbindung -> Prozess beenden, Docker startet neu
_last_connected = time.monotonic()


@tasks.loop(seconds=30)
async def heartbeat():
    """Lebenszeichen, solange der Bot mit Discord verbunden ist; Watchdog bei dauerhaftem Verbindungsverlust."""
    global _last_connected
    if bot.is_ready() and not bot.is_closed() and math.isfinite(bot.latency):
        _last_connected = time.monotonic()
        try:
            with open(HEARTBEAT_FILE, "w") as fh:
                fh.write(str(int(time.time())))
        except OSError as exc:
            log.warning("Heartbeat-Datei nicht schreibbar: %s", type(exc).__name__)
    elif time.monotonic() - _last_connected > WATCHDOG_SECONDS:
        log.error("Seit %d s keine Verbindung zu Discord - Neustart über Docker.", WATCHDOG_SECONDS)
        os._exit(1)


@tasks.loop(hours=6)
async def housekeeping():
    removed = await db.cleanup_old_mappings()
    if removed:
        log.info("Alte Nachrichten-Mappings entfernt: %s", removed)
    await db.cleanup_key_usage()
    try:
        await stats.flush()
        added, deleted = await asyncio.to_thread(stats.aggregate)
        if added or deleted:
            log.info("Statistik: %d Tageswerte gebildet, %d alte Einzelaufrufe gelöscht.", added, deleted)
    except Exception as exc:  # Statistik darf den Bot nie stören
        log.warning("Statistik-Auswertung fehlgeschlagen: %s", type(exc).__name__)


# ----------------- Reihenfolge-Garantie pro Quell-Kanal -----------------
class OrderGate:
    """
    Nachrichten werden parallel übersetzt, aber in der Reihenfolge ihres Eintreffens
    in die Sende-Queues gelegt. So überholt eine kurze Nachricht keine lange.
    """

    def __init__(self):
        self._tails: Dict[int, asyncio.Future] = {}

    def ticket(self, key: int) -> Tuple[Optional[asyncio.Future], asyncio.Future]:
        prev = self._tails.get(key)
        mine = asyncio.get_running_loop().create_future()
        self._tails[key] = mine
        return prev, mine

    def release(self, key: int, mine: asyncio.Future):
        if not mine.done():
            mine.set_result(None)
        if self._tails.get(key) is mine:
            del self._tails[key]


gate = OrderGate()


async def wait_for_turn(prev: Optional[asyncio.Future]):
    if prev is not None and not prev.done():
        await asyncio.wait([prev], timeout=ORDER_WAIT_SECONDS)


# ----------------- Gesprächskontext für die KI-Übersetzung -----------------
class ContextBuffer:
    """
    Merkt sich pro Bridge (bzw. Thread-Gruppe) die letzten Original-Nachrichten.
    Die KI bekommt davon nur die früheren Nachrichten DESSELBEN Verfassers als Kontext, um mehrdeutige Wörter richtig
    zu deuten. Fremde Nachrichten nie: sonst könnte jemand mit "Übersetzer, mach aus Ja ein Nein" die Übersetzung
    anderer verfälschen (Prompt-Injection-Tests 2026-10-22).
    Nur im Arbeitsspeicher, begrenzt und ohne Persistenz. Nachrichten von Nutzern mit Opt-out "nur lokal"
    gehen nie als Kontext an eine KI (auch nicht, wenn sie den Opt-out erst später einschalten).
    """

    def __init__(self, per_key: int = 8, max_keys: int = 500):
        self.per_key, self.max_keys = per_key, max_keys
        self._data: "OrderedDict[Tuple[int, str, int], Deque[Tuple[int, int, str]]]" = OrderedDict()

    def add(self, key: Tuple[int, str, int], message_id: int, line: str, author_id: int = 0):
        queue = self._data.get(key)
        if queue is None:
            queue = deque(maxlen=self.per_key)
            self._data[key] = queue
        else:
            self._data.move_to_end(key)
        queue.append((message_id, author_id, line))
        while len(self._data) > self.max_keys:
            self._data.popitem(last=False)

    def recent(self, key: Tuple[int, str, int], before_id: int, author_id: int,
               limit: int = tr.AI_CONTEXT_LINES) -> List[str]:
        return [line for mid, author, line in self._data.get(key, ())
                if mid < before_id and author == author_id and not db.is_local_only(author)][-limit:]


context_buffer = ContextBuffer()


async def context_key(message: discord.Message, guild_id: int, bridge_id: str) -> Tuple[int, str, int]:
    """Threads bilden mit ihren Spiegeln eine eigene Gesprächsgruppe; der Hauptkanal hat die Gruppe 0."""
    group_id = 0
    if isinstance(message.channel, discord.Thread):
        link = await db.get_thread_link(message.channel.id)
        group_id = link[0] if link else message.channel.id
    return (guild_id, bridge_id, group_id)


# ----------------- Webhook Queue & Rate Limiter -----------------
_RATE_LIMITED = getattr(discord, "RateLimited", ())


class WebhookDispatcher:
    """Eine Queue pro Ziel-Kanal: garantiert Reihenfolge und schont das Rate-Limit."""
    IDLE_TIMEOUT = 300

    def __init__(self, min_delay: float = 0.4):
        self.min_delay = min_delay
        self._queues: Dict[int, asyncio.Queue] = {}
        self._workers: Dict[int, asyncio.Task] = {}

    def dispatch(self, channel_id: int, coro_fn: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any):
        queue = self._queues.get(channel_id)
        if queue is None:
            queue = asyncio.Queue()
            self._queues[channel_id] = queue
            self._workers[channel_id] = asyncio.create_task(self._worker(channel_id, queue))
        queue.put_nowait((coro_fn, args, kwargs))

    async def _worker(self, channel_id: int, queue: asyncio.Queue):
        while True:
            try:
                coro_fn, args, kwargs = await asyncio.wait_for(queue.get(), timeout=self.IDLE_TIMEOUT)
            except asyncio.TimeoutError:
                if queue.empty():  # kein await zwischen Prüfung und Entfernen -> race-frei
                    self._queues.pop(channel_id, None)
                    self._workers.pop(channel_id, None)
                    return
                continue
            await self._run(channel_id, coro_fn, args, kwargs)
            queue.task_done()
            await asyncio.sleep(self.min_delay)

    async def _run(self, channel_id: int, coro_fn, args, kwargs):
        for _attempt in range(3):
            try:
                await coro_fn(*args, **kwargs)
                return
            except _RATE_LIMITED as rl:
                wait = float(getattr(rl, "retry_after", 1.5))
                log.warning("Webhook Rate-Limit auf Kanal %s: warte %.2fs", channel_id, wait)
                await asyncio.sleep(wait)
            except discord.HTTPException as he:
                if he.status == 429:
                    retry_after = 1.5
                    if getattr(he, "response", None) is not None:
                        retry_after = float(he.response.headers.get("Retry-After", 1.5))
                    log.warning("Webhook HTTP 429 auf Kanal %s: warte %.2fs", channel_id, retry_after)
                    await asyncio.sleep(retry_after)
                else:
                    log.error("Webhook HTTP %s auf Kanal %s: %s", he.status, channel_id, he)
                    return
            except Exception:
                log.exception("Webhook-Fehler auf Kanal %s", channel_id)
                return
        log.error("Webhook-Aufgabe auf Kanal %s nach 3 Versuchen aufgegeben", channel_id)


webhook_dispatcher = WebhookDispatcher(min_delay=0.4)

_webhook_locks: "weakref.WeakValueDictionary[int, asyncio.Lock]" = weakref.WeakValueDictionary()
_thread_locks: "weakref.WeakValueDictionary[Tuple[int, int], asyncio.Lock]" = weakref.WeakValueDictionary()


def _lock_for(store: "weakref.WeakValueDictionary", key) -> asyncio.Lock:
    lock = store.get(key)
    if lock is None:
        lock = asyncio.Lock()
        store[key] = lock
    return lock


def _is_own_webhook(wh: discord.Webhook) -> bool:
    return bool(wh.user and bot.user and wh.user.id == bot.user.id)


async def get_webhook(channel: discord.TextChannel, create: bool = True) -> Optional[discord.Webhook]:
    cached = webhook_cache.get(channel.id)
    if cached is not None:
        return cached
    async with _lock_for(_webhook_locks, channel.id):
        cached = webhook_cache.get(channel.id)
        if cached is not None:
            return cached
        for wh in await channel.webhooks():
            if _is_own_webhook(wh) and wh.token:
                webhook_cache[channel.id] = wh
                return wh
        if not create:
            return None
        wh = await channel.create_webhook(name="YATB Bridge")
        webhook_cache[channel.id] = wh
        return wh


async def drop_channel_webhook(channel: discord.abc.GuildChannel):
    """Entfernt die vom Bot angelegten Webhooks eines Kanals (z. B. nach /remove)."""
    webhook_cache.pop(channel.id, None)
    if not isinstance(channel, BRIDGEABLE):
        return
    try:
        for wh in await channel.webhooks():
            if _is_own_webhook(wh):
                await wh.delete(reason="YATB bridge removed")
    except discord.HTTPException:
        pass


async def _send_webhook_chunk(
    channel: discord.TextChannel,
    *,
    content: Optional[str],
    username: str,
    avatar_url: Optional[str],
    thread_id: Optional[int],
    files_data: List[Tuple[bytes, str, Optional[str]]],
    embeds: List[discord.Embed],
    source_message_id: int,
    source_channel_id: int,
    source_parent_id: int,
    guild_id: int,
    chunk_index: int,
    src_hash: str,
):
    kwargs: Dict[str, Any] = {
        "content": content or None,
        "username": username,
        "allowed_mentions": discord.AllowedMentions.none(),
        "wait": True,
    }
    if avatar_url:
        kwargs["avatar_url"] = avatar_url
    if embeds:
        kwargs["embeds"] = embeds
    if thread_id:
        kwargs["thread"] = discord.Object(id=thread_id)

    sent: Optional[discord.WebhookMessage] = None
    for _attempt in range(3):
        webhook = await get_webhook(channel)
        # Dateien müssen bei jedem Versuch neu erzeugt werden (Streams sind nach dem Senden verbraucht)
        files = [discord.File(io.BytesIO(data), filename=name, description=desc) for data, name, desc in files_data]
        try:
            sent = await webhook.send(files=files, **kwargs)
            break
        except discord.NotFound as exc:
            if exc.code == 10015:  # Unknown Webhook -> gelöscht, neu anlegen
                webhook_cache.pop(channel.id, None)
                continue
            raise
        except discord.HTTPException as exc:
            if exc.status == 400 and "username" in str(exc).lower() and kwargs["username"] != FALLBACK_NAME:
                kwargs["username"] = FALLBACK_NAME
                continue
            raise
    if sent is None:
        raise RuntimeError("Webhook-Senden fehlgeschlagen")

    try:
        await db.save_message_mapping(
            source_message_id, source_channel_id, source_parent_id, sent.id,
            channel.id, thread_id, chunk_index, guild_id, src_hash,
        )
    except Exception:
        log.exception("Mapping konnte nicht gespeichert werden")


async def _edit_webhook_message(
    channel: discord.TextChannel, message_id: int, thread_id: Optional[int],
    content: Optional[str], embeds: Optional[List[discord.Embed]] = None,
):
    webhook = await get_webhook(channel, create=False)
    if webhook is None:
        return
    kwargs: Dict[str, Any] = {"content": content}
    if embeds is not None:
        kwargs["embeds"] = embeds
    if thread_id:
        kwargs["thread"] = discord.Object(id=thread_id)
    try:
        await webhook.edit_message(message_id, **kwargs)
    except discord.NotFound:
        pass


async def _delete_webhook_message(channel: discord.TextChannel, message_id: int, thread_id: Optional[int]):
    webhook = await get_webhook(channel, create=False)
    if webhook is None:
        return
    try:
        if thread_id:
            await webhook.delete_message(message_id, thread=discord.Object(id=thread_id))
        else:
            await webhook.delete_message(message_id)
    except discord.NotFound:
        pass


# ----------------- Reporting -----------------
_notice_times: Dict[Any, float] = {}


async def send_report(guild: discord.Guild, message: str, embed: Optional[discord.Embed] = None):
    _, report_ch_id, _ = db.get_guild_config(guild.id)
    if not report_ch_id:
        return
    channel = guild.get_channel(report_ch_id)
    if isinstance(channel, discord.TextChannel):
        try:
            await channel.send(content=message, embed=embed)
        except discord.HTTPException as exc:
            log.warning("Log-Nachricht auf %s fehlgeschlagen: %s", guild.id, exc)


async def notify_once(guild: discord.Guild, key: Any, message: str, interval: float = 6 * 3600):
    """Meldung höchstens einmal pro Intervall (verhindert Spam im Log-Kanal)."""
    full_key = (guild.id, key)
    now = time.monotonic()
    if now - _notice_times.get(full_key, -1e12) < interval:
        return
    _notice_times[full_key] = now
    await send_report(guild, message)


# ----------------- Verbrauch, Limits und Statistik -----------------
def fmt_monthly(ms: limits.MonthlyStatus, provider: providers.Provider, currency: Optional[str] = None) -> str:
    if ms.kind == "cost":
        return f"{ms.used:.2f} / {ms.limit:.2f} {currency or provider.currency}"
    return f"{int(ms.used):,} / {int(ms.limit):,} chars"


def fmt_counts(row: db.UsageRow, provider: Optional[providers.Provider]) -> str:
    if provider is not None and provider.kind == "openai":
        return f"{row.requests} req · {row.tokens_in + row.tokens_out:,} tok"
    return f"{row.chars:,} chars"


async def notify_key_usage(guild: discord.Guild, key: db.KeyRuntime, provider: providers.Provider, crossed: List[str]):
    """Warnstufe an jeden Server melden, der denselben Key nutzt - ohne die anderen Server zu nennen."""
    if not crossed:
        return
    top = crossed[-1]
    guild_ids = (await db.guilds_for_fingerprint(key.fingerprint) if key.key_id else []) or [guild.id]
    for gid in guild_ids:
        target = bot.get_guild(gid)
        if target is None:
            continue
        info = next((i for i in await db.list_api_keys(gid) if i.fingerprint == key.fingerprint), None)
        tier, budget = (info.tier, info.budget) if info else (key.tier, key.budget)
        limit_on = info.limit_enabled if info else key.limit_enabled
        _day, _month, ms = await limits.monthly_status(key.fingerprint, provider, tier, budget)
        desc = _key_desc(info) if info else provider.name
        usage = fmt_monthly(ms, provider, info.currency if info else key.currency) if ms else ""
        loc = target.preferred_locale
        if top == "warn_100":
            text = tx(loc, "usage_full" if limit_on else "usage_full_nolimit", desc=desc, usage=usage)
        else:
            text = tx(loc, "usage_warn", desc=desc, usage=usage, pct=int((ms.ratio if ms else 1.0) * 100))
        await send_report(target, text)


async def handle_notices(guild: discord.Guild, notices: Sequence[chain.Notice]):
    """Meldungen der Übersetzungskette in den Log-Kanal (Duplikate einer Nachricht nur einmal)."""
    seen = set()
    loc = guild.preferred_locale
    for n in notices:
        key = (n.kind, n.provider.id, n.key.key_id if n.key else 0, tuple(n.crossed))
        if key in seen:
            continue
        seen.add(key)
        if n.kind == "usage" and n.key is not None:
            await notify_key_usage(guild, n.key, n.provider, n.crossed)
        elif n.kind == "key_rejected":
            await notify_once(guild, ("key_rejected", n.provider.id),
                              tx(loc, "key_rejected", provider=n.provider.name, status=n.status or "?"))
        elif n.kind == "model_missing":
            await notify_once(guild, ("model_missing", n.provider.id),
                              tx(loc, "model_missing", provider=n.provider.name, model=n.provider.model or "?"))
        elif n.kind == "provider_spend_limit":
            await notify_once(guild, ("provider_spend_limit", n.provider.id),
                              tx(loc, "provider_spend_limit", provider=n.provider.name))
        elif n.kind == "provider_quota":
            await notify_once(guild, ("provider_quota", n.provider.id), tx(loc, "provider_quota", provider=n.provider.name))


# ----------------- Hilfsfunktionen -----------------
def clamp(text: Optional[str], limit: int) -> Optional[str]:
    if text is None:
        return None
    return text if len(text) <= limit else text[: limit - 1] + "…"


_FORBIDDEN_NAME = re.compile(r"(clyde|discord)", re.IGNORECASE)
_HOMOGLYPHS = str.maketrans({"o": "\u043e", "e": "\u0435", "O": "\u041e", "E": "\u0415"})
_TAG_RE = re.compile(r"\s\[(?:AI|Google|Azure|Libre|Raw|Direct|Ollama(?:\+Libre|\+Raw)?)\]$")  # neue + alte Tags


def safe_username(name: str, tag: str) -> str:
    """Webhook-Namen: max. 80 Zeichen, 'discord'/'clyde' sind verboten."""
    name = _FORBIDDEN_NAME.sub(lambda m: m.group(0).translate(_HOMOGLYPHS), name or "").strip() or FALLBACK_NAME
    suffix = f" {tag}" if tag else ""
    return name[: 80 - len(suffix)] + suffix


def make_snippet(text: Optional[str], limit: int = 60) -> str:
    if not text:
        return ""
    lines = [ln for ln in text.splitlines() if not ln.startswith("-# ↩️")]
    snippet = " ".join(" ".join(lines).split())
    snippet = re.sub(r"https?://\S+", "🔗", snippet)  # keine Link-Vorschau im Reply-Kopf
    snippet = discord.utils.escape_markdown(snippet)
    return snippet if len(snippet) <= limit else snippet[: limit - 1] + "…"


def parent_id_of(channel: Any) -> int:
    return channel.parent_id if isinstance(channel, discord.Thread) else channel.id


# Überbrückbare Kanäle: Text-/Ankündigungskanäle und Foren (auch Medien-Kanäle sind ForumChannel)
BRIDGEABLE = (discord.TextChannel, discord.ForumChannel)


def is_forum(channel: Any) -> bool:
    return isinstance(channel, discord.ForumChannel)


# ----------------- Nachrichten-Inhalt (Text, Forwards, Embeds, Sticker) -----------------
@dataclass
class EmbedPlan:
    src: discord.Embed
    title: Optional[int] = None
    description: Optional[int] = None
    footer: Optional[int] = None
    author: Optional[int] = None
    fields: List[Tuple[Optional[int], Optional[int], bool]] = field(default_factory=list)


@dataclass
class Payload:
    segments: List[str]                      # alle zu übersetzenden Texte; [0] ist immer der Haupttext
    forward_idx: List[int] = field(default_factory=list)
    forwarded: bool = False
    embed_plans: List[EmbedPlan] = field(default_factory=list)
    sticker_embeds: List[discord.Embed] = field(default_factory=list)
    sticker_lines: List[str] = field(default_factory=list)
    attachments: List[Any] = field(default_factory=list)

    @property
    def has_content(self) -> bool:
        return bool(
            self.segments[0].strip() or self.forwarded or self.embed_plans
            or self.sticker_embeds or self.sticker_lines or self.attachments
        )

    @property
    def hash(self) -> str:
        return hashlib.sha1("\x1f".join(self.segments).encode()).hexdigest()[:16]


def _add_segment(segments: List[str], text: Optional[str]) -> Optional[int]:
    if text and text.strip():
        segments.append(text)
        return len(segments) - 1
    return None


def build_payload(message: discord.Message) -> Payload:
    segments = [message.content or ""]
    payload = Payload(segments=segments)
    attachments = list(message.attachments)
    stickers = list(message.stickers)
    embeds = [e for e in message.embeds if e.type == "rich"]  # Link-Vorschauen erzeugt Discord selbst neu

    snapshots = getattr(message, "message_snapshots", None) or []
    for snap in snapshots:
        snap_msg = getattr(snap, "message", snap)
        payload.forwarded = True
        idx = _add_segment(segments, getattr(snap_msg, "content", "") or "")
        if idx is not None:
            payload.forward_idx.append(idx)
        attachments += list(getattr(snap_msg, "attachments", None) or [])
        stickers += list(getattr(snap_msg, "stickers", None) or [])
        embeds += [e for e in (getattr(snap_msg, "embeds", None) or []) if e.type == "rich"]

    for st in stickers[:3]:
        fmt = getattr(st, "format", None)
        if fmt is discord.StickerFormatType.lottie:  # Lottie lässt sich nicht als Bild darstellen
            payload.sticker_lines.append(f"🏷️ {st.name}")
        else:
            emb = discord.Embed()
            emb.set_image(url=st.url)
            payload.sticker_embeds.append(emb)

    for emb in embeds[:10]:
        plan = EmbedPlan(
            src=emb,
            title=_add_segment(segments, emb.title),
            description=_add_segment(segments, emb.description),
            footer=_add_segment(segments, emb.footer.text),
            author=_add_segment(segments, emb.author.name),
        )
        for fld in emb.fields:
            plan.fields.append((_add_segment(segments, fld.name), _add_segment(segments, fld.value), bool(fld.inline)))
        payload.embed_plans.append(plan)

    payload.attachments = attachments
    return payload


def build_embeds(plans: List[EmbedPlan], texts: List[str]) -> List[discord.Embed]:
    def get(idx: Optional[int]) -> Optional[str]:
        return texts[idx] if idx is not None and idx < len(texts) and texts[idx].strip() else None

    out: List[discord.Embed] = []
    for plan in plans:
        src = plan.src
        # Optionale Werte nur übergeben, wenn sie gesetzt sind - nie None (versionsunabhängig sicher)
        emb_kwargs: Dict[str, Any] = {}
        for key, value in (
            ("title", clamp(get(plan.title), 256)),
            ("description", clamp(get(plan.description), 4096)),
            ("url", src.url),
            ("colour", src.colour),
            ("timestamp", src.timestamp),
        ):
            if value:
                emb_kwargs[key] = value
        emb = discord.Embed(**emb_kwargs)
        if get(plan.author):
            author_kwargs = {k: v for k, v in (("url", src.author.url), ("icon_url", src.author.icon_url)) if v}
            emb.set_author(name=clamp(get(plan.author), 256), **author_kwargs)
        if src.image.url:
            emb.set_image(url=src.image.url)
        if src.thumbnail.url:
            emb.set_thumbnail(url=src.thumbnail.url)
        if get(plan.footer):
            footer_kwargs = {"icon_url": src.footer.icon_url} if src.footer.icon_url else {}
            emb.set_footer(text=clamp(get(plan.footer), 2048), **footer_kwargs)
        for name_idx, value_idx, inline in plan.fields[:25]:
            name, value = get(name_idx), get(value_idx)
            if name and value:
                emb.add_field(name=clamp(name, 256), value=clamp(value, 1024), inline=inline)
        if emb.title or emb.description or emb.fields or src.image.url or src.thumbnail.url:
            out.append(emb)
    return out


def fit_embeds(embeds: List[discord.Embed]) -> List[discord.Embed]:
    """Discord: max. 10 Embeds und insgesamt 6000 Zeichen pro Nachricht."""
    out: List[discord.Embed] = []
    total = 0
    for emb in embeds[:10]:
        while len(emb) > 6000 and emb.fields:
            emb.remove_field(len(emb.fields) - 1)
        if total + len(emb) > 6000:
            break
        total += len(emb)
        out.append(emb)
    return out


def render_content(payload: Payload, texts: List[str], label: str, extra_lines: List[str]) -> str:
    parts: List[str] = []
    body = texts[0].strip("\n") if texts else ""
    if body.strip():
        parts.append(body)
    if payload.forwarded:
        fwd = [texts[i] for i in payload.forward_idx if i < len(texts) and texts[i].strip()]
        quoted = "\n".join("> " + ln for t in fwd for ln in t.splitlines())
        parts.append(f"↪️ **{label}:**\n{quoted}" if quoted else f"↪️ **{label}**")
    parts.extend(payload.sticker_lines)
    parts.extend(extra_lines)
    return "\n\n".join(parts)


# ----------------- Antworten (Replies) -----------------
@dataclass
class ReplyCtx:
    name: str
    origin_id: int          # ID der Original-Nachricht (nicht der gespiegelten)
    origin_loc: int         # Kanal/Thread, in dem die Original-Nachricht liegt
    origin_parent: int      # Eltern-Textkanal der Original-Nachricht
    raw_snippet: str


async def resolve_reply_ctx(message: discord.Message) -> Optional[ReplyCtx]:
    ref = message.reference
    if ref is None or ref.message_id is None or message.type != discord.MessageType.reply:
        return None  # Crossposts/Forwards tragen ebenfalls eine Referenz, sind aber keine Antworten
    rtype = getattr(ref, "type", None)
    if rtype is not None and getattr(rtype, "name", "") == "forward":
        return None  # Forwards werden über message_snapshots behandelt (normale Antworten: Typ "default")

    ref_msg = ref.resolved if isinstance(ref.resolved, discord.Message) else None
    if ref_msg is None:
        channel = message.guild.get_channel_or_thread(ref.channel_id) if ref.channel_id else None
        channel = channel or message.channel
        try:
            ref_msg = await channel.fetch_message(ref.message_id)
        except discord.HTTPException:
            return None  # gelöscht oder nicht lesbar

    origin = None
    if ref_msg.webhook_id is not None:
        origin = await db.find_origin(ref_msg.id)
        name = _TAG_RE.sub("", ref_msg.author.name)
    else:
        name = ref_msg.author.display_name
    if origin:
        o_id, o_loc, o_parent = origin
    else:
        o_id, o_loc, o_parent = ref_msg.id, ref_msg.channel.id, parent_id_of(ref_msg.channel)

    snippet = make_snippet(ref_msg.content) or ("🖼️" if (ref_msg.attachments or ref_msg.stickers) else "")
    return ReplyCtx(name=name, origin_id=o_id, origin_loc=o_loc, origin_parent=o_parent, raw_snippet=snippet)


async def build_reply_header(guild: discord.Guild, ctx: Optional[ReplyCtx], target_parent_id: int) -> str:
    """Kopfzeile '↩️ Name: Auszug' - verlinkt auf die Nachricht im Ziel-Kanal, falls sie dort existiert."""
    if ctx is None:
        return ""
    msg_id = loc_id = None
    if ctx.origin_parent == target_parent_id:
        msg_id, loc_id = ctx.origin_id, ctx.origin_loc      # Original liegt bereits im Ziel-Kanal
    else:
        mirror = await db.find_mirror(ctx.origin_id, target_parent_id)
        if mirror:
            msg_id, loc_id = mirror

    snippet = ctx.raw_snippet
    if msg_id:
        location = guild.get_channel_or_thread(loc_id)
        if location is not None:
            try:  # Auszug aus der Nachricht im Ziel-Kanal = bereits in Zielsprache
                fetched = await location.fetch_message(msg_id)
                snippet = make_snippet(fetched.content) or snippet
            except discord.HTTPException:
                pass

    name = discord.utils.escape_markdown(ctx.name).replace("[", "(").replace("]", ")")
    who = f"[{name}](https://discord.com/channels/{guild.id}/{loc_id}/{msg_id})" if msg_id else name
    line = f"-# ↩️ **{who}**" + (f": {snippet}" if snippet else "")
    return clamp(line, 300) or ""


# ----------------- Anhänge -----------------
async def download_attachments(
    guild: discord.Guild, attachments: List[Any]
) -> Tuple[List[Tuple[bytes, str, Optional[str]]], List[str]]:
    """Lädt Anhänge herunter. Zu große oder überzählige werden als Link angehängt."""
    limit = min(getattr(guild, "filesize_limit", 10 * 1024 * 1024), MAX_FILE_BYTES)

    def link(att) -> str:
        return f"📎 [{att.filename.replace('[', '(').replace(']', ')')}]({att.url})"

    todo, extra, total = [], [], 0
    for att in attachments:
        if len(todo) >= 10 or att.size > limit or total + att.size > limit:
            extra.append(link(att))
            continue
        total += att.size
        todo.append(att)

    results = await asyncio.gather(*(att.read() for att in todo), return_exceptions=True)
    files: List[Tuple[bytes, str, Optional[str]]] = []
    for att, res in zip(todo, results):
        if isinstance(res, Exception):
            log.warning("Anhang konnte nicht geladen werden (%s): %s", att.filename, type(res).__name__)
            extra.append(link(att))
        else:
            files.append((res, att.filename, getattr(att, "description", None)))
    return files, extra


# ----------------- Übersetzung für mehrere Zielsprachen -----------------
async def translate_for_langs(
    guild: discord.Guild, source_lang: str, langs: List[str], segments: List[str],
    context: Optional[List[str]] = None, local_only: bool = False,
) -> Dict[str, chain.TranslationResult]:
    """Übersetzt einmal pro Zielsprache (nicht pro Kanal) über die Kette des Servers und meldet Key-Probleme.
    local_only: Opt-out des Verfassers - nur Libre, nichts an Dritte, kein Kontext."""
    outs = await asyncio.gather(*(
        chain.translate(http_session, guild.id, segments, source_lang, lang, None if local_only else context, local_only)
        for lang in langs
    ))
    await handle_notices(guild, [n for r in outs for n in r.notices])
    return dict(zip(langs, outs))


# ----------------- Threads -----------------
async def fetch_thread(guild: discord.Guild, thread_id: int) -> Optional[discord.Thread]:
    """Holt einen Thread (auch wenn archiviert/nicht im Cache) und entarchiviert ihn bei Bedarf."""
    thread = guild.get_thread(thread_id)
    if thread is None:
        try:
            fetched = await guild.fetch_channel(thread_id)
        except (discord.NotFound, discord.Forbidden):
            return None
        thread = fetched if isinstance(fetched, discord.Thread) else None
    if thread is not None and thread.archived and not thread.locked:
        try:
            await thread.edit(archived=False)
        except discord.HTTPException:
            pass
    return thread


async def ensure_target_thread(
    guild: discord.Guild,
    source_thread: discord.Thread,
    group_id: int,
    target_channel: discord.TextChannel,
    bridge_id: str,
    translate_title: Callable[[], Awaitable[str]],
) -> int:
    """Liefert die ID des Spiegel-Threads im Ziel-Kanal; legt ihn (genau einmal) an, falls er fehlt."""
    async with _lock_for(_thread_locks, (group_id, target_channel.id)):
        existing = await db.lookup_target_thread(source_thread.id, target_channel.id)
        if existing:
            if await fetch_thread(guild, existing) is not None:
                return existing
            await db.delete_thread_link(existing)  # Thread wurde gelöscht -> neu anlegen

        title = (await translate_title()).strip()[:100] or "Thread"
        ttype = discord.ChannelType.news_thread if target_channel.is_news() else discord.ChannelType.public_thread
        created = await target_channel.create_thread(name=title, type=ttype)
        await db.register_thread(created.id, target_channel.id, group_id, guild.id, bridge_id)
        return created.id


# ----------------- Foren (und Medien-Kanäle): Beiträge und Tags -----------------
# Ein Beitrag wird im Ziel-Forum per Webhook angelegt (Titel, Tags, erster Teil des Starters), Antworten laufen über
# die normale Thread-Spiegelung. Tags werden 1:1 zugeordnet: gespeicherte Zuordnung, gleicher Name - oder YATB legt
# das Gegenstück an (übersetzter Name, gleiches Emoji; braucht "Kanäle verwalten" im Ziel-Forum).
MAX_FORUM_TAGS = 20       # Discord: höchstens 20 Tags pro Forum
MAX_POST_TAGS = 5         # Discord: höchstens 5 Tags pro Beitrag
_tag_locks: "weakref.WeakValueDictionary[int, asyncio.Lock]" = weakref.WeakValueDictionary()


async def _translate_short(guild_id: int, text: str, source_lang: str, target_lang: str) -> str:
    if source_lang == target_lang:
        return text
    res = await chain.translate(http_session, guild_id, [text], source_lang, target_lang)
    return (res.texts[0] or text).strip()


async def map_forum_tag(guild: discord.Guild, source_forum: discord.ForumChannel, tag: discord.ForumTag,
                        target_forum: discord.ForumChannel, source_lang: str, target_lang: str) -> Optional[discord.ForumTag]:
    """Gegenstück eines Tags im Ziel-Forum (gespeichert, gleicher Name oder neu angelegt) oder None."""
    async with _lock_for(_tag_locks, target_forum.id):
        linked = await db.get_tag_link(source_forum.id, tag.id, target_forum.id)
        if linked and (found := target_forum.get_tag(linked)) is not None:
            return found
        name = (await _translate_short(guild.id, tag.name, source_lang, target_lang))[:20].strip() or tag.name[:20]
        wanted = {name.casefold(), tag.name.casefold()}
        match = next((t for t in target_forum.available_tags if t.name.casefold() in wanted), None)
        if match is None:
            loc = guild.preferred_locale
            if not target_forum.permissions_for(guild.me).manage_channels:
                await notify_once(guild, ("tags_perm", target_forum.id),
                                  tx(loc, "rep_tags_no_permission", channel=target_forum.mention))
                return None
            if len(target_forum.available_tags) >= MAX_FORUM_TAGS:
                await notify_once(guild, ("tags_full", target_forum.id), tx(loc, "rep_tags_full", channel=target_forum.mention))
                return None
            try:
                match = await target_forum.create_tag(name=name, emoji=tag.emoji, moderated=tag.moderated,
                                                      reason="YATB: Tag aus einem verbundenen Forum")
            except discord.HTTPException as exc:
                log.warning("Tag in Forum %s nicht angelegt: %s", target_forum.id, exc)
                return None
        await db.save_tag_link(guild.id, source_forum.id, tag.id, target_forum.id, match.id)
        return match


async def map_forum_tags(guild: discord.Guild, source_forum: Any, tags: Sequence[discord.ForumTag],
                         target_forum: discord.ForumChannel, source_lang: str, target_lang: str) -> List[discord.ForumTag]:
    out: List[discord.ForumTag] = []
    if not is_forum(source_forum):
        return out
    for tag in list(tags)[:MAX_POST_TAGS]:
        found = await map_forum_tag(guild, source_forum, tag, target_forum, source_lang, target_lang)
        if found is not None and all(t.id != found.id for t in out):
            out.append(found)
    return out


async def sync_forum_tags(guild: discord.Guild, forum: discord.ForumChannel, bridge_id: str, lang: str):
    """Neues Forum in einer Bridge: alle Tags in beide Richtungen abgleichen (Fehlendes wird angelegt)."""
    try:
        for target_id, target_lang in db.get_bridge_targets(guild.id, bridge_id, forum.id):
            other = guild.get_channel(target_id)
            if not is_forum(other):
                continue
            target_lang = tr.normalize_lang(target_lang)
            for tag in list(forum.available_tags):
                await map_forum_tag(guild, forum, tag, other, lang, target_lang)
            for tag in list(other.available_tags):
                await map_forum_tag(guild, other, tag, forum, target_lang, lang)
    except Exception:
        log.exception("Tag-Abgleich für Forum %s fehlgeschlagen", forum.id)


async def create_forum_post(forum: discord.ForumChannel, *, title: str, tags: List[discord.ForumTag], content: str,
                            username: str, avatar_url: Optional[str], files_data: List[Tuple[bytes, str, Optional[str]]],
                            embeds: List[discord.Embed]) -> discord.WebhookMessage:
    if not tags and forum.flags.require_tag and forum.available_tags:
        tags = [forum.available_tags[0]]   # Forum verlangt einen Tag, keiner zugeordnet -> erster verfügbarer
    kwargs: Dict[str, Any] = {"content": content or None, "username": username, "wait": True,
                              "allowed_mentions": discord.AllowedMentions.none(), "thread_name": title[:100] or "Post"}
    if tags:
        kwargs["applied_tags"] = tags
    if avatar_url:
        kwargs["avatar_url"] = avatar_url
    if embeds:
        kwargs["embeds"] = embeds
    for _attempt in range(3):
        webhook = await get_webhook(forum)
        files = [discord.File(io.BytesIO(data), filename=name, description=desc) for data, name, desc in files_data]
        try:
            return await webhook.send(files=files, **kwargs)
        except discord.NotFound as exc:
            if exc.code == 10015:
                webhook_cache.pop(forum.id, None)
                continue
            raise
        except discord.HTTPException as exc:
            if exc.status == 400 and "username" in str(exc).lower() and kwargs["username"] != FALLBACK_NAME:
                kwargs["username"] = FALLBACK_NAME
                continue
            raise
    raise RuntimeError("Forenbeitrag konnte nicht angelegt werden")


async def ensure_forum_post(
    guild: discord.Guild, message: discord.Message, source_thread: discord.Thread, group_id: int,
    forum: discord.ForumChannel, bridge_id: str, source_lang: str, lang: str,
    translate_title: Callable[[], Awaitable[str]], chunks: List[str], files_data, embeds: List[discord.Embed],
    username: str, avatar_url: Optional[str], src_hash: str, parent_id: int,
) -> Tuple[int, int]:
    """(Thread-ID des Spiegel-Beitrags, Anzahl schon gesendeter Teile). Der Starter legt den Beitrag selbst an."""
    async with _lock_for(_thread_locks, (group_id, forum.id)):
        existing = await db.lookup_target_thread(source_thread.id, forum.id)
        if existing:
            if await fetch_thread(guild, existing) is not None:
                return existing, 0
            await db.delete_thread_link(existing)
        title = (await translate_title()).strip()[:100] or "Post"
        tags = await map_forum_tags(guild, source_thread.parent, source_thread.applied_tags, forum, source_lang, lang)
        starter = message.id == source_thread.id
        if starter:
            single = len(chunks) == 1
            sent = await create_forum_post(
                forum, title=title, tags=tags, content=chunks[0], username=username, avatar_url=avatar_url,
                files_data=files_data if (single or forum.is_media()) else [], embeds=embeds if single else [])
        else:  # Antwort in einem Beitrag ohne Spiegel (z. B. älter als die Bridge): Beitrag mit Verweis anlegen
            sent = await create_forum_post(
                forum, title=title, tags=tags, content=f"🔗 https://discord.com/channels/{guild.id}/{source_thread.id}",
                username="YATB", avatar_url=None, files_data=[], embeds=[])
        thread_id = sent.channel.id
        await db.register_thread(thread_id, forum.id, group_id, guild.id, bridge_id)
        if not starter:
            return thread_id, 0
        await db.save_message_mapping(message.id, message.channel.id, parent_id, sent.id, forum.id, thread_id, 0,
                                      guild.id, src_hash)
        return thread_id, 1


# ----------------- Nachrichtenverteilung -----------------
@bot.event
async def on_message(message: discord.Message):
    if message.guild is None:
        return
    # Gefolgte Ankündigungskanäle anderer Server liefern ihre Beiträge als Webhook-Nachricht
    # mit dem Flag "is_crossposted". Die Webhooks dieses Bots tragen dieses Flag nie -> keine Schleifen.
    is_crosspost = message.webhook_id is not None and bool(getattr(message.flags, "is_crossposted", False))
    if message.webhook_id is not None and not is_crosspost:
        return
    if not is_crosspost and message.author.bot and not (BRIDGE_BOTS and bot.user and message.author.id != bot.user.id):
        return
    if message.type not in (discord.MessageType.default, discord.MessageType.reply):
        return

    channel = message.channel
    if isinstance(channel, discord.Thread):
        if channel.type not in (discord.ChannelType.public_thread, discord.ChannelType.news_thread):
            return  # private Threads werden nie überbrückt
    parent_id = parent_id_of(channel)

    info = db.get_bridge_channel_info(parent_id)
    if info is None:
        return
    guild_id, bridge_id, source_lang = info
    targets = db.get_bridge_targets(guild_id, bridge_id, parent_id)
    if not targets:
        return

    prev, mine = gate.ticket(channel.id)  # synchron, vor dem ersten await -> Reihenfolge bleibt erhalten
    try:
        await _bridge_message(message, parent_id, guild_id, bridge_id, tr.normalize_lang(source_lang), targets, prev)
    except Exception:
        log.exception("Fehler beim Überbrücken von Nachricht %s", message.id)
    finally:
        gate.release(channel.id, mine)


async def _bridge_message(
    message: discord.Message, parent_id: int, guild_id: int, bridge_id: str,
    source_lang: str, targets: List[Tuple[int, str]], prev: Optional[asyncio.Future],
):
    guild = message.guild
    payload = build_payload(message)
    if not payload.has_content:
        return

    langs = sorted({tr.normalize_lang(lang) for _, lang in targets})

    source_thread: Optional[discord.Thread] = message.channel if isinstance(message.channel, discord.Thread) else None
    group_id = 0
    if source_thread is not None:
        link = await db.get_thread_link(source_thread.id)
        if link:
            group_id = link[0]
        else:
            group_id = source_thread.id
            await db.register_thread(source_thread.id, parent_id, group_id, guild_id, bridge_id)

    # Kontext für die KI: frühere Nachrichten desselben Verfassers in dieser Bridge (ohne die aktuelle)
    ctx_key = (guild_id, bridge_id, group_id)
    local_only = db.is_local_only(message.author.id)  # Opt-out des Verfassers: nur lokal (Libre)
    context = context_buffer.recent(ctx_key, message.id, message.author.id)
    if payload.segments[0].strip():
        snippet = " ".join(payload.segments[0].split())[:220]
        context_buffer.add(ctx_key, message.id, f"{message.author.display_name}: {snippet}", message.author.id)

    (files_data, extra_lines), results, reply_ctx = await asyncio.gather(
        download_attachments(guild, payload.attachments),
        translate_for_langs(guild, source_lang, langs, payload.segments, context, local_only),
        resolve_reply_ctx(message),
    )

    title_notices: List[chain.Notice] = []
    avatar_url = message.author.display_avatar.url if message.author.display_avatar else None
    author_name = message.author.display_name

    source_is_forum = is_forum(guild.get_channel(parent_id))

    async def post(target_id: int, target_lang: str):
        target_channel = guild.get_channel(target_id)
        if not isinstance(target_channel, BRIDGEABLE) or is_forum(target_channel) != source_is_forum:
            return  # Foren nur mit Foren
        lang = tr.normalize_lang(target_lang)
        res = results[lang]
        try:
            await get_webhook(target_channel)  # früh prüfen (Rechte), Ergebnis wird gecacht

            async def translate_title() -> str:
                r = await chain.translate(http_session, guild_id, [source_thread.name or "Thread"], source_lang, lang,
                                          local_only=local_only)
                title_notices.extend(r.notices)
                return r.texts[0]

            thread_id: Optional[int] = None
            if source_thread is not None and not is_forum(target_channel):
                thread_id = await ensure_target_thread(
                    guild, source_thread, group_id, target_channel, bridge_id, translate_title
                )

            header = await build_reply_header(guild, reply_ctx, target_id)
            content = render_content(payload, res.texts, FORWARD_LABEL.get(lang, "Forwarded"), extra_lines)
            embeds = fit_embeds(payload.sticker_embeds + build_embeds(payload.embed_plans, res.texts))
            chunks = tr.split_message(content, 1950 - (len(header) + 1 if header else 0))
            if not chunks:
                chunks = [""]
            if header:
                chunks[0] = f"{header}\n{chunks[0]}" if chunks[0] else header
            if chunks == [""] and not files_data and not embeds:
                return

            username = safe_username(author_name, res.main_engine)
            last = len(chunks) - 1
            sent_parts, rest_files = 0, files_data
            if source_thread is not None and is_forum(target_channel):
                await wait_for_turn(prev)  # Starter vor Antworten: der Beitrag muss zuerst stehen
                thread_id, sent_parts = await ensure_forum_post(
                    guild, message, source_thread, group_id, target_channel, bridge_id, source_lang, lang,
                    translate_title, chunks, files_data, embeds, username, avatar_url, payload.hash, parent_id)
                if sent_parts and (last == 0 or target_channel.is_media()):
                    rest_files = []   # Dateien hingen schon am Beitrag
            await wait_for_turn(prev)  # erst jetzt einreihen -> Reihenfolge des Originals bleibt erhalten
            for idx, chunk in enumerate(chunks):
                if idx < sent_parts:
                    continue
                webhook_dispatcher.dispatch(
                    target_id, _send_webhook_chunk, target_channel,
                    content=chunk, username=username, avatar_url=avatar_url, thread_id=thread_id,
                    files_data=rest_files if idx == last else [],
                    embeds=embeds if idx == last else [],
                    source_message_id=message.id, source_channel_id=message.channel.id,
                    source_parent_id=parent_id, guild_id=guild_id, chunk_index=idx, src_hash=payload.hash,
                )
        except discord.Forbidden:
            await notify_once(
                guild, ("forbidden", target_id),
                tx(guild.preferred_locale, "send_forbidden", channel=f"<#{target_id}>"), 3600,
            )

    outcomes = await asyncio.gather(*(post(t_id, t_lang) for t_id, t_lang in targets), return_exceptions=True)
    for outcome in outcomes:
        if isinstance(outcome, Exception):
            log.error("Zustellung fehlgeschlagen: %r", outcome)

    if title_notices:
        await handle_notices(guild, title_notices)


# ----------------- Edit & Delete (Raw-Events: funktionieren auch für nicht gecachte Nachrichten) -----------------
@bot.event
async def on_raw_message_edit(payload: discord.RawMessageUpdateEvent):
    if payload.guild_id is None or not (payload.data or {}).get("edited_timestamp"):
        return  # Link-Vorschau-Updates und Ähnliches haben keinen edited_timestamp
    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    channel = guild.get_channel_or_thread(payload.channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(payload.channel_id)
        except discord.HTTPException:
            return
    parent_id = parent_id_of(channel)
    if not db.is_bridged(parent_id):
        return
    mappings = await db.get_message_mappings(payload.message_id)
    if not mappings:
        return
    try:
        message = await channel.fetch_message(payload.message_id)
    except discord.HTTPException:
        return
    try:
        await _apply_edit(message, parent_id, mappings)
    except Exception:
        log.exception("Fehler beim Synchronisieren des Edits %s", payload.message_id)


async def _apply_edit(message: discord.Message, parent_id: int, mappings: List[Tuple]):
    info = db.get_bridge_channel_info(parent_id)
    if info is None:
        return
    guild = message.guild
    guild_id, bridge_id, source_lang = info
    source_lang = tr.normalize_lang(source_lang)

    payload = build_payload(message)
    if mappings[0][4] == payload.hash:
        return  # inhaltlich unverändert

    by_target: Dict[int, List[Tuple]] = {}
    for row in mappings:
        by_target.setdefault(row[1], []).append(row)

    target_langs = {
        t_id: tr.normalize_lang(t_info[2])
        for t_id in by_target if (t_info := db.get_bridge_channel_info(t_id))
    }
    if not target_langs:
        return

    context = context_buffer.recent(await context_key(message, guild_id, bridge_id), message.id, message.author.id)
    results = await translate_for_langs(
        guild, source_lang, sorted(set(target_langs.values())), payload.segments, context,
        db.is_local_only(message.author.id),
    )
    reply_ctx = await resolve_reply_ctx(message)
    avatar_url = message.author.display_avatar.url if message.author.display_avatar else None

    for target_id, rows in by_target.items():
        target_channel = guild.get_channel(target_id)
        if not isinstance(target_channel, BRIDGEABLE) or target_id not in target_langs:
            continue
        lang = target_langs[target_id]
        res = results[lang]
        rows.sort(key=lambda r: r[3])
        thread_id = rows[0][2]

        header = await build_reply_header(guild, reply_ctx, target_id)
        content = render_content(payload, res.texts, FORWARD_LABEL.get(lang, "Forwarded"), [])
        chunks = tr.split_message(content, 1950 - (len(header) + 1 if header else 0)) or [""]
        if header:
            chunks[0] = f"{header}\n{chunks[0]}" if chunks[0] else header
        embeds = fit_embeds(payload.sticker_embeds + build_embeds(payload.embed_plans, res.texts)) if payload.embed_plans else None

        existing = [(r[0], r[3]) for r in rows]
        last = len(chunks) - 1
        for idx, chunk in enumerate(chunks):
            if idx < len(existing):
                webhook_dispatcher.dispatch(
                    target_id, _edit_webhook_message, target_channel, existing[idx][0], thread_id,
                    chunk or None, embeds if idx == last else None,
                )
            else:  # Text ist länger geworden -> zusätzliche Nachricht
                webhook_dispatcher.dispatch(
                    target_id, _send_webhook_chunk, target_channel,
                    content=chunk, username=safe_username(message.author.display_name, res.main_engine),
                    avatar_url=avatar_url, thread_id=thread_id, files_data=[],
                    embeds=(embeds or []) if idx == last else [],
                    source_message_id=message.id, source_channel_id=message.channel.id,
                    source_parent_id=parent_id, guild_id=guild_id, chunk_index=idx, src_hash=payload.hash,
                )
        surplus = existing[len(chunks):]
        for msg_id, _chunk_idx in surplus:  # Text ist kürzer geworden -> überzählige Nachrichten löschen
            webhook_dispatcher.dispatch(target_id, _delete_webhook_message, target_channel, msg_id, thread_id)
        await db.delete_mapping_rows(message.id, [msg_id for msg_id, _ in surplus])

    await db.update_mapping_hash(message.id, payload.hash)


async def _handle_deleted(guild_id: Optional[int], channel_id: int, message_ids: List[int]):
    if guild_id is None:
        return
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    channel = guild.get_channel_or_thread(channel_id)
    if channel is not None and not db.is_bridged(parent_id_of(channel)):
        return
    for message_id in message_ids:
        mappings = await db.get_message_mappings(message_id)
        if not mappings:
            continue
        for target_message_id, target_id, thread_id, _chunk, _hash in mappings:
            target_channel = guild.get_channel(target_id)
            if isinstance(target_channel, BRIDGEABLE):
                webhook_dispatcher.dispatch(
                    target_id, _delete_webhook_message, target_channel, target_message_id, thread_id
                )
        await db.delete_message_mappings(message_id)


@bot.event
async def on_raw_message_delete(payload: discord.RawMessageDeleteEvent):
    await _handle_deleted(payload.guild_id, payload.channel_id, [payload.message_id])


@bot.event
async def on_raw_bulk_message_delete(payload: discord.RawBulkMessageDeleteEvent):
    await _handle_deleted(payload.guild_id, payload.channel_id, list(payload.message_ids))


# ----------------- Beiträge/Threads: Titel, Tags, geschlossen, gesperrt -----------------
@bot.event
async def on_thread_update(before: discord.Thread, after: discord.Thread):
    """Nur das Original gibt Änderungen weiter (Spiegel nicht) - so entstehen keine Schleifen."""
    if after.guild is None or not db.is_bridged(after.parent_id):
        return
    renamed = before.name != after.name
    retagged = {t.id for t in before.applied_tags} != {t.id for t in after.applied_tags}
    state = before.archived != after.archived or before.locked != after.locked
    if not (renamed or retagged or state):
        return
    link = await db.get_thread_link(after.id)
    info = db.get_bridge_channel_info(after.parent_id)
    if not link or link[0] != after.id or info is None:
        return
    guild, source_lang = after.guild, tr.normalize_lang(info[2])
    for thread_id, parent_id in await db.group_threads(after.id):
        target_info = db.get_bridge_channel_info(parent_id)
        if thread_id == after.id or target_info is None:
            continue
        mirror = guild.get_thread(thread_id)
        if mirror is None:
            try:
                mirror = await guild.fetch_channel(thread_id)
            except discord.HTTPException:
                continue
        lang = tr.normalize_lang(target_info[2])
        kwargs: Dict[str, Any] = {}
        if renamed:
            kwargs["name"] = (await _translate_short(guild.id, after.name, source_lang, lang))[:100] or after.name
        if retagged and is_forum(mirror.parent):
            kwargs["applied_tags"] = await map_forum_tags(guild, after.parent, after.applied_tags, mirror.parent,
                                                          source_lang, lang)
        if state:
            kwargs["archived"], kwargs["locked"] = after.archived, after.locked
        try:
            if mirror.archived and ("name" in kwargs or "applied_tags" in kwargs):
                await mirror.edit(archived=False)          # geschlossene Spiegel erst öffnen, dann ändern
                kwargs.setdefault("archived", after.archived)
            if kwargs:
                await mirror.edit(**kwargs)
        except discord.HTTPException as exc:
            log.warning("Spiegel-Thread %s nicht aktualisiert: %s", thread_id, exc)


# ----------------- Reaktionen spiegeln -----------------
# Discord erlaubt keine Reaktion "im Namen" eines Nutzers: YATB setzt dasselbe Emoji einmal auf alle anderen Fassungen
# (Original + Übersetzungen) und nimmt es wieder weg, sobald in keinem Kanal mehr ein Mensch so reagiert hat.
# Zuordnung über message_mappings (7 Tage); bei aufgeteilten Übersetzungen zählt der erste Teil.
_reaction_locks: "weakref.WeakValueDictionary[int, asyncio.Lock]" = weakref.WeakValueDictionary()


async def reaction_copies(channel_id: int, message_id: int) -> List[Tuple[int, int]]:
    """Alle Fassungen einer gespiegelten Nachricht als [(ort_id, nachricht_id), ...], Original zuerst; sonst []."""
    origin = await db.find_origin(message_id)
    source_id, source_place = (origin[0], origin[1]) if origin else (message_id, channel_id)
    rows = await db.get_message_mappings(source_id)
    if not rows:
        return []
    copies, seen = [(source_place, source_id)], set()
    for target_id, target_channel, target_thread, chunk, _hash in rows:
        if chunk == 0 and target_channel not in seen:
            seen.add(target_channel)
            copies.append((target_thread or target_channel, target_id))
    return copies


def _reaction_relevant(payload) -> bool:
    """Nur Server, nur Bridge-Kanäle (oder deren Threads), nie die eigenen Reaktionen des Bots."""
    if payload.guild_id is None or (bot.user is not None and getattr(payload, "user_id", None) == bot.user.id):
        return False
    member = getattr(payload, "member", None)
    if member is not None and member.bot and not BRIDGE_BOTS:  # andere Bots (Umfragen, Rollen-Menüs) nicht spiegeln
        return False
    guild = bot.get_guild(payload.guild_id)
    place = guild.get_channel_or_thread(payload.channel_id) if guild else None
    parent_id = getattr(place, "parent_id", None) if isinstance(place, discord.Thread) else None
    return db.is_bridged(payload.channel_id) or (parent_id is not None and db.is_bridged(parent_id))


def _usable_emoji(emoji: discord.PartialEmoji) -> bool:
    """Unicode-Emojis immer; eigene Emojis nur, wenn der Bot sie kennt (Server, auf denen er ist)."""
    return emoji.id is None or bot.get_emoji(emoji.id) is not None


async def _partial_message(guild: discord.Guild, place_id: int, message_id: int) -> Optional[discord.PartialMessage]:
    place = guild.get_channel_or_thread(place_id) or await fetch_thread(guild, place_id)
    return place.get_partial_message(message_id) if place is not None else None


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if not _reaction_relevant(payload) or not _usable_emoji(payload.emoji):
        return
    copies = await reaction_copies(payload.channel_id, payload.message_id)
    guild = bot.get_guild(payload.guild_id)
    if not copies or guild is None:
        return
    async with _lock_for(_reaction_locks, copies[0][1]):
        for place_id, message_id in copies:
            if message_id == payload.message_id:
                continue
            partial = await _partial_message(guild, place_id, message_id)
            if partial is None:
                continue
            try:
                await partial.add_reaction(payload.emoji)
            except discord.HTTPException as exc:  # gelöscht, 20 Reaktionen voll, Recht fehlt
                log.debug("Reaktion auf %s nicht gespiegelt: %s", message_id, exc)


async def _recheck_reaction(guild_id: int, channel_id: int, message_id: int, emoji: discord.PartialEmoji):
    """Nach dem Entfernen: hat irgendwo noch ein Mensch so reagiert? Wenn nein, eigene Spiegel-Reaktionen weg."""
    copies = await reaction_copies(channel_id, message_id)
    guild = bot.get_guild(guild_id)
    if not copies or guild is None or bot.user is None:
        return
    async with _lock_for(_reaction_locks, copies[0][1]):
        humans, mine = 0, []
        for place_id, msg_id in copies:
            partial = await _partial_message(guild, place_id, msg_id)
            try:
                msg = await partial.fetch() if partial is not None else None
            except discord.HTTPException:
                msg = None
            reaction = next((r for r in msg.reactions if str(r.emoji) == str(emoji)), None) if msg else None
            if reaction is None:
                continue
            humans += reaction.count - (1 if reaction.me else 0)
            if reaction.me:
                mine.append(msg)
        if humans > 0:
            return
        for msg in mine:
            try:
                await msg.remove_reaction(emoji, bot.user)
            except discord.HTTPException as exc:
                log.debug("Spiegel-Reaktion auf %s nicht entfernt: %s", msg.id, exc)


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if _reaction_relevant(payload):
        await _recheck_reaction(payload.guild_id, payload.channel_id, payload.message_id, payload.emoji)


@bot.event
async def on_raw_reaction_clear_emoji(payload: discord.RawReactionClearEmojiEvent):
    if _reaction_relevant(payload):  # Moderator hat ein Emoji ganz entfernt
        await _recheck_reaction(payload.guild_id, payload.channel_id, payload.message_id, payload.emoji)


# ----------------- Slash Commands -----------------
# /yatb (nur Admins): info, guide, status, reset, uninstall + Gruppen bridge, keys, log
# /yatb-user (alle Nutzer): privacy, help
# Befehlsnamen bleiben englisch; Beschreibungen übersetzt YatbTranslator in die Sprache des Discord-Clients.
yatb_group = app_commands.Group(
    name="yatb",
    description="YATB translation bridges (admin settings)",
    default_permissions=discord.Permissions(administrator=True),
    guild_only=True,
)
bridge_group = app_commands.Group(name="bridge", description="Manage translation bridges", parent=yatb_group)
keys_group = app_commands.Group(name="keys", description="Manage this server's API keys (stored encrypted)", parent=yatb_group)
log_group = app_commands.Group(name="log", description="Log channel for notifications", parent=yatb_group)
user_group = app_commands.Group(name="yatb-user", description="YATB settings for your own messages", guild_only=True)

REQUIRED_PERMS = {
    "view_channel": "View Channel",
    "read_message_history": "Read Message History",
    "manage_webhooks": "Manage Webhooks",
    "create_public_threads": "Create Public Threads",
    "send_messages_in_threads": "Send Messages in Threads",
    "manage_threads": "Manage Threads",
    "add_reactions": "Add Reactions",   # Reaktionen spiegeln
}


def missing_permissions(channel: Union[discord.TextChannel, discord.ForumChannel]) -> List[str]:
    me = channel.guild.me
    if me is None:
        return []
    perms = channel.permissions_for(me)
    return [label for attr, label in REQUIRED_PERMS.items() if not getattr(perms, attr, True)]


async def _reply(interaction: discord.Interaction, text: str = "", **kwargs):
    if interaction.response.is_done():
        await interaction.followup.send(text, ephemeral=True, **kwargs)
    else:
        await interaction.response.send_message(text, ephemeral=True, **kwargs)


class ConfirmView(discord.ui.View):
    """Bestätigungsdialog für destruktive Befehle (nur der Aufrufer darf klicken)."""

    def __init__(self, user_id: int, locale: Any, action: Callable[[discord.Interaction], Awaitable[None]]):
        super().__init__(timeout=60)
        self.user_id, self.locale, self.action = user_id, locale, action
        self.confirm_btn.label = tx(locale, "btn_confirm")
        self.cancel_btn.label = tx(locale, "btn_cancel")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(tx(self.locale, "not_yours"), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(view=None)
        await self.action(interaction)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content=tx(self.locale, "cancelled"), view=None)


async def drop_guild_webhooks(guild: discord.Guild):
    for channel_id, _bridge, _lang in db.list_guild_bridges(guild.id):
        channel = guild.get_channel(channel_id)
        if channel is not None:
            await drop_channel_webhook(channel)


# ----------------- /yatb info, guide, status -----------------
@yatb_group.command(name="info", description="Setup guide and overview of all commands")
async def yatb_info(interaction: discord.Interaction):
    loc = interaction.locale
    embed = discord.Embed(title=tx(loc, "info_title"), description=tx(loc, "info_desc"), color=discord.Color.blue())
    for i in range(1, 6):
        embed.add_field(name=tx(loc, f"info_f{i}_name"), value=tx(loc, f"info_f{i}_val"), inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


GUIDE_CHOICES = [app_commands.Choice(name=p.name, value=p.id) for p in providers.PROVIDERS.values()]


@yatb_group.command(name="guide", description="How to get an API key for a translation service")
@app_commands.describe(provider="Translation service")
@app_commands.choices(provider=GUIDE_CHOICES)
async def yatb_guide(interaction: discord.Interaction, provider: app_commands.Choice[str]):
    loc, prov = interaction.locale, providers.PROVIDERS[provider.value]
    embed = discord.Embed(title=tx(loc, "guide_title", provider=prov.name), color=discord.Color.blue())
    embed.add_field(name=tx(loc, "guide_steps"), value=tx(loc, f"guide_{prov.id}")[:1024], inline=False)
    if not providers.free_allowed(prov):
        plan = tx(loc, "guide_plan_paid_only")
    else:
        plan = tx(loc, "guide_plan_free_paid")
    embed.add_field(name=tx(loc, "guide_plan"), value=plan, inline=False)
    notes = "\n".join(f"• {n}" for n in (prov.privacy("paid"), prov.privacy("free") if providers.free_allowed(prov) else "") if n)
    if notes:
        embed.add_field(name=tx(loc, "guide_privacy"), value=notes[:1024], inline=False)
    embed.set_footer(text=tx(loc, "guide_footer"))
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def _ping(url: str) -> Tuple[str, int]:
    """('ok' | 'offline' | 'error', Millisekunden)"""
    if http_session is None or http_session.closed:
        return "offline", 0
    t0 = time.perf_counter()
    try:
        async with http_session.get(url, timeout=aiohttp.ClientTimeout(total=3.0)) as resp:
            if resp.status == 200:
                return "ok", round((time.perf_counter() - t0) * 1000)
            return "offline", 0
    except Exception:
        return "error", 0


async def _stage_line(spec: chain.Spec, loc: Any) -> str:
    """Eine Stufe der Kette für /yatb status: Name, Stufe, Zustand, Monatsverbrauch."""
    if spec.key is None:
        return f"{spec.tag} Libre"
    state = tx(loc, "stage_active")
    if not chain.breaker(spec).allow():
        state = tx(loc, "stage_paused")
    _d, month, ms = await limits.monthly_status(spec.key.fingerprint, spec.provider, spec.key.tier, spec.key.budget)
    if ms is not None and spec.key.limit_enabled and (ms.limit - ms.used) <= ms.limit * limits.EXHAUSTED_REMAINING:
        state = tx(loc, "stage_exhausted")
    usage = fmt_monthly(ms, spec.provider, spec.key.currency) if ms else fmt_counts(month, spec.provider)
    label = f' "{spec.key.label}"' if spec.key.label else ""
    return f"{spec.tag} {spec.provider.name}{label} ({spec.key.tier}) · {state} · {usage}"


CHANNEL_LIMIT = 500  # Discord: höchstens 500 Kanäle pro Server (Kategorien zählen mit, Threads nicht)


def channel_counts(guild: discord.Guild) -> Dict[str, int]:
    """Kanäle nach Art: text, news, voice, stage, forum, media, category."""
    counts: Dict[str, int] = {k: 0 for k in ("text", "news", "voice", "stage", "forum", "media", "category")}
    for ch in guild.channels:
        if isinstance(ch, discord.CategoryChannel):
            counts["category"] += 1
        elif isinstance(ch, discord.StageChannel):
            counts["stage"] += 1
        elif isinstance(ch, discord.VoiceChannel):
            counts["voice"] += 1
        elif isinstance(ch, discord.ForumChannel):
            counts["media" if ch.is_media() else "forum"] += 1
        elif isinstance(ch, discord.TextChannel):
            counts["news" if ch.is_news() else "text"] += 1
    return counts


@yatb_group.command(name="channels", description="How many channels this server uses (Discord limit: 500)")
async def channels_cmd(interaction: discord.Interaction):
    loc, guild = interaction.locale, interaction.guild
    counts = channel_counts(guild)
    total = len(guild.channels)
    free = max(0, CHANNEL_LIMIT - total)
    pct = round(total / CHANNEL_LIMIT * 100)
    bridges = db.get_bridge_ids(guild.id)
    color = discord.Color.red() if free < 25 else discord.Color.orange() if pct >= 80 else discord.Color.green()
    embed = discord.Embed(title=tx(loc, "channels_title"), color=color,
                          description=tx(loc, "channels_total", total=total, limit=CHANNEL_LIMIT, pct=pct, free=free))
    types = [f"{tx(loc, 'channels_type_' + k)}: **{n}**" for k, n in counts.items() if n]
    embed.add_field(name=tx(loc, "channels_types"), value="\n".join(types) or "-", inline=False)
    embed.add_field(name=tx(loc, "channels_bridges"),
                    value=tx(loc, "channels_bridges_value", channels=len(db.list_guild_bridges(guild.id)),
                             bridges=len(bridges), per_lang=len(bridges)), inline=False)
    if free < 25:
        embed.add_field(name="⚠️", value=tx(loc, "channels_warn", free=free), inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@yatb_group.command(name="status", description="Translation chain, usage and service health of this server")
async def status_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    loc = interaction.locale
    (lt_state, lt_ms), (bridges_count, channels_count, mappings_count) = await asyncio.gather(
        _ping(f"{tr.LIBRE_URL}/languages"), db.get_stats(interaction.guild_id)
    )
    lines = [f"{i}. {await _stage_line(spec, loc)}" for i, spec in enumerate(chain.build_chain(interaction.guild_id), 1)]
    embed = discord.Embed(
        title=tx(loc, "status_title"), color=discord.Color.green() if lt_state == "ok" else discord.Color.orange(),
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )
    embed.add_field(name=tx(loc, "status_chain"), value="\n".join(lines)[:1024], inline=False)
    embed.add_field(name="🌐 Discord", value=f"`{round(bot.latency * 1000)} ms`", inline=True)
    embed.add_field(name="⚡ LibreTranslate", value=tx(loc, "online", ms=lt_ms) if lt_state == "ok" else tx(loc, lt_state),
                    inline=True)
    embed.add_field(name=tx(loc, "status_stats_name"),
                    value=tx(loc, "status_stats", b=bridges_count, c=channels_count, m=mappings_count), inline=False)
    await interaction.followup.send(embed=embed, ephemeral=True)


# ----------------- /yatb bridge add | remove | list -----------------
async def bridge_id_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    if interaction.guild_id is None:
        return []
    return [
        app_commands.Choice(name=b_id, value=b_id)
        for b_id in db.get_bridge_ids(interaction.guild_id) if current.lower() in b_id.lower()
    ][:25]


@bridge_group.command(name="add", description="Add a channel to a translation bridge")
@app_commands.describe(bridge_id="Name of the bridge (channels with the same name are connected)",
                       channel="Text, forum or media channel", language="Language of this channel")
@app_commands.autocomplete(bridge_id=bridge_id_autocomplete)
@app_commands.choices(language=tr.LANG_CHOICES)
async def bridge_add(
    interaction: discord.Interaction, bridge_id: str, channel: Union[discord.TextChannel, discord.ForumChannel],
    language: app_commands.Choice[str],
):
    loc, guild = interaction.locale, interaction.guild
    bridge_id = bridge_id.strip()[:64]
    if not bridge_id:
        await _reply(interaction, tx(loc, "bad_bridge"))
        return
    others = [guild.get_channel(cid) for cid, _ in db.get_bridge_targets(guild.id, bridge_id, channel.id)]
    if any(o is not None and is_forum(o) != is_forum(channel) for o in others):
        await _reply(interaction, tx(loc, "bridge_kind_mismatch", bridge=bridge_id))
        return
    lang_code = language.value
    await db.add_bridge_channel(channel.id, interaction.guild_id, bridge_id, lang_code)
    msg = tx(loc, "channel_added", channel=channel.mention, bridge=bridge_id, lang=tr.format_lang(lang_code))
    missing = missing_permissions(channel)
    if missing:
        msg += "\n" + tx(loc, "perms_missing", channel=channel.mention, perms=", ".join(missing))
    if is_forum(channel):
        if not channel.permissions_for(guild.me).manage_channels:
            msg += "\n" + tx(loc, "forum_tags_hint", channel=channel.mention)
        asyncio.create_task(sync_forum_tags(guild, channel, bridge_id, tr.normalize_lang(lang_code)))
    await _reply(interaction, msg)
    await send_report(interaction.guild, tx(interaction.guild.preferred_locale, "rep_added", user=interaction.user.mention,
                                            channel=channel.mention, bridge=bridge_id, lang=tr.format_lang(lang_code)))


@bridge_group.command(name="remove", description="Remove a channel from its bridge")
@app_commands.describe(channel="Text, forum or media channel")
async def bridge_remove(interaction: discord.Interaction, channel: Union[discord.TextChannel, discord.ForumChannel]):
    loc = interaction.locale
    removed = await db.remove_bridge_channel(channel.id, interaction.guild_id)
    if removed is None:
        await _reply(interaction, tx(loc, "channel_not_found", channel=channel.mention))
        return
    b_id, lang_code = removed
    await _reply(interaction, tx(loc, "channel_removed", channel=channel.mention, bridge=b_id))
    await send_report(interaction.guild, tx(interaction.guild.preferred_locale, "rep_removed", user=interaction.user.mention,
                                            channel=channel.mention, bridge=b_id, lang=tr.format_lang(lang_code)))
    await drop_channel_webhook(channel)


@bridge_group.command(name="list", description="List all bridges of this server")
async def bridge_list(interaction: discord.Interaction):
    loc = interaction.locale
    rows = db.list_guild_bridges(interaction.guild_id)
    if not rows:
        await _reply(interaction, tx(loc, "no_bridges"))
        return
    _, rep_id, _ = db.get_guild_config(interaction.guild_id)
    embed = discord.Embed(title=tx(loc, "bridges_title"), color=discord.Color.blue())
    bridges: Dict[str, List[str]] = {}
    for ch_id, b_id, lang in rows:
        bridges.setdefault(b_id, []).append(f"<#{ch_id}> ({tr.format_lang(lang)})")
    for b_id, ch_list in list(bridges.items())[:25]:
        embed.add_field(name=tx(loc, "list_field", bridge=b_id), value="\n".join(ch_list)[:1024], inline=False)
    engines = " → ".join(s.provider.name if s.provider else "Libre" for s in chain.build_chain(interaction.guild_id))
    embed.set_footer(text=tx(loc, "list_footer", engines=engines, log=f"#{interaction.guild.get_channel(rep_id)}"
                             if rep_id and interaction.guild.get_channel(rep_id) else tx(loc, "none")))
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ----------------- /yatb keys add | edit | list | remove -----------------
# Alle Key-Daten laufen über das Formular (Modal), keine Slash-Optionen: so fragt das Formular pro Anbieter genau
# ab, was er braucht. Der Key wird verschlüsselt gespeichert und nie wieder angezeigt (nur Anbieter, Label, …1234).
_SECRET_RE = re.compile(r"^\S{16,512}$")
_REGION_RE = re.compile(r"^[a-z0-9]{2,32}$")
_CONFIRM_OK = {"OK", "QUOTA_EXCEEDED", "RATE_LIMITED"}  # Key gültig, nur gerade gedrosselt
CURRENCIES = ("USD", "EUR")


def parse_budget(text: str, default_currency: str) -> Tuple[Optional[float], Optional[str]]:
    """'8.50 EUR', '8,5 €', '$10', '10 usd', '7' -> (Betrag, Währung); leer -> (None, None). ValueError bei Unsinn."""
    raw = (text or "").strip()
    if not raw:
        return None, None
    low = raw.lower().replace("€", " eur ").replace("$", " usd ")
    currency = default_currency
    for code in CURRENCIES:
        if code.lower() in low.split():
            currency = code
            low = " ".join(w for w in low.split() if w != code.lower())
    low = low.strip().replace(",", ".")
    if not re.fullmatch(r"\d{1,4}(\.\d{1,2})?", low):
        raise ValueError(raw)
    amount = float(low)
    if amount > 1000:
        raise ValueError(raw)
    return amount, currency


def _key_currency(info, provider: Optional[providers.Provider]) -> str:
    return getattr(info, "currency", None) or (provider.currency if provider else "USD")


def _key_desc(info: db.ApiKeyInfo) -> str:
    provider = providers.PROVIDERS.get(info.provider)
    return f"`#{info.id}` {provider.name if provider else info.provider}" + (f' "{info.label}"' if info.label else "")


def _budget_text(info, provider: Optional[providers.Provider], loc: Any) -> str:
    if info.tier != "paid":
        return "-"
    amount = info.budget if info.budget is not None else (provider.limits_paid.budget_month if provider else None)
    if amount is None:
        return tx(loc, "none_set")
    return f"{amount:.2f} {_key_currency(info, provider)}" + ("" if info.budget is not None else f" ({tx(loc, 'default')})")


def _key_line(info: db.ApiKeyInfo, loc: Any) -> str:
    provider = providers.PROVIDERS.get(info.provider)
    parts = [_key_desc(info), info.tier, f"{tx(loc, 'keys_limit')} {tx(loc, 'keys_on' if info.limit_enabled else 'keys_off')}"]
    if info.tier == "paid":
        parts.append(f"{tx(loc, 'keys_budget')} {_budget_text(info, provider, loc)}")
    if info.region:
        parts.append(info.region)
    if info.last4:
        parts.append(f"`…{info.last4}`")
    return " · ".join(parts) + (tx(loc, "keys_shared_tag") if info.shared else "")


async def key_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[int]]:
    if interaction.guild_id is None:
        return []
    choices = []
    for info in await db.list_api_keys(interaction.guild_id):
        provider = providers.PROVIDERS.get(info.provider)
        name = f"#{info.id} {provider.name if provider else info.provider}"
        name += (f' "{info.label}"' if info.label else "") + (f" …{info.last4}" if info.last4 else "")
        if current.lower() in name.lower():
            choices.append(app_commands.Choice(name=name[:100], value=info.id))
    return choices[:25]


def _text_field(text: str, description: Optional[str] = None, **kwargs) -> discord.ui.Label:
    return discord.ui.Label(text=text[:45], description=(description or None) and description[:100],
                            component=discord.ui.TextInput(style=discord.TextStyle.short, **kwargs))


def _select_field(text: str, options: List[Tuple[str, str]], selected: str, description: Optional[str] = None) -> discord.ui.Label:
    return discord.ui.Label(text=text[:45], description=(description or None) and description[:100], component=discord.ui.Select(
        options=[discord.SelectOption(label=lbl, value=val, default=val == selected) for val, lbl in options],
        min_values=1, max_values=1,
    ))


def _selected(label: Optional[discord.ui.Label], fallback: str) -> str:
    if label is None:
        return fallback
    values = getattr(label.component, "values", None) or []
    return values[0] if values else fallback


class KeyForm(discord.ui.Modal):
    """Formular pro Anbieter: neu (mit Key-Feld) oder bearbeiten (ohne Key, mit Limit-Schalter). Höchstens 5 Felder."""

    def __init__(self, provider: providers.Provider, locale: Any, info: Optional[db.ApiKeyInfo] = None):
        edit = info is not None
        super().__init__(title=tx(locale, "form_title_edit" if edit else "form_title_add", provider=provider.name)[:45],
                         timeout=600)
        self.provider, self.info, self.loc = provider, info, locale
        self.f_secret = self.f_tier = self.f_region = self.f_limit = None
        currency = _key_currency(info, provider) if edit else provider.currency
        if not edit:
            self.f_secret = _text_field(tx(locale, "form_key"), tx(locale, "form_key_desc"), min_length=16, max_length=512)
            self.add_item(self.f_secret)
        self.f_label = _text_field(tx(locale, "form_label"), tx(locale, "form_label_desc"), required=False, max_length=32,
                                   default=(info.label or "") if edit else None)
        self.add_item(self.f_label)
        if providers.free_allowed(provider):
            self.f_tier = _select_field(tx(locale, "form_tier"), [("free", tx(locale, "tier_free")), ("paid", tx(locale, "tier_paid"))],
                                        info.tier if edit else "free", tx(locale, "form_tier_desc"))
            self.add_item(self.f_tier)
        budget_default = f"{info.budget:.2f} {currency}" if edit and info.budget is not None else None
        default_budget = provider.limits_paid.budget_month
        self.f_budget = _text_field(
            tx(locale, "form_budget"),
            tx(locale, "form_budget_desc", default=f"{default_budget:.2f} {currency}" if default_budget is not None else "-"),
            required=False, max_length=20, placeholder=f"8.50 {currency}", default=budget_default,
        )
        self.add_item(self.f_budget)
        if provider.needs_region:
            self.f_region = _text_field(tx(locale, "form_region"), tx(locale, "form_region_desc"), min_length=2, max_length=32,
                                        placeholder="westeurope", default=(info.region or "") if edit else None)
            self.add_item(self.f_region)
        if edit:
            self.f_limit = _select_field(tx(locale, "form_limit"), [("on", tx(locale, "keys_on")), ("off", tx(locale, "keys_off"))],
                                         "on" if info.limit_enabled else "off", tx(locale, "form_limit_desc"))
            self.add_item(self.f_limit)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        loc, guild, prov = interaction.locale, interaction.guild, self.provider
        label = (self.f_label.component.value or "").strip() or None
        tier = _selected(self.f_tier, "free") if self.f_tier else "paid"
        try:
            budget, currency = parse_budget(self.f_budget.component.value,
                                            _key_currency(self.info, prov) if self.info else prov.currency)
        except ValueError:
            await _reply(interaction, tx(loc, "form_budget_invalid"))
            return
        region = None
        if self.f_region is not None:
            region = (self.f_region.component.value or "").strip().lower()
            if not _REGION_RE.match(region):
                await _reply(interaction, tx(loc, "keys_region_needed"))
                return
        if self.info is None:
            await self._add(interaction, label, tier, budget, currency, region)
        else:
            await self._edit(interaction, label, tier, budget, currency, region, _selected(self.f_limit, "on") == "on")

    async def _add(self, interaction, label, tier, budget, currency, region):
        loc, guild, prov = interaction.locale, interaction.guild, self.provider
        secret = (self.f_secret.component.value or "").strip()
        if not _SECRET_RE.match(secret):
            await _reply(interaction, tx(loc, "keys_bad_format"))
            return
        status = await providers.verify_key(http_session, prov, secret, region)
        if status in providers.REJECT_STATUSES:
            await _reply(interaction, tx(loc, "keys_rejected", provider=prov.name, status=status))
            return
        meta = json.dumps({"region": region}) if region else None
        result, info = await db.add_api_key(interaction.guild_id, prov.id, secret, tier, label, meta, interaction.user.id,
                                            budget, currency if currency != prov.currency else None)
        if result == "no_crypto":
            await _reply(interaction, tx(loc, "keys_no_crypto"))
            return
        if result == "duplicate":
            await _reply(interaction, tx(loc, "keys_duplicate", desc=_key_desc(info)))
            return
        if result == "too_many":
            await _reply(interaction, tx(loc, "keys_too_many", max=db.MAX_KEYS_PER_GUILD))
            return
        lines = [tx(loc, "keys_saved", desc=_key_desc(info)), _key_line(info, loc)]
        if status not in _CONFIRM_OK:
            lines.append(tx(loc, "keys_unverified", provider=prov.name, status=status))
        if info.shared:
            lines.append(tx(loc, "keys_shared_warn"))
        if not providers.free_allowed(prov):
            lines.append(tx(loc, "keys_paid_only", provider=prov.name))
        if note := prov.privacy(tier):
            lines.append(f"🔒 {note}")
        await _reply(interaction, "\n".join(lines))
        log.info("API-Key %s (%s) auf Guild %s hinzugefügt.", info.id, prov.id, interaction.guild_id)
        await send_report(guild, tx(guild.preferred_locale, "rep_key_added", user=interaction.user.mention, desc=_key_desc(info)))

    async def _edit(self, interaction, label, tier, budget, currency, region, limit_on):
        loc, guild, prov, old = interaction.locale, interaction.guild, self.provider, self.info
        turn_off = old.limit_enabled and not limit_on
        updated = await db.update_api_key(
            interaction.guild_id, old.id, label=label, tier=tier, budget=budget,
            currency=currency if currency != prov.currency else None, limit_enabled=old.limit_enabled if turn_off else limit_on,
            region=region,
        )
        if updated is None:
            await _reply(interaction, tx(loc, "keys_not_found"))
            return
        await _reply(interaction, tx(loc, "keys_updated", desc=_key_desc(updated)) + "\n" + _key_line(updated, loc))
        await send_report(guild, tx(guild.preferred_locale, "rep_key_edited", user=interaction.user.mention, desc=_key_desc(updated)))
        if turn_off:  # Limit aus nur mit ausdrücklicher Bestätigung (Kosten liegen beim Admin)
            async def apply(inter: discord.Interaction):
                done = await db.set_api_key_limit(inter.guild_id, old.id, False)
                if done is not None:
                    await _reply(inter, tx(inter.locale, "keys_limit_off", desc=_key_desc(done)))
                    g_loc = inter.guild.preferred_locale
                    await send_report(inter.guild, tx(g_loc, "rep_key_limit", user=inter.user.mention, desc=_key_desc(done),
                                                      state=tx(g_loc, "keys_off")))
            view = ConfirmView(interaction.user.id, loc, apply)
            await interaction.followup.send(tx(loc, "keys_confirm_limit_off", desc=_key_desc(updated)), view=view, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        # Standard-Handler loggt Modal + Traceback - hier bewusst nur der Fehlertyp (Eingabe = Key)
        log.error("Key-Formular fehlgeschlagen: %s", type(error).__name__)
        try:
            await _reply(interaction, tx(interaction.locale, "keys_error"))
        except discord.HTTPException:
            pass


class ProviderPicker(discord.ui.View):
    """Schritt 1 von /yatb keys add: Anbieter wählen -> Formular für genau diesen Anbieter."""

    def __init__(self, user_id: int, locale: Any):
        super().__init__(timeout=300)
        self.user_id, self.locale = user_id, locale
        options = []
        for p in providers.PROVIDERS.values():
            if not p.enabled:
                continue
            kind = "AI" if p.kind == "openai" else "Translator"
            plan = tx(locale, "tier_paid") if not providers.free_allowed(p) else f"{tx(locale, 'tier_free')} / {tx(locale, 'tier_paid')}"
            options.append(discord.SelectOption(label=p.name, value=p.id, description=f"{kind} · {plan}"[:100]))
        self.picker.options = options[:25]
        self.picker.placeholder = tx(locale, "form_pick_provider")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(tx(self.locale, "not_yours"), ephemeral=True)
            return False
        return True

    @discord.ui.select(min_values=1, max_values=1, options=[discord.SelectOption(label="-", value="-")])
    async def picker(self, interaction: discord.Interaction, select: discord.ui.Select):
        provider = providers.PROVIDERS.get(select.values[0])
        if provider is None:
            await interaction.response.send_message(tx(interaction.locale, "keys_not_found"), ephemeral=True)
            return
        await interaction.response.send_modal(KeyForm(provider, interaction.locale))


@keys_group.command(name="add", description="Add an API key (entered in a private form, stored encrypted)")
async def keys_add(interaction: discord.Interaction):
    loc = interaction.locale
    if not db.crypto_available():
        await _reply(interaction, tx(loc, "keys_no_crypto"))
        return
    await _reply(interaction, tx(loc, "form_pick_intro"), view=ProviderPicker(interaction.user.id, loc))


@keys_group.command(name="edit", description="Change the settings of a key (the key itself is never shown)")
@app_commands.describe(key="Key to change")
@app_commands.autocomplete(key=key_autocomplete)
async def keys_edit(interaction: discord.Interaction, key: int):
    info = next((i for i in await db.list_api_keys(interaction.guild_id) if i.id == key), None)
    provider = providers.PROVIDERS.get(info.provider) if info else None
    if info is None or provider is None:
        await _reply(interaction, tx(interaction.locale, "keys_not_found"))
        return
    await interaction.response.send_modal(KeyForm(provider, interaction.locale, info))


@keys_group.command(name="list", description="Show this server's API keys and their usage (never the keys themselves)")
async def keys_list(interaction: discord.Interaction):
    loc = interaction.locale
    infos = await db.list_api_keys(interaction.guild_id)
    if not infos:
        await _reply(interaction, tx(loc, "keys_none"))
        return
    lines = []
    for info in infos:
        lines.append(_key_line(info, loc))
        provider = providers.PROVIDERS.get(info.provider)
        if provider is not None and info.fingerprint:
            u_day, u_month, ms = await limits.monthly_status(info.fingerprint, provider, info.tier, info.budget)
            month = (f"{fmt_monthly(ms, provider, info.currency)} ({ms.ratio * 100:.0f}%)" if ms
                     else fmt_counts(u_month, provider))
            lines.append(tx(loc, "keys_usage_line", month=month, today=fmt_counts(u_day, provider)))
    embed = discord.Embed(title=tx(loc, "keys_title"), description="\n".join(lines)[:4096], color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, ephemeral=True)


@keys_group.command(name="remove", description="Remove an API key from this server")
@app_commands.describe(key="Key to remove")
@app_commands.autocomplete(key=key_autocomplete)
async def keys_remove(interaction: discord.Interaction, key: int):
    loc = interaction.locale
    info = next((i for i in await db.list_api_keys(interaction.guild_id) if i.id == key), None)
    if info is None:
        await _reply(interaction, tx(loc, "keys_not_found"))
        return

    async def do_remove(inter: discord.Interaction):
        removed = await db.remove_api_key(inter.guild_id, key)
        if removed is None:
            await _reply(inter, tx(inter.locale, "keys_not_found"))
            return
        await _reply(inter, tx(inter.locale, "keys_removed", desc=_key_desc(removed)))
        log.info("API-Key %s (%s) auf Guild %s entfernt.", removed.id, removed.provider, inter.guild_id)
        await send_report(inter.guild, tx(inter.guild.preferred_locale, "rep_key_removed", user=inter.user.mention,
                                          desc=_key_desc(removed)))

    view = ConfirmView(interaction.user.id, loc, do_remove)
    await interaction.response.send_message(tx(loc, "keys_confirm_remove", desc=_key_desc(info)), view=view, ephemeral=True)


# ----------------- /yatb log set | clear -----------------
@log_group.command(name="set", description="Set the channel for notifications (usage warnings, key problems, changes)")
@app_commands.describe(channel="Text channel")
async def log_set(interaction: discord.Interaction, channel: discord.TextChannel):
    await db.set_guild_report_channel(interaction.guild_id, channel.id)
    await _reply(interaction, tx(interaction.locale, "report_channel_set", channel=channel.mention))
    await send_report(interaction.guild, tx(interaction.guild.preferred_locale, "rep_channel_set", channel=channel.mention))


@log_group.command(name="clear", description="Turn off the notification channel")
async def log_clear(interaction: discord.Interaction):
    await db.set_guild_report_channel(interaction.guild_id, None)
    await _reply(interaction, tx(interaction.locale, "report_channel_cleared"))


# ----------------- /yatb reset | uninstall -----------------
@yatb_group.command(name="reset", description="Delete all bridges, keys and settings of this server")
async def reset_guild_cmd(interaction: discord.Interaction):
    async def do_reset(inter: discord.Interaction):
        await drop_guild_webhooks(inter.guild)
        await db.clear_guild_data(inter.guild_id)
        await inter.followup.send(tx(inter.locale, "reset_done"), ephemeral=True)

    view = ConfirmView(interaction.user.id, interaction.locale, do_reset)
    await interaction.response.send_message(tx(interaction.locale, "confirm_reset"), view=view, ephemeral=True)


@yatb_group.command(name="uninstall", description="Delete all data of this server and make the bot leave")
async def uninstall_cmd(interaction: discord.Interaction):
    async def do_uninstall(inter: discord.Interaction):
        guild = inter.guild
        await drop_guild_webhooks(guild)
        await db.clear_guild_data(guild.id)
        await inter.followup.send(tx(inter.locale, "uninstall_done"), ephemeral=True)
        await asyncio.sleep(2)
        await guild.leave()

    view = ConfirmView(interaction.user.id, interaction.locale, do_uninstall)
    await interaction.response.send_message(tx(interaction.locale, "confirm_uninstall"), view=view, ephemeral=True)


# ----------------- /yatb-user privacy | help (für alle Nutzer) -----------------
def _privacy_embed(user_id: int, loc: Any) -> discord.Embed:
    local = db.is_local_only(user_id)
    embed = discord.Embed(title=tx(loc, "privacy_title"), color=discord.Color.green() if local else discord.Color.blue(),
                          description=tx(loc, "privacy_state_local" if local else "privacy_state_standard"))
    embed.add_field(name=tx(loc, "privacy_standard_name"), value=tx(loc, "privacy_standard_desc"), inline=False)
    embed.add_field(name=tx(loc, "privacy_local_name"), value=tx(loc, "privacy_local_desc"), inline=False)
    return embed


class PrivacyView(discord.ui.View):
    def __init__(self, user_id: int, locale: Any):
        super().__init__(timeout=300)
        self.user_id, self.locale = user_id, locale
        local = db.is_local_only(user_id)
        self.standard_btn.label, self.local_btn.label = tx(locale, "privacy_btn_standard"), tx(locale, "privacy_btn_local")
        self.standard_btn.disabled, self.local_btn.disabled = not local, local

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(tx(self.locale, "not_yours"), ephemeral=True)
            return False
        return True

    async def _set(self, interaction: discord.Interaction, local: bool):
        await db.set_local_only(self.user_id, local)
        log.info("Opt-out 'nur lokal' %s.", "eingeschaltet" if local else "ausgeschaltet")  # bewusst ohne Nutzer-ID
        await interaction.response.edit_message(embed=_privacy_embed(self.user_id, self.locale),
                                                view=PrivacyView(self.user_id, self.locale))

    @discord.ui.button(label="Standard", style=discord.ButtonStyle.primary)
    async def standard_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._set(interaction, False)

    @discord.ui.button(label="Local only", style=discord.ButtonStyle.success)
    async def local_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._set(interaction, True)


@user_group.command(name="privacy", description="Choose who may translate your messages (applies on all servers)")
async def user_privacy(interaction: discord.Interaction):
    await _reply(interaction, embed=_privacy_embed(interaction.user.id, interaction.locale),
                 view=PrivacyView(interaction.user.id, interaction.locale))


@user_group.command(name="help", description="What this bot does with your messages")
async def user_help(interaction: discord.Interaction):
    loc = interaction.locale
    embed = discord.Embed(title=tx(loc, "user_help_title"), description=tx(loc, "user_help_desc"), color=discord.Color.blue())
    embed.add_field(name=tx(loc, "user_help_tags_name"), value=tx(loc, "user_help_tags"), inline=False)
    embed.add_field(name=tx(loc, "user_help_privacy_name"), value=tx(loc, "user_help_privacy"), inline=False)
    await _reply(interaction, embed=embed)


# ----------------- Übersetzung der Befehlsbeschreibungen -----------------
class YatbTranslator(app_commands.Translator):
    """Beschreibungen von Befehlen/Optionen in die Sprache des Discord-Clients; Namen bleiben englisch."""

    async def translate(self, string: app_commands.locale_str, locale: discord.Locale,
                        context: app_commands.TranslationContext) -> Optional[str]:
        if context.location in (app_commands.TranslationContextLocation.command_name,
                                app_commands.TranslationContextLocation.group_name,
                                app_commands.TranslationContextLocation.parameter_name):
            return None
        return command_text(locale, string.message)


# ----------------- Bot Events -----------------
_ready_done = False


@bot.event
async def on_ready():
    global _ready_done
    if not _ready_done:  # on_ready feuert bei jedem Reconnect - Einmal-Aufgaben nur beim ersten Mal
        _ready_done = True
        if os.getenv("CLEANUP_GUILD_COMMANDS") == "1":
            for guild in bot.guilds:
                bot.tree.clear_commands(guild=guild)
                await bot.tree.sync(guild=guild)
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="/yatb info"))
        log.info("YATB online als %s - bereit.", bot.user)


@bot.event
async def on_guild_join(guild: discord.Guild):
    await asyncio.sleep(2)
    inviter = None
    try:  # braucht 'View Audit Log' - ohne dieses Recht greift der Fallback auf den Server-Owner
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.bot_add):
            if entry.target and bot.user and entry.target.id == bot.user.id:
                inviter = entry.user
                break
    except discord.HTTPException:
        pass
    target_user = inviter or guild.owner
    if target_user is None:
        return
    try:
        await target_user.send(tx(guild.preferred_locale, "welcome", name=target_user.name, guild=guild.name))
    except discord.HTTPException as exc:
        log.info("Willkommens-DM fehlgeschlagen: %s", exc)


@bot.event
async def on_guild_remove(guild: discord.Guild):
    await db.clear_guild_data(guild.id)


@bot.event
async def on_guild_channel_delete(channel: discord.abc.GuildChannel):
    webhook_cache.pop(channel.id, None)
    if db.is_bridged(channel.id):
        await db.remove_bridge_channel(channel.id, channel.guild.id)


def main():
    if not DISCORD_TOKEN:
        raise SystemExit("DISCORD_TOKEN fehlt (Umgebungsvariable oder .env).")
    bot.run(DISCORD_TOKEN, log_handler=None)


if __name__ == "__main__":
    main()