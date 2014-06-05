# google/python-runtime

[`google/python-runtime`](https://index.docker.io/u/google/python-runtime) is a [docker](https://docker.io) base image for easily running [Python](http://python.org) application.

It is based on [`google/python`](https://index.docker.io/u/google/python) base image.

## Usage

- Create a Dockerfile in your python application directory with the following content:

        FROM google/python-runtime

- Run the following command in your application directory:

        docker build -t my/app .

### Notes

- Your application sources are copied into the `/app` directory.
- A virtualenv with your dependencies is created under the `/env` directory.

## Notes

The image assumes that your application:

- has a [`requirements.txt`](https://pip.pypa.io/en/latest/user_guide.html#requirements-files) file to specify its dependencies
- listens on port `8080`
- either has a `main.py` script as entrypoint or defines `ENTRYPOINT ["/env/bin/python", "/app/some_other_file.py"]` in its `Dockerfile`


When building your application docker image, dependencies of your application are automatically fetched in a virtualenv using `pip install`.
