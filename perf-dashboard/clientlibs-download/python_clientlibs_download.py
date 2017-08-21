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
import time
import uuid

from google.cloud import bigquery

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
    ],
    GRPC_TABLE_NAME: [
        'grpcio',
    ],
    THIRD_PARTY_TABLE_NAME: [
        'pandas-gbq',
    ]
}


def wait_for_job(job):
    """Wait for the query job to complete."""
    while True:
        job.reload()  # Refreshes the state via a GET request.
        if job.state == 'DONE':
            if job.error_result:
                raise RuntimeError(job.errors)
            return
        time.sleep(1)


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
    query_job = client.run_async_query(
        str(uuid.uuid4()),
        query,
        query_parameters=(
            bigquery.ArrayQueryParameter(
                'client_libs', 'STRING',
                client_libs),
            bigquery.ArrayQueryParameter(
                'week_dates', 'STRING',
                week_dates)
        ))
    query_job.use_legacy_sql = False

    # Start the query job and wait it to complete
    query_job.begin()
    wait_for_job(query_job)

    # Fetch the results
    result = query_job.result().fetch_data()
    result_list = [item for item in result]

    # In case the result_list contains the metadata like total_rows, the
    # actual rows will be the first element of the result_list.
    if len(result_list) > 0 and isinstance(result_list[0], list):
        result_list = result_list[0]

    rows = [(date_time,) + row for row in result_list]
    print(rows)

    return rows


def insert_rows(dataset_name, table_name, rows):
    """Insert rows to a bigquery table.

    Args:
        dataset_name (str): Name of the dataset that holds the tables.
        table_name (str): Name of the bigquery table.
        rows (list): The rows that going to be inserted into the table.

    Returns:
        list: Empty if inserted successfully, else the errors when inserting
              each row.
    """
    project = os.environ.get(GCLOUD_PROJECT_ENV)
    client = bigquery.Client(project=project)
    dataset = client.dataset(dataset_name)
    table = bigquery.Table(name=table_name, dataset=dataset)
    table.reload()
    error = table.insert_data(rows)
    return error


def main():
    for table_name in CLIENTLIBS.keys():
        rows = get_weekly_clientlibs_downloads(
            clientlibs_table_name=table_name,
            date_str=datetime.datetime.now().strftime("%Y%m%d"))
        insert_rows(
            dataset_name=DATASET_NAME,
            table_name=table_name,
            rows=rows)


if __name__ == '__main__':
    main()
