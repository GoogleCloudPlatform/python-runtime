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

"""A script to collect the number of StackOverflow posts related to
Python and Google Cloud Platform."""

import datetime
import os
import sys
import time
import uuid

from collections import Counter

from google.cloud import bigquery

sys.path.insert(0, os.path.abspath(__file__+"/../../.."))
from perf_dashboard import bq_utils

GCLOUD_PROJECT_ENV = 'GCLOUD_PROJECT'
DATASET_NAME = 'stackoverflow'
TABLE_NAME = 'tag_count_timestamp'


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
    query_job.result()

    # Get the results
    destination_table = query_job.destination
    destination_table.reload()
    results = destination_table.fetch_data()

    rows = [row[0] for row in results]

    return rows


def count_unique_tags(data):
    flattened_tag_list = [tag for tag_list in data for tag in tag_list]
    tag_count = Counter(flattened_tag_list)

    # Add current timestamp to the rows
    date_time = datetime.datetime.now()
    time_tag_count = [(date_time,) + item for item in tag_count.items()]

    return time_tag_count


def main():
    rows = get_stackoverflow_tags_count()
    tag_count = count_unique_tags(rows)
    project = os.environ.get(GCLOUD_PROJECT_ENV)
    bq_utils.insert_rows(project, DATASET_NAME, TABLE_NAME, tag_count)


if __name__ == '__main__':
    main()
