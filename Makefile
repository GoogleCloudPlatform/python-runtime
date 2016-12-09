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
	-docker rmi "google/python" 2>/dev/null
	docker tag "$(IMAGE_NAME)" "google/python"

.PHONY: build-interpreters
build-interpreters:
	export DOCKER_FLAGS
	make -C python-interpreter-builder build

cloudbuild.yaml: cloudbuild.yaml.in
	envsubst < cloudbuild.yaml.in > cloudbuild.yaml

.PHONY: cloudbuild
cloudbuild: cloudbuild.yaml
	gcloud alpha container builds create . --config=cloudbuild.yaml

.PHONY: build
# no structure tests since they are implicit in cloudbuild
build: cloudbuild integration-tests

.PHONY: build-local
build-local: local-image structure-tests integration-tests

.PHONY: ext_run.sh # Force refetch every time
ext_run.sh:
	curl https://raw.githubusercontent.com/GoogleCloudPlatform/runtimes-common/master/structure_tests/ext_run.sh > ext_run.sh
	chmod +x ext_run.sh

.PHONY: structure-tests
structure-tests: local-image ext_run.sh
	make -C tests structure-tests

.PHONY: benchmarks
benchmarks:
	make -C tests benchmarks

.PHONY: google-cloud-python
google-cloud-python:
	make -C tests google-cloud-python

.PHONY: google-cloud-system-tests
google-cloud-system-tests:
	make -C system_tests

.PHONY: integration-tests
tests: benchmarks google-cloud-system-tests google-cloud-python
