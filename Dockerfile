# The Google App Engine base image is debian (jessie) with ca-certificates
# installed.
FROM gcr.io/google_appengine/debian8

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

# Upgrade pip (debian package version tends to run a few version behind) and
# install virtualenv system-wide.
RUN pip install --upgrade pip virtualenv

# Install the Google-built interpreters
ADD python-interpreter-builder/output/interpreters.tar.gz /

# Setup the app working directory
RUN ln -s /home/vmagent/app /app
WORKDIR /app

# Port 8080 is the port used by Google App Engine for serving HTTP traffic.
EXPOSE 8080
ENV PORT 8080

# The user's Dockerfile must specify an entrypoint with ENTRYPOINT or CMD.
CMD []
