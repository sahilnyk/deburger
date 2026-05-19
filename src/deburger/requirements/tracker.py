"""Track requirement completion and progress."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SubGoal:
    id: str
    description: str
    weight: int
    completion: float = 0.0
    evidence: list[str] = None

    def __post_init__(self):
        if self.evidence is None:
            self.evidence = []


@dataclass
class Requirement:
    description: str
    sub_goals: list[SubGoal]
    overall_completion: float = 0.0


class RequirementTracker:
    def __init__(self, requirement: Requirement):
        self.requirement = requirement

    def calculate_progress(self, changes: list) -> float:
        total_score = 0.0
        total_weight = sum(g.weight for g in self.requirement.sub_goals)

        for goal in self.requirement.sub_goals:
            completion = self._assess_goal(goal, changes)
            goal.completion = completion
            total_score += completion * goal.weight

        self.requirement.overall_completion = total_score / total_weight if total_weight > 0 else 0
        return self.requirement.overall_completion

    def _assess_goal(self, goal: SubGoal, changes: list) -> float:
        keywords = self._extract_keywords(goal.description)
        matches = 0
        total_checks = len(keywords)

        if total_checks == 0:
            return 0.0

        for change in changes:
            content = self._get_change_content(change)
            for keyword in keywords:
                if self._keyword_present(keyword, content):
                    matches += 1
                    goal.evidence.append(f"{change.file_path}: {keyword}")
                    break

        return min(matches / total_checks, 1.0)

    def _extract_keywords(self, description: str) -> list[str]:
        desc_lower = description.lower()
        keywords = []

        if "endpoint" in desc_lower or "api" in desc_lower:
            keywords.extend(["@app.route", "def ", "return "])
        if "auth" in desc_lower or "jwt" in desc_lower:
            keywords.extend(["jwt", "token", "authenticate"])
        if "validation" in desc_lower:
            keywords.extend(["validate", "validator", "schema"])
        if "test" in desc_lower:
            keywords.extend(["def test_", "assert ", "pytest"])
        if "database" in desc_lower or "db" in desc_lower:
            keywords.extend(["db.", "session", "query"])

        return keywords

    def _keyword_present(self, keyword: str, content: str) -> bool:
        return keyword.lower() in content.lower()

    def _get_change_content(self, change) -> str:
        try:
            with open(change.file_path) as f:
                return f.read()
        except Exception:
            return ""

    def get_next_focus(self) -> Optional[SubGoal]:
        incomplete = [g for g in self.requirement.sub_goals if g.completion < 0.9]
        return min(incomplete, key=lambda g: g.completion) if incomplete else None
