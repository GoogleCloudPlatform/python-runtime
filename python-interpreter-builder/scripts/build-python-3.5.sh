#!/bin/bash

set -e

# Get the source
mkdir -p /opt/sources
cd /opt/sources
wget -nv https://www.python.org/ftp/python/3.5.2/Python-3.5.2.tgz
tar xzf Python-3.5.2.tgz

# Build
cd Python-3.5.2
# Use /opt/python{X}.{Y} for the prefix.
./configure --prefix=/opt/python3.5 --with-lto
# Explicitly build the profile-guided-optimized interpreter
make profile-opt
make install

# Clean-up sources
rm /opt/sources/Python-3.5.2.tgz
rm -r /opt/sources/Python-3.5.2
