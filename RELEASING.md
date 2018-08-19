# Google Cloud Platform - Python Runtime Docker Image

## `build.sh`

There is a shell script called `build.sh` that builds everything in this
repository.

### Environment variables for `build.sh`

DOCKER_NAMESPACE
: The prefix applied to all images names created.  To push images to Google
Container Registry (GCR), this should be `gcr.io/YOUR-PROJECT-NAME`.

TAG
: The suffix applied to all images created.  This should be unique.  If not
specified, the current time will be used (timestamp format `YYYY-mm-dd-HHMMSS`).

GOOGLE_APPLICATION_CREDENTIALS_FOR_TESTS
: (System test only) Path to service account credentials in JSON format.

GOOGLE_CLOUD_PROJECT_FOR_TESTS
: (System test only) Name of the Google Cloud Platform project to run the system
tests under.
  
## Building and Releasing

A custom Jenkins job builds and releases this repository using scripts and job
configurations that are not yet available publicly.  The control flow is as
follows:

1. Jenkins job `python/release` is invoked by
  a. Manually running the script `build_and_release.py` with arguments
  b. Manually invoking the job from the GUI
2. The job runs the script `release.sh`
  a. Service account credentials are read
  b. `gcloud auth activate-service-account` is performed
  c. `gcloud config set project` is performed
3. The script invokes `build.sh` in this repository
4. `build.sh` invokes Google Cloud Build with the `cloudbuild-*.yaml`
   config files.

## Building interpreters

The interpreters used are now built in a separate step, and stored on GCS.
This allows the runtime images to be build more rapidly.

To build the interpreters, run:

```shell
gcloud builds submit . --config=cloudbuild_interpreters.yaml
```

## Building outside Jenkins

To build this repository outside Jenkins, authenticate and authorize yourself
with `gcloud auth`, set the variables listed above, and run:

``` shell
./build.sh
```

This assumes an environment similar to the internal Jenkins environment (Linux,
Debian or Ubuntu-like).

## Building locally

To build this repository using local Docker commands instead of the Google
Cloud Build service, add the `--local` flag as shown:

``` shell
./build.sh --local
```

To open an interactive shell session to this image after building it, do the
following:

``` shell
docker run -it --entrypoint /bin/bash YOUR-IMAGE-NAME
```

## Running tests against a released image

To run compatibility tests against an existing image, such as
`gcr.io/google-appengine/python:latest`, run:

```shell
DOCKER_NAMESPACE=gcr.io/google-appengine TAG=latest ./build.sh --nobuild --test
```

## Running benchmarks

There is a benchmark suite which compares the performance of interpreters
against each other.

**Benchmark different versions of interpreter in the same release

``` shell
DOCKER_NAMESPACE=DOCKER_NAMESPACE_EXAMPLE TAG=TAG_EXAMPLE ./build.sh --nobuild --benchmark
```

**Benchmark same versions of interpreter from release to release

``` shell
DOCKER_NAMESPACE=DOCKER_NAMESPACE_EXAMPLE TAG1=TAG1_EXAMPLE TAG2=TAG2_EXAMPLE ./benchmark_between_releases.sh
```

Since these benchmarks are run on cloud instances, the timings may vary from run
to run.

## Running system tests

**TAKE NOTE: You will incur charges for use of Google Cloud Platform services!**

System tests perform mutating operations against the real Google Cloud services.
Since these system tests may fail or be flaky for outside reasons such as
netorking issues, configuration errors, or services outages, they are run
separately from building the images, and should be run in their own project.

To run the system tests, you need a Google Cloud Project with a service account.
From the [Google Cloud Console](https://console.cloud.google.com/), either
create a new project or switch to an existing one. Next,
[create a service account](
https://cloud.google.com/iam/docs/creating-managing-service-accounts) that will
be used to run the system tests. Once you have a service account,
[create and download a service account key](https://cloud.google.com/iam/docs/managing-service-account-keys).

In the
[IAM & Admin](https://console.cloud.google.com/permissions/projectpermissions)
section, grant the `Owner` role to the service account you created above.  Also
grant the `Editor` role to the `cloud-logs@google.com` service account.

Then, follow the
[system test setup instructions](https://github.com/GoogleCloudPlatform/google-cloud-python/blob/master/CONTRIBUTING.rst#running-system-tests). It
describes various steps, including running some scripts to populate and/or
delete datastore example data and indexes (populate_datastore.py,
clear_datastore.py, and `gcloud preview datastore create-indexes
system_tests/data/index.yaml`).

From the cloud console, you will need to enable at least the following APIs for
your project:

-   Bigquery API
-   Cloud Bigtable Admin API
-   Cloud Spanner API
-   Google Cloud Natural Language API
-   Google Cloud Pub/Sub API
-   Google Cloud Speech API
-   Google Cloud Storage JSON API
-   Google Cloud Translation API
-   Google Cloud Vision API
-   Stackdriver Logging API
-   Stackdriver Monitoring API

Once all the setup has been done, run the following:

``` shell
./build.sh --nobuild --system_tests
```
