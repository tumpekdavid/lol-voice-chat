# lol-voice-chat

Discord bot that joins a voice channel, listens for PTT audio, and answers spoken LoL champion-ability questions via OpenAI Realtime API. Goal: sub-second turn latency. One process, ~$5/mo VPS.

## Two components, one process
- **ETL** — APScheduler polls Riot `versions.json` ~30 min, on new patch fetches Meraki CDN, writes `data/champions/<name>.md`. Last patch in `state.txt`.
- **Bot** — discord.py + `discord-ext-voice-recv` receives PTT frames → OpenAI Realtime (`gpt-realtime`) WebSocket. Model calls `get_champion_abilities(name)` which reads the markdown file.

## Stack
Python 3.12, uv, discord.py, OpenAI Realtime, APScheduler.

## Current state (mostly TODO)
Only `data_pipeline/transform/src/meraki_to_llm.py` exists — pure Meraki-JSON → markdown renderer (stdout). HTTP fetch, scheduler, state file, Discord, Realtime, alias map, cost cap are all unbuilt.

## Locked-in choices — do not silently revert
Meraki (not Data Dragon) · filesystem (not DB) · Realtime (not chained STT/TTS) · function calling (not RAG) · in-process APScheduler (not GH Actions / cron) · PTT (not VAD).

## Hard rules
- `core/` must not import from `adapters/` or `infrastructure/`.
- Check per-user daily budget **before** opening the Realtime socket. Audio ≈ $0.30/min combined; an open mic burns $50+/day.
- Voice answers 1–3 sentences. Model must call the tool for any ability data — never answer from training knowledge.

## Read on demand
- Adding files, wiring abstractions, deciding where code goes → [docs/architecture.md](docs/architecture.md)
- Considering an alternative tech/library/pattern, or need full rationale for a locked choice → [docs/decisions.md](docs/decisions.md)
- Commands, env vars, Docker, out-of-scope check → [docs/operations.md](docs/operations.md)
