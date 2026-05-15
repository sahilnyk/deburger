"""Error classification logic."""

from deburger.models.error import ErrorInfo, ErrorClassification


class ErrorClassifier:
    """Classify errors by complexity and category."""

    # Simple errors that are usually easy to fix
    LOW_COMPLEXITY_ERRORS = {
        "NameError",
        "AttributeError",
        "ImportError",
        "ModuleNotFoundError",
        "IndentationError",
        "SyntaxError",
    }

    # Medium complexity errors
    MEDIUM_COMPLEXITY_ERRORS = {
        "TypeError",
        "ValueError",
        "KeyError",
        "IndexError",
        "ZeroDivisionError",
        "FileNotFoundError",
        "AssertionError",
    }

    # Categories for better fix generation
    ERROR_CATEGORIES = {
        "NameError": "undefined_variable",
        "AttributeError": "missing_attribute",
        "ImportError": "import_error",
        "ModuleNotFoundError": "import_error",
        "TypeError": "type_mismatch",
        "ValueError": "invalid_value",
        "KeyError": "missing_key",
        "IndexError": "index_out_of_range",
        "ZeroDivisionError": "division_by_zero",
        "FileNotFoundError": "file_not_found",
        "AssertionError": "assertion_failed",
    }

    def classify(self, error: ErrorInfo) -> ErrorClassification:
        """
        Classify an error by complexity and category.

        Args:
            error: The error to classify

        Returns:
            Classification metadata
        """
        error_type = error.error_type

        # Determine complexity
        if error_type in self.LOW_COMPLEXITY_ERRORS:
            complexity = "low"
            confidence = 0.9
        elif error_type in self.MEDIUM_COMPLEXITY_ERRORS:
            complexity = "medium"
            confidence = 0.75
        else:
            complexity = "high"
            confidence = 0.6

        # Determine category
        category = self.ERROR_CATEGORIES.get(error_type, "unknown")

        return ErrorClassification(
            complexity=complexity,
            category=category,
            confidence=confidence,
        )
