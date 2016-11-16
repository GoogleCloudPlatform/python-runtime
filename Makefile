ifdef FORCE_REBUILD
	DOCKER_FLAGS = --no-cache --pull
endif

# Note: 'make build/tests/benchmarks' share images by retagging the
# candidate as 'google/python'.  So this could cause trouble with
# concurrent builds on the same machine.
CANDIDATE_NAME ?= $(shell date +%Y-%m-%d_%H_%M)
IMAGE_NAME ?= google/python:$(CANDIDATE_NAME)
export IMAGE_NAME

.PHONY: local-image
local-image: build-interpreters
	docker build $(DOCKER_FLAGS) -t "$(IMAGE_NAME)" .
	docker tag -f "$(IMAGE_NAME)" "google/python"

.PHONY: local-tests
local-tests: local-image
	curl https://raw.githubusercontent.com/GoogleCloudPlatform/runtimes-common/master/structure_tests/ext_run.sh > ext_run.sh
	chmod +x ext_run.sh
	make -C tests all

.PHONY: build-interpreters
build-interpreters:
	export DOCKER_FLAGS
	make -C python-interpreter-builder build

.PHONY: benchmarks
benchmarks:
	make -C tests benchmarks

.PHONY: google-cloud-system-tests
google-cloud-system-tests:
	make -C system_tests

.PHONY: cloudbuild
cloudbuild:
	envsubst <cloudbuild.yaml.in > cloudbuild.yaml
	gcloud alpha container builds create . --config=cloudbuild.yaml
