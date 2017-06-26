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
import contextlib
import os
import re
import shutil
import subprocess
import unittest.mock

import pytest
import yaml

import local_cloudbuild


# Matches script boilerplate
STAGING_DIR_REGEX = re.compile(
    b'(?m)Copying source to staging directory (.+)$')


@pytest.fixture
def testdata_dir():
    testdata_dir = os.path.join(os.path.dirname(__file__), 'testdata')
    assert os.path.isdir(testdata_dir), (
        'Could not run test: testdata directory not found')
    return testdata_dir


@pytest.mark.parametrize('s, subs, expected, expected_used', [
    # Empty string
    ('', {}, "''", []),
    # No substitutions
    ('a', {}, 'a', []),
    # Unused substitition (ok here but error in generate_script)
    ('a', {'FOO': 'foo'}, 'a', []),
    ('a', {'_FOO': '_foo'}, 'a', []),
    # Defined builtin substitution
    ('a$FOOb', {'FOO': 'foo'}, 'afoob', ['FOO']),
    ('a${FOO}b', {'FOO': 'foo'}, 'afoob', ['FOO']),
    # Defined user substitution
    ('a$_FOOb', {'_FOO': '_foo'}, 'a_foob', ['_FOO']),
    ('a${_FOO}b', {'_FOO': '_foo'}, 'a_foob', ['_FOO']),
    # Multiple substitutions
    ('$FOO${FOO}${BAR}$FOO',
     {'FOO': 'foo', 'BAR': 'bar'},
     'foofoobarfoo',
     ['FOO', 'BAR']),
    # Invalid names
    ('a $ b', {}, "'a $ b'", []),
    ('a$foo b', {}, "'a$foo b'", []),
    ('a$0FOO b', {}, "'a$0FOO b'", []),
])
def test_sub_and_quote_valid(s, subs, expected, expected_used):
    used = set()
    actual = local_cloudbuild.sub_and_quote(s, subs, used)
    assert actual == expected
    assert used == set(expected_used)


@pytest.mark.parametrize('s, subs', [
    # Undefined builtin substitution
    ('a$FOOb', {}),
    ('a${FOO}b', {}),
    # Undefined user substitution
    ('a$_FOOb', {}),
    ('a${_FOO}b', {}),
])
def test_sub_and_quote_invalid(s, subs):
    with pytest.raises(ValueError):
        used = set()
        local_cloudbuild.sub_and_quote(s, subs, used)


def have_docker():
    """Determine if the Docker daemon is present and usable"""
    if ((shutil.which('docker') is not None) and
        (subprocess.call(['docker', 'info'],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL) == 0)):
        return True
    return False


_args = argparse.Namespace(
    config='some_config_file',
    output_script='some_output_script',
    run=False,
    substitutions={},
)


def test_get_cloudbuild_valid():
    raw_yaml = 'steps:\n- name: step1\n- name: step2\n'
    raw_config = yaml.safe_load(raw_yaml)
    actual = local_cloudbuild.get_cloudbuild(raw_config, _args)
    assert len(actual.steps) == 2


@pytest.mark.parametrize('raw_yaml', [
    # Empty cloud build
    '',
    # No steps
    'foo: bar\n',
    # Steps not a list
    'steps: astring\n',
    ])
def test_get_cloudbuild_invalid(raw_yaml):
    raw_config = yaml.safe_load(raw_yaml)
    with pytest.raises(ValueError):
        local_cloudbuild.get_cloudbuild(raw_config, _args)


@pytest.mark.parametrize('raw_step, expected', [
    # Empty step
    ({}, local_cloudbuild.Step(
        args=[],
        dir_='',
        env=[],
        name='',
    )),
    # Full step
    ({'name': 'aname',
      'args': ['arg1', 2, 'arg3 with \n newline'],
      'env': ['ENV1=value1', 'ENV2=space in value2'],
      'dir': 'adir',
      }, local_cloudbuild.Step(
        args=['arg1', '2', 'arg3 with \n newline'],
        env=['ENV1=value1', 'ENV2=space in value2'],
        dir_='adir',
        name='aname',
    )),
])
def test_get_step_valid(raw_step, expected):
    actual = local_cloudbuild.get_step(raw_step)
    assert actual == expected


@pytest.mark.parametrize('raw_step', [
    # Wrong type
    [],
    # More wrong types
    {'args': 'not_a_list'},
    {'args': [[]]},
    {'env': 'not_a_list'},
    {'env': [{}]},
    {'dir': {}},
    {'name': []},
])
def test_get_step_invalid(raw_step):
    with pytest.raises(ValueError):
        local_cloudbuild.get_step(raw_step)


# Basic valid case
_base_step = local_cloudbuild.Step(
    args=['arg1', 'arg2'],
    dir_='',
    env=['ENV1=value1', 'ENV2=value2'],
    name='aname',
)
_subs = {'BUILTIN': 'builtin', '_USER': '_user'}


def test_generate_command_basic():
    command = local_cloudbuild.generate_command(_base_step, _subs, set())
    assert command == [
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
    ]


@pytest.mark.parametrize('step, args', [
    # dir specified
    (_base_step._replace(dir_='adir'),
     ['--workdir', '/workspace/adir']),
    # Shell quoting
    (_base_step._replace(args=['arg with \n newline']),
     ["'arg with \n newline'"]),
    (_base_step._replace(dir_='dir/ with space/'),
     ["/workspace/'dir/ with space/'"]),
    (_base_step._replace(env=['env with space']),
     ["'env with space'"]),
    (_base_step._replace(name='a name'),
     ["'a name'"]),
    # Variable substitution
    (_base_step._replace(name='a $BUILTIN substitution'),
     ["'a builtin substitution'"]),
    (_base_step._replace(name='a $_USER substitution'),
     ["'a _user substitution'"]),
    (_base_step._replace(name='a curly brace ${BUILTIN} substitution'),
     ["'a curly brace builtin substitution'"]),
    (_base_step._replace(
        name='an escaped $$ or $$$$ or $$FOO or $${_FOO} is unescaped'),
     ["'an escaped $ or $$ or $FOO or ${_FOO} is unescaped'"]),
])
def test_generate_command_valid(step, args):
    command = local_cloudbuild.generate_command(step, _subs, set())
    for arg in args:
        assert arg in command


@pytest.mark.parametrize('step', [
    _base_step._replace(name='a $UNSET_BUILTIN substitution'),
    _base_step._replace(name='a $_UNSET_USER substitution'),
])
def test_generate_command_invalid(step):
    with pytest.raises(ValueError):
        local_cloudbuild.generate_command(step, _subs, set())


def test_generate_script_golden(testdata_dir):
    config_name = 'cloudbuild_ok.yaml'
    expected_output_script = os.path.join(
        testdata_dir, config_name + '_golden.sh')
    cloudbuild = local_cloudbuild.CloudBuild(
        output_script='test_generate_script',
        run=False,
        steps=[
            local_cloudbuild.Step(
                args=['/bin/sh', '-c', 'printenv MESSAGE'],
                dir_='',
                env=['MESSAGE=Hello World!'],
                name='debian',
            ),
            local_cloudbuild.Step(
                args=['/bin/sh', '-c', 'printenv MESSAGE'],
                dir_='',
                env=['MESSAGE=Goodbye\\n And Farewell!', 'UNUSED=unused'],
                name='debian',
            )
        ],
        substitutions=local_cloudbuild.DEFAULT_SUBSTITUTIONS,
    )
    actual = local_cloudbuild.generate_script(cloudbuild)
    # Compare output against golden
    with open(expected_output_script, 'r', encoding='utf8') as expected_file:
        expected = expected_file.read()
        assert actual == expected


def test_generate_script_unused_user_substitution():
    cloudbuild = local_cloudbuild.CloudBuild(
        output_script='',
        run=False,
        steps=[],
        substitutions={'_FOO': '_foo'},
    )
    with pytest.raises(ValueError, match='User substitution variables'):
        local_cloudbuild.generate_script(cloudbuild)


def test_make_executable(tmpdir):
    test_script_filename = tmpdir.join('test_make_executable.sh')
    with test_script_filename.open('w', encoding='utf8') as test_script:
        test_script.write('#!/bin/sh\necho "Output from test_make_executable"')
    local_cloudbuild.make_executable(str(test_script_filename))
    output = subprocess.check_output([str(test_script_filename)])
    assert output.decode('utf8') == "Output from test_make_executable\n"


def test_write_script(tmpdir):
    contents = 'The contents\n'
    output_script_filename = tmpdir.join('test_write_script')
    cloudbuild = local_cloudbuild.CloudBuild(
        output_script=str(output_script_filename),
        run=False,
        steps=[],
        substitutions={},
    )
    local_cloudbuild.write_script(cloudbuild, contents)
    with output_script_filename.open('r', encoding='utf8') as output_script:
        actual = output_script.read()
    assert actual == contents


@contextlib.contextmanager
def chdir(new_dir):
    """Not threadsafe"""
    old_dir = os.getcwd()
    os.chdir(new_dir)
    yield
    os.chdir(old_dir)


@pytest.mark.parametrize('config_name, substitutions, exception, cleanup', [
    # Everything is ok
    ('cloudbuild_ok.yaml', None, None, True),
    # Builtin substitutions like $PROJECT_ID work
    ('cloudbuild_builtin_substitutions.yaml', None, None, True),
    # User substitutions like $_FOO work
    ('cloudbuild_user_substitutions.yaml',
     {'_FOO': 'this is foo value'},
     None, True
     ),
    # User substitutions like $_FOO fails when undefined
    ('cloudbuild_user_substitutions.yaml', None, ValueError, False),
    # Exit code 1 (failure)
    ('cloudbuild_err_rc1.yaml', None, subprocess.CalledProcessError, True),
    # Command not found
    ('cloudbuild_err_not_found.yaml', None, subprocess.CalledProcessError,
     True),
    # Cleaning up files owned by root
    ('cloudbuild_difficult_cleanup.yaml', None, None, True),
])
def test_local_cloudbuild(testdata_dir, tmpdir, config_name, substitutions,
                          exception, cleanup):
    if not have_docker():
        pytest.fail('This test requires a working Docker daemon')

    check_call_output = None

    def check_call(*args, **kw_args):
        """Act like subprocess.check_call but store stdout"""
        nonlocal check_call_output
        try:
            check_call_output = subprocess.check_output(*args, **kw_args)
            print(check_call_output)
        except subprocess.CalledProcessError as e:
            check_call_output = e.output
            print(check_call_output)
            raise

    # Read cloudbuild.yaml from testdata file, write output to
    # tempdir, and maybe try to run it
    with unittest.mock.patch('subprocess.check_call', check_call):
        if substitutions is None:
            substitutions = local_cloudbuild.DEFAULT_SUBSTITUTIONS
        should_succeed = (exception is None)
        config = os.path.join(testdata_dir, config_name)
        actual_output_script = tmpdir.join(config_name + '_local.sh')
        args = argparse.Namespace(
            config=config,
            output_script=str(actual_output_script),
            run=True,
            substitutions=substitutions,
        )

        # The source directory of the build is currently hardcoded as
        # '.', so we must chdir there.
        with chdir(testdata_dir):
            if should_succeed:
                local_cloudbuild.local_cloudbuild(args)
            else:
                with pytest.raises(exception):
                    local_cloudbuild.local_cloudbuild(args)

        # Check that staging dir was cleaned up
        if cleanup:
            assert check_call_output is not None
            match = re.search(STAGING_DIR_REGEX, check_call_output)
            assert match
            staging_dir = match.group(1)
            assert not os.path.isdir(staging_dir)


@pytest.mark.parametrize('argv, expected', [
    # Test explicit output_script
    (['argv0', '--output_script=my_output'], 'my_output'),
    # Test implicit output_script
    (['argv0', '--config=my_config'], 'my_config_local.sh'),
])
def test_parse_args_output_script(argv, expected):
    args = local_cloudbuild.parse_args(argv)
    assert args.output_script == expected


@pytest.mark.parametrize('argv, expected', [
    # Test run flag (default)
    (['argv0'], True),
    (['argv0', '--no-run'], False),
])
def test_parse_args_run_flag(argv, expected):
    args = local_cloudbuild.parse_args(argv)
    assert args.run == expected


if __name__ == '__main__':
    pytest.main([__file__])
