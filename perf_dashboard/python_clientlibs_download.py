# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import os
import sys
import time
import uuid

from google.cloud import bigquery

import bq_utils

GCLOUD_PROJECT_ENV = 'GCLOUD_PROJECT'

DATETIME_FORMAT = '%Y%m%d'

DATASET_NAME = 'python_clientlibs_download_by_week'

VENEER_TABLE_NAME = 'veneer_client_libs'
STACKDRIVER_TABLE_NAME = 'stackdriver_client_libs'
GRPC_TABLE_NAME = 'grpc_lib'
THIRD_PARTY_TABLE_NAME = 'third_party_client_libs'

TABLES = [
    VENEER_TABLE_NAME,
    GRPC_TABLE_NAME,
    STACKDRIVER_TABLE_NAME,
    THIRD_PARTY_TABLE_NAME,
]

CLIENTLIBS = {
    VENEER_TABLE_NAME: [
        'google-cloud-core',
        'google-cloud-speech',
        'google-cloud-language',
        'google-cloud-pubsub',
        'google-cloud-bigquery',
        'google-cloud-bigtable',
        'google-cloud-datastore',
        'google-cloud-spanner',
        'google-cloud-storage',
        'google-cloud-vision',
        'google-cloud-translate',
        'google-cloud-dns',
        'google-cloud-videointelligence',
    ],
    STACKDRIVER_TABLE_NAME: [
        'google-cloud-logging',
        'google-cloud-monitoring',
        'google-cloud-error_reporting',
        'google-cloud-trace',
    ],
    GRPC_TABLE_NAME: [
        'grpcio',
    ],
    THIRD_PARTY_TABLE_NAME: [
        'pandas-gbq',
    ]
}


def get_weekly_clientlibs_downloads(clientlibs_table_name, date_str):
    """Use a SQL query to collect the weekly download data of the client
    libraries.

    Args:
        clientlibs_table_name (str): Table name, which is the key in the
                                     CLIENTLIBS dict.
        date_str (str): A date string in "YYYYMMDD" format.

    Returns:
         list: rows of the query result.
    """
    client_libs = CLIENTLIBS[clientlibs_table_name]
    date_time = datetime.datetime.strptime(date_str, DATETIME_FORMAT)
    week_dates = [(date_time + datetime.timedelta(days=-i))
                      .strftime(DATETIME_FORMAT)
                  for i in range(7)]
    query = """
            SELECT
                file.project as client_library_name,
                COUNT(*) as download_count
            FROM
                `the-psf.pypi.downloads*`
            WHERE
                file.project IN UNNEST(@client_libs)
                AND
                _TABLE_SUFFIX IN UNNEST(@week_dates)
            GROUP BY client_library_name
        """
    client = bigquery.Client()
    query_parameters=[
        bigquery.ArrayQueryParameter(
            'client_libs', 'STRING', client_libs),
        bigquery.ArrayQueryParameter(
            'week_dates', 'STRING', week_dates)
    ]
    job_config = bigquery.QueryJobConfig()
    job_config.query_parameters = query_parameters
    query_job = client.query(query, job_config=job_config)

    # Wait for the job to complete and get the results
    results = [row.values() for row in query_job.result()]

    rows = [(date_time,) + row for row in results]

    return rows


def main():
    for table_name in CLIENTLIBS.keys():
        rows = get_weekly_clientlibs_downloads(
            clientlibs_table_name=table_name,
            date_str=datetime.datetime.now().strftime("%Y%m%d"))
        bq_utils.insert_rows(
            project=os.environ.get(GCLOUD_PROJECT_ENV),
            dataset_name=DATASET_NAME,
            table_name=table_name,
            rows=rows)


if __name__ == '__main__':
    main()
