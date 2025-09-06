"""
Compatibility shim for legacy imports of umbra.modules.core

This module provides backward compatibility for code that expects to import
from umbra.modules.core. It re-exports the core infrastructure from umbra.core
to maintain compatibility without requiring sweeping refactors.

Usage:
    from umbra.modules.core import config, UmbraConfig, PermissionManager
    from umbra.modules.core import envelope, module_base, logger
    
This is equivalent to:
    from umbra.core import config, UmbraConfig, PermissionManager
    from umbra.core import envelope, module_base, logger
"""

# Re-export everything from umbra.core for backward compatibility
from umbra.core import *
from umbra.core import __all__ as _core_all

# Explicitly re-export the main items from __all__
from umbra.core import (
    config,
    UmbraConfig, 
    PermissionManager,
    setup_logging,
    get_logger
)

# Re-export all submodules that might be imported
from umbra.core import (
    approvals,
    envelope, 
    logger,
    module_base,
    permissions,
    redact,
    risk
)

# Create comprehensive __all__ that includes everything available in umbra.core
__all__ = _core_all + [
    'approvals',
    'envelope', 
    'logger',
    'module_base', 
    'permissions',
    'redact',
    'risk'
]

# For debugging/introspection - indicate this is a compatibility shim
__compatibility_shim__ = True
__shim_target__ = "umbra.core"