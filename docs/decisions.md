# Locked-in decisions (rationale)

If you're tempted to suggest one of the alternatives below, read first.

## Both phases

- **MCP server first, voice bot second.** The MCP tool is the same `get_champion_abilities` the Realtime model would call, so `core/` is built once and voice is added later as another adapter. Phase 1 tests data quality and name resolution against a real model for ~$0 (runs locally on the Claude subscription, no VPS, no audio billing) before taking on Discord voice receive and Realtime — the riskiest, costliest part. The value over the model's own knowledge is patch-current numbers.

- **Meraki Analytics CDN, not Riot Data Dragon.** Data Dragon ability text is templated/unparseable with incorrect numbers. Meraki scrapes the LoL Wiki with clean, accurate values.

- **Filesystem, one `.md` per champion. No database.** ~170 records, ~1.5 MB total, single writer (ETL), single reader, always keyed by exact name, wholesale-replaced per patch. Filesystem is faster, zero infra, git-diffable per patch. If we ever need to query *inside* the data → SQLite, not Mongo.

- **File names are Riot champion IDs, not display names.** `monkeyking.md` is Wukong, `nunu.md` is Nunu & Willump. IDs survive renames and match Riot/Meraki sources. The transform also writes `index.json` (display name → ID) from Meraki's `name` field — no hand-kept mapping. The repository serves only the names in that index; `query_handler` maps what the model typed onto one of them and never sees IDs or markdown.

- **Function calling, not RAG.** Tool returns the full markdown for one champion (~1–5k tokens, median ~2k). No vector DB. Unresolved or ambiguous names return candidates — never silently pick.

## Phase 1

- **Official MCP Python SDK (`mcp`), stdio transport.** Claude Code and Claude Desktop launch stdio servers as a subprocess — no hosting, ports or auth. Streamable HTTP only if a remote client ever needs it.

- **Name normalization, not fuzzy matching.** Typed names from an LLM are near-correct, so lowercase + strip spaces and punctuation (`Kha'Zix` → `khazix`) resolves them; misses return close candidates. `list_champions` lets the model self-correct. Aliases and fuzzy matching arrive with voice, where speech-to-text mangles names.

- **ETL run by hand, no scheduler.** The server is launched on demand by the client, not long-lived, so there is no process to host a scheduler. Patches land every ~2 weeks; running extract + transform manually is fine.

## Phase 2

- **OpenAI Realtime API (`gpt-realtime`), not chained STT → LLM → TTS.** Speech-to-speech in one socket. Chained pipelines add 800 ms+ per turn — unacceptable for voice.

- **Alias map + fuzzy match in the handler.** `kha`, `kha'zix`, `khazix` → `khazix.md`. Needed for speech-to-text errors.

- **In-process APScheduler, not GitHub Actions or host cron.** Bot runs 24/7, coupling ETL to bot uptime is fine. Schedule lives in code, ships in the Docker image, redeploys identically anywhere. Chosen for portability.

- **Push-to-talk, not VAD.** Discord only transmits voice frames while the PTT key is held — clean audio segment per question, no voice-activity detection needed.

- **Discord receive lib.** `discord.py`'s built-in receive was removed in 2.0+. Use `discord-ext-voice-recv`. (If we ever go Node: `@discordjs/voice` has more mature receive.)
