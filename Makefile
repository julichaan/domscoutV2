SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

PYTHON ?= python3
VENV ?= venv
PIP := $(VENV)/bin/pip
VENV_PY := $(VENV)/bin/python

.PHONY: help install setup venv install-python install-client build build-client install-tools ensure-static start run-server dev status clean clean-pyc clean-db clean-client reset

help: ## Show available targets
	@echo "DomScout v2 - Make targets"
	@echo ""
	@awk 'BEGIN {FS = ":.*## "; printf "Usage: make <target>\n\nTargets:\n"} /^[a-zA-Z_-]+:.*## / { printf "  %-16s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: install-tools setup ## Full install: external tools + app setup

setup: venv install-python install-client build ## Prepare Python env, dependencies, and frontend build

venv: ## Create Python virtual environment if missing
	@if [ ! -d "$(VENV)" ]; then \
		echo "[+] Creating Python virtual environment"; \
		$(PYTHON) -m venv $(VENV); \
	else \
		echo "[=] Virtual environment already exists"; \
	fi

install-python: venv ## Install backend Python dependencies
	@echo "[+] Installing backend dependencies"
	@$(PIP) install -r server/requirements.txt

install-client: ## Install frontend Node dependencies
	@echo "[+] Installing frontend dependencies"
	@cd client && npm install

build: build-client ## Build frontend assets into server/static

build-client: ## Build Vue frontend into server/static
	@echo "[+] Building frontend"
	@cd client && npm run build

install-tools: venv ## Install external reconnaissance tools via install.py
	@echo "[+] Installing external tools (subfinder/findomain/httpx/gowitness/etc.)"
	@$(VENV_PY) install.py

ensure-static: ## Build frontend only if server/static is missing
	@if [ ! -f "server/static/index.html" ]; then \
		echo "[!] Frontend build not found. Running make build..."; \
		$(MAKE) --no-print-directory build; \
	fi

start: ensure-static ## Start Flask app in production mode (serves built frontend)
	@if [ ! -x "$(VENV_PY)" ]; then \
		echo "[!] Python virtualenv not found. Run: make setup"; \
		exit 1; \
	fi
	@echo "======================================"
	@echo "DomScout v2 - Starting Server"
	@echo "======================================"
	@echo "[*] Starting Flask server at http://localhost:5000"
	@echo "[!] Press Ctrl+C to stop"
	@cd server && ../$(VENV_PY) app.py

run-server: start ## Alias for start

dev: ## Start backend + Vue dev server
	@if [ ! -x "$(VENV_PY)" ]; then \
		echo "[!] Python virtualenv not found. Run: make setup"; \
		exit 1; \
	fi
	@echo "======================================"
	@echo "DomScout v2 - Development Mode"
	@echo "======================================"
	@set -e; \
	cd server; \
	../$(VENV_PY) app.py & \
	BACKEND_PID=$$!; \
	echo "[*] Backend running on http://localhost:5000 (PID: $$BACKEND_PID)"; \
	trap 'echo ""; echo "[*] Stopping backend server..."; kill $$BACKEND_PID 2>/dev/null || true' EXIT INT TERM; \
	cd ../client; \
	npm run serve

status: ## Show quick environment/tool status
	@echo "Python: $$($(PYTHON) --version 2>/dev/null || echo 'missing')"
	@echo "Node: $$(node --version 2>/dev/null || echo 'missing')"
	@echo "npm: $$(npm --version 2>/dev/null || echo 'missing')"
	@echo "Virtualenv: $$( [ -d "$(VENV)" ] && echo 'present' || echo 'missing' )"
	@echo "Backend deps: $$( [ -f "server/requirements.txt" ] && echo 'requirements file found' || echo 'missing' )"
	@echo "Frontend build: $$( [ -f "server/static/index.html" ] && echo 'present' || echo 'missing' )"
	@echo "Tools in PATH:"
	@for tool in subfinder findomain assetfinder sublist3r dnsx httpx httpx-toolkit gowitness; do \
		if command -v $$tool >/dev/null 2>&1; then \
			echo "  - $$tool: OK"; \
		fi; \
	done

clean: clean-pyc ## Remove temporary Python cache files

clean-pyc: ## Remove Python cache files
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete

clean-db: ## Remove SQLite database (DANGEROUS: deletes scan history)
	@rm -f server/domscout.db
	@echo "[!] Removed server/domscout.db"

clean-client: ## Remove frontend dependencies and build artifacts
	@rm -rf client/node_modules
	@rm -rf server/static/*
	@echo "[!] Removed client/node_modules and server/static contents"

reset: clean clean-db clean-client ## Full cleanup of local generated state
	@echo "[!] Local project state reset complete"
