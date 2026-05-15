"""Tests for error parser."""

import pytest
from deburger.core.parser import ErrorParser


@pytest.fixture
def parser():
    return ErrorParser()


@pytest.fixture
def sample_traceback():
    return '''
Traceback (most recent call last):
  File "/home/user/project/test_math.py", line 10, in test_divide
    result = divide(10, 0)
  File "/home/user/project/math_utils.py", line 5, in divide
    return a / b
ZeroDivisionError: division by zero
'''


@pytest.fixture
def sample_type_error():
    return '''
Traceback (most recent call last):
  File "/home/user/project/test_api.py", line 25, in test_get_user
    data = get_user("123")
  File "/home/user/project/api.py", line 15, in get_user
    return users[user_id]
TypeError: list indices must be integers or slices, not str
'''


def test_parse_basic_error(parser, sample_traceback):
    """Test parsing a basic ZeroDivisionError."""
    error = parser.parse(sample_traceback)

    assert error is not None
    assert error.error_type == "ZeroDivisionError"
    assert error.message == "division by zero"
    assert error.file_path == "/home/user/project/math_utils.py"
    assert error.line_number == 5
    assert error.function_name == "divide"
    assert len(error.traceback) == 2


def test_parse_type_error(parser, sample_type_error):
    """Test parsing a TypeError."""
    error = parser.parse(sample_type_error)

    assert error is not None
    assert error.error_type == "TypeError"
    assert "list indices must be integers" in error.message
    assert error.file_path == "/home/user/project/api.py"
    assert error.line_number == 15
    assert error.function_name == "get_user"


def test_parse_invalid_traceback(parser):
    """Test parsing invalid input returns None."""
    error = parser.parse("not a traceback")
    assert error is None


def test_parse_empty_string(parser):
    """Test parsing empty string returns None."""
    error = parser.parse("")
    assert error is None


def test_error_hash_generation(parser, sample_traceback):
    """Test error hash is generated correctly."""
    error = parser.parse(sample_traceback)

    assert error is not None
    assert len(error.error_hash) == 64  # SHA256 hex digest
    assert len(error.short_hash) == 8


def test_error_hash_consistency(parser, sample_traceback):
    """Test same error produces same hash."""
    error1 = parser.parse(sample_traceback)
    error2 = parser.parse(sample_traceback)

    assert error1.error_hash == error2.error_hash


def test_traceback_frames(parser, sample_traceback):
    """Test all traceback frames are extracted."""
    error = parser.parse(sample_traceback)

    assert error is not None
    assert len(error.traceback) == 2

    # First frame
    frame1 = error.traceback[0]
    assert frame1.file_path == "/home/user/project/test_math.py"
    assert frame1.line_number == 10
    assert frame1.function_name == "test_divide"
    assert "divide(10, 0)" in frame1.code_line

    # Second frame
    frame2 = error.traceback[1]
    assert frame2.file_path == "/home/user/project/math_utils.py"
    assert frame2.line_number == 5
    assert frame2.function_name == "divide"


def test_parse_multiple_errors(parser):
    """Test parsing output with multiple failures."""
    output = '''
FAILED test_one.py::test_a - ZeroDivisionError
Traceback (most recent call last):
  File "test_one.py", line 5, in test_a
    x = 1/0
ZeroDivisionError: division by zero

FAILED test_two.py::test_b - KeyError
Traceback (most recent call last):
  File "test_two.py", line 10, in test_b
    y = data["key"]
KeyError: 'key'
'''

    errors = parser.parse_multiple(output)

    assert len(errors) == 2
    assert errors[0].error_type == "ZeroDivisionError"
    assert errors[1].error_type == "KeyError"
