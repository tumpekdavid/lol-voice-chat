# Architecture

## Runtime shape — two components, one process

- **ETL** — APScheduler polls Riot `versions.json` ~30 min; on a new patch it fetches the Meraki CDN and writes `data/champions/<name>.md`. Last processed patch in `data/state.txt`.
- **Bot** — discord.py + `discord-ext-voice-recv` receives PTT frames → OpenAI Realtime (`gpt-realtime`) WebSocket. The model calls `get_champion_abilities(name)`, which reads the markdown file.

Stack: Python 3.12, uv, discord.py, OpenAI Realtime, APScheduler.

## Target directory layout

```
core/                   # domain logic + interfaces (no I/O imports)
  champion.py
  repository.py         # ChampionRepository protocol
  data_source.py        # ChampionDataSource protocol
  voice_session.py      # VoiceSession protocol
  client_adapter.py     # ClientAdapter protocol
  query_handler.py      # get_champion_abilities tool + alias/fuzzy resolution
  budget.py             # per-user daily cost cap
adapters/
  discord_bot.py        # DiscordBotAdapter (PTT receive, voice send)
  openai_realtime.py    # OpenAIRealtimeSession
infrastructure/
  filesystem_repo.py    # FilesystemChampionRepository
  meraki_source.py      # MerakiDataSource — thin ChampionDataSource adapter over data_pipeline/
  scheduler.py          # APScheduler wiring (polls versions.json, invokes the ETL)
data_pipeline/          # ETL, sibling tree — owns fetch + render, imports nothing from core/
  extract/src/          # meraki_extract.py — CDN → data/raw/<name>.json
  transform/src/        # meraki_to_llm.py — data/raw → data/champions/<name>.md
  shared/               # logging_config.py
data/raw/               # one <name>.json per champion (extract output)
data/champions/         # one <name>.md per champion (transform output)
data/state.txt          # last processed patch
main.py                 # composition root
```

`data_pipeline/` is a sibling of the ports-and-adapters tree, not a layer inside it. The bot reaches ETL output through `ChampionRepository` (the markdown files), never by importing `data_pipeline` — only `infrastructure/` and `main.py` may do that.

## Where existing code goes
- `data_pipeline/transform/src/meraki_to_llm.py` → stays put; gains a directory mode that writes `data/champions/<name>.md`.
- `data_pipeline/transform/src/detect_meta.py` → delete (one-off exploration, also references wrong-case `data/Aatrox.json`).
- `data/aatrox.json`, `data/alistar.json` → keep as test fixtures.

## Abstraction boundaries

Interfaces in `core/` speak in domain terms (champion, patch, ability), are wired via constructor injection. Adding a new concrete impl must require **zero** changes to callers — if not, the seam is wrong.

| Interface              | Today                          | Future swap                  |
| ---------------------- | ------------------------------ | ---------------------------- |
| `ChampionRepository`   | `FilesystemChampionRepository` | `SqliteChampionRepository`   |
| `ChampionDataSource`   | `MerakiDataSource`             | Meraki + Wiki blend          |
| `VoiceSession`         | `OpenAIRealtimeSession`        | Claude / local Whisper stack |
| `ClientAdapter`        | `DiscordBotAdapter`            | Desktop / web                |

**Do not abstract:** logging, file I/O primitives, APScheduler internals, Discord protocol details (keep inside `DiscordBotAdapter`), the pure markdown render function.

## Open contradictions to resolve
1. **Transform output target.** `meraki_to_llm.py` takes one file and writes to stdout; extract now produces ~170 files in `data/raw/`, so transform needs a directory mode writing `data/champions/<name>.md`. Next change in the pipeline.
