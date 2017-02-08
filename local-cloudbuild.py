#!/usr/bin/env python
#
# Run the steps of cloudbuild.yaml locally, emulating Google Container
# Builder functionality.  Does not actually push images to the
# Container Registry.  Not all functionality is supported.
#
# Based on https://cloud.google.com/container-builder/docs/api/build-steps

# System packages
import argparse
import getpass
import os
import shutil
import subprocess
import sys
import tempfile

# Third party packages
import yaml


# Types
class CloudBuildError(Exception):
    pass


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
    cloudbuild = None
    with open(args.cloudbuild, 'rb') as infile:
        cloudbuild = yaml.safe_load(infile)

    host_workspace_parent = tempfile.mkdtemp(prefix='local-cloudbuild_%s_' %
                                             getpass.getuser())
    host_workspace = os.path.join(host_workspace_parent, 'workspace')
    try:
        # Prepare workspace
        shutil.copytree('.', host_workspace, symlinks=True)

        # Execute a series of 'docker run' commands locally
        print('Running cloudbuild locally.  Host workspace directory is %s' %
              host_workspace)
        run_steps(cloudbuild, host_workspace)
    finally:
        if not args.keep_workspace:
            shutil.rmtree(host_workspace_parent, ignore_errors=True)


def run_steps(cloudbuild, host_workspace):
    """Run the steps listed in a cloudbuild.yaml file.

    Args:
        cloudbuild (dict): The decoded contents of a cloudbuild.yaml
        host_workspace (str): Scratch directory

    Raises:
        CloudBuildError if the yaml contents are invalid
    """
    steps = cloudbuild.get('steps', {})
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
    name = get(step, 'name', str)
    dir_ = get(step, 'dir', list)
    env = get(step, 'env', list)
    args = get(step, 'args', list)
    run_docker(name, dir_, env, args, host_workspace)


def get(container, field_name, field_type):
    """Fetch a field from a container with typechecking and default values.

    If the field is not present, a instance of `field_type` is
    constructed with no arguments and used as the default value.

    Args:
        container (dict): Object decoded from yaml
        field_name (str): Field that should be present in `container`
        field_type (type): Expected type for field value

    Returns:
        fetched or default value of field

    Raises:
        CloudBuildError if field value is present but is the wrong type.
    """
    value = container.get(field_name)
    if value is None:
        return field_type()
    if not isinstance(value, field_type):
        raise CloudBuildError(
            'Syntax error: Expected "%d" to be of type "%d", but found "%d"',
            field_name, field_type, type(value))
    return value


def run_docker(name, dir_, env_args, args, host_workspace):
    """Construct and execute a single 'docker run' command"""
    workdir = '/workspace'
    if dir_:
        workdir += '/' + dir_

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


if __name__ == '__main__':
    sys.exit(main(sys.argv))
