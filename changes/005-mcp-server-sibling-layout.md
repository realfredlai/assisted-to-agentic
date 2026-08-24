# 005 — Move the MCP server beside backend and frontend

> Process, gates, and the sign-off rule: [`memory/WORKFLOW_STATUS.md`](../memory/WORKFLOW_STATUS.md).

**Goal:** Move `my-domain-lang-mcp/` out of `config-service/backend/` to sit alongside `backend/` and `frontend/` as a peer deliverable. `backend/` is the Django project; the MCP server is not part of it, and nesting it there misrepresents both.

## Stages

| Stage | State | Signed off |
|-------|-------|------------|
| 1. PLAN | complete | ☑ |
| 2. BUILD & ASSESS | complete | ☑ |
| 3. REFLECT & ADAPT | complete | ☑ |
| 4. COMMIT & PICK NEXT | **awaiting final sign-off** | ☐ |

## Inputs

- The user's instruction (2026-08-24): "my-domain-lang-mcp shouldn't be inside backend project. Instead it lives at the same level as backend and frontend."
- The three places the old location is load-bearing rather than cosmetic: `tools.py`'s `sys.path` seam, the Makefile's `MCP_DIR`, and the ruff/gitignore exclude paths.

## Outputs

The directory at `config-service/my-domain-lang-mcp/`, every path reference updated, the gate green from the new location, and the **rationale** corrected wherever docs claimed the nesting was deliberate.

---

## 1. PLAN

### Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Move mechanism | `git mv` | Preserves rename detection in history, so `git log --follow` still works on the moved files. |
| The venv | Delete and recreate with `make mcp-install`, not move | Virtualenvs are not relocatable — `venv/bin/*` scripts carry absolute shebangs. It is gitignored and disposable; recreating is the honest fix. |
| Path seam | `_CONFIG_SERVICE = parents[2]`, then `_BACKEND = _CONFIG_SERVICE / "backend"` | The old `_BACKEND = parents[2]` was only correct while nested. Naming the anchor `_CONFIG_SERVICE` makes the arithmetic legible and stops `DEFAULT_DB` from depending on `_BACKEND.parent`, which was a second hop that only worked by coincidence. |
| Historical records | **Not rewritten.** `changes/002`, `changes/004`, and `JOURNAL.md` keep their original text; 002 and 004 get a one-line forward pointer to this item | Those record what was decided and true at the time — `JOURNAL.md` is explicitly append-only, and purged work items are the historical record. Rewriting them would falsify the record; leaving them bare would mislead a future reader. A pointer does both jobs. |
| Rationale correction | The claim "that is why the project sits inside `backend/`" is **removed**, not softened | It appeared in `ARCHITECTURE.md`, the MCP README, and 004's notes as justification for the nesting. The direct import never required nesting — only a correct relative path. Leaving the claim standing would preserve a wrong reason for a decision that has been reversed. |

### Acceptance criteria

- [x] **AC1** — Given the repo, When the tree is inspected, Then `config-service/my-domain-lang-mcp/` exists and nothing named `my-domain-lang-mcp` remains under `config-service/backend/`.
      Test: manual — `ls` + `git status`; recorded in BUILD.
- [x] **AC2** — Given the moved project, When `make mcp-test` runs, Then all 18 tests pass from the new location.
      Test: existing `stdio_server/main_test.py` + `tools_test.py` (unchanged).
- [x] **AC3** — Given the moved project, When `make check` runs, Then it is green — proving the ruff exclude, the `MYPYPATH` wiring, and `MCP_DIR` all followed the move.
      Test: manual gate command; output in BUILD.
- [x] **AC4** — Given no `KNOWLEDGE_DB` override, When the default database path is resolved, Then it still points at `config-service/knowledge.db`.
      Test: `stdio_server/tools_test.py::test_default_db_path_resolves_to_config_service_knowledge_db` (unchanged — it asserts the destination, not the route).
- [x] **AC5** — Given the current docs and config, When they are searched for `backend/my-domain-lang-mcp`, Then no live reference remains; the only matches are historical records carrying a forward pointer.
      Test: manual `grep`; output in BUILD.
- [x] **AC6** — Given `git log --follow` on a moved file, Then its pre-move history is still reachable.
      Test: manual; output in BUILD.

### Tasks

- [x] T1 — Delete the old venv; `git mv` the directory.
- [x] T2 — Fix the path seam in `tools.py`.
- [x] T3 — Update `Makefile` (`MCP_DIR`), `.gitignore`, `ruff.toml`.
- [x] T4 — Recreate the venv; run `make mcp-test`, then `make check`.
- [x] T5 — Update docs and correct the nesting rationale; add forward pointers to 002 and 004.

### Test strategy

No new tests. This is a move: the existing 18 tests are the regression net, and the point is that **none of them should need changing** — `PROJECT_DIR` and the default-db-path assertion are both written relative to `__file__` or to the destination, so they survive a relocation. If a test had needed editing, that would have been a signal the suite was coupled to the layout. The gate (AC3) is what proves the tooling paths followed.

### File changes

| File | Change | Purpose |
|------|--------|---------|
| `config-service/backend/my-domain-lang-mcp/**` → `config-service/my-domain-lang-mcp/**` | move | the point of the item |
| `…/my-domain-lang-mcp/stdio_server/tools.py` | modify | path seam |
| `config-service/Makefile`, `.gitignore`, `ruff.toml` | modify | `MCP_DIR`, ignore path, lint exclude |
| `config-service/README.md`, `context/ARCHITECTURE.md`, `memory/ENV_SCRIPTS.md`, `…/my-domain-lang-mcp/README.md` | modify | paths + remove the nesting rationale |
| `changes/002-mcp-stdio-server.md`, `changes/004-mcp-knowledge-tools.md` | modify | one-line forward pointer each |
| `memory/WORKFLOW_STATUS.md`, `JOURNAL.md` | modify | pointer, history, run entry |

### Out of scope

- Any behaviour change. The server, its tools, and its error semantics are untouched.
- Moving `knowledge/` or `knowledge.db` — the database stays at `config-service/knowledge.db`, which both the Django command and the MCP server already agree on.
- Rewriting historical records (see Decisions).

### Open questions

None.

---

## 2. BUILD & ASSESS

**Implemented:** `git mv config-service/backend/my-domain-lang-mcp config-service/my-domain-lang-mcp`; the old venv deleted and recreated in place by `make mcp-install`. `tools.py`'s seam re-anchored on `_CONFIG_SERVICE = parents[2]`, with `_BACKEND` and `DEFAULT_DB` derived from it. `Makefile` (`MCP_DIR`), `.gitignore`, and `ruff.toml` exclude updated. Docs updated across `config-service/README.md`, `context/ARCHITECTURE.md`, `memory/ENV_SCRIPTS.md`, and the MCP README — including **removing the claim that the direct import was why the project sat inside `backend/`**, which was never true. Forward pointers added to `changes/002` and `004`.

**Deviations from plan:** none of substance. One process slip: my first attempt at the `002` forward pointer asserted on remembered text rather than the file's actual text and failed — caught by the assertion rather than silently writing nothing, then re-read and fixed.

**Verification evidence:**

```
$ ls config-service/                     -> backend  frontend  knowledge  my-domain-lang-mcp  ...
$ ls config-service/backend | grep -c my-domain-lang-mcp   -> 0

$ make mcp-test
18 passed in 3.23s          # no test file needed editing

$ make check
All checks passed!                              # ruff (exclude followed the move)
Success: no issues found in 21 source files     # mypy backend
Success: no issues found in 5 source files      # mypy MCP server (MYPYPATH followed)
Ran 44 tests in 0.259s / OK
18 passed in 2.84s
All checks passed.
```

`make check` passing is the real proof: the ruff exclude, the `MYPYPATH` wiring, and `MCP_DIR` would each have failed loudly had they not been updated — and mypy still resolves `knowledge_graph` from the new location, so the sibling `sys.path` seam is genuinely checked, not silently `Any`.

**Not one test needed changing.** `PROJECT_DIR` is derived from `__file__` and the default-db assertion checks the destination (`config-service/knowledge.db`) rather than the route, so both survived relocation untouched — which is what a suite that is not coupled to its own layout should do.

---

## 3. REFLECT & ADAPT

| Friction | Disposition |
|----------|-------------|
| **A wrong reason had been written down three times.** "That is why the project sits inside `backend/`" appeared in `ARCHITECTURE.md`, the MCP README, and `changes/004` — presented as justification, but the direct import only ever needed a correct relative path. Documenting a decision's rationale makes a bad rationale durable and quotable. | **Fixed now** — the claim is removed rather than softened, and `changes/002` records explicitly that its stated reasoning was wrong. A superseded decision is easy to spot; a superseded *reason* left standing quietly teaches the wrong lesson. |
| **The venv could not move.** `git mv` renames the directory, but virtualenv scripts carry absolute shebangs, so the moved venv would have been subtly broken. | **Fixed now** — deleted and recreated via `make mcp-install`. Worth remembering generally: a gitignored directory is not automatically safe to relocate. |
| **Path arithmetic was written to be brittle.** `_BACKEND = parents[2]` was correct only while nested, and `DEFAULT_DB = _BACKEND.parent` reached the right place by a second coincidence. | **Fixed now** — anchored on `_CONFIG_SERVICE` and derived both from it, so the two facts ("where the backend is", "where the database is") are each stated once against a named root. |
| **I asserted on remembered file text and was wrong.** The `002` decision row did not read as I recalled. | **Accepted** — no change needed; the practice that caught it (asserting the match before writing, rather than a silent `sed`) is already what I do. The lesson is that it earned its keep. |

**Adjustments to remaining tasks:** none.

**Process or doc changes:** none. The existing rules covered this; the reflection worth keeping is about *rationale rot* — when a structural decision is reversed, the recorded reason must be corrected, not just the structure.

---

## 4. COMMIT & PICK NEXT

Recorded at close.
