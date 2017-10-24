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

import bq_utils

GCLOUD_PROJECT_ENV = 'GCLOUD_PROJECT'
DATASET_NAME = 'stackoverflow'
TAG_COUNT_TABLE_NAME = 'tag_count_timestamp'
UNANSWERED_POSTS_TABLE_NAME = 'unanswered_posts'


def get_stackoverflow_tags_count():
    """Get all the tags contains python and cloud key words"""
    query = """
            SELECT
                SPLIT(tags, '|') tags
            FROM
                `bigquery-public-data.stackoverflow.posts_questions`
            WHERE
                tags LIKE '%python%'
            AND (tags LIKE '%google-cloud-platform%' OR tags LIKE '%gcp%')
        """

    results = bq_utils.execute_query(query)

    rows = [row[0] for row in results]

    return rows


def get_posts_list_unanswered():
    # Get the list of posts that are unanswered
    query = """
            SELECT
                id, title, tags
            FROM
                `bigquery-public-data.stackoverflow.posts_questions`
            WHERE
                tags LIKE '%python%'
            AND (tags LIKE '%google-cloud-platform%' OR tags LIKE '%gcp%')
            AND accepted_answer_id is NULL
            AND answer_count = 0;
        """

    results = bq_utils.execute_query(query)

    # Add current timestamp to the rows
    date_time = datetime.datetime.now()
    rows = [(date_time,) + row for row in results]

    return rows


def count_unique_tags(data):
    flattened_tag_list = [tag for tag_list in data for tag in tag_list]
    tag_count = Counter(flattened_tag_list)

    # Add current timestamp to the rows
    date_time = datetime.datetime.now()
    time_tag_count = [(date_time,) + item for item in tag_count.items()]

    return time_tag_count


def main():
    project = os.environ.get(GCLOUD_PROJECT_ENV)

    # Get the posts count for each tag
    rows = get_stackoverflow_tags_count()
    tag_count = count_unique_tags(rows)
    bq_utils.insert_rows(
        project, DATASET_NAME, TAG_COUNT_TABLE_NAME, tag_count)

    # Get the list of unanswered posts
    unanswered_posts = get_posts_list_unanswered()
    bq_utils.insert_rows(
        project, DATASET_NAME, UNANSWERED_POSTS_TABLE_NAME, unanswered_posts)


if __name__ == '__main__':
    main()
