"""Tests for pricing cache."""

import asyncio
import pytest
from decimal import Decimal
from deburger.cost.cache import PricingCache


@pytest.fixture
def cache(tmp_path):
    return PricingCache(cache_dir=tmp_path)


def test_set_and_get(cache):
    data = {"gb_second_cost": Decimal("0.0000166667"), "request_cost": Decimal("0.0000002")}
    asyncio.run(cache.set("aws:us-east-1:lambda", data))
    result = asyncio.run(cache.get("aws:us-east-1:lambda"))
    assert result["gb_second_cost"] == Decimal("0.0000166667")
    assert result["request_cost"] == Decimal("0.0000002")


def test_get_missing_key(cache):
    result = asyncio.run(cache.get("nonexistent"))
    assert result is None


def test_expired_entry_returns_none(cache):
    data = {"cost": Decimal("1.0")}
    asyncio.run(cache.set("key", data, ttl=-1))
    result = asyncio.run(cache.get("key"))
    assert result is None


def test_clear_all(cache):
    asyncio.run(cache.set("k1", {"a": Decimal("1")}))
    asyncio.run(cache.set("k2", {"b": Decimal("2")}))
    asyncio.run(cache.clear_all())
    assert asyncio.run(cache.get("k1")) is None
    assert asyncio.run(cache.get("k2")) is None


def test_overwrite_existing(cache):
    asyncio.run(cache.set("key", {"v": Decimal("1")}))
    asyncio.run(cache.set("key", {"v": Decimal("99")}))
    result = asyncio.run(cache.get("key"))
    assert result["v"] == Decimal("99")
