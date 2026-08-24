# 004 — MCP Phase 2: knowledge-graph tools

**Goal:** Give the Phase-1 MCP server something to say — expose the config-service domain knowledge graph as MCP tools, so a coding agent can ask what a domain word means in this codebase instead of assuming its ordinary meaning.

## Stages

| Stage | State | Signed off |
|-------|-------|------------|
| 1. PLAN | complete | ☑ signed off by user ("go all the way", 2026-08-24) |
| 2. BUILD & ASSESS | complete | ☑ |
| 3. REFLECT & ADAPT | complete | ☑ |
| 4. COMMIT & PICK NEXT | complete | ☑ |

## Decisions

| Decision | Choice |
|----------|--------|
| Backend access | **Direct import** of `knowledge_graph.storage` through a `sys.path` seam (pointing at the sibling `backend/` since [005](005-mcp-server-sibling-layout.md) moved this project out of it) — it is pure stdlib, so no Django or PyYAML enters this venv. The reference's subprocess-and-parse-stdout approach has three failure modes for data reachable in-process. `importer.py` is never imported: this server is a reader. |
| Tool surface | Four — `lookup_term`, `get_related_terms`, `list_domain_areas`, `validate_knowledge_graph`. The reference's `ping` is dropped: every listed tool is context an agent pays for on every call. |
| Return types | `TypedDict`, which yields a real `outputSchema` + `structuredContent` (a bare `dict` yields neither — measured). `get_related_terms` adds the target's `to_name` so an agent needn't issue one lookup per edge. |
| Database path | Defaults to `config-service/knowledge.db`; **`KNOWLEDGE_DB`** overrides it — the seam that keeps the tests hermetic. |
| Missing graph | Existence checked **before** touching `Storage`, because `sqlite3.connect()` creates a file for a missing path. Both that and `OperationalError` become errors naming the path and `make knowledge-import`. |
| Error channels | Protocol errors (`-32602`) for unknown tool **and** invalid arguments, via `spec_conformance_guard`; `isError` results for unknown term and unbuilt graph. This is the spec's split; mcp 2.0.0 does not implement it. The guard validates against each tool's `input_schema` and, since the SDK does not coerce, rejects exactly what the SDK would — only the channel changes. |
| Caveat | The SDK marks its middleware signature "provisional"; `mcp==2.0.0` is pinned exactly, so re-verify the guard at any deliberate upgrade. Recorded in `context/ARCHITECTURE.md` so it survives this purge. |
| Out of scope | HTTP transport; write/mutation tools; resources and prompts; registering the server in any agent's config; growing the graph's content. |

## Acceptance criteria — all met

- [x] **AC1** — exactly four tools, each with a description and an `outputSchema`.
- [x] **AC2** — `lookup_term` resolves id, name, and alias case-insensitively, with definition, aliases, and warnings.
- [x] **AC3** — an unknown term is a **tool-execution** error naming the term and suggesting `list_domain_areas` — not a protocol error.
- [x] **AC4** — `get_related_terms` returns outgoing edges only, each with `from`, `to`, `relationship`, `to_name`.
- [x] **AC5** — `list_domain_areas` returns the areas, sorted and de-duplicated.
- [x] **AC6** — `validate_knowledge_graph` reports a clean graph as valid and names the missing node in a broken one.
- [x] **AC7** — a missing database yields an actionable error **and creates no file**.
- [x] **AC8** — the default path resolves to `config-service/knowledge.db`.
- [x] **AC9** — missing/wrong-typed arguments and unknown tool names are all JSON-RPC **`-32602`**, and the session survives.
- [x] **AC10** — a raw `tools/call` over real stdio returns structured content with stdout carrying only JSON-RPC frames.
- [x] **AC11** — `make mcp-test` passes with Docker stopped and `knowledge.db` absent.

Proven by 18 tests: `stdio_server/tools_test.py` (11, tool behaviour against temporary in-process graphs) and `stdio_server/main_test.py` (7, protocol layer).

**Deliberate invalidation:** work item 002's AC2 asserted an empty tool list — the point of Phase 1, and false by design from here. Its test was *replaced*, not quietly weakened, under a docstring naming what it replaces and why; resources and prompts are still asserted empty.

## Outcome

**Complete.** Commit `a82d322` (+ purge follow-up). The [003](003-lint-and-typecheck.md) quality gate immediately found three real defects in this item's own new code (`E501`, `I001`, and an unnecessary `noqa` caught by `RUF100`), and mypy confirmed the `MYPYPATH` wiring resolves `knowledge_graph` in production. Full PLAN/BUILD/REFLECT reasoning preserved in git history at `a82d322`.
