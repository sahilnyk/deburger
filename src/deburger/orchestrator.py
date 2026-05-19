"""Main orchestrator for deburger workflow."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from deburger.analyzer.diff_analyzer import DiffAnalyzer
from deburger.security.scanner import SecurityScanner
from deburger.metrics.calculator import MetricsCalculator
from deburger.requirements.tracker import RequirementTracker, Requirement
from deburger.guidance.steering import AISteeringEngine


@dataclass
class AnalysisResult:
    requirement_progress: float
    security_issues: list
    quality_score: float
    files_changed: int
    lines_added: int
    lines_removed: int
    guidance: Optional[str] = None


class DeburgerOrchestrator:
    """Orchestrate full deburger analysis workflow."""

    def __init__(
        self,
        requirement: Requirement,
        guardrails: list[str],
        repo_path: Optional[Path] = None,
    ):
        self.requirement = requirement
        self.guardrails = guardrails
        self.repo_path = repo_path or Path.cwd()

        self.analyzer = DiffAnalyzer(repo_path)
        self.scanner = SecurityScanner()
        self.metrics_calc = MetricsCalculator()
        self.tracker = RequirementTracker(requirement)
        self.steering = AISteeringEngine(requirement.description, guardrails)

    def analyze_changes(self, since: str = "HEAD~1") -> AnalysisResult:
        """Run full analysis on code changes."""

        changes = self.analyzer.get_changes(since)

        if not changes:
            return self._empty_result()

        progress = self.tracker.calculate_progress(changes)

        all_vulns = []
        total_quality = 0.0
        quality_count = 0

        for change in changes:
            try:
                content = self.analyzer.get_file_content(change.file_path)

                vulns = self.scanner.scan_file(change.file_path, content)
                all_vulns.extend(vulns)

                if change.file_path.endswith(".py"):
                    metrics = self.metrics_calc.calculate(change.file_path, content)
                    total_quality += metrics.overall_score
                    quality_count += 1

            except Exception:
                pass

        avg_quality = total_quality / quality_count if quality_count > 0 else 0.0

        next_goal = self.tracker.get_next_focus()
        guidance_prompt = self.steering.generate_guidance(
            current_progress=progress,
            security_issues=all_vulns,
            quality_score=avg_quality,
            next_goal=next_goal.description if next_goal else None,
        )

        guidance_text = self.steering.format_for_llm(guidance_prompt)

        total_added = sum(c.lines_added for c in changes)
        total_removed = sum(c.lines_removed for c in changes)

        return AnalysisResult(
            requirement_progress=progress,
            security_issues=all_vulns,
            quality_score=avg_quality,
            files_changed=len(changes),
            lines_added=total_added,
            lines_removed=total_removed,
            guidance=guidance_text,
        )

    def check_code_before_commit(self, code: str) -> tuple[bool, list[str]]:
        """Validate code before allowing commit."""

        violations = self.steering.check_guardrail_violations(code)

        if violations:
            return False, violations

        return True, []

    def _empty_result(self) -> AnalysisResult:
        return AnalysisResult(
            requirement_progress=0.0,
            security_issues=[],
            quality_score=0.0,
            files_changed=0,
            lines_added=0,
            lines_removed=0,
            guidance=None,
        )
