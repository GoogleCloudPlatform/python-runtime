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

from datetime import datetime
from google.cloud import bigquery

DATASET_NAME = 'python_clientlibs_download_by_week'
VENEER_TABLE_NAME = 'veneer_client_libs'
STACKDRIVER_TABLE_NAME = 'stackdriver_client_libs'
GRPC_TABLE_NAME = 'grpc_lib'
TABLES = [VENEER_TABLE_NAME, GRPC_TABLE_NAME, STACKDRIVER_TABLE_NAME]

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
}


def get_weekly_clientlibs_downloads(client_library, date_str):
    """Use a SQL query to collect the weekly download data of the client
    libraries.

    Args:
        client_library (str): key of the client_library in the CLIENTLIBS dict.
        date_str (str): A date string in "YYYYMMDD" format.

    Returns:
         tuple: rows of the query result.
    """
    timestamp = 'TIMESTAMP("{}")'.format(date_str)
    fields = [
        '{} as timestamp'.format(timestamp),
        'file.project as client_library_name',
        'COUNT(*) as download_count']
    client_libs = CLIENTLIBS[client_library]
    query = """
    SELECT
      %(fields)s
    FROM
      TABLE_DATE_RANGE(%(table_name)s,
                       DATE_ADD(%(timestamp)s, -6, "day"),
                       %(timestamp)s)
    WHERE file.project IN %(client_libs)s
    GROUP BY timestamp, client_library_name
    """ % {
        'fields': ', '.join(fields),
        'table_name': '[the-psf:pypi.downloads]',
        'client_libs': tuple(client_libs),
        'timestamp': timestamp,
    }
    print query
    client = bigquery.Client()
    query_job = client.run_sync_query(query)
    query_job.run()

    return query_job.rows


def insert_rows(dataset_name, table_name, rows):
    """Insert rows to a bigquery table.

    Args:
        dataset_name (str): Name of the dataset that holds the tables.
        table_name (str): Name of the bigquery table.
        rows (tuple): The rows that going to be inserted into the table.

    Returns:
        list: Empty if inserted successfully, else the errors when inserting
              each row.
    """
    client = bigquery.Client()
    dataset = client.dataset(dataset_name)
    table = bigquery.Table(name=table_name, dataset=dataset)
    table.reload()
    error = table.insert_data(rows)
    return error


def main():
    for key in CLIENTLIBS.keys():
        rows = get_weekly_clientlibs_downloads(
            client_library=key,
            date_str=datetime.now().strftime("%Y%m%d"))
        insert_rows(
            dataset_name=DATASET_NAME,
            table_name=key,
            rows=rows)


if __name__ == '__main__':
    main()
