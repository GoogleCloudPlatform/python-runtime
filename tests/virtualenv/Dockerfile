FROM google/python

ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

RUN if [ "$(which python)" != "/usr/bin/python" ]; then exit 1; fi;
RUN virtualenv /env
# All commands from this point on should use the virtualenv
RUN if [ "$(which python)" != "/env/bin/python" ]; then exit 1; fi;
RUN if [ "$(python --version 2>&1)" != "Python 2.7.9" ]; then exit 1; fi;
RUN if [ "$(which pip)" != "/env/bin/pip" ]; then exit 1; fi;
RUN pip install gunicorn flask
RUN if [ "$(which gunicorn)" != "/env/bin/gunicorn" ]; then exit 1; fi;
RUN python -c "import sys; import flask; sys.exit(0 if flask.__file__.startswith('/env') else 1)"

# Python 3.4
RUN rm -rf /env
RUN if [ "$(which python3.4)" != "/usr/bin/python3.4" ]; then exit 1; fi;
RUN virtualenv -p python3.4 /env
# All commands from this point on should use the virtualenv
RUN if [ "$(which python)" != "/env/bin/python" ]; then exit 1; fi;
RUN if [ "$(which python3)" != "/env/bin/python3" ]; then exit 1; fi;
RUN if [ "$(python --version 2>&1)" != "Python 3.4.2" ]; then exit 1; fi;
RUN if [ "$(which pip)" != "/env/bin/pip" ]; then exit 1; fi;
RUN if [ "$(which pip3)" != "/env/bin/pip3" ]; then exit 1; fi;
RUN pip install gunicorn flask
RUN if [ "$(which gunicorn)" != "/env/bin/gunicorn" ]; then exit 1; fi;
RUN python -c "import sys; import flask; sys.exit(0 if flask.__file__.startswith('/env') else 1)"

# Python 3.5
RUN rm -rf /env
RUN if [ "$(which python3.5)" != "/opt/python3.5/bin/python3.5" ]; then exit 1; fi;
RUN virtualenv -p python3.5 /env
# All commands from this point on should use the virtualenv
RUN if [ "$(which python)" != "/env/bin/python" ]; then exit 1; fi;
RUN if [ "$(which python3)" != "/env/bin/python3" ]; then exit 1; fi;
RUN if [ "$(which python3.5)" != "/env/bin/python3.5" ]; then exit 1; fi;
RUN if [ "$(python --version 2>&1)" != "Python 3.5.2" ]; then exit 1; fi;
RUN if [ "$(which pip)" != "/env/bin/pip" ]; then exit 1; fi;
RUN if [ "$(which pip3)" != "/env/bin/pip3" ]; then exit 1; fi;
RUN pip install gunicorn flask
RUN if [ "$(which gunicorn)" != "/env/bin/gunicorn" ]; then exit 1; fi;
RUN python -c "import sys; import flask; sys.exit(0 if flask.__file__.startswith('/env') else 1)"
