# Operations

## Commands

```bash
# existing
uv run --project data_pipeline/transform python data_pipeline/transform/src/meraki_to_llm.py data/aatrox.json

# planned
uv run python main.py                              # bot + scheduler
uv run python -m infrastructure.scheduler --once   # ETL once manually
docker build -t lol-voice-chat .
uv run pytest
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
