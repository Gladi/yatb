# Running your own YATB instance

YATB is built to run as a small Docker Compose stack on one Linux host (x86_64 or ARM). The reference instance runs
on a 4-core ARM VM; the bot itself needs little, LibreTranslate needs about 2-3 GB RAM for seven languages.

## 1. Discord application

1. Create an application in the [Discord Developer Portal](https://discord.com/developers/applications).
2. **Bot** tab: create the bot, copy the token (`DISCORD_TOKEN`), enable the privileged intent
   **Message Content**. Turn off *Public Bot* if only you should be able to invite it.
3. **OAuth2 → URL Generator:** scopes `bot` and `applications.commands`, bot permissions:
   - View Channels, Read Message History, Send Messages (log channel), Manage Webhooks,
     Create Public Threads, Send Messages in Threads, Manage Threads, Add Reactions
   - optional: Manage Channels (only on forum categories - YATB creates missing forum tags),
     View Audit Log (welcome message goes to the person who added the bot instead of the owner)
4. Dashboard only: **OAuth2** tab: copy the client ID and client secret, add the redirect URL
   `https://<your-domain>/app/callback`.

## 2. Files

```
git clone https://github.com/Gladi/yatb.git && cd yatb
cp docker-compose.example.yml docker-compose.yml
cp .env.example .env              # DISCORD_TOKEN and optional settings
chmod 600 .env
mkdir -m 700 secrets
head -c 32 /dev/urandom | base64 > secrets/yatb_master_key        # encrypts the API keys - back it up separately
head -c 32 /dev/urandom | base64 > secrets/yatb_internal_token    # bot <-> dashboard, only with the dashboard
```

The dashboard additionally needs `secrets/yatb_discord_client_secret` (the OAuth2 client secret) and the settings
`YATB_BASE_URL` and `YATB_CLIENT_ID` in `docker-compose.yml`. Without the dashboard, remove the `yatb-web` service
and the `yatb_internal_token` secret.

## 3. Start

```
docker compose up -d --build
docker compose logs -f bot        # logs are in German: "Master-Schlüssel geladen", then "YATB online als ..."
```

The first start of LibreTranslate downloads its language models (a few minutes). Then invite the bot with the URL
from step 1.3 and run `/yatb info` on your server.

## 4. Web access (dashboard)

The dashboard listens on port 8080 inside the Docker network and expects a reverse proxy with TLS in front of it,
serving it under `/app` of `YATB_BASE_URL`. A Caddy example is in `site/Caddyfile.snippet` (`yatb_app`).

## 5. Configuration

- `.env`: see `.env.example` - all settings except `DISCORD_TOKEN` are optional.
- `config/providers.toml`: providers, models, prices and free-tier limits. It is mounted read-only; after a change,
  restart the bot (`docker compose restart bot`), no rebuild needed.
- AI context: `AI_CONTEXT_HINT` tells the AI what kind of community it translates for (default: gaming).

## 6. Data and backups

| Path | Content |
|---|---|
| `data/db/bridge_bot.db` | bridges, encrypted API keys, usage, privacy choices |
| `data/stats/stats.db` | call statistics without message texts |
| `data/web/sessions.db` | dashboard sessions (hashed), 7 days |
| `secrets/yatb_master_key` | without it, stored API keys cannot be decrypted |

Back up the databases regularly (`sqlite3 data/db/bridge_bot.db "VACUUM INTO 'backup.db'"`) and keep the master key
in a separate place (for example a password manager). Message mappings are deleted after 7 days.

## 7. Updates

```
git pull
docker compose up -d --build bot yatb-web
```

Run the unit tests before going live:
`docker run --rm --network none -v "$PWD":/src:ro -w /src yatb-bot python -m unittest discover -s tests`

## 8. Website

`site/` builds the static website of the reference instance (yatb.gladi.de) in seven languages. It is not needed to
run the bot. To publish your own, edit `site/site.toml` and `site/content/` - the privacy policy and terms describe
the reference instance and must be adapted to yours.
