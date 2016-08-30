.PHONY: all
all: 2vs3

# Tests Python 2.7 against Python 3.4.
.PHONY: 2vs3
2vs3:
	cat Dockerfile Dockerfile.2vs3 | docker build -
