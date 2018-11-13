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
import collections.abc
import functools
import io
import os
import re
import sys

import yaml

import validation_utils

# Validate characters for dockerfile image names.
#
# This roots out obvious mistakes, the full gory details are here:
# https://github.com/docker/distribution/blob/master/reference/regexp.go
IMAGE_REGEX = re.compile(r"""(?x)
    ^
    [a-zA-Z0-9]          # First char must be alphanumeric
    [a-zA-Z0-9-_./:@+]*  # Punctuation allowed after that
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
    '3': '3.6',
    '3.4': '3.4',
    '3.5': '3.5',
    '3.6': '3.6',
    '3.7': '3.7',
}

# Name of environment variable potentially set by gcloud
GAE_APPLICATION_YAML_PATH = 'GAE_APPLICATION_YAML_PATH'

# Validated application configuration
AppConfig = collections.namedtuple(
    'AppConfig',
    'base_image dockerfile_python_version entrypoint has_requirements_txt is_python_compat'
)


def get_app_config(raw_config, base_image, config_file, source_dir):
    """Read and validate the application runtime configuration.

    We validate the user input for security and better error messages.

    Consider parsing a yaml file which has a string value where we
    expected a list.  Python will happily use the string as a sequence
    of individual characters, at least for a while, leading to
    confusing results when it finally fails.

    We also try to prevent Dockerfile and Bash injection attacks.  For
    example, specifying entrypoint as "true\\nADD /etc/passwd /pwned"
    would allow the user to inject arbitrary directives into the
    Dockerfile, which is a support problem if nothing else.

    Args:
        raw_config (dict): deserialized app.yaml
        base_image (str): Docker image name to build on top of
        config_file (str): Path to user's app.yaml (might be <service>.yaml)
        source_dir (str): Directory containing user's source code

    Returns:
        AppConfig: valid configuration
    """
    # Examine app.yaml
    if not isinstance(raw_config, collections.abc.Mapping):
        raise ValueError(
            'Expected {} contents to be a Mapping type, but found type "{}"'.
            format(config_file, type(raw_config)))

    # Short circuit for python compat.
    if validation_utils.get_field_value(
        raw_config, 'runtime', str) == 'python-compat':
      return AppConfig(
          base_image=None,
          dockerfile_python_version=None,
          entrypoint=None,
          has_requirements_txt=None,
          is_python_compat=True)

    entrypoint = validation_utils.get_field_value(
        raw_config, 'entrypoint', str)
    if not PRINTABLE_REGEX.match(entrypoint):
        raise ValueError(
            'Invalid "entrypoint" value in app.yaml: {!r}'.format(entrypoint))

    # Mangle entrypoint in the same way as the Cloud SDK
    # (googlecloudsdk/third_party/appengine/api/validation.py)
    #
    # We could handle both string ("shell form") and list ("exec
    # form") but it appears that gcloud only handles string form.
    if entrypoint and not entrypoint.startswith('exec '):
        entrypoint = 'exec ' + entrypoint

    raw_runtime_config = validation_utils.get_field_value(
        raw_config, 'runtime_config', dict)
    python_version = validation_utils.get_field_value(
        raw_runtime_config, 'python_version', str)

    dockerfile_python_version = PYTHON_INTERPRETER_VERSION_MAP.get(
        python_version)
    if dockerfile_python_version is None:
        valid_versions = str(sorted(PYTHON_INTERPRETER_VERSION_MAP.keys()))
        raise ValueError(
            'Invalid "python_version" field in "runtime_config" section '
            'of app.yaml: {!r}.  Valid options are: {}'.
            format(python_version, valid_versions))

    # Examine user's files
    has_requirements_txt = os.path.isfile(
        os.path.join(source_dir, 'requirements.txt'))

    return AppConfig(
        base_image=base_image,
        dockerfile_python_version=dockerfile_python_version,
        entrypoint=entrypoint,
        has_requirements_txt=has_requirements_txt,
        is_python_compat=False)


def get_data(name):
    """Return the contents of the named data resource

    These templates are copied from the Google Cloud SDK at
    google-cloud-sdk/platform/ext-runtime/python/data
    and the two should be kept in sync.

    Args:
        name (str): Name of file, without directory

    Returns:
        str: Contents of data file
    """
    filename = os.path.join(os.path.dirname(__file__), 'data', name)
    with io.open(filename, 'r', encoding='utf8') as template_file:
        return template_file.read()


def generate_files(app_config):
    """Generate a Dockerfile and helper files for an application.

    Args:
        app_config (AppConfig): Validated configuration

    Returns:
        dict: Map of filename to desired file contents
    """
    if app_config.has_requirements_txt:
        optional_requirements_txt = get_data('Dockerfile.requirements_txt')
    else:
        optional_requirements_txt = ''

    if app_config.entrypoint:
        optional_entrypoint = get_data(
            'Dockerfile.entrypoint.template').format(
                entrypoint=app_config.entrypoint)
    else:
        optional_entrypoint = ''

    if app_config.is_python_compat:
      dockerfile = get_data('Dockerfile.python_compat')
      dockerignore = get_data('dockerignore.python_compat')
    else:
      dockerfile = ''.join([
          get_data('Dockerfile.preamble.template').format(
              base_image=app_config.base_image),
          get_data('Dockerfile.virtualenv.template').format(
              python_version=app_config.dockerfile_python_version),
          optional_requirements_txt,
          get_data('Dockerfile.install_app'),
          optional_entrypoint,
      ])
      dockerignore =  get_data('dockerignore')

    return {
        'Dockerfile': dockerfile,
        '.dockerignore': dockerignore,
    }


def generate_dockerfile_command(base_image, config_file, source_dir):
    """Write a Dockerfile and helper files for an application.

    Args:
        base_image (str): Docker image name to build on top of
        config_file (str): Path to user's app.yaml (might be <service>.yaml)
        source_dir (str): Directory container user's source code
    """
    # Read yaml file.  Does not currently support multiple services
    # with configuration filenames besides app.yaml
    with io.open(config_file, 'r', encoding='utf8') as yaml_config_file:
        raw_config = yaml.safe_load(yaml_config_file)

    # Determine complete configuration
    app_config = get_app_config(raw_config, base_image, config_file,
                                  source_dir)

    # Generate list of filenames and their textual contents
    files = generate_files(app_config)

    # Write files
    for filename, contents in files.items():
        full_filename = os.path.join(source_dir, filename)
        with io.open(full_filename, 'w', encoding='utf8') as outfile:
            outfile.write(contents)


def parse_args(argv):
    """Parse and validate command line flags"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--base-image',
        type=functools.partial(
            validation_utils.validate_arg_regex, flag_regex=IMAGE_REGEX),
        default='gcr.io/google-appengine/python:latest',
        help='Name of Docker image to use as base')
    # In some cases, gcloud sets an environment variable to indicate
    # the location of the application configuration file, rather than
    # using the --config flag.  The order of precedence from highest
    # to lowest is:
    #
    # 1) --config flag
    # 2) $GAE_APPLICATION_YAML_PATH environment variable
    # 3) a file named "app.yaml" in the current working directory
    parser.add_argument(
        '--config',
        type=functools.partial(
            validation_utils.validate_arg_regex, flag_regex=PRINTABLE_REGEX),
        default=(os.environ.get(GAE_APPLICATION_YAML_PATH) or 'app.yaml'),
        help='Path to application configuration file'
        )
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
    generate_dockerfile_command(args.base_image, args.config, args.source_dir)


if __name__ == '__main__':
    main()
