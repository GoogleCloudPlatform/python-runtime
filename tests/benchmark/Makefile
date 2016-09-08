.PHONY: all
all: 2vs3 34vs35

# Tests Python 3.4 against Python 2.7.
.PHONY: 2vs3
2vs3:
	cat Dockerfile Dockerfile.2vs3 | docker build -

# Tests Python 3.5 against Python 3.4.
.PHONY: 2vs3
34vs35:
	cat Dockerfile Dockerfile.34vs35 | docker build -
