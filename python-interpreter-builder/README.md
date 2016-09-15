# Python Interpreter Builder

This is a Docker-based Python interpreter builder. It builds Python interpreters
using a Debian-based Docker image. These interpreters are suitable to be moved
to another Debian-based Docker image. This avoids needing to install build
dependencies in the final container.


## Building

Use make:

    make build

The interpreters will be outputted to `output/interpreters.tar.gz`, this is
suitable to be added directly to a Docker container:

    ADD interpreters.tar.gz /

Docker will automatically un-tar the interpreters into `/opt`.
