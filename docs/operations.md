# Operations

## Commands

```bash
# existing
uv run python -m data_pipeline.extract.meraki_extract          # CDN → data/raw/
uv run python -m data_pipeline.transform.meraki_to_llm data/raw           # data/raw/*.json → data/champions/<key>.md + index.json
uv run python -m data_pipeline.transform.meraki_to_llm data/aatrox.json   # one champion → stdout
uv run pytest
uv run python main.py                                                     # MCP server over stdio (normally launched by the client)

# planned — phase 2
uv run python -m infrastructure.scheduler --once   # ETL once manually
docker build -t lol-voice-chat .
```

### Connecting an MCP client

- **Claude Code** in the devcontainer: register the server once (local scope, private to you). The `claude` CLI isn't on PATH here; it is bundled with the VS Code extension at `~/.vscode-server/extensions/anthropic.claude-code-<version>-linux-x64/resources/native-binary/claude`. Then check `/mcp` in a new session.

  ```bash
  claude mcp add lol-champions -- uv run --directory /workspaces/lol-voice-chat python main.py
  ```

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

- **Names.** `champion_name` is an enum of display names; the server accepts exact matches only and returns an error otherwise, never a guess. Both phases.
- **Tool descriptions.** The client's model decides when to call a tool from its description alone — say the data is patch-current and to prefer it over its own memory for numbers.
- **stdout is the protocol.** Under stdio transport, stdout carries MCP messages; logs go to stderr only (`main.py` configures that before building the server).

Phase 2:

- **Cost.** Realtime audio ≈ $0.06/min in, $0.24/min out. Check per-user daily budget *before* opening the WebSocket.
- **System prompt.** 1–3 sentence answers; model must call the tool for ability data.

## Out of scope
- Items, runes, summoner spells
- Match history, player lookups, live game state
- Non-English locales
- Web/desktop frontend (allowed by `ClientAdapter`, not on roadmap)
