# Full stack app: RESTful API + SPA

This document contains details necessary to create a questions asked by a plan before implementation, which will later be used to create an implementation plan for a full stack app consisting of REST API and SPA. Please review the contents of this file and recommend a PROMPT that can be sent to an AI coding assistant for help with creating an implementation plan for this service.

## Open questions to be answered

1. **Application domain**: The specs describe the technology stack but not what the application does. What models/resources does the API expose? Without this, the plan covers project scaffolding and architectural setup only.
Answer: Simply expose a user model via rest API as a list and Frontend vue.js displays the user list.
2. **Vue Router** *(approval needed)*: An SPA requires client-side routing. Vue Router is the official routing library for Vue.js. It is not explicitly listed in the specs but is functionally required for an SPA.
Answer: Install Vue Router.
3. **Build tooling** *(approval needed)*: Vue.js 3 projects require a build tool. Vite is the standard build tool shipped with `create-vue` (the official Vue scaffolding tool). It is not explicitly listed in the specs.
Answer: Use Vite.
4. **CORS handling**: If the frontend dev server (e.g. port 5173) and backend dev server (e.g. port 8000) run on separate origins, cross-origin requests must be handled. This plan uses Vite's built-in dev proxy to avoid adding a backend dependency. If a backend solution is preferred, `django-cors-headers` would need approval.
Answer: Install and implement `django-cors-headers`.
5. **HTTP client**: The frontend needs to make API calls. This plan uses the browser-native `fetch` API to avoid adding a dependency (e.g. `axios`).
Answer: Prefer to use `axios`.
6. **Authentication/authorization**: No auth requirements are specified. Is the API public, or will auth be needed?
Answer: Just public for MVP product.
7. **Project name**: What should the Django project and Vue app be named? This plan uses `config` for the Django project and `frontend` for the Vue app.
Answer: It's named config-service and place both DRF and Vue.js inside ./config-service folder.
8. **Deployment**: Are there any deployment requirements (Docker, reverse proxy, etc.)?
Answer: postgres can be run in Docker.
