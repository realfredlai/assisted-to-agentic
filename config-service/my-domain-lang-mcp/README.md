# my-domain-lang-mcp

An MCP server (stdio transport) that exposes the config-service **domain language** to a coding agent — so it can ask what `Configuration` means in this codebase instead of assuming. Built on the official [MCP Python SDK](https://py.sdk.modelcontextprotocol.io/) v2.

## Tools

| Tool | Purpose |
|---|---|
| `lookup_term` | Definition, aliases, **warnings**, source files and docs for one term. Resolves id, display name, or alias, case-insensitively (`application` / `Application` / `app`). |
| `get_related_terms` | The relationships pointing *out* of a term, each with the target's id and display name. Directed — incoming edges are excluded. |
| `list_domain_areas` | The distinct areas the domain is partitioned into. Cheap orientation, and the right first call. |
| `validate_knowledge_graph` | Reports edges pointing at nodes that do not exist. `{valid, issues}`. |

The `warnings` field is the point of the whole thing: several terms mean something specific here (this `User` is **not** `django.contrib.auth`'s user and cannot log in; `Application` is not a Django app).

Read-only. The graph is rebuilt from YAML by `make knowledge-import`, which needs Django and PyYAML — neither of which this venv has.

## How it reaches the graph

It **imports `backend/knowledge_graph.storage` directly** through a `sys.path` seam pointing at the sibling `backend/`. That module is pure stdlib (sqlite3 + json + pathlib), so no Django and no PyYAML are involved, and the server gets typed objects instead of re-parsed subprocess stdout.

This project is a **peer of `backend/` and `frontend/`**, not part of the Django project: its own venv, its own dependencies, and `manage.py` knows nothing about it. (It briefly lived under `backend/`; the nesting was never what made the import work.)

The database path defaults to `config-service/knowledge.db` and is overridden by **`KNOWLEDGE_DB`** — which is how the tests point at temporary graphs without touching the real file. If the graph has not been built, every tool returns an actionable error naming the path and the fix rather than a bare sqlite failure (and, importantly, without leaving an empty database file behind).

## Error channels

The MCP spec (Tools § Error Handling) splits failures in two, and this server keeps them apart — mcp 2.0.0 does not:

| Situation | Answer | Why |
|---|---|---|
| Unknown tool name | JSON-RPC **`-32602`** | Protocol error: the request itself is malformed. |
| Missing or wrong-typed arguments | JSON-RPC **`-32602`** | Same category, per spec. |
| Unknown domain term | `isError: true` + text naming the term and suggesting `list_domain_areas` | Tool *execution* error: actionable feedback the model can self-correct on. |
| Graph not built | `isError: true` + the path and `make knowledge-import` | Same — the call was well-formed; the environment isn't ready. |

mcp 2.0.0 answers the first two with `isError` results, which blurs "you called this wrong" into "the tool ran and failed". `spec_conformance_guard` in `main.py` restores the spec behaviour. It validates against each tool's own `input_schema`, and since the SDK does not coerce arguments, it rejects exactly what the SDK would have rejected — only the channel changes.

**Caveat:** the SDK marks its middleware signature "provisional — expected to change before v2 is final". `mcp==2.0.0` is pinned exactly; re-verify the guard at any deliberate upgrade.

## Layout

```
my-domain-lang-mcp/
├── requirements.txt        # mcp, pytest, pytest-asyncio, mypy — exact pins
├── pytest.ini              # *_test.py discovery, asyncio_mode = auto
├── venv/                   # created by `make mcp-install` (gitignored)
└── stdio_server/
    ├── main.py             # build_server(): tool registration + the guard
    ├── tools.py            # the seams + the four tool implementations
    ├── main_test.py        # protocol layer: handshake, error channels, raw stdio
    └── tools_test.py       # tool behaviour, against temporary graphs
```

The folder name is hyphenated so it cannot be a Python package; the package is `stdio_server` (leaving room for an `http_server` sibling).

## Setup, test, run

From `config-service/` — **no Docker needed**, this never touches Postgres:

```bash
make mcp-install   # create venv + install dependencies
make mcp-test      # 18 tests
make mcp-run       # run the server on stdio
```

The test suite is hermetic: it builds its own graphs in-process with `Storage` and never shells out to `manage.py`, so it passes with Docker stopped and `knowledge.db` absent.

## Poking it with MCP Inspector

```bash
cd my-domain-lang-mcp
npx @modelcontextprotocol/inspector -- venv/bin/python -m stdio_server.main
```

Try `lookup_term` with `app`, then `get_related_terms` with `application`, then `lookup_term` with something that does not exist to see the actionable error.

## Registering in a coding agent

```json
{
  "mcpServers": {
    "my-domain-lang": {
      "command": "/absolute/path/to/my-domain-lang-mcp/venv/bin/python",
      "args": ["-m", "stdio_server.main"],
      "cwd": "/absolute/path/to/my-domain-lang-mcp"
    }
  }
}
```

Run `make knowledge-import` once first, or every tool will (correctly) report that the graph has not been built.
