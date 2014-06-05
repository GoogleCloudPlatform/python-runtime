FROM google/python

WORKDIR /app
ONBUILD RUN virtualenv /env
ONBUILD ADD requirements.txt /app/requirements.txt
ONBUILD RUN /env/bin/pip install -r /app/requirements.txt
ONBUILD ADD . /app

EXPOSE 8080
CMD []
ENTRYPOINT ["/env/bin/python", "main.py"]
