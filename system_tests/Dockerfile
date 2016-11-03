FROM google/python

# Inject secrets
ADD data/ data/
ENV GOOGLE_APPLICATION_CREDENTIALS /app/data/cloud-python-runtime-qa-credentials.json
ENV GCLOUD_PROJECT cloud-python-runtime-qa

# Get the source.
RUN git clone https://github.com/GoogleCloudPlatform/google-cloud-python.git
WORKDIR google-cloud-python

# Install tox for running the system tests
RUN pip install --upgrade tox

# List of system tests to run.  Ideally would be all of them.  But
# some of them get permission or other errors that are probably
# related to incomplete test setup.
ENV MODULES="datastore storage speech bigquery pubsub language translate monitoring bigtable"

# Run Python 2.7, 3.4 system tests
RUN GOOGLE_CLOUD_TESTS_API_KEY=$(cat /app/data/cloud-python-runtime-qa-api-key.txt) \
    tox -e system-tests,system-tests3 -- ${MODULES}
