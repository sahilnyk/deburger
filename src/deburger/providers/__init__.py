"""Cloud provider plugin system."""

from deburger.providers.base import CloudProvider, Resource, Cost, PricingData
from deburger.providers.registry import ProviderRegistry
from deburger.providers.aws_provider import AWSProvider
from deburger.providers.gcp_provider import GCPProvider
from deburger.providers.azure_provider import AzureProvider

# Auto-register providers
ProviderRegistry.register(AWSProvider())
ProviderRegistry.register(GCPProvider())
ProviderRegistry.register(AzureProvider())

__all__ = [
    "CloudProvider",
    "Resource",
    "Cost",
    "PricingData",
    "ProviderRegistry",
    "AWSProvider",
    "GCPProvider",
    "AzureProvider",
]
