# Config storage: expand config-service into an application configuration store

This document contains details necessary to create a prompt, which will later be used to create an implementation plan for expanding `config-service` from a single User resource into a configuration store for applications across the organization. Please review the contents of this file and recommend a PROMPT that can be sent to an AI coding assistant for help with creating an implementation plan for this expansion.

The prompt should:

- ask the assistant to create a comprehensive plan that includes models/migrations, serializers/views/routing, and the SPA CRUD screens.
- recommend strict adherence to ALL of the details in this document.
- strongly encourage the assistant to not add any additional dependencies without approval.
- encourage the assistant to ask for more information if they need it.
- no guesswork

## Overview

`config-service` grows from a single `User` resource into a configuration store for applications across the organization. The backend (Django 5.2 / DRF 3.17) gains two new resources, `Application` and `Configuration`, exposed via nested REST routes. The Vue 3 SPA gains full CRUD screens for both.

## Requirements

1. `Application` is a first-class entity: `name` (unique, ≤100 chars), `app_type` one of `mobile`, `desktop`, `web`, `cloud`, and a many-to-many `users` relationship to the existing `User` model.

   NOTE: the original requirement said a users↔configuration many-to-many; during design review this was corrected by the owner to users↔**application**.

2. `Configuration` belongs to exactly one `Application` (FK, cascade delete), has `name` (unique per application, ≤100 chars) and exactly three environments stored as three JSON columns: `dev_settings`, `uat_settings`, `prod_settings` (each defaults to `{}`, must be a JSON object — arrays/scalars rejected with 400).

3. API: nested REST routes, hand-rolled wiring (NO drf-nested-routers — the minimal-dependency policy stands):
   - `GET/POST /api/applications/` ; `GET/PUT/PATCH/DELETE /api/applications/{id}/` — `users` is a writable array of user ids.
   - `GET/POST /api/applications/{app_id}/configurations/` ; `GET/PUT/PATCH/DELETE /api/applications/{app_id}/configurations/{id}/` — `application` is read-only, taken from the URL. 404 for unknown app id and for a config id under the wrong application. Duplicate config name within an app → 400.

4. SPA: full CRUD UI for applications and configurations (nav bar Users | Applications; list/detail/form pages; three JSON textareas with client-side JSON validation for configurations; deletes via `window.confirm`). Users remain display-only in the SPA (mutations via API/admin only).

5. Existing `/api/users/` API and the user list page are unchanged. No new dependencies, no auth (public API, unchanged MVP decision), schema stays ORM-migration-owned.

## Out of scope

Auth, pagination/search, per-environment metadata, frontend tests, TypeScript/Pinia, production deployment.

## Testing

~20 new backend tests (model + API for both resources) via Django's default runner; existing 7 stay green.
