#!/bin/bash

set -e

apt-get -q update

xargs -a <(awk '/^\s*[^#]/' '/resources/apt-packages.txt') -r -- \
    apt-get install --no-install-recommends -yq

apt-get upgrade -yq

# Remove unneeded files.
apt-get clean
rm /var/lib/apt/lists/*_*
