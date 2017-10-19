FROM ${STAGING_IMAGE}

# Get the source.
RUN git clone --depth 1 https://github.com/GoogleCloudPlatform/google-cloud-python.git
WORKDIR google-cloud-python

# Upgrade setuptools
RUN pip install --upgrade setuptools

# Install nox
RUN pip install --upgrade nox-automation

# Run unit tests for all supported Python versions
ADD run_unit_tests.sh /run_unit_tests.sh
ENTRYPOINT ["/run_unit_tests.sh"]
