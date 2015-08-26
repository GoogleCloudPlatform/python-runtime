# The Google App Engine base image is debian (wheezy) with ca-certificates
# installed.
#FROM gcr.io/google_appengine/base
# Will switch back to google_appengine/base when it switches to jessie.
FROM debian:jessie
ENV DEBIAN_FRONTEND noninteractive
ENV PORT 8080

# Ideally, this should be moved into the base image
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
EXPOSE 8080

# Install Python, pip, and C dev libraries necessary to compile the most popular
# Python libraries.
RUN apt-get -q update && \
    apt-get install --no-install-recommends -y -q \
        python3 python3-dev python3-pip build-essential git mercurial \
        libffi-dev libssl-dev libxml2-dev \
        libxslt1-dev libpq-dev libmysqlclient-dev libcurl4-openssl-dev \
        libjpeg-dev zlib1g-dev libpng12-dev \
    && apt-get clean && rm /var/lib/apt/lists/*_*

# Upgrade pip (debian package version tends to run a few versions behind) and
# install virtualenv system-wide.
RUN pip3 install --upgrade pip virtualenv

# Install all application dependencies into a new virtualenv.
WORKDIR /app
RUN virtualenv /env
ONBUILD ADD requirements.txt /app/requirements.txt
ONBUILD RUN /env/bin/pip install -r /app/requirements.txt
ONBUILD ADD . /app

# Set virtualenv environment variables. This is equivalent to running source
# /env/bin/activate
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

CMD []
# The user's Dockerfile must specify an entrypoint.
