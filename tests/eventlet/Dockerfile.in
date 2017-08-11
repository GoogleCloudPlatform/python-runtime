FROM ${STAGING_IMAGE}
LABEL python_version=python3.6
RUN virtualenv --no-download /env -p python3.6

# Set virtualenv environment variables. This is equivalent to running
# source /env/bin/activate
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH
ADD requirements.txt /app/
RUN pip install -r requirements.txt
ADD . /app/
RUN gunicorn -k eventlet -b :$PORT --daemon main:app ; \
    wget --retry-connrefused --tries=5 http://localhost:$PORT/
