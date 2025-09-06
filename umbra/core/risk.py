"""
Risk classification system for UMBRA core.
Re-exports risk levels from the concierge module for compatibility.
"""

# Re-export RiskLevel from concierge module for backward compatibility
from ..modules.concierge.risk import RiskLevel, RiskPattern, RiskClassifier

# Export for compatibility
__all__ = ["RiskLevel", "RiskPattern", "RiskClassifier"]