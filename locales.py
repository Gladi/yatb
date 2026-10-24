"""
YATB - alle Bot-Texte in einer Sprachtabelle

* MESSAGES["en"] ist Referenz und Rückfall: fehlt ein Text in einer Sprache, wird Englisch genutzt.
* Englisch und Deutsch werden von Hand gepflegt. Französisch, Spanisch, Italienisch und Russisch stehen in
  locales_mt.py - einmalig maschinell übersetzt (Gemini) und dort gekennzeichnet, bis Muttersprachler sie prüfen.
* Platzhalter wie {channel} müssen in allen Sprachen gleich sein (prüft tests/test_locales.py).
* COMMANDS: Beschreibungen der Slash-Befehle/Optionen, Schlüssel = englischer Text (für YatbTranslator in bot.py).
"""
from typing import Any, Dict, Optional

MESSAGES: Dict[str, Dict[str, str]] = {
    "en": {
        # ---- allgemein
        "btn_confirm": "Confirm", "btn_cancel": "Cancel", "cancelled": "Cancelled.",
        "not_yours": "Only the person who ran the command can use these buttons.",
        "none": "None", "none_set": "not set", "default": "default",
        "online": "🟢 Online ({ms} ms)", "offline": "🔴 Offline", "error": "🔴 Error",
        "welcome": "Hello {name}! Thanks for adding **YATB** to **{guild}**.\n• Start with `/yatb info`.\n"
                   "• Add a translation key with `/yatb keys add` (how to get one: `/yatb guide`).",
        # ---- /yatb info
        "info_title": "🌐 YATB (Yet Another Translation Bot) - Guide",
        "info_desc": "YATB connects text channels of different languages into translation bridges: a message in one "
                     "channel appears translated in all others, including replies, edits, deletes and threads.",
        "info_f1_name": "1. Connect channels",
        "info_f1_val": "`/yatb bridge add` adds a channel to a bridge - channels with the same bridge name are translated "
                       "into each other.\n*Example:* `/yatb bridge add chat #english English` and "
                       "`/yatb bridge add chat #german German`. Overview: `/yatb bridge list`.\n"
                       "Forum and media channels work the same way (forum with forum). For automatic tags YATB needs "
                       "*Manage Channels* there - easiest on the category of the forums.",
        "info_f2_name": "2. Translation services",
        "info_f2_val": "Without keys YATB translates with LibreTranslate (local, free, basic quality). Better results with "
                       "your own API keys: `/yatb keys add` (AI providers, Google, Azure). Order: AI → Google → Azure → "
                       "Libre. How to get a key: `/yatb guide`.",
        "info_f3_name": "3. Usage & limits",
        "info_f3_val": "`/yatb keys list` shows the usage per key, `/yatb keys edit` changes plan, budget and limit. "
                       "Warnings at 90/95/100 % go to the log channel (`/yatb log set`).",
        "info_f4_name": "4. Status",
        "info_f4_val": "`/yatb status` shows the translation chain of this server and the state of every service.",
        "info_f5_name": "5. Privacy & reset",
        "info_f5_val": "Members can choose `/yatb-user privacy` → *Local only*: their messages are then only translated "
                       "locally and never sent to third parties.\n• `/yatb reset`: deletes all bridges, keys and settings.\n"
                       "• `/yatb uninstall`: deletes all data and the bot leaves the server.",
        # ---- /yatb guide
        "guide_title": "🔑 How to get a {provider} API key",
        "guide_steps": "Steps", "guide_plan": "Plan", "guide_privacy": "Privacy",
        "guide_plan_paid_only": "Only paid keys (project/account with billing) can be used.",
        "guide_plan_free_paid": "Free and paid keys are possible. With a free key the provider's limits apply; with a "
                                "paid key you set a monthly budget.",
        "guide_footer": "Menu names at the providers can change. Tip: also set a spending limit in your provider account.",
        "guide_gemini": "1. Open aistudio.google.com and sign in with your Google account.\n"
                        "2. Create or choose a Google Cloud project and **enable billing** for it - the free tier may not "
                        "be used for users in the EEA, UK or Switzerland.\n"
                        "3. **Get API key** → **Create API key** for this project.\n"
                        "4. Run `/yatb keys add`, choose **Google Gemini** and paste the key.",
        "guide_mistral": "1. Sign in at console.mistral.ai.\n"
                         "2. Under **Billing** choose a paid plan (the free Experiment plan may use your data for training).\n"
                         "3. **API Keys** → **Create new key**.\n"
                         "4. Run `/yatb keys add`, choose **Mistral** and paste the key.",
        "guide_groq": "1. Sign in at console.groq.com.\n"
                      "2. Recommended: enable zero data retention under **Settings → Data Controls**.\n"
                      "3. **API Keys** → **Create API Key**.\n"
                      "4. Run `/yatb keys add` and choose **Groq**. The free plan has low limits (about 30 requests per minute).",
        "guide_novita": "1. Sign in at novita.ai and add credit (there is no free plan).\n"
                        "2. Create a key under **Key Management**.\n"
                        "3. Run `/yatb keys add` and choose **Novita**.",
        "guide_google_translate": "1. Open console.cloud.google.com and create a project.\n"
                                  "2. Enable the **Cloud Translation API** (a billing account is required; the first "
                                  "500,000 characters per month are free).\n"
                                  "3. **APIs & Services → Credentials → Create credentials → API key**, then restrict the "
                                  "key to the Cloud Translation API.\n"
                                  "4. Run `/yatb keys add` and choose **Google Translate**.",
        "guide_azure": "1. In portal.azure.com create a **Translator** resource (pricing tier **F0** = 2 million characters "
                       "per month free).\n"
                       "2. Open **Keys and Endpoint**: copy **Key 1** and the **Location/Region** (e.g. westeurope).\n"
                       "3. Run `/yatb keys add`, choose **Azure Translator** and enter key and region.",
        # ---- /yatb status
        "status_title": "🛠️ YATB system status",
        "bridge_kind_mismatch": "❌ Forums can only be linked with forums, text channels only with text channels. Bridge `{bridge}` already contains the other kind - please use a different bridge name.",
        "forum_tags_hint": "ℹ️ To create missing tags in {channel} itself, YATB needs the permission **Manage Channels** in this forum. Without it, only tags with the same name are matched.",
        "rep_tags_no_permission": "⚠️ YATB could not create a matching tag in {channel}: the permission **Manage Channels** is missing there.",
        "rep_tags_full": "⚠️ {channel} already has 20 tags (Discord limit) - a matching tag could not be created.",
        "channels_title": "📊 Channels on this server",
        "channels_total": "**{total} of {limit}** channels used ({pct} %) - **{free}** still free.\\nDiscord allows 500 channels per server; categories count, threads do not.",
        "channels_types": "By type",
        "channels_type_text": "💬 Text",
        "channels_type_news": "📢 Announcement",
        "channels_type_voice": "🔊 Voice",
        "channels_type_stage": "🎙️ Stage",
        "channels_type_forum": "🗂️ Forum",
        "channels_type_media": "🖼️ Media",
        "channels_type_category": "📁 Categories",
        "channels_bridges": "YATB bridges",
        "channels_bridges_value": "**{channels}** channels in **{bridges}** bridges. Adding one more language to every bridge needs **{per_lang}** new channels.",
        "channels_warn": "Only **{free}** channels left. Remove unused channels before adding new languages.",
        "status_chain": "🔗 Translation chain (in this order)",
        "stage_active": "active", "stage_paused": "⏸ paused (errors)", "stage_exhausted": "🚫 limit reached",
        "status_stats_name": "📊 Server statistics",
        "status_stats": "• Bridges: `{b}`\n• Channels: `{c}`\n• Message tracker: `{m}`",
        # ---- /yatb bridge
        "bad_bridge": "Please enter a bridge name.",
        "channel_added": "✅ Channel {channel} added to bridge `{bridge}` ({lang}).",
        "channel_removed": "🗑️ Channel {channel} removed from bridge `{bridge}`.",
        "channel_not_found": "⚠️ Channel {channel} is not part of any bridge on this server.",
        "no_bridges": "No bridges on this server yet. Use `/yatb bridge add`.",
        "bridges_title": "🌐 Bridges on this server",
        "list_field": "Bridge: {bridge}",
        "list_footer": "Engines: {engines} | Log: {log}",
        "perms_missing": "⚠️ Missing permissions in {channel}: {perms}. The bridge may not work until they are granted.",
        "send_forbidden": "⚠️ I lack the permissions to bridge messages into {channel} (Manage Webhooks, Create Public "
                          "Threads, Send Messages in Threads).",
        "rep_added": "➕ **Bridge:** {user} added {channel} to `{bridge}` ({lang}).",
        "rep_removed": "🗑️ **Bridge:** {user} removed {channel} ({lang}) from `{bridge}`.",
        # ---- /yatb keys (Formular)
        "form_pick_intro": "Which service is the key for? Choose it below - a form for exactly this service opens next. "
                           "The key is entered only there.",
        "form_pick_provider": "Choose a translation service",
        "form_title_add": "Add {provider} key",
        "form_title_edit": "Edit {provider} key",
        "form_key": "API key", "form_key_desc": "Stored encrypted and never shown again.",
        "form_label": "Name (optional)", "form_label_desc": "To tell your keys apart, e.g. main",
        "form_tier": "Plan", "form_tier_desc": "Free: the provider's limits apply. Paid: monthly budget.",
        "tier_free": "Free", "tier_paid": "Paid",
        "form_budget": "Monthly budget (paid only)",
        "form_budget_desc": "e.g. 8.50 EUR or 10 USD. Empty = default ({default}).",
        "form_budget_invalid": "❌ Budget not understood. Use e.g. `8.50 EUR` or `10 USD` (max. 1000). Nothing was changed.",
        "form_region": "Azure region", "form_region_desc": "Location of your Translator resource, e.g. westeurope",
        "form_limit": "Usage limit", "form_limit_desc": "On = stop at the plan limits or budget (recommended)",
        # ---- /yatb keys (Antworten)
        "keys_no_crypto": "🔒 Key storage is not available yet: the bot operator has not configured the master key.",
        "keys_region_needed": "❌ Azure needs the region of your Translator resource (e.g. `westeurope`). Nothing was saved.",
        "keys_bad_format": "❌ That does not look like an API key (16-512 characters, no spaces). Nothing was saved.",
        "keys_rejected": "❌ {provider} rejected this key ({status}). It was not saved.",
        "keys_unverified": "⚠️ {provider} could not be reached to verify the key ({status}); it was saved anyway.",
        "keys_saved": "🔑 Key saved: {desc}. It is stored encrypted and will never be shown again.",
        "keys_updated": "✅ Settings saved: {desc}",
        "keys_duplicate": "ℹ️ This key is already stored on this server: {desc}.",
        "keys_too_many": "❌ This server already has {max} keys. Remove one first (`/yatb keys remove`).",
        "keys_shared_warn": "⚠️ This key is already used on another server. Usage and limit are counted together.",
        "keys_paid_only": "ℹ️ {provider} is only used with paid keys (billing enabled), so the key was saved as **paid**.",
        "keys_error": "❌ The key could not be processed. Nothing was changed.",
        "keys_none": "No API keys are stored on this server. Add one with `/yatb keys add`.",
        "keys_title": "🔑 API keys of this server",
        "keys_limit": "limit", "keys_budget": "budget", "keys_on": "on", "keys_off": "off",
        "keys_shared_tag": " · 🔗 also used on another server",
        "keys_usage_line": "  ↳ month: {month} · today: {today}",
        "keys_not_found": "⚠️ This key was not found on this server.",
        "keys_removed": "🗑️ Key removed: {desc}.",
        "keys_confirm_remove": "⚠️ Remove the key {desc}? Translations with this key stop immediately.",
        "keys_limit_on": "✅ Usage limit enabled for {desc}.",
        "keys_limit_off": "⚠️ Usage limit disabled for {desc}.",
        "keys_confirm_limit_off": "⚠️ **Disable the usage limit for {desc}?**\nThe bot will then keep using this key beyond "
                                  "the free/plan limits. Any costs charged by the provider are **your responsibility**.",
        "rep_key_added": "🔑 {user} added an API key: {desc}.",
        "rep_key_edited": "ℹ️ {user} changed the settings of {desc}.",
        "rep_key_removed": "🗑️ {user} removed an API key: {desc}.",
        "rep_key_limit": "ℹ️ {user} set the usage limit of {desc} to **{state}**.",
        "rep_order_set": "🔀 {user} changed the order of the translation services: {order}.",
        "rep_order_reset": "🔀 {user} reset the order of the translation services to the default: {order}.",
        # ---- Meldungen der Übersetzungskette (Log-Kanal)
        "usage_warn": "⚠️ Key {desc}: **{pct}%** of the monthly limit used ({usage}).",
        "usage_full": "🚫 Key {desc}: monthly limit reached ({usage}). The key is paused until the 1st of next month "
                      "(00:00 UTC) or until its limit is raised; translations use the next engine.",
        "usage_full_nolimit": "⚠️ Key {desc}: monthly limit exceeded ({usage}). The limit is switched off for this key, so "
                              "it keeps being used - any costs are the admin's responsibility.",
        "key_rejected": "🔑 {provider} rejected the API key of this server ({status}). The key is skipped for 1 hour and the "
                        "next engine is used. Check it with `/yatb keys list` or replace it with `/yatb keys add`.",
        "model_missing": "⚠️ {provider}: the model `{model}` is not available (removed or renamed by the provider). It is "
                         "skipped for 6 hours; the bot operator needs to update the provider configuration.",
        "provider_spend_limit": "⚠️ {provider} reports that the monthly spending limit or credit of the key's account is "
                                "used up. The key is paused and retried every hour; translations use the next engine. "
                                "Raise the limit in the {provider} console.",
        "provider_quota": "⚠️ {provider} reports that the quota of this server's key is used up. The key is paused until "
                          "00:00 UTC; translations use the next engine.",
        # ---- /yatb log, reset, uninstall
        "report_channel_set": "📢 Log channel set to {channel}.",
        "report_channel_cleared": "📢 Log channel turned off.",
        "rep_channel_set": "ℹ️ {channel} is now the log channel.",
        "confirm_reset": "⚠️ This deletes **all** bridges, keys and settings of this server. Continue?",
        "confirm_uninstall": "⚠️ This deletes **all** data of this server and the bot will leave. Continue?",
        "reset_done": "🔄 All bridges, webhook links, keys and settings of this server have been deleted.",
        "uninstall_done": "👋 All data has been deleted. YATB is now leaving the server.",
        # ---- /yatb-user
        "privacy_title": "🔒 Your translation privacy",
        "privacy_state_standard": "Current setting: **Standard**.",
        "privacy_state_local": "Current setting: **Local only**.",
        "privacy_standard_name": "Standard",
        "privacy_standard_desc": "Best quality. Your messages may be sent to the translation services the admins of the "
                                 "server added (e.g. AI providers, Google, Azure). The admins choose these services.",
        "privacy_local_name": "Local only",
        "privacy_local_desc": "Your messages stay with the bot: they are only translated by LibreTranslate on its own "
                              "server and never sent to AI providers, Google or Azure - also not as context for other "
                              "people's translations. Translation quality is lower. Applies on all servers with YATB.",
        "privacy_btn_standard": "Use Standard", "privacy_btn_local": "Use Local only",
        "user_help_title": "ℹ️ YATB - translation bridges",
        "user_help_desc": "This server connects channels in different languages. When you write in one of them, YATB posts "
                          "a translation in the others under your name. Replies, edits, deletes and reactions are mirrored. YATB does "
                          "not store message texts - only which message belongs to which translation (7 days).",
        "user_help_tags_name": "What the tag after the name means",
        "user_help_tags": "`[AI]` AI provider · `[Google]` Google Translate · `[Azure]` Azure Translator · "
                          "`[Libre]` LibreTranslate (local) · `[Raw]` not translated (no service available)",
        "user_help_privacy_name": "Your choice",
        "user_help_privacy": "With `/yatb-user privacy` you can decide that your messages are only translated locally and "
                             "never sent to third parties.",
    },
    "de": {
        "btn_confirm": "Bestätigen", "btn_cancel": "Abbrechen", "cancelled": "Abgebrochen.",
        "not_yours": "Nur die Person, die den Befehl ausgeführt hat, kann diese Buttons benutzen.",
        "none": "Keiner", "none_set": "nicht gesetzt", "default": "Standard",
        "online": "🟢 Online ({ms} ms)", "offline": "🔴 Offline", "error": "🔴 Fehler",
        "welcome": "Hallo {name}! Danke, dass du **YATB** zu **{guild}** hinzugefügt hast.\n• Starte mit `/yatb info`.\n"
                   "• Hinterlege einen Übersetzungs-Key mit `/yatb keys add` (Anleitung: `/yatb guide`).",
        "info_title": "🌐 YATB (Yet Another Translation Bot) - Anleitung",
        "info_desc": "YATB verbindet Text-Kanäle verschiedener Sprachen zu Übersetzungs-Bridges: Eine Nachricht in einem "
                     "Kanal erscheint übersetzt in allen anderen, inklusive Antworten, Bearbeitungen, Löschungen und Threads.",
        "info_f1_name": "1. Kanäle verbinden",
        "info_f1_val": "`/yatb bridge add` nimmt einen Kanal in eine Bridge auf - Kanäle mit demselben Bridge-Namen werden "
                       "ineinander übersetzt.\n*Beispiel:* `/yatb bridge add chat #english English` und "
                       "`/yatb bridge add chat #deutsch German`. Übersicht: `/yatb bridge list`.\n"
                       "Foren- und Medien-Kanäle funktionieren genauso (Forum mit Forum). Für automatische Tags braucht "
                       "YATB dort *Kanäle verwalten* - am einfachsten auf der Kategorie der Foren.",
        "info_f2_name": "2. Übersetzungsdienste",
        "info_f2_val": "Ohne Keys übersetzt YATB mit LibreTranslate (lokal, kostenlos, einfache Qualität). Bessere "
                       "Ergebnisse mit eigenen API-Keys: `/yatb keys add` (KI-Anbieter, Google, Azure). Reihenfolge: "
                       "KI → Google → Azure → Libre. So bekommst du einen Key: `/yatb guide`.",
        "info_f3_name": "3. Verbrauch & Limits",
        "info_f3_val": "`/yatb keys list` zeigt den Verbrauch pro Key, `/yatb keys edit` ändert Tarif, Budget und Limit. "
                       "Warnungen bei 90/95/100 % gehen in den Log-Kanal (`/yatb log set`).",
        "info_f4_name": "4. Status",
        "info_f4_val": "`/yatb status` zeigt die Übersetzungskette dieses Servers und den Zustand jedes Dienstes.",
        "info_f5_name": "5. Datenschutz & Zurücksetzen",
        "info_f5_val": "Mitglieder können `/yatb-user privacy` → *Nur lokal* wählen: Ihre Nachrichten werden dann nur lokal "
                       "übersetzt und nie an Dritte geschickt.\n• `/yatb reset`: löscht alle Bridges, Keys und "
                       "Einstellungen.\n• `/yatb uninstall`: löscht alle Daten und der Bot verlässt den Server.",
        "guide_title": "🔑 So bekommst du einen {provider} API-Key",
        "guide_steps": "Schritte", "guide_plan": "Tarif", "guide_privacy": "Datenschutz",
        "guide_plan_paid_only": "Nur bezahlte Keys (Projekt/Konto mit Abrechnung) sind nutzbar.",
        "guide_plan_free_paid": "Kostenlose und bezahlte Keys sind möglich. Bei kostenlosen Keys gelten die Limits des "
                                "Anbieters, bei bezahlten legst du ein Monatsbudget fest.",
        "guide_footer": "Menünamen bei den Anbietern können sich ändern. Tipp: Lege auch im Konto des Anbieters ein "
                        "Ausgabenlimit fest.",
        "guide_gemini": "1. Öffne aistudio.google.com und melde dich mit deinem Google-Konto an.\n"
                        "2. Lege ein Google-Cloud-Projekt an oder wähle eines und **aktiviere die Abrechnung** - die "
                        "kostenlose Stufe darf für Nutzer im EWR, in UK und der Schweiz nicht genutzt werden.\n"
                        "3. **Get API key** → **Create API key** für dieses Projekt.\n"
                        "4. `/yatb keys add` ausführen, **Google Gemini** wählen und den Key einfügen.",
        "guide_mistral": "1. Melde dich bei console.mistral.ai an.\n"
                         "2. Wähle unter **Billing** einen bezahlten Tarif (der kostenlose Experiment-Tarif darf deine "
                         "Daten zum Training nutzen).\n"
                         "3. **API Keys** → **Create new key**.\n"
                         "4. `/yatb keys add` ausführen, **Mistral** wählen und den Key einfügen.",
        "guide_groq": "1. Melde dich bei console.groq.com an.\n"
                      "2. Empfohlen: Unter **Settings → Data Controls** die Datenspeicherung abschalten (Zero Data Retention).\n"
                      "3. **API Keys** → **Create API Key**.\n"
                      "4. `/yatb keys add` ausführen und **Groq** wählen. Der kostenlose Tarif hat niedrige Limits "
                      "(etwa 30 Anfragen pro Minute).",
        "guide_novita": "1. Melde dich bei novita.ai an und lade Guthaben auf (es gibt keinen kostenlosen Tarif).\n"
                        "2. Unter **Key Management** einen Key anlegen.\n"
                        "3. `/yatb keys add` ausführen und **Novita** wählen.",
        "guide_google_translate": "1. Öffne console.cloud.google.com und lege ein Projekt an.\n"
                                  "2. Aktiviere die **Cloud Translation API** (ein Rechnungskonto ist nötig; die ersten "
                                  "500.000 Zeichen pro Monat sind kostenlos).\n"
                                  "3. **APIs & Dienste → Anmeldedaten → Anmeldedaten erstellen → API-Schlüssel**, danach "
                                  "den Schlüssel auf die Cloud Translation API beschränken.\n"
                                  "4. `/yatb keys add` ausführen und **Google Translate** wählen.",
        "guide_azure": "1. Lege in portal.azure.com eine **Translator**-Ressource an (Tarif **F0** = 2 Mio. Zeichen pro "
                       "Monat kostenlos).\n"
                       "2. Öffne **Schlüssel und Endpunkt**: Kopiere **Schlüssel 1** und **Standort/Region** "
                       "(z. B. westeurope).\n"
                       "3. `/yatb keys add` ausführen, **Azure Translator** wählen und Key und Region eintragen.",
        "status_title": "🛠️ YATB Systemstatus",
        "bridge_kind_mismatch": "❌ Foren lassen sich nur mit Foren verbinden, Textkanäle nur mit Textkanälen. Die Bridge `{bridge}` enthält schon die andere Art - bitte nimm einen anderen Bridge-Namen.",
        "forum_tags_hint": "ℹ️ Damit YATB fehlende Tags in {channel} selbst anlegen kann, braucht es dort das Recht **Kanäle verwalten**. Ohne dieses Recht werden nur gleichnamige Tags zugeordnet.",
        "rep_tags_no_permission": "⚠️ YATB konnte in {channel} keinen passenden Tag anlegen: Dort fehlt das Recht **Kanäle verwalten**.",
        "rep_tags_full": "⚠️ {channel} hat schon 20 Tags (Discord-Limit) - ein passender Tag konnte nicht angelegt werden.",
        "channels_title": "📊 Kanäle auf diesem Server",
        "channels_total": "**{total} von {limit}** Kanälen belegt ({pct} %) - **{free}** noch frei.\\nDiscord erlaubt 500 Kanäle pro Server; Kategorien zählen mit, Threads nicht.",
        "channels_types": "Nach Art",
        "channels_type_text": "💬 Text",
        "channels_type_news": "📢 Ankündigung",
        "channels_type_voice": "🔊 Sprache",
        "channels_type_stage": "🎙️ Bühne",
        "channels_type_forum": "🗂️ Forum",
        "channels_type_media": "🖼️ Medien",
        "channels_type_category": "📁 Kategorien",
        "channels_bridges": "YATB-Bridges",
        "channels_bridges_value": "**{channels}** Kanäle in **{bridges}** Bridges. Eine weitere Sprache für alle Bridges braucht **{per_lang}** neue Kanäle.",
        "channels_warn": "Nur noch **{free}** Kanäle frei. Entferne ungenutzte Kanäle, bevor du neue Sprachen hinzufügst.",
        "status_chain": "🔗 Übersetzungskette (in dieser Reihenfolge)",
        "stage_active": "aktiv", "stage_paused": "⏸ pausiert (Fehler)", "stage_exhausted": "🚫 Limit erreicht",
        "status_stats_name": "📊 Server-Statistik",
        "status_stats": "• Bridges: `{b}`\n• Kanäle: `{c}`\n• Nachrichten-Tracker: `{m}`",
        "bad_bridge": "Bitte einen Bridge-Namen angeben.",
        "channel_added": "✅ Kanal {channel} zur Bridge `{bridge}` hinzugefügt ({lang}).",
        "channel_removed": "🗑️ Kanal {channel} aus der Bridge `{bridge}` entfernt.",
        "channel_not_found": "⚠️ Kanal {channel} gehört zu keiner Bridge auf diesem Server.",
        "no_bridges": "Auf diesem Server gibt es noch keine Bridges. Nutze `/yatb bridge add`.",
        "bridges_title": "🌐 Bridges auf diesem Server",
        "list_field": "Bridge: {bridge}",
        "list_footer": "Engines: {engines} | Log: {log}",
        "perms_missing": "⚠️ Fehlende Rechte in {channel}: {perms}. Die Bridge funktioniert evtl. erst, wenn sie vergeben sind.",
        "send_forbidden": "⚠️ Mir fehlen Rechte, um Nachrichten nach {channel} zu übertragen (Webhooks verwalten, "
                          "Öffentliche Threads erstellen, Nachrichten in Threads senden).",
        "rep_added": "➕ **Bridge:** {user} hat {channel} zu `{bridge}` ({lang}) hinzugefügt.",
        "rep_removed": "🗑️ **Bridge:** {user} hat {channel} ({lang}) aus `{bridge}` entfernt.",
        "form_pick_intro": "Für welchen Dienst ist der Key? Wähle ihn unten aus - danach öffnet sich ein Formular genau für "
                           "diesen Dienst. Nur dort wird der Key eingegeben.",
        "form_pick_provider": "Übersetzungsdienst wählen",
        "form_title_add": "{provider}-Key hinzufügen",
        "form_title_edit": "{provider}-Key bearbeiten",
        "form_key": "API-Key", "form_key_desc": "Wird verschlüsselt gespeichert und nie wieder angezeigt.",
        "form_label": "Name (optional)", "form_label_desc": "Zur Unterscheidung deiner Keys, z. B. Haupt-Key",
        "form_tier": "Tarif", "form_tier_desc": "Free: Es gelten die Limits des Anbieters. Paid: Monatsbudget.",
        "tier_free": "Free (kostenlos)", "tier_paid": "Paid (bezahlt)",
        "form_budget": "Monatsbudget (nur bei Paid)",
        "form_budget_desc": "z. B. 8,50 EUR oder 10 USD. Leer = Standard ({default}).",
        "form_budget_invalid": "❌ Budget nicht verstanden. Bitte z. B. `8,50 EUR` oder `10 USD` eingeben (max. 1000). Es "
                               "wurde nichts geändert.",
        "form_region": "Azure-Region", "form_region_desc": "Standort deiner Translator-Ressource, z. B. westeurope",
        "form_limit": "Verbrauchslimit", "form_limit_desc": "An = stoppt an Tarifgrenze oder Budget (empfohlen)",
        "keys_no_crypto": "🔒 Keys können noch nicht gespeichert werden: Der Betreiber hat den Master-Schlüssel nicht eingerichtet.",
        "keys_region_needed": "❌ Azure braucht die Region deiner Translator-Ressource (z. B. `westeurope`). Es wurde nichts gespeichert.",
        "keys_bad_format": "❌ Das sieht nicht nach einem API-Key aus (16-512 Zeichen, keine Leerzeichen). Es wurde nichts gespeichert.",
        "keys_rejected": "❌ {provider} hat diesen Key abgelehnt ({status}). Er wurde nicht gespeichert.",
        "keys_unverified": "⚠️ {provider} war nicht erreichbar, um den Key zu prüfen ({status}); er wurde trotzdem gespeichert.",
        "keys_saved": "🔑 Key gespeichert: {desc}. Er liegt verschlüsselt vor und wird nie wieder angezeigt.",
        "keys_updated": "✅ Einstellungen gespeichert: {desc}",
        "keys_duplicate": "ℹ️ Dieser Key ist auf diesem Server bereits hinterlegt: {desc}.",
        "keys_too_many": "❌ Dieser Server hat bereits {max} Keys. Bitte zuerst einen entfernen (`/yatb keys remove`).",
        "keys_shared_warn": "⚠️ Dieser Key wird bereits auf einem anderen Server genutzt. Verbrauch und Limit werden gemeinsam gezählt.",
        "keys_paid_only": "ℹ️ {provider} wird nur mit bezahlten Keys (Abrechnung aktiv) genutzt, der Key wurde als **Paid** gespeichert.",
        "keys_error": "❌ Der Key konnte nicht verarbeitet werden. Es wurde nichts geändert.",
        "keys_none": "Auf diesem Server sind keine API-Keys hinterlegt. Hinzufügen mit `/yatb keys add`.",
        "keys_title": "🔑 API-Keys dieses Servers",
        "keys_limit": "Limit", "keys_budget": "Budget", "keys_on": "an", "keys_off": "aus",
        "keys_shared_tag": " · 🔗 auch auf anderem Server genutzt",
        "keys_usage_line": "  ↳ Monat: {month} · heute: {today}",
        "keys_not_found": "⚠️ Dieser Key wurde auf diesem Server nicht gefunden.",
        "keys_removed": "🗑️ Key entfernt: {desc}.",
        "keys_confirm_remove": "⚠️ Den Key {desc} entfernen? Übersetzungen mit diesem Key enden sofort.",
        "keys_limit_on": "✅ Verbrauchslimit für {desc} eingeschaltet.",
        "keys_limit_off": "⚠️ Verbrauchslimit für {desc} ausgeschaltet.",
        "keys_confirm_limit_off": "⚠️ **Verbrauchslimit für {desc} ausschalten?**\nDer Bot nutzt den Key dann auch über die "
                                  "Free-/Tarif-Grenzen hinaus. Eventuelle Kosten beim Anbieter liegen **in deiner Verantwortung**.",
        "rep_key_added": "🔑 {user} hat einen API-Key hinzugefügt: {desc}.",
        "rep_key_edited": "ℹ️ {user} hat die Einstellungen von {desc} geändert.",
        "rep_key_removed": "🗑️ {user} hat einen API-Key entfernt: {desc}.",
        "rep_key_limit": "ℹ️ {user} hat das Verbrauchslimit von {desc} auf **{state}** gestellt.",
        "rep_order_set": "🔀 {user} hat die Reihenfolge der Übersetzungsdienste geändert: {order}.",
        "rep_order_reset": "🔀 {user} hat die Reihenfolge der Übersetzungsdienste auf den Standard zurückgesetzt: {order}.",
        "usage_warn": "⚠️ Key {desc}: **{pct} %** des Monatslimits verbraucht ({usage}).",
        "usage_full": "🚫 Key {desc}: Monatslimit erreicht ({usage}). Der Key pausiert bis zum 1. des nächsten Monats "
                      "(00:00 UTC) oder bis sein Limit erhöht wird; übersetzt wird mit der nächsten Engine.",
        "usage_full_nolimit": "⚠️ Key {desc}: Monatslimit überschritten ({usage}). Das Limit ist für diesen Key "
                              "ausgeschaltet, er wird weiter genutzt - eventuelle Kosten liegen beim Admin.",
        "key_rejected": "🔑 {provider} hat den API-Key dieses Servers abgelehnt ({status}). Der Key wird 1 Stunde "
                        "übersprungen, es übersetzt die nächste Engine. Prüfen mit `/yatb keys list` oder ersetzen mit "
                        "`/yatb keys add`.",
        "model_missing": "⚠️ {provider}: Das Modell `{model}` ist nicht verfügbar (vom Anbieter entfernt oder umbenannt). Es "
                         "wird 6 Stunden übersprungen; der Betreiber muss die Anbieter-Konfiguration anpassen.",
        "provider_spend_limit": "⚠️ {provider} meldet, dass das monatliche Ausgabenlimit oder Guthaben des Kontos zu diesem "
                                "Key aufgebraucht ist. Der Key pausiert und wird stündlich neu versucht; übersetzt wird mit "
                                "der nächsten Engine. Hebe das Limit in der Konsole von {provider} an.",
        "provider_quota": "⚠️ {provider} meldet, dass das Kontingent des Keys dieses Servers aufgebraucht ist. Der Key "
                          "pausiert bis 00:00 UTC; übersetzt wird mit der nächsten Engine.",
        "report_channel_set": "📢 Log-Kanal auf {channel} gesetzt.",
        "report_channel_cleared": "📢 Log-Kanal ausgeschaltet.",
        "rep_channel_set": "ℹ️ {channel} ist jetzt der Log-Kanal.",
        "confirm_reset": "⚠️ Das löscht **alle** Bridges, Keys und Einstellungen dieses Servers. Fortfahren?",
        "confirm_uninstall": "⚠️ Das löscht **alle** Daten dieses Servers und der Bot verlässt ihn. Fortfahren?",
        "reset_done": "🔄 Alle Bridges, Webhook-Zuordnungen, Keys und Einstellungen dieses Servers wurden gelöscht.",
        "uninstall_done": "👋 Alle Daten wurden gelöscht. YATB verlässt nun den Server.",
        "privacy_title": "🔒 Deine Übersetzungs-Privatsphäre",
        "privacy_state_standard": "Aktuelle Einstellung: **Standard**.",
        "privacy_state_local": "Aktuelle Einstellung: **Nur lokal**.",
        "privacy_standard_name": "Standard",
        "privacy_standard_desc": "Beste Qualität. Deine Nachrichten können an die Übersetzungsdienste gehen, die die Admins "
                                 "des Servers hinterlegt haben (z. B. KI-Anbieter, Google, Azure). Die Admins wählen diese Dienste aus.",
        "privacy_local_name": "Nur lokal",
        "privacy_local_desc": "Deine Nachrichten bleiben beim Bot: Sie werden nur von LibreTranslate auf seinem eigenen "
                              "Server übersetzt und nie an KI-Anbieter, Google oder Azure geschickt - auch nicht als "
                              "Kontext für die Übersetzungen anderer. Die Qualität ist geringer. Gilt auf allen Servern mit YATB.",
        "privacy_btn_standard": "Standard nutzen", "privacy_btn_local": "Nur lokal nutzen",
        "user_help_title": "ℹ️ YATB - Übersetzungs-Bridges",
        "user_help_desc": "Dieser Server verbindet Kanäle verschiedener Sprachen. Wenn du in einem davon schreibst, postet "
                          "YATB eine Übersetzung in den anderen unter deinem Namen. Antworten, Bearbeitungen, Löschungen und "
                          "Reaktionen werden übernommen. YATB speichert keine Nachrichtentexte - nur, welche Nachricht zu welcher "
                          "Übersetzung gehört (7 Tage).",
        "user_help_tags_name": "Was das Kürzel hinter dem Namen bedeutet",
        "user_help_tags": "`[AI]` KI-Anbieter · `[Google]` Google Translate · `[Azure]` Azure Translator · "
                          "`[Libre]` LibreTranslate (lokal) · `[Raw]` nicht übersetzt (kein Dienst verfügbar)",
        "user_help_privacy_name": "Deine Wahl",
        "user_help_privacy": "Mit `/yatb-user privacy` kannst du festlegen, dass deine Nachrichten nur lokal übersetzt und "
                             "nie an Dritte geschickt werden.",
    },
}

# Beschreibungen der Befehle/Optionen: englischer Text -> Übersetzung (Namen der Befehle bleiben englisch)
COMMANDS: Dict[str, Dict[str, str]] = {
    "de": {
        "Add a channel to a translation bridge": "Kanal zu einer Übersetzungs-Bridge hinzufügen",
        "Add an API key (entered in a private form, stored encrypted)": "API-Key hinzufügen (privates Formular, verschlüsselt gespeichert)",
        "Change the settings of a key (the key itself is never shown)": "Einstellungen eines Keys ändern (der Key selbst wird nie angezeigt)",
        "Choose who may translate your messages (applies on all servers)": "Festlegen, wer deine Nachrichten übersetzen darf (gilt auf allen Servern)",
        "Delete all bridges, keys and settings of this server": "Alle Bridges, Keys und Einstellungen dieses Servers löschen",
        "Delete all data of this server and make the bot leave": "Alle Daten dieses Servers löschen und den Bot entfernen",
        "How to get an API key for a translation service": "So bekommst du einen API-Key für einen Übersetzungsdienst",
        "Key to change": "Zu ändernder Key",
        "Key to remove": "Zu entfernender Key",
        "Language of this channel": "Sprache dieses Kanals",
        "List all bridges of this server": "Alle Bridges dieses Servers anzeigen",
        "Log channel for notifications": "Log-Kanal für Benachrichtigungen",
        "Manage this server's API keys (stored encrypted)": "API-Keys dieses Servers verwalten (verschlüsselt gespeichert)",
        "Manage translation bridges": "Übersetzungs-Bridges verwalten",
        "Name of the bridge (channels with the same name are connected)": "Name der Bridge (Kanäle mit gleichem Namen werden verbunden)",
        "Remove a channel from its bridge": "Kanal aus seiner Bridge entfernen",
        "Remove an API key from this server": "API-Key von diesem Server entfernen",
        "Set the channel for notifications (usage warnings, key problems, changes)": "Kanal für Benachrichtigungen festlegen (Verbrauch, Key-Probleme, Änderungen)",
        "Setup guide and overview of all commands": "Anleitung und Übersicht aller Befehle",
        "Show this server's API keys and their usage (never the keys themselves)": "API-Keys dieses Servers und ihren Verbrauch anzeigen (nie die Keys selbst)",
        "Text channel": "Text-Kanal",
        "Translation chain, usage and service health of this server": "Übersetzungskette, Verbrauch und Zustand der Dienste dieses Servers",
        "How many channels this server uses (Discord limit: 500)": "Wie viele Kanäle dieser Server belegt (Discord-Limit: 500)",
        "Text, forum or media channel": "Text-, Forum- oder Medien-Kanal",
        "Translation service": "Übersetzungsdienst",
        "Turn off the notification channel": "Benachrichtigungskanal ausschalten",
        "What this bot does with your messages": "Was dieser Bot mit deinen Nachrichten macht",
        "YATB settings for your own messages": "YATB-Einstellungen für deine eigenen Nachrichten",
        "YATB translation bridges (admin settings)": "YATB Übersetzungs-Bridges (Admin-Einstellungen)",
    },
}

try:  # maschinell übersetzte Sprachen (fr/es/it/ru/nl) - optional, damit ein Fehler dort den Bot nie stoppt
    from locales_mt import COMMANDS_MT, MESSAGES_MT
    for _lang, _table in MESSAGES_MT.items():
        MESSAGES.setdefault(_lang, {}).update(_table)
    for _lang, _table in COMMANDS_MT.items():
        COMMANDS.setdefault(_lang, {}).update(_table)
except ImportError:
    pass


def _lang(locale: Any) -> str:
    return str(locale).split("-")[0].lower() if locale else "en"


def get_text(locale: Any, key: str, **kwargs: Any) -> str:
    """Text in der Sprache des Discord-Clients/Servers, sonst Englisch. Fehlt ein Platzhalter, wird Englisch genutzt."""
    template = MESSAGES.get(_lang(locale), {}).get(key) or MESSAGES["en"].get(key, key)
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        return MESSAGES["en"].get(key, key).format(**kwargs)


def command_text(locale: Any, english: str) -> Optional[str]:
    """Übersetzte Befehlsbeschreibung oder None (dann zeigt Discord den englischen Text)."""
    return COMMANDS.get(_lang(locale), {}).get(english)
