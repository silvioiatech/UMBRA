"""
AI provider interfaces and implementations.
"""

from .openrouter import OpenRouterProvider, ModelRole

# Legacy alias for compatibility
OpenRouterClient = OpenRouterProvider

__all__ = ["OpenRouterProvider", "OpenRouterClient", "ModelRole"]
