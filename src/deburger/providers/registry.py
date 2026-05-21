"""Provider registry for plugin management."""

from typing import Dict, List, Optional
from deburger.providers.base import CloudProvider


class ProviderRegistry:
    """Registry for cloud provider plugins."""

    _providers: Dict[str, CloudProvider] = {}

    @classmethod
    def register(cls, provider: CloudProvider):
        """Register a cloud provider."""
        cls._providers[provider.name] = provider

    @classmethod
    def get(cls, name: str) -> Optional[CloudProvider]:
        """Get provider by name."""
        return cls._providers.get(name)

    @classmethod
    def list_providers(cls) -> List[str]:
        """List all registered providers."""
        return list(cls._providers.keys())

    @classmethod
    def get_all(cls) -> List[CloudProvider]:
        """Get all registered providers."""
        return list(cls._providers.values())
