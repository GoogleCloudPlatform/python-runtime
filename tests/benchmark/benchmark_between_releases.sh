#!/bin/bash

# Build the benchmark image for release 1 from Dockerfile
echo "Building image for release 1"
export FULL_BASE_IMAGE="${DOCKER_NAMESPACE}/python:${TAG1}"
envsubst <"Dockerfile".in >"Dockerfile" '$FULL_BASE_IMAGE'
docker build --no-cache -t benchmark_1 .
rm Dockerfile

# Build the benchmark image for release 2 from Dockerfile
echo "Building image for release 2"
export FULL_BASE_IMAGE="${DOCKER_NAMESPACE}/python:${TAG2}"
envsubst <"Dockerfile".in >"Dockerfile" '$FULL_BASE_IMAGE'
docker build --no-cache -t benchmark_2 .
rm Dockerfile

echo "Successfully built images"

# Create folders to hold the files
mkdir release1
mkdir release2

# Start running the containers and copy the benchmark result for python versions from container to host
docker run -it --name benchmark_1 -h CONTAINER1 -v "${PWD}"/release1:/export benchmark_1 /bin/bash -c "cp /result/py*.json /export/"
docker run -it --name benchmark_2 -h CONTAINER2 -v "${PWD}"/release2:/export benchmark_2 /bin/bash -c "cp /result/py*.json /export/"

echo "Start benchmarking the python interpreter performance between the two releases"

# Compare the performance between the interpreter in different release
pyperformance compare release1/py2.7.json release2/py2.7.json --output_style table > py2.7_res
pyperformance compare release1/py3.4.json release2/py3.4.json --output_style table > py3.4_res
pyperformance compare release1/py3.5.json release2/py3.5.json --output_style table > py3.5_res

echo "Completed"
