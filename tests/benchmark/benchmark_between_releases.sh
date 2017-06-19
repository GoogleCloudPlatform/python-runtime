#!/bin/bash

# Build the benchmark image for release 1 from Dockerfile
echo "Building image for release 1"
export STAGING_IMAGE="${DOCKER_NAMESPACE}/python:${TAG1}"
envsubst <"Dockerfile".in >"Dockerfile" '$STAGING_IMAGE'
docker build --no-cache -t benchmark_1 .
rm Dockerfile

# Build the benchmark image for release 2 from Dockerfile
echo "Building image for release 2"
export STAGING_IMAGE="${DOCKER_NAMESPACE}/python:${TAG2}"
envsubst <"Dockerfile".in >"Dockerfile" '$STAGING_IMAGE'
docker build --no-cache -t benchmark_2 .
rm Dockerfile

echo "Successfully built images"

# Create folders to hold the files
mkdir "$TAG1"
mkdir "$TAG2"

# Start running the containers and copy the benchmark result for python versions from container to host
docker run -it --name benchmark_1 -h CONTAINER1 -v "${PWD}"/"$TAG1":/export benchmark_1 /bin/bash -c "cp /result/py*.json /export/"
docker run -it --name benchmark_2 -h CONTAINER2 -v "${PWD}"/"$TAG2":/export benchmark_2 /bin/bash -c "cp /result/py*.json /export/"

echo "Start benchmarking the python interpreter performance between the two releases"

# Compare the performance between the interpreter in different release
pyperformance compare "$TAG1"/py2.7.json "$TAG2"/py2.7.json --output_style table > py2.7_res
pyperformance compare "$TAG1"/py3.4.json "$TAG2"/py3.4.json --output_style table > py3.4_res
pyperformance compare "$TAG1"/py3.5.json "$TAG2"/py3.5.json --output_style table > py3.5_res

# Check if the python3.6 benchmark result exists
if [[ ( -e '"$TAG1"/py3.6.json' ) && ( -e '"$TAG2"/py3.6.json' ) ]]; then
    pyperformance compare "$TAG1"/py3.6.json "$TAG2"/py3.6.json --output_style table > py3.6_res;
fi

echo "Start extracting data and generating CSV file, then upload to Cloud Storage and insert to Big Query table"

# Extracting memory usage and running time data from the performace result json, generating CSV files
for path_to_file in $TAG1/*.json; do
    python generate_csv.py --filename $path_to_file --tag $TAG1
done

for path_to_file in $TAG2/*.json; do
    python generate_csv.py --filename $path_to_file --tag $TAG2
done

# Set the project that hold the cloud storage bucket and big query tables
gcloud config set project cloud-python-runtime-qa

# Get the list of existing release data on Cloud Storage and skip if the current TAG1 or TAG2 existing in the list
gsutil ls gs://python-runtime-benchmark > existing_releases

for container_tag in $TAG1 $TAG2; do
    if grep --fixed-strings --quiet "$container_tag" existing_releases; then
        echo "Performance data of $container_tag existed, so skip processing it."
    else
        # Upload the CSV files to Cloud Storage
        gsutil cp -r $container_tag gs://python-runtime-benchmark
        # Load the CSV files from Cloud Storage to Big Query table
        # Load the performance data of each function
        for path_to_file in $container_tag/py2.7.csv $container_tag/py3.4.csv $container_tag/py3.5.csv; do
             bq load benchmark.benchmark_functions gs://python-runtime-benchmark/"$path_to_file" container_tag:string,runtime_version:string,function_name:string,time_used:float,mem_usage:float
        done
        # Load the average performance data of each runtime version in a release
        bq load benchmark.benchmark_statistics gs://python-runtime-benchmark/"$container_tag"/averages.csv container_tag:string,runtime_version:string,ave_time_used:float,ave_mem_usage:float
    fi
done

echo "Completed"
