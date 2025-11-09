.PHONY: help setup start stop logs clean restart

.DEFAULT_GOAL := help

help:
	@echo "MCP Code Execution POC - Available Commands"
	@echo "make help      Show this help message"
	@echo "make setup     Complete project setup"
	@echo "make start     Start the FastAPI server"
	@echo "make stop      Stop the server and kill processes on port 8000"
	@echo "make restart   Stop and start the server"
	@echo "make logs      Show server logs (last 50 lines)"
	@echo "make clean     Stop server and clear all cache/temp files"

setup:
	@echo "Step 1/7: Checking Python version..."
	@python3 --version || (echo "Python 3.10+ required" && exit 1)
	@echo "Step 2/7: Installing/checking uv..."
	@if ! command -v uv &> /dev/null; then \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		export PATH="$$HOME/.local/bin:$$PATH"; \
	else \
		echo "uv already installed"; \
	fi
	@echo "Step 3/7: Installing Python dependencies..."
	@uv sync
	@echo "Step 4/7: Setting up environment configuration..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env file created - configure API keys before starting"; \
	else \
		echo ".env file already exists"; \
	fi
	@echo "Step 5/7: Creating required directories..."
	@mkdir -p workspace logs data/rag data/invoices data/rag_index servers
	@echo "Step 6/7: Setting up RAG index..."
	@if [ -f .env ] && grep -q "OPENAI_API_KEY=your-openai-api-key-here" .env; then \
		echo "Skipping RAG setup - configure OPENAI_API_KEY in .env first"; \
	else \
		uv run python scripts/setup_rag.py || echo "RAG setup skipped"; \
	fi
	@echo "Step 7/7: Setting up PostgreSQL database..."
	@if command -v docker &> /dev/null; then \
		if ! docker ps -q -f name=postgres-mcp | grep -q .; then \
			echo "Starting PostgreSQL in Docker..."; \
			docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres --name postgres-mcp postgres:14 2>&1 || docker start postgres-mcp 2>&1; \
			echo "Waiting for PostgreSQL to be ready..."; \
			sleep 5; \
		fi; \
		uv run python scripts/setup_pg.py || echo "PostgreSQL setup failed"; \
	else \
		echo "Docker not available - skipping PostgreSQL setup"; \
	fi
	@echo "Setup complete. Edit .env and run 'make start'"

start:
	@echo "Starting server at http://localhost:8000"
	@uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

stop:
	@echo "Stopping server..."
	@-pkill -9 -f "uvicorn app.main:app" 2>/dev/null || true
	@echo "Killing processes on port 8000..."
	@-lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@sleep 1
	@echo "Server stopped"

restart:
	@echo "Restarting server..."
	@$(MAKE) stop
	@sleep 2
	@$(MAKE) start

logs:
	@echo "=== Server Logs (last 50 lines) ==="
	@if [ -d logs ]; then \
		latest_log=$$(ls -t logs/*.json 2>/dev/null | head -1); \
		if [ -n "$$latest_log" ]; then \
			echo "Latest log file: $$latest_log"; \
			cat "$$latest_log" | python3 -m json.tool 2>/dev/null || cat "$$latest_log"; \
		else \
			echo "No log files found in logs/"; \
		fi; \
	else \
		echo "logs/ directory not found"; \
	fi
	@echo ""
	@echo "=== Recent Run Logs ==="
	@ls -lht logs/*.json 2>/dev/null | head -10 || echo "No logs found"

clean:
	@echo "Cleaning up..."
	@$(MAKE) stop
	@echo "Clearing Python cache..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clearing .pytest_cache..."
	@rm -rf .pytest_cache 2>/dev/null || true
	@echo "Clearing uv cache..."
	@rm -rf .venv/__pycache__ 2>/dev/null || true
	@echo "Clean complete"
