.PHONY: build
build:
	docker build $(DOCKER_FLAGS) -t google/python-interpreter-builder .
	# Extract the built interpreters
	# This is needed because `docker cp` doesn't work on images, just containers.
	-docker rm python-interpreter-builder
	docker run --name python-interpreter-builder google/python-interpreter-builder /bin/bash
	mkdir -p output
	docker cp python-interpreter-builder:/interpreters.tar.gz ../runtime-image/interpreters.tar.gz
	docker rm python-interpreter-builder
