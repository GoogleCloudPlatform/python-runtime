# google/python

[`google/python`](https://index.docker.io/u/google/python) is a [docker](https://docker.io) base image that bundles the stable version of [python](http://python.org) installed from [debian stable](https://packages.debian.org/stable/) and [pip](https://pip.pypa.io/en/latest/) and [virtualenv](https://virtualenv.pypa.io/) installed from [PyPI](https://pypi.python.org/pypi).

## Usage

- Create a Dockerfile in your python application directory with the following content:

        FROM google/python

        WORKDIR /app
        RUN virtualenv /env
        ADD requirements.txt /app/requirements.txt
        RUN /env/bin/pip install requirements.txt
        ADD . /app
        
        CMD []
        ENTRYPOINT ["/env/bin/python", "/app/main.py"]

- Run the following command in your application directory:

        docker build -t my/app .
