"""Tests for revision-aware issue comparison."""

from unittest.mock import patch

from deburger.integrations.git_diff import added_issues, parse_revision_range


def test_parses_compact_revision_range():
    assert parse_revision_range("main..feature", "HEAD") == ("main", "feature")


def test_keeps_separate_revision_arguments():
    assert parse_revision_range("main", "release") == ("main", "release")


def test_reports_only_added_issues():
    base_code = "value = 1\n"
    head_code = "for item in items:\n    result = db.query(item.id)\n"
    config = {
        "detect": {"n_plus_one_queries": True, "sequential_async": True},
        "traffic": {"requests_per_day": 100},
    }

    with patch(
        "deburger.integrations.git_diff.changed_files",
        return_value=["app.py"],
    ), patch(
        "deburger.integrations.git_diff.read_file",
        side_effect=[base_code, head_code],
    ):
        issues = added_issues("main", "feature", config)

    assert len(issues) == 1
    assert issues[0].file_path == "app.py"


def test_ignores_unchanged_issues():
    code = "for item in items:\n    result = db.query(item.id)\n"
    config = {
        "detect": {"n_plus_one_queries": True, "sequential_async": True},
        "traffic": {"requests_per_day": 100},
    }

    with patch(
        "deburger.integrations.git_diff.changed_files",
        return_value=["app.py"],
    ), patch(
        "deburger.integrations.git_diff.read_file",
        side_effect=[code, code],
    ):
        issues = added_issues("main", "feature", config)

    assert issues == []
