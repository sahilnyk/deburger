"""Tests for requirement tracker."""

import pytest
from unittest.mock import Mock

from deburger.requirements.tracker import RequirementTracker, Requirement, SubGoal


def test_track_progress_with_matching_keywords():
    req = Requirement(
        description="Build API with authentication",
        sub_goals=[
            SubGoal(id="api", description="Create API endpoints", weight=50),
            SubGoal(id="auth", description="Add JWT authentication", weight=50),
        ],
    )

    tracker = RequirementTracker(req)

    change = Mock()
    change.file_path = "api.py"

    tracker._get_change_content = lambda c: """
def login():
    token = jwt.encode(payload, secret)
    return token

@app.route('/api/users')
def get_users():
    return users
"""

    progress = tracker.calculate_progress([change])

    assert progress > 0.0
    assert progress <= 1.0


def test_empty_changes_zero_progress():
    req = Requirement(
        description="Build system",
        sub_goals=[SubGoal(id="core", description="Core functionality", weight=100)],
    )

    tracker = RequirementTracker(req)
    progress = tracker.calculate_progress([])

    assert progress == 0.0


def test_get_next_focus():
    req = Requirement(
        description="Build system",
        sub_goals=[
            SubGoal(id="done", description="Completed", weight=50, completion=1.0),
            SubGoal(id="partial", description="In progress", weight=30, completion=0.5),
            SubGoal(id="todo", description="Not started", weight=20, completion=0.0),
        ],
    )

    tracker = RequirementTracker(req)
    next_goal = tracker.get_next_focus()

    assert next_goal is not None
    assert next_goal.id == "todo"


def test_all_complete_no_next_focus():
    req = Requirement(
        description="Build system",
        sub_goals=[
            SubGoal(id="done1", description="Task 1", weight=50, completion=1.0),
            SubGoal(id="done2", description="Task 2", weight=50, completion=0.95),
        ],
    )

    tracker = RequirementTracker(req)
    next_goal = tracker.get_next_focus()

    assert next_goal is None
