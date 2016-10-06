# Google Cloud Platform - Python Runtime Docker Image

This repository contains the source for the `gcr.io/google_appengine/python` [docker](https://docker.io) base image. This image can be used as the base image for running applications on [Google App Engine Flexible](https://cloud.google.com/appengine/docs/flexible/), [Google Container Engine](https://cloud.google.com/container-engine), or any other Docker host.

This image is based on Debian Jessie and contains packages required to build most of the popular Python libraries. For more information about this runtime, see the [documentation](https://cloud.google.com/appengine/docs/flexible/python/runtime).

## App Engine

When using App Engine Flexible, you can use the runtime without worrying about docker by specifying `runtime: python` in your `app.yaml`:

```yaml
runtime: python
vm: true
entrypoint: gunicorn -b :$PORT main:app

runtime_config:
  # You can also specify 2 for Python 2.7
  python_version: 3
```

If you have an existing App Engine application using this runtime and want to customize it, you can use the [`Cloud SDK`](https://cloud.google.com/sdk/gcloud/reference/preview/app/gen-config) to create a custom runtime:

    gcloud beta app gen-config --custom 

You can then modify the `Dockerfile` and `.dockerignore` as needed for you application. 

## Container Engine & other Docker hosts.
  
For other docker hosts, you'll need to create a `Dockerfile` based on this image that copies your application code, installs dependencies, and declares an command or entrypoint. For example:

    FROM gcr.io/google_appengine/python
    
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

## Contributing changes

* See [CONTRIBUTING.md](CONTRIBUTING.md)

## Licensing

* See [LICENSE](LICENSE)
