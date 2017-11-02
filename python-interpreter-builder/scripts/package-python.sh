#!/bin/bash

set -euo pipefail
set -x

function usage {
  echo "Usage: $0 long_version tag
Create .deb package file for a Python interpreter with 
  long_version: (x.y.z) Interpreter version
  tag: version suffix unique to this build
" >&2
  exit 1
}
  # Process command line
if [ -z "${1:+set}" -o -z "${2:+set}" ]; then
  usage
fi
LONG_VERSION=$1
BUILD_TAG=$2
SHORT_VERSION=${1%.*}

# Compute version specs
DEB_PACKAGE_NAME=gcp-python${SHORT_VERSION}
# Can't have - (hyphen) in debian revision as per
# https://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Version
DEBIAN_REVISION=${BUILD_TAG//-/.}
DEB_PACKAGE_VERSION=${LONG_VERSION}-${DEBIAN_REVISION}

PACKAGE_DIR=/opt/packages
# E.g. gcp-python3.6_3.6.2-1gcp~2017.07.25.110644_amd64.deb
DEB_FILENAME=${DEB_PACKAGE_NAME}_${DEB_PACKAGE_VERSION}_amd64.deb

# Create directory for intermediate files
SCRATCH_DIR=$(mktemp --directory)
cd "${SCRATCH_DIR}"

# Synthesize Debian control file.  Note that the "Depends:" is
# currently Debian8-specific, and lacks version specifiers present in
# the standard Debian Python packages.
export DEB_PACKAGE_NAME DEB_PACKAGE_VERSION SHORT_VERSION
envsubst </DEBIAN/control.in >control \
  '${DEB_PACKAGE_NAME} ${DEB_PACKAGE_VERSION} ${SHORT_VERSION}'

# Generate components of .deb archive
tar czf control.tar.gz control
tar czf data.tar.gz "/opt/python${SHORT_VERSION}"
echo "2.0" >debian-binary

# Generate final .deb.
mkdir -p "${PACKAGE_DIR}"
ar rcD "${PACKAGE_DIR}/${DEB_FILENAME}" \
  debian-binary control.tar.gz data.tar.gz
rm debian-binary control.tar.gz data.tar.gz

# Validate .deb
dpkg --install --dry-run "${PACKAGE_DIR}/${DEB_FILENAME}"

# Add to list
echo "${DEB_FILENAME}" >> "${PACKAGE_DIR}/packages.txt"
