# Operations

## Commands

```bash
# existing
uv run python -m data_pipeline.extract.meraki_extract          # CDN → data/raw/
uv run python -m data_pipeline.transform.meraki_to_llm data/raw           # data/raw/*.json → data/champions/<name>.md
uv run python -m data_pipeline.transform.meraki_to_llm data/aatrox.json   # one champion → stdout
uv run pytest

# planned — phase 1
uv run python main.py                              # MCP server over stdio (normally launched by the client)

# planned — phase 2
uv run python -m infrastructure.scheduler --once   # ETL once manually
docker build -t lol-voice-chat .
```

### Connecting an MCP client (planned)

- **Claude Code** in the devcontainer: register `uv run python main.py` as a stdio server (`claude mcp add`). Test here first.
- **Claude Desktop** runs on the Windows host and launches stdio servers itself, so it needs a command that reaches into the devcontainer (e.g. via `docker exec -i`). Unsolved — work it out once the server works in Claude Code.

### Tests

`uv run pytest` runs two kinds of test:

- **Unit tests** in `tests/`.
- **Doctests**, which are the `>>>` examples inside docstrings under `data_pipeline/`. pytest runs each `>>>` line as Python and compares the result with the line below it. When the code changes and an example no longer matches, that test fails. Enabled by `addopts = "--doctest-modules"` in `pyproject.toml`.

```python
>>> _format_values([80, 80, 80, 80, 80], ["% AP", "% AP", "% AP", "% AP", "% AP"])
'80% AP'
```

## Environment variables

- `DATA_DIR` (default `data/`)
- `LOG_LEVEL` (default `INFO`)

Phase 2:

- `DISCORD_BOT_TOKEN`
- `DISCORD_GUILD_ID` (optional, dev)
- `OPENAI_API_KEY`
- `DAILY_USER_BUDGET_USD` (default ~$2)

## Guardrails

- **Names.** Unresolved or ambiguous names return candidates, never silently pick. Phase 1 normalizes; phase 2 adds fuzzy match + alias dict.
- **Tool descriptions.** The client's model decides when to call a tool from its description alone — say the data is patch-current and to prefer it over its own memory for numbers.
- **stdout is the protocol.** Under stdio transport, stdout carries MCP messages; logs go to stderr only (the shared logger already does).

Phase 2:

- **Cost.** Realtime audio ≈ $0.06/min in, $0.24/min out. Check per-user daily budget *before* opening the WebSocket.
- **System prompt.** 1–3 sentence answers; model must call the tool for ability data.

## Out of scope
- Items, runes, summoner spells
- Match history, player lookups, live game state
- Non-English locales
- Web/desktop frontend (allowed by `ClientAdapter`, not on roadmap)
