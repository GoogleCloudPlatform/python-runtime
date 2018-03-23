# The Google App Engine base image is debian (jessie) with ca-certificates
# installed.
FROM ${OS_BASE_IMAGE}

# Install Python build dependencies (based on Debian Build-Depends)
RUN apt-get update && apt-get install -yq \
    autoconf \
    blt-dev \
    bzip2 \
    debhelper \
    dpkg-dev \
    gcc \
    gettext-base \
    libbluetooth-dev \
    libbz2-dev \
    libdb-dev \
    libexpat1-dev \
    libffi-dev \
    libgdbm-dev \
    libgpm2 \
    liblzma-dev \
    libmpdec-dev \
    libncursesw5-dev \
    libreadline-dev \
    libsqlite3-dev \
    libssl-dev \
    locales \
    lsb-release \
    mime-support \
    net-tools \
    netbase \
    python \
    python3 \
    sharutils \
    time \
    tk-dev \
    wget \
    xauth \
    xvfb \
    zlib1g-dev \
  && rm -rf /var/lib/apt/lists/*

# Setup locale. This prevents Python 3 IO encoding issues.
ENV LANG C.UTF-8

# Add build scripts
ADD scripts /scripts
ADD DEBIAN /DEBIAN
