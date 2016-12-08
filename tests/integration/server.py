#!/usr/bin/python

# Copyright 2016 Google Inc. All rights reserved.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import time

from google.cloud import logging as gcloud_logging
from google.cloud import monitoring as gcloud_monitoring
from google.cloud.monitoring import MetricKind, ValueType
from google.cloud.exceptions import Forbidden as ForbiddenException
from google.cloud.exceptions import NotFound as NotFoundException

from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/logging', methods=['POST'])
def _logging():
    request_data = request.get_json()
    if request_data is None:
        raise ErrorResponse('Unable to parse request JSON: '
                            'did you set the Content-type header?')
    log_name = request_data.get('log_name', '')
    if log_name == '':
        raise ErrorResponse('Please provide log name')
    token = request_data.get('token', '')
    if token == '':
        raise ErrorResponse('Please provide token name')

    _log("log name is {0}, token is {1}".format(log_name, token))
    _log(token, log_name)

    return 'OK', 200


# TODO (nkubala): just as a note, currently the client logging API is broken
def _log(token, log_name='stdout'):
    # TODO (nkubala): write token to 'log_name' log, instead of stdout
    # is this possible in non-standard (flex)???

    try:
        client = gcloud_logging.Client()
        gcloud_logger = client.logger(log_name)
        gcloud_logger.log_text(token)
    except Exception as e:
        logging.error('Error while writing logs: {0}'.format(e))
        raise ErrorResponse('Error while writing logs: {0}'.format(e))

    # logging.info(token)
    print token


@app.route('/monitoring', methods=['POST'])
def _monitoring():
    request_data = request.get_json()
    if request_data is None:
        raise ErrorResponse('Unable to parse request JSON: '
                            'did you set the Content-type header?')
    name = request_data.get('name', '')
    if name == '':
        raise ErrorResponse('Please provide metric name')
    token = request_data.get('token', '')
    if token == '':
        raise ErrorResponse('Please provide metric token')

    try:
        client = gcloud_monitoring.Client()

        try:
            descriptor = client.fetch_metric_descriptor(name)
            if descriptor is None:
                _create_descriptor(name, client)
        except (ForbiddenException, NotFoundException) as ignored:
            _create_descriptor(name, client)

        metric = client.metric(name, {})
        resource = client.resource('global', labels={})
        client.write_point(metric, resource, token)
    except Exception as e:
        logging.error('Error while writing custom metric: {0}'.format(e))
        raise ErrorResponse('Error while writing custom metric: {0}'.format(e))

    return 'OK', 200


def _create_descriptor(name, client):
    logging.info('No descriptor found with name {0}: Creating...'.format(name))
    descriptor = client.metric_descriptor(
        name,
        metric_kind=MetricKind.GAUGE,
        value_type=ValueType.INT64,
        description='Test Metric'
        )
    descriptor.create()
    time.sleep(5)


@app.route('/exception', methods=['POST'])
def _exception():
    return ('', 204)


@app.route('/trace', methods=['POST'])
def _trace():
    return ('', 204)


class ErrorResponse(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(ErrorResponse)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
