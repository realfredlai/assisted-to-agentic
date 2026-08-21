# 001 — Knowledge graph CLI

**Goal:** Give `config-service` a machine-queryable projection of its domain language: hand-authored YAML nodes/edges describing the domain terms, imported into a local SQLite store, queried through a `manage.py knowledge` CLI. Modelled on `assisted-to-agentic-module-5/examples/knowledge-graph`, adapted to this project's stack and dependency rules.

## Stages

| Stage | State | Signed off |
|-------|-------|------------|
| 1. PLAN | complete | ☑ signed off by user ("start build", 2026-08-19) |
| 2. BUILD & ASSESS | complete | ☑ signed off by user (2026-08-19) |
| 3. REFLECT & ADAPT | complete | ☑ signed off by user (2026-08-19) |
| 4. COMMIT & PICK NEXT | in progress | ☐ |

## Inputs

- Reference implementation: `/Users/admin/code/Lois/assisted-to-agentic-module-5/examples/knowledge-graph` (Typer CLI + FastAPI + SQLite over YAML; 26 tests)
- `context/DOMAIN.md` — **the source of truth for domain content**; the YAML is a derived projection of it, not a second authority
- `context/ARCHITECTURE.md` — file paths for `source_files` entries
- Existing backend layout, `config-service/Makefile`, `memory/ENV_SCRIPTS.md`

## Outputs

- `config-service/knowledge/{nodes,edges}/*.yaml` — hand-authored domain knowledge
- `config-service/backend/knowledge_graph/` — new Django app: storage, importer, management command, tests
- `config-service/knowledge.db` — generated SQLite store (gitignored)
- Makefile targets, `.gitignore` entry, and doc updates

## Decisions taken before PLAN

| Decision | Choice | Why |
|----------|--------|-----|
| Knowledge file format | **YAML** (`PyYAML`) | Matches the reference; comments and multi-line definitions matter for hand-authoring. **New dependency approved by the user in this session.** |
| CLI shape | **Django management command** | Zero further dependencies, idiomatic here, testable with Django's own framework. Verified: management commands run with the database unreachable, so the reference's zero-infrastructure property holds. |
| Storage | **SQLite file**, not Postgres/ORM | Keeps knowledge out of the app's migration history; single inspectable file; swappable implementation behind a stable CLI. |
| Output format | **JSON by default**, `--format table` for humans | Load-bearing: JSON default is what makes the CLI wrappable by a subprocess (e.g. an MCP server) later. |

---

## 1. PLAN

### Acceptance criteria

- [x] **AC1 — Import populates the store.**
      Given a knowledge directory with 2 node files and 1 edge file,
      When `manage.py knowledge import` runs,
      Then the SQLite file is created and the command reports the node and edge counts.
      Test: `knowledge_graph/tests.py::ImportCommandTest::test_import_reports_counts`

- [x] **AC2 — Import rejects duplicate node ids.**
      Given two nodes sharing the id `application`,
      When `import` runs,
      Then it exits non-zero and names the duplicate id.
      Test: `knowledge_graph/tests.py::ImportCommandTest::test_duplicate_id_fails`

- [x] **AC3 — Lookup resolves by id, name, and alias, case-insensitively.**
      Given an imported node `application` with name `Application` and alias `app`,
      When `knowledge lookup app` (or `Application`, or `APPLICATION`) runs,
      Then it prints that node as JSON with definition, aliases, warnings, source_files.
      Test: `knowledge_graph/tests.py::LookupCommandTest::test_resolves_by_id_name_and_alias`

- [x] **AC4 — Unknown term fails cleanly.**
      Given an imported store,
      When `knowledge lookup nonsense` runs,
      Then it prints `{"error": "not_found", "term": "nonsense"}` and exits non-zero.
      Test: `knowledge_graph/tests.py::LookupCommandTest::test_unknown_term_exits_nonzero`

- [x] **AC5 — Related returns outgoing edges.**
      Given the edge `application --owns--> configuration`,
      When `knowledge related application` runs,
      Then the JSON output contains that edge.
      Test: `knowledge_graph/tests.py::RelatedCommandTest::test_returns_outgoing_edges`

- [x] **AC6 — list-areas returns distinct areas, sorted.**
      Given nodes in areas `config_storage` and `user_directory`,
      When `knowledge list-areas` runs,
      Then it prints both, sorted, with no duplicates.
      Test: `knowledge_graph/tests.py::ListAreasCommandTest::test_distinct_sorted`

- [x] **AC7 — Validate detects orphan edges.**
      Given an edge whose `to` names a node id that does not exist,
      When `knowledge validate` runs,
      Then it exits non-zero and names the missing reference; and given a clean graph it exits zero saying the graph is valid.
      Test: `knowledge_graph/tests.py::ValidateCommandTest::test_orphan_edge_detected` and `::test_clean_graph_passes`

- [x] **AC8 — The real knowledge files import and validate cleanly.**
      Given the committed `config-service/knowledge/` tree,
      When `import` then `validate` run against it,
      Then both succeed and every node id referenced by an edge exists.
      Test: `knowledge_graph/tests.py::RealKnowledgeTest::test_shipped_knowledge_imports_and_validates`

- [x] **AC9 — `--format table` prints human-readable output.**
      Given an imported node with warnings,
      When `knowledge lookup application --format table` runs,
      Then output is plain text including the name, definition, and each warning (not JSON).
      Test: `knowledge_graph/tests.py::LookupCommandTest::test_table_format`

- [x] **AC10 — Make targets work.**
      Given a clean checkout with dependencies installed,
      When `make knowledge-import` then `make knowledge-validate` run,
      Then both succeed.
      Test: manual — no automated test; commands run and output recorded in BUILD evidence.

### Tasks

- [x] T1 — Add `PyYAML` to `backend/requirements.txt`; `make install` (AC1)
- [x] T2 — Create the `knowledge_graph` Django app; register in `INSTALLED_APPS` (AC1)
- [x] T3 — `storage.py`: `Node`/`Edge` dataclasses, schema, `insert_*`, `lookup`, `get_related`, `list_areas`, `validate_consistency` (AC3, AC5, AC6, AC7)
- [x] T4 — `importer.py`: walk `nodes/`+`edges/`, validate required fields, reject duplicate ids (AC1, AC2)
- [x] T5 — `management/commands/knowledge.py`: argparse subcommands `import`, `validate`, `lookup`, `related`, `list-areas`; `--format`, `--db`, `--knowledge-dir` (AC1–AC7, AC9)
- [x] T6 — Author `knowledge/nodes/*.yaml` + `knowledge/edges/*.yaml` from `context/DOMAIN.md` (AC8)
- [x] T7 — Tests in `knowledge_graph/tests.py` using `SimpleTestCase` + `call_command` (AC1–AC9)
- [x] T8 — Makefile targets `knowledge-import`, `knowledge-validate`, `knowledge-lookup TERM=…`; add `knowledge.db` to `make clean` (AC10)
- [x] T9 — `knowledge.db` into `config-service/.gitignore` (AC10)

### Domain content (T6) — derived from context/DOMAIN.md

Nodes, areas `user_directory` and `config_storage`:

| id | name | aliases | key warnings |
|----|------|---------|--------------|
| `user` | User | person, directory entry | **Not** `django.contrib.auth`'s user — nobody logs in as one; email is unique |
| `application` | Application | app | Name unique; deleting cascades to its configurations |
| `app_type` | AppType | application type | Exactly four values: mobile, desktop, web, cloud |
| `configuration` | Configuration | config, config entry | Name unique **per application**; `application` always comes from the URL, never the request body |
| `environment_settings` | EnvironmentSettings | dev/uat/prod settings | Three independent JSON objects; **no Environment entity exists** in this domain; no schema beyond "must be an object" |

Edges: `application owns configuration`, `application classified_by app_type`, `application associated_with user`, `user associated_with application`, `configuration belongs_to application`, `configuration contains environment_settings`.

`source_files` and `documentation` point at real paths (`backend/api/models.py`, `backend/api/serializers.py`, `context/DOMAIN.md`, …), verified to exist during BUILD.

> **Drift risk, accepted deliberately:** the YAML restates facts that `context/DOMAIN.md` owns. Mitigation: DOMAIN.md is declared the source of truth in the YAML header comment and in the work item; a `documentation:` entry on every node points back to it. Revisit if the two ever disagree.

### Test strategy

- Django's own framework (project rule: no pytest). `SimpleTestCase` — these tests touch a temp SQLite file, never Postgres.
- Commands invoked via `call_command(..., stdout=StringIO())`; knowledge trees built in `tempfile.TemporaryDirectory()`.
- One integration test (AC8) runs against the **shipped** YAML, so authoring mistakes fail the suite.
- Not tested: `--format table` exact layout beyond "contains the key fields"; Makefile targets (manual, AC10).

### File changes

| File | Change | Purpose |
|------|--------|---------|
| `config-service/backend/requirements.txt` | modify | Add `PyYAML` |
| `config-service/backend/config/settings.py` | modify | Register `knowledge_graph` in `INSTALLED_APPS` |
| `config-service/backend/knowledge_graph/__init__.py`, `apps.py` | create | Django app |
| `config-service/backend/knowledge_graph/storage.py` | create | SQLite store + query primitives |
| `config-service/backend/knowledge_graph/importer.py` | create | YAML → storage |
| `config-service/backend/knowledge_graph/management/commands/knowledge.py` | create | The CLI |
| `config-service/backend/knowledge_graph/tests.py` | create | AC1–AC9 |
| `config-service/knowledge/nodes/config_service.yaml` | create | Domain nodes |
| `config-service/knowledge/edges/config_service.yaml` | create | Domain edges |
| `config-service/Makefile` | modify | knowledge-* targets; extend `clean` |
| `config-service/.gitignore` | modify | Ignore `knowledge.db` |

Docs updated at stage 4: `config-service/README.md`, `context/ARCHITECTURE.md`, `memory/ENV_SCRIPTS.md` (new commands + test count), `memory/WORKFLOW_STATUS.md` (test count).

### Out of scope

- **REST API surface** — the reference ships FastAPI endpoints; the request was "cli and knowledge". Offered as a follow-up work item; if wanted here, it should be DRF, not FastAPI.
- MCP server wrapping the CLI (the Module 5 exercise proper).
- Frontend UI for browsing the graph.
- Auto-generating YAML from code or from DOMAIN.md.

### Open questions

None — format and CLI shape resolved with the user before planning; storage, placement, and scope decided as recorded above.

---

## 2. BUILD & ASSESS

**Implemented:** all nine tasks. `knowledge_graph` Django app (storage.py, importer.py, `management/commands/knowledge.py` with import/validate/lookup/related/list-areas, JSON default + `--format table`); knowledge tree at `config-service/knowledge/` (5 nodes across `user_directory`/`config_storage`, 6 edges, source-of-truth header pointing at DOMAIN.md); 10 tests in `knowledge_graph/tests.py` (SimpleTestCase, temp SQLite, no Postgres); Makefile targets `knowledge-import`/`knowledge-validate`/`knowledge-lookup TERM=…`; `knowledge.db` gitignored and removed by `make clean`; PyYAML 6.0.3 pinned in requirements.txt. Defaults resolve via `settings.BASE_DIR.parent`, so the command behaves identically from any cwd. Every `source_files`/`documentation` path in the YAML verified to exist.

**Deviations from plan:** none in the file-change list. Two build notes: (1) the reference's `ImportError` class shadowed the Python builtin — renamed `KnowledgeImportError` here; (2) first append to requirements.txt concatenated onto the last line (file had no trailing newline) — caught and rewritten in the same task.

**Verification evidence:**

```
$ make test                       # full suite, Postgres up
Ran 44 tests in 0.281s
OK                                # 34 existing + 10 knowledge_graph

$ make knowledge-import
imported 5 nodes
imported 6 edge(s)

$ make knowledge-validate
knowledge graph is valid

$ make knowledge-lookup TERM=app  # alias → Application, JSON
{"id": "application", "type": "domain_term", "area": "config_storage", ...}

$ manage.py knowledge lookup "config entry" --format table
Configuration (config_storage) … 3 warnings, sources, docs

$ manage.py knowledge related application
[{"from": "application", "to": "configuration", "relationship": "owns"},
 {"from": "application", "to": "app_type", "relationship": "classified_by"},
 {"from": "application", "to": "user", "relationship": "associated_with"}]

$ manage.py knowledge list-areas
["config_storage", "user_directory"]
```

Note: the knowledge-* targets were run and verified **before** Docker was started — live confirmation of the zero-infrastructure property (AC10 evidence). Docker Desktop was then started to run the full `make test` gate (api tests need Postgres). Lint/type-check: not configured (per gate table) — not run, not claimed.

---

## 3. REFLECT & ADAPT

| Friction | Disposition |
|----------|-------------|
| `requirements.txt` had no trailing newline; the first append produced `django-cors-headers==4.9.0PyYAML==6.0.3` on one line | **Fixed now** — caught immediately (output review), file rewritten with proper newlines and re-verified via `pip install -r`. Nothing deferred: a one-off authoring hazard, not a recurring process gap. |
| Reference code's exception class `ImportError` shadows the Python builtin | **Fixed now** — ported as `KnowledgeImportError`. Lesson: reference implementations are starting points, not authorities; deviations recorded in BUILD notes. |
| Docker daemon was down at gate time; `make test` failed at `db-up` before any test ran | **Fixed via doc update** — procedural memory lacked the "daemon itself is down" case (it only covered the container). Added to ENV_SCRIPTS.md off-script section: `open -a Docker`, poll `docker info` (~5–10s). Knowledge commands were unaffected — by design. |
| YAML restates facts DOMAIN.md owns (drift risk) | **Accepted** — mitigations already in place: source-of-truth header in both YAML files, `documentation:` back-links on every node, and the `RealKnowledgeTest` gate. Revisit only if the two actually diverge. |

**Adjustments to remaining tasks:** none — all nine tasks complete; stage-4 doc updates (README, ARCHITECTURE.md, ENV_SCRIPTS commands table, test counts) remain as planned.

**Process or doc changes:** ENV_SCRIPTS.md updated (Docker-daemon-down procedure) — applied this stage. No changes proposed to the four-stage process itself: first full pass through PLAN → BUILD ran without process friction; `call_command` with argparse subparsers worked cleanly on Django 5.2.

---

## 4. COMMIT & PICK NEXT

_Not started._

---

> **Purge (after commit):** delete sections 1–4's working notes; keep title, goal, acceptance criteria with their met state, the completion marker, and the commit range.
