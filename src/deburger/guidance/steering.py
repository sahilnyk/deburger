"""Steer AI back toward requirements when drifting."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GuidancePrompt:
    focus_area: str
    current_progress: float
    target_progress: float
    security_issues: list
    quality_score: float
    next_action: str
    reasoning: str


class AISteeringEngine:
    def __init__(self, requirement: str, guardrails: list[str]):
        self.requirement = requirement
        self.guardrails = guardrails

    def generate_guidance(
        self,
        current_progress: float,
        security_issues: list,
        quality_score: float,
        next_goal: Optional[str] = None,
    ) -> GuidancePrompt:
        """Generate actionable guidance for AI to follow."""

        focus_area = self._determine_focus(current_progress, security_issues, quality_score, next_goal)
        next_action = self._suggest_action(focus_area, security_issues)
        reasoning = self._explain_reasoning(focus_area, current_progress, security_issues)

        return GuidancePrompt(
            focus_area=focus_area,
            current_progress=current_progress,
            target_progress=min(current_progress + 0.15, 1.0),
            security_issues=security_issues,
            quality_score=quality_score,
            next_action=next_action,
            reasoning=reasoning,
        )

    def _determine_focus(
        self,
        progress: float,
        security_issues: list,
        quality_score: float,
        next_goal: Optional[str],
    ) -> str:
        if security_issues:
            high_severity = [v for v in security_issues if v.severity.value == "HIGH"]
            if high_severity:
                return "security_critical"
            return "security_improvements"

        if quality_score < 60:
            return "code_quality"

        if progress < 0.3:
            return "core_functionality"

        if next_goal:
            return next_goal

        if progress < 0.7:
            return "feature_completion"

        return "testing_and_polish"

    def _suggest_action(self, focus_area: str, security_issues: list) -> str:
        actions = {
            "security_critical": self._security_action(security_issues),
            "security_improvements": "Address remaining security issues before continuing",
            "code_quality": "Refactor to reduce complexity and improve maintainability",
            "core_functionality": "Implement essential features first",
            "feature_completion": "Complete remaining sub-goals",
            "testing_and_polish": "Add comprehensive tests and edge case handling",
        }

        return actions.get(focus_area, "Continue with current implementation")

    def _security_action(self, security_issues: list) -> str:
        if not security_issues:
            return "Continue"

        issue = security_issues[0]
        return f"Fix {issue.type}: {issue.fix_suggestion or issue.description}"

    def _explain_reasoning(self, focus_area: str, progress: float, security_issues: list) -> str:
        reasons = {
            "security_critical": f"High severity security issues block further development",
            "security_improvements": f"{len(security_issues)} security issues should be addressed",
            "code_quality": "Code quality below acceptable threshold",
            "core_functionality": f"At {progress:.0%} completion, focus on core features",
            "feature_completion": f"At {progress:.0%}, continue toward 100%",
            "testing_and_polish": "Core features complete, focus on quality",
        }

        return reasons.get(focus_area, "Continue development")

    def format_for_llm(self, guidance: GuidancePrompt) -> str:
        """Format guidance as LLM-ready prompt."""

        guardrails_text = "\n".join(f"- {g}" for g in self.guardrails)

        return f"""# Code Development Guidance

Requirement: {self.requirement}
Current Progress: {guidance.current_progress:.0%}
Target for Next Change: {guidance.target_progress:.0%}

## Current Status
- Code Quality Score: {guidance.quality_score:.0f}/100
- Security Issues: {len(guidance.security_issues)}
- Focus Area: {guidance.focus_area}

## Next Action
{guidance.next_action}

## Reasoning
{guidance.reasoning}

## Mandatory Guardrails
{guardrails_text}

## Instructions
1. Focus exclusively on: {guidance.focus_area}
2. {guidance.next_action}
3. Do not add features outside the current focus
4. Validate all user input
5. Follow security best practices

Write code that moves from {guidance.current_progress:.0%} to {guidance.target_progress:.0%} completion.
"""

    def check_guardrail_violations(self, code: str) -> list[str]:
        """Check if code violates any guardrails."""
        violations = []

        forbidden_patterns = {
            "eval(": "Code execution vulnerability",
            "exec(": "Code execution vulnerability",
            "shell=True": "Shell injection risk",
            "password = \"": "Hardcoded credential",
            "api_key = \"": "Hardcoded API key",
            ".format(": "Potential SQL injection if used in queries",
        }

        for pattern, reason in forbidden_patterns.items():
            if pattern in code:
                violations.append(f"Guardrail violation: {reason}")

        for guardrail in self.guardrails:
            if "never disable security" in guardrail.lower():
                if "security" in code and "False" in code:
                    violations.append("Attempting to disable security features")

        return violations
