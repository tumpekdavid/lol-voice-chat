# lol-voice-chat

Discord bot that answers spoken LoL champion-ability questions in voice chat via the OpenAI Realtime API, fed by an ETL that renders Meraki CDN data to markdown. One process, ~$5/mo VPS, sub-second turn latency.

## Code standards

**Top-down ordering.** Public, high-level functions first; the private helpers they call below them. Callers before callees, so a reader meets the API before the details. Same for classes: public methods, then private. Private names take a leading underscore.

**Descriptive names.** Spell things out — `champion_name`, not `cn`; `format_values`, not `fmt_vals`. Applies to functions as well as variables. Existing abbreviations get renamed when their file is touched for other reasons, not before.

**Type hints always.** Every parameter and return type, on public and private alike. Modern syntax — `list[str]`, `dict | None`.

**Comments must earn their place.** A one-line docstring on every public function saying what it does — no `Args:`/`Returns:` blocks, the signature already carries that. Inline comments only where the code is genuinely non-obvious: a workaround, a non-local constraint, a reason. Never narrate what the next line plainly says.

**Import boundaries.** `core/` must not import from `adapters/` or `infrastructure/`. Nothing outside `infrastructure/` and `main.py` imports `data_pipeline/`.

`ruff` enforces the mechanical half (docstrings, annotations, naming, imports): `uv run ruff check .`

## Read on demand

- Runtime shape, directory layout, wiring abstractions, where code goes → [docs/architecture.md](docs/architecture.md)
- Considering an alternative tech/library/pattern, or need the rationale for a locked-in choice → [docs/decisions.md](docs/decisions.md)
- Commands, env vars, Docker, cost/budget guardrails, out-of-scope check → [docs/operations.md](docs/operations.md)
