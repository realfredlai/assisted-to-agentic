# 005 — Move the MCP server beside backend and frontend

**Goal:** Move `my-domain-lang-mcp/` out of `config-service/backend/` to sit alongside `backend/` and `frontend/`. `backend/` is the Django project; the MCP server is not part of it, and nesting it there misrepresented both.

## Stages

| Stage | State | Signed off |
|-------|-------|------------|
| 1. PLAN | complete | ☑ |
| 2. BUILD & ASSESS | complete | ☑ |
| 3. REFLECT & ADAPT | complete | ☑ |
| 4. COMMIT & PICK NEXT | **awaiting final sign-off** | ☐ |

## Decisions

| Decision | Choice |
|----------|--------|
| Move mechanism | `git mv`, so `git log --follow` still reaches the pre-move history. |
| The venv | Deleted and recreated via `make mcp-install` — virtualenvs are not relocatable (absolute shebangs in `venv/bin/*`). Gitignored and disposable. |
| Path seam | Anchored on `_CONFIG_SERVICE = parents[2]`, with `_BACKEND` and `DEFAULT_DB` derived from it. The old `_BACKEND = parents[2]` was correct only while nested, and `DEFAULT_DB = _BACKEND.parent` reached the right place by a second coincidence. |
| Historical records | `changes/002`, `changes/004`, and `JOURNAL.md` keep their original text; 002 and 004 carry a forward pointer to this item. Rewriting them would falsify the record. |
| Rationale correction | The claim "that is why the project sits inside `backend/`" was **removed**, not softened — it appeared in three places as justification and was never true. The import needs a correct relative path, not nesting. `changes/002` now records that its stated reasoning was mistaken. |
| Out of scope | Any behaviour change; moving `knowledge/` or `knowledge.db`. |

## Acceptance criteria — all met

- [x] **AC1** — `config-service/my-domain-lang-mcp/` exists; nothing of that name remains under `backend/`.
- [x] **AC2** — `make mcp-test` passes from the new location: 18 tests.
- [x] **AC3** — `make check` green, proving the ruff exclude, the `MYPYPATH` wiring, and `MCP_DIR` all followed the move.
- [x] **AC4** — the default database path still resolves to `config-service/knowledge.db`.
- [x] **AC5** — no live reference to `backend/my-domain-lang-mcp` remains; the only matches are historical records, which carry forward pointers.
- [x] **AC6** — `git log --follow` on a moved file still reaches `a82d322` and `c602243`.

**No test file needed editing.** `PROJECT_DIR` derives from `__file__` and the default-db assertion checks the destination rather than the route, so both survived relocation untouched — which is what a suite not coupled to its own layout should do.

## Outcome

**Complete.** Commit `b8c7811` (+ purge follow-up). The reflection worth keeping: **rationale rot** — when a structural decision is reversed, the recorded *reason* has to be corrected too, not just the structure. A superseded decision is easy to spot; a superseded reason left standing quietly teaches the wrong lesson. Full PLAN/BUILD/REFLECT reasoning preserved in git history at `b8c7811`.
