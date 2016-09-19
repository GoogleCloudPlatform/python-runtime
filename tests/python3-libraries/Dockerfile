FROM google/python

RUN virtualenv -p /opt/python3.5/bin/python3.5 /env
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH
ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
