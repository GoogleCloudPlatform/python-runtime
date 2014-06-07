FROM google/python

WORKDIR /app
ONBUILD ADD . /app
ONBUILD RUN virtualenv /env
ONBUILD RUN [ -f /app/requirements.txt ] && /env/bin/pip install -r /app/requirements.txt || true

EXPOSE 8080
CMD []
ENTRYPOINT ["/env/bin/python", "main.py"]
