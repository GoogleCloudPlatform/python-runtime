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

"""Emulate the Google Container Builder locally.

The input is a local cloudbuild.yaml file.  This is translated into a
series of commands for the locally installed Docker daemon.  These
commands are output as a shell script and optionally executed.

The output images are not pushed to the Google Container Registry.
Not all cloudbuild.yaml functionality is supported.  In particular,
substitutions are a simplified subset that doesn't include all the
corner cases and error conditions.

See https://cloud.google.com/container-builder/docs/api/build-steps
for more information.
"""

import argparse
import collections
import collections.abc
import functools
import io
import os
import re
import shlex
import subprocess
import sys

import yaml


# Exclude non-printable control characters (including newlines)
PRINTABLE_REGEX = re.compile(r"""^[^\x00-\x1f]*$""")

# Container Builder substitutions
# https://cloud.google.com/container-builder/docs/api/build-requests#substitutions
SUBSTITUTION_REGEX = re.compile(r"""(?x)
    (?<!\\)                # Don't match if backslash before dollar sign
    \$                     # Dollar sign
    (
        [A-Z_][A-Z0-9_]*   # Variable name, no curly brackets
        |
        {[A-Z_][A-Z0-9_]*} # Variable name, with curly brackets
    )
""")

# For easier development, we allow redefining builtins like
# --substitutions=PROJECT_ID=foo even though gcloud doesn't.
KEY_VALUE_REGEX = re.compile(r'^([A-Z_][A-Z0-9_]*)=(.*)$')

# Default builtin substitutions
DEFAULT_SUBSTITUTIONS = {
    'BRANCH_NAME': '',
    'BUILD_ID': 'abcdef12-3456-7890-abcd-ef0123456789',
    'COMMIT_SHA': '',
    'PROJECT_ID': 'dummy-project-id',
    'REPO_NAME': '',
    'REVISION_ID': '',
    'TAG_NAME': '',
}

# File template
BUILD_SCRIPT_HEADER = """\
#!/bin/bash
# This is a generated file.  Do not edit.

set -euo pipefail

SOURCE_DIR=.

# Setup staging directory
HOST_WORKSPACE=$(mktemp -d)
function cleanup {
    if [ "${HOST_WORKSPACE}" != '/' -a -d "${HOST_WORKSPACE}" ]; then
        rm -rf "${HOST_WORKSPACE}"
    fi
}
trap cleanup EXIT

# Copy source to staging directory
echo "Copying source to staging directory ${HOST_WORKSPACE}"
rsync -avzq --exclude=.git "${SOURCE_DIR}" "${HOST_WORKSPACE}"

# Build commands
"""

BUILD_SCRIPT_FOOTER = """\
# End of build commands

echo "Build completed successfully"
"""


# Validated cloudbuild recipe + flags
CloudBuild = collections.namedtuple('CloudBuild', 'output_script run steps substitutions')

# Single validated step in a cloudbuild recipe
Step = collections.namedtuple('Step', 'args dir_ env name')


def sub_and_quote(s, substitutions):
    """Return a shell-escaped, variable substituted, version of the string s."""

    def sub(match):
        """Perform a single substitution."""
        variable_name = match.group(1)
        if variable_name[0] == '{':
            # Strip curly brackets
            variable_name = variable_name[1:-1]
        if variable_name not in substitutions:
            if variable_name.startswith('_'):
                # User variables must be set
                raise ValueError(
                    'Variable "{}" used without being defined.  Try adding '
                    'it to the --substitutions flag'.format(
                        variable_name))
            else:
                # Builtin variables are silently turned into empty strings
                value = ''
        else:
            value = substitutions.get(variable_name)
        return value

    substituted_s = re.sub(SUBSTITUTION_REGEX, sub, s)
    quoted_s = shlex.quote(substituted_s)
    return quoted_s

def get_field_value(container, field_name, field_type):
    """Fetch a field from a container with typechecking and default values.

    The field value is coerced to the desired type.  If the field is
    not present, a instance of `field_type` is constructed with no
    arguments and used as the default value.

    Args:
        container (dict): Object decoded from yaml
        field_name (str): Field that should be present in `container`
        field_type (type): Expected type for field value

    Returns:
        Any: Fetched or default value of field

    Raises:
        ValueError: if field value cannot be converted to the desired type
    """
    try:
        value = container[field_name]
    except (IndexError, KeyError):
        return field_type()

    msg = 'Expected "{}" field to be of type "{}", but found type "{}"'
    if not isinstance(value, field_type):
        # list('some string') is a successful type cast as far as Python
        # is concerned, but doesn't exactly produce the results we want.
        # We have a whitelist of conversions we will attempt.
        whitelist = (
            (float, str),
            (int, str),
            (str, float),
            (str, int),
            (int, float),
            )
        if (type(value), field_type) not in whitelist:
            raise ValueError(msg.format(field_name, field_type, type(value)))

    try:
        value = field_type(value)
    except ValueError as e:
        e.message = msg.format(field_name, field_type, type(value))
        raise
    return value


def get_cloudbuild(raw_config, args):
    """Read and validate a cloudbuild recipe

    Args:
        raw_config (dict): deserialized cloudbuild.yaml
        args (argparse.Namespace): ccommand line flags

    Returns:
        CloudBuild: valid configuration
    """
    if not isinstance(raw_config, dict):
        raise ValueError(
            'Expected {} contents to be of type "dict", but found type "{}"'.
            format(args.config, type(raw_config)))

    raw_steps = get_field_value(raw_config, 'steps', list)
    if not raw_steps:
        raise ValueError('No steps defined in {}'.format(args.config))

    steps = [get_step(raw_step) for raw_step in raw_steps]
    return CloudBuild(
        output_script=args.output_script,
        run=args.run,
        steps=steps,
        substitutions=args.substitutions,
    )


def get_step(raw_step):
    """Read and validate a single cloudbuild step

    Args:
        raw_step (dict): deserialized step

    Returns:
        Step: valid build step
    """
    if not isinstance(raw_step, dict):
        raise ValueError(
            'Expected step to be of type "dict", but found type "{}"'.
            format(type(raw_step)))
    raw_args = get_field_value(raw_step, 'args', list)
    args = [get_field_value(raw_args, index, str)
            for index in range(len(raw_args))]
    dir_ = get_field_value(raw_step, 'dir', str)
    raw_env = get_field_value(raw_step, 'env', list)
    env = [get_field_value(raw_env, index, str)
           for index in range(len(raw_env))]
    name = get_field_value(raw_step, 'name', str)
    return Step(
        args=args,
        dir_=dir_,
        env=env,
        name=name,
    )


def generate_command(step, subs):
    """Generate a single shell command to run for a single cloudbuild step

    Args:
        step (Step): Valid build step
        subs (dict): Substitution map to apply

    Returns:
        [str]: A single shell command, expressed as a list of quoted tokens.
    """
    quoted_args = [sub_and_quote(arg, subs) for arg in step.args]
    quoted_env = []
    for env in step.env:
        quoted_env.extend(['--env', sub_and_quote(env, subs)])
    quoted_name = sub_and_quote(step.name, subs)
    workdir = '/workspace'
    if step.dir_:
        workdir = os.path.join(workdir, sub_and_quote(step.dir_, subs))
    process_args = [
        'docker',
        'run',
        '--volume',
        '/var/run/docker.sock:/var/run/docker.sock',
        '--volume',
        '/root/.docker:/root/.docker',
        '--volume',
        '${HOST_WORKSPACE}:/workspace',
        '--workdir',
        workdir,
    ] + quoted_env + [quoted_name] + quoted_args
    return process_args


def generate_script(cloudbuild):
    """Generate the contents of a shell script

    Args:
        cloudbuild (CloudBuild): Valid cloudbuild configuration

    Returns:
        (str): Contents of shell script
    """
    outfile = io.StringIO()
    outfile.write(BUILD_SCRIPT_HEADER)
    docker_commands = [generate_command(step, cloudbuild.substitutions)
                       for step in cloudbuild.steps]
    for docker_command in docker_commands:
        line = ' '.join(docker_command) + '\n\n'
        outfile.write(line)
    outfile.write(BUILD_SCRIPT_FOOTER)
    s = outfile.getvalue()
    outfile.close()
    return s


def make_executable(path):
    """Set executable bit(s) on file"""
    # http://stackoverflow.com/questions/12791997
    mode = os.stat(path).st_mode
    mode |= (mode & 0o444) >> 2  # copy R bits to X
    os.chmod(path, mode)


def write_script(cloudbuild, contents):
    """Write a shell script to a file."""
    print('Writing build script to {}'.format(cloudbuild.output_script))
    with open(cloudbuild.output_script, 'w', encoding='utf8') as outfile:
        outfile.write(contents)
    make_executable(cloudbuild.output_script)


def local_cloudbuild(args):
    """Execute the steps of a cloudbuild.yaml locally

    Args:
        args: command line flags as per parse_args
    """
    # Load and parse cloudbuild.yaml
    with open(args.config, 'r', encoding='utf8') as cloudbuild_file:
        raw_config = yaml.safe_load(cloudbuild_file)

    # Determine configuration
    cloudbuild = get_cloudbuild(raw_config, args)

    # Create shell script
    contents = generate_script(cloudbuild)
    write_script(cloudbuild, contents)

    # Run shell script
    if cloudbuild.run:
        args = [os.path.abspath(cloudbuild.output_script)]
        subprocess.check_call(args)


def validate_arg_regex(flag_value, flag_regex):
    """Check a named command line flag against a regular expression"""
    if not re.match(flag_regex, flag_value):
        raise argparse.ArgumentTypeError(
            'Value "{}" does not match pattern "{}"'.format(
                flag_value, flag_regex.pattern))
    return flag_value


def validate_arg_dict(flag_value):
    """Parse a command line flag as a key=val,... dict"""
    if not flag_value:
        return {}
    entries = flag_value.split(',')
    pairs = []
    for entry in entries:
        match = re.match(KEY_VALUE_REGEX, entry)
        if not match:
            raise argparse.ArgumentTypeError(
                'Value "{}" should be a list like _KEY1=value1,_KEY2=value2"'.format(
                    flag_value))
        pairs.append((match.group(1), match.group(2)))
    return dict(pairs)


def parse_args(argv):
    """Parse and validate command line flags"""
    parser = argparse.ArgumentParser(
        description='Process cloudbuild.yaml locally to build Docker images')
    parser.add_argument(
        '--config',
        type=functools.partial(
            validate_arg_regex, flag_regex=PRINTABLE_REGEX),
        default='cloudbuild.yaml',
        help='Path to cloudbuild.yaml file'
    )
    parser.add_argument(
        '--output_script',
        type=functools.partial(
            validate_arg_regex, flag_regex=PRINTABLE_REGEX),
        help='Filename to write shell script to',
    )
    parser.add_argument(
        '--no-run',
        action='store_false',
        help='Create shell script but don\'t execute it',
        dest='run',
    )
    parser.add_argument(
        '--substitutions',
        type=validate_arg_dict,
        default={},
        help='Parameters to be substituted in the build specification',
    )
    args = parser.parse_args(argv[1:])
    if not args.output_script:
        args.output_script = args.config + "_local.sh"
    return args


def main():
    args = parse_args(sys.argv)
    local_cloudbuild(args)


if __name__ == '__main__':
    main()
