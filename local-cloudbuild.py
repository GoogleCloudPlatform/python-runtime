#!/usr/bin/env python

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

"""Emulate the Google Container Builder locally.

The input is a cloudbuild.yaml file locally, which is processed using
a locally installed Docker daemon.  The output images are not pushed
to the Google Container Registry.  Not all functionality is supported.

See https://cloud.google.com/container-builder/docs/api/build-steps
for more information.
"""

import argparse
import getpass
import os
import shutil
import subprocess
import sys
import tempfile

import yaml


class CloudBuildError(Exception):
    """Syntax error in cloudbuild.yaml or other user error"""
    pass


def run_steps(cloudbuild, host_workspace):
    """Run the steps listed in a cloudbuild.yaml file.

    Args:
        cloudbuild (dict): The decoded contents of a cloudbuild.yaml
        host_workspace (str): Scratch directory

    Raises:
        CloudBuildError if the yaml contents are invalid
    """
    steps = cloudbuild.get_field_value('steps', {})
    if not steps:
        raise CloudBuildError('No steps defined in cloudbuild.yaml')

    for step in steps:
        run_one_step(step, host_workspace)


def run_one_step(step, host_workspace):
    """Run a single step listed in a cloudbuild.yaml file.

    Args:
        step (dict): A single step to perform
        host_workspace (str): Scratch directory
    """
    name = get_field_value(step, 'name', str)
    dir_ = get_field_value(step, 'dir', list)
    env = get_field_value(step, 'env', list)
    args = get_field_value(step, 'args', list)
    run_docker(name, dir_, env, args, host_workspace)


def get_field_value(container, field_name, field_type):
    """Fetch a field from a container with typechecking and default values.

    If the field is not present, a instance of `field_type` is
    constructed with no arguments and used as the default value.

    Args:
        container (dict): Object decoded from yaml
        field_name (str): Field that should be present in `container`
        field_type (type): Expected type for field value

    Returns:
        (any) fetched or default value of field

    Raises:
        CloudBuildError if field value is present but is the wrong type.
    """
    value = container.get(field_name)
    if value is None:
        return field_type()
    if not isinstance(value, field_type):
        raise CloudBuildError(
            'Expected "%d" to be of type "%d", but found "%d"',
            field_name, field_type, type(value))
    return value


def run_docker(name, dir_, env_args, args, host_workspace):
    """Construct and execute a single 'docker run' command"""
    workdir = '/workspace'
    if dir_:
        workdir = os.path.join(workdir, dir_)

    env_pairs = []
    for env_arg in env_args:
        env_pairs.append('--env', env_arg)

    process_args = [
        'docker',
        'run',
        '--volume',
        '/var/run/docker.sock:/var/run/docker.sock',
        '--volume',
        '/root/.docker:/root/.docker',
        '--volume',
        '%s:/workspace' % host_workspace,
        '--workdir',
        workdir,
    ] + env_args + [name] + args

    print('Executing ' + ' '.join(process_args))
    subprocess.check_call(process_args)


def main(argv):
    """Main entrypoint for cli"""
    parser = argparse.ArgumentParser(
        description='Process cloudbuild.yaml locally to build Docker images')
    parser.add_argument(
        'cloudbuild', type=str, help='Path to cloudbuild.yaml input file')
    parser.add_argument(
        '--keep_workspace',
        type=bool,
        default=False,
        help='Retain workspace directory after building')
    args = parser.parse_args(argv[1:])

    # Load and parse cloudbuild.yaml
    with open(args.cloudbuild, 'rb') as infile:
        cloudbuild = yaml.safe_load(infile)

    host_workspace_parent = tempfile.mkdtemp(prefix='local-cloudbuild_')
    host_workspace = os.path.join(host_workspace_parent, 'workspace')
    try:
        # Prepare workspace
        print('Running cloudbuild locally.  Host workspace directory is %s' %
              host_workspace)
        shutil.copytree('.', host_workspace, symlinks=True)

        # Execute a series of 'docker run' commands locally
        run_steps(cloudbuild, host_workspace)
    finally:
        if not args.keep_workspace:
            shutil.rmtree(host_workspace_parent, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
