# Use no-cache to prevent layer caching because there is a layer that does
# a `git clone` which can not be cached.
DOCKER_FLAGS ?= --no-cache

ifndef GOOGLE_APPLICATION_CREDENTIALS
$(error GOOGLE_APPLICATION_CREDENTIALS is not set; download service account credentials in JSON format from the Google Cloud Console and invoke make with something like GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json)
endif

ifndef GOOGLE_CLOUD_PROJECT
$(error GOOGLE_CLOUD_PROJECT is not set; invoke make with something like GOOGLE_CLOUD_PROJECT=my-project-name)
endif


.PHONY: all
all: Dockerfile
	@echo "Running system tests in project ${GOOGLE_CLOUD_PROJECT} using service account credentials from ${GOOGLE_APPLICATION_CREDENTIALS}"
	docker build --tag google-cloud-python-system-tests $(DOCKER_FLAGS) .
	docker run --rm -v $(GOOGLE_APPLICATION_CREDENTIALS):/app/credentials/credentials.json google-cloud-python-system-tests

.PHONY:	Dockerfile
Dockerfile: Dockerfile.in
	envsubst < $< > $@
