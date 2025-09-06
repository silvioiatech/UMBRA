"""
Compatibility shim for legacy imports of umbra.modules.core

This module provides backward compatibility for code that expects to import
from umbra.modules.core. It re-exports the core infrastructure from umbra.core
to maintain compatibility without requiring sweeping refactors.

Usage:
    from umbra.modules.core import config, UmbraConfig, PermissionManager
    
This is equivalent to:
    from umbra.core import config, UmbraConfig, PermissionManager
"""

# Re-export everything from umbra.core for backward compatibility
from umbra.core import *
from umbra.core import __all__ as _core_all

# Explicitly re-export the main items  
from umbra.core import (
    config,
    UmbraConfig, 
    PermissionManager,
    setup_logging,
    get_logger
)

# Make sure __all__ includes everything from core
__all__ = _core_all

# For debugging/introspection - indicate this is a compatibility shim
__compatibility_shim__ = True
__shim_target__ = "umbra.core"