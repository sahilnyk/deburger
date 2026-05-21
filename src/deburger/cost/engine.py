"""Cost calculation engine - figures out how much your code actually costs."""

from decimal import Decimal
from typing import Dict, List, Optional
from dataclasses import dataclass

from deburger.analyzers.base import Issue, IssueType
from deburger.providers.base import CloudProvider, Resource, ResourceType
from deburger.cost.cache import PricingCache


@dataclass
class CostBreakdown:
    """What you're spending vs what you could be spending."""
    issue_id: str
    resource_type: ResourceType
    current_cost: Decimal
    optimized_cost: Decimal
    savings: Decimal
    confidence: float
    details: Dict[str, Decimal]
    period_days: int = 30


@dataclass
class TrafficEstimate:
    """How much traffic you're actually getting."""
    requests_per_day: int
    avg_duration_ms: int
    avg_memory_mb: int
    db_queries_per_request: int
    concurrent_connections: int
    data_transfer_gb: Decimal

    @classmethod
    def from_config(cls, config: dict) -> "TrafficEstimate":
        """Load from config file."""
        traffic = config.get("traffic", {})
        return cls(
            requests_per_day=traffic.get("requests_per_day", 100000),
            avg_duration_ms=traffic.get("avg_duration_ms", 1000),
            avg_memory_mb=traffic.get("avg_memory_mb", 1024),
            db_queries_per_request=traffic.get("db_queries_per_request", 10),
            concurrent_connections=traffic.get("concurrent_connections", 100),
            data_transfer_gb=Decimal(str(traffic.get("data_transfer_gb", 100)))
        )


class CostEngine:
    """Calculates real cloud costs using actual pricing data."""

    def __init__(self, provider: CloudProvider, region: str, cache: Optional[PricingCache] = None):
        self.provider = provider
        self.region = region
        self.cache = cache or PricingCache()
        self._pricing_preloaded = {}

    async def preload_pricing(self):
        """Preload all pricing data in parallel (one call per resource type)."""
        import asyncio

        resource_types = [
            ResourceType.LAMBDA,
            ResourceType.DATABASE,
            ResourceType.CACHE,
            ResourceType.STORAGE,
        ]

        tasks = [self._get_pricing(rt) for rt in resource_types]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Now all pricing is cached - subsequent calls will be instant

    async def calculate_issue_cost(
        self,
        issue: Issue,
        traffic: TrafficEstimate,
        resource_config: Optional[Dict] = None
    ) -> CostBreakdown:
        """Figure out how much this issue is costing you."""

        if issue.type == IssueType.N_PLUS_ONE_QUERY:
            return await self._cost_n_plus_one(issue, traffic, resource_config or {})
        elif issue.type == IssueType.SEQUENTIAL_ASYNC:
            return await self._cost_sequential_async(issue, traffic, resource_config or {})
        elif issue.type == IssueType.OVER_PROVISIONED_LAMBDA:
            return await self._cost_over_provisioned(issue, traffic, resource_config or {})
        elif issue.type == IssueType.MISSING_CACHING:
            return await self._cost_missing_cache(issue, traffic, resource_config or {})
        else:
            return self._estimate_generic(issue, traffic)

    async def _cost_n_plus_one(
        self,
        issue: Issue,
        traffic: TrafficEstimate,
        resource_config: Dict
    ) -> CostBreakdown:
        """Calculate cost for N+1 query hell."""

        iterations = self._guess_loop_iterations(issue)

        monthly_requests = traffic.requests_per_day * 30
        queries_per_request = iterations
        total_queries = monthly_requests * queries_per_request

        db_type = resource_config.get("database", {}).get("type", "rds")
        pricing = await self._get_pricing(ResourceType.DATABASE)

        io_cost_per_query = pricing.get("io_cost_per_operation", Decimal("0.0000002"))
        connection_overhead = pricing.get("connection_overhead", Decimal("0.00001"))

        current_cost = (
            Decimal(total_queries) * io_cost_per_query +
            Decimal(monthly_requests) * connection_overhead * Decimal(iterations)
        )

        # With fix: one bulk query per request
        optimized_queries = monthly_requests
        optimized_cost = Decimal(optimized_queries) * io_cost_per_query

        savings = current_cost - optimized_cost

        return CostBreakdown(
            issue_id=f"{issue.file_path}:{issue.line_number}",
            resource_type=ResourceType.DATABASE,
            current_cost=current_cost,
            optimized_cost=optimized_cost,
            savings=savings,
            confidence=0.85,
            details={
                "io_operations": current_cost - (Decimal(monthly_requests) * connection_overhead * Decimal(iterations)),
                "connection_overhead": Decimal(monthly_requests) * connection_overhead * Decimal(iterations),
                "optimized_io": optimized_cost
            }
        )

    async def _cost_sequential_async(
        self,
        issue: Issue,
        traffic: TrafficEstimate,
        resource_config: Dict
    ) -> CostBreakdown:
        """Calculate cost for sequential async operations."""

        await_count = issue.context.get("await_count", 2)
        monthly_requests = traffic.requests_per_day * 30

        # Sequential: everything waits in line
        sequential_time_ms = traffic.avg_duration_ms * await_count

        # Parallel: everything runs at once (with some overhead)
        parallel_time_ms = int(traffic.avg_duration_ms * 1.2)

        wasted_ms = sequential_time_ms - parallel_time_ms
        wasted_seconds = Decimal(wasted_ms) / Decimal(1000)

        pricing = await self._get_pricing(ResourceType.LAMBDA)

        memory_gb = Decimal(traffic.avg_memory_mb) / Decimal(1024)
        gb_second_cost = pricing.get("gb_second_cost", Decimal("0.0000166667"))

        wasted_gb_seconds = Decimal(monthly_requests) * memory_gb * wasted_seconds
        savings = wasted_gb_seconds * gb_second_cost

        current_cost = Decimal(monthly_requests) * memory_gb * Decimal(sequential_time_ms) / Decimal(1000) * gb_second_cost
        optimized_cost = Decimal(monthly_requests) * memory_gb * Decimal(parallel_time_ms) / Decimal(1000) * gb_second_cost

        return CostBreakdown(
            issue_id=f"{issue.file_path}:{issue.line_number}",
            resource_type=ResourceType.LAMBDA,
            current_cost=current_cost,
            optimized_cost=optimized_cost,
            savings=savings,
            confidence=0.90,
            details={
                "sequential_compute": current_cost,
                "parallel_compute": optimized_cost,
                "wasted_time_ms": wasted_ms
            }
        )

    async def _cost_over_provisioned(
        self,
        issue: Issue,
        traffic: TrafficEstimate,
        resource_config: Dict
    ) -> CostBreakdown:
        """Calculate cost for over-provisioned resources."""

        current_memory = resource_config.get("memory_mb", traffic.avg_memory_mb)
        optimal_memory = int(current_memory * 0.6)

        monthly_requests = traffic.requests_per_day * 30
        duration_seconds = Decimal(traffic.avg_duration_ms) / Decimal(1000)

        pricing = await self._get_pricing(ResourceType.LAMBDA)
        gb_second_cost = pricing.get("gb_second_cost", Decimal("0.0000166667"))

        current_gb = Decimal(current_memory) / Decimal(1024)
        current_cost = Decimal(monthly_requests) * current_gb * duration_seconds * gb_second_cost

        optimal_gb = Decimal(optimal_memory) / Decimal(1024)
        optimized_cost = Decimal(monthly_requests) * optimal_gb * duration_seconds * gb_second_cost

        savings = current_cost - optimized_cost

        return CostBreakdown(
            issue_id=f"{issue.file_path}:{issue.line_number}",
            resource_type=ResourceType.LAMBDA,
            current_cost=current_cost,
            optimized_cost=optimized_cost,
            savings=savings,
            confidence=0.75,
            details={
                "current_memory_mb": current_memory,
                "optimal_memory_mb": optimal_memory,
                "current_cost": current_cost,
                "optimal_cost": optimized_cost
            }
        )

    async def _cost_missing_cache(
        self,
        issue: Issue,
        traffic: TrafficEstimate,
        resource_config: Dict
    ) -> CostBreakdown:
        """Calculate savings from adding caching."""

        cache_hit_rate = Decimal("0.80")
        monthly_requests = traffic.requests_per_day * 30

        pricing = await self._get_pricing(ResourceType.DATABASE)
        query_cost = pricing.get("io_cost_per_operation", Decimal("0.0000002"))

        current_cost = Decimal(monthly_requests) * query_cost * Decimal(traffic.db_queries_per_request)

        # With cache: only misses hit the database
        cache_misses = Decimal(monthly_requests) * (Decimal("1.0") - cache_hit_rate)
        db_cost_with_cache = cache_misses * query_cost * Decimal(traffic.db_queries_per_request)

        cache_pricing = await self._get_pricing(ResourceType.CACHE)
        cache_monthly_cost = cache_pricing.get("monthly_cost", Decimal("50"))

        optimized_cost = db_cost_with_cache + cache_monthly_cost
        savings = current_cost - optimized_cost

        return CostBreakdown(
            issue_id=f"{issue.file_path}:{issue.line_number}",
            resource_type=ResourceType.CACHE,
            current_cost=current_cost,
            optimized_cost=optimized_cost,
            savings=savings,
            confidence=0.70,
            details={
                "db_cost_no_cache": current_cost,
                "db_cost_with_cache": db_cost_with_cache,
                "cache_service_cost": cache_monthly_cost,
                "cache_hit_rate": float(cache_hit_rate)
            }
        )

    def _estimate_generic(self, issue: Issue, traffic: TrafficEstimate) -> CostBreakdown:
        """Fallback for unknown issue types."""
        estimated_cost = issue.estimated_monthly_cost or Decimal("0")
        savings = issue.savings_monthly or Decimal("0")

        return CostBreakdown(
            issue_id=f"{issue.file_path}:{issue.line_number}",
            resource_type=ResourceType.OTHER,
            current_cost=estimated_cost,
            optimized_cost=estimated_cost - savings,
            savings=savings,
            confidence=0.50,
            details={"estimated": estimated_cost}
        )

    def _guess_loop_iterations(self, issue: Issue) -> int:
        """Guess how many times a loop runs."""
        if "estimated_iterations" in issue.context:
            return issue.context["estimated_iterations"]

        code = issue.code_snippet.lower()

        if "pagination" in code or "page" in code:
            return 50
        elif "batch" in code:
            return 100
        elif "limit" in code:
            import re
            match = re.search(r'limit\s*=\s*(\d+)', code)
            if match:
                return int(match.group(1))

        return 500

    async def _get_pricing(self, resource_type: ResourceType) -> Dict[str, Decimal]:
        """Get pricing data from cache or provider."""
        cache_key = f"{self.provider.name}:{self.region}:{resource_type.value}"

        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        pricing = await self.provider.get_pricing(self.region, resource_type)

        pricing_dict = {
            "gb_second_cost": pricing.gb_second_cost if hasattr(pricing, 'gb_second_cost') else Decimal("0"),
            "io_cost_per_operation": pricing.io_cost if hasattr(pricing, 'io_cost') else Decimal("0.0000002"),
            "request_cost": pricing.request_cost if hasattr(pricing, 'request_cost') else Decimal("0.0000002"),
            "connection_overhead": Decimal("0.00001"),
            "monthly_cost": Decimal("50")
        }

        await self.cache.set(cache_key, pricing_dict, ttl=86400)
        return pricing_dict

    async def calculate_total_savings(self, issues: List[Issue], traffic: TrafficEstimate) -> Dict:
        """Calculate total savings across all issues (runs in parallel for speed)."""
        import asyncio

        # Process all issues concurrently for max speed
        tasks = [self.calculate_issue_cost(issue, traffic) for issue in issues]
        breakdowns = await asyncio.gather(*tasks)

        total_savings = sum(b.savings for b in breakdowns)
        total_current = sum(b.current_cost for b in breakdowns)
        total_optimized = sum(b.optimized_cost for b in breakdowns)

        by_resource = {}
        for breakdown in breakdowns:
            rt = breakdown.resource_type.value
            if rt not in by_resource:
                by_resource[rt] = {"count": 0, "savings": Decimal("0")}
            by_resource[rt]["count"] += 1
            by_resource[rt]["savings"] += breakdown.savings

        return {
            "total_current_cost": total_current,
            "total_optimized_cost": total_optimized,
            "total_savings": total_savings,
            "savings_percentage": float((total_savings / total_current * 100) if total_current > 0 else 0),
            "issues_count": len(issues),
            "breakdowns": breakdowns,
            "by_resource_type": by_resource,
            "period_days": 30
        }
