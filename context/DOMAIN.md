# Domain

This document is semantic memory for agents: it describes **what** `config-service` is about, independent of technology. For **how** it is built, see [ARCHITECTURE.md](ARCHITECTURE.md); for project purpose and scope, see [ABOUT.md](ABOUT.md).

## Domain summary

`config-service` started as a minimal **user directory** and has grown into an **application configuration store**: a registry of people (name + email), a registry of applications across the organization (name + type + linked users), and per-application configurations holding settings for three environments (dev/uat/prod). Domain complexity is still kept intentionally low — the project exists to practice AI-assisted engineering workflow.

## Entities

### User

A directory entry for a person — **not** an authentication account (it is unrelated to `django.contrib.auth`; nobody logs in as a `User`).

| Field | Type | Rules |
|-------|------|-------|
| `id` | auto integer | Primary key, read-only |
| `first_name` | string (≤100) | Required |
| `last_name` | string (≤100) | Required |
| `email` | email string | Required, **unique** across all users, validated as an email address |
| `created_at` | datetime | Set once on creation, read-only |
| `updated_at` | datetime | Refreshed on every save, read-only |

**Invariants and conventions:**

- Email uniqueness is the only cross-record constraint; attempting to create a second user with an existing email is rejected.
- Users are always presented ordered by `last_name`, then `first_name`.
- A user's display name is "`first_name` `last_name`" (e.g. "Alice Smith").

### Application

Represents an application owned by the organization that needs its configuration tracked.

| Field | Type | Rules |
|-------|------|-------|
| `id` | auto integer | Primary key, read-only |
| `name` | string (≤100) | Required, **unique** across all applications |
| `app_type` | string, choice | Required; one of `mobile`, `desktop`, `web`, `cloud` |
| `users` | array of user ids (M2M) | Optional; the users associated with this application |
| `created_at` | datetime | Set once on creation, read-only |
| `updated_at` | datetime | Refreshed on every save, read-only |

**Invariants and conventions:**

- Name uniqueness is the only cross-record constraint on applications.
- Applications are always presented ordered by `name`.
- Deleting an application cascades and deletes all of its configurations.
- Deleting a user leaves the application in place; the user is simply removed from its `users` set.

### Configuration

A named set of environment settings belonging to exactly one application.

| Field | Type | Rules |
|-------|------|-------|
| `id` | auto integer | Primary key, read-only |
| `application` | FK to Application | Required; read-only from the API's perspective — always derived from the URL, never accepted in the request body |
| `name` | string (≤100) | Required, **unique per application** (the same name may be reused across different applications) |
| `dev_settings` | JSON object | Optional; defaults to `{}`; must be a JSON object (arrays/scalars rejected) |
| `uat_settings` | JSON object | Optional; defaults to `{}`; must be a JSON object (arrays/scalars rejected) |
| `prod_settings` | JSON object | Optional; defaults to `{}`; must be a JSON object (arrays/scalars rejected) |
| `created_at` | datetime | Set once on creation, read-only |
| `updated_at` | datetime | Refreshed on every save, read-only |

**Invariants and conventions:**

- Configurations are always presented ordered by `name`.
- A configuration always belongs to exactly one application (`on_delete=CASCADE`).
- The three environments are independent JSON blobs with no shared schema enforced beyond "must be an object."

## Actors

- **Visitor** — anonymous; opens the SPA and views the user list. Read-only, no login.
- **API client** — any HTTP client (curl, scripts, the SPA); may perform full CRUD on users, applications, and configurations. The API is public by MVP decision — there is no authentication or authorization.
- **Administrator** — manages user, application, and configuration records through Django admin (`/admin/`), which requires a Django superuser account (this is Django's own auth, separate from the `User` entity).

## Use cases

1. **View the user directory** — visitor opens the SPA; the list of users (name — email) is displayed, or "No users found." when empty.
2. **Register a user** — API client POSTs first name, last name, and a unique email.
3. **Look up / correct / remove a user** — API client retrieves, updates, or deletes a specific user by id.
4. **Back-office management** — administrator creates or edits users, applications, and configurations in Django admin.
5. **Manage the application registry** — API client or SPA user creates, lists, views, edits, or deletes applications (name, type, linked users). This supersedes the original spec wording of a users↔configuration relationship: the many-to-many is **users↔application**, corrected during design review.
6. **Manage an application's configurations** — API client or SPA user creates, lists, views, edits, or deletes configurations nested under an application, editing the dev/uat/prod settings as JSON objects.

## Domain decisions and boundaries (MVP)

Decisions recorded in `prompts/4-web-api-plan-answers.md` and `prompts/8-web-api-config-storage-specs.md`:

- The API exposes the User, Application, and Configuration resources; no other models exist or are planned in this module.
- The API is **public** — auth is explicitly out of scope for the MVP.
- The frontend is no longer entirely display-only: the SPA has full CRUD screens for applications and configurations. Users remain the one display-only resource — the SPA still offers no create/edit/delete UI for users; user mutations happen via the API or admin only.
- No soft-deletion, no status/roles beyond `app_type`, no pagination or search, no per-environment settings schema — everything is assumed small and unstructured.
