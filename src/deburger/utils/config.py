"""Configuration loading and validation."""

import os
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class SubGoalConfig:
    """Sub-goal configuration."""

    id: str
    description: str
    weight: int
    keywords: List[str] = field(default_factory=list)


@dataclass
class LLMConfig:
    """LLM provider configuration."""

    provider: str = "openai"
    api_key: Optional[str] = None
    model: str = "gpt-4"
    guardrails: List[str] = field(default_factory=list)


@dataclass
class SecurityConfig:
    """Security scanning configuration."""

    enabled: bool = True
    fail_on_high: bool = True
    fail_on_critical: bool = True
    ignore_patterns: List[str] = field(default_factory=list)
    custom_patterns: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricsConfig:
    """Code quality metrics configuration."""

    min_quality_score: int = 70
    max_complexity: int = 10
    min_test_coverage: int = 0


@dataclass
class DeburgerConfig:
    """Complete deburger configuration."""

    requirement: str
    sub_goals: List[SubGoalConfig]
    llm: LLMConfig
    security: SecurityConfig
    metrics: MetricsConfig
    project_root: Path = field(default_factory=Path.cwd)

    @classmethod
    def load(cls, config_path: str = ".deburger.yml") -> "DeburgerConfig":
        """Load configuration from YAML file."""
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Config file not found: {config_path}\n"
                "Run 'deburger init' to create configuration"
            )

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        # Parse sub-goals
        sub_goals = []
        for sg_data in data.get("sub_goals", []):
            sub_goals.append(
                SubGoalConfig(
                    id=sg_data["id"],
                    description=sg_data["description"],
                    weight=sg_data.get("weight", 10),
                    keywords=sg_data.get("keywords", []),
                )
            )

        # Parse LLM config
        llm_data = data.get("llm", {})
        api_key = llm_data.get("api_key", "")

        # Expand environment variables
        if api_key and api_key.startswith("${") and api_key.endswith("}"):
            env_var = api_key[2:-1]
            api_key = os.getenv(env_var)

        llm = LLMConfig(
            provider=llm_data.get("provider", "openai"),
            api_key=api_key,
            model=llm_data.get("model", "gpt-4"),
            guardrails=llm_data.get("guardrails", []),
        )

        # Parse security config
        security_data = data.get("security", {})
        security = SecurityConfig(
            enabled=security_data.get("enabled", True),
            fail_on_high=security_data.get("fail_on_high", True),
            fail_on_critical=security_data.get("fail_on_critical", True),
            ignore_patterns=security_data.get("ignore_patterns", []),
            custom_patterns=security_data.get("custom_patterns", {}),
        )

        # Parse metrics config
        metrics_data = data.get("metrics", {})
        metrics = MetricsConfig(
            min_quality_score=metrics_data.get("min_quality_score", 70),
            max_complexity=metrics_data.get("max_complexity", 10),
            min_test_coverage=metrics_data.get("min_test_coverage", 0),
        )

        return cls(
            requirement=data.get("requirement", "No requirement specified"),
            sub_goals=sub_goals,
            llm=llm,
            security=security,
            metrics=metrics,
            project_root=path.parent,
        )

    def save(self, config_path: str = ".deburger.yml"):
        """Save configuration to YAML file."""
        data = {
            "requirement": self.requirement,
            "sub_goals": [
                {
                    "id": sg.id,
                    "description": sg.description,
                    "weight": sg.weight,
                    "keywords": sg.keywords,
                }
                for sg in self.sub_goals
            ],
            "llm": {
                "provider": self.llm.provider,
                "api_key": f"${{{self.llm.provider.upper()}_API_KEY}}",
                "model": self.llm.model,
                "guardrails": self.llm.guardrails,
            },
            "security": {
                "enabled": self.security.enabled,
                "fail_on_high": self.security.fail_on_high,
                "fail_on_critical": self.security.fail_on_critical,
                "ignore_patterns": self.security.ignore_patterns,
            },
            "metrics": {
                "min_quality_score": self.metrics.min_quality_score,
                "max_complexity": self.metrics.max_complexity,
                "min_test_coverage": self.metrics.min_test_coverage,
            },
        }

        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []

        if not self.requirement:
            errors.append("Requirement is required")

        if not self.sub_goals:
            errors.append("At least one sub-goal is required")

        total_weight = sum(sg.weight for sg in self.sub_goals)
        if total_weight != 100:
            errors.append(f"Sub-goal weights must sum to 100 (current: {total_weight})")

        if self.metrics.min_quality_score < 0 or self.metrics.min_quality_score > 100:
            errors.append("min_quality_score must be between 0 and 100")

        return errors


def load_config(config_path: str = ".deburger.yml") -> DeburgerConfig:
    """Load configuration from file."""
    return DeburgerConfig.load(config_path)
