# Graphify Installation Guide

[Graphify](https://github.com/Graphify-Labs/graphify) is an AI coding assistant
skill that turns a folder of code, docs, papers, images, or videos into a
queryable knowledge graph. It ships on PyPI as `graphifyy` (the CLI command
itself is `graphify` — see the naming note below).

## Installation

### Prerequisites

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) (recommended) or [`pipx`](https://pypa.github.io/pipx/)

### Step 1 — install the CLI

```bash
uv tool install graphifyy      # recommended: isolated env
# or
pipx install graphifyy
```

> **Naming note:** the PyPI package is `graphifyy` (double-y) — other
> `graphify*` packages on PyPI are not affiliated. The installed command is
> still `graphify`.

If `graphify` isn't found right after install, the tool bin dir
(`~/.local/bin`) probably isn't on `PATH` yet:

```bash
uv tool update-shell   # or: pipx ensurepath
```

then open a new terminal.

### Step 2 — register the assistant skill

```bash
graphify install
```

This registers a `/graphify` skill with your AI coding assistant (Claude
Code by default). To scope the install to the current repo instead of your
user profile:

```bash
graphify install --project
```

Project-scoped installs write under `.claude/skills/graphify/SKILL.md` (or
the equivalent path for other assistants) and print a `git add` hint for the
files it creates.

## Quick start

```bash
graphify install
```

Then, inside your AI assistant:

```
/graphify .
```

That produces three files under `graphify-out/`:

- `graph.html` — an interactive force-directed graph, open in any browser
- `GRAPH_REPORT.md` — key concepts, surprising connections, suggested questions
- `graph.json` — the full graph, queryable without re-reading source files

## Why LLM Wiki users might want this

LLM Wiki already builds a persistent, interlinked markdown knowledge base
under `wiki/` (see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)). Graphify
is a complementary, optional tool for a different use case: a one-shot,
visual graph of a *codebase or raw source folder* — useful when you want to
explore `src/llm_wiki/` itself, or a `raw/` folder of PDFs and notes, as a
force-directed graph before deciding what to ingest into the wiki.

- **Code parsing is fully local.** Code is parsed with tree-sitter AST —
  deterministic, no LLM calls, nothing leaves your machine. Docs, PDFs,
  images, and video use your assistant's model (or a configured API key) for
  a semantic pass.
- **Every edge is labeled.** Connections are tagged `EXTRACTED` (explicit in
  the source) or `INFERRED` (resolved by graphify).
- **Not a vector index.** No embeddings or vector store — a real graph you
  traverse, distinct from LLM Wiki's `wiki search --backend qmd` retrieval
  layer.

## Optional extras

Install only what you need, e.g.:

```bash
uv tool install "graphifyy[pdf]"    # PDF extraction
uv tool install "graphifyy[mcp]"    # MCP stdio server
uv tool install "graphifyy[all]"    # everything
```

See the [upstream README](https://github.com/Graphify-Labs/graphify) for the
full extras table (office docs, video/audio transcription, Neo4j/FalkorDB
push, SQL/Postgres introspection, and more).

## Troubleshooting

**`graphify: command not found`** — the tool bin dir isn't on `PATH` yet;
run `uv tool update-shell` (or `pipx ensurepath`) and open a new terminal.

**`ModuleNotFoundError: No module named 'graphify'` after `pip install`** —
avoid plain `pip install` if possible. The skill resolves Python at runtime
from `graphify-out/.graphify_python`; if that points to a different
environment than where `pip` installed the package, resolution breaks.
`uv tool install` and `pipx install` isolate the package and avoid this.

## Resources

- [Graphify GitHub](https://github.com/Graphify-Labs/graphify)
- [Graphify on PyPI](https://pypi.org/project/graphifyy/)
