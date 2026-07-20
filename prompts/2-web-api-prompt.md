# Prompt: Create an implementation plan for a full stack RESTful API + SPA

## Request

You are asked to create a **comprehensive implementation plan** for a full stack application consisting of a RESTful API backend and a Single Page Application (SPA) frontend. Do NOT write any application code yet — produce a plan only.

The plan must include:

1. **Dependencies** — an explicit list of every dependency (backend and frontend) with the version to use and a one-line justification for each.
2. **File/folder structure** — the complete directory layout for the project, covering the backend, the frontend, and configuration files.
3. **Architectural patterns** — the patterns to be used in each tier (e.g., how business logic is organized in DRF, how the SPA communicates with the API, how the ORM/migrations are managed) and how the three tiers interact.

## Rules — strict adherence required

- You MUST strictly adhere to ALL details in the "Application specs" and "System environment requirements" sections below. Do not deviate from them or substitute alternatives.
- You MUST NOT add any additional dependencies, frameworks, libraries, or tools beyond what is required by these specifications without asking for approval first.
- If any information you need is missing, unclear, or ambiguous, ASK for more information before proceeding.
- NO guesswork. Do not make assumptions — every decision in the plan must be traceable to the specifications below or to an answer you have explicitly received.

## Application specs

1. This is an app that is written in Python using Django REST Framework (DRF).
2. It has a 3-tier architecture consisting of:
   - Frontend Single Page Application (SPA) written in Vue.js;
   - Backend API managed by DRF. All business logic is handled there;
   - Postgres DB managed by Django's native ORM, including migration strategy and bootstrapping;
3. The default test framework that comes with Django is sufficient — do not introduce additional testing tools.

## System environment requirements

1. Use the latest LTS Python version.
2. Run all applications in a Python virtual environment.
3. Vue.js should be on the latest stable version.