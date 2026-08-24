# 006 — Ship an Inspector config; fix the broken README command

> Process, gates, and the sign-off rule: [`memory/WORKFLOW_STATUS.md`](../memory/WORKFLOW_STATUS.md).

**Goal:** The MCP README documents an Inspector command that does not work. Replace it with one that does, and ship the config file it needs so testing the server is a copy-paste rather than a debugging session.

## Stages

| Stage | State | Signed off |
|-------|-------|------------|
| 1. PLAN | complete | ☑ |
| 2. BUILD & ASSESS | complete | ☑ |
| 3. REFLECT & ADAPT | complete | ☑ |
| 4. COMMIT & PICK NEXT | **awaiting final sign-off** | ☐ |

## Inputs

- The user's instruction (2026-08-24): add the Inspector config and fix the README.
- **The bug, reproduced:** `npx @modelcontextprotocol/inspector -- venv/bin/python -m stdio_server.main` — the exact line in the current README — fails. The Inspector's argument parser consumes `-m` as one of its own flags, so Python launches with no module, receives JSON-RPC frames on stdin, and tries to execute them as source: `NameError: name 'true' is not defined`, then `Connection timed out after 15000 ms`. Any server command containing a flag hits this.
- Measured alternatives: passing `--` before the target loses the Inspector's own `--method`; putting the target first re-triggers the `-m` capture. `--config`/`--server` is the only form that works.

## Outputs

`my-domain-lang-mcp/inspector.json` (portable, committed), a README section with commands that were actually run, and the same fix reflected where Inspector is mentioned elsewhere.

---

## 1. PLAN

### Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Fix mechanism | Ship a **committed `inspector.json`** and use `--config inspector.json --server my-domain-lang` | The only invocation that survives the `-m` in our command. It also doubles as the agent-registration snippet, so one file serves both purposes. |
| Portability | **Relative** `"command": "venv/bin/python"`, no `cwd` key — run from `my-domain-lang-mcp/` | Verified working. An absolute path would be machine-specific and unfit to commit; `$PWD`-generation in the README would leave an untracked file behind. The cost is one documented `cd`, which the README states. |
| Safety of committing it | Fine — `--config` is documented **read-only** ("served as-is, never written or seeded") | The writable file is `--catalog` (`~/.mcp-inspector/mcp.json`), which we do not use. So the committed file cannot be mutated by a session. |
| README content | Show the **web UI**, the **per-tool CLI** invocations, and the **error paths**, with real terms from the shipped graph | A doc that lists tool names teaches less than one that says "run this, expect that". Every command in it was executed. |
| Honesty note | Record that the Inspector **short-circuits unknown tool names client-side** | `--tool-name not_a_tool` returns the Inspector's own "not found on server", never reaching our `-32602` guard. Without this note a reader would reasonably conclude the guard is missing. |

### Acceptance criteria

- [x] **AC1** — Given a fresh clone, When `inspector.json` is used from `my-domain-lang-mcp/`, Then the Inspector connects and `tools/list` returns the four tools — with no machine-specific path in the committed file.
      Test: manual — the command run and output recorded in BUILD.
- [x] **AC2** — Given the README, When every command in its Inspector section is run verbatim, Then each succeeds.
      Test: manual, all commands executed; recorded in BUILD.
- [x] **AC3** — Given the docs, Then the broken `-- venv/bin/python -m stdio_server.main` line is no longer **prescribed** anywhere; where it appears, it is explicitly labelled as the thing that does not work, with the reason.
      Test: manual `grep`.
      *Re-worded during BUILD (was: "no longer appears anywhere"). Deleting it outright tested worse: a reader who already ran the old command and searched for the error would find nothing. Keeping it as a labelled anti-pattern, with the `NameError` it produces, makes the failure searchable. Changed deliberately rather than quietly reported as met.*
- [x] **AC4** — Given `make check`, Then the gate is still green (the new file is data, but the tree must stay clean).
      Test: `make check`.

### Tasks

- [x] T1 — Add `my-domain-lang-mcp/inspector.json` with relative paths.
- [x] T2 — Rewrite the README's Inspector section: setup, web UI, per-tool CLI, error paths, the client-side short-circuit note.
- [x] T3 — Point `config-service/README.md` and `memory/ENV_SCRIPTS.md` at the working invocation.
- [x] T4 — Run every documented command; run `make check`.

### Test strategy

No automated tests: the deliverable is a config file and prose, and the only meaningful verification is **executing every command the README tells a reader to run**. That is the check, and it is the one that would have caught the original bug — the broken line was written from plausibility rather than from a terminal.

### File changes

| File | Change | Purpose |
|------|--------|---------|
| `changes/006-mcp-inspector-config.md` | create | this work item |
| `config-service/my-domain-lang-mcp/inspector.json` | create | the config that makes Inspector work |
| `config-service/my-domain-lang-mcp/README.md` | modify | working commands |
| `config-service/README.md`, `memory/ENV_SCRIPTS.md` | modify | point at the working invocation |
| `memory/WORKFLOW_STATUS.md`, `JOURNAL.md` | modify | pointer, history, run entry |

### Out of scope

- Any server behaviour change.
- A `make mcp-inspect` target — the command is a one-liner and `npx` downloads on demand; wrapping it would imply the Inspector is a project dependency, which it is not.

### Open questions

None.

---

## 2. BUILD & ASSESS

**Implemented:** `my-domain-lang-mcp/inspector.json` (relative paths, no `cwd` key — portable and machine-independent). The README's Inspector section rewritten as setup → web UI → a per-tool CLI table → the error paths, with a note on why a config file is required and one on what the Inspector cannot show. `config-service/README.md` and `ENV_SCRIPTS.md` point at the working invocation.

**Deviations from plan:** AC3 re-worded during BUILD (see the criterion) — the broken command is kept as a labelled anti-pattern rather than deleted, so the failure stays searchable for anyone who already hit it.

**Verification evidence** — every command in the README, run verbatim from the committed config:

```
$ npx @modelcontextprotocol/inspector --cli --config inspector.json --server my-domain-lang --method tools/list
  -> lookup_term, get_related_terms, list_domain_areas, validate_knowledge_graph

--tool-name lookup_term --tool-arg term=app         -> id "application", name "Application"
--tool-name lookup_term --tool-arg term=APP         -> id "application"     (alias, case-insensitive)
--tool-name get_related_terms --tool-arg term=application
                                                    -> owns / classified_by / associated_with
--tool-name list_domain_areas                       -> ["config_storage", "user_directory"]
--tool-name validate_knowledge_graph                -> {"valid": true, "issues": []}

--tool-name lookup_term --tool-arg term=nonsense_term
   -> isError: true, "No domain term matches 'nonsense_term'. Call list_domain_areas ..."
--tool-name lookup_term            (no arg)
   -> {"error":"Invalid arguments for tool lookup_term: 'term' is a required property"}
-e KNOWLEDGE_DB=/tmp/nope.db --tool-name list_domain_areas
   -> isError: true, names the path + "make knowledge-import"; no file created (checked)
--tool-name not_a_tool
   -> {"error":"tool_not_found","message":"Tool 'not_a_tool' not found on server."}   <- Inspector's own
      client-side check; never reaches the server's -32602 guard. Documented as such.

$ grep -c "/Users/" inspector.json    -> 0        (nothing machine-specific committed)
$ make check                          -> All checks passed.
```

The web UI was also started with the same config and printed its tokenised `http://127.0.0.1:6274?MCP_INSPECTOR_API_TOKEN=…` URL.

---

## 3. REFLECT & ADAPT

| Friction | Disposition |
|----------|-------------|
| **The README documented a command that had never been run.** It was written from the reference project's shape and looked entirely plausible — and it fails on the first try, with an error (`NameError: name 'true' is not defined`) that points at Python rather than at the real cause. Plausible-looking documentation is worse than none: it costs the reader a debugging session and makes them doubt the server rather than the docs. | **Fixed now**, and generalised into a standing rule: **commands in documentation must be executed before they are committed.** Added to `AGENTS.md`. This is the doc-level twin of the rule 003 added for gates — a command that has never been run and a command that works look identical on the page. |
| The Inspector's own arg parser captures `-m`, and no amount of `--` placement recovers it. | **Accepted and documented.** Not our bug to fix; the config-file form is the supported path, and the README now explains the failure so nobody re-derives it. |
| The Inspector short-circuits unknown tool names client-side, hiding the server's `-32602`. | **Accepted, documented.** Left as a note pointing at the raw-frame test that does cover it — otherwise a reader would reasonably conclude the guard is missing. |

**Adjustments to remaining tasks:** none.

**Process or doc changes:** one standing rule added to `AGENTS.md` — run documented commands before committing them.

---

## 4. COMMIT & PICK NEXT

Recorded at close.
