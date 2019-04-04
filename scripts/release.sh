#!/bin/bash
set -euo pipefail
export KOKORO_GITHUB_DIR=${KOKORO_ROOT}/src/github
source ${KOKORO_GFILE_DIR}/kokoro/common.sh

source "${KOKORO_PIPER_DIR}/google3/third_party/runtimes_common/kokoro/common.sh"

cd ${KOKORO_GITHUB_DIR}/python-runtime

if [ -z "${TAG:+set}" ]; then
  export TAG=$(date +%Y-%m-%d-%H%M%S)
fi

./build.sh $BUILD_FLAGS

METADATA=$(pwd)/METADATA
cd ${KOKORO_GFILE_DIR}/kokoro
python note.py python -m ${METADATA} -t ${TAG}
