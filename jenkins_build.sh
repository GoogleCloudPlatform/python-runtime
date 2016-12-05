RUNTIME_NAME="python"

CANDIDATE_NAME=`date +%Y-%m-%d_%H_%M`
echo "CANDIDATE_NAME:${CANDIDATE_NAME}"

IMAGE_NAME="${DOCKER_NAMESPACE}/${RUNTIME_NAME}:${CANDIDATE_NAME}"

export IMAGE_NAME
export FORCE_REBUILD
make build

if [ "${UPLOAD_TO_STAGING}" = "true" ]; then
  STAGING="${DOCKER_NAMESPACE}/${RUNTIME_NAME}:staging"
  docker rmi "${STAGING}" 2>/dev/null || true # Ignore if tag not present
  docker tag "${IMAGE_NAME}" "${STAGING}"
  gcloud docker push "${STAGING}"
fi
