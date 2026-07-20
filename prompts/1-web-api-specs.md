# Full stack app: RESTful API + SPA

This document contains details necessary to create a prompt, which will later be used to create an implementation plan for a full stack app consisting of REST API and SPA. Please review the contents of this file and recommend a PROMPT that can be sent to an AI coding assistant for help with creating an implementation plan for this service.

The prompt should:

- ask the assistant to create a comprehensive plan that includes dependencies, file/folder structure, and architectural patterns.
- recommend strict adherence to ALL of the details in this document.
- strongly encourage the assistant to not add any additional dependencies without approval.
- encourage the assistant to ask for more information if they need it.
- no guesswork

## Application specs

1. This is an app that is written in python using Django REST framework (DRF).
2. It has a 3 tier architecture consisting of:
   - Frontend Single Page Application (SPA) written in Vue.js;
   - Backend API managed by DRF. All business logics are handled there;
   - Postgres DB managed by Django native ORM, including migration strategy, bootstrapping;
3. Default test come with Django should be enough.

## System environment requirement

1. Use latest LTS python version.
2. Run all applications in python virtual environment.
3. Vue.js should be on latest stable version.