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

"""Common util methods for processing data in BigQuery."""

import uuid

from google.cloud import bigquery


def insert_rows(project, dataset_name, table_name, rows):
    """Insert rows to bigquery table."""
    client = bigquery.Client(project=project)
    dataset = client.dataset(dataset_name)
    table = bigquery.Table(table_name, dataset)
    table.reload()
    table.insert_data(rows)


def execute_query(query):
    """Execute query and return the query results."""
    client = bigquery.Client()
    query_job = client.run_async_query(str(uuid.uuid4()), query)
    query_job.use_legacy_sql = False

    # Start the query job and wait it to complete
    query_job.begin()
    query_job.result()

    # Get the results
    destination_table = query_job.destination
    destination_table.reload()
    results = destination_table.fetch_data()

    return results
