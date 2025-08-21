# Orlando Punx Infrastructure - Development Makefile
.DEFAULT_GOAL := help
.PHONY: help setup format lint test clean install dev-install refactor archive

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Orlando Punx Infrastructure - Development Commands$(NC)"
	@echo "================================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Initial project setup
	@echo "$(YELLOW)🚀 Setting up development environment...$(NC)"
	python -m pip install --upgrade pip
	pip install -e .[dev]
	pre-commit install
	@echo "$(GREEN)✅ Setup complete!$(NC)"

dev-install: ## Install development dependencies
	@echo "$(YELLOW)📦 Installing development dependencies...$(NC)"
	pip install -e .[dev]
	@echo "$(GREEN)✅ Development dependencies installed!$(NC)"

format: ## Format code with Black and isort
	@echo "$(YELLOW)🎨 Formatting code...$(NC)"
	black src/ scripts/ tools/
	isort src/ scripts/ tools/
	@echo "$(GREEN)✅ Code formatted!$(NC)"

lint: ## Run linters (flake8, mypy, shellcheck)
	@echo "$(YELLOW)🔍 Running linters...$(NC)"
	flake8 src/ scripts/ tools/
	mypy src/
	find . -name "*.sh" -not -path "./archive/*" -not -path "./venv/*" -not -path "./.venv/*" -exec shellcheck {} +
	@echo "$(GREEN)✅ Linting complete!$(NC)"

test: ## Run tests with coverage
	@echo "$(YELLOW)🧪 Running tests...$(NC)"
	pytest
	@echo "$(GREEN)✅ Tests complete!$(NC)"

clean: ## Clean build artifacts and cache
	@echo "$(YELLOW)🧹 Cleaning up...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/
	@echo "$(GREEN)✅ Cleanup complete!$(NC)"

# Refactoring commands
refactor: archive restructure consolidate ## Complete refactoring process

archive: ## Archive old files and virtual environment
	@echo "$(YELLOW)📦 Archiving old files...$(NC)"
	mkdir -p archive/old-scripts archive/old-workflows
	# Archive virtual environment
	if [ -d "scripts/event-sync/venv" ]; then \
		echo "$(YELLOW)Removing virtual environment...$(NC)"; \
		rm -rf scripts/event-sync/venv; \
	fi
	# Archive backup files
	find scripts/event-sync/ -name "*_backup.py" -exec mv {} archive/old-scripts/ \;
	find scripts/event-sync/ -name "*_old.py" -exec mv {} archive/old-scripts/ \;
	# Archive old workflows
	find .github/workflows/ -name "*backup*.yml" -exec mv {} archive/old-workflows/ \; || true
	find .github/workflows/ -name "*old*.yml" -exec mv {} archive/old-workflows/ \; || true
	@echo "$(GREEN)✅ Archiving complete!$(NC)"

restructure: ## Create new directory structure
	@echo "$(YELLOW)🏗️ Creating new directory structure...$(NC)"
	mkdir -p src/{scrapers,sync,gallery,utils}
	mkdir -p scripts tools/{debug,migration,monitoring}
	mkdir -p tests/{fixtures} docs/{setup,api,troubleshooting,development}
	mkdir -p config deployment/{docker,systemd} archive/migration-notes
	# Create __init__.py files
	touch src/__init__.py src/scrapers/__init__.py src/sync/__init__.py
	touch src/gallery/__init__.py src/utils/__init__.py tests/__init__.py
	@echo "$(GREEN)✅ Directory structure created!$(NC)"

consolidate: ## Consolidate and move core files
	@echo "$(YELLOW)🔄 Consolidating core files...$(NC)"
	# This would contain the actual file moving logic
	# For safety, this should be run interactively or with confirmation
	@echo "$(BLUE)ℹ️  File consolidation should be run manually$(NC)"
	@echo "$(BLUE)ℹ️  See CODEBASE_REFACTORING_ANALYSIS.md for details$(NC)"

check: format lint test ## Run all quality checks

pre-commit: ## Run pre-commit hooks manually
	@echo "$(YELLOW)🔍 Running pre-commit hooks...$(NC)"
	pre-commit run --all-files
	@echo "$(GREEN)✅ Pre-commit checks complete!$(NC)"

requirements: ## Generate requirements.txt from pyproject.toml
	@echo "$(YELLOW)📋 Generating requirements.txt...$(NC)"
	pip-compile pyproject.toml --output-file requirements.txt
	pip-compile pyproject.toml --extra dev --output-file requirements-dev.txt
	@echo "$(GREEN)✅ Requirements files generated!$(NC)"

install: ## Install production dependencies only
	@echo "$(YELLOW)📦 Installing production dependencies...$(NC)"
	pip install -e .
	@echo "$(GREEN)✅ Production dependencies installed!$(NC)"
