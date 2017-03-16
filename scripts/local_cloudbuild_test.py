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

"""Unit test for local_cloudbuild.py"""

import argparse
import os
import re
import shutil
import subprocess
import tempfile
import unittest
import unittest.mock

import yaml

import local_cloudbuild


# Matches script boilerplate
STAGING_DIR_REGEX = re.compile(
    b'(?m)Copying source to staging directory (.+)$')

class ValidationUtilsTest(unittest.TestCase):

    def test_get_field_value(self):
        valid_cases = (
            # Normal case, field present and correct type
            ({ 'present': 1 }, 'present', int, 1),
            ({ 'present': '1' }, 'present', str, '1'),
            ({ 'present': [1] }, 'present', list, [1]),
            ({ 'present': {1: 2} }, 'present', dict, {1: 2}),
            # Missing field replaced by default
            ({}, 'missing', str, ''),
            # Valid conversions
            ({ 'str_to_int': '1' }, 'str_to_int', int, 1),
            ({ 'int_to_str': 1 }, 'int_to_str', str, '1'),
        )
        for valid_case in valid_cases:
            with self.subTest(valid_case=valid_case):
                container, field_name, field_type, expected = valid_case
                self.assertEqual(
                    local_cloudbuild.get_field_value(
                        container, field_name, field_type),
                    expected)

        invalid_cases = (
            # Type conversion failures
            ({ 'bad_list_to_dict': [1] }, 'bad_list_to_dict', dict),
            ({ 'bad_list_to_str': [1] }, 'bad_list_to_str', str),
            ({ 'bad_dict_to_list': {1: 2} }, 'bad_dict_to_list', list),
            ({ 'bad_str_to_int': 'not_an_int' }, 'bad_str_to_int', int),
            ({ 'bad_str_to_list': 'abc' }, 'bad_str_to_list', list),
        )
        for invalid_case in invalid_cases:
            with self.subTest(invalid_case=invalid_case):
                container, field_name, field_type = invalid_case
                with self.assertRaises(ValueError):
                    local_cloudbuild.get_field_value(
                        container, field_name, field_type)

    def test_validate_arg_regex(self):
        self.assertEqual(
            local_cloudbuild.validate_arg_regex('abc', re.compile('a[b]c')),
            'abc')
        with self.assertRaises(argparse.ArgumentTypeError):
            local_cloudbuild.validate_arg_regex('abc', re.compile('a[d]c'))


class LocalCloudbuildTest(unittest.TestCase):

    def setUp(self):
        self.testdata_dir = 'testdata'
        assert os.path.isdir(self.testdata_dir), 'Could not run test: testdata directory not found'

    def check_call_with_capture(self, *args, **kw_args):
        """Act like subprocess.check_call but capture stdout"""
        try:
            self.check_call_output = subprocess.check_output(*args, **kw_args)
            print(self.check_call_output)
        except subprocess.CalledProcessError as e:
            self.check_call_output = e.output
            print(self.check_call_output)
            raise

    def have_docker(self):
        """Determine if the Docker daemon is present and usable"""
        if ((shutil.which('docker') is not None) and
            (subprocess.call(['docker', 'info'],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL) == 0)):
            return True
        return False

    def test_get_cloudbuild(self):
        args = argparse.Namespace(
            config='some_config_file',
            output_script='some_output_script',
            run=False,
        )
        # Basic valid case
        valid_case = 'steps:\n- name: step1\n- name: step2\n'
        raw_config = yaml.safe_load(valid_case)
        actual = local_cloudbuild.get_cloudbuild(raw_config, args)
        self.assertEqual(len(actual.steps), 2)

        invalid_cases = (
            # Empty cloud build
            '',
            # No steps
            'foo: bar\n',
            # Steps not a list
            'steps: astring\n',
        )
        for invalid_case in invalid_cases:
            with self.subTest(invalid_case=invalid_case):
                raw_config = yaml.safe_load(invalid_case)
                with self.assertRaises(ValueError):
                    local_cloudbuild.get_cloudbuild(raw_config, args)

    def test_get_step(self):
        valid_cases = (
            # Empty step
            ({}, local_cloudbuild.Step(
                args=[],
                dir_='',
                env=[],
                name='',
            )),
            # Full step
            ({'name' : 'aname',
              'args' : [ 'arg1', 2, 'arg3 with \n newline', ],
              'env' : [ 'ENV1=value1', 'ENV2=space in value2' ],
              'dir' : 'adir',
              }, local_cloudbuild.Step(
                  args = [ 'arg1', '2', 'arg3 with \n newline', ],
                  env = [ 'ENV1=value1', 'ENV2=space in value2' ],
                  dir_ = 'adir',
                  name = 'aname',
              )),
        )
        for valid_case in valid_cases:
            with self.subTest(valid_case=valid_case):
                raw_step, expected = valid_case
                actual = local_cloudbuild.get_step(raw_step)
                self.assertEqual(actual, expected)

        invalid_cases = (
            # Wrong type
            [],
            # More wrong types
            {'args': 'not_a_list'},
            {'args': [ [] ]},
            {'env': 'not_a_list'},
            {'env': [ {} ]},
            {'dir': {}},
            {'name': []},
        )
        for invalid_case in invalid_cases:
            with self.subTest(invalid_case=invalid_case):
                with self.assertRaises(ValueError):
                    local_cloudbuild.get_step(invalid_case)

    def test_generate_command(self):
        # Basic valid case
        base_step = local_cloudbuild.Step(
            args = ['arg1','arg2'],
            dir_ = '',
            env = ['ENV1=value1', 'ENV2=value2'],
            name = 'aname',
        )
        command = local_cloudbuild.generate_command(base_step)
        self.assertEqual(command, [
            'docker',
            'run',
            '--volume',
            '/var/run/docker.sock:/var/run/docker.sock',
            '--volume',
            '/root/.docker:/root/.docker',
            '--volume',
            '${HOST_WORKSPACE}:/workspace',
            '--workdir',
            '/workspace',
            '--env',
            'ENV1=value1',
            '--env',
            'ENV2=value2',
            'aname',
            'arg1',
            'arg2',
        ])

        # dir specified
        step = base_step._replace(dir_='adir')
        command = local_cloudbuild.generate_command(step)
        self.assertIn('--workdir', command)
        self.assertIn('/workspace/adir', command)

        # Shell quoting
        step = base_step._replace(args=['arg with \n newline'])
        command = local_cloudbuild.generate_command(step)
        self.assertIn("'arg with \n newline'", command)

        step = base_step._replace(dir_='dir/ with space/')
        command = local_cloudbuild.generate_command(step)
        self.assertIn("/workspace/'dir/ with space/'", command)

        step = base_step._replace(env=['env with space'])
        command = local_cloudbuild.generate_command(step)
        self.assertIn("'env with space'", command)

        step = base_step._replace(name='a name')
        command = local_cloudbuild.generate_command(step)
        self.assertIn("'a name'", command)

    def test_generate_script(self):
        config_name = 'cloudbuild_ok.yaml'
        config = os.path.join(self.testdata_dir, config_name)
        expected_output_script = os.path.join(self.testdata_dir, config_name + '_golden.sh')
        cloudbuild = local_cloudbuild.CloudBuild(
            output_script='test_generate_script',
            run=False,
            steps=[
                local_cloudbuild.Step(
                    args=['/bin/sh', '-c', 'echo "${MESSAGE}"'],
                    dir_='',
                    env=['MESSAGE=Hello World!'],
                    name='debian',
                ),
                local_cloudbuild.Step(
                    args=['/bin/sh', '-c', 'echo "${MESSAGE}"'],
                    dir_='',
                    env=['MESSAGE=Goodbye\\n And Farewell!', 'UNUSED=unused'],
                    name='debian',
                )
            ]
        )
        actual = local_cloudbuild.generate_script(cloudbuild)
        self.maxDiff = 2**16
        # Compare output against golden
        with open(expected_output_script, 'r', encoding='utf8') as expected:
            self.assertEqual(actual, expected.read())

    def test_make_executable(self):
        with tempfile.TemporaryDirectory(
                prefix='local_cloudbuild_test_') as tempdir:
            test_script_filename = os.path.join(tempdir, 'test_make_executable.sh')
            with open(test_script_filename, 'w', encoding='utf8') as test_script:
                test_script.write('#!/bin/sh\necho "Output from test_make_executable"')
            local_cloudbuild.make_executable(test_script_filename)
            output = subprocess.check_output([test_script_filename])
            self.assertEqual(output.decode('utf8'), "Output from test_make_executable\n")

    def test_write_script(self):
        with tempfile.TemporaryDirectory(
            prefix='local_cloudbuild_test_') as tempdir:
            contents = 'The contents\n'
            output_script_filename = os.path.join(tempdir, 'test_write_script')
            cloudbuild = local_cloudbuild.CloudBuild(
                output_script=output_script_filename,
                run=False,
                steps=[],
            )
            local_cloudbuild.write_script(cloudbuild, contents)
            with open(output_script_filename, 'r', encoding='utf8') as output_script:
                actual = output_script.read()
            self.assertEqual(actual, contents)

    def test_local_cloudbuild(self):
        # Actually run it if we can find a docker command.
        should_run = self.have_docker()

        # Read cloudbuild.yaml from testdata file, write output to
        # tempdir, and maybe try to run it
        cases = (
            # Everything is ok
            ('cloudbuild_ok.yaml', True),
            # Exit code 1 (failure)
            ('cloudbuild_err_rc1.yaml', False),
            # Command not found
            ('cloudbuild_err_not_found.yaml', False),
            # Cleaning up files owned by root
            ('cloudbuild_difficult_cleanup.yaml', True),
        )
        for case in cases:
            with self.subTest(case=case), \
                    tempfile.TemporaryDirectory(prefix='local_cloudbuild_test_') as tempdir, \
                    unittest.mock.patch('subprocess.check_call', self.check_call_with_capture):
                config_name, should_succeed = case
                config = os.path.join(self.testdata_dir, config_name)
                actual_output_script = os.path.join(
                    tempdir, config_name + '_local.sh')
                args = argparse.Namespace(
                    config=config,
                    output_script=actual_output_script,
                    run=should_run)

                if should_run:
                    print('Executing docker commands in {}'.format(actual_output_script))
                    if should_succeed:
                        local_cloudbuild.local_cloudbuild(args)
                    else:
                        with self.assertRaises(subprocess.CalledProcessError):
                            local_cloudbuild.local_cloudbuild(args)

                    # Check that staging dir was cleaned up
                    match = re.search(STAGING_DIR_REGEX, self.check_call_output)
                    self.assertTrue(match)
                    staging_dir = match.group(1)
                    self.assertFalse(os.path.isdir(staging_dir), staging_dir)
                else:
                    # Generate but don't execute script
                    local_cloudbuild.local_cloudbuild(args)

    def test_parse_args(self):
        # Test explicit output_script
        argv = ['argv0', '--output_script=my_output']
        args = local_cloudbuild.parse_args(argv)
        self.assertEqual(args.output_script, 'my_output')
        # Test implicit output_script
        argv = ['argv0', '--config=my_config']
        args = local_cloudbuild.parse_args(argv)
        self.assertEqual(args.output_script, 'my_config_local.sh')

        # Test run flag (default and --no-run)
        argv = ['argv0']
        args = local_cloudbuild.parse_args(argv)
        self.assertEqual(args.run, True)
        argv = ['argv0', '--no-run']
        args = local_cloudbuild.parse_args(argv)
        self.assertEqual(args.run, False)


if __name__ == '__main__':
    unittest.main()
