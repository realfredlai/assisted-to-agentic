# Journal entries

1. Entry 1:
    - Prompt (what we're asking of our assistant): Read @/prompts/1-web-api-specs.md and follow the instructions at the top of the file.
    - Tool (your AI assistant): Cline
    - Mode (if applicable): Plan
    - Context (clean, from previous, etc.): Clean
    - Model (LLM model and version): Claude Sonnet 4.6
    - Input (file added to the prompt): prompts/1-web-api-specs.md
    - Output (file that contains the response): prompts/2-web-api-prompt.md
    - Cost (total cost of the full run): [enter after the run completes]
    - Reflections (narrative assessments of the response): [enter after the run completes]

2. Entry 2:
    - Prompt (what we're asking of our assistant): Read @/prompts/2-web-api-prompt.md and follow the instructions at the top of the file.
    - Mode (if applicable): Plan
    - Context (clean, from previous, etc.): Clean
    - Input (file added to the prompt): prompts/1-web-api-specs.md
    - Output (file that contains the response): prompts/3-web-api-plan.md

3. Entry 3:
    - Prompt (what we're asking of our assistant): Read @/prompts/4-web-api-plan-answers.md and follow the instructions at the top of the file.
    - Mode (if applicable): Plan
    - Context (clean, from previous, etc.): From previous
    - Input (file added to the prompt): prompts/3-web-api-plan.md
    - Output (file that contains the response): prompts/4-web-api-implementation.md

4. Entry 4:
    - Prompt (what we're asking of our assistant): Read @/prompts/5-web-api-versions-upgrade-specs.md and follow the instructions at the top of the file.
    - Mode (if applicable): Plan
    - Context (clean, from previous, etc.): From previous
    - Input (file added to the prompt): prompts/4-web-api-implementation.md
    - Output (file that contains the response): prompts/6-web-api-versions-upgrade-prompt.md

5. Entry 5:
    - Prompt (what we're asking of our assistant): Read entry 4 on @JOURNAL.md and generate a plan; reconcile it with the existing @prompts/6-web-api-versions-upgrade-prompt.md. Then: execute with Option 1 (subagent-driven).
    - Tool (your AI assistant): Claude Code
    - Mode (if applicable): Plan, then subagent-driven execution
    - Context (clean, from previous, etc.): Clean
    - Model (LLM model and version): Claude Fable 5
    - Input (file added to the prompt): prompts/5-web-api-versions-upgrade-specs.md, prompts/6-web-api-versions-upgrade-prompt.md
    - Output (file that contains the response): prompts/7-web-api-versions-upgrade-plan.md (plan with citations + reconciliation); execution merged to main as commits bf9935b..4ff19f4 (Django 5.2.16, DRF 3.17.1, psycopg2-binary 2.9.12, django-cors-headers 4.9.0; 7/7 tests green at every step)

6. Entry 6:
    - Prompt (what we're asking of our assistant): Use @context/ABOUT.md as semantic memory for this project; fill in all the details from the implementation plan at @prompts/4-web-api-implementation.md.
    - Tool (your AI assistant): Claude Code
    - Mode (if applicable): Subagent-driven execution requested; resolved to verification + documentation (the plan was already fully implemented and merged as of Entry 5)
    - Context (clean, from previous, etc.): Clean
    - Model (LLM model and version): Claude Fable 5
    - Input (file added to the prompt): context/ABOUT.md, prompts/4-web-api-implementation.md
    - Output (file that contains the response): context/ABOUT.md (all sections filled: justification, personas, domain context, scope); prompts/4-web-api-implementation.md (all task checkboxes marked complete); verified 7/7 backend tests green on main before checking off

7. Entry 7:
    - Prompt (what we're asking of our assistant): I have domain.md and architecture.md (fill in the two new empty context docs).
    - Tool (your AI assistant): Claude Code
    - Mode (if applicable): Documentation (content sourced from the actual source files, not just the plan)
    - Context (clean, from previous, etc.): From previous
    - Model (LLM model and version): Claude Fable 5
    - Input (file added to the prompt): context/DOMAIN.md and context/ARCHITECTURE.md (empty stubs), config-service backend/frontend source files
    - Output (file that contains the response): context/DOMAIN.md (entities, actors, use cases, MVP boundaries); context/ARCHITECTURE.md (tiers, stack, patterns, API surface, data flow, testing, dev workflow, key decisions); context/ABOUT.md updated to link the companion docs

8. Entry 8:
    - Prompt (what we're asking of our assistant): /superpowers:brainstorming config-storage expansion
    - Tool (your AI assistant): Claude Code
    - Mode (if applicable): Brainstorm → plan → subagent-driven implementation
    - Context (clean, from previous, etc.): From previous
    - Model (LLM model and version): Claude Fable 5
    - Input (file added to the prompt): prompts/8-web-api-config-storage-specs.md, plan file (`/Users/admin/.claude/plans/swift-waddling-lollipop.md`)
    - Output (file that contains the response): backend api files (models.py, serializers.py, views.py, urls.py, admin.py, migrations/0002_application_configuration.py, tests.py — 27 new tests, 34 total); frontend src files (services/api.js, router/index.js, App.vue, new views/ApplicationListView.vue, views/ApplicationDetailView.vue, views/ApplicationFormView.vue, views/ConfigurationFormView.vue, components/ApplicationList.vue, components/ConfigurationList.vue); context docs (DOMAIN.md, ARCHITECTURE.md, ABOUT.md) and config-service/README.md updated to match; implemented on branch `feature/config-storage`, commits `f36d1c9..9816aa2`

9. Entry 9:
    - Prompt (what we're asking of our assistant): Make sure there is a Makefile to bring up the full stack, including installing dependencies, tests, and anything else done regularly.
    - Tool (your AI assistant): Claude Code
    - Mode (if applicable): Direct implementation with end-to-end verification
    - Context (clean, from previous, etc.): From previous
    - Model (LLM model and version): Claude Fable 5
    - Input (file added to the prompt): config-service/README.md, docker-compose.yml, frontend/package.json (existing regular commands)
    - Output (file that contains the response): config-service/Makefile (up, install, test, migrate/makemigrations, backend/frontend, db-up/db-down/db-destroy/db-status, superuser, shell, build, clean); README.md gains a Quick Start (Make) section; context/ARCHITECTURE.md development workflow section now documents the Make targets. Verified: make install, make test (34/34 green), make migrate, make build, and make up (API :8000 and SPA :5173 both 200, then shut down)

10. Entry 10:
    - Prompt (what we're asking of our assistant): @memory/ENV_SCRIPTS.md, document it.
    - Tool (your AI assistant): Claude Code
    - Mode (if applicable): Documentation
    - Context (clean, from previous, etc.): From previous
    - Model (LLM model and version): Claude Fable 5
    - Input (file added to the prompt): memory/ENV_SCRIPTS.md (empty stub), config-service/Makefile
    - Output (file that contains the response): memory/ENV_SCRIPTS.md — procedural memory (distinct from the semantic memory in context/): environments (prerequisites, services/ports), scripts (all Make targets grouped by purpose, smoke checks), and when to go off-script (no-target operations, port conflicts, dependency changes, bad db state, promote-to-target rule, plus invariants that always hold); context/ABOUT.md links it as procedural memory

11. Entry 11:
    - Prompt (what we're asking of our assistant): another memory/WORKFLOW_STATUS.md
    - Tool (your AI assistant): Claude Code
    - Mode (if applicable): Documentation
    - Context (clean, from previous, etc.): From previous
    - Model (LLM model and version): Claude Fable 5
    - Input (file added to the prompt): git history/status, JOURNAL.md, SDD ledger
    - Output (file that contains the response): memory/WORKFLOW_STATUS.md — episodic memory (mutable snapshot; JOURNAL.md remains the append-only run log): current position (branch, health, in-flight, uncommitted), completed workflow stages table with commits and journal references, workflow conventions, known loose ends; update-every-run discipline stated in the doc; linked from context/ABOUT.md

12. Entry 12:
    - Prompt (what we're asking of our assistant): Re WORKFLOW_STATUS.md — adopt a four-stage pattern (PLAN, BUILD & ASSESS, REFLECT & ADAPT, COMMIT & PICK NEXT); document per-stage inputs/outputs and transition rules; only the user marks a stage complete. Also define work item structure (changes/XXX-name.md), acceptance criteria format (Given-When-Then), status tracking (lightweight pointer), and purge discipline.
    - Tool (your AI assistant): Claude Code
    - Mode (if applicable): Documentation / process design
    - Context (clean, from previous, etc.): From previous
    - Model (LLM model and version): Claude Opus 5
    - Input (file added to the prompt): memory/WORKFLOW_STATUS.md, assisted-to-agentic-module-1/examples (no work-item template found there), config-service dependency and Makefile inventory
    - Output (file that contains the response): memory/PROCESS.md (new — procedural: four stages with inputs/outputs/exit rules, sign-off rule that overrides autonomous-execution defaults, work-item structure, Given-When-Then format, status-tracking split, purge discipline, open decision on lint/type-check tooling); changes/TEMPLATE.md (new — work-item template with stage table, GWT criteria naming their tests, per-stage note sections, purge note); memory/WORKFLOW_STATUS.md rewritten as a thin episodic pointer (active work item + stage, current position, completed-work table, open decisions; stale commit hash 9816a2 → 9816aa2 fixed); AGENTS.md rewritten to load the process and the three memory kinds; context/ABOUT.md links PROCESS.md

13. Entry 13:
    - Prompt (what we're asking of our assistant): Restatement of the memory framework — procedural memory (ENV_SCRIPTS.md) covers environments, environment variables, developer scripts, and when to go off-script; episodic memory (WORKFLOW_STATUS.md) covers the four-stage framework, per-task work items with acceptance criteria/decisions/outcome, and purge-after-commit discipline.
    - Tool (your AI assistant): Claude Code
    - Mode (if applicable): Documentation / framework consolidation
    - Context (clean, from previous, etc.): From previous
    - Model (LLM model and version): Claude Opus 5
    - Input (file added to the prompt): settings.py, docker-compose.yml, .gitignore files, CI check (none exists)
    - Output (file that contains the response): memory/ENV_SCRIPTS.md rewritten to the four prescribed sections (environments incl. "no CI, no staging/production" and the 5173 CORS constraint; environment variables — no .env, so the docker-compose POSTGRES_* values and the Django settings that would otherwise be env vars, with the dev-only SECRET_KEY flagged; developer scripts as tables; when to go off-script + invariants). memory/PROCESS.md (created in entry 12) consolidated back into memory/WORKFLOW_STATUS.md per this framing — the four stages, sign-off rule, work-item structure, Given-When-Then format and purge discipline are now Part 1 of the episodic doc, with the pointer and history as Part 2; PROCESS.md deleted. AGENTS.md, context/ABOUT.md, and changes/TEMPLATE.md re-pointed accordingly

14. Entry 14:
    - Prompt (what we're asking of our assistant): Confirmed no lint/type-check tooling yet, but it is coming in the near future.
    - Tool (your AI assistant): Claude Code
    - Mode (if applicable): Documentation refinement
    - Context (clean, from previous, etc.): From previous
    - Model (LLM model and version): Claude Opus 5
    - Input (file added to the prompt): memory/WORKFLOW_STATUS.md, memory/ENV_SCRIPTS.md, changes/TEMPLATE.md, AGENTS.md
    - Output (file that contains the response): BUILD & ASSESS gate rewritten to be forward-compatible — a check table (tests ✅ / lint ⏳ / typecheck ⏳) where the rule is "run and report every configured check, never a planned one," so added tooling joins the gate by flipping a row rather than needing a rewrite; open decision reframed from "awaiting your call" to "planned" with a four-point update checklist (requirements/package.json → Makefile targets → ENV_SCRIPTS.md → gate rows) plus the same note for CI; ENV_SCRIPTS.md and changes/TEMPLATE.md and AGENTS.md aligned

15. Entry 15:
    - Prompt (what we're asking of our assistant): Referring to assisted-to-agentic-module-5/examples/knowledge-graph, implement a similar CLI and knowledge for this project. PLAN signed off with "start build".
    - Tool (your AI assistant): Claude Code
    - Mode (if applicable): Four-stage process — PLAN (Opus 5, signed off), then BUILD & ASSESS (Fable 5)
    - Context (clean, from previous, etc.): From previous
    - Model (LLM model and version): Claude Opus 5 (plan) / Claude Fable 5 (build)
    - Input (file added to the prompt): changes/001-knowledge-graph-cli.md, module-5 knowledge-graph reference, context/DOMAIN.md
    - Output (file that contains the response): backend knowledge_graph app (storage, importer, manage.py knowledge command, 10 tests), config-service/knowledge/ YAML (5 nodes, 6 edges, DOMAIN.md as source of truth), Makefile knowledge-* targets, PyYAML dependency (approved), knowledge.db gitignored. 44/44 tests green. BUILD & ASSESS awaiting sign-off; nothing committed yet.

16. Entry 16:
    - Prompt (what we're asking of our assistant): sign off stage 2
    - Tool (your AI assistant): Claude Code
    - Mode (if applicable): Four-stage process — REFLECT & ADAPT
    - Context (clean, from previous, etc.): From previous
    - Model (LLM model and version): Claude Fable 5
    - Input (file added to the prompt): changes/001-knowledge-graph-cli.md BUILD notes
    - Output (file that contains the response): work item REFLECT & ADAPT section — four frictions dispositioned (requirements.txt newline: fixed; builtin-shadowing ImportError from reference: fixed; Docker daemon down at gate: fixed via ENV_SCRIPTS.md addition; YAML/DOMAIN.md drift: accepted with mitigations); no process changes proposed. Stage 3 awaiting sign-off.
