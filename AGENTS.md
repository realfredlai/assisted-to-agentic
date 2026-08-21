# Agent Instructions

## Process — read before starting work

**`memory/WORKFLOW_STATUS.md`** defines the four stages every piece of work follows — PLAN → BUILD & ASSESS → REFLECT & ADAPT → COMMIT & PICK NEXT — with the inputs, outputs, and exit rule for each, plus the work-item format and purge discipline.

**Only the human partner may mark a stage complete.** When you think a stage is done, set it to `awaiting sign-off`, report the evidence, and stop. This overrides the usual "keep going without checking in" defaults, including `superpowers:subagent-driven-development`'s no-pause rule. Inside a stage, work autonomously; at a stage boundary, stop.

Work-item detail lives in `changes/NNN-name.md` (start from `changes/TEMPLATE.md`), never in the status file.

## Memory framework

Read at the start of each conversation; load selectively as the task requires.

**Semantic memory — what the system is** (`context/`):

- `context/ABOUT.md` — project purpose, personas, and constraints
- `context/ARCHITECTURE.md` — the how: patterns, data flow, and key decisions
- `context/DOMAIN.md` — the what: the config-service domain (user directory, application registry, configurations) and use cases
- `context/IMPLEMENTATION.md` — languages, versions, dependencies, preferences

**Procedural memory — how things work** (`memory/ENV_SCRIPTS.md`): environments and ports, environment variables, every developer script (`make` targets), and when it is acceptable to go off-script.

**Episodic memory — what happened** (`memory/WORKFLOW_STATUS.md`, `changes/`, `JOURNAL.md`): the stage framework and sign-off rule, the current pointer and history, per-task work items, and the append-only run log (add a numbered entry per run).

## Standing rules

- Run everyday tasks through `config-service/Makefile` (`make up`, `make test`, …) rather than raw docker/`manage.py`/npm commands. `memory/ENV_SCRIPTS.md` says when going off-script is appropriate.
- Do not add dependencies without approval.
- Lint/type-check tooling and CI are planned but do not exist yet — run and report every check that *is* configured (`make test`), and never report one that isn't.
- Never destroy data (`make db-destroy`, dropping volumes or tables) without explicit permission.
- Keep docs current in the same commit as the change they describe.
