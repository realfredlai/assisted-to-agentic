# 002 — MCP stdio server (Phase 1: handshake)

**Goal:** Stand up a Python MCP server project at `config-service/backend/my-domain-lang-mcp/` that completes the MCP initialize handshake over stdio with proper protocol-layer error handling — exposing **zero** tools, resources, or prompts. Phase 2 will wire it to `backend/knowledge_graph`; this phase delivers the skeleton that makes that wiring trivial.

## Stages

| Stage | State | Signed off |
|-------|-------|------------|
| 1. PLAN | signed off 2026-08-21 ("build it") | ☑ |
| 2. BUILD & ASSESS | signed off 2026-08-21 ("sign off now", incl. AC4/AC5 re-confirm) | ☑ |
| 3. REFLECT & ADAPT | signed off 2026-08-21 ("go for it") | ☑ |
| 4. COMMIT & PICK NEXT | **awaiting final sign-off** | ☐ |

## Decisions

| Decision | Choice |
|----------|--------|
| Language + SDK | Python, official `mcp` SDK v2 — `mcp==2.0.0`, user-approved. Reference (v1 `FastMCP` API) studied for shape, written in v2 idioms. |
| Dependency management | pip + venv + requirements.txt (user-chosen over recommended uv); exact pins; own venv; no console script — runs as `python -m stdio_server.main`. |
| Test dependencies | `pytest==9.1.1` + `pytest-asyncio==1.4.0` (approved with PLAN sign-off). |
| Location + layout | `backend/my-domain-lang-mcp/` per instruction; inner package `stdio_server/` (hyphens invalid in module names; room for an `http_server` sibling; Phase-2 `knowledge_graph` import is why it lives in `backend/`). |
| Protocol-layer error handling | stderr-only logging; clean exit 0 on EOF/SIGINT, log-and-exit-1 otherwise; JSON-RPC errors for unknown methods (`-32601`) and unknown tools (`-32602` via `unknown_tool_guard` middleware — mcp 2.0.0 deviates from spec Tools § Error Handling by answering `isError` results; corrected after the user's spec review). Middleware API is SDK-"provisional" — safe under the exact pin; re-verify at upgrade (recorded in ARCHITECTURE.md). |

## Acceptance criteria — all met

- [x] **AC1** — In-memory handshake completes with `server_info.name == "my-domain-lang-mcp"` and a non-empty protocol version.
      Test: `stdio_server/main_test.py::test_handshake_completes_in_memory`
- [x] **AC2** — Tools, resources, and prompts all list empty — nothing exposed in Phase 1.
      Test: `stdio_server/main_test.py::test_no_tools_resources_or_prompts`
- [x] **AC3** — Handshake completes over a real stdio subprocess via the SDK client.
      Test: `stdio_server/main_test.py::test_handshake_over_real_stdio`
- [x] **AC4** — Calling a nonexistent tool yields a JSON-RPC protocol error `-32602` (`MCPError` client-side) and the session remains usable.
      Test: `stdio_server/main_test.py::test_unknown_tool_yields_protocol_error_not_crash`
- [x] **AC5** — A hand-rolled stdio exchange gets only JSON-RPC frames on stdout (`-32601` for an unknown method, `-32602` + `Unknown tool: invalid_tool_name` for an unknown tool — the spec's example verbatim), with the startup log on stderr only.
      Test: `stdio_server/main_test.py::test_raw_initialize_and_stderr_discipline`
- [x] **AC6** — Closing stdin exits the server cleanly: return code 0, no traceback.
      Test: `stdio_server/main_test.py::test_clean_exit_on_client_disconnect`

## 4. COMMIT & PICK NEXT

**Commits:** `c602243` (feat: add MCP stdio server, Phase 1) + the purge follow-up.

**Docs updated (in the feat commit):** `config-service/README.md`, `context/ARCHITECTURE.md`, `memory/ENV_SCRIPTS.md`, `memory/WORKFLOW_STATUS.md`, `AGENTS.md` (new standing rule), `backend/my-domain-lang-mcp/README.md`.

**Journal entries:** #18–#22.

**Next work item:** Phase 2 — expose `knowledge_graph` as MCP tools (proposed; the user's stated roadmap). Also queued: lint-and-typecheck. Number assigned at pick.

**Outcome:** Verification at close: `make mcp-test` 6/6 (stable ×5 twice), `make test` 44/44, `make mcp-run` clean EOF exit. Full PLAN/BUILD/REFLECT reasoning is preserved in git history at `c602243`.
