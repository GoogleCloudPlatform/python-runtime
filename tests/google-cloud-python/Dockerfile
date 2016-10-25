FROM google/python

# Install tox
RUN pip install --upgrade tox

# Get the source.
RUN git clone https://github.com/GoogleCloudPlatform/google-cloud-python.git
WORKDIR google-cloud-python

# Checkout the latest release.
RUN git checkout $(git describe --tags)

# Run Python 2.7 unit tests
RUN python2.7 scripts/run_unit_tests.py

# Run Python 3.4 unit tests
RUN python3.4 scripts/run_unit_tests.py

# Run Python 3.5 unit tests
ENV PATH /opt/python3.5/bin:$PATH
RUN python3.5 scripts/run_unit_tests.py
