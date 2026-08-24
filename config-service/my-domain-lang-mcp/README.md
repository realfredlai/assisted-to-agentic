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

## Testing it with MCP Inspector

Build the graph first, or every tool will (correctly) report that it has not been built:

```bash
cd config-service && make knowledge-import
```

Then run everything below from **this directory** (`config-service/my-domain-lang-mcp/`) — [`inspector.json`](inspector.json) uses paths relative to it.

> **Why a config file rather than a bare command?** The Inspector's argument parser consumes `-m` as one of its own flags, so `npx @modelcontextprotocol/inspector -- venv/bin/python -m stdio_server.main` launches Python with no module; it then reads JSON-RPC frames on stdin and tries to execute them as source (`NameError: name 'true' is not defined`) before timing out. Any server command containing a flag hits this. `--config`/`--server` is the form that works. The file is read-only to the Inspector (the writable one is `--catalog`), so it is safe to commit — and it doubles as the registration snippet below.

### Web UI

```bash
npx @modelcontextprotocol/inspector --config inspector.json --server my-domain-lang
```

It prints a URL of the form `http://127.0.0.1:6274?MCP_INSPECTOR_API_TOKEN=…` — open **that exact URL**; the token is required.

### CLI — one tool at a time

```bash
npx @modelcontextprotocol/inspector --cli --config inspector.json --server my-domain-lang \
  --method tools/call --tool-name lookup_term --tool-arg term=app
```

Swap the tail for each tool:

| Tool | Tail | Expect |
|---|---|---|
| `lookup_term` | `--tool-name lookup_term --tool-arg term=app` | `application` / Application, plus 3 warnings |
| `get_related_terms` | `--tool-name get_related_terms --tool-arg term=application` | 3 outgoing edges: `owns`→Configuration, `classified_by`→AppType, `associated_with`→User |
| `list_domain_areas` | `--tool-name list_domain_areas` | `["config_storage", "user_directory"]` |
| `validate_knowledge_graph` | `--tool-name validate_knowledge_graph` | `{"valid": true, "issues": []}` |

`--method tools/list` (no tool name) dumps the whole surface with input and output schemas.

Terms in the shipped graph: `application` (alias `app`), `configuration` (`config`, `config entry`), `user` (`person`, `directory entry`), `app_type` (`application type`), `environment_settings` (`dev settings`, `uat settings`, `prod settings`). Try `term=APP` to see case-insensitive alias resolution.

### The error paths

These are the interesting part — the two channels are meant to behave differently:

```bash
# tool-execution error: actionable, the model can correct itself
--method tools/call --tool-name lookup_term --tool-arg term=nonsense_term
#  -> isError: true, "No domain term matches 'nonsense_term'. Call list_domain_areas ..."

# protocol error: the -32602 argument guard
--method tools/call --tool-name lookup_term
#  -> {"error":"Invalid arguments for tool lookup_term: 'term' is a required property"}

# unbuilt graph, without disturbing the real one
-e KNOWLEDGE_DB=/tmp/nope.db --method tools/call --tool-name list_domain_areas
#  -> isError: true, names the path and `make knowledge-import` — and creates no file
```

**One thing the Inspector cannot show you:** `--tool-name not_a_tool` returns *the Inspector's own* "Tool 'not_a_tool' not found on server", because it validates against `tools/list` client-side and never sends the call. The server's `-32602 Unknown tool` response is real but only a raw JSON-RPC frame reaches it — which is what `stdio_server/main_test.py::test_raw_initialize_and_stderr_discipline` does.

## Registering in a coding agent

Same shape as [`inspector.json`](inspector.json), but with absolute paths — an agent will not be launching it from this directory:

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
