# Config Service — developer tasks. Run from this directory: make <target>
# `make` alone lists the targets.

SHELL := /bin/bash
PYTHON3 ?= python3
VENV := backend/venv
MANAGE := cd backend && venv/bin/python manage.py
MCP_DIR := backend/my-domain-lang-mcp
MCP_VENV := $(MCP_DIR)/venv

.DEFAULT_GOAL := help

.PHONY: help install install-backend install-frontend up backend frontend \
        db-up db-down db-destroy db-status migrate makemigrations \
        test superuser shell build clean \
        knowledge-import knowledge-validate knowledge-lookup \
        mcp-install mcp-test mcp-run

help: ## List available targets
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

## ---------- Setup ----------

install: install-backend install-frontend ## Install all dependencies (venv + pip, npm)

install-backend: ## Create venv (if missing) and install Python dependencies
	@test -d $(VENV) || $(PYTHON3) -m venv $(VENV)
	$(VENV)/bin/pip install -r backend/requirements.txt

install-frontend: ## Install Node dependencies
	cd frontend && npm install

## ---------- Full stack ----------

up: install db-up migrate ## Bring up the full stack: db + backend :8000 + frontend :5173 (Ctrl+C stops both servers)
	$(MAKE) -j2 backend frontend

backend: db-up ## Run the Django dev server on :8000
	$(MANAGE) runserver

frontend: ## Run the Vite dev server on :5173
	cd frontend && npm run dev

## ---------- Database ----------

db-up: ## Start PostgreSQL (Docker, detached; no-op if already running)
	docker compose up -d

db-down: ## Stop PostgreSQL (data is kept in the pgdata volume)
	docker compose down

db-destroy: ## Stop PostgreSQL AND DELETE ALL DATA (removes the pgdata volume)
	docker compose down -v

db-status: ## Show the database container status
	docker compose ps

migrate: db-up ## Apply database migrations
	$(MANAGE) migrate

makemigrations: ## Generate migrations after model changes
	$(MANAGE) makemigrations api

## ---------- Regular tasks ----------

test: db-up ## Run the backend test suite (Django default test framework)
	$(MANAGE) test

superuser: db-up ## Create a Django admin superuser (interactive)
	$(MANAGE) createsuperuser

shell: db-up ## Open a Django shell
	$(MANAGE) shell

build: ## Build the frontend for production (frontend/dist/)
	cd frontend && npm run build

## ---------- Knowledge graph ----------

knowledge-import: ## Import knowledge/ YAML into knowledge.db
	$(MANAGE) knowledge import

knowledge-validate: ## Check the knowledge graph for missing references
	$(MANAGE) knowledge validate

knowledge-lookup: ## Look up TERM in the knowledge graph (make knowledge-lookup TERM=app)
	$(MANAGE) knowledge lookup "$(TERM)"

## ---------- MCP server (no Docker needed) ----------

mcp-install: ## Create the MCP server venv (if missing) and install its dependencies
	@test -d $(MCP_VENV) || $(PYTHON3) -m venv $(MCP_VENV)
	$(MCP_VENV)/bin/pip install -r $(MCP_DIR)/requirements.txt

mcp-test: ## Run the MCP server test suite (pytest)
	cd $(MCP_DIR) && venv/bin/python -m pytest

mcp-run: ## Run the MCP stdio server (for MCP Inspector or manual protocol poking)
	cd $(MCP_DIR) && venv/bin/python -m stdio_server.main

clean: ## Remove build artifacts, Python caches, and knowledge.db (keeps venv, node_modules, db data)
	rm -rf frontend/dist
	rm -f knowledge.db
	find backend -type d -name __pycache__ -prune -exec rm -rf {} +
