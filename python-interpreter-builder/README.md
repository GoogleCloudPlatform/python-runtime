# Python Interpreter Builder

This is a Docker-based Python interpreter builder. It builds Python interpreters
using a Debian-based Docker image. These interpreters are suitable to be moved
to another Debian-based Docker image. This avoids needing to install build
dependencies in the final container.


## Building

Use:

    docker build --tag=google/python/interpreter-builder .

The interpreters will be stored in the image at `/interpreters.tar.gz`.  This is
suitable to be extracted from this image and added directly to another Docker
image via:

    ADD interpreters.tar.gz /

Docker will automatically un-tar the interpreters into `/opt`.
