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

from collections import defaultdict

GCLOUD_PROJECT_ENV = 'GCLOUD_PROJECT'
DATETIME_FORMAT = '%Y%m%d'
DATASET_NAME = 'stackoverflow'
TABLE_NAME = 'tag_count_timestamp'


def wait_for_job(job):
    """Wait for the query job to complete."""
    while True:
        job.reload()  # Refreshes the state via a GET request.
        if job.state == 'DONE':
            if job.error_result:
                raise RuntimeError(job.errors)
            return
        time.sleep(1)


def get_stackoverflow_tags_count():
    # Get all the tags contains python and cloud key words
    query = """
            SELECT
                SPLIT(tags, '|') tags
            FROM
                `bigquery-public-data.stackoverflow.posts_questions`
            WHERE
                tags LIKE '%python%'
            AND (tags LIKE '%google-cloud-platform%' OR tags LIKE '%gcp%')
        """

    client = bigquery.Client()
    query_job = client.run_async_query(str(uuid.uuid4()), query)
    query_job.use_legacy_sql = False

    # Start the query job and wait it to complete
    query_job.begin()
    wait_for_job(query_job)

    # Fetch the results
    result = query_job.query_results().fetch_data()
    result_list = [item for item in result]

    # In case the result_list contains the metadata like total_rows, the
    # actual rows will be the first element of the result_list.
    if len(result_list) > 0 and isinstance(result_list[0], list):
        result_list = result_list[0]

    rows = [row[0] for row in result_list]

    return rows


def count_unique_tags(data):
    tag_count = defaultdict(int)

    for row in data:
        for tag in row:
            tag_count[tag] += 1

    # Add current timestamp to the rows
    date_str = datetime.datetime.now().strftime(DATETIME_FORMAT)
    date_time = datetime.datetime.strptime(date_str, DATETIME_FORMAT)

    time_tag_count = [(date_time,) + item for item in tag_count.items()]

    return time_tag_count


def insert_rows(dataset_name, table_name, rows):
    project = os.environ.get(GCLOUD_PROJECT_ENV)
    client = bigquery.Client(project=project)
    dataset = client.dataset(dataset_name)
    table = bigquery.Table(table_name, dataset)
    table.reload()
    table.insert_data(rows)


def main():
    rows = get_stackoverflow_tags_count()
    tag_count = count_unique_tags(rows)
    insert_rows(DATASET_NAME, TABLE_NAME, tag_count)


if __name__ == '__main__':
    main()
