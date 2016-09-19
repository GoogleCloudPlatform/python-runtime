ifdef FORCE_REBUILD
	DOCKER_FLAGS = --no-cache --pull
endif

.PHONY: build
build: build-interpreters
	docker build $(DOCKER_FLAGS) -t google/python .

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
