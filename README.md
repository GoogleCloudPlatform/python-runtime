# Google Cloud Platform Python Docker Image

This repository contains the source for the `gcr.io/google_appengine/python` [docker](https://docker.io) base image. This image can be used as the base image for running applications on [Google App Engine Managed VMs](https://cloud.google.com/appengine), [Google Container Engine](https://cloud.google.com/container-engine), or any other Docker host.

This image is based on Debian Jessie and contains packages required to build most of the popular Python libraries.

## App Engine

To generate a Dockerfile that uses this image as a base, use the [`Cloud SDK`](https://cloud.google.com/sdk/gcloud/reference/preview/app/gen-config):

    gcloud preview app gen-config --custom 

You can then modify the `Dockerfile` and `.dockerignore` as needed for you application.

## Container Engine & other Docker hosts.
  
For other docker hosts, you'll need to create a `Dockerfile` based on this image that copies your application code, installs dependencies, and declares an command or entrypoint. For example:

    FROM gcr.io/google_appengine/python
    
    # Create a virtualenv for dependencies. This isolates these packages from
    # system-level packages.
    RUN virtualenv /env
    
    # Setting these environment variables are the same as running
    # source /env/bin/activate
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

## Contributing changes

* See [CONTRIBUTING.md](CONTRIBUTING.md)

## Licensing

* See [LICENSE](LICENSE)
