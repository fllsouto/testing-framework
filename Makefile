
ENV_FOLDER=.venv
ENV_ACTIVATE=.venv/bin/activate
SRC=src

.PHONY: setup_env install_deps setup_python test test-verbose format lint-black lint-bandit typecheck lint check

setup_env:
	echo "Setting up virtual environment..."
	python3 -m venv $(ENV_FOLDER)

install_deps: setup_env
	echo "Installing dependencies..."
	. $(ENV_ACTIVATE) && pip install -r requirements.txt

setup_python: install_deps
	echo "Setting up Python environment"

test:
	echo "Running tests..."
	. $(ENV_ACTIVATE) && pytest .

test-verbose:
	echo "Running tests (verbose, with stdout)..."
	. $(ENV_ACTIVATE) && pytest -sv .

format:
	echo "Formatting with black..."
	. $(ENV_ACTIVATE) && black $(SRC)

lint-black:
	echo "Checking formatting with black..."
	. $(ENV_ACTIVATE) && black --check --diff $(SRC)

lint-bandit:
	echo "Scanning for security issues with bandit..."
	. $(ENV_ACTIVATE) && bandit -r $(SRC) -c pyproject.toml

typecheck:
	echo "Type-checking with mypy..."
	. $(ENV_ACTIVATE) && mypy

lint: lint-black lint-bandit typecheck

check: lint test
