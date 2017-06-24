#!/bin/bash

# Copyright 2016 Google Inc. All rights reserved.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euo pipefail

# Actions
benchmark=0 # Should run benchmarks?
build=1 # Should build images?
system_tests=0 # Should run system tests?

local=0 # Should run using local Docker daemon instead of GCR?

# Note that $gcloud_cmd has spaces in it
gcloud_cmd="gcloud beta container builds submit ."
local_gcloud_cmd="scripts/local_cloudbuild.py"

# Helper functions
function fatal() {
  echo "$1" >&2
  exit 1
}

function usage {
  fatal "Usage: $0 [OPTION]...
Build and test artifacts in this repository

Options:
  --benchmark: Run benchmarking suite
  --[no]build: Build all images (default)
  --local: Build images using local Docker daemon
  --system_tests: Run system tests
"
}
  
# Read environment variables
if [ -z "${DOCKER_NAMESPACE+set}" ] ; then
  fatal 'Error: $DOCKER_NAMESPACE is not set; invoke with something like DOCKER_NAMESPACE=gcr.io/YOUR-PROJECT-NAME'
fi

if [ -z "${TAG+set}" ] ; then
  export TAG=`date +%Y-%m-%d-%H%M%S`
fi

substitutions="_DOCKER_NAMESPACE=${DOCKER_NAMESPACE},_TAG=${TAG}"

# Read command line arguments
while [ $# -gt 0 ]; do
  case "$1" in
    --benchmark)
      benchmark=1
      shift
      ;;
    --build)
      build=1
      shift
      ;;
    --nobuild)
      build=0
      shift
      ;;
    --local)
      local=1
      shift
      ;;
    --system_tests)
      system_tests=1
      shift
      ;;
    *)
      usage
      ;;
  esac
done

# If no actions chosen, then tell the user
if [ "${benchmark}" -eq 0 -a "${build}" -eq 0 -a "${system_tests}" -eq 0 ]; then
  fatal 'Error: No actions specified (for example, --build), exiting'
fi

# Running build local or remote?
if [ "${local}" -eq 1 ]; then 
  gcloud_cmd="${local_gcloud_cmd}"
fi

# Read action-specific environment variables
if [ "${system_tests}" -eq 1 ]; then
  if [ -z "${GOOGLE_APPLICATION_CREDENTIALS_FOR_TESTS+set}" ] ; then
    fatal 'Error: $GOOGLE_APPLICATION_CREDENTIALS_FOR_TESTS is not set; invoke with something like GOOGLE_APPLICATION_CREDENTIALS_FOR_TESTS=/path/to/service/account/creds.json'
  fi

  if [ -z "${GOOGLE_CLOUD_PROJECT_FOR_TESTS+set}" ] ; then
    fatal 'Error: $GOOGLE_CLOUD_PROJECT_FOR_TESTS is not set; invoke with something like GOOGLE_CLOUD_PROJECT_FOR_TESTS=YOUR-PROJECT-NAME'
  fi
fi

# Use latest released Debian as our base image
export DEBIAN_BASE_IMAGE="gcr.io/google-appengine/debian8:latest"
export STAGING_IMAGE="${DOCKER_NAMESPACE}/python:${TAG}"
echo "Using base image name ${STAGING_IMAGE}"

# Generate Dockerfiles
for outfile in \
  builder/gen-dockerfile/Dockerfile \
  python-interpreter-builder/Dockerfile \
  runtime-image/Dockerfile \
  tests/benchmark/Dockerfile \
  tests/google-cloud-python/Dockerfile \
  tests/google-cloud-python-system/Dockerfile \
  tests/integration/Dockerfile \
  ; do
  envsubst <"${outfile}".in >"${outfile}" '$DEBIAN_BASE_IMAGE $STAGING_IMAGE $GOOGLE_CLOUD_PROJECT_FOR_TESTS'
done

# Make some files available to the runtime builder Docker context
mkdir -p builder/gen-dockerfile/data
for file in \
  scripts/gen_dockerfile.py \
  scripts/validation_utils.py \
  scripts/data/* \
  ; do
  cp -a "${file}" "builder/gen-dockerfile/${file##scripts/}"
done

# Build images and push to GCR
if [ "${build}" -eq 1 ]; then
  echo "Building images"
  ${gcloud_cmd} --config cloudbuild.yaml --substitutions "${substitutions}"
fi

# If both system tests and benchmarks are requested, run them both
# even if one or the other has errors.  If the build step had errors,
# this script will have already exited.
exit_code=0

# Run system tests
if [ "${system_tests}" -eq 1 ]; then
  echo "Running system tests using project ${GOOGLE_CLOUD_PROJECT_FOR_TESTS}"

  trap "rm -f tests/google-cloud-python-system/credentials.json" EXIT
  cp "${GOOGLE_APPLICATION_CREDENTIALS_FOR_TESTS}" tests/google-cloud-python-system/credentials.json
  ${gcloud_cmd} --config cloudbuild_system_tests.yaml --substitutions  "${substitutions}" || \
    exit_code=1
  rm -f tests/google-cloud-python-system/credentials.json
fi

# Run benchmarks
if [ "${benchmark}" -eq 1 ] ; then
  echo "Running benchmark"
  ${gcloud_cmd} --config cloudbuild_benchmark.yaml --substitutions  "${substitutions}" || \
    exit_code=1
fi

exit ${exit_code}
