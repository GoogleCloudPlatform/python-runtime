#!/bin/bash

set -e

export IMAGE_NAME=$1

if [ -z "$1" ]; then
  echo "Usage: ./build.sh [image_path]"
  echo "Please provide fully qualified path to target image."
  exit 1
fi

envsubst < cloudbuild.yaml.in > cloudbuild.yaml
gcloud alpha container builds create . --config=cloudbuild.yaml
