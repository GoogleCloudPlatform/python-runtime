FROM ${STAGING_IMAGE}

# Install performance
RUN pip install performance

# Create virtual environment
RUN pip install --upgrade virtualenv

# Required for Python 3.4, see
# https://bugs.launchpad.net/ubuntu/+source/python3.4/+bug/1290847
RUN apt-get update && apt-get install -y --force-yes python3-pip python3-venv

RUN mkdir /result

# Run the benchmark and compare the performance, add the
# --debug-single-value flag to let the benchmark run in fastest mode
RUN pyperformance run --debug-single-value --python=python2.7 -o /result/py2.7.json
RUN pyperformance run --debug-single-value --python=python3.4 -o /result/py3.4.json
RUN pyperformance run --debug-single-value --python=python3.5 -o /result/py3.5.json
RUN if [ -e "/opt/python3.6/bin/python3.6" ]; then pyperformance run --debug-single-value --python=python3.6 -o /result/py3.6.json; fi

RUN pyperformance compare /result/py2.7.json /result/py3.4.json --output_style table
RUN pyperformance compare /result/py3.4.json /result/py3.5.json --output_style table
RUN if [ -e "/result/py3.6.json" ]; then pyperformance compare /result/py3.5.json /result/py3.6.json --output_style table; fi