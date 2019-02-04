# The Google App Engine base image is debian (jessie) with ca-certificates
# installed.
# Source: https://github.com/GoogleCloudPlatform/debian-docker
FROM ${OS_BASE_IMAGE}

ADD resources /resources
ADD scripts /scripts

# Install Python, pip, and C dev libraries necessary to compile the most popular
# Python libraries.
RUN /scripts/install-apt-packages.sh

# Setup locale. This prevents Python 3 IO encoding issues.
ENV LANG C.UTF-8
# Make stdout/stderr unbuffered. This prevents delay between output and cloud
# logging collection.
ENV PYTHONUNBUFFERED 1

RUN wget https://storage.googleapis.com/python-interpreters/latest/interpreter-3.4.tar.gz && \
    wget https://storage.googleapis.com/python-interpreters/latest/interpreter-3.5.tar.gz && \
    wget https://storage.googleapis.com/python-interpreters/latest/interpreter-3.6.tar.gz && \
    wget https://storage.googleapis.com/python-interpreters/latest/interpreter-3.7.tar.gz && \
    tar -xzf interpreter-3.4.tar.gz && \
    tar -xzf interpreter-3.5.tar.gz && \
    tar -xzf interpreter-3.6.tar.gz && \
    tar -xzf interpreter-3.7.tar.gz && \
    rm interpreter-*.tar.gz

# Add Google-built interpreters to the path
ENV PATH /opt/python3.7/bin:/opt/python3.6/bin:/opt/python3.5/bin:/opt/python3.4/bin:$PATH
RUN update-alternatives --install /usr/local/bin/python3 python3 /opt/python3.6/bin/python3.6 50 && \
    update-alternatives --install /usr/local/bin/pip3 pip3 /opt/python3.6/bin/pip3.6 50

# Upgrade pip (debian package version tends to run a few version behind) and
# install virtualenv system-wide.
RUN /usr/bin/pip install --upgrade -r /resources/requirements.txt && \
    /opt/python3.4/bin/pip3.4 install --upgrade -r /resources/requirements.txt && \
    rm -f /opt/python3.4/bin/pip /opt/python3.4/bin/pip3 && \
    /opt/python3.5/bin/pip3.5 install --upgrade -r /resources/requirements.txt && \
    rm -f /opt/python3.5/bin/pip /opt/python3.5/bin/pip3 && \
    /opt/python3.6/bin/pip3.6 install --upgrade -r /resources/requirements.txt && \
    rm -f /opt/python3.6/bin/pip /opt/python3.6/bin/pip3 && \
    /opt/python3.7/bin/pip3.7 install --upgrade -r /resources/requirements.txt && \
    rm -f /opt/python3.7/bin/pip /opt/python3.7/bin/pip3 && \
    /usr/bin/pip install --upgrade -r /resources/requirements-virtualenv.txt

# Setup the app working directory
RUN ln -s /home/vmagent/app /app
WORKDIR /app

# Port 8080 is the port used by Google App Engine for serving HTTP traffic.
EXPOSE 8080
ENV PORT 8080

# The user's Dockerfile must specify an entrypoint with ENTRYPOINT or CMD.
CMD []
