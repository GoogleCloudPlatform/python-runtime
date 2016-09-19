ifdef FORCE_REBUILD
	DOCKER_FLAGS = --no-cache --pull
endif

IMAGE_NAME ?= google/python

.PHONY: build
build: build-interpreters
	docker build $(DOCKER_FLAGS) -t "$(IMAGE_NAME)" .

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
