"""Base classes for cloud provider plugins."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional, Any
from enum import Enum


class ResourceType(Enum):
    """Types of cloud resources."""
    LAMBDA = "lambda"
    DATABASE = "database"
    STORAGE = "storage"
    CONTAINER = "container"
    API_GATEWAY = "api_gateway"
    QUEUE = "queue"
    CDN = "cdn"
    DATA_TRANSFER = "data_transfer"


@dataclass
class Resource:
    """Represents a cloud resource."""
    type: ResourceType
    name: str
    region: str
    config: Dict[str, Any]

    # Usage metrics
    invocations: Optional[int] = None
    duration_ms: Optional[float] = None
    memory_mb: Optional[int] = None
    storage_gb: Optional[float] = None
    requests: Optional[int] = None


@dataclass
class Cost:
    """Cost breakdown for a resource."""
    resource_name: str
    resource_type: ResourceType

    # Cost components
    compute_cost: Decimal = Decimal("0")
    storage_cost: Decimal = Decimal("0")
    transfer_cost: Decimal = Decimal("0")
    request_cost: Decimal = Decimal("0")

    @property
    def total(self) -> Decimal:
        """Total cost."""
        return (
            self.compute_cost +
            self.storage_cost +
            self.transfer_cost +
            self.request_cost
        )

    currency: str = "USD"
    period: str = "monthly"


@dataclass
class PricingData:
    """Pricing data from cloud provider."""
    provider: str
    region: str
    resource_type: ResourceType
    prices: Dict[str, Decimal]
    updated_at: str


@dataclass
class Optimization:
    """Optimization suggestion."""
    title: str
    description: str
    original_code: str
    fixed_code: str
    savings_monthly: Decimal
    confidence: float  # 0.0 to 1.0
    auto_fixable: bool = False


class CloudProvider(ABC):
    """Abstract base class for cloud providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name: aws, gcp, azure"""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name"""
        pass

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]):
        """Initialize provider with configuration."""
        pass

    @abstractmethod
    async def calculate_cost(
        self,
        resource: Resource,
        traffic_estimate: Dict[str, int]
    ) -> Cost:
        """Calculate cost for a resource."""
        pass

    @abstractmethod
    async def get_pricing(
        self,
        region: str,
        resource_type: ResourceType
    ) -> PricingData:
        """Fetch pricing data from provider API."""
        pass

    @abstractmethod
    def optimize(self, resource: Resource, issue: Dict) -> Optional[Optimization]:
        """Generate optimization suggestion."""
        pass

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Check if credentials are valid."""
        pass
