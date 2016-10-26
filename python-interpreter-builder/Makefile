INTERPRETER_IMAGE_NAME ?= gcr.io/gcp-runtimes/python-interpreter-builder

.PHONY: build
build:
	docker build $(DOCKER_FLAGS) -t google/python-interpreter-builder .
	# Extract the built interpreters
	# This is needed because `docker cp` doesn't work on images, just containers.
	-docker rm python-interpreter-builder
	docker run --name python-interpreter-builder google/python-interpreter-builder /bin/bash
	docker cp python-interpreter-builder:/interpreters.tar.gz interpreters.tar.gz
	docker rm python-interpreter-builder

# This requires the $INTERPRETER_IMAGE_NAME env var to be set.
cloudbuild:
	envsubst <cloudbuild.yaml.in >cloudbuild.yaml
	gcloud alpha container builds create . --config=cloudbuild.yaml