"""Tests for cloud providers."""

import asyncio
import pytest
from decimal import Decimal
from deburger.providers import ProviderRegistry, AWSProvider, GCPProvider, AzureProvider
from deburger.providers.base import Resource, ResourceType


class TestProviderRegistry:
    def test_all_providers_registered(self):
        names = ProviderRegistry.list_providers()
        assert "aws" in names
        assert "gcp" in names
        assert "azure" in names

    def test_get_by_name(self):
        assert isinstance(ProviderRegistry.get("aws"), AWSProvider)
        assert isinstance(ProviderRegistry.get("gcp"), GCPProvider)
        assert isinstance(ProviderRegistry.get("azure"), AzureProvider)

    def test_get_unknown_returns_none(self):
        assert ProviderRegistry.get("unknown") is None


class TestAWSProvider:
    @pytest.fixture
    def provider(self):
        p = AWSProvider()
        asyncio.run(p.initialize({"region": "us-east-1"}))
        return p

    def test_lambda_pricing(self, provider):
        pricing = asyncio.run(provider.get_pricing("us-east-1", ResourceType.LAMBDA))
        assert pricing.gb_second_cost == Decimal("0.0000166667")
        assert pricing.request_cost == Decimal("0.0000002")

    def test_database_pricing(self, provider):
        pricing = asyncio.run(provider.get_pricing("us-east-1", ResourceType.DATABASE))
        assert pricing.io_cost == Decimal("0.0000002")

    def test_calculate_lambda_cost(self, provider):
        resource = Resource(
            type=ResourceType.LAMBDA,
            name="my-func",
            region="us-east-1",
            config={},
            memory_mb=1024,
            duration_ms=1000,
        )
        cost = asyncio.run(provider.calculate_cost(resource, {"requests_per_day": 100000}))
        assert cost.total > 0


class TestGCPProvider:
    def test_lambda_pricing(self):
        p = GCPProvider()
        asyncio.run(p.initialize({"region": "us-central1"}))
        pricing = asyncio.run(p.get_pricing("us-central1", ResourceType.LAMBDA))
        assert pricing.gb_second_cost == Decimal("0.0000025")


class TestAzureProvider:
    def test_lambda_pricing(self):
        p = AzureProvider()
        asyncio.run(p.initialize({"region": "eastus"}))
        pricing = asyncio.run(p.get_pricing("eastus", ResourceType.LAMBDA))
        assert pricing.gb_second_cost == Decimal("0.000016")
