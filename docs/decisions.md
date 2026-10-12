# Locked-in decisions (rationale)

If you're tempted to suggest one of the alternatives below, read first.

## Both phases

- **MCP server first, voice bot second.** The MCP tool is the same `get_champion_abilities` the Realtime model would call, so `core/` is built once and voice is added later as another adapter. Phase 1 tests data quality and name resolution against a real model for ~$0 (runs locally on the Claude subscription, no VPS, no audio billing) before taking on Discord voice receive and Realtime — the riskiest, costliest part. The value over the model's own knowledge is patch-current numbers.

- **Meraki Analytics CDN, not Riot Data Dragon.** Data Dragon ability text is templated/unparseable with incorrect numbers. Meraki scrapes the LoL Wiki with clean, accurate values.

- **Filesystem, one `.md` per champion. No database.** ~170 records, ~1.5 MB total, single writer (ETL), single reader, always keyed by exact name, wholesale-replaced per patch. Filesystem is faster, zero infra, git-diffable per patch. If we ever need to query *inside* the data → SQLite, not Mongo.

- **File names are lowercased Meraki champion keys, not display names.** `monkeyking.md` is Wukong (key `MonkeyKing`), `nunu.md` is Nunu & Willump. Keys survive renames and are what the CDN URLs use. The transform also writes `index.json` (display name → markdown file name) from Meraki's `name` field — no hand-kept mapping. The repository serves only the display names in that index; they become the tool's `champion_name` enum, and `query_handler` never sees keys or files. Code says "key", never "ID": Meraki's `id` is a number (62), and Riot's Data Dragon calls `MonkeyKing` the `id`.

- **Function calling, not RAG.** Tool returns the full markdown for one champion (~1–5k tokens, median ~2k). No vector DB. One champion per call; matchup questions use parallel tool calls, not a list parameter.

- **Closed vocabulary: `champion_name` is an enum, not free text.** The tool schema lists every display name, so the model maps whatever the user said (`wu kong`, `kaisa`, `the void bug`) onto an exact name using its own knowledge — better at that than any matching we'd write. The server does an exact lookup; a name outside the enum (clients may not enforce it) returns an error telling the model to pick a listed name. Costs ~600 tokens per request (170 names, ~1.7k chars), cached as part of the tool definitions — about a third of one tool result. Rejected: free text + normalization/substring/`difflib` resolution (most of the code, and can silently pick the wrong champion); a separate `list_champions` tool (same tokens plus a round trip, and models skip it and guess).

## Phase 1

- **Official MCP Python SDK (`mcp`), stdio transport.** Claude Code and Claude Desktop launch stdio servers as a subprocess — no hosting, ports or auth. Streamable HTTP only if a remote client ever needs it.

- **ETL run by hand, no scheduler.** The server is launched on demand by the client, not long-lived, so there is no process to host a scheduler. Patches land every ~2 weeks; running extract + transform manually is fine.

## Phase 2

- **OpenAI Realtime API (`gpt-realtime`), not chained STT → LLM → TTS.** Speech-to-speech in one socket. Chained pipelines add 800 ms+ per turn — unacceptable for voice.

- **Same enum, no alias map or fuzzy match.** The speech-to-speech model hears the name itself and picks from the enum, so there is no separate transcript to mangle. Add matching only if Realtime testing shows it picking wrong names.

- **In-process APScheduler, not GitHub Actions or host cron.** Bot runs 24/7, coupling ETL to bot uptime is fine. Schedule lives in code, ships in the Docker image, redeploys identically anywhere. Chosen for portability.

- **Push-to-talk, not VAD.** Discord only transmits voice frames while the PTT key is held — clean audio segment per question, no voice-activity detection needed.

- **Discord receive lib.** `discord.py`'s built-in receive was removed in 2.0+. Use `discord-ext-voice-recv`. (If we ever go Node: `@discordjs/voice` has more mature receive.)
