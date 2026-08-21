# NNN — <short title>

> Copy to `changes/NNN-short-name.md` (zero-padded, sequential). Delete these quote blocks as you fill it in.
> Process, gates, and the sign-off rule: [`memory/WORKFLOW_STATUS.md`](../memory/WORKFLOW_STATUS.md).

**Goal:** <one or two sentences: what this work item delivers and why>

## Stages

> Only the human partner ticks these. An agent sets `awaiting sign-off` and stops.

| Stage | State | Signed off |
|-------|-------|------------|
| 1. PLAN | not started / in progress / awaiting sign-off | ☐ |
| 2. BUILD & ASSESS | not started | ☐ |
| 3. REFLECT & ADAPT | not started | ☐ |
| 4. COMMIT & PICK NEXT | not started | ☐ |

## Inputs

> What this work consumes: spec/prompt files, context docs, existing code or endpoints, decisions already made.

-

## Outputs

> What exists when this is done: files, endpoints, UI routes, migrations, docs.

-

---

## 1. PLAN

### Acceptance criteria

> Given-When-Then, observable behaviour only. Each names the test that proves it (file + test name), or says why it can't be automated.

- [ ] **AC1** — Given <state>, When <action>, Then <observable result>.
      Test: `<file>::<test name>`
- [ ] **AC2** — Given …, When …, Then ….
      Test: `<file>::<test name>`

### Tasks

> Each independently testable, each mapping to at least one AC.

- [ ] T1 — <task> (AC1)
- [ ] T2 — <task> (AC2)

### Test strategy

> What kind of tests, at what level, and what is deliberately not tested.

-

### File changes

| File | Change | Purpose |
|------|--------|---------|
| `path/to/file` | create / modify / delete | <why> |

### Out of scope

-

### Open questions

> Must be empty (answered) before PLAN can be signed off.

-

---

## 2. BUILD & ASSESS

> Fill in during implementation.

**Implemented:** <what was actually built>

**Deviations from plan:** <what differed and why — or "none">

**Verification evidence:**

```
$ make test
<paste the actual output>
```

> Paste the output of every configured check. Today that is `make test` only — `make lint` / `make typecheck` are planned but do not exist yet, so do not claim a check that never ran. See "Open decisions" in memory/WORKFLOW_STATUS.md.

---

## 3. REFLECT & ADAPT

> Every friction point gets a disposition: fixed now / deferred (say where it's recorded) / accepted.

| Friction | Disposition |
|----------|-------------|
| <what slowed things down or surprised us> | <fixed now / deferred → where / accepted> |

**Adjustments to remaining tasks:** <or "none">

**Process or doc changes:** <AGENTS.md, context/, memory/, Makefile — applied or declined>

---

## 4. COMMIT & PICK NEXT

**Commits:** `<base7>..<head7>` — <commit message summary>

**Docs updated:** <which files, in the same commit>

**Journal entry:** #<n>

**Next work item:** <NNN-name, or "none queued">

---

> **Purge (after the work is committed):** in a follow-up commit, delete sections 1–4's working notes and keep only the title, goal, acceptance criteria with their met/unmet state, the completion marker, and the commit range. The reasoning stays in git history; the scaffolding stops cluttering the tree.
