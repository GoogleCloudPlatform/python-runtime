ifdef FORCE_REBUILD
	DOCKER_FLAGS = --no-cache --pull
endif

# Note: 'make build/tests/benchmarks' share images by retagging the
# candidate as 'google/python'.  So this could cause trouble with
# concurrent builds on the same machine.
CANDIDATE_NAME ?= $(shell date +%Y-%m-%d_%H_%M)
IMAGE_NAME ?= google/python:$(CANDIDATE_NAME)

.PHONY: build
build: build-interpreters
	docker build $(DOCKER_FLAGS) -t "$(IMAGE_NAME)" .
	docker tag -f "$(IMAGE_NAME)" "google/python"

.PHONY: build-interpreters
build-interpreters:
	export DOCKER_FLAGS
	make -C python-interpreter-builder build

.PHONY: tests
tests:
	make -C tests all

.PHONY: benchmarks
benchmarks:
	make -C tests benchmarks

.PHONY: cloudbuild
cloudbuild:
	envsubst <cloudbuild.yaml.in > cloudbuild.yaml
	gcloud alpha container builds create . --config=cloudbuild.yaml