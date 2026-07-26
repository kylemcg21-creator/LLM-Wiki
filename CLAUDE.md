# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`llm-wiki` is the **toolkit** (Python package + CLI + MCP server) implementing Andrej
Karpathy's LLM Wiki pattern: a compounding knowledge base where an LLM agent maintains
structured, interlinked markdown instead of re-deriving answers from raw chunks each time.

**This repo is not itself a populated wiki.** It ships the toolkit under `src/llm_wiki/`,
a scaffold template under `src/llm_wiki/scaffold/` (what `wiki init` generates for users),
and four populated example wikis under `examples/` used for tests, demos, and CI. There is
no `wiki/` or `raw/` at the repo root, so CLI commands run from a clone always need
`--root <path>` (or `LLM_WIKI_ROOT=<path>`) pointed at one of the `examples/*` dirs.

```bash
wiki --root examples/demo search "memex"
# or
LLM_WIKI_ROOT=examples/demo wiki lint
make demo-search   # shortcut for the line above
```

## Commands

```bash
pip install -e ".[dev,mcp]"        # editable install with dev + MCP extras

pytest -v                           # run tests
pytest -v tests/test_lint.py        # single file
pytest -v tests/test_lint.py::test_broken_link_detected   # single test

ruff check src tests                # lint
ruff check src tests --fix          # lint, autofix
ruff format src tests               # format
ruff format --check src tests       # format check (CI mode)
make lint                           # ruff check + ruff format --check + pytest (the CI gate)
make format                         # ruff format + ruff check --fix

python scripts/sync_agents.py       # copy root AGENTS.md -> scaffold + all examples/*/AGENTS.md
                                     # required after any AGENTS.md edit; CI fails if out of sync
make sync-agents                    # same, via Makefile

make demo / demo-search / demo-lint / demo-ingest   # wiki --root examples/demo <cmd>
./scripts/demo-walkthrough.sh       # scripted end-to-end CLI tour (also run in CI)
```

Coverage gate: `pytest.ini_options` in `pyproject.toml` sets `--cov-fail-under=80` and omits
`*/scaffold/*` from coverage. Ruff config: line-length 100, target py310, rules `E, F, I, UP`.

## Architecture

### Two audiences for the same code

- **Toolkit code** (`src/llm_wiki/*.py`) — read-mostly operations: search, lint, expand,
  stats, backlinks/graph, scaffolding. Ships as the `wiki` CLI (`click`) and as an MCP
  server (`python -m llm_wiki.mcp_server`, optional `[mcp]` extra) exposing the same
  operations as tools (`wiki_search`, `wiki_expand`, `wiki_lint`, `wiki_list`, `wiki_stats`,
  `wiki_ingest_status`, `wiki_recent_log`, `wiki_backlinks`, `wiki_graph`, `wiki_new`).
- **`AGENTS.md`** — the *write* side of the system. It's the schema and operating
  procedure a coding agent (Claude Code, Cursor, etc.) follows inside a generated wiki
  project to actually ingest sources and write wiki pages. The toolkit deliberately never
  writes wiki content itself (except `wiki new`, which scaffolds an empty page from
  `templates/`) — that's the agent's job, guided by `AGENTS.md`.

### Module map (`src/llm_wiki/`)

- `paths.py` — resolves the project root. `find_root()` walks up from cwd (or reads
  `LLM_WIKI_ROOT`) looking for `wiki/index.md` + `AGENTS.md` as the root signature. Nearly
  every other module takes a root/wiki-dir `Path` rather than doing its own discovery.
- `links.py` — the wikilink engine: parses `[[Obsidian-style]]` and markdown links, builds
  a case-insensitive slug index (matches by stem *and* full relative path), resolves links
  (returns no match on collisions rather than guessing — see `is_ambiguous_link`), and
  derives backlinks (`inbound_links`) and the full link graph (`export_graph`). Path
  resolution (`resolve_page`) is hardened against traversal outside the wiki root.
- `search.py` — BM25 ranking over wiki markdown (title/heading term boosts), plus an
  optional `qmd` backend that shells out to the external `qmd` CLI for hybrid search when a
  wiki outgrows BM25 recall. `search_wiki_with_backend()` is the dispatch point.
- `lint.py` — the health-check engine; largest module. Validates structure (required
  files), broken/ambiguous wikilinks, frontmatter (`type`, dates), raw↔source coverage,
  orphan pages, index gaps, and unfiled contradictions (detected via keyword markers like
  "contradicts"/"supersedes" — see `CONTRADICTION_MARKERS`). Issues carry a severity
  (`error`/`warning`/`info`) and category; see `docs/LINT.md` for the full catalog. CLI/MCP
  both filter on severity+category and CI uses `--severity error` as its quality gate.
- `ingest.py` — computes raw↔source coverage (`pending`/`ingested`/`orphan`/`incomplete`)
  by cross-referencing `raw/` against `wiki/sources/*.md` frontmatter.
- `expand.py` — extracts a table of contents and single sections from a page, so an agent
  can read one heading instead of a whole file (token economy for context windows).
  `stats.py` — page/raw/log counts; also parses `wiki/log.md` entries.
- `new_page.py` — renders a page from `templates/{entity,concept,source,answer}.md`.
- `bootstrap.py` — implements `wiki init`: copies `src/llm_wiki/scaffold/` into a target
  dir, template-substitutes `{{project_name}}`/`{{date}}`/`{{project_root}}`, seeds
  `wiki/log.md` with an `init` entry, optionally runs `git init`. Resolves the scaffold via
  `importlib.resources` for installed packages, falling back to the local `scaffold/` dir
  for editable installs.
- `watch.py` — polls `raw/` for files without a matching source page.
- `cli.py` — the `wiki` Click group wiring all of the above together; every subcommand
  resolves its root via `_get_root()` (the `--root` option, or `find_root()` autodetection).
- `mcp_server.py` — FastMCP wrapper exposing the same operations as MCP tools, returning
  JSON strings (including `{"error": ...}` payloads for invalid inputs instead of raising).

### `AGENTS.md` sync (important when touching agent instructions)

Root `AGENTS.md` is the single canonical source for wiki-maintenance conventions
(page types, frontmatter schema, ingest/query/lint procedures, wikilink conventions).
`scripts/sync_agents.py` copies it verbatim to `src/llm_wiki/scaffold/AGENTS.md` and to
each `examples/*/AGENTS.md`. **Never hand-edit the copies** — edit the root file, then run
`python scripts/sync_agents.py`. A pre-commit hook (`.pre-commit-config.yaml`) runs this
automatically on `AGENTS.md` changes, and CI (`ci.yml`) independently verifies sync via
`git diff --exit-code` after re-running the script — an unsynced copy fails CI.

### Examples as fixtures, not docs

`examples/{demo,research,reading,business}/` are real, populated wikis (`raw/`, `wiki/`,
`AGENTS.md`) used three ways: manual exploration (open as an Obsidian vault), CLI/MCP
smoke-testing (`make demo-*`, `./scripts/demo-walkthrough.sh`), and a CI quality gate — each
must `wiki lint --severity error` clean, or CI fails.

### `src/llm_wiki/scaffold/`

The literal template `wiki init` copies into new projects: `AGENTS.md`, `CLAUDE.md`
(a short pointer file, not this one), `templates/`, empty `wiki/` subdirs, and MCP configs
for Cursor/Claude Code/Windsurf/OpenCode. It is excluded from coverage
(`tool.coverage.run.omit`) and kept in sync with root `AGENTS.md` as described above.
