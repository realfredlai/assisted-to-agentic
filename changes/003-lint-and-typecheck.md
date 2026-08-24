# 003 — Lint and type checking

> Process, gates, and the sign-off rule: [`memory/WORKFLOW_STATUS.md`](../memory/WORKFLOW_STATUS.md).

**Goal:** Make the BUILD & ASSESS gate real. Add lint and type checking to every part of the repo that can carry them, fix the existing violations, and wire them into `make` so the ⏳ rows in the gate table become ✅ — replacing a two-check gate that runs on trust with a four-check gate that runs on command.

## Stages

| Stage | State | Signed off |
|-------|-------|------------|
| 1. PLAN | signed off 2026-08-24 ("go all the way") | ☑ |
| 2. BUILD & ASSESS | complete | ☑ |
| 3. REFLECT & ADAPT | complete | ☑ |
| 4. COMMIT & PICK NEXT | in progress | ☐ |

## Inputs

- The user's instruction (2026-08-24) to implement this alongside MCP Phase 2 — which carries the **dependency approval** this item has been blocked on since 2026-08-19.
- The four-point update checklist in `memory/WORKFLOW_STATUS.md` → Open decisions (requirements/package.json → Makefile → ENV_SCRIPTS → gate rows).
- The code to be checked: `backend/api/`, `backend/knowledge_graph/`, `backend/my-domain-lang-mcp/stdio_server/`, `frontend/src/` (13 `.vue`/`.js` files).
- **Empirical sizing done during PLAN** (versions and violation counts below are measured, not assumed).

## Outputs

`ruff.toml`, `mypy.ini`, `frontend/eslint.config.js`, the tool pins in three dependency files, `make lint` / `lint-fix` / `typecheck` / `check`, a clean run of all of them, and the docs (`ENV_SCRIPTS.md`, `WORKFLOW_STATUS.md` gate rows, `AGENTS.md`) telling the truth about what is now configured.

---

## 1. PLAN

### Decisions

| Decision | Choice | Why / alternatives |
|----------|--------|--------------------|
| Python linter | **ruff 0.16.4** (exact pin) | One fast tool covering flake8 + isort + pyupgrade + bugbear. Alternatives (flake8 + isort + black separately) mean three dependencies and three configs. |
| Ruff ruleset | `select = ["E", "F", "I", "B", "UP", "SIM", "RUF"]`, `line-length = 100` | Measured: this finds **~20 violations** repo-wide, roughly half auto-fixable — a real but small cleanup. Note ruff 0.16.4's *implicit* defaults already include `RUF`/`SIM`/`PLR` (verified with `--isolated`), so an explicit `select` is what makes the gate reproducible rather than version-dependent. |
| Code formatting | **Out of scope** — lint only, no `ruff format` | Formatting the whole repo is a large mechanical diff that would bury the substantive fixes. Deferred as its own decision, noted in ENV_SCRIPTS. |
| Type checker | **mypy 2.3.1** (exact pin), `--ignore-missing-imports`, default strictness | Measured: `api/`, `knowledge_graph/`, all pass **clean today** at this setting. Starting strict would mean a large annotation project; starting here makes the gate real immediately and can be tightened later. |
| Type-check scope + honesty | All of `backend/` and the MCP server, **but** the gate row must record that mypy without `django-stubs` barely checks Django code (untyped imports become `Any`) — real value lands on `knowledge_graph/` and `stdio_server/` | Measured: `api/` passes trivially. Claiming "type checking ✅" without this caveat would be exactly the overclaiming this framework exists to prevent. `django-stubs` deferred. |
| mypy across two venvs | Pinned at the **same version** in both `backend/requirements.txt` and `my-domain-lang-mcp/requirements.txt`; `make typecheck` runs it once per project from that project's venv | The MCP server's imports (`mcp`, `pytest`) only resolve inside its own venv; a single mypy run from the backend venv would silently skip them. Same-version pinning is called out in ENV_SCRIPTS so the two cannot drift. |
| JS/Vue linter | **eslint 10.9.0** + **eslint-plugin-vue 10.10.0**, flat config `eslint.config.js` | The Vue scaffold declined eslint originally; this reverses that deliberately. Flat config is the current format. |
| Frontend type checking | **None** — and say so | There is no TypeScript in this project, so there is nothing for `vue-tsc` to check. `make typecheck` covers Python only; the docs must not imply otherwise. |
| Make targets | `lint`, `lint-fix`, `typecheck`, and **`check`** = lint + typecheck + test + mcp-test | The gate is four checks; `make check` makes "run the gate" one command. `lint-fix` exists because ~half the findings are auto-fixable. |
| Config file locations | `config-service/ruff.toml` and `config-service/mypy.ini` (not `pyproject.toml`) | This repo has no `pyproject.toml` anywhere — backend and MCP server both use `requirements.txt`. Introducing one just to hold tool config would imply a packaging story that does not exist. |
| **Accommodating 004's `sys.path` import seam** | Establish the convention now: an inline **`# noqa: E402`** at the deliberate late import, plus **`mypy_path`** in `mypy.ini` so the MCP project resolves `knowledge_graph.*` | **Measured, and this would otherwise break the gate the day after it is built.** 004's `tools.py` must `sys.path.insert(...)` *before* `from knowledge_graph.storage import …` — that ordering is the mechanism, not a mistake, and it triggers ruff **E402** (verified: fires without the noqa, clean with it). mypy separately reports `import-not-found` for that module (verified) — and note `--ignore-missing-imports` "fixes" it only by treating `Storage` as `Any`, which is false comfort; `mypy_path` makes it genuinely checked (verified: exit 0 with real resolution). Inline `noqa` is preferred over a blanket per-file-ignore so the exemption is visible at the one line it applies to. **If the user reverses the 003→004 order, 004 owns adding both.** |

### Acceptance criteria

- [x] **AC1** — Given the repo with the tooling installed, When `make lint` runs, Then it exits 0 with no reported violations across `backend/` (excluding `venv/` and `migrations/`), the MCP server, and `frontend/src/`.
      Test: manual gate command — `make lint`; output pasted into BUILD. (Not automatable as a unit test: the linter *is* the test.)
- [x] **AC2** — Given a deliberately introduced violation (an unused import in `backend/knowledge_graph/storage.py`), When `make lint` runs, Then it exits **non-zero** and names that file and rule.
      Test: manual, recorded in BUILD — proves the gate can actually fail, not just pass vacuously. Violation reverted immediately after.
- [x] **AC3** — Given the repo, When `make typecheck` runs, Then it exits 0, having run mypy in **both** venvs (backend and MCP server), with each project's run visible in the output.
      Test: manual gate command — `make typecheck`; output pasted into BUILD.
- [x] **AC4** — Given a deliberately introduced type error (`def list_areas(self) -> int:` returning a list in `storage.py`), When `make typecheck` runs, Then it exits non-zero and names the error.
      Test: manual, recorded in BUILD. Same anti-vacuity check as AC2, and it must be introduced in a file mypy genuinely checks — not in `api/`, where untyped Django imports would let it pass.
- [x] **AC5** — Given the frontend, When `make lint` runs, Then eslint checks all 13 `.vue`/`.js` files under `frontend/src/` and reports no violations.
      Test: manual — the eslint portion of `make lint` output, showing the file count.
- [x] **AC6** — Given a clean tree, When `make check` runs, Then it runs lint, typecheck, backend tests, and MCP tests in that order and exits 0 — and if any one fails, `make check` exits non-zero.
      Test: manual gate command; the failure half proven by re-using the AC2 violation.
      Note: `make check` **requires Docker**, because `make test` depends on `db-up`. `make lint`, `make typecheck`, and `make mcp-test` are each Docker-free; only the aggregate needs the database.
- [x] **AC7** — Given the existing suites, When the cleanup is complete, Then `make test` still reports 44/44 and `make mcp-test` 6/6 — no behaviour changed by a lint fix.
      Test: `backend/api/tests.py`, `backend/knowledge_graph/tests.py`, `stdio_server/main_test.py` (existing suites, unchanged).
- [x] **AC8** — Given the docs, When the work is committed, Then `ENV_SCRIPTS.md` has real commands in place of its "planned, not yet configured" section, `WORKFLOW_STATUS.md`'s gate rows read ✅ **with the django-stubs caveat recorded**, `AGENTS.md`'s "lint/type-check do not exist yet" rule is rewritten, and the stale open decision is deleted.
      Test: manual doc review at stage 4 (not automatable).

### Tasks

- [x] T1 — Add pins: `ruff` + `mypy` to `backend/requirements.txt`, `mypy` (same version) to `my-domain-lang-mcp/requirements.txt`; eslint devDeps + `lint` script to `frontend/package.json`. Install into both venvs. (AC1, AC3, AC5)
- [x] T2 — Write `ruff.toml`, `mypy.ini`, `frontend/eslint.config.js`. (AC1, AC3, AC5)
- [x] T3 — Add `lint`, `lint-fix`, `typecheck`, `check` to the Makefile. (AC1, AC3, AC5, AC6)
- [x] T4 — Fix the violations: `ruff check --fix` for the auto-fixable half, then the rest by hand (measured: mostly import sorting, `raise ... from` inside except blocks, mutable class defaults, line length). Re-run both suites after. (AC1, AC7)
- [x] T5 — Prove the gates can fail: introduce and revert the AC2 lint violation and the AC4 type error, recording both outputs. (AC2, AC4, AC6)
- [x] T6 — Update `ENV_SCRIPTS.md`, `WORKFLOW_STATUS.md` gate rows + open decision, `AGENTS.md`. (AC8)

### Test strategy

This work item's deliverable *is* test infrastructure, so its acceptance is demonstrated by running the gates and pasting real output rather than by new unit tests — with a **deliberate-failure check for each gate** (AC2, AC4), because a linter that passes because it is misconfigured and a linter that passes because the code is clean look identical from the outside. The existing 50 tests (44 backend + 6 MCP) serve as the regression net for the cleanup itself (AC7).

Deliberately not tested: the linters' own correctness; formatting; CI (still does not exist).

### File changes

| File | Change | Purpose |
|------|--------|---------|
| `changes/003-lint-and-typecheck.md` | create | this work item |
| `config-service/ruff.toml` | create | ruff ruleset + excludes |
| `config-service/mypy.ini` | create | mypy settings |
| `config-service/frontend/eslint.config.js` | create | eslint flat config |
| `config-service/backend/requirements.txt` | modify | pin `ruff`, `mypy` |
| `config-service/backend/my-domain-lang-mcp/requirements.txt` | modify | pin `mypy` (same version) |
| `config-service/frontend/package.json` | modify | eslint devDeps + `lint` script |
| `config-service/Makefile` | modify | `lint`, `lint-fix`, `typecheck`, `check` |
| backend + frontend source files | modify | fix the ~20 violations; exact list recorded at BUILD |
| `memory/ENV_SCRIPTS.md` | modify | replace the "not configured" section |
| `memory/WORKFLOW_STATUS.md` | modify | flip gate rows to ✅ with caveat; delete the open decision |
| `AGENTS.md` | modify | rewrite the "lint/type-check do not exist yet" standing rule |
| `config-service/README.md`, `context/ARCHITECTURE.md` | modify (stage 4) | document the checks |
| `JOURNAL.md` | modify | entry per run |

### Out of scope

- **Code formatting** (`ruff format`, prettier) — deferred, see Decisions.
- **`django-stubs`** and strict mypy — deferred; the gate records what it does and does not cover.
- **CI** — still no pipeline; this makes the checks runnable locally, nothing more.
- Frontend type checking (no TypeScript exists).
- Any behaviour change: lint fixes must be behaviour-preserving, guarded by AC7.

### Open questions

None. The one blocker — approval for `ruff`, `mypy`, `eslint`, `eslint-plugin-vue` as new dependencies — is carried by the user's instruction to implement this item; the exact pins are listed above for confirmation at sign-off.

---

## 2. BUILD & ASSESS

**Implemented:** `ruff.toml`, `mypy.ini`, `frontend/eslint.config.js`; `ruff==0.16.4` + `mypy==2.3.1` pinned in `backend/requirements.txt`, `mypy==2.3.1` (same version) in the MCP project's; eslint devDeps + a `lint` script in `package.json`; Makefile targets `lint`, `lint-fix`, `typecheck`, `check`. All 18 ruff violations and the 1 real eslint error fixed; `ALLOWED_HOSTS` annotated after a genuine mypy catch. Docs rewritten in `ENV_SCRIPTS.md`, `WORKFLOW_STATUS.md` (gate rows + prose + open decision), `AGENTS.md`.

**Deviations from plan:**

1. **eslint preset `flat/recommended` → `flat/essential`.** `recommended` produced **112 warnings**, essentially all `vue/max-attributes-per-line` and `vue/singleline-html-element-content-newline` — i.e. formatting, which this plan explicitly put out of scope. `essential` is the correctness-only preset, leaving exactly **1 real finding** (an unused `catch (e)` binding in `ConfigurationFormView.vue`, fixed with optional catch binding). Keeping `recommended` would have meant either a repo-wide reformat or a gate that tolerates 112 warnings.
2. **Two extra frontend devDependencies:** `@eslint/js` and `globals`, beyond the planned `eslint` + `eslint-plugin-vue`. Flat config needs them to reference the recommended JS ruleset and browser globals.
3. **`--max-warnings 0` added** to the eslint script. A gate that passes with warnings outstanding is not a gate; this makes warnings fail like errors.
4. **RUF012 per-file-ignores** for `backend/api/models.py` and `serializers.py`. All 10 RUF012 hits are Django/DRF declarative inner classes (`Meta.ordering`, `Meta.fields`, `read_only_fields`) — plain lists by framework convention. The rule wants `ClassVar` annotations, which fight the idiom for no safety gain; the rule stays active everywhere else. The plan assumed every violation would be *fixed*; this one is *scoped* instead, deliberately and in writing.
5. **mypy path wiring moved from `mypy.ini` to the Makefile.** `mypy_path` is resolved relative to the working directory, and the MCP run happens from `backend/my-domain-lang-mcp/`, where `mypy_path = backend` would point at a directory that does not exist. The Makefile passes `MYPYPATH=$(CURDIR)/backend` explicitly instead. `mypy.ini` keeps `[mypy-knowledge_graph.*] ignore_missing_imports = False` so a broken path **fails loudly** rather than silently degrading `Storage` to `Any`.

**Accommodating 004 (verified, not assumed):** a throwaway probe file carrying 004's exact import seam (`sys.path.insert` then `from knowledge_graph.storage import Storage`) was run through both gates and removed. Ruff: clean with the inline `# noqa: E402`. Mypy: clean with `MYPYPATH` — and the **negative control without it** produced `Cannot find implementation or library stub for module named "knowledge_graph.storage" [import-not-found]`, proving the loud-failure override works rather than passing vacuously.

**Verification evidence:**

```
$ make lint
backend/venv/bin/ruff check .
All checks passed!
cd frontend && npm run lint          # eslint src --max-warnings 0
(exit 0)

$ make typecheck
--- backend ---
Success: no issues found in 21 source files
--- mcp server ---
cd backend/my-domain-lang-mcp && MYPYPATH=.../backend venv/bin/mypy --config-file .../mypy.ini stdio_server
Success: no issues found in 3 source files

$ make check
... Ran 44 tests in 0.273s / OK
... 6 passed in 1.99s
All checks passed.                   # exit 0
```

Both gates proven able to **fail** (AC2, AC4) — not just to pass:

```
$ # AC2: unused `import os` added to knowledge_graph/storage.py
$ make lint   ->  F401 `os` imported but unused ... Found 2 errors.   exit=2

$ # AC4: list_areas(self) -> int  (still returning a list)
$ make typecheck -> storage.py:150: error: Incompatible return value type
                    (got "list[Any]", expected "int")  [return-value]     exit=2

$ # both reverted; make lint exit=0, make typecheck exit=0
```

Before the cleanup: 18 ruff violations (10 RUF012, 4 I001, 3 B904, 1 SIM117) and 1 eslint error. After: zero, with the RUF012 group scoped rather than fixed (deviation 4).

---

## 3. REFLECT & ADAPT

| Friction | Disposition |
|----------|-------------|
| **A linter's "recommended" preset is not the same as its useful rules.** vue's `flat/recommended` bundles formatting opinions; adopting it would have flooded the gate with 112 whitespace warnings and buried the single real bug. | **Fixed now** — switched to `flat/essential`, matching this item's own out-of-scope decision on formatting. Recorded in `ENV_SCRIPTS.md` so the choice is not silently reverted later. |
| **Default rulesets drift between releases.** ruff 0.16.4's implicit defaults already include `RUF`/`SIM`/`PLR` — not the `E4,E7,E9,F` I would have assumed. Measured with `--isolated`. | **Fixed now** — `ruff.toml` pins an explicit `select` list, so bumping the pin cannot silently change what the gate means. |
| **Framework idiom vs lint rule.** RUF012 flags Django/DRF `Meta` classes, which are declarative by design. | **Fixed now** — narrow per-file-ignores with a comment explaining why, rather than disabling the rule globally or annotating framework code into submission. |
| **`mypy_path` is cwd-relative**, so the shared `mypy.ini` could not serve a run launched from the MCP subdirectory — and `--ignore-missing-imports` would have hidden the breakage by treating `Storage` as `Any`. | **Fixed now** — explicit `MYPYPATH` in the Makefile plus an `ignore_missing_imports = False` override for `knowledge_graph.*`, verified with a negative control. This was the advisor's catch during PLAN; without it 003 would have signed off green and 004 would have broken the gate the next day. |
| Flat eslint config needs `@eslint/js` and `globals` beyond the two planned packages. | **Accepted** — two small, standard devDependencies; recorded as deviation 2. |

**Adjustments to remaining tasks:** none. 004's plan already assumes the `# noqa: E402` + `MYPYPATH` arrangement this item shipped, now verified end-to-end.

**Process or doc changes:** one framework change applied — **a work item that adds a check must demonstrate that check failing**, not just passing. AC2 and AC4 are the reason this item can claim a working gate rather than a possibly-misconfigured one; the rule is now written into `WORKFLOW_STATUS.md`'s BUILD & ASSESS section so the next gate-adding item inherits it.

---

## 4. COMMIT & PICK NEXT

**Commits:**

**Docs updated:**

**Journal entry:**

**Next work item:**
