"""Tests for calculator (some will fail to demonstrate deburger)."""

import pytest
from calculator import add, subtract, multiply, divide, get_value_from_dict, process_list


def test_add():
    """Test addition - should pass."""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_subtract():
    """Test subtraction - should pass."""
    assert subtract(5, 3) == 2
    assert subtract(0, 5) == -5


def test_multiply():
    """Test multiplication - should pass."""
    assert multiply(3, 4) == 12
    assert multiply(-2, 3) == -6


def test_divide():
    """Test division - will fail with ZeroDivisionError."""
    assert divide(10, 2) == 5
    assert divide(6, 0) == 0  # This will fail!


def test_get_value():
    """Test dictionary access - will fail with KeyError."""
    data = {"name": "John", "age": 30}
    assert get_value_from_dict(data, "name") == "John"
    assert get_value_from_dict(data, "email") == "test@example.com"  # This will fail!


def test_process_list():
    """Test list processing - will fail with IndexError."""
    items = [1, 2, 3]
    result = process_list(items)  # This will fail!
    assert result == 1
