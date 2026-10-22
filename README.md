# YATB - Yet Another Translation Bot

YATB links Discord channels in different languages. Everyone writes in their own language; YATB posts the
translation in the other channels of the bridge under the author's name and avatar.

Website and user guide: **[yatb.gladi.de](https://yatb.gladi.de)** · Support: [Ko-fi](https://ko-fi.com/letsgo2u)

## Features

- **Seven languages:** English, German, French, Spanish, Italian, Russian, Dutch, in any combination.
- **The whole conversation:** replies, edits, deletes, threads, attachments, reactions and announcements from
  followed channels are mirrored. Forum and media channels work too (posts, titles and tags).
- **Translation chain per server:** AI providers with the server's own API keys (Google Gemini, Mistral, Groq,
  Novita - any OpenAI-compatible API can be added in `config/providers.toml`), then Google Translate, Azure
  Translator and a self-hosted LibreTranslate. Every answer is validated (mentions, links, emoji, code and Markdown
  must survive); a failed answer falls through to the next stage.
- **Bring your own keys:** server admins add keys in a private Discord form. Keys are encrypted per server
  (AES-256-GCM, HKDF from a master key) and never shown again. Daily/monthly limits, budgets and warnings per key.
- **Privacy:** message texts are not stored. Members can choose *Local only* (`/yatb-user privacy`): their messages
  are then only translated by the self-hosted LibreTranslate.
- **Dashboard (optional):** Discord login, usage statistics per provider, key settings and chain order for admins,
  privacy choice for members.

## Commands

| Command | Who | Purpose |
|---|---|---|
| `/yatb info`, `/yatb guide` | admins | setup guide, how to get an API key |
| `/yatb bridge add / remove / list` | admins | link channels (text with text, forum with forum) |
| `/yatb keys add / edit / list / remove` | admins | manage the server's API keys |
| `/yatb status`, `/yatb channels` | admins | chain, usage and health; channel count (Discord limit 500) |
| `/yatb log set / clear` | admins | channel for usage warnings and key problems |
| `/yatb reset`, `/yatb uninstall` | admins | delete the server's data (and leave) |
| `/yatb-user privacy`, `/yatb-user help` | everyone | own privacy choice, what the bot does with messages |

## Running your own instance

YATB runs as a Docker Compose stack (bot, optional dashboard, LibreTranslate). See
**[docs/self-hosting.md](docs/self-hosting.md)** for the Discord setup, configuration and secrets.

```
cp docker-compose.example.yml docker-compose.yml
cp .env.example .env            # add your DISCORD_TOKEN
mkdir -m 700 secrets && head -c 32 /dev/urandom | base64 > secrets/yatb_master_key
docker compose up -d --build
```

## Development

- Python 3.11, [discord.py](https://github.com/Rapptz/discord.py) 2.x, aiohttp, SQLite.
- Unit tests (offline, no Discord connection):
  `docker run --rm --network none -v "$PWD":/src:ro -w /src <image> python -m unittest discover -s tests`
- End-to-end tests against a test server: `tests/e2e_bridge.py`, `tests/e2e_forum.py` (need a separate test bot
  and a driver bot; see the file headers).
- Code comments are mostly in German; user-facing texts live in `locales.py` (en/de by hand) and `locales_mt.py`
  (machine-translated).

| Path | Content |
|---|---|
| `bot.py` | Discord events, webhooks, slash commands |
| `chain.py`, `translator.py`, `markup.py`, `validator.py` | translation chain, engines, placeholders, checks |
| `database.py`, `key_crypto.py`, `limits.py`, `stats.py` | storage, key encryption, limits, statistics |
| `internal_api.py`, `dashboard/` | internal API of the bot, web dashboard |
| `config/providers.toml` | providers, models, prices and free-tier limits |
| `site/` | static website generator for yatb.gladi.de |

## Security

Please report vulnerabilities privately, see [SECURITY.md](SECURITY.md).

## License

[GNU Affero General Public License v3.0](LICENSE). If you run a modified version for others (for example as a
public bot or dashboard), the AGPL requires you to offer them the source code of your version.
