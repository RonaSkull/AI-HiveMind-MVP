"""
Model Context Protocol (MCP) implementation for multi-agent systems.
"""

from .enhanced_context import EnhancedContextManager, ContextNode
from .persistence import Database, RedisManager
from .config import get_settings, configure_logging

__version__ = "0.3.0"

__all__ = [
    # Core components
    "EnhancedContextManager",
    "ContextNode",
    
    # Persistence
    "Database",
    "RedisManager",
    
    # Config
    "get_settings",
    "configure_logging"
]

# Configure logging when the package is imported
configure_logging()
