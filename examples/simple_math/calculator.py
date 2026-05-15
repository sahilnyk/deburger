"""Simple calculator with intentional bugs for testing deburger."""


def add(a, b):
    """Add two numbers."""
    return a + b


def subtract(a, b):
    """Subtract two numbers."""
    return a - b


def multiply(a, b):
    """Multiply two numbers."""
    return a * b


def divide(a, b):
    """Divide two numbers."""
    # Bug: No zero division check
    return a / b


def get_value_from_dict(data, key):
    """Get value from dictionary."""
    # Bug: No key existence check
    return data[key]


def process_list(items):
    """Process a list of items."""
    # Bug: Index out of range
    return items[10]
