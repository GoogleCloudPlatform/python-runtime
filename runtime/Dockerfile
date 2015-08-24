# The Google App Engine base image is debian (wheezy) with ca-certificates
# installed.
FROM gcr.io/google_appengine/base

# Install Python, pip, and C dev libraries necessary to compile the most popular
# Python libraries.
RUN apt-get -q update && \
 apt-get install --no-install-recommends -y -q \
   python2.7 python-pip python-dev build-essential git mercurial \
   libffi-dev libssl-dev libxml2-dev \
   libxslt1-dev libpq-dev libmysqlclient-dev libcurl4-openssl-dev \
   libjpeg-dev zlib1g-dev libpng12-dev && \
 apt-get clean && rm /var/lib/apt/lists/*_*

# Upgrade pip (debian package version tends to run a few version behind) and
# install virtualenv system-wide.
RUN pip install --upgrade pip virtualenv

EXPOSE 8080

# Install all application dependencies into a new virtualenv.
WORKDIR /app
ONBUILD RUN virtualenv /env
ONBUILD ADD requirements.txt /app/requirements.txt
ONBUILD RUN /env/bin/pip install -r /app/requirements.txt
ONBUILD ADD . /app

# Set virtualenv environment variables. This is equivalent to running source
# /env/bin/activate
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH
ENV PORT 8080

CMD []
# The user's Dockerfile must specify an entrypoint.
