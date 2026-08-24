# 004 — MCP Phase 2: knowledge-graph tools

> Process, gates, and the sign-off rule: [`memory/WORKFLOW_STATUS.md`](../memory/WORKFLOW_STATUS.md).

**Goal:** Give the Phase-1 MCP server something to say. Expose the config-service domain knowledge graph as MCP tools — look up a term, walk its relationships, list the domain areas, validate the graph — so a coding agent can ask what `Configuration` means in this codebase instead of guessing. Backed by a **direct import** of `backend/knowledge_graph`, not a subprocess.

## Stages

| Stage | State | Signed off |
|-------|-------|------------|
| 1. PLAN | **awaiting sign-off** | ☐ |
| 2. BUILD & ASSESS | not started | ☐ |
| 3. REFLECT & ADAPT | not started | ☐ |
| 4. COMMIT & PICK NEXT | not started | ☐ |

## Inputs

- Work item [`002`](002-mcp-stdio-server.md) — the Phase-1 server, its `unknown_tool_guard`, and its stated Phase-2 plan.
- `backend/knowledge_graph/storage.py` — `Storage.lookup()` / `get_related()` / `list_areas()` / `validate_consistency()`, `NodeNotFoundError`.
- The reference `domain-lang-mcp/stdio_server/tools.py` — studied for tool naming and description style; its subprocess-and-JSON-parse approach is **not** copied (see Decisions).
- MCP spec, Tools § Error Handling — the protocol-error vs tool-execution-error split established in 002.
- **Empirical verification done during PLAN** (all claims below are measured, not assumed).

## Outputs

`stdio_server/tools.py` (four tools + the storage seam), `tools_test.py`, a `main.py` that registers them behind an extended spec-conformance guard, updated `main_test.py`, and docs describing the tool surface.

---

## 1. PLAN

### Verified during planning

Each of these shaped a decision below and was confirmed by running it, not by reading docs:

1. **The MCP venv can import `knowledge_graph.storage` directly** — it is pure stdlib (`json`, `sqlite3`, `dataclasses`, `pathlib`); `knowledge_graph/__init__.py` is empty, so nothing drags in Django or PyYAML. Confirmed by importing it from the MCP venv and running real queries against the shipped `knowledge.db`.
2. **A missing `knowledge.db` fails badly by default** — `sqlite3.connect()` *creates an empty file*, then queries raise `OperationalError: no such table: nodes`. Unhandled, the server would litter a stray db and leak a stdlib error to the agent.
3. **Bare `dict` returns produce no structured output** (`output_schema: null`); a **`TypedDict`** or Pydantic return annotation produces a real `outputSchema` plus `structuredContent`. A `list[str]` return is wrapped as `{"result": [...]}`.
4. **`ToolError` → `isError: true`** with the message preserved — the correct channel for actionable, model-correctable failures.
5. **mcp 2.0.0 also deviates from spec on invalid arguments** — the spec lists "Invalid arguments" as a *protocol* error alongside "Unknown tools", but the SDK answers with an `isError` result carrying a pydantic validation dump.
6. **A jsonschema guard for arguments is safe** — the SDK does **not** coerce (`{"term": 123}` is rejected, not cast). Tested against `input_schema` over five argument shapes (valid / wrong type / null / missing / extra key); the guard's verdict matched the SDK's on every one. So the guard changes the *error channel*, never which calls succeed. `jsonschema` is a declared dependency of `mcp` itself, so this adds nothing new.

### Decisions

| Decision | Choice | Why / alternatives |
|----------|--------|--------------------|
| Backend access | **Direct import** of `knowledge_graph.storage` via a `sys.path` seam | Verified fact 1. The reference shells out to `uv run knowledge-graph` and parses stdout — three failure modes (process spawn, exit code, JSON parse) for data already reachable in-process. Direct import is faster, typed, and keeps the server standalone. This is why 002 placed the project inside `backend/`. |
| Which module | `storage.py` **only** — never `importer.py` | `importer.py` needs PyYAML; the MCP server is a **reader**. Rebuilding the graph stays a `make knowledge-import` job. Keeps the MCP venv free of PyYAML. |
| Database path | Default `…/config-service/knowledge.db` resolved relative to `__file__`; **`KNOWLEDGE_DB` env var overrides** | Zero-config for `make mcp-run`, and the override is the seam that keeps tests hermetic (see Test strategy). |
| Missing / unbuilt database | Check `path.exists()` **before** touching `Storage`; catch `sqlite3.OperationalError`. Both → `ToolError` naming the path and saying `run: make knowledge-import` | Verified fact 2. Existence-check-first is what prevents the stray empty db file. |
| Tool surface | **Four** tools: `lookup_term`, `get_related_terms`, `list_domain_areas`, `validate_knowledge_graph` | One per `Storage` query primitive. The reference's fifth tool, `ping`, is dropped: it echoes a string, and every tool in the list is context an agent pays for on every call. `list_domain_areas` is the connectivity check. |
| Return types | **`TypedDict`** returns, so every tool ships an `outputSchema` and `structuredContent` | Verified fact 3. Stdlib-only (no new dependency), and typed results are what make the tools usable without string-parsing. The reference returns `json.dumps(...)` strings — a v1-era shape. |
| Edge shape | `{"from": …, "to": …, "relationship": …, "to_name": …}` via functional `TypedDict` syntax (`from` is a Python keyword) | `to_name` is added because `get_related` returns bare ids; without it an agent must issue one `lookup_term` per edge just to render the answer. |
| Term not found | `ToolError` → `isError: true`, message naming the term and pointing at `list_domain_areas` | Verified fact 4. This is the spec's *tool-execution error* category — "actionable feedback for the model to self-correct" — and is deliberately **not** a protocol error. It is the other half of the distinction learned in 002. |
| Invalid arguments | **Extend the guard**: validate `arguments` against the tool's `input_schema` in middleware, raise `MCPError(-32602)` | Verified fact 6 — safe, and the same spec paragraph that motivated 002's `unknown_tool_guard`. Phase 1 had no arguments, so this could not arise until now. Alternative (leave it) means knowingly shipping a second deviation we have already characterised. |
| Guard structure | Rename to a single `spec_conformance_guard` covering unknown tool **and** invalid arguments | One middleware, one concern (protocol-error conformance), one place to re-verify at an SDK upgrade — the caveat recorded in ARCHITECTURE.md. |
| Keeping the import seam gate-clean | Inline **`# noqa: E402`** at the late import; rely on **`mypy_path`** so `knowledge_graph.*` resolves for mypy | The `sys.path.insert` must run *before* the import, which ruff flags as E402 and mypy cannot resolve unaided (both verified). [`003`](003-lint-and-typecheck.md) establishes this convention and ships the `mypy.ini` entry. **If 004 is built first, it owns adding both** — otherwise 003 signs off green and this item immediately breaks the gate it was handed. |

### Acceptance criteria

- [ ] **AC1** — Given a connected client, When it lists tools, Then exactly four are returned — `lookup_term`, `get_related_terms`, `list_domain_areas`, `validate_knowledge_graph` — each with a non-empty description and an `outputSchema`.
      Test: `stdio_server/tools_test.py::test_tool_surface_is_the_four_knowledge_tools`
- [ ] **AC2** — Given a knowledge database containing a node `application` (name `Application`, alias `app`), When `lookup_term` is called with `application`, `Application`, `APP`, or `app`, Then each returns `structuredContent` whose `id` is `application`, with its definition, aliases, and warnings.
      Test: `stdio_server/tools_test.py::test_lookup_term_resolves_id_name_and_alias_case_insensitively`
- [ ] **AC3** — Given that database, When `lookup_term` is called with `nonsense_term`, Then the result is a **tool-execution error** (`is_error=True`) whose message names the term and suggests `list_domain_areas` — and is *not* a JSON-RPC protocol error.
      Test: `stdio_server/tools_test.py::test_unknown_term_is_an_actionable_tool_error`
- [ ] **AC4** — Given a database where `application` has outgoing edges, When `get_related_terms` is called with `application`, Then it returns one record per outgoing edge, each carrying `from`, `to`, `relationship`, and the target's `to_name`; incoming edges are excluded.
      Test: `stdio_server/tools_test.py::test_get_related_returns_outgoing_edges_with_target_names`
- [ ] **AC5** — Given a database with nodes in two areas, When `list_domain_areas` is called, Then it returns both area names, sorted and de-duplicated.
      Test: `stdio_server/tools_test.py::test_list_domain_areas`
- [ ] **AC6** — Given a database whose edges all resolve, When `validate_knowledge_graph` is called, Then it returns `valid: true` with an empty `issues` list; given one with an edge pointing at a missing node, it returns `valid: false` and an issue naming that node.
      Test: `stdio_server/tools_test.py::test_validate_reports_clean_and_broken_graphs`
- [ ] **AC7** — Given `KNOWLEDGE_DB` pointing at a path that does not exist, When any knowledge tool is called, Then the result is a tool error naming the path and instructing `make knowledge-import` — **and no file is created at that path**.
      Test: `stdio_server/tools_test.py::test_missing_database_is_reported_and_creates_no_file`
- [ ] **AC8** — Given no `KNOWLEDGE_DB` override, When the default database path is resolved, Then it points at `config-service/knowledge.db`.
      Test: `stdio_server/tools_test.py::test_default_db_path_resolves_to_config_service_knowledge_db` (path arithmetic only — asserts no file exists, keeping the suite hermetic)
- [ ] **AC9** — Given a connected client, When `lookup_term` is called with a missing `term`, a non-string `term`, or an unknown tool name, Then each is answered with JSON-RPC protocol error **`-32602`** and the session survives.
      Test: `stdio_server/main_test.py::test_invalid_arguments_are_protocol_errors` and the existing `test_unknown_tool_yields_protocol_error_not_crash`
- [ ] **AC10** — Given the subprocess server over real stdio, When a hand-rolled `tools/call` for `lookup_term` is sent after the handshake, Then stdout carries only JSON-RPC frames and the response contains the term's structured content.
      Test: `stdio_server/main_test.py::test_raw_tools_call_over_stdio`
- [ ] **AC11** — Given the whole suite, When `make mcp-test` runs, Then it passes **with Docker stopped and `knowledge.db` absent** — no Postgres, no Django, no generated artefacts. (`mcp-test` has no `db-up` prerequisite, unlike `make test`.)
      Test: the full `make mcp-test` run, executed with the daemon down and `knowledge.db` moved aside; recorded in BUILD.

### Tasks

- [ ] T1 — `stdio_server/tools.py`: the `sys.path` + db-path seams, `_open_storage()` with the missing/unbuilt-db handling, and the four tool functions with `TypedDict` returns. (AC2–AC8)
- [ ] T2 — `main.py`: register the four tools with agent-facing descriptions; extend `unknown_tool_guard` into `spec_conformance_guard` (unknown tool + jsonschema argument validation → `-32602`). (AC1, AC9)
- [ ] T3 — `tools_test.py`: hermetic fixtures building temp databases via `Storage`; the tool-behaviour tests. (AC1–AC8)
- [ ] T4 — `main_test.py`: **replace** `test_no_tools_resources_or_prompts` (see Deliberate invalidation), add the invalid-argument and raw `tools/call` tests. (AC1, AC9, AC10)
- [ ] T5 — Verify with Docker down and `knowledge.db` moved aside. (AC11)
- [ ] T6 — Docs: the MCP README's tool table and Phase-1/2 framing; `config-service/README.md`, `context/ARCHITECTURE.md`, `ENV_SCRIPTS.md` at stage 4.

### Deliberate invalidation of a prior acceptance criterion

Work item 002's **AC2** asserts that tools, resources, and prompts all list *empty* — that was the point of Phase 1. Phase 2 makes it false by design. Per the acceptance-criteria rule ("if a criterion turns out wrong, change it deliberately, note it, and re-confirm"), `test_no_tools_resources_or_prompts` is **replaced**, not quietly edited: resources and prompts stay asserted empty, tools become AC1's four. Recorded here so the change is visible rather than looking like a silently weakened test.

### Test strategy

Three levels, all hermetic — `make mcp-test` must keep working with Docker stopped and no `knowledge.db` present (AC11):

- **Tool behaviour** (`tools_test.py`) — temp databases built **in-process with `Storage` + `insert_node`**, pointed at by `KNOWLEDGE_DB`. Never by shelling out to `manage.py knowledge import`: that would drag Django, PyYAML, and the backend venv into the MCP test path and destroy the standalone property. Exercised through the in-memory MCP client, so schemas and error channels are asserted as a client sees them.
- **Protocol layer** (`main_test.py`) — the argument-validation and unknown-tool paths at `-32602`, plus a raw stdio `tools/call`.
- **No test depends on the real shipped `knowledge.db`** — it is gitignored and generated, so requiring it would make the suite environment-dependent. AC8 covers the real path by asserting path *resolution* instead.

Deliberately not tested: `Storage`'s own query semantics (covered by `knowledge_graph/tests.py`), the YAML importer, SDK internals.

### File changes

| File | Change | Purpose |
|------|--------|---------|
| `changes/004-mcp-knowledge-tools.md` | create | this work item |
| `…/my-domain-lang-mcp/stdio_server/tools.py` | create | seams + four tool implementations |
| `…/my-domain-lang-mcp/stdio_server/tools_test.py` | create | tool behaviour tests |
| `…/my-domain-lang-mcp/stdio_server/main.py` | modify | register tools; extend the guard |
| `…/my-domain-lang-mcp/stdio_server/main_test.py` | modify | replace the empty-surface test; add protocol tests |
| `…/my-domain-lang-mcp/README.md` | modify | tool table, Phase-2 status |
| `config-service/README.md`, `context/ARCHITECTURE.md`, `memory/ENV_SCRIPTS.md` | modify (stage 4) | tool surface + agent registration |
| `memory/WORKFLOW_STATUS.md`, `JOURNAL.md` | modify | pointer, history, run entry |

### Out of scope

- **HTTP transport** — stdio only; the reference's `http_server/` variant is a separate concern.
- **Write tools** — no importing, editing, or mutating the graph over MCP. Read-only by design; `make knowledge-import` stays the way the graph is rebuilt.
- **Resources and prompts** — tools only. MCP resources would be a reasonable later shape for the `context/` docs; not now.
- **Registering the server into any agent's config** — the README documents the snippet; no config on this machine is touched.
- **Expanding the knowledge graph's content** — the five nodes and six edges are what they are; growing them is a `knowledge/` YAML change, not this item.

### Open questions

None. The design questions that existed (subprocess vs direct import, structured output shape, whether the invalid-argument guard is safe) were settled empirically during PLAN — see Verified during planning.

---

## 2. BUILD & ASSESS

> Fill in during implementation.

**Implemented:**

**Deviations from plan:**

**Verification evidence:**

---

## 3. REFLECT & ADAPT

| Friction | Disposition |
|----------|-------------|
| | |

**Adjustments to remaining tasks:**

**Process or doc changes:**

---

## 4. COMMIT & PICK NEXT

**Commits:**

**Docs updated:**

**Journal entry:**

**Next work item:**
