#!/bin/bash

# Build the benchmark image for release 1 from Dockerfile
echo "Building image for release 1"
export FULL_BASE_IMAGE="${DOCKER_NAMESPACE}/python:${TAG1}"
export TAG="${TAG1}"
envsubst <"Dockerfile".in >"Dockerfile" '$FULL_BASE_IMAGE $TAG'
docker build -t benchmark_1 .
rm Dockerfile

# Build the benchmark image for release 2 from Dockerfile
echo "Building image for release 2"
export FULL_BASE_IMAGE="${DOCKER_NAMESPACE}/python:${TAG2}"
export TAG="${TAG2}"
envsubst <"Dockerfile".in >"Dockerfile" '$FULL_BASE_IMAGE $TAG'
docker build -t benchmark_2 .
rm Dockerfile

echo "Successfully built images"

# Start running the containers
docker run -it --name benchmark_1 -h CONTAINER1 -v /"${TAG1}" benchmark_1 ls
docker run -it --name benchmark_2 -h CONTAINER2 -v /"${TAG2}" benchmark_2 ls

# Create folders to hold the files
mkdir release1
mkdir release2

# Copy the benchmark result for python versions from container to host
docker cp benchmark_1:/"${TAG1}"/ release1/
docker cp benchmark_2:/"${TAG2}"/ release2/

echo "Start benchmarking the python interpreter performance between the two releases"

# Compare the performance between the interpreter in different release
pyperformance compare release1/"${TAG1}"/py2.7.json release2/"${TAG2}"/py2.7.json --output_style table > py2.7_res
pyperformance compare release1/"${TAG1}"/py3.4.json release2/"${TAG2}"/py3.4.json --output_style table > py3.4_res
pyperformance compare release1/"${TAG1}"/py3.5.json release2/"${TAG2}"/py3.5.json --output_style table > py3.5_res

echo "Completed"