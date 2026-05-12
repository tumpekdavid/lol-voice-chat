# Locked-in decisions (rationale)

If you're tempted to suggest one of the alternatives below, read first.

- **Meraki Analytics CDN, not Riot Data Dragon.** Data Dragon ability text is templated/unparseable with incorrect numbers. Meraki scrapes the LoL Wiki with clean, accurate values.

- **Filesystem, one `.md` per champion. No database.** ~165 records, ~1–2 MB total, single writer (ETL), single reader (bot), always keyed by exact name, wholesale-replaced per patch. Filesystem is faster, zero infra, git-diffable per patch. If we ever need to query *inside* the data → SQLite, not Mongo.

- **OpenAI Realtime API (`gpt-realtime`), not chained STT → LLM → TTS.** Speech-to-speech in one socket. Chained pipelines add 800 ms+ per turn — unacceptable for voice.

- **Function calling, not RAG.** Tool returns the full markdown for one champion. No vector DB. Ambiguous names return `{error: "ambiguous", candidates: [...]}` — never silently pick. Alias map in the handler (`kha`, `kha'zix`, `khazix` → `khazix.md`).

- **In-process APScheduler, not GitHub Actions or host cron.** Bot runs 24/7, coupling ETL to bot uptime is fine. Schedule lives in code, ships in the Docker image, redeploys identically anywhere. Chosen for portability.

- **Push-to-talk, not VAD.** Discord only transmits voice frames while the PTT key is held — clean audio segment per question, no voice-activity detection needed.

- **Discord receive lib.** `discord.py`'s built-in receive was removed in 2.0+. Use `discord-ext-voice-recv`. (If we ever go Node: `@discordjs/voice` has more mature receive.)
