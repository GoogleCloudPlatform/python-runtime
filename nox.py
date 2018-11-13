# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import fnmatch
import os

import nox


def _list_files(folder, pattern):
    """Lists all files below the given folder that match the pattern."""
    for root, folders, files in os.walk(folder):
        for filename in files:
            if fnmatch.fnmatch(filename, pattern):
                yield os.path.join(root, filename)


@nox.session
def check_requirements(session):
    """Checks for out of date requirements and optionally updates them."""
    session.install('gcp-devrel-py-tools')

    if 'update' in session.posargs:
        command = 'update-requirements'
    else:
        command = 'check-requirements'

    reqfiles = list(_list_files('.', 'requirements*.txt'))

    for reqfile in reqfiles:
        session.run('gcp-devrel-py-tools', command, reqfile)


@nox.session
def lint(session):
    session.interpreter = 'python3'  # So it understands Python3 syntax
    session.install('flake8', 'flake8-import-order')
    session.run(
        'flake8',
        '--import-order-style', 'google',
        '--application-import-names',
        'gen_dockerfile,local_cloudbuild,validation_utils',
        'scripts',
        'nox.py',
    )


@nox.session
@nox.parametrize('version', ['3.4', '3.5', '3.6', '3.7'])
def tests(session, version):
    session.interpreter = 'python' + version
    session.install('-r', 'scripts/requirements-test.txt')
    session.run(
        'py.test',
        '--ignore=scripts/testdata',
        '--cov=scripts',
        '--cov-append',
        '--cov-config=.coveragerc',
        '--cov-report=',  # Report generated below
        'scripts',
        env={'PYTHONPATH': ''}
    )


@nox.session
def cover(session):
    """Run the final coverage report.

    This outputs the coverage report aggregating coverage from the unit
    test runs (not system test runs), and then erases coverage data.
    """
    session.interpreter = 'python3.6'
    session.install('coverage', 'pytest-cov')
    session.run('coverage', 'report', '--show-missing', '--fail-under=97')
    session.run('coverage', 'erase')
