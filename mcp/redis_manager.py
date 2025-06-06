"""
Redis-based storage for the Model Context Protocol.
"""

import json
import logging
from typing import Any, Dict, List, Optional, AsyncGenerator, Union
from contextlib import asynccontextmanager
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError

from .config import get_settings

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis-based storage manager for MCP with improved async handling."""
    
    def __init__(
        self, 
        url: Optional[str] = None, 
        **kwargs
    ):
        """Initialize Redis client.
        
        Args:
            url: Redis connection URL
            **kwargs: Additional arguments to pass to Redis client
        """
        self.settings = get_settings()
        self.url = url or str(self.settings.REDIS_URL)
        self.client_kwargs = {
            "decode_responses": False,  # We'll handle encoding/decoding
            **kwargs
        }
        self._client = None
        self._lock = asyncio.Lock()
        self._is_connected = False
    
    @property
    def client(self) -> Optional[redis.Redis]:
        """Get the Redis client instance."""
        return self._client
    
    async def _ensure_connected(self) -> None:
        """Ensure we have an active connection to Redis."""
        if self._is_connected and self._client:
            try:
                await self._client.ping()
                return
            except (RedisError, ConnectionError):
                self._is_connected = False
                if self._client:
                    await self._client.close()
        
        async with self._lock:
            if not self._is_connected:
                try:
                    self._client = redis.Redis.from_url(
                        self.url,
                        **self.client_kwargs
                    )
                    await self._client.ping()
                    self._is_connected = True
                    logger.info(f"Connected to Redis at {self.url}")
                except (RedisError, ConnectionError) as e:
                    logger.error(f"Failed to connect to Redis: {e}")
                    self._is_connected = False
                    self._client = None
                    raise
    
    async def close(self) -> None:
        """Close Redis connection."""
        async with self._lock:
            if self._client and self._is_connected:
                try:
                    await self._client.aclose()
                except Exception as e:
                    logger.warning(f"Error closing Redis connection: {e}")
                finally:
                    self._is_connected = False
                    self._client = None
                    logger.info("Closed Redis connection")
    
    async def __aenter__(self):
        await self._ensure_connected()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None, 
        **kwargs
    ) -> bool:
        """Set a key-value pair with optional TTL."""
        try:
            await self._ensure_connected()
            if not self._client:
                return False
                
            serialized = json.dumps(value).encode('utf-8')
            ex = ttl if ttl is not None else None
            return await self._client.set(key, serialized, ex=ex, **kwargs)
        except (TypeError, json.JSONEncodeError) as e:
            logger.error(f"Failed to serialize value: {e}")
            return False
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis error in set: {e}")
            self._is_connected = False
            return False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get a value by key."""
        try:
            await self._ensure_connected()
            if not self._client:
                return default
                
            value = await self._client.get(key)
            if value is None:
                return default
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to deserialize value: {e}")
            return default
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis error in get: {e}")
            self._is_connected = False
            return default
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        if not keys:
            return 0
            
        try:
            await self._ensure_connected()
            if not self._client:
                return 0
                
            return await self._client.delete(*keys)
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis error in delete: {e}")
            self._is_connected = False
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        try:
            await self._ensure_connected()
            if not self._client:
                return False
                
            return bool(await self._client.exists(key))
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis error in exists: {e}")
            self._is_connected = False
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set a key's time to live in seconds."""
        try:
            await self._ensure_connected()
            if not self._client:
                return False
                
            return await self._client.expire(key, ttl)
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis error in expire: {e}")
            self._is_connected = False
            return False
    
    async def ttl(self, key: str) -> int:
        """Get the time to live for a key in seconds."""
        try:
            await self._ensure_connected()
            if not self._client:
                return -2
                
            return await self._client.ttl(key)
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis error in ttl: {e}")
            self._is_connected = False
            return -2
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Find all keys matching the given pattern."""
        try:
            await self._ensure_connected()
            if not self._client:
                return []
                
            return [k.decode('utf-8') for k in await self._client.keys(pattern)]
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis error in keys: {e}")
            self._is_connected = False
            return []
    
    async def flushdb(self) -> bool:
        """Delete all keys in the current database."""
        try:
            await self._ensure_connected()
            if not self._client:
                return False
                
            await self._client.flushdb()
            return True
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis error in flushdb: {e}")
            self._is_connected = False
            return False


@asynccontextmanager
async def get_redis_manager(
    url: Optional[str] = None, 
    **kwargs
) -> AsyncGenerator[RedisManager, None]:
    """
    Context manager for Redis connections.
    
    Args:
        url: Optional Redis URL
        **kwargs: Additional Redis client parameters
        
    Yields:
        RedisManager: Configured Redis manager instance
    """
    manager = RedisManager(url, **kwargs)
    try:
        await manager._ensure_connected()
        yield manager
    finally:
        await manager.close()


class RedisContextManager:
    """
    Redis-backed context manager that implements the context storage interface.
    """
    
    def __init__(self, redis_manager: RedisManager):
        """
        Initialize with a Redis manager instance.
        
        Args:
            redis_manager: RedisManager instance
        """
        self.redis = redis_manager
    
    async def get(self, key: str) -> Optional[str]:
        """Get a value from Redis."""
        result = await self.redis.get(key)
        return json.dumps(result) if result is not None else None
    
    async def set(self, key: str, value: str, **kwargs) -> None:
        """Set a value in Redis."""
        ttl = kwargs.get('ttl')
        await self.redis.set(key, json.loads(value), ttl=ttl)
    
    async def delete(self, key: str) -> None:
        """Delete a value from Redis."""
        await self.redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        return await self.redis.exists(key)
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching a pattern."""
        return await self.redis.keys(pattern)
