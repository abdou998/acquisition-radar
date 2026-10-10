"""
Adapters package for Acquisition Radar.
"""

from radar.adapters.registry import registry, AdapterRegistry
from radar.adapters.base import BaseMarketplaceAdapter

__all__ = ["registry", "AdapterRegistry", "BaseMarketplaceAdapter"]
