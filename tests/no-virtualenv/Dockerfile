FROM google/python

RUN if [ "$(which python)" != "/usr/bin/python" ]; then exit 1; fi;
RUN pip install gunicorn
RUN if [ "$(which gunicorn)" != "/usr/local/bin/gunicorn" ]; then exit 1; fi;
