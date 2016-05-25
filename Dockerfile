# The Google App Engine base image is debian (jessie) with ca-certificates
# installed.
FROM gcr.io/google_appengine/base

# Install Python, pip, and C dev libraries necessary to compile the most popular
# Python libraries.
RUN apt-get -q update && \
 apt-get install --no-install-recommends -y -q \
   python2.7 python3.4 python2.7-dev python3.4-dev python-pip build-essential git mercurial \
   libffi-dev libssl-dev libxml2-dev \
   libxslt1-dev libpq-dev libmysqlclient-dev libcurl4-openssl-dev \
   libjpeg-dev zlib1g-dev libpng12-dev \
   gfortran libblas-dev liblapack-dev libatlas-dev libquadmath0 \
   libfreetype6-dev pkg-config swig \
   && \
 apt-get clean && rm /var/lib/apt/lists/*_*

# Setup locale. This prevents Python 3 IO encoding issues.
ENV LANG C.UTF-8
# Make stdout/stderr unbuffered. This prevents delay between output and cloud
# logging collection.
ENV PYTHONUNBUFFERED 1

# Upgrade pip (debian package version tends to run a few version behind) and
# install virtualenv system-wide.
RUN pip install --upgrade pip virtualenv

RUN ln -s /home/vmagent/app /app
WORKDIR /app

# Port 8080 is the port used by Google App Engine for serving HTTP traffic.
EXPOSE 8080
ENV PORT 8080

# The user's Dockerfile must specify an entrypoint with ENTRYPOINT or CMD.
CMD []
