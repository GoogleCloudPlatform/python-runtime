# Google Cloud Platform - Python Runtime Docker Image

This repository contains the source for the
[`gcr.io/google-appengine/python`](https://gcr.io/google-appengine/python)
[docker](https://docker.io) base image. This image can be used as the base image
for running applications on
[Google App Engine Flexible](https://cloud.google.com/appengine/docs/flexible/),
[Google Container Engine](https://cloud.google.com/container-engine), or any
other Docker host.

This image is based on Debian Jessie and contains packages required to build
most of the popular Python libraries. For more information about this runtime,
see the
[documentation](https://cloud.google.com/appengine/docs/flexible/python/runtime).

## App Engine

When using App Engine Flexible, you can use the runtime without worrying about
docker by specifying `runtime: python` in your `app.yaml`:

```yaml
runtime: python
vm: true
entrypoint: gunicorn -b :$PORT main:app

runtime_config:
  # You can also specify 2 for Python 2.7
  python_version: 3
```

If you have an existing App Engine application using this runtime and want to
customize it, you can use the
[`Cloud SDK`](https://cloud.google.com/sdk/gcloud/reference/preview/app/gen-config)
to create a custom runtime:

    gcloud beta app gen-config --custom 

You can then modify the `Dockerfile` and `.dockerignore` as needed for you
application.

## Container Engine & other Docker hosts.
  
For other docker hosts, you'll need to create a `Dockerfile` based on this image
that copies your application code, installs dependencies, and declares an
command or entrypoint. For example:

    FROM gcr.io/google-appengine/python
    
    # Create a virtualenv for dependencies. This isolates these packages from
    # system-level packages.
    RUN virtualenv /env
    
    # Setting these environment variables are the same as running
    # source /env/bin/activate.
    ENV VIRTUAL_ENV /env
    ENV PATH /env/bin:$PATH
    
    # Copy the application's requirements.txt and run pip to install all
    # dependencies into the virtualenv.
    ADD requirements.txt /app/requirements.txt
    RUN pip install -r /app/requirements.txt
    
    # Add the application source code.
    ADD . /app
    
    # Run a WSGI server to serve the application. gunicorn must be declared as
    # a dependency in requirements.txt.
    CMD gunicorn -b :$PORT main:app

## Building the image

Google regularly builds and releases this image at
[`gcr.io/google-appengine/python`](https://gcr.io/google-appengine/python).

To rebuild the image yourself, first set the following variables in your
shell. You need to be authenticated to a Google Cloud Project to invoke the
Google Container Builder service, and also to run the system tests.

```shell
$ export GOOGLE_CLOUD_PROJECT=YOUR-PROJECT-NAME
$ DOCKER_NAMESPACE=gcr.io/${GCLOUD_PROJECT}
$ CANDIDATE_NAME=`date +%Y-%m-%d_%H_%M`
$ export IMAGE_NAME=${DOCKER_NAMESPACE}/python:${CANDIDATE_NAME}
$ gcloud config set project ${GOOGLE_CLOUD_PROJECT}
```

To rebuild the image using the Google Container Builder service, do the
following:

```shell
$ make cloud-build
$ make cloud-test
```

To rebuild the image using your local Docker daemon, do the following:

``` shell
$ make local-build
$ make local-test
```

To open an interactive shell session to this image after building it, do the following:

``` shell
docker run -it --entrypoint /bin/bash ${IMAGE_NAME}
```

## Running the system tests

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

From the cloud console, you will need to enable the following APIs for your project:

-   Bigquery API
-   Cloud Bigtable Admin API
-   Google Cloud Natural Language API
-   Google Cloud Pub/Sub API
-   Google Cloud Storage JSON API
-   Google Cloud Vision API
-   Google Translate API
-   Stackdriver Logging API
-   Stackdriver Monitoring API

## Contributing changes

* See [CONTRIBUTING.md](CONTRIBUTING.md)

## Licensing

* See [LICENSE](LICENSE)
