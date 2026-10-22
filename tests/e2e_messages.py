"""
Eigene Testnachrichten für tests/e2e_bridge.py.

Nach dem Vorbild der Benchmark-Testsets (bench/testset_chat.json, testset_ann.json) geschrieben, aber frei
erfunden: gleicher Ton (Allianz-Chat eines Weltraum-MMOs, offizielle Ankündigungen), gleiche Längenverteilung
(kurz/mittel/lang/sehr lang), typische Eigenheiten (Allianz-Tags wie [NOVA], Abkürzungen, Tippfehler, gemischtes
Deutsch/Englisch, "Commanders", "LLAP", Durchstreichungen) - ohne echte Spielernamen oder Nachrichten.

Platzhalter, die zur Laufzeit ersetzt werden: {ME} (Tester-Bot-ID), {ROLE} (Rollen-ID), {CHANNEL} (Kanal-ID),
{EMOJI} (echtes Server-Emoji :yatb: des Test-Servers).

Code: ```-Blöcke und Inline-`…` sind auf den Servern mal Formatierung (Text -> übersetzen), mal echter Code
(-> unverändert) - mit und ohne Sprachangabe. Der Bot muss das selbst erkennen. Die Erwartung steht pro Nachricht
im optionalen 4. Feld: {"blocks": [...], "inline": [...]} mit "translate"/"keep" in Reihenfolge des Vorkommens.
"""

T, K = "translate", "keep"

# (Name, Art, Text[, Erwartung]) - Art: "chat", "ann" (Ankündigung), "markdown" (gezielte Formatierungsprobe)
MESSAGES = [
    # ---------------- Chat: kurz ----------------
    ("chat_short_armada", "chat", "who's online for the armada at 20 ST?"),
    ("chat_short_laugh", "chat", "lol RIFT got wrecked again 😂"),
    ("chat_short_thanks", "chat", "ty for the help @[NOVA] Vexx, much appreciated"),
    ("chat_short_afk", "chat", "afk 10 min, brb"),
    ("chat_short_tc", "chat", "is TC on today or tmrw??"),

    # ---------------- Chat: mittel ----------------
    ("chat_mid_pass", "chat",
     "Each Battle Pass is 50$ now and a season still runs 3 months.\nNot sure thats worth it tbh."),
    ("chat_mid_refinery", "chat",
     "Can someone explain how the new isogenite refinery works? I keep getting the wrong chests and "
     "the tooltip doesnt help at all."),
    ("chat_mid_roe", "chat",
     "Reminder: no hitting miners in our home system. Thats against the ROE we all agreed on, "
     "repeat offenders will be reported."),
    ("chat_mid_recruit", "chat", "[KHAN] has 4 open spots, G6+ preferred. DM me if interested 👍"),

    # ---------------- Chat: lang ----------------
    ("chat_long_share", "chat",
     "if its a shared territory between 2 alliances there are three systems that give access. "
     "1 can be captured by alliance A, the second by alliance B and the third goes to whoever is not "
     "defending that week.\n\nThat way nobody has to fight over it every single time and the smaller "
     "members still get their chests."),
    ("chat_long_vote", "chat",
     "The exact same proposal cant be put to a vote again right away.\n\n"
     "But if the current proposal is a set of points (like the ROE) and one of them changes through another "
     "vote, then the whole set gets updated. Thats how we handled it last season too."),
    ("chat_long_mixed", "chat",
     "Facts/Fakten:\n1) @[RIFT] Kael and @[NOVA] Mirra are admirals (sie sind Admirals)\n"
     "2) The war has been going on for weeks and small players suffer (die Kleinen leiden)\n"
     "3) Nobody wants another reset\n\n**note:** this is just my view, not the official alliance position"),

    # ---------------- Chat: sehr lang ----------------
    ("chat_very_long_opinion", "chat",
     "Thanks for the long and well written post, but Im not changing my stance. There DONT have to be "
     "6 alliances in the rotation around the capital. 4 are enough for a good rotation, and those 4 "
     "should be picked by power ranking, not by who shouts the loudest in this channel.\n\n"
     "> If several alliances are close in power, a vote decides.\n\n"
     "That part of the proposal is fine imo. What Im against is forcing alliances that cant even hold "
     "their own territory into the rotation. It just means more hits on miners, more drama and more "
     "people quitting. We saw exactly that in season 4 and nobody wants to go back there.\n\n"
     "So my vote stays NO unless the power ranking part gets added. gg"),

    # ---------------- Code-Blöcke als Formatierung (Inhalt muss übersetzt werden) ----------------
    ("chat_codeblock_results", "chat",
     "After some headaches I got all votes counted\n\n"
     "```\nPLAYER COUNCIL - VOTING RESULTS\n\nTotal: 1,214 votes\n\n"
     " 1. Kael [S12]            - 231 votes (19.0%)\n"
     " 2. Mirra (S40 Ops70)     - 198 votes (16.3%)\n"
     " 3. Vexx                  - 120 votes ( 9.9%)\n\nThe top 3 join the council next month.\n```", {"blocks": [T]}),
    ("chat_codeblock_rules", "chat",
     "Pinned for the new members:\n```\nALLIANCE RULES\n1. Be respectful to everyone.\n"
     "2. Join the armada when you are online.\n3. Never hit allied miners.\n```", {"blocks": [T]}),

    # ---------------- Ankündigungen ----------------
    ("ann_mid_issue", "ann",
     "We are aware of an issue where the Haven event store shows the wrong prices. "
     "This is only a display issue, the correct amount is charged."),
    ("ann_mid_fixed", "ann",
     "~~The missing Dilithium rewards from the Voyage event are being investigated.~~ "
     "The rewards have been sent to all affected players and a compensation chest is on its way."),
    ("ann_long_maintenance", "ann",
     "@everyone\n\nCommanders!\n\nWe wanted to remind you about our upcoming maintenance for US and EU servers.\n\n"
     "Update 96.2 will be released during the maintenance on <t:1893456000:F>.\n"
     "Downtime: roughly 2 hours.\nCeasefire peace shields: 8 hours.\n\n"
     "Once the maintenance is complete we strongly recommend updating your game client to avoid technical issues.\n\n"
     "LLAP\nThe Dev Team"),
    ("ann_long_rewards", "ann",
     "@everyone\n\nCommanders,\n\nStarting next week we are changing the rewards of the **Interstellar Dominance** "
     "event for players of Operations level 61+.\n\n**What changes:**\n"
     "- Operations level 66+ now earn Haven structure shards (50 shards for 1st place)\n"
     "- Vanguard Prisms drop in every run\n- ~~Weekly cap of 3 runs~~ the weekly cap is removed\n\n"
     "Full details are in the [patch notes](https://example.com/patch-96-2).\n\nLLAP\nThe Dev Team"),
    ("ann_very_long_event", "ann",
     "# 🚀 Galactic Clash Event\n@everyone\n\nCommanders,\n\nThe **Galactic Clash** begins on <t:1893456000:f> "
     "and runs for seven days. Alliances compete for control of the central sectors, and every captured sector "
     "grants bonus loot to all members, including those who were offline during the capture.\n\n"
     "## How it works\n- Each alliance can declare war on up to **two** sectors per day\n"
     "- Captured sectors must be defended for 4 hours before they count\n"
     "- Peace shields do *not* protect stations inside contested sectors\n\n"
     "## Rewards\n1. 1st place: 500 Paragon Recruit Tokens and an exclusive hull skin\n"
     "2. 2nd place: 300 Paragon Recruit Tokens\n3. Every participant: 50 Paragon Recruit Tokens\n\n"
     "> Please read the [event rules](https://example.com/galactic-clash) before declaring war. "
     "Breaking the rules can lead to removal from the event.\n\n"
     "## Schedule\n- Day 1-2: sector declarations open, no attacks yet\n"
     "- Day 3-6: open warfare, captured sectors award points every hour\n"
     "- Day 7: final hour, all points are doubled until the event closes\n\n"
     "We know many of you asked for an event that rewards the whole alliance and not only the top players. "
     "This is our first attempt, so please share your feedback in <#{CHANNEL}> after the event ends. "
     "We will read every comment and adjust the rules for the next run if something does not feel fair, "
     "especially for smaller alliances and players who can only play in the evening.\n\n"
     "-# Times are shown in your local time zone.\n\nLLAP\nThe Dev Team"),

    # ---------------- Markdown-Proben (alle Discord-Formatierungen) ----------------
    ("md_inline_styles", "markdown",
     "**Double XP weekend** starts *Friday*! Grab your ***boosters***, __don't forget__ to ~~skip~~ **read** "
     "the __*event rules*__ and _stay tuned_. ||The secret boss spawns at midnight.||"),
    ("md_headers_subtext", "markdown",
     "# Season 12: Interstellar Dominance\n## What's new\n### Balance changes\n"
     "The Paragon Recruit Tokens now drop twice as often.\n-# Patch 12.1 · subject to change"),
    ("md_lists", "markdown",
     "Before the update, please:\n- Finish your active missions\n- Collect your daily rewards\n"
     "  - Alliance chest\n  - Supply crates\n* Log out safely\n\nAfter the update:\n"
     "1. Restart the game\n2. Claim the compensation\n3. Report bugs in <#{CHANNEL}>"),
    ("md_quotes", "markdown",
     "> The Mak'ala's Crucible event has been extended by 24 hours.\n> Rewards stay the same.\n\n"
     "Thanks for your patience, Commanders!\n\n>>> Known issue: some players cannot open the shop.\n"
     "We are working on a fix."),
    ("md_code", "markdown",
     "Use `/redeem SPACE2026` in the chat window. If it fails, send us this:\n"
     "```json\n{\"error\": \"0x8007\", \"server\": \"EU-3\", \"retry\": true}\n```", {"blocks": [K], "inline": [K]}),
    ("md_code_untagged", "markdown",
     "If the bot crashes, run this on the server:\n```\ndocker compose restart bot\ndocker logs -f discord-bot\n```\n"
     "and `check the log channel afterwards` please.", {"blocks": [K], "inline": [T]}),
    ("md_code_tagged_prose", "markdown",
     "Heads up Commanders:\n```fix\nIMPORTANT: Maintenance starts tomorrow at noon. Please log out before.\n```",
     {"blocks": [T]}),
    ("md_links", "markdown",
     "Read the full [patch notes](https://example.com/patch-12) and vote in our "
     "[community poll](<https://example.com/poll>). FAQ: <https://example.com/faq> or https://example.com/status"),
    ("md_mentions_emoji_time", "markdown",
     "@everyone <@{ME}> and <@&{ROLE}> please meet in <#{CHANNEL}> at <t:1893456000:F> "
     "(<t:1893456000:R>). Use </yatb info:1234567890123456789> for help. "
     "{EMOJI} 🚀 see you there"),
    ("md_escapes", "markdown",
     "Fuel costs 5\\*3 credits, \\*this is not italic\\*, \\_neither is this\\_ and \\`this is not code\\`."),
    # Regel-Posts wie in #server-rules: Zitate mit Überschriften, verschachtelte Zitate, Trennlinien, Fußnoten-Marker
    ("md_rules_footnotes", "markdown",
     "**All Commanders** must follow these rules while in the alliance.\n"
     "# ------------------------------\n"
     "> ## 1. Fleet Conduct\n"
     "> ### 1.1: Teamwork\n"
     "> - Please be **Helpful** and **Patient** with new members at all times.\n"
     "> - Leaving an armada mid-fight **Is Not** acceptable.\n"
     "> ### 1.2: Screenshots\n"
     "> - Crop out player names from ***(1)*** **Every** screenshot before posting it.\n"
     ">   -  ***(1)*** Only exception: reports of an ROE breach, which go into a private ticket.\n"
     "# ------------------------------\n"
     "> ## 2. Support\n"
     "> > - For **Help From An Officer**, **Feedback** or to **Report A Problem**, open a ticket in <#{CHANNEL}> .\n"
     "> > - We answer as soon as we can.\n"
     "# ------------------------------"),
    ("md_rules_warnings", "markdown",
     "# -------- **Penalties** --------\n"
     "> - Every breach is reviewed by the officer team.\n"
     "> - The ***(2)*** **Penalty** depends on the **Severity**, how **Often** it happened and the **Warnings** of the "
     "**Last 60 Days**.\n"
     ">   - ***(2)*** i.e. how long and how strict the penalty will be.\n"
     "## Warning Levels\n"
     "> - 1 Warning = Reminder.\n"
     "> - 2 Warnings = Mute.\n"
     "> - 3 Warnings = Kick.\n"
     "\n"
     "***Officers may update these rules at any time. You will be told when they do. ***"),
]

# Für die Synchron-Tests (Antwort, Edit, Löschen)
REPLY_TEXT = "Thanks, see you there Commanders!"
EDIT_TEXT = "**Double XP weekend** starts *Saturday*! Grab your boosters."
EDIT_PROBE = "**Double XP weekend** starts *Friday*! Grab your boosters."
DELETE_PROBE = "This message will be deleted again in a moment (delete sync test)."
REACT_PROBE = "React to this if you are in for the armada tonight (reaction sync test)."

# Für den Limit-Test: eine lange Nachricht (passt nicht mehr in den Rest) und viele kurze
LIMIT_LONG = (
    "Long post incoming, sorry. After three seasons in this alliance I want to share what worked and what did not. "
    "The armadas worked well whenever at least eight people showed up on time, and they failed every time we started "
    "late or without a clear target. Territory capture was mostly fine, but we lost too many sectors on weekends "
    "because nobody was online to defend. The mining rules were the biggest problem: half of the members never read "
    "the ROE, so we kept hitting allied miners and had to pay compensation. For next season I suggest three things. "
    "First, one armada lead per time zone, so EU and US both have someone in charge. Second, a weekend defense "
    "rotation where every member signs up for at least one slot. Third, a short quiz on the ROE before anyone gets "
    "access to the territory channels. None of this is complicated, it just needs a few people who actually do it. "
    "If you agree, react with a thumbs up and I will put it on the agenda for the next officer meeting. "
    "If you disagree, tell me why, I am happy to change the plan. Thanks for reading all of this, see you in the "
    "next armada and good luck in the arena this week, Commanders."
)
LIMIT_SHORT = [
    "Ready for the raid tonight?", "Who has spare fuel cells?", "Alliance meeting starts in ten minutes.",
    "Great job on the defense yesterday!", "Can someone help me with the station upgrade?",
    "The new event looks really fun.", "Remember to collect your daily rewards.", "Good luck in the arena, everyone!",
    "Does anyone know when the patch drops?", "Thanks for the reinforcements!", "Let's push the next sector together.",
    "I just unlocked the new hull skin.", "Watch out for pirates near the gate.", "See you all tomorrow, Commanders.",
    "Who wants to join the mining run?", "Anyone selling dilithium?", "Armada in five, be ready.",
    "Nice shot on that hostile!", "Shields up, incoming fleet.", "Back online, what did I miss?",
    "Who is leading the next armada?", "Daily goals done, logging off.", "That boss was brutal lol.",
    "Need two more for the territory push.", "gg everyone, well played.",
]
