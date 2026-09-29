---
paths:
  - "data_pipeline/**/*.py"
---

# Examples as doctests

When a function transforms data and its behavior isn't obvious from the name, add one or two input → output examples to its docstring in `>>>` form, below the summary line. pytest runs them (`--doctest-modules`), so a stale example fails the build. Use literal, readable inputs — write the list out rather than `[""] * 5` or `*[15] * 16`.

Doctests are only collected under `data_pipeline/` (`testpaths` in `pyproject.toml`); extending this rule to another folder means adding it there too.
