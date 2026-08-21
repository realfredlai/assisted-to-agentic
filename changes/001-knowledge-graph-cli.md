# 001 — Knowledge graph CLI

**Goal:** Give `config-service` a machine-queryable projection of its domain language: hand-authored YAML nodes/edges describing the domain terms, imported into a local SQLite store, queried through a `manage.py knowledge` CLI. Modelled on `assisted-to-agentic-module-5/examples/knowledge-graph`, adapted to this project's stack and dependency rules.

## Stages

| Stage | State | Signed off |
|-------|-------|------------|
| 1. PLAN | complete | ☑ signed off by user ("start build", 2026-08-19) |
| 2. BUILD & ASSESS | complete | ☑ signed off by user (2026-08-19) |
| 3. REFLECT & ADAPT | complete | ☑ signed off by user ("go for it", 2026-08-19) |
| 4. COMMIT & PICK NEXT | **awaiting sign-off** | ☐ |

## Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Knowledge file format | YAML (`PyYAML` — new dependency, user-approved) | Comments and multi-line definitions matter for hand-authoring; matches the reference |
| CLI shape | Django management command (`manage.py knowledge`) | Idiomatic here, zero further dependencies, works with the database down |
| Storage | SQLite file (`knowledge.db`, gitignored), not Postgres/ORM | Domain language is not application data; zero-infrastructure; swappable behind the CLI |
| Output format | JSON default, `--format table` for humans | JSON default keeps the CLI subprocess-wrappable (future MCP server) |
| Source of truth | `context/DOMAIN.md`; the YAML is a derived projection | Declared in YAML headers + per-node back-links; shipped-YAML test guards import/validate |
| Out of scope | REST surface (would be DRF, not FastAPI), MCP server, UI | Request was "cli and knowledge"; candidates for later work items |

## Acceptance criteria — all met

- [x] **AC1** — import populates the store and reports node/edge counts
- [x] **AC2** — import rejects duplicate node ids, exits non-zero
- [x] **AC3** — lookup resolves id, name, and alias, case-insensitively
- [x] **AC4** — unknown term prints `{"error": "not_found", …}` and exits non-zero
- [x] **AC5** — related returns outgoing edges only (directed)
- [x] **AC6** — list-areas returns distinct areas, sorted
- [x] **AC7** — validate detects orphan edges; clean graph passes
- [x] **AC8** — the shipped knowledge/ tree imports (5 nodes, 6 edges) and validates cleanly
- [x] **AC9** — `--format table` prints human-readable output
- [x] **AC10** — `make knowledge-import` / `knowledge-validate` / `knowledge-lookup` work (verified with Docker down)

Proven by `knowledge_graph/tests.py` (10 tests; suite 44/44 green) and recorded manual runs.

## Outcome

**Complete.** Commits: `980ba66` (memory-framework docs precursor), `a91a4aa` (feature — app, YAML, Makefile targets, docs), plus the purge follow-up. Full PLAN/BUILD/REFLECT notes preserved in git history at `a91a4aa`.
