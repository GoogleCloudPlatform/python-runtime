#!/usr/bin/env python3

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

"""Generate a Dockerfile and helper files for a Python application."""

import argparse
import collections
import functools
import io
import os
import re
import sys

import yaml

import validation_utils


# Validate characters for dockerfile image names
# https://github.com/docker/docker/blob/master/api/names.go
IMAGE_REGEX = re.compile(r"""(?x)
    ^
    [a-zA-Z0-9]       # First char must be alphanumeric
    [-a-zA-Z0-9_./]*  # Punctuation allowed after that
    (
        :                 # At most one colon allowed
        [-a-zA-Z0-9_./]+  # Colon must be followed by other chars
    )?
    $
""")

# `entrypoint` is specified as free-form text parsed as a unix shell
# command line, which limits the sanity checking possible.  We
# disallow newlines and control characters which would break the
# Dockerfile format.
PRINTABLE_REGEX = re.compile(r"""^[^\x00-\x1f]*$""")

# Map from app.yaml "python_version" to {python_version} in Dockerfile
PYTHON_INTERPRETER_VERSION_MAP = {
    '': '',  # == 2.7
    '2': '',  # == 2.7
    '3': '3.5',
    '3.4': '3.4',
    '3.5': '3.5',
    '3.6': '3.6',
}

# File templates.
# Designed to exactly match the current output of 'gcloud app gen-config'
DOCKERFILE_TEMPLATE = """\
FROM {base_image}
LABEL python_version=python{dockerfile_python_version}
RUN virtualenv --no-download /env -p python{dockerfile_python_version}

# Set virtualenv environment variables. This is equivalent to running
# source /env/bin/activate
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH
{optional_requirements_txt}ADD . /app/
{optional_entrypoint}"""

DOCKERFILE_REQUIREMENTS_TXT = """\
ADD requirements.txt /app/
RUN pip install -r requirements.txt
"""

DOCKERFILE_ENTRYPOINT_TEMPLATE = """\
CMD {entrypoint}
"""

DOCKERIGNORE = """\
# Copyright 2015 Google Inc. All Rights Reserved.
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

.dockerignore
Dockerfile
.git
.hg
.svn
"""

# Validated application configuration
AppConfig = collections.namedtuple(
    'AppConfig',
    'base_image dockerfile_python_version entrypoint has_requirements_txt'
)


def get_app_config(raw_config, args):
    """Read and validate the application runtime configuration.

    Args:
        raw_config (dict): deserialized app.yaml
        args (argparse.Namespace): ccommand line flags

    Returns:
        AppConfig: valid configuration
    """
    # Examine app.yaml
    if not isinstance(raw_config, dict):
        raise ValueError(
            'Expected {} contents to be of type "dict", but found type "{}"'.
            format(args.config, type(raw_config)))

    entrypoint = validation_utils.get_field_value(raw_config, 'entrypoint', str)
    if not PRINTABLE_REGEX.match(entrypoint):
        raise ValueError('Invalid character in "entrypoint" field of app.yaml')
    raw_runtime_config = validation_utils.get_field_value(raw_config, 'runtime_config', dict)
    python_version = validation_utils.get_field_value(raw_runtime_config, 'python_version', str)
    dockerfile_python_version = PYTHON_INTERPRETER_VERSION_MAP.get(
        python_version)
    if dockerfile_python_version is None:
        valid_versions = str(sorted(PYTHON_INTERPRETER_VERSION_MAP.keys()))
        msg = ('Invalid "python_version" field in "runtime_config" section '
               'of app.yaml.  Valid options are:\n{}').format(valid_versions)
        raise ValueError(msg)

    # Examine user's files
    has_requirements_txt = os.path.isfile(
        os.path.join(args.source_dir, 'requirements.txt'))

    # Compute base image name and Dockerfile contents
    base_image = args.base_image

    return AppConfig(
        base_image=base_image,
        dockerfile_python_version=dockerfile_python_version,
        entrypoint=entrypoint,
        has_requirements_txt=has_requirements_txt)


def generate_files(app_config):
    """Generate a Dockerfile and helper files for an application.

    Args:
        app_config (AppConfig): Validated configuration

    Returns:
        dict: Map of filename to desired file contents
    """
    if app_config.has_requirements_txt:
        optional_requirements_txt = DOCKERFILE_REQUIREMENTS_TXT
    else:
        optional_requirements_txt = ''

    if app_config.entrypoint:
        # Mangle entrypoint in the same way as the Cloud SDK
        # (googlecloudsdk/third_party/appengine/api/validation.py)
        #
        # We could handle both string ("shell form") and list ("exec
        # form") but it appears that gcloud only handles string form.
        entrypoint = app_config.entrypoint
        if entrypoint and not entrypoint.startswith('exec '):
            entrypoint = 'exec ' + entrypoint
        optional_entrypoint = DOCKERFILE_ENTRYPOINT_TEMPLATE.format(
            entrypoint=entrypoint)
    else:
        optional_entrypoint = ''

    dockerfile = DOCKERFILE_TEMPLATE.format(
        base_image=app_config.base_image,
        dockerfile_python_version=app_config.dockerfile_python_version,
        optional_requirements_txt=optional_requirements_txt,
        optional_entrypoint=optional_entrypoint)

    return {
        'Dockerfile': dockerfile,
        '.dockerignore': DOCKERIGNORE,
    }


def gen_dockerfile(args):
    """Write a Dockerfile and helper files for an application.

    Args:
        args (argparse.Namespace): ccommand line flags
    """
    # Read yaml file.  Does not currently support multiple services
    # with configuration filenames besides app.yaml
    with io.open(args.config, 'r', encoding='utf8') as yaml_config_file:
        raw_config = yaml.load(yaml_config_file)

    # Determine configuration
    app_config = get_app_config(raw_config, args)

    # Generate list of filenames and their textual contents
    files = generate_files(app_config)

    # Write files
    for filename, contents in files.items():
        full_filename = os.path.join(args.source_dir, filename)
        with io.open(full_filename, 'w', encoding='utf8') as outfile:
            outfile.write(contents)


def parse_args(argv):
    """Parse and validate command line flags"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config',
        type=functools.partial(
            validation_utils.validate_arg_regex, flag_regex=PRINTABLE_REGEX),
        default='app.yaml',
        help='Path to application configuration file'
        )
    parser.add_argument(
        '--base-image',
        type=functools.partial(
            validation_utils.validate_arg_regex, flag_regex=IMAGE_REGEX),
        default='gcr.io/google-appengine/python:latest',
        help='Name of Docker image to use as base')
    parser.add_argument(
        '--source-dir',
        type=functools.partial(
            validation_utils.validate_arg_regex, flag_regex=PRINTABLE_REGEX),
        default='.',
        help=('Application source and output directory'))
    args = parser.parse_args(argv[1:])
    return args


def main():
    args = parse_args(sys.argv)
    gen_dockerfile(args)


if __name__ == '__main__':
    main()
