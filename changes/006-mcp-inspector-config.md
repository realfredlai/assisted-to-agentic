# 006 — Ship an Inspector config; fix the broken README command

**Goal:** The MCP README documented an Inspector command that did not work. Replace it with one that does, and ship the config file it needs so testing the server is a copy-paste rather than a debugging session.

## Stages

| Stage | State | Signed off |
|-------|-------|------------|
| 1. PLAN | complete | ☑ |
| 2. BUILD & ASSESS | complete | ☑ |
| 3. REFLECT & ADAPT | complete | ☑ |
| 4. COMMIT & PICK NEXT | complete | ☑ |

## The bug

`npx @modelcontextprotocol/inspector -- venv/bin/python -m stdio_server.main` — the exact line the README carried — fails. The Inspector's argument parser consumes `-m` as one of its own flags, so Python launches with no module, receives JSON-RPC frames on stdin, and tries to execute them as source: `NameError: name 'true' is not defined`, then `Connection timed out after 15000 ms`. Any server command containing a flag hits this; neither `--` placement nor target-first ordering recovers it. `--config`/`--server` is the only form that works.

## Decisions

| Decision | Choice |
|----------|--------|
| Fix | Commit `inspector.json` and use `--config inspector.json --server my-domain-lang`. It doubles as the agent-registration snippet. |
| Portability | Relative `"command": "venv/bin/python"`, no `cwd` key — run from `my-domain-lang-mcp/`. Nothing machine-specific is committed (`grep -c "/Users/"` → 0). |
| Safe to commit | `--config` is documented read-only ("served as-is, never written or seeded"); the writable file is `--catalog`, which we do not use. |
| Keep the broken line | Retained as a **labelled anti-pattern** with the `NameError` it produces, so anyone who already ran it can search for the error and find the explanation. |
| Out of scope | A `make mcp-inspect` target — wrapping an `npx` one-liner would imply the Inspector is a project dependency, which it is not. |

## Acceptance criteria — all met

- [x] **AC1** — `inspector.json` connects from a fresh checkout and `tools/list` returns the four tools, with no machine-specific path committed.
- [x] **AC2** — every command in the README's Inspector section was run verbatim and succeeded.
- [x] **AC3** — the broken command is no longer **prescribed** anywhere; where it appears it is labelled as the thing that does not work, with the reason.
      *Re-worded during BUILD (was "no longer appears anywhere"): deleting it tested worse, because a reader who already hit the error would find nothing when searching for it.*
- [x] **AC4** — `make check` green.

## Outcome

**Complete.** Commit `19727ca` (+ purge follow-up). Also documented what the Inspector *cannot* show: it validates tool names against `tools/list` client-side, so its "tool not found" never reaches the server's `-32602` guard — only `main_test.py::test_raw_initialize_and_stderr_discipline` covers that.

**The lesson, now a standing rule in `AGENTS.md`:** run every command you put in a doc before committing it. The broken line was written from plausibility, not from a terminal — and a command that has never been executed looks exactly like one that works. It is the doc-level twin of the rule 003 added for gates. Full PLAN/BUILD/REFLECT reasoning preserved in git history at `19727ca`.
