# Workflow Status

**Episodic memory** — what happened: a record of work done over time, plus the framework for capturing it and knowing when to let it go.

Each feature or task gets a **work item file** in [`changes/`](../changes/) capturing its acceptance criteria, the decisions made, and the outcome. Once a task is committed the working scaffolding — implementation plans, stage tracking — is **purged**; the acceptance criteria and the outcome stay, the noise goes.

This file holds the pointer and the history. The detail lives in the work item. Companion: [ENV_SCRIPTS.md](ENV_SCRIPTS.md) (procedural — how to run everything). **Update this file at the end of every run.** If it disagrees with `git log`, `git log` wins — fix this file.

---

# Part 1 — The framework

## The sign-off rule

**Only the human partner may mark a stage complete.** An agent never ticks a stage box for itself.

When an agent believes a stage is done it sets that stage to `awaiting sign-off`, reports the evidence, and **stops**. Work does not flow into the next stage until the user says so.

This deliberately **overrides** two defaults that otherwise apply:

- `superpowers:subagent-driven-development`'s "do not pause to check in with your human partner between tasks"
- the general autonomous-operation default ("don't ask permission for reversible work that follows from the request")

Inside a stage, autonomy is full — work through the tasks without check-ins. At a stage boundary, stop. If a plan or skill says to continue past a gate, this rule wins.

## The four stages

Every piece of work moves through these in order. Each lists its **inputs**, its **outputs**, and the **exit rule** that must hold before sign-off is requested.

### 1. PLAN

Break the work into testable tasks; define the test strategy and file changes **before touching code**.

- **Inputs:** the request (a `prompts/NNN-*.md` artifact or a direct instruction); relevant `context/` docs; the current code; this file, for what is already in flight.
- **Outputs:** one work item at `changes/NNN-name.md` (from [`changes/TEMPLATE.md`](../changes/TEMPLATE.md)) filled through its PLAN section — goal, acceptance criteria, task breakdown, test strategy, file-change list, out-of-scope, open questions.
- **Exit rule — all must hold:**
  - Every acceptance criterion is Given-When-Then and **names the test that will prove it** (file + test name), or states why it cannot be automated.
  - Every task is independently testable and maps to at least one criterion.
  - The file-change list names each file and whether it is created, modified, or deleted.
  - Open questions are answered — not carried into BUILD.
  - **No production code written yet.**

### 2. BUILD & ASSESS

Implement and validate.

- **Inputs:** the signed-off work item.
- **Outputs:** the code and tests; the work item's BUILD & ASSESS section recording what was implemented, any deviation from the plan and why, and the verification evidence (command run + actual output).
- **Exit rule — all must hold:**
  - **Every check that is configured passes cleanly**, with the real output pasted into the work item — not "it passes" as a bare claim.
  - Each acceptance criterion is demonstrated by the test named for it in PLAN.
  - Nothing outside the planned file-change list was touched, or the deviation is recorded.

  The intended gate is **tests + linting + type checking, all clean**. What is configured today:

  | Check | Command | Status |
  |-------|---------|--------|
  | Tests (backend) | `make test` | ✅ configured — 44 tests |
  | Tests (MCP server) | `make mcp-test` | ✅ configured — 18 tests (pytest); hermetic, needs no Docker |
  | Linting | `make lint` | ✅ configured — ruff (all Python) + eslint (`frontend/src/`) |
  | Type checking | `make typecheck` | ✅ configured — mypy, **backend + MCP server**. Caveat: without `django-stubs` it barely checks `backend/api/` (untyped imports become `Any`); real coverage is `knowledge_graph/` and the MCP server. |

  `make check` runs all four in one command (and needs Docker, because `make test` does).

  **A work item that adds a check must demonstrate that check failing.** Introduce a defect the new check should catch, record the non-zero exit, revert it. A misconfigured check and a genuinely clean codebase are indistinguishable from a passing run alone — this rule is why 003 could claim a working gate rather than a hopeful one.

  **All four are configured — run every one and paste its real output.** `make check` is the single command. Read the type-checking caveat before citing a clean mypy run as evidence about `backend/api/`. If a future check is added in a ⏳ state, the same rule applies: never report one that does not exist.

### 3. REFLECT & ADAPT

Assess the friction; adjust the remaining tasks or the process itself.

- **Inputs:** the BUILD notes; the friction actually hit — surprises, rework, missing context, awkward tooling.
- **Outputs:** the work item's REFLECT & ADAPT section: each friction point with a **disposition** (fixed now / deferred, with where it is recorded / accepted), any adjustment to remaining tasks, and any proposed change to the process or docs (`AGENTS.md`, `context/`, `memory/`, a new Makefile target).
- **Exit rule:** every friction point has a disposition; task adjustments are written into the work item; process and doc changes are applied or explicitly declined. "No friction" is a valid reflection when true — say so plainly rather than inventing lessons.

### 4. COMMIT & PICK NEXT

- **Inputs:** a green build and the reflection dispositions.
- **Outputs:** the commit(s); updated docs and READMEs; a numbered `JOURNAL.md` entry; the purge commit; this file updated with the next work item.
- **Exit rule — all must hold:**
  - The commit message states what changed and why, in the repo's style (`feat:`, `fix:`, `docs:`, `chore:`).
  - Docs describing what changed are updated **in the same commit** (`context/`, `config-service/README.md`, `memory/`).
  - The working tree is clean.
  - The purge commit has landed.
  - The next work item is identified, or the user is told nothing is queued.

## Work item structure

One file per unit of work: `changes/NNN-short-name.md`, zero-padded and sequential, matching the numbering already used in `prompts/`. Start from [`changes/TEMPLATE.md`](../changes/TEMPLATE.md).

The work item is the **single source of detail** — this file never copies its contents. It carries the goal, the stage table with sign-off state, acceptance criteria, inputs and outputs, tasks, test strategy, file changes, out-of-scope, open questions, and one notes section per stage.

## Acceptance criteria format

Given-When-Then, because it forces observable behaviour:

```
- [ ] AC1 — Given an application with no configurations,
      When the client GETs /api/applications/{id}/configurations/,
      Then the response is 200 with an empty JSON array.
      Test: backend/api/tests.py::ConfigurationAPITest::test_list_empty
```

- **Observable behaviour only.** "The serializer is clean" is not a criterion; "POST with a duplicate name returns 400" is.
- **Every criterion names its test.** If one genuinely cannot be automated (a visual check), say so and name the manual step.
- Criteria are written in PLAN and are **not** quietly rewritten during BUILD to match what got built. If a criterion turns out wrong, change it deliberately, note it, and re-confirm.

## Purge discipline

Once a work item's code is committed, the stage scaffolding is noise. The code is the truth.

**Order matters:** commit the work **with the PLAN / BUILD / REFLECT notes intact**, then remove them in a **follow-up commit** (`docs: purge stage notes from changes/NNN`). The reasoning is preserved in git history and merely stops cluttering the working tree — purging before the first commit would delete reasoning that was never recorded anywhere.

After the purge a work item keeps only: title, number, and goal; the acceptance criteria and the fact that they are met; the completion marker and the commit range. Everything else goes.

---

# Part 2 — Where we are

## Active work item

**None in flight.** Work items 003–007 all received sign-off on 2026-08-25 and are closed. Nothing is queued; see [Open decisions](#open-decisions) for candidates.

## Current position

- **Branch:** `main` (tracks `origin/main`); no feature branches open — merged branches are deleted after fast-forward.
- **Health:** `make check` green end to end, verified 2026-08-24 — ruff + eslint clean, mypy clean (21 backend + 5 MCP files), 44 backend tests, 18 MCP tests. `make up` end-to-end verified 2026-08-03.
- **Uncommitted:** nothing.

## Completed work

Predates the `changes/` convention — the record is the journal entries and commits below, not backfilled work items.

| # | Work | Artifacts | Result | Journal |
|---|------|-----------|--------|---------|
| 1 | Full stack app: specs → prompt → plan → implementation | `prompts/1`–`4` | Merged `8cd130e` (Django 5.1 / DRF 3.15, User API + SPA, 7 tests) | Entries 1–3 |
| 2 | Versions upgrade | `prompts/5`–`7` | Merged `bf9935b..4ff19f4` (Django 5.2.16, DRF 3.17.1, psycopg2-binary 2.9.12, cors-headers 4.9.0, Python 3.14) | Entries 4–5 |
| 3 | Semantic-memory docs | `context/*.md` | Written; kept current with the code | Entries 6–7 |
| 4 | Config-storage expansion | `prompts/8` | Merged `f36d1c9..9816aa2` via `feature/config-storage` (Application + Configuration models, nested API, CRUD UI; 34 tests) | Entry 8 |
| 5 | Developer tooling | `config-service/Makefile` | Committed; every target verified | Entry 9 |
| 6 | Memory framework: procedural + episodic, four-stage process | `memory/*.md`, `changes/TEMPLATE.md` | Committed `980ba66` | Entries 10–14 |
| 7 | Knowledge graph CLI (first work item under the four-stage process) | `changes/001`, `knowledge/`, `backend/knowledge_graph/` | Committed `a91a4aa` (+ purge commit); 44/44 tests | Entries 15–17 |
| 13 | SDLC guardrails skill: the four-stage process as a triggerable `.claude/skills/` skill, proven by behavioural subagent evals (with-skill 100% vs baseline 51%; baseline wrote unplanned code and committed under pressure despite AGENTS.md) | `changes/007`, `.claude/skills/config-service-sdlc/` | Committed (+ purge); `make check` green; MCP server registered user-scope in Claude Code | Entries 28–29 |
| 12 | Inspector config + README fix: the documented Inspector command had never been run and did not work | `changes/006`, `my-domain-lang-mcp/inspector.json` | Committed `19727ca` (+ purge); every documented command executed | Entry 27 |
| 11 | Move the MCP server beside `backend/` and `frontend/` — it is a peer deliverable, not part of the Django project | `changes/005`, `config-service/my-domain-lang-mcp/` | Committed `b8c7811` (+ purge); `git mv`, no test changes needed, gate green | Entry 26 |
| 10 | MCP Phase 2: the knowledge graph as four MCP tools, via direct import | `changes/004`, `stdio_server/tools.py` | Committed `a82d322` (+ purge); 18 MCP tests, hermetic | Entry 25 |
| 9 | Lint + type checking: the four-check quality gate (`make check`) | `changes/003`, `ruff.toml`, `mypy.ini`, `eslint.config.js` | Committed `5840bfa` (+ purge); gates proven able to fail, not just pass | Entry 24 |
| 8 | MCP stdio server, Phase 1: handshake + protocol-layer error handling (incl. spec-conformance middleware for unknown tools) | `changes/002`, `my-domain-lang-mcp/` (moved there by 005) | Committed `c602243` (+ purge commit); 6/6 MCP + 44/44 backend tests | Entries 18–22 |

## Open decisions

- **CI still does not exist.** Lint and type checking now run locally (003), but nothing runs them automatically. If a pipeline is added, document it in `ENV_SCRIPTS.md` under Environments and say which checks it runs.
- `JOURNAL.md` entries 1–4 still carry "[enter after the run completes]" in Cost/Reflections (entries 2–4 also omit Tool/Model) — backfill or leave, your call.
- No seed-data fixture; an empty database shows "No users found." until records are created via the API or admin.
- **Candidates for the next work item** (none started, no numbers assigned):
  1. **Use the MCP server in anger** — it is now registered user-scope in Claude Code (007's session) and `✔ Connected`; real queries are what will show whether the tool descriptions and `warnings` are actually useful.
  2. **Grow the knowledge graph** — five nodes and six edges cover the domain thinly. This is a `knowledge/*.yaml` content change, not code.
  3. **CI** — the four checks exist but nothing runs them automatically.
  4. **MCP resources** — exposing the `context/` docs as MCP resources is the natural companion to the tools.
  5. **Hook-based hard enforcement** — 007's skill is advisory; a `settings.json` PreToolUse hook that mechanically blocks commits without sign-off is the escalation if advisory ever proves insufficient (the evals say it currently suffices: with-skill compliance was 10/10).
  6. **Skill description-trigger optimization** — skill-creator's `run_loop.py` over ~20 realistic queries, deferred from 007.
- **Deferred inside 003, worth revisiting later:** code formatting (`ruff format` / prettier — a large mechanical diff, kept out so it cannot bury substantive fixes) and `django-stubs` + strict mypy (without stubs, mypy barely checks Django code; the gate row records that rather than overclaiming).
