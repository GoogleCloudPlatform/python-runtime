.PHONY: build
build:
	docker build $(DOCKER_FLAGS) -t google/python-interpreter-builder .
	# Extract the built interpreters
	# This is needed because `docker cp` doesn't work on images, just containers.
	docker run --name python-interpreter-builder google/python-interpreter-builder /bin/bash
	mkdir -p output
	docker cp --follow-link python-interpreter-builder:/interpreters.tar.gz output/interpreters.tar.gz
	docker rm python-interpreter-builder
