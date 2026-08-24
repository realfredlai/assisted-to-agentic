# 003 — Lint and type checking

**Goal:** Make the BUILD & ASSESS gate real — lint and type checking wired into `make`, existing violations fixed, so the gate's ⏳ rows become ✅.

## Stages

| Stage | State | Signed off |
|-------|-------|------------|
| 1. PLAN | complete | ☑ signed off by user ("go all the way", 2026-08-24) |
| 2. BUILD & ASSESS | complete | ☑ |
| 3. REFLECT & ADAPT | complete | ☑ |
| 4. COMMIT & PICK NEXT | **awaiting final sign-off** | ☐ |

## Decisions

| Decision | Choice |
|----------|--------|
| Python lint | `ruff==0.16.4`, explicit `select = [E, F, I, B, UP, SIM, RUF]`, line length 100 — explicit because ruff's implicit defaults shift between releases. |
| Type check | `mypy==2.3.1`, default strictness, run **once per project venv**. Pinned at the same version in `backend/requirements.txt` and the MCP project's — bump together. |
| SPA lint | `eslint` 10 + `eslint-plugin-vue` 10, `flat/essential` (correctness) not `flat/recommended` (formatting), `--max-warnings 0`. |
| Scoped, not fixed | `RUF012` off `api/models.py` + `serializers.py`: Django/DRF declarative `Meta` lists are framework convention, and `ClassVar` annotations would fight the idiom. Rule stays active elsewhere. |
| Out of scope | Formatting (`ruff format`, prettier), `django-stubs` + strict mypy, frontend type checking (no TypeScript), CI. |
| Honesty requirement | The gate row records that mypy without `django-stubs` barely checks `backend/api/` — untyped imports become `Any`. Real coverage is `knowledge_graph/` and the MCP server. |
| Path wiring | `MYPYPATH` is set in the Makefile, not `mypy.ini` (`mypy_path` is cwd-relative and the MCP run happens from a subdirectory); `[mypy-knowledge_graph.*] ignore_missing_imports = False` makes a broken path fail loudly instead of silently typing `Storage` as `Any`. |

## Acceptance criteria — all met

- [x] **AC1** — `make lint` exits 0 across backend, MCP server, and `frontend/src/`.
- [x] **AC2** — an introduced unused import makes `make lint` exit **2**, naming file and rule.
- [x] **AC3** — `make typecheck` exits 0, running mypy in both venvs.
- [x] **AC4** — an introduced bad return type makes `make typecheck` exit **2**, naming the error.
- [x] **AC5** — eslint covers all 13 `.vue`/`.js` files under `frontend/src/` with zero findings.
- [x] **AC6** — `make check` runs lint + typecheck + both suites and exits 0 (needs Docker, via `make test`).
- [x] **AC7** — `make test` 44/44 and `make mcp-test` 6/6 still green after the cleanup.
- [x] **AC8** — `ENV_SCRIPTS.md`, `WORKFLOW_STATUS.md` gate rows, and `AGENTS.md` updated; the stale open decision deleted.

AC2 and AC4 are the anti-vacuity checks: a misconfigured gate and a clean codebase look identical from a passing run alone. That requirement is now a framework rule in `WORKFLOW_STATUS.md` for any work item that adds a check.

## Outcome

**Complete.** Commit `5840bfa` (+ purge follow-up). 18 ruff violations and 1 eslint error fixed; `ALLOWED_HOSTS` annotated after a genuine mypy catch. 004's `sys.path` import seam was pre-verified against both gates — including a negative control proving the loud-failure override works. Full PLAN/BUILD/REFLECT reasoning preserved in git history at `5840bfa`.
