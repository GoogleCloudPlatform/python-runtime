ifneq ($(FORCE_REBUILD),0)
	export DOCKER_FLAGS=--no-cache --pull
endif

ifndef IMAGE_NAME
$(error IMAGE_NAME is not set; invoke make with something like IMAGE_NAME=google/python:2017-01-02_03_45)
endif

.PHONY: all
all: cloud-test

## Files that must be refreshed every build

.PHONY: cloudbuild.yaml # Force reevaluation of env vars every time
cloudbuild.yaml: cloudbuild.yaml.in
	envsubst < $< > $@


.PHONY: tests/google-cloud-python/Dockerfile # Force reevaluation of env vars every time
tests/google-cloud-python/Dockerfile: tests/google-cloud-python/Dockerfile.in
	envsubst < $< > $@

.PHONY: ext_run.sh # Force refetch every time
ext_run.sh:
	curl https://raw.githubusercontent.com/GoogleCloudPlatform/runtimes-common/master/structure_tests/ext_run.sh > ext_run.sh
	chmod +x ext_run.sh

## Build using Google Container Builder service

.PHONY: cloud-build
cloud-build: cloudbuild.yaml tests/google-cloud-python/Dockerfile
	gcloud beta container builds submit . --config=cloudbuild.yaml

.PHONY: cloud-test
# structure-tests and google-cloud-python-tests are implicit in cloud-build
cloud-test: cloud-build integration-tests

## Build using local Docker daemon

.PHONY: local-build
local-build: local-build-interpreters
	docker build $(DOCKER_FLAGS) -t "$(IMAGE_NAME)" runtime-image

.PHONY: local-build-interpreters
local-build-interpreters:
	make -C python-interpreter-builder build

.PHONY: local-test
local-test: local-build local-structure-tests local-google-cloud-python-tests integration-tests

.PHONY: local-structure-tests
local-structure-tests: local-build ext_run.sh
	make -C tests structure-tests

# Unit tests for Google Cloud Client Library for Python
.PHONY: local-google-cloud-python-tests
local-google-cloud-python-tests: tests/google-cloud-python/Dockerfile
	make -C tests google-cloud-python

## Always local

.PHONY: integration-tests
integration-tests: google-cloud-python-system-tests benchmarks

# System tests for Google Cloud Client Library for Python.
# They require gcloud auth and network access.
.PHONY: google-cloud-python-system-tests
google-cloud-python-system-tests:
	make -C system_tests

.PHONY: benchmarks
benchmarks:
	make -C tests benchmarks
