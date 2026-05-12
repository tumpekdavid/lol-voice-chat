# Architecture

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
  meraki_source.py      # MerakiDataSource (HTTP + markdown render)
  scheduler.py          # APScheduler wiring
data/champions/         # one <name>.md per champion (ETL output)
data/state.txt          # last processed patch
main.py                 # composition root
```

## Where existing code goes
- `data_pipeline/transform/src/meraki_to_llm.py` → render function inside `infrastructure/meraki_source.py`.
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
1. **Layout collision.** `.devcontainer/devcontainer.json` provisions `data_pipeline/{extract,load,transform}` via `uv init`. Target above is ports-and-adapters. Pick one before adding new files; recommend dropping the postCreateCommand and using a single package.
2. **Transform output target.** `meraki_to_llm.py` writes to stdout; ETL needs to write to `data/champions/<name>.md`. Trivial change on move.
