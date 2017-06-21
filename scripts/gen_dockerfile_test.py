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
import re
import shutil
import subprocess
import tempfile
import unittest
import unittest.mock

import yaml

import gen_dockerfile

# Expected list of files generated
EXPECTED_OUTPUT_FILES = ['Dockerfile', '.dockerignore']


class GenDockerfileTest(unittest.TestCase):
    def setUp(self):
        self.testdata_dir = os.path.join(os.path.dirname(__file__), 'testdata')
        assert os.path.isdir(self.testdata_dir), 'Could not run test: testdata directory not found'

    def compare_file(self, filename, dir1, dir2):
        """Compare identically named files in two different directories"""
        if not filecmp.cmp(os.path.join(dir1, filename),
                           os.path.join(dir2, filename)):
            msg = 'Contents of "{}" differ between "{}" and "{}"'.format(
                filename, dir1, dir2)
            self.assertMultiLineEqual(contents1, contents2, msg)

    def test_get_app_config(self):
        config_file = 'some_config_file'
        base_image = 'some_image_name'
        source_dir = 'some_source_dir'

        valid_cases = (
            # Basic app.yaml
            ('env: flex', False, {
                'base_image': 'some_image_name',
                'dockerfile_python_version': '',
                'has_requirements_txt': False,
                'entrypoint': '',
            }),
            # All supported python versions
            ('runtime_config:\n python_version:', False, {
                'dockerfile_python_version': '',
            }),
            ('runtime_config:\n python_version: 2', False, {
                'dockerfile_python_version': '',
            }),
            ('runtime_config:\n python_version: 3', False, {
                'dockerfile_python_version': '3.5',
            }),
            ('runtime_config:\n python_version: 3.4', False, {
                'dockerfile_python_version': '3.4',
            }),
            ('runtime_config:\n python_version: 3.5', False, {
                'dockerfile_python_version': '3.5',
            }),
            # requirements.txt present
            ('env: flex', True, {
                'has_requirements_txt': True,
            }),
            # entrypoint present
            ('entrypoint: my entrypoint', False, {
                'entrypoint': 'exec my entrypoint',
            }),
        )
        for valid_case in valid_cases:
            with self.subTest(valid_case=valid_case):
                app_yaml, isfile, expected = valid_case
                raw_app_config = yaml.safe_load(app_yaml)
                with unittest.mock.patch.object(
                        os.path, 'isfile', return_value=isfile):
                    actual = gen_dockerfile.get_app_config(
                        raw_app_config, base_image, config_file,
                        source_dir)
                    for key, value in expected.items():
                        self.assertEqual(getattr(actual, key), value)

        invalid_cases = (
            # Empty app.yaml
            '',
            # Invalid entrypoint
            'entrypoint: "bad \\n entrypoint"',
            # Invalid python version
            'runtime_config:\n python_version: 1',
            'runtime_config:\n python_version: python2',
        )
        for invalid_case in invalid_cases:
            with self.subTest(invalid_case=invalid_case):
                raw_app_config = yaml.safe_load(invalid_case)
                with self.assertRaises(ValueError):
                    gen_dockerfile.get_app_config(
                        raw_app_config, base_image, config_file,
                        source_dir)

    def test_generate_files(self):
        base = gen_dockerfile.AppConfig(
            base_image='',
            dockerfile_python_version='',
            entrypoint='',
            has_requirements_txt=False
        )
        cases = (
            # Requirements.txt
            (base, False, 'ADD requirements.txt'),
            (base._replace(has_requirements_txt=True), True,
             'ADD requirements.txt'),
            # Entrypoint
            (base, False, 'CMD'),
            (base._replace(entrypoint='my entrypoint'), True,
             'CMD my entrypoint'),
            (base._replace(entrypoint='exec my entrypoint'), True,
             'CMD exec my entrypoint'),
            # Base runtime image
            (base._replace(base_image='my_base_runtime_image'), True,
             'FROM my_base_runtime_image'),
            # Python version
            (base._replace(dockerfile_python_version='_my_version'), True,
             'python_version=python_my_version'),
        )
        for case in cases:
            with self.subTest(case=case):
                app_config, should_find, test_string = case
                result = gen_dockerfile.generate_files(app_config)
                self.assertEqual(
                    sorted(result.keys()), sorted(EXPECTED_OUTPUT_FILES))
                dockerfile = result['Dockerfile']
                if should_find:
                    self.assertIn(test_string, dockerfile)
                else:
                    self.assertNotIn(test_string, dockerfile)

    def test_generate_dockerfile_command(self):
        """Generates output and compares against a set of golden files.

        Optionally runs 'gcloud app gen-config' and compares against that.
        """
        # Sample app from https://github.com/GoogleCloudPlatform/python-docs-samples
        with tempfile.TemporaryDirectory(
                prefix='gen_dockerfile_test_') as parent_tempdir:
            for app in ['hello_world']:
                app_dir = os.path.join(self.testdata_dir, app)
                temp_dir = os.path.join(parent_tempdir, app)
                os.mkdir(temp_dir)

                # Copy sample app to writable temp dir, and generate Dockerfile.
                config_dir = os.path.join(temp_dir, 'config')
                shutil.copytree(app_dir, config_dir)
                gen_dockerfile.generate_dockerfile_command(
                    base_image='gcr.io/google-appengine/python',
                    config_file=os.path.join(config_dir, 'app.yaml'),
                    source_dir=config_dir)

                # Compare against golden files
                golden_dir = os.path.join(self.testdata_dir, app + '_golden')
                for filename in EXPECTED_OUTPUT_FILES:
                    with self.subTest(source='golden', filename=filename):
                        self.compare_file(filename, config_dir, golden_dir)

                # Copy sample app to different writable temp dir, and
                # generate Dockerfile using gcloud.
                if not shutil.which('gcloud'):
                    self.skipTest(
                        '"gcloud" tool not found in $PATH, skipping test')
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
                    with self.subTest(source='gcloud', filename=filename):
                        self.compare_file(filename, config_dir, gen_config_dir)

    def test_parse_args(self):
        valid_cases = (
            [],
            ['argv0', '--base-image=nocolon'],
            ['argv0', '--base-image=name:andcolon'],
            ['argv0', '--base-image=name@sha256:digest'],
        )
        for argv in valid_cases:
            with self.subTest(valid_argv=argv):
                args = gen_dockerfile.parse_args(argv)

        def mock_error(*args):
            """Prevent argparse from calling sys.exit()"""
            raise AssertionError(*args)

        invalid_cases = (
            ['argv0', '--base-image='],
            ['argv0', '--base-image=:'],
            ['argv0', '--base-image=:noname'],
        )
        for argv in invalid_cases:
            with self.subTest(invalid_argv=argv):
                with unittest.mock.patch.object(
                    argparse.ArgumentParser, 'error', mock_error):
                    with self.assertRaises(AssertionError):
                        gen_dockerfile.parse_args(argv)


if __name__ == '__main__':
    unittest.main()
