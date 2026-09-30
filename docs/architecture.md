# Architecture

## Phases

- **Phase 1 — MCP server (current).** An MCP server exposes champion ability data as tools to LLM clients (Claude Code, Claude Desktop). Validates the data, name resolution and tool contract without voice.
- **Phase 2 — Discord voice bot.** Adds push-to-talk voice via the OpenAI Realtime API on top of the same `core/`. The Realtime model calls the same `get_champion_abilities` tool.

## Runtime shape

**Phase 1** — two pieces, run separately:

- **ETL** — run by hand when a patch drops: extract fetches the Meraki CDN into `data/raw/`, transform renders `data/champions/<name>.md`. Commands in [operations.md](operations.md).
- **MCP server** — `main.py`, stdio transport. The client launches it as a subprocess on demand; nothing is hosted. Tools:
  - `get_champion_abilities(champion_name)` — full markdown for one champion, or candidates if the name doesn't resolve.
  - `list_champions()` — every available champion name.

**Phase 2** — one long-running process:

- **ETL** — APScheduler polls Riot `versions.json` ~30 min; on a new patch it runs extract + transform. Last processed patch in `data/state.txt`.
- **Bot** — discord.py + `discord-ext-voice-recv` receives PTT frames → OpenAI Realtime (`gpt-realtime`) WebSocket. The model calls `get_champion_abilities(champion_name)`.

Stack: Python 3.12, uv, official MCP Python SDK (`mcp`). Phase 2 adds discord.py, OpenAI Realtime, APScheduler.

## Target directory layout

```
core/                   # domain logic + interfaces (no I/O imports)
  repository.py         # ChampionRepository protocol
  query_handler.py      # get_champion_abilities / list_champions + name resolution
  champion.py           # phase 2 if needed
  data_source.py        # phase 2: ChampionDataSource protocol
  voice_session.py      # phase 2: VoiceSession protocol
  client_adapter.py     # phase 2: ClientAdapter protocol
  budget.py             # phase 2: per-user daily cost cap
adapters/
  mcp_server.py         # MCP tool definitions over query_handler
  discord_bot.py        # phase 2: DiscordBotAdapter (PTT receive, voice send)
  openai_realtime.py    # phase 2: OpenAIRealtimeSession
infrastructure/
  filesystem_repo.py    # FilesystemChampionRepository — reads data/champions/
  meraki_source.py      # phase 2: MerakiDataSource — ChampionDataSource over data_pipeline/
  scheduler.py          # phase 2: APScheduler wiring (polls versions.json, invokes the ETL)
data_pipeline/          # ETL, sibling tree — owns fetch + render, imports nothing from core/
  extract/              # meraki_extract.py — CDN → data/raw/<name>.json
  transform/            # meraki_to_llm.py — data/raw → data/champions/<name>.md
  shared/               # logging_config.py
data/raw/               # one <name>.json per champion (extract output)
data/champions/         # one <name>.md per champion (transform output)
data/state.txt          # phase 2: last processed patch
main.py                 # composition root — phase 1: builds the repo + handler, runs the MCP server
```

`data_pipeline/` is a sibling of the ports-and-adapters tree, not a layer inside it. The server reaches ETL output through `ChampionRepository` (the markdown files), never by importing `data_pipeline` — only `infrastructure/` and `main.py` may do that.

`data/aatrox.json` and `data/alistar.json` are test fixtures.

## Abstraction boundaries

Interfaces in `core/` speak in domain terms (champion, patch, ability), are wired via constructor injection. Adding a new concrete impl must require **zero** changes to callers — if not, the seam is wrong.

| Interface            | Implementation                   | Future swap                  |
| -------------------- | -------------------------------- | ---------------------------- |
| `ChampionRepository` | `FilesystemChampionRepository`   | `SqliteChampionRepository`   |
| `ChampionDataSource` | phase 2: `MerakiDataSource`      | Meraki + Wiki blend          |
| `VoiceSession`       | phase 2: `OpenAIRealtimeSession` | Claude / local Whisper stack |
| `ClientAdapter`      | phase 2: `DiscordBotAdapter`     | Desktop / web                |

The MCP server is not a `ClientAdapter` — it has no audio or session loop, it only maps MCP tool calls onto `query_handler`. It gets no interface of its own.

**Do not abstract:** logging, file I/O primitives, MCP SDK details (keep inside `adapters/mcp_server.py`), APScheduler internals, Discord protocol details (keep inside `DiscordBotAdapter`), the pure markdown render function.
