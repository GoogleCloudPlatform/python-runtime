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

"""Unit test for validation_utils.py"""

import argparse
import re

import pytest

import validation_utils


@pytest.mark.parametrize('container, field_name, field_type, expected', [
    # Normal case, field present and correct type
    ({'present': 1}, 'present', int, 1),
    ({'present': '1'}, 'present', str, '1'),
    ({'present': [1]}, 'present', list, [1]),
    ({'present': {1: 2}}, 'present', dict, {1: 2}),
    # Missing field replaced by default
    ({}, 'missing', str, ''),
    # Valid conversions
    ({'str_to_int': '1'}, 'str_to_int', int, 1),
    ({'int_to_str': 1}, 'int_to_str', str, '1'),
    # None
    ({'None_to_int': None}, 'None_to_int', int, 0),
    ({'None_to_str': None}, 'None_to_str', str, ''),
])
def test_get_field_value_valid(container, field_name, field_type, expected):
    assert validation_utils.get_field_value(
        container, field_name, field_type) == expected


@pytest.mark.parametrize('container, field_name, field_type', [
    # Type conversion failures
    ({'bad_list_to_dict': [1]}, 'bad_list_to_dict', dict),
    ({'bad_list_to_str': [1]}, 'bad_list_to_str', str),
    ({'bad_dict_to_list': {1: 2}}, 'bad_dict_to_list', list),
    ({'bad_str_to_int': 'not_an_int'}, 'bad_str_to_int', int),
    ({'bad_str_to_list': 'abc'}, 'bad_str_to_list', list),
])
def test_get_field_value_invalid(container, field_name, field_type):
    with pytest.raises(ValueError):
        validation_utils.get_field_value(container, field_name, field_type)


def test_validate_arg_regex():
    assert validation_utils.validate_arg_regex(
        'abc', re.compile('a[b]c')) == 'abc'
    with pytest.raises(argparse.ArgumentTypeError):
        validation_utils.validate_arg_regex('abc', re.compile('a[d]c'))


@pytest.mark.parametrize('arg, expected', [
    # Normal case, field present and correct type
    ('', {}),
    ('_A=1', {'_A': '1'}),
    ('_A=1,_B=2', {'_A': '1', '_B': '2'}),
    # Repeated key is ok
    ('_A=1,_A=2', {'_A': '2'}),
    # Extra = is ok
    ('_A=x=y=z,_B=2', {'_A': 'x=y=z', '_B': '2'}),
    # No value is ok
    ('_A=', {'_A': ''}),
])
def test_validate_arg_dicts_valid(arg, expected):
    assert validation_utils.validate_arg_dict(arg) == expected


@pytest.mark.parametrize('arg', [
    # No key
    ',_A',
    '_A,',
    # Invalid variable name
    '_Aa=1',
    '_aA=1',
    '0A=1',
])
def test_validate_arg_dicts_invalid(arg):
    with pytest.raises(argparse.ArgumentTypeError):
        validation_utils.validate_arg_dict(arg)


if __name__ == '__main__':
    pytest.main([__file__])
