"""Tests for cost engine."""

import asyncio
import pytest
from decimal import Decimal
from deburger.cost import CostEngine, TrafficEstimate
from deburger.providers import ProviderRegistry
from deburger.analyzers.base import Issue, IssueType, Severity


@pytest.fixture
def traffic():
    return TrafficEstimate(
        requests_per_day=100000,
        avg_duration_ms=1000,
        avg_memory_mb=1024,
        db_queries_per_request=10,
        concurrent_connections=100,
        data_transfer_gb=Decimal("100"),
    )


@pytest.fixture
def engine():
    provider = ProviderRegistry.get("aws")
    asyncio.run(provider.initialize({"region": "us-east-1"}))
    return CostEngine(provider, "us-east-1")


@pytest.fixture
def n_plus_one_issue():
    return Issue(
        type=IssueType.N_PLUS_ONE_QUERY,
        severity=Severity.CRITICAL,
        file_path="test.py",
        line_number=10,
        code_snippet="for item in items:\n    db.query(item.id)",
        estimated_monthly_cost=Decimal("300"),
        description="N+1 query",
        explanation="N+1 in loop",
        context={"estimated_iterations": 500},
    )


def test_calculate_n_plus_one_cost(engine, traffic, n_plus_one_issue):
    result = asyncio.run(engine.calculate_issue_cost(n_plus_one_issue, traffic))
    assert result.savings > 0
    assert result.current_cost > result.optimized_cost
    assert result.confidence == 0.85


def test_calculate_total_savings(engine, traffic, n_plus_one_issue):
    result = asyncio.run(engine.calculate_total_savings([n_plus_one_issue], traffic))
    assert result["total_savings"] > 0
    assert result["issues_count"] == 1
    assert result["savings_percentage"] > 0


def test_traffic_estimate_from_config():
    config = {
        "traffic": {
            "requests_per_day": 50000,
            "avg_duration_ms": 500,
            "avg_memory_mb": 512,
            "db_queries_per_request": 5,
            "concurrent_connections": 50,
            "data_transfer_gb": 50,
        }
    }
    traffic = TrafficEstimate.from_config(config)
    assert traffic.requests_per_day == 50000
    assert traffic.avg_duration_ms == 500


def test_empty_issues_returns_zero(engine, traffic):
    result = asyncio.run(engine.calculate_total_savings([], traffic))
    assert result["total_savings"] == 0
    assert result["savings_percentage"] == 0.0
