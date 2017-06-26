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

"""Unit test for gen_dockerfile.py"""

import argparse
import filecmp
import os
import shutil
import subprocess
import unittest.mock

import pytest
import yaml

import gen_dockerfile


# Expected list of files generated
EXPECTED_OUTPUT_FILES = ['Dockerfile', '.dockerignore']


@pytest.fixture
def testdata_dir():
    testdata_dir = os.path.join(os.path.dirname(__file__), 'testdata')
    assert os.path.isdir(testdata_dir), (
        'Could not run test: testdata directory not found')
    return testdata_dir


def compare_file(filename, dir1, dir2):
    """Compare identically named files in two different directories"""
    assert filecmp.cmp(
        os.path.join(dir1, filename), os.path.join(dir2, filename))


@pytest.mark.parametrize('app_yaml, expected', [
    # Basic app.yaml
    ('env: flex', {
        'base_image': 'some_image_name',
        'dockerfile_python_version': '',
        'has_requirements_txt': False,
        'entrypoint': '',
    }),
    # All supported python versions
    ('runtime_config:\n python_version:', {
        'dockerfile_python_version': '',
    }),
    ('runtime_config:\n python_version: 2', {
        'dockerfile_python_version': '',
    }),
    ('runtime_config:\n python_version: 3', {
        'dockerfile_python_version': '3.5',
    }),
    ('runtime_config:\n python_version: 3.4', {
        'dockerfile_python_version': '3.4',
    }),
    ('runtime_config:\n python_version: 3.5', {
        'dockerfile_python_version': '3.5',
    }),
    # entrypoint present
    ('entrypoint: my entrypoint', {
        'entrypoint': 'exec my entrypoint',
    }),
])
def test_get_app_config_valid(app_yaml, expected):
    config_file = 'some_config_file'
    base_image = 'some_image_name'
    source_dir = 'some_source_dir'
    raw_app_config = yaml.safe_load(app_yaml)
    actual = gen_dockerfile.get_app_config(
        raw_app_config, base_image, config_file,
        source_dir)
    for key, value in expected.items():
        assert getattr(actual, key) == value


def test_get_app_config_requirements_txt():
    """requirements.txt file present"""
    app_yaml = 'env: flex'
    expected = {
        'has_requirements_txt': True,
    }
    with unittest.mock.patch.object(os.path, 'isfile', return_value=True):
        test_get_app_config_valid(app_yaml, expected)


@pytest.mark.parametrize('app_yaml', [
    # Empty app.yaml
    '',
    # Invalid entrypoint
    'entrypoint: "bad \\n entrypoint"',
    # Invalid python version
    'runtime_config:\n python_version: 1',
    'runtime_config:\n python_version: python2',
])
def test_get_app_config_invalid(app_yaml):
    config_file = 'some_config_file'
    base_image = 'some_image_name'
    source_dir = 'some_source_dir'
    raw_app_config = yaml.safe_load(app_yaml)
    with pytest.raises(ValueError):
        gen_dockerfile.get_app_config(
            raw_app_config, base_image, config_file, source_dir)


# Basic AppConfig used below
_base = gen_dockerfile.AppConfig(
    base_image='',
    dockerfile_python_version='',
    entrypoint='',
    has_requirements_txt=False
)


@pytest.mark.parametrize('app_config, should_find, test_string', [
    # Requirements.txt
    (_base, False, 'ADD requirements.txt'),
    (_base._replace(has_requirements_txt=True), True,
     'ADD requirements.txt'),
    # Entrypoint
    (_base, False, 'CMD'),
    (_base._replace(entrypoint='my entrypoint'), True,
     'CMD my entrypoint'),
    (_base._replace(entrypoint='exec my entrypoint'), True,
     'CMD exec my entrypoint'),
    # Base runtime image
    (_base._replace(base_image='my_base_runtime_image'), True,
     'FROM my_base_runtime_image'),
    # Python version
    (_base._replace(dockerfile_python_version='_my_version'), True,
     'python_version=python_my_version'),
])
def test_generate_files(app_config, should_find, test_string):
    result = gen_dockerfile.generate_files(app_config)
    assert sorted(result.keys()) == sorted(EXPECTED_OUTPUT_FILES)
    dockerfile = result['Dockerfile']
    if should_find:
        assert test_string in dockerfile
    else:
        assert test_string not in dockerfile


@pytest.mark.parametrize('app', [
    # Sample from https://github.com/GoogleCloudPlatform/python-docs-samples
    'hello_world',
])
def test_generate_dockerfile_command(tmpdir, testdata_dir, app):
    """Generates output and compares against a set of golden files.

    Optionally runs 'gcloud app gen-config' and compares against that.
    """
    app_dir = os.path.join(testdata_dir, app)
    temp_dir = os.path.join(str(tmpdir), app)
    os.mkdir(temp_dir)

    # Copy sample app to writable temp dir, and generate Dockerfile.
    config_dir = os.path.join(temp_dir, 'config')
    shutil.copytree(app_dir, config_dir)
    gen_dockerfile.generate_dockerfile_command(
        base_image='gcr.io/google-appengine/python',
        config_file=os.path.join(config_dir, 'app.yaml'),
        source_dir=config_dir)

    # Compare against golden files
    golden_dir = os.path.join(testdata_dir, app + '_golden')
    for filename in EXPECTED_OUTPUT_FILES:
        compare_file(filename, config_dir, golden_dir)

    # Copy sample app to different writable temp dir, and
    # generate Dockerfile using gcloud.
    if not shutil.which('gcloud'):
        print('"gcloud" tool not found in $PATH, skipping rest of test')
        return
    gen_config_dir = os.path.join(temp_dir, 'gen_config')
    shutil.copytree(app_dir, gen_config_dir)
    app_yaml = os.path.join(gen_config_dir, 'app.yaml')
    gcloud_args = [
        'gcloud', '--quiet', 'beta', 'app', 'gen-config',
        gen_config_dir, '--custom', '--config={}'.format(app_yaml)
    ]
    print('Invoking gcloud as {}'.format(gcloud_args))
    subprocess.check_call(gcloud_args)
    for filename in EXPECTED_OUTPUT_FILES:
        compare_file(filename, config_dir, gen_config_dir)


@pytest.mark.parametrize('argv', [
    [],
    ['argv0', '--base-image=nocolon'],
    ['argv0', '--base-image=name:andcolon'],
    ['argv0', '--base-image=name@sha256:digest'],
])
def test_parse_args_valid(argv):
    args = gen_dockerfile.parse_args(argv)
    assert args is not None


@pytest.mark.parametrize('argv', [
    ['argv0', '--base-image='],
    ['argv0', '--base-image=:'],
    ['argv0', '--base-image=:noname'],
])
def test_parse_args_invalid(argv):
    def mock_error(*args):
        """Prevent argparse from calling sys.exit()"""
        raise AssertionError(*args)

    with unittest.mock.patch.object(argparse.ArgumentParser, 'error',
                                    mock_error):
        with pytest.raises(AssertionError):
            gen_dockerfile.parse_args(argv)
