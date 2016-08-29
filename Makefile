.PHONY: build
build:
	docker build -t google/python .

.PHONY: tests
tests:
	make -C tests all

.PHONY: benchmarks
benchmarks:
	make -C tests benchmarks
