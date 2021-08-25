ENV_NAME=vote-app-env
BIN=$(ENV_NAME)/bin/
PYTHON=$(BIN)/python

# Run linters check only
lint:
	$(BIN)isort . --profile black --skip $(ENV_NAME) --check
	$(BIN)black . --exclude=$(ENV_NAME) --check

# Run linters and try to fix the errors
format:
	$(BIN)isort . --profile black --skip $(ENV_NAME)
	$(BIN)black . --exclude=$(ENV_NAME)