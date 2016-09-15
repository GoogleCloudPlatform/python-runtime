.PHONY: build
build: build-interpreters
	docker build -t google/python .

.PHONY: build-interpreters
build-interpreters:
	make -C python-interpreter-builder build

.PHONY: tests
tests:
	make -C tests all

.PHONY: benchmarks
benchmarks:
	make -C tests benchmarks
