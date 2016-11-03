# Use no-cache to prevent layer caching because there is a layer that does
# a `git clone` which can not be cached.
CACHE ?= --no-cache

.PHONY: all
all:
	docker build $(CACHE) .
