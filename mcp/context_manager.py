"""
Model Context Protocol (MCP) Context Manager

Provides a shared context for agent communication with Redis backend support.
"""
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
import logging

logger = logging.getLogger(__name__)

class MCPContextManager:
    """
    Manages shared context between agents with Redis backend support.
    
    Args:
        redis_client: Optional Redis client instance. If None, uses in-memory storage.
        namespace: Optional namespace for Redis keys.
    """
    
    def __init__(self, redis_client=None, namespace: str = "mcp"):
        self.redis = redis_client
        self.namespace = namespace
        self._context = {}
        
    def _get_key(self, context_id: str) -> str:
        """Generate namespaced Redis key."""
        return f"{self.namespace}:{context_id}"
        
    def update(
        self, 
        agent_id: str, 
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> str:
        """
        Update context with agent data.
        
        Args:
            agent_id: Unique identifier for the agent
            data: Dictionary of data to store
            ttl: Optional TTL in seconds for Redis entries
            
        Returns:
            str: Context ID for the stored data
        """
        timestamp = datetime.utcnow().isoformat()
        context_id = hashlib.sha256(f"{agent_id}:{timestamp}".encode()).hexdigest()
        
        entry = {
            "data": data,
            "metadata": {
                "agent_id": agent_id,
                "timestamp": timestamp,
                "context_id": context_id,
                "version": "1.0"
            }
        }
        
        try:
            if self.redis:
                serialized = json.dumps(entry)
                self.redis.set(
                    self._get_key(context_id), 
                    serialized,
                    ex=ttl
                )
                # Add to agent's context history
                history_key = f"{self.namespace}:agent:{agent_id}:history"
                self.redis.lpush(history_key, context_id)
                # Keep only last 100 entries
                self.redis.ltrim(history_key, 0, 99)
            else:
                self._context[context_id] = entry
                
            logger.debug(f"Context updated: {context_id} by {agent_id}")
            return context_id
            
        except Exception as e:
            logger.error(f"Failed to update context: {e}")
            raise
    
    def get(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve context by ID.
        
        Args:
            context_id: ID of the context to retrieve
            
        Returns:
            Optional[Dict]: Context data or None if not found
        """
        try:
            if self.redis:
                result = self.redis.get(self._get_key(context_id))
                return json.loads(result) if result else None
            return self._context.get(context_id)
            
        except Exception as e:
            logger.error(f"Failed to get context {context_id}: {e}")
            return None
    
    def search(
        self, 
        agent_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for context entries.
        
        Args:
            agent_id: Optional filter by agent ID
            limit: Maximum number of results to return
            
        Returns:
            List of matching context entries, up to the specified limit
        """
        try:
            if self.redis:
                if agent_id:
                    history_key = f"{self.namespace}:agent:{agent_id}:history"
                    # Get context IDs from the agent's history, limited by the specified limit
                    context_ids = self.redis.lrange(history_key, 0, limit - 1)
                    # Fetch each context and filter out any None values
                    results = []
                    for ctx_id in context_ids:
                        if len(results) >= limit:
                            break
                        ctx = self.get(ctx_id.decode())
                        if ctx:
                            results.append(ctx)
                    return results
                else:
                    # This is a simple implementation - in production, use Redis Search
                    return []
            else:
                if agent_id:
                    return [
                        ctx for ctx in self._context.values() 
                        if ctx["metadata"]["agent_id"] == agent_id
                    ][:limit]
                return list(self._context.values())[:limit]
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def clear(self, context_id: Optional[str] = None) -> bool:
        """
        Clear context entries.
        
        Args:
            context_id: Optional ID of context to clear. If None, clears all.
            
        Returns:
            bool: True if operation was successful
        """
        try:
            if context_id:
                if self.redis:
                    return bool(self.redis.delete(self._get_key(context_id)))
                return bool(self._context.pop(context_id, None) is not None)
            else:
                if self.redis:
                    # In production, use SCAN + DEL for pattern matching
                    pass
                self._context.clear()
                return True
                
        except Exception as e:
            logger.error(f"Failed to clear context: {e}")
            return False
