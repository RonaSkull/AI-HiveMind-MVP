"""
Persistence layer for the MCP system.
Handles both database and Redis operations with async support.
"""

import asyncio
import json
import logging
import aiosqlite
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, AsyncGenerator, Tuple

logger = logging.getLogger(__name__)

class Database:
    """Async database connection handler with SQLite support."""
    
    def __init__(self, dsn: str):
        """Initialize with a database connection string."""
        self.dsn = dsn
        self.conn = None
        self.is_sqlite = dsn.startswith('sqlite')
    
    async def connect(self) -> None:
        """Establish a connection to the database."""
        try:
            if self.is_sqlite:
                # Extract the database path from the DSN
                db_path = self.dsn.replace('sqlite+aiosqlite://', '')
                if db_path == ':memory:':
                    self.conn = await aiosqlite.connect(':memory:')
                else:
                    self.conn = await aiosqlite.connect(db_path)
                # Enable foreign key support for SQLite
                await self.conn.execute('PRAGMA foreign_keys = ON')
                await self.conn.commit()
                logger.info("SQLite database connection established")
            else:
                raise ValueError("Only SQLite is supported in this implementation")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            await self.conn.close()
            self.conn = None
            logger.info("Database connection closed")
    
    async def execute(self, query: str, *args) -> str:
        """
        Execute a query and return the status.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            str: Status message with number of rows affected
        """
        if not self.conn:
            raise RuntimeError("Database not connected. Call connect() first.")
            
        try:
            # Convert query to use SQLite's parameter style if needed
            query = query.replace('$', '?')
            cursor = await self.conn.execute(query, args)
            await self.conn.commit()
            return f"Query OK, rows affected: {cursor.rowcount}"
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    async def fetchrow(self, query: str, *args) -> Optional[dict]:
        """
        Fetch a single row.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            Optional[dict]: Row data or None if not found
        """
        if not self.conn:
            raise RuntimeError("Database not connected. Call connect() first.")
            
        try:
            # Convert query to use SQLite's parameter style if needed
            query = query.replace('$', '?')
            cursor = await self.conn.execute(query, args)
            row = await cursor.fetchone()
            if not row:
                return None
            return dict(row)
        except Exception as e:
            logger.error(f"Error fetching row: {e}")
            raise
    
    async def fetch(self, query: str, *args) -> list:
        """
        Fetch multiple rows.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            list: List of row data as dictionaries
        """
        if not self.conn:
            raise RuntimeError("Database not connected. Call connect() first.")
            
        try:
            # Convert query to use SQLite's parameter style if needed
            query = query.replace('$', '?')
            cursor = await self.conn.execute(query, args)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching rows: {e}")
            raise
    
    async def fetchval(self, query: str, *args) -> Any:
        """
        Fetch a single value.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            Any: The first column of the first row, or None if no rows
        """
        if not self.conn:
            raise RuntimeError("Database not connected. Call connect() first.")
            
        try:
            # Convert query to use SQLite's parameter style if needed
            query = query.replace('$', '?')
            cursor = await self.conn.execute(query, args)
            row = await cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Error fetching value: {e}")
            raise


class RedisManager:
    """Redis client wrapper with async support."""
    
    def __init__(self, url: str, **kwargs):
        """
        Initialize the Redis client.
        
        Args:
            url: Redis connection URL
            **kwargs: Additional connection parameters
        """
        self.url = url
        self.client = None
        self._connection_params = kwargs
    
    async def connect(self) -> None:
        """Establish a connection to Redis."""
        try:
            self.client = Redis.from_url(
                self.url,
                decode_responses=True,
                **self._connection_params
            )
            await self.client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def close(self) -> None:
        """Close the Redis connection."""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")
    
    async def set(self, key: str, value: Any, **kwargs) -> bool:
        """Set a key-value pair in Redis."""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return await self.client.set(key, value, **kwargs)
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get a value from Redis by key."""
        try:
            value = await self.client.get(key)
            if value is None:
                return default
            try:
                return json.loads(value)
            except (TypeError, json.JSONDecodeError):
                return value
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return default
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys from Redis."""
        try:
            return await self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Error deleting keys {keys}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        try:
            return bool(await self.client.exists(key))
        except Exception as e:
            logger.error(f"Error checking if key exists {key}: {e}")
            return False
    
    async def expire(self, key: str, time: int) -> bool:
        """Set a key's time to live in seconds."""
        try:
            return await self.client.expire(key, time)
        except Exception as e:
            logger.error(f"Error setting TTL for key {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> int:
        """Get the TTL for a key in seconds."""
        try:
            return await self.client.pttl(key) / 1000
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return -2  # Key doesn't exist
    
    async def flushdb(self) -> bool:
        """Delete all keys in the current database."""
        try:
            await self.client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Error flushing database: {e}")
            return False
