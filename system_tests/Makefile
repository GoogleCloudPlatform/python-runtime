# Use no-cache to prevent layer caching because there is a layer that does
# a `git clone` which can not be cached.
DOCKER_FLAGS ?= --no-cache

.PHONY:	Dockerfile
Dockerfile: Dockerfile.in
	envsubst < $< > $@

.PHONY: all
all:
	docker build $(DOCKER_FLAGS) .
