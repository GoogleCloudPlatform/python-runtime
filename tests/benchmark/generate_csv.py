# Copyright 2016 Google Inc. All Rights Reserved.
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


import argparse
import csv
import json
import os
import sys


def generate_csv(filename, tag):
    """Extract function name, time used and memory usage from the metadata and write to the output CSV file.

    Args:
        filename (str): Filename of the performance json file to read
        tag (str): Tag of the docker container
    """
    with open(filename) as input:
        data = json.load(input)
    benchmarks = data["benchmarks"]
    runtime_version = os.path.basename(filename).split(".json")[0]

    # Write data to CSV file
    with open("{}.csv".format(os.path.splitext(filename)[0]), "wb") as output:
        csv_writer = csv.writer(output, delimiter=',')
        for benchmark in benchmarks:
            try:
                # Get the function name
                func_name = benchmark["metadata"]["name"]
                # Get the time used for this function, convert to millisecond
                time_used = float(benchmark["runs"][0]["values"][0]) * 1000
                # Get the memory usage, convert to MB
                mem_usage = float(benchmark["metadata"]["mem_max_rss"]) / float(1<<20)
                line = [tag, runtime_version, func_name, time_used, mem_usage]
                # Write to CSV file
                csv_writer.writerow(line)
            except KeyError:
                # Skip the benchmark result if it does not contain the fields we want
                pass


def get_averages(filename, tag):
    """Calculate the averages of time_used and memory_usage and append to CSV file.

    Args:
        filename (str): Filename of the performance json file to read
        tag (str): Tag of the docker container
    """
    with open("{}.csv".format(os.path.splitext(filename)[0]), "rb") as input:
        lines = input.readlines()
        # Get the two columns of times_used and mem_usage
        rows_of_data = [map(float, line.split(',')[-2:]) for line in lines]
        # Calculate the sum of the two columns
        col_sums = map(sum, zip(*rows_of_data))
        # Calculate the average of the two columns by using the sum divided by the total number of lines
        averages = [col_sum / len(lines) for col_sum in col_sums]

    # Get the runtime version from filename
    runtime_version = os.path.basename(filename).split(".json")[0]

    # Write the averages to CSV file in appending mode
    with open("{}/averages.csv".format(tag), "a+") as output:
        try:
            csv_writer = csv.writer(output, delimiter=',')
            csv_writer.writerow([tag, runtime_version] + averages)
        except IOError:
            print "Could not write averages to file."


def parse_args(argv):
    """Parse and validate command line flags"""
    parser = argparse.ArgumentParser(
        description='Read the python performance json file and extract data to genarate CSV file.'
    )
    parser.add_argument(
        '--filename',
        help='Filename of the performance json file to read'
    )
    parser.add_argument(
        '--tag',
        help='Tag of the docker container'
    )
    args = parser.parse_args(argv[1:])
    return args


def main():
    args = parse_args(sys.argv)
    generate_csv(args.filename, args.tag)
    get_averages(args.filename, args.tag)


if __name__ == '__main__':
    main()
