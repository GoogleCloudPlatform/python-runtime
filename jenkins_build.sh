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
export FORCE_REBUILD
make cloud-test
