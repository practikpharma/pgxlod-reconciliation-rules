.DEFAULT_GOAL := help

.PHONY: build help test

OS=$(shell uname -s)

# UID mapping between host and container only matters when running Docker on Linux
ifeq ($(OS),Linux)
MAPUSER=-u $(shell id -u):$(shell id -g)
else
MAPUSER=
endif

# Shared paths between host and container must be windows path when running Docker under Cygwin
# winpty must be executed as a prefix for a docker run interactive session under Cygwin
ifeq ($(OS),CYGWIN_NT-10.0)
INTERACTIVE=winpty
else
INTERACTIVE=
endif

INAME=pgxlod-reconciliation-rules
VERSION=latest

bash: ## Start interactive mode with the Docker container
	@$(INTERACTIVE) docker run -it --rm --entrypoint=bash $(INAME):$(VERSION)

build: ## Build the pgxlod-reconciliation-rules docker image
	@docker build -t $(INAME):$(VERSION) .

help: ## Display available commands in Makefile
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

run: ## Run the Docker image in batch mode
	@docker run --rm $(MAPUSER) -v ${PWD}/data:/data $(INAME):$(VERSION) --configuration /data/conf.json.example --integration-ontology /data/pgxo.owl --max-rows 10000 --threads 4 batch --output /data/output.ttl

test: ## Run tests for the reconciliation scripts
	@./test/testrun.sh
