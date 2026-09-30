# Operations

## Commands

```bash
# existing
uv run python -m data_pipeline.extract.meraki_extract          # CDN → data/raw/
uv run python -m data_pipeline.transform.meraki_to_llm data/raw           # data/raw/*.json → data/champions/<name>.md
uv run python -m data_pipeline.transform.meraki_to_llm data/aatrox.json   # one champion → stdout
uv run pytest

# planned
uv run python main.py                              # bot + scheduler
uv run python -m infrastructure.scheduler --once   # ETL once manually
docker build -t lol-voice-chat .
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

- `DISCORD_BOT_TOKEN`
- `DISCORD_GUILD_ID` (optional, dev)
- `OPENAI_API_KEY`
- `DAILY_USER_BUDGET_USD` (default ~$2)
- `DATA_DIR` (default `data/`)

## Guardrails

- **Cost.** Realtime audio ≈ $0.06/min in, $0.24/min out. Check per-user daily budget *before* opening the WebSocket.
- **Names.** Fuzzy match + alias dict; ambiguity returns candidates, never silently picks.
- **System prompt.** 1–3 sentence answers; model must call the tool for ability data.

## Out of scope
- Items, runes, summoner spells
- Match history, player lookups, live game state
- Non-English locales
- Web/desktop frontend (allowed by `ClientAdapter`, not on roadmap)
