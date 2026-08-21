# 002 — MCP stdio server (Phase 1: handshake)

**Goal:** Stand up a Python MCP server project at `config-service/backend/my-domain-lang-mcp/` that completes the MCP initialize handshake over stdio with proper protocol-layer error handling — exposing **zero** tools, resources, or prompts. Phase 2 will wire it to `backend/knowledge_graph`; this phase delivers the skeleton that makes that wiring trivial.

## Stages

| Stage | State | Signed off |
|-------|-------|------------|
| 1. PLAN | signed off 2026-08-21 ("build it") | ☑ |
| 2. BUILD & ASSESS | signed off 2026-08-21 ("sign off now", incl. AC4/AC5 re-confirm) | ☑ |
| 3. REFLECT & ADAPT | signed off 2026-08-21 ("go for it") | ☑ |
| 4. COMMIT & PICK NEXT | in progress | ☐ |

## Inputs

- The request (this run's prompt): stdio MCP server, official SDK, dependency management proposed, handshake only, protocol-layer error handling, follow the four-stage process.
- Reference implementation (study, don't copy): `assisted-to-agentic-module-5/examples/domain-lang-mcp/` (local checkout of the GitHub URL given) — uv + hatchling project, `stdio_server/` package, FastMCP v1 API, pytest with in-memory client sessions, `*_test.py` naming.
- MCP Python SDK v2 docs: [migration guide](https://py.sdk.modelcontextprotocol.io/migration/) and [what's new](https://py.sdk.modelcontextprotocol.io/whats-new/) — `FastMCP` → `MCPServer` (`from mcp.server.mcpserver import MCPServer`, decorator API unchanged, `run(transport="stdio")`); v1's `create_connected_server_and_client_session` replaced by unified `Client`: `async with Client(server)` (in-memory) / `Client(StdioServerParameters(...))` (subprocess); after connect: `client.server_info`, `client.server_capabilities`, `client.protocol_version`.
- Existing code: `backend/knowledge_graph/` — `storage.py` and `importer.py` are Django-free (sqlite3/json/pathlib/yaml only), verified by import inspection; only the management command needs Django.
- Facts about the machine: `/opt/homebrew/bin/python3` is 3.14.4 (same as `backend/venv`); PyPI `mcp` latest is 2.0.0 (2026-07-28; 1.x ended at 1.29.0 the same day).

## Outputs

- `config-service/backend/my-domain-lang-mcp/` — pip/venv project: `requirements.txt`, `pytest.ini`, `README.md`, `stdio_server/` package with `main.py` (server + entry point) and `main_test.py` (6 tests).
- Makefile targets `mcp-install`, `mcp-test`, `mcp-run`; `.gitignore` entry for the new venv; ENV_SCRIPTS.md section; WORKFLOW_STATUS gate row for the new test command (flipped at BUILD, when the command exists).

---

## 1. PLAN

### Decisions

| Decision | Choice | Why / alternatives |
|----------|--------|--------------------|
| Language + SDK | Python, official `mcp` SDK, **v2.x** (exact pin at build, `mcp==2.0.0` per backend's exact-pin convention) | **User-approved 2026-08-21.** Current official major; fresh projects don't start on a dead-end major. The reference's v1 API (`FastMCP`) is studied for shape, rewritten in v2 idioms — "study it but don't copy it verbatim". Alternative 1.29 (final v1, matches reference line-for-line) rejected. |
| Dependency management | **pip + venv + requirements.txt** | **User-chosen 2026-08-21** over the recommended uv: one toolchain across the repo, matching `backend/`. Consequences: no pyproject packaging → no console script (run via `python -m stdio_server.main`); no lockfile → exact pins in requirements.txt; own `venv/` inside `my-domain-lang-mcp/`, created the same way as the backend's. |
| Test dependencies | `pytest` + `pytest-asyncio` (exact pins at build) | The SDK is async; Django's test runner has no jurisdiction here. Mirrors the reference. **New dependencies — this sign-off is their approval.** |
| Location + layout | `config-service/backend/my-domain-lang-mcp/` (per instruction) with inner package `stdio_server/` | Hyphens are invalid in module names, so the folder can't be the package. `stdio_server` mirrors the reference layout and leaves room for a future `http_server` sibling. Sitting inside `backend/` makes the Phase-2 `knowledge_graph` import a `sys.path` one-liner. |
| Server identity | `MCPServer("my-domain-lang-mcp")` | Matches the folder name the user chose; asserted by tests. |
| Test naming | `*_test.py`, `asyncio_mode = auto`, via `pytest.ini` | Mirrors the reference's pytest conventions; `pytest.ini` because there is no pyproject.toml to host config. |
| Protocol-layer error handling (the Phase-1 meaning of it) | (a) logging configured to **stderr only** — stdout carries nothing but JSON-RPC frames; (b) `main()` exits 0 on client disconnect/EOF and SIGINT, logs-and-exits-nonzero on unexpected errors — never a raw traceback masquerading as protocol output; (c) malformed/unknown requests are answered with JSON-RPC errors by the SDK dispatcher and the session survives — proven by test, not assumed. | This is what "proper error handling" means when there are no tools yet: the transport discipline. |

### Acceptance criteria

- [x] **AC1** — Given the server built by `build_server()`, When a v2 `Client` connects in-memory, Then the initialize handshake completes: `client.server_info.name == "my-domain-lang-mcp"` and `client.protocol_version` is a non-empty string.
      Test: `backend/my-domain-lang-mcp/stdio_server/main_test.py::test_handshake_completes_in_memory`
- [x] **AC2** — Given a connected client, When it lists tools, resources, and prompts, Then each comes back empty (or the server declares no such capability) — nothing is exposed in Phase 1.
      Test: `stdio_server/main_test.py::test_no_tools_resources_or_prompts`
- [x] **AC3** — Given the server launched as a real subprocess (`venv/bin/python -m stdio_server.main`), When a `Client` connects via `StdioServerParameters`, Then the handshake completes with the same server identity as AC1.
      Test: `stdio_server/main_test.py::test_handshake_over_real_stdio`
- [x] **AC4** — Given a connected client, When it calls a tool that does not exist, Then it receives a JSON-RPC **protocol error** with code `-32602` (Invalid params, per spec Tools § Error Handling; `MCPError` client-side) — and the session remains usable afterwards (a subsequent list request succeeds).
      Test: `stdio_server/main_test.py::test_unknown_tool_yields_protocol_error_not_crash`
      *History: BUILD first re-worded this to `is_error=True` results, wrongly calling the SDK's behaviour "the v2 contract". The user corrected this against the spec, which classifies unknown tools as protocol errors (`-32602`) distinct from tool-execution errors (`isError: true`). mcp 2.0.0 deviates from the spec here, so the server now restores spec behaviour via middleware — see BUILD deviations.*
- [x] **AC5** — Given the subprocess server, When a hand-rolled JSON-RPC `initialize` exchange is performed on its stdin, followed by an unknown method and a `tools/call` naming an unknown tool, Then stdout yields only parseable JSON-RPC frames (no log noise on the wire), the unknown method is answered with `-32601` (method not found), the unknown tool with `-32602` and message `Unknown tool: invalid_tool_name` (the spec's own example, verbatim, with no `result` member), the server survives both, and the startup log line appears on stderr.
      Test: `stdio_server/main_test.py::test_raw_initialize_and_stderr_discipline`
      *Extended during BUILD: gained the `-32601` unknown-method assertion, then the `-32602` unknown-tool assertion after the user's spec correction. Needs re-confirm at stage-2 sign-off.*
- [x] **AC6** — Given a running subprocess server, When its stdin is closed (client disconnect), Then the process exits cleanly: return code 0, no traceback on stderr.
      Test: `stdio_server/main_test.py::test_clean_exit_on_client_disconnect`

### Tasks

- [x] T1 — Scaffold the project: `requirements.txt` (exact pins: `mcp`, `pytest`, `pytest-asyncio`), `pytest.ini`, `README.md`, `stdio_server/__init__.py`; `.gitignore` entry for `backend/my-domain-lang-mcp/venv/`; Makefile `mcp-install` / `mcp-test` / `mcp-run` targets. (all ACs — everything runs through this)
- [x] T2 — `stdio_server/main.py`: `build_server()` returning a bare `MCPServer("my-domain-lang-mcp")` — no tools, resources, or prompts registered. (AC1, AC2)
- [x] T3 — `main.py`: `main()` entry point — logging to stderr, `run(transport="stdio")`, clean exit on EOF/SIGINT, log-and-exit-nonzero on unexpected error. (AC3, AC5, AC6)
- [x] T4 — `stdio_server/main_test.py`: three in-memory tests (AC1, AC2, AC4) and three subprocess tests (AC3 via SDK client, AC5 via hand-rolled frames, AC6 via stdin close). (AC1–AC6)
- [x] T5 — Docs: ENV_SCRIPTS.md gained the MCP project's commands; WORKFLOW_STATUS gate table gained the `make mcp-test` row (done at BUILD, once the command existed); README.md / ARCHITECTURE.md updates land with the stage-4 commit per the exit rule.

### Test strategy

Two levels, all in one file since Phase 1 is one module:

- **In-memory** (fast, no subprocess): v2 `Client(server)` dispatches in-process — proves handshake semantics, empty capability surface, and error-then-survive behaviour (AC1, AC2, AC4).
- **Black-box subprocess** (the real thing): spawn `sys.executable -m stdio_server.main`, exercise actual stdio framing — SDK-client handshake (AC3), a hand-rolled `initialize` frame asserting stdout purity + stderr logging (AC5, protocol version imported from the SDK's constant, not hardcoded), and EOF shutdown (AC6).

Deliberately not tested: SDK internals (v2's own stray-print protection is theirs to test), performance, anything about `knowledge_graph` (Phase 2). No Docker, no Postgres — like the knowledge CLI, this project must work with the daemon down.

### File changes

| File | Change | Purpose |
|------|--------|---------|
| `changes/002-mcp-stdio-server.md` | create | this work item |
| `config-service/backend/my-domain-lang-mcp/requirements.txt` | create | `mcp==2.0.0` + pytest + pytest-asyncio, exact pins |
| `config-service/backend/my-domain-lang-mcp/pytest.ini` | create | `*_test.py` discovery, `asyncio_mode = auto` |
| `config-service/backend/my-domain-lang-mcp/README.md` | create | purpose, run/test commands, agent-registration snippet (`python -m stdio_server.main`) |
| `config-service/backend/my-domain-lang-mcp/stdio_server/__init__.py` | create | package marker |
| `config-service/backend/my-domain-lang-mcp/stdio_server/main.py` | create | `build_server()` + `main()` |
| `config-service/backend/my-domain-lang-mcp/stdio_server/main_test.py` | create | the 6 tests above |
| `config-service/.gitignore` | modify | ignore `backend/my-domain-lang-mcp/venv/` |
| `config-service/Makefile` | modify | `mcp-install`, `mcp-test`, `mcp-run` |
| `memory/ENV_SCRIPTS.md` | modify | MCP server commands section |
| `memory/WORKFLOW_STATUS.md` | modify | Part 2 pointer now; gate row for `make mcp-test` at BUILD |
| `config-service/README.md` | modify (stage 4) | project structure + MCP section |
| `context/ARCHITECTURE.md` | modify (stage 4) | MCP server section |
| `JOURNAL.md` | modify | entry per run |

### Out of scope

- **Any tools, resources, or prompts** — including the reference's `ping`. Phase 2.
- **`knowledge_graph` wiring** — Phase 2. Noted for then: `storage.py`/`importer.py` are Django-free, so direct import beats the reference's subprocess indirection; the location inside `backend/` was chosen for exactly that.
- HTTP transport variant; registering the server into any agent's config (README shows the snippet, nobody's config is touched).
- Lint/typecheck — still its own proposed work item (renumbered `003-lint-and-typecheck`).

### Open questions

None — the two that existed (dependency tool, SDK major) were put to the user and answered 2026-08-21: pip+venv+requirements.txt; mcp 2.x. Recorded in Decisions.

---

## 2. BUILD & ASSESS

**Implemented:** exactly the planned file list — `backend/my-domain-lang-mcp/` with `requirements.txt` (`mcp==2.0.0`, `pytest==9.1.1`, `pytest-asyncio==1.4.0`), `pytest.ini`, `README.md`, `stdio_server/{__init__,main,main_test}.py`; `.gitignore` venv entry; Makefile `mcp-install`/`mcp-test`/`mcp-run`; ENV_SCRIPTS.md MCP section; WORKFLOW_STATUS gate row. `main.py` is `build_server()` (bare `MCPServer("my-domain-lang-mcp", version="0.1.0", instructions=…)`, nothing registered) plus `main()` (stderr-only logging, `run(transport="stdio")`, exit 0 on EOF/SIGINT, log-and-exit-1 on unexpected exceptions). Six tests: 3 in-memory via `Client(server)`, 3 black-box subprocess. v2 API surface verified empirically before coding (probe scripts), not assumed from docs.

**Deviations from plan:**

1. **mcp 2.0.0 deviates from the spec on unknown tools — corrected with a middleware guard.** The SDK answers `tools/call` for an unregistered tool with `CallToolResult(is_error=True)` (verified on the wire), but the spec (Tools § Error Handling) classifies unknown tools as **protocol errors** — standard JSON-RPC `-32602` — distinct from tool-execution errors (`isError: true`), which exist to carry actionable feedback the model can self-correct on. BUILD initially re-worded AC4 to the SDK's behaviour, wrongly presenting it as "the v2 contract"; the user corrected this against the spec. Fix: `build_server()` appends an `unknown_tool_guard` middleware (the documented `server.middleware` extension point — runs pre-validation; a raised `MCPError` becomes the JSON-RPC error response) that answers unregistered `tools/call` with `-32602 Unknown tool: <name>`. AC4 restored to protocol-error wording; AC5's raw exchange now asserts the spec's example verbatim. Note: the SDK marks the middleware signature "provisional — expected to change before v2 is final"; `mcp==2.0.0` is pinned exactly, so this only matters at a deliberate upgrade.
2. **AC5 also gained the `-32601` unknown-method assertion** (protocol-layer proof at the raw JSON-RPC level, alongside the `-32602` unknown-tool one).
3. **`Client` + stdio wiring differs from the docs**: v2's `Client` does not accept `StdioServerParameters` directly (the what's-new doc implied it does — TypeError in practice); it wants a `Transport`, satisfied by `Client(stdio_client(params))`. Test-only fix.
4. **Raw-exchange test rewritten for determinism**: the first version pushed all frames through `communicate()`, which closes stdin immediately — server shutdown then raced the unknown-method dispatch (3 failures in 5 runs). Now an incremental write→read exchange with a 30 s kill-timer guard. Test-design fix; the server behaviour itself was correct.

Nothing outside the planned file-change list was touched.

**Verification evidence:**

```
$ make mcp-test          # after the -32602 middleware fix
stdio_server/main_test.py ......                                         [100%]
============================== 6 passed in 1.90s ===============================

(stability: 5 consecutive full runs after the fix — 6 passed ×5; also ×5 before it)

$ make test
Ran 44 tests in 0.282s
OK

$ make mcp-run < /dev/null
2026-08-21 16:32:54,397 my-domain-lang-mcp INFO starting my-domain-lang-mcp 0.1.0 (stdio)
2026-08-21 16:32:54,401 my-domain-lang-mcp INFO client disconnected; shutting down
exit: 0

$ # wire-level check that prompted the fix (tools/call unknown tool, before middleware):
$ #   {"jsonrpc":"2.0","id":3,"result":{"content":[...],"isError":true}}   ← SDK default, spec-noncompliant
$ # after middleware:
$ #   {"jsonrpc":"2.0","id":3,"error":{"code":-32602,"message":"Unknown tool: invalid_tool_name"}}
```

`make lint` / `make typecheck` remain unconfigured — not run, not claimed.

---

## 3. REFLECT & ADAPT

| Friction | Disposition |
|----------|-------------|
| **Docs-derived API knowledge was wrong** — the v2 what's-new implied `Client(StdioServerParameters(...))` works; in practice it TypeErrors (needs `Client(stdio_client(params))`). mcp 2.0.0 postdates the model's knowledge cutoff, so neither memory nor docs could be trusted alone. | **Fixed now** during BUILD by probing the installed package empirically (signatures, source, wire responses) before coding. Practice promoted to a standing rule in `AGENTS.md` (see below). |
| **SDK behaviour was conflated with protocol contract** — BUILD presented mcp 2.0.0's `isError: true` answer for unknown tools as "the v2 contract"; the spec classifies unknown tools as protocol errors (`-32602`). Caught by the user in stage-2 review, not by the agent. | **Fixed now** — `unknown_tool_guard` middleware + wire-level tests + AC4 restored. Root lesson: for protocol conformance the *spec* is the source of truth; an SDK's behaviour is only evidence of its implementation. Folded into the same `AGENTS.md` rule. |
| **Flaky subprocess test** — the first raw-exchange test pushed all frames via `communicate()`, closing stdin immediately; server shutdown raced dispatch (3 failures in 5 runs). | **Fixed now** — incremental write→read exchange with a kill-timer. The ×5 stability-repeat habit is what exposed it; kept as practice for subprocess tests. |
| **Middleware API marked "provisional"** by the SDK ("expected to change before v2 is final") — the spec-compliance guard rests on it. | **Accepted** — `mcp==2.0.0` is pinned exactly, so nothing can drift until a deliberate upgrade; the caveat must be recorded in `context/ARCHITECTURE.md`'s MCP section at stage 4 so it survives the purge. |

**Adjustments to remaining tasks:** stage-4 doc updates (T5 remainder) must carry the spec-deviation note and the provisional-middleware caveat into `context/ARCHITECTURE.md`, since work-item deviations get purged.

**Process or doc changes:** one standing rule added to `AGENTS.md` (applied this stage): verify third-party SDK/protocol behaviour empirically before coding against it, and treat the spec — not the SDK — as the source of truth for conformance claims.

---

## 4. COMMIT & PICK NEXT

**Commits:**

**Docs updated:**

**Journal entry:**

**Next work item:**
