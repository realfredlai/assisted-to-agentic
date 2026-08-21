# my-domain-lang-mcp

An MCP server (stdio transport) for the config-service domain language, built on the official [MCP Python SDK](https://py.sdk.modelcontextprotocol.io/) v2.

**Phase 1 (current):** the server completes the MCP initialize handshake and exposes **no tools, resources, or prompts**. What it does deliver is the protocol-layer discipline a stdio server owes its client:

- stdout carries JSON-RPC frames only — all logging goes to stderr;
- unknown methods are answered with `-32601` (method not found), and a `tools/call` naming an unregistered tool with `-32602` — a **protocol error** per spec (Tools § Error Handling), distinct from tool-execution errors (`isError: true`). mcp 2.0.0 answers unknown tools with an `isError` result instead; a small `unknown_tool_guard` middleware in `build_server()` restores the spec behaviour. The session survives both errors;
- client disconnect (stdin EOF) and Ctrl+C exit cleanly with code 0; unexpected errors are logged to stderr and exit nonzero.

**Phase 2 (next):** expose the sibling [`knowledge_graph`](../knowledge_graph/) package as MCP tools. Its `storage`/`importer` modules are Django-free, so the server will import them directly — no subprocess indirection. That planned wiring is why this project lives inside `backend/`.

## Layout

```
my-domain-lang-mcp/
├── requirements.txt        # mcp + pytest, exact pins (pip/venv, like the backend)
├── pytest.ini              # *_test.py discovery, asyncio_mode = auto
├── venv/                   # created by `make mcp-install` (gitignored)
└── stdio_server/
    ├── main.py             # build_server() + main() entry point
    └── main_test.py        # 6 tests: in-memory handshake + real-stdio black-box
```

The folder name is hyphenated so it cannot be a Python package; the package is `stdio_server`, mirroring the course reference layout (an `http_server` sibling could join it later).

## Setup, test, run

From `config-service/` (Docker not required — this project never touches Postgres):

```bash
make mcp-install   # create venv + install dependencies
make mcp-test      # run the 6-test suite
make mcp-run       # run the server on stdio (for Inspector / manual poking)
```

Or manually from this directory: `python3 -m venv venv && venv/bin/pip install -r requirements.txt`, then `venv/bin/python -m pytest` / `venv/bin/python -m stdio_server.main`.

## Poking it with MCP Inspector

```bash
npx @modelcontextprotocol/inspector -- backend/my-domain-lang-mcp/venv/bin/python -m stdio_server.main
```

(run from `config-service/` with the Inspector's cwd set here, or adjust paths). Expect a successful connect showing server `my-domain-lang-mcp` — and empty tool/resource/prompt lists.

## Registering in a coding agent (once Phase 2 lands)

There is nothing to call yet, so registration is documentation-only for now. The shape, for later:

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

## Tests

Two levels, both in `stdio_server/main_test.py`:

- **In-memory** — the v2 SDK's `Client(server)` dispatches in-process: handshake identity, empty capability surface, unknown-tool `-32602` protocol error that doesn't poison the session.
- **Black-box subprocess** — spawns `python -m stdio_server.main` and speaks real stdio: SDK-client handshake, a hand-rolled JSON-RPC exchange (initialize → unknown method → `-32601` → unknown tool → `-32602`, asserting stdout purity throughout), and clean EOF exit.
