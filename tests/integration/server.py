#!/usr/bin/python

from google.cloud import logging as gcloud_logging
from google.cloud import monitoring as gcloud_monitoring
from google.cloud.monitoring import MetricKind, ValueType
from google.cloud.exceptions import Forbidden as ForbiddenException
from google.cloud.exceptions import NotFound as NotFoundException
from oauth2client.client import GoogleCredentials

import logging
import time

from flask import Flask, request, jsonify
app = Flask(__name__)


@app.route('/')
def hello_world():
	return 'Hello World!'


@app.route('/logging', methods=['POST'])
def _logging():
	request_data = request.get_json()
	if request_data is None:
		raise ErrorResponse("Unable to parse request JSON: did you set the Content-type header?")
	log_name = request_data.get('log_name', '')
	if log_name == '':
		raise ErrorResponse("please provide log name")
	token = request_data.get('token', '')
	if token == '':
		raise ErrorResponse("please provide token name")

	_log("log name is {0}, token is {1}".format(log_name, token))
	_log(token, log_name)

	return ('OK', 200)


# TODO (nkubala): just as a note, currently the client logging API is broken
def _log(token, log_name='stdout'):
	# TODO (nkubala): write token to 'log_name' log, instead of stdout
	# is this possible in non-standard (flex)???

	try:
		client = gcloud_logging.Client(credentials=GoogleCredentials.get_application_default())
		gcloud_logger = client.logger(log_name)
		gcloud_logger.log_text(token)
	except Exception as e:
		logging.error("error while writing logs")
		raise ErrorResponse("error while writing logs: {0}".format(e))

	# logging.info(token)
	print token


@app.route('/monitoring', methods=['POST'])
def _monitoring():
	request_data = request.get_json()
	if request_data is None:
		raise ErrorResponse("Unable to parse request JSON: did you set the Content-type header?")
	name = request_data.get('name', '')
	if name == '':
		raise ErrorResponse("please provide metric name")
	token = request_data.get('token', '')
	if token == '':
		raise ErrorResponse("please provide metric token")

	try:
		client = gcloud_monitoring.Client(credentials=GoogleCredentials.get_application_default())

		try:
			descriptor = client.fetch_metric_descriptor(name)
			if descriptor is None:
				_create_descriptor(name, client)
		except (ForbiddenException, NotFoundException) as ignored:
			# print "forbidden"
			_create_descriptor(name, client)

		metric = client.metric(name, {})
		resource = client.resource('global', labels={})
		client.write_point(metric, resource, token)
	except Exception as e:
		logging.error(e)
		raise ErrorResponse("error while writing custom metric: {0}".format(e))
	# finally:
	# 	if descriptor is not None:
	# 		descriptor.delete()

	return ('OK', 200)


def _create_descriptor(name, client):
	logging.info("no descriptor found with name {0}: creating".format(name))
	descriptor = client.metric_descriptor(
		name,
		metric_kind=MetricKind.GAUGE,
		value_type=ValueType.INT64,
		description="this is a test metric"
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
