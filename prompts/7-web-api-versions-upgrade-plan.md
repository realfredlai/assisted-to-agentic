# Full Stack Versions Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `config-service` to Django 5.2 and DRF 3.17 (with supporting dependency bumps), keeping every intermediate state on an officially supported version combination and all 7 tests green after each step.

**Architecture:** This is a dependency-only upgrade — no application code changes are expected. Each task pins one package to its new version in `requirements.txt`, reinstalls, and verifies with the existing test suite plus a live API check before committing. The upgrade order is chosen so that every intermediate combination is officially supported by the maintainers.

**Tech Stack:** Django 5.2.16, DRF 3.17.1, psycopg2-binary 2.9.12, django-cors-headers 4.9.0, Python 3.14.4 (unchanged), PostgreSQL 16 (unchanged), Vue 3.5.13 / Vite 6 / vue-router 4.5 / axios 1.9 (unchanged).

## Global Constraints

Copied from `prompts/6-web-api-versions-upgrade-prompt.md` (the prompt that requested this plan):

- Target versions are fixed: **Django 5.2, DRF 3.17, Vue.js 3.5, Python 3.14**. Do not substitute alternatives.
- Every compatibility claim must cite official documentation or release notes. No unsupported assertions.
- NO guesswork — every decision traceable to the spec, official docs, or an explicit answer from the user.
- Do NOT add any new dependencies, frameworks, libraries, or tools without approval. (Version bumps of already-present packages required by the upgrade are in scope; switching psycopg2 → psycopg3 would be a new dependency and is deliberately NOT done.)
- Verification after each step: the existing 7 Django/DRF tests, manual curl checks against `/api/users/`, and frontend build verification.
- All work happens under `./config-service/` (`backend/` and `frontend/`).

---

## 1. Compatibility validation (citations)

All six validations required by the prompt, verified 2026-07-21:

| # | Claim | Verdict | Evidence |
|---|-------|---------|----------|
| 1 | Django 5.2 ↔ Python 3.14 | ✅ Compatible | [Django 5.2 release notes](https://docs.djangoproject.com/en/6.0/releases/5.2/): "Django 5.2 supports Python 3.10, 3.11, 3.12, 3.13, and 3.14 (as of 5.2.8)." Current interpreter is 3.14.4; latest 5.2 patch is [5.2.16 (security release, 2026-07-07)](https://www.djangoproject.com/weblog/2026/jul/07/security-releases/). |
| 2 | Django 5.2 ↔ DRF 3.17 | ✅ Compatible | [DRF release notes](https://www.django-rest-framework.org/community/release-notes/): 3.17.0 (2026-03-18) supports Django 4.2–6.0 ("versions below 4.2 no longer supported", Django 6.0 support added) and Python 3.10–3.14 (3.14 added, 3.9 dropped). Latest patch: 3.17.1 (2026-03-24). |
| 3 | Django 5.2 ↔ PostgreSQL 16 | ✅ Compatible | [Django 5.2 release notes](https://docs.djangoproject.com/en/6.0/releases/5.2/): "Django 5.2 supports PostgreSQL 14 and higher" (PostgreSQL 13 dropped). PostgreSQL 16 stays as-is. |
| 4 | Django 5.2 ↔ psycopg2-binary | ✅ Compatible, bump needed for Python 3.14 | [Django 5.2 databases docs](https://docs.djangoproject.com/en/5.2/ref/databases/): Django 5.2 supports psycopg2 2.8.4+ but *recommends* psycopg 3.1.8+; psycopg2 "is likely to be deprecated and removed at some point in the future." Current 2.9.10 satisfies Django 5.2, but official Python 3.14 support arrived in [psycopg2 2.9.11 (2025-10-10)](https://www.psycopg.org/docs/news.html); latest is 2.9.12 (2026-04-20). Plan bumps to 2.9.12; migration to psycopg3 is out of scope per the no-new-dependencies rule (flagged as future work). |
| 5 | Django 5.2 ↔ django-cors-headers | ✅ Compatible, bump recommended for Python 3.14 | [django-cors-headers changelog](https://github.com/adamchainz/django-cors-headers/blob/main/CHANGELOG.rst): 4.7.0 (2025-02-06) added "Support Django 5.2" — the **current pinned version already supports Django 5.2**. 4.8.0 (2025-09-08) added "Support Python 3.14"; 4.9.0 (2025-09-18) added Django 6.0 support. Plan bumps to 4.9.0 for official Python 3.14 support. |
| 6 | Vue 3.5 ↔ Vite / vue-router / axios | ✅ Already on target, no changes | `frontend/package.json` pins `vue ^3.5.13` — the Vue 3.5 target is **already met**. [@vitejs/plugin-vue 5.x](https://www.npmjs.com/package/@vitejs/plugin-vue) declares peer deps `vite ^5.0.0 || ^6.0.0` and `vue ^3.2.25` (satisfied by Vite 6.2 / Vue 3.5.13); [vue-router 4.x](https://router.vuejs.org/) is the Vue 3 router line (4.5 satisfied); axios is framework-agnostic. **No frontend package changes are required.** |

**No incompatibilities found** — no stop-and-report condition triggered.

### Version changes (from → to)

| Package | From | To | Why |
|---------|------|----|-----|
| Django | 5.1.9 | **5.2.16** | Target Django 5.2; 5.2.16 is the latest 5.2.x patch (July 2026 security release). |
| djangorestframework | 3.15.2 | **3.17.1** | Target DRF 3.17; 3.17.1 is the latest patch. |
| psycopg2-binary | 2.9.10 | **2.9.12** | Official Python 3.14 support (added in 2.9.11). |
| django-cors-headers | 4.7.0 | **4.9.0** | Official Python 3.14 support (added in 4.8.0). |
| Python | 3.14.4 | *(no change)* | Already at target 3.14. |
| Vue.js + frontend deps | 3.5.13 | *(no change)* | Already at target 3.5. |
| PostgreSQL | 16 | *(no change)* | Supported by Django 5.2 (14+). |

### Breaking changes / deprecations screened against this project

- **Django 5.2** ([release notes](https://docs.djangoproject.com/en/6.0/releases/5.2/)): backwards-incompatible changes concern MySQL charset defaults, `EmailMultiAlternatives`, oracledb/gettext minimums, and `HttpRequest.accepted_types` ordering. **None apply** — this project is PostgreSQL-only, sends no email, and serves a JSON-only DRF API. No settings changes or migrations required.
- **DRF 3.16 → 3.17** ([release notes](https://www.django-rest-framework.org/community/release-notes/)): drops Python 3.9, Django < 4.2, and the deprecated `coreapi` schema support. **None apply** — the project runs Python 3.14, targets Django 5.2, and uses only `ModelViewSet` / `ModelSerializer` / `DefaultRouter` (verified in `backend/api/views.py`, `serializers.py`, `urls.py`; no coreapi imports anywhere).
- **psycopg2 2.9.11–2.9.12** ([news](https://www.psycopg.org/docs/news.html)): drops Python 3.8, adds 3.14 wheels and PostgreSQL 18 error codes. No API changes affecting Django's ORM usage.
- **django-cors-headers 4.8.0–4.9.0** ([changelog](https://github.com/adamchainz/django-cors-headers/blob/main/CHANGELOG.rst)): support additions only; no setting renames. `CORS_ALLOWED_ORIGINS` in `backend/config/settings.py` is unchanged.

## 2. Upgrade order and justification

```
Task 1: DRF        3.15.2 → 3.17.1   (works with BOTH Django 5.1 and 5.2)
Task 2: Django     5.1.9  → 5.2.16   (DRF and cors-headers already 5.2-ready)
Task 3: psycopg2   2.9.10 → 2.9.12   (independent driver bump)
Task 4: cors-headers 4.7.0 → 4.9.0   (independent; Python 3.14 official)
Task 5: Full-stack verification + docs
```

**Why DRF before Django (not the intuitive "Django first"):**

- DRF 3.15.2 officially supports Django only up to 5.0 — Django 5.1/5.2 support arrived in DRF 3.16.0 ([DRF 3.16 announcement](https://www.django-rest-framework.org/community/3.16-announcement/)). The current combo (Django 5.1.9 + DRF 3.15.2) is *already* outside the official support matrix.
- Upgrading Django to 5.2 first would deepen that gap (Django 5.2 + DRF 3.15.2 = unsupported).
- Upgrading DRF to 3.17.1 first is safe because DRF 3.17 supports Django 4.2–6.0, which includes the currently-installed Django 5.1.9. After Task 1 the Django↔DRF combination is officially supported and stays that way through every remaining task. (psycopg2-binary and django-cors-headers gain *official* Python 3.14 support only in Tasks 3–4 — a gap that already existed at baseline and is never worsened; every intermediate state is test-verified.)

**Why psycopg2/cors-headers after Django:** both current versions already satisfy Django 5.2 (validations #4, #5), so these bumps are not blockers; sequencing them separately keeps each commit to a single-variable change that can be bisected or reverted independently.

**Files modified across the whole plan:**

- Modify: `config-service/backend/requirements.txt` (4 version pins, one per task)
- Modify: `config-service/README.md:7` (version references, Task 5)
- No changes to: application code, migrations, settings, or any `frontend/` file

---

### Task 0: Baseline verification (no changes)

**Files:** none modified.

**Interfaces:**
- Consumes: existing repo state.
- Produces: a recorded green baseline (7 passing tests, working API and frontend build) that every later task is compared against.

- [ ] **Step 1: Start PostgreSQL**

```bash
cd config-service && docker compose up -d db && docker compose ps
```

Expected: `db` service `running (healthy or started)` on port 5432.

- [ ] **Step 2: Run the existing test suite on current versions**

```bash
cd config-service/backend && source venv/bin/activate && python manage.py test -v 2
```

Expected: `Ran 7 tests ... OK` (2 model tests + 5 API tests). If this fails, STOP — fix the baseline before upgrading anything.

- [ ] **Step 3: Record current versions**

```bash
pip freeze | grep -iE "django|psycopg" 
```

Expected output (baseline):

```
Django==5.1.9
django-cors-headers==4.7.0
djangorestframework==3.15.2
psycopg2-binary==2.9.10
```

- [ ] **Step 4: Baseline API smoke check**

```bash
python manage.py runserver 8000 &
sleep 3
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/users/
kill %1
```

Expected: `200`.

- [ ] **Step 5: Baseline frontend build**

```bash
cd ../frontend && npm run build
```

Expected: `vite v6.x building for production... ✓ built in ...` with no errors.

---

### Task 1: Upgrade DRF 3.15.2 → 3.17.1

**Files:**
- Modify: `config-service/backend/requirements.txt:2`

**Interfaces:**
- Consumes: green baseline from Task 0.
- Produces: `djangorestframework==3.17.1` installed and passing; Django still 5.1.9. Every combo now inside official support matrices.

- [ ] **Step 1: Update the pin**

In `config-service/backend/requirements.txt`, change:

```diff
-djangorestframework==3.15.2
+djangorestframework==3.17.1
```

- [ ] **Step 2: Install**

```bash
cd config-service/backend && source venv/bin/activate && pip install -r requirements.txt
```

Expected: `Successfully installed djangorestframework-3.17.1`.

- [ ] **Step 3: Run system checks and tests**

```bash
python manage.py check && python manage.py test -v 2
```

Expected: `System check identified no issues (0 silenced).` then `Ran 7 tests ... OK`.

- [ ] **Step 4: API smoke check**

```bash
python manage.py runserver 8000 &
sleep 3
curl -s http://localhost:8000/api/users/ | head -c 200; echo
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/users/
kill %1
```

Expected: JSON array (`[]` or user objects) and `200`.

- [ ] **Step 5: Commit**

```bash
cd ../.. && git add config-service/backend/requirements.txt
git commit -m "chore: upgrade djangorestframework 3.15.2 -> 3.17.1"
```

---

### Task 2: Upgrade Django 5.1.9 → 5.2.16

**Files:**
- Modify: `config-service/backend/requirements.txt:1`

**Interfaces:**
- Consumes: DRF 3.17.1 from Task 1 (supports Django 4.2–6.0).
- Produces: `Django==5.2.16` installed and passing — the primary upgrade target reached.

- [ ] **Step 1: Update the pin**

In `config-service/backend/requirements.txt`, change:

```diff
-Django==5.1.9
+Django==5.2.16
```

- [ ] **Step 2: Install**

```bash
cd config-service/backend && source venv/bin/activate && pip install -r requirements.txt
```

Expected: `Successfully installed Django-5.2.16` (plus possible `asgiref`/`sqlparse` transitive bumps — these are Django's own dependencies, not new packages).

- [ ] **Step 3: Check for unexpected migration or check drift**

```bash
python manage.py check && python manage.py makemigrations --check --dry-run
```

Expected: `System check identified no issues (0 silenced).` and `No changes detected`. If Django 5.2 proposes a migration, STOP and report — none is expected for this model.

- [ ] **Step 4: Run tests**

```bash
python manage.py test -v 2
```

Expected: `Ran 7 tests ... OK`.

- [ ] **Step 5: API smoke check**

```bash
python manage.py runserver 8000 &
sleep 3
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/users/
kill %1
```

Expected: `200`.

- [ ] **Step 6: Commit**

```bash
cd ../.. && git add config-service/backend/requirements.txt
git commit -m "chore: upgrade Django 5.1.9 -> 5.2.16 (5.2 LTS)"
```

---

### Task 3: Upgrade psycopg2-binary 2.9.10 → 2.9.12

**Files:**
- Modify: `config-service/backend/requirements.txt:3`

**Interfaces:**
- Consumes: Django 5.2.16 from Task 2.
- Produces: `psycopg2-binary==2.9.12` — DB driver with official Python 3.14 wheels.

- [ ] **Step 1: Update the pin**

In `config-service/backend/requirements.txt`, change:

```diff
-psycopg2-binary==2.9.10
+psycopg2-binary==2.9.12
```

- [ ] **Step 2: Install**

```bash
cd config-service/backend && source venv/bin/activate && pip install -r requirements.txt
```

Expected: `Successfully installed psycopg2-binary-2.9.12` from a prebuilt `cp314` wheel (no compiler invocation).

- [ ] **Step 3: Run tests (exercises the DB driver end-to-end)**

```bash
python manage.py test -v 2
```

Expected: `Ran 7 tests ... OK` — the test suite creates/destroys a PostgreSQL test database, which fully exercises the driver.

- [ ] **Step 4: Commit**

```bash
cd ../.. && git add config-service/backend/requirements.txt
git commit -m "chore: upgrade psycopg2-binary 2.9.10 -> 2.9.12 for official Python 3.14 support"
```

---

### Task 4: Upgrade django-cors-headers 4.7.0 → 4.9.0

**Files:**
- Modify: `config-service/backend/requirements.txt:4`

**Interfaces:**
- Consumes: Django 5.2.16 from Task 2.
- Produces: `django-cors-headers==4.9.0` — CORS middleware with official Python 3.14 support.

- [ ] **Step 1: Update the pin**

In `config-service/backend/requirements.txt`, change:

```diff
-django-cors-headers==4.7.0
+django-cors-headers==4.9.0
```

- [ ] **Step 2: Install**

```bash
cd config-service/backend && source venv/bin/activate && pip install -r requirements.txt
```

Expected: `Successfully installed django-cors-headers-4.9.0`.

- [ ] **Step 3: Run checks and tests**

```bash
python manage.py check && python manage.py test -v 2
```

Expected: `System check identified no issues (0 silenced).` then `Ran 7 tests ... OK`.

- [ ] **Step 4: Verify CORS headers still emitted for the frontend origin**

```bash
python manage.py runserver 8000 &
sleep 3
curl -s -i -H "Origin: http://localhost:5173" http://localhost:8000/api/users/ | grep -i "access-control-allow-origin"
kill %1
```

Expected: `access-control-allow-origin: http://localhost:5173`.

- [ ] **Step 5: Commit**

```bash
cd ../.. && git add config-service/backend/requirements.txt
git commit -m "chore: upgrade django-cors-headers 4.7.0 -> 4.9.0 for official Python 3.14 support"
```

---

### Task 5: Full-stack verification and documentation

**Files:**
- Modify: `config-service/README.md:7`

**Interfaces:**
- Consumes: all four upgraded packages (Tasks 1–4).
- Produces: end-to-end verified stack and accurate README.

- [ ] **Step 1: Final requirements.txt sanity check**

`config-service/backend/requirements.txt` must now read exactly:

```
Django==5.2.16
djangorestframework==3.17.1
psycopg2-binary==2.9.12
django-cors-headers==4.9.0
```

- [ ] **Step 2: Full backend verification**

```bash
cd config-service/backend && source venv/bin/activate
python manage.py check && python manage.py test -v 2
```

Expected: 0 issues, `Ran 7 tests ... OK`.

- [ ] **Step 3: Frontend build verification (unchanged deps, rebuilt against upgraded API)**

```bash
cd ../frontend && npm run build
```

Expected: `✓ built` with no errors. (No frontend package changes were made; this confirms the build still passes.)

- [ ] **Step 4: Manual end-to-end check**

```bash
# Terminal 1: backend
cd config-service/backend && source venv/bin/activate && python manage.py runserver 8000
# Terminal 2: frontend
cd config-service/frontend && npm run dev
```

Open `http://localhost:5173` — the user list must render with no CORS errors in the browser console.

- [ ] **Step 5: Update README version references**

In `config-service/README.md`, change line 7:

```diff
-- **Backend:** Python 3.14, Django 5.1, Django REST Framework 3.15, django-cors-headers 4.7
+- **Backend:** Python 3.14, Django 5.2, Django REST Framework 3.17, django-cors-headers 4.9
```

- [ ] **Step 6: Commit**

```bash
cd ../.. && git add config-service/README.md
git commit -m "docs: update README for Django 5.2 / DRF 3.17 upgrade"
```

---

## 3. Rollback strategy

Each task is a single-pin commit, so rollback is per-package:

```bash
git revert <commit-sha>            # restores the previous pin
pip install -r requirements.txt    # reinstalls the previous version
python manage.py test -v 2         # confirm green
```

No migrations, schema changes, or data changes occur anywhere in this plan, so no database rollback is ever needed.

Caveat: revert in reverse task order. Reverting the DRF commit alone while keeping the Django 5.2 commit would recreate the unsupported Django 5.2 + DRF 3.15.2 combination.

## 4. Out of scope / future work (requires approval per the rules)

- **psycopg2 → psycopg3 migration:** Django recommends psycopg 3.1.8+ and warns psycopg2 support "is likely to be deprecated" ([databases docs](https://docs.djangoproject.com/en/5.2/ref/databases/)). Django 6.0 planning makes this worth doing before the next major upgrade — but it introduces a new dependency, which the rules forbid without approval.
- **Django 6.0:** released Dec 2025; DRF 3.17 and cors-headers 4.9.0 already support it. Not a target of this upgrade.
- **Frontend bumps (Vite 7, etc.):** not required by any target; frontend already meets the Vue 3.5 target.

## 5. Reconciliation with `prompts/6-web-api-versions-upgrade-prompt.md`

`prompts/6-web-api-versions-upgrade-prompt.md` is the **prompt** produced by journal entry 4 (per `prompts/5-web-api-versions-upgrade-specs.md`, whose instruction was to "recommend a PROMPT"). It is not itself an implementation plan — this document is the plan that prompt requests. Reconciliation of every requirement in file 6 against this plan:

| File 6 requirement | Where satisfied here | Discrepancies found |
|---|---|---|
| §1 Compatibility validation with citations | Section 1, all six checks | None — all six pass. |
| §2 Upgrade order with justification | Section 2 | Order is DRF→Django (not Django→DRF): file 6's example ordering rationale ("upgrade Django before DRF") is inverted for this project, because DRF 3.15.2 doesn't officially support Django 5.2 while DRF 3.17.1 supports both 5.1 and 5.2. |
| §3 Per-dependency from→to + breaking changes + files | Section 1 (tables) + per-task **Files** blocks | File 6 doesn't name a Django 5.2 patch; this plan pins 5.2.16 (latest security patch). File 6 lists DRF target "3.17"; pinned as 3.17.1. |
| §4 Verification strategy (7 tests, curl, frontend build) | Every task's steps + Task 5 end-to-end | None. |
| Current-state tables | Verified against `requirements.txt`, `package.json`, `docker-compose.yml`, `tests.py` (7 tests confirmed) | None — file 6's current-state data is accurate. |
| Rule: strict target adherence | All four targets hit exactly (Django 5.2.x, DRF 3.17.x, Vue 3.5 already met, Python 3.14 already met) | None. |
| Rule: no new dependencies | Only version bumps of the four existing pins; psycopg3 explicitly deferred | psycopg2-binary and django-cors-headers get patch/minor bumps beyond file 6's implicit "current versions" — required for official Python 3.14 support, documented in Section 1 (#4, #5). |
| Rule: ask if unclear / no guesswork | No open questions remained after validation — every claim in Section 1 carries a citation | None. |
