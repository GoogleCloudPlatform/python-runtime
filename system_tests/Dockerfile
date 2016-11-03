FROM google/python

# Inject secrets
# TODO: Encrypt/decrypt secrets
ADD data/ data/
ENV GOOGLE_APPLICATION_CREDENTIALS /home/vmagent/app/data/cloud-python-runtime-qa-credentials.json

# Get the source.
RUN git clone https://github.com/GoogleCloudPlatform/google-cloud-python.git
WORKDIR google-cloud-python

# Checkout the latest release.
RUN git checkout $(git describe --tags --abbrev 0)

# Install gcloud so we can do test setup
RUN apt-get update && apt-get install curl
RUN curl https://sdk.cloud.google.com | bash
ENV PATH ${PATH}:/root/google-cloud-sdk/bin

# System test setup as per google-cloud-python/CONTRIBUTING.rst
RUN gcloud config set project cloud-python-runtime-qa
RUN gcloud components install app-engine-python
RUN gcloud auth activate-service-account \
    --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
RUN gcloud preview datastore create-indexes system_tests/data/index.yaml
# TODO: python system_tests/clear_datastore.py
# TODO: python system_tests/populate_datastore.py

# Install tox for running the system tests
RUN pip install --upgrade tox

# List of system tests to run.  Ideally would be all of them.  But
# some of them get permission or other errors that are probably
# related to incomplete test setup.
ENV MODULES="datastore storage speech bigquery pubsub language bigtable"

# Run Python 2.7, 3.4 system tests
# TODO(https://github.com/GoogleCloudPlatform/google-cloud-python/issues/2670)
RUN GOOGLE_CLOUD_TESTS_API_KEY=$(cat /home/vmagent/app/data/cloud-python-runtime-qa-api-key.txt) \
    tox -e system-tests,system-tests3 -- ${MODULES}
