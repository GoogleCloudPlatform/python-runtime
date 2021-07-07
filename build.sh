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
build=0 # Should build images?
client_test=0 # Should run Google Cloud Client Library tests
test=0 # Should run standard test suite?

local=0 # Should run using local Docker daemon instead of GCR?

os_base=ubuntu18 # Which operating system base to use
interpreter=0 # Should build interpreters instead of images

# Note that $gcloud_cmd has spaces in it
gcloud_cmd="gcloud builds submit"
# May need to install via "gcloud components install cloud-build-local"
local_gcloud_cmd="cloud-build-local --push=false --dryrun=false"

# Helper functions
function fatal() {
  echo "$1" >&2
  exit 1
}

function usage {
  fatal "Usage: $0 [OPTION]...
Build and test artifacts in this repository

Options:
  --[no]benchmark: Run benchmarking suite (default false)
  --[no]build: Build all images (default true if no options set)
  --[no]test: Run basic tests (default true if no options set)
  --[no]client_test: Run Google Cloud Client Library tests (default false)
  --[no]local: Build images using local Docker daemon (default false)
  --os_base: Which OS image to build on top of [debian8, ubuntu16, ubuntu18]
"
}

# Read environment variables
if [ -z "${DOCKER_NAMESPACE:+set}" ] ; then
  fatal 'Error: $DOCKER_NAMESPACE is not set; invoke with something like DOCKER_NAMESPACE=gcr.io/YOUR-PROJECT-NAME'
fi

if [ -z "${BUILDER_DOCKER_NAMESPACE:+set}" ] ; then
  export BUILDER_DOCKER_NAMESPACE="${DOCKER_NAMESPACE}"
fi

if [ -z "${TAG:+set}" ] ; then
  export TAG=`date +%Y-%m-%d-%H%M%S`
fi

build_substitutions="\
_BUILDER_DOCKER_NAMESPACE=${BUILDER_DOCKER_NAMESPACE},\
_DOCKER_NAMESPACE=${DOCKER_NAMESPACE},\
_TAG=${TAG}\
"

substitutions="\
_DOCKER_NAMESPACE=${DOCKER_NAMESPACE},\
_TAG=${TAG}\
"

# Read command line arguments
while [ $# -gt 0 ]; do
  case "$1" in
    --benchmark)
      benchmark=1
      shift
      ;;
    --nobenchmark)
      benchmark=0
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
    --client_test)
      client_test=1
      shift
      ;;
    --noclient_test)
      client_test=0
      shift
      ;;
    --local)
      local=1
      shift
      ;;
    --nolocal)
      local=0
      shift
      ;;
    --os_base=debian8)
      os_base=debian8
      shift
      ;;
    --os_base=ubuntu16)
      os_base=ubuntu16
      shift
      ;;
    --os_base=ubuntu18)
      os_base=ubuntu18
      shift
      ;;
    --test)
      test=1
      shift
      ;;
    --notest)
      test=0
      shift
      ;;
    --interpreter)
      interpreter=1
      shift
      ;;
    *)
      usage
      ;;
  esac
done

# If no actions chosen, then tell the user
if [ "${benchmark}" -eq 0 -a \
  "${build}" -eq 0 -a \
  "${client_test}" -eq 0 -a \
  "${test}" -eq 0 \
]; then
  echo 'No actions specified, defaulting to --build --test'
  build=1
  test=1
fi

# Running build local or remote?
if [ "${local}" -eq 1 ]; then 
  gcloud_cmd="${local_gcloud_cmd}"
fi

# Pick OS image to use as base
if [ "${os_base}" == "debian8" ]; then
  export OS_BASE_IMAGE="gcr.io/google-appengine/debian8:latest"
elif [ "${os_base}" == "ubuntu16" ]; then
  export OS_BASE_IMAGE="gcr.io/gcp-runtimes/ubuntu_16_0_4:latest"
elif [ "${os_base}" == "ubuntu18" ]; then
  export OS_BASE_IMAGE="gcr.io/gcp-runtimes/ubuntu_18_0_4:latest"
else
  echo "Unsupported OS base image: $OS_BASE_IMAGE"
  exit 1
fi
export STAGING_IMAGE="${DOCKER_NAMESPACE}/python:${TAG}"
echo "Using base image name ${STAGING_IMAGE}"

# Generate Dockerfiles
for outfile in \
  builder/gen-dockerfile/Dockerfile \
  python-interpreter-builder/Dockerfile \
  runtime-image/Dockerfile \
  tests/benchmark/Dockerfile \
  tests/eventlet/Dockerfile \
  tests/google-cloud-python/Dockerfile \
  tests/integration/Dockerfile \
  ; do
  envsubst <"${outfile}".in >"${outfile}" \
    '$OS_BASE_IMAGE $STAGING_IMAGE $GOOGLE_CLOUD_PROJECT_FOR_TESTS $TAG'
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

# Make a file available to the eventlet test.
cp -a scripts/testdata/hello_world/main.py tests/eventlet/main.py

# Build interpreters and push to GCS
if [ "${interpreter}" -eq 1 ]; then
  echo "Building interpreters"
  ${gcloud_cmd} \
    --config=cloudbuild_interpreters.yaml \
    .
fi

# Build images and push to GCR
if [ "${build}" -eq 1 ]; then
  echo "Building images"
  ${gcloud_cmd} \
    --config=cloudbuild.yaml \
    --substitutions="${build_substitutions}" \
    .
fi

# Run the tests that don't require (too many) external services
if [ "${test}" -eq 1 ]; then
  echo "Testing compatibility with popular Python libraries"
  ${gcloud_cmd} \
    --config=cloudbuild_test.yaml \
    --substitutions="${substitutions}" \
    .
fi

# Run client library tests
if [ "${client_test}" -eq 1 ]; then
  echo "Testing compatibility with Google Cloud Client Libraries"
  ${gcloud_cmd} \
    --config=cloudbuild_client_test.yaml \
    --substitutions="${substitutions}" \
    .
fi

# Run benchmarks
if [ "${benchmark}" -eq 1 ] ; then
  echo "Running benchmark"
  ${gcloud_cmd} \
    --config=cloudbuild_benchmark.yaml \
    --substitutions="${substitutions}" \
    .
fi
