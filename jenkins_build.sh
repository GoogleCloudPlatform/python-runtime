#!/bin/sh

set -eu

RUNTIME_NAME="python"

CANDIDATE_NAME=`date +%Y-%m-%d_%H_%M`
echo "CANDIDATE_NAME:${CANDIDATE_NAME}"

if [ -z "${DOCKER_NAMESPACE+set}" ] ; then
  echo "Error: DOCKER_NAMESPACE is not set; invoke with something like DOCKER_NAMESPACE=gcr.io/YOUR-PROJECT-NAME" >&2
  exit 1
fi
IMAGE_NAME="${DOCKER_NAMESPACE}/${RUNTIME_NAME}:${CANDIDATE_NAME}"
export IMAGE_NAME

if [ -z "${GOOGLE_CLOUD_PROJECT+set}" ] ; then
  echo "Error: GOOGLE_CLOUD_PROJECT is not set; invoke with something like GOOGLE_CLOUD_PROJECT=YOUR-PROJECT-NAME" >&2
  exit 1
fi

export FORCE_REBUILD

make cloud-build
# We explicitly pull the image using 'gcloud', instead of letting
# Docker do it, so that we have the right credentials.
gcloud docker -- pull "${IMAGE_NAME}"
# Note that system test failures might be caused environment factors
# outside our control.  Also, the images will be pushed to GCR by the
# previous build step regardless of system test failures.
make integration-tests || \
  echo "ERROR: System test failure, please examine the logs"
