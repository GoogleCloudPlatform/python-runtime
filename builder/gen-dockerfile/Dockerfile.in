FROM ${STAGING_IMAGE}
LABEL python_version=python3.6
RUN virtualenv --no-download /env -p python3.6

# Set virtualenv environment variables. This is equivalent to running
# source /env/bin/activate
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH
ADD requirements.txt /builder/
RUN pip install -r /builder/requirements.txt
ADD . /builder/
WORKDIR /workspace
ENTRYPOINT [ "python", "/builder/gen_dockerfile.py" ]
