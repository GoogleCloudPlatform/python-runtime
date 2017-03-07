#!/bin/bash
# This is a generated file.  Do not edit.

set -euo pipefail

SOURCE_DIR=.

# Setup staging directory
HOST_WORKSPACE=$(mktemp -d)
function cleanup {
    if [ "${HOST_WORKSPACE}" != '/' -a -d "${HOST_WORKSPACE}" ]; then
        rm -rf "${HOST_WORKSPACE}"
    fi
}
trap cleanup EXIT

# Copy source to staging directory
echo "Copying source to staging directory ${HOST_WORKSPACE}"
rsync -avzq --exclude=.git "${SOURCE_DIR}" "${HOST_WORKSPACE}"

# Build commands
docker run --volume /var/run/docker.sock:/var/run/docker.sock --volume /root/.docker:/root/.docker --volume ${HOST_WORKSPACE}:/workspace --workdir /workspace --env 'MESSAGE=Hello World!' debian /bin/sh -c 'printenv MESSAGE'

docker run --volume /var/run/docker.sock:/var/run/docker.sock --volume /root/.docker:/root/.docker --volume ${HOST_WORKSPACE}:/workspace --workdir /workspace --env 'MESSAGE=Goodbye\n And Farewell!' --env UNUSED=unused debian /bin/sh -c 'printenv MESSAGE'

# End of build commands

echo "Build completed successfully"
