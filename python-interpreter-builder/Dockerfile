# The Google App Engine base image is debian (jessie) with ca-certificates
# installed.
FROM gcr.io/google-appengine/debian8

# Install Python build dependencies
RUN apt-get update && apt-get install -yq \
    build-essential \
    wget \
    pkg-config \
    libbz2-dev \
    libgdbm-dev \
    liblzma-dev \
    libncurses5-dev \
    libreadline-dev \
    libsqlite3-dev \
    libssl-dev \
    zlib1g-dev

# Setup locale. This prevents Python 3 IO encoding issues.
ENV LANG C.UTF-8

# Add build scripts
ADD scripts /scripts

# Build the Python 3.5 interpreter
RUN /scripts/build-python-3.5.sh

# Tar the interpreters. Tarring is needed because docker cp doesn't handle
# links correctly.
RUN tar czf /interpreters.tar.gz /opt
