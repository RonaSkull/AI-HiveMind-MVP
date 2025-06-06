"""
Tests for the persistence layer.
"""

import asyncio
import json
import os
import sqlite3
import sys
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, AsyncGenerator, Optional

import aiosqlite
import pytest
import pytest_asyncio
from mcp import Database, RedisManager, EnhancedContextManager

# Test data
TEST_CONTEXT = {
    "type": "test",
    "data": {"key": "value"},
    "metadata": {"test": True}
}

# Test configuration - use in-memory SQLite for testing
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
TEST_REDIS_URL = "redis://localhost:6379/15"  # Using DB 15 for testing

class SQLiteDatabase(Database):
    """SQLite-specific database implementation."""
    
    async def _setup_tables(self):
        """Set up SQLite tables."""
        await self.execute("""
            CREATE TABLE IF NOT EXISTS context_nodes (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                node_type TEXT NOT NULL,
                parent_id TEXT,
                tags TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
                version INTEGER DEFAULT 1,
                FOREIGN KEY (parent_id) REFERENCES context_nodes(id) ON DELETE CASCADE
            )
        """)
        
        await self.execute("""
            CREATE TABLE IF NOT EXISTS context_relationships (
                parent_id TEXT,
                child_id TEXT,
                relationship_type TEXT DEFAULT 'child',
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
                PRIMARY KEY (parent_id, child_id),
                FOREIGN KEY (parent_id) REFERENCES context_nodes(id) ON DELETE CASCADE,
                FOREIGN KEY (child_id) REFERENCES context_nodes(id) ON DELETE CASCADE
            )
        """)

@pytest_asyncio.fixture
async def db() -> AsyncGenerator[Database, None]:
    """Create a test database connection."""
    # Create a new in-memory database for each test
    db = SQLiteDatabase(TEST_DB_URL)
    await db.connect()
    
    # Setup test tables
    await db._setup_tables()
    
    try:
        yield db
    finally:
        # Cleanup
        try:
            await db.execute("DELETE FROM context_relationships")
            await db.execute("DELETE FROM context_nodes")
            await db.close()
        except Exception as e:
            print(f"Error during test cleanup: {e}")
            await db.close()
            raise

class MockRedisManager(RedisManager):
    """In-memory Redis manager for testing."""
    
    def __init__(self, url: str):
        self.url = url
        self.data = {}
        self.ttl = {}
        self.connected = False
        
    async def connect(self):
        self.connected = True
        
    async def close(self):
        self.connected = False
        
    async def get(self, key: str) -> Any:
        if not self.connected:
            raise RuntimeError("Not connected to Redis")
            
        if key in self.ttl and self.ttl[key] < datetime.now().timestamp():
            del self.data[key]
            del self.ttl[key]
            return None
        return self.data.get(key)
    
    async def set(self, key: str, value: Any, **kwargs) -> bool:
        if not self.connected:
            raise RuntimeError("Not connected to Redis")
            
        self.data[key] = value
        if 'ttl' in kwargs and kwargs['ttl'] is not None:
            self.ttl[key] = datetime.now().timestamp() + kwargs['ttl']
        return True
    
    async def delete(self, key: str) -> bool:
        if not self.connected:
            raise RuntimeError("Not connected to Redis")
            
        if key in self.data:
            del self.data[key]
        if key in self.ttl:
            del self.ttl[key]
        return True
    
    async def exists(self, key: str) -> bool:
        if not self.connected:
            raise RuntimeError("Not connected to Redis")
            
        if key in self.ttl and self.ttl[key] < datetime.now().timestamp():
            if key in self.data:
                del self.data[key]
            del self.ttl[key]
            return False
        return key in self.data
    
    async def expire(self, key: str, ttl: int) -> bool:
        if not self.connected:
            raise RuntimeError("Not connected to Redis")
            
        if key in self.data:
            self.ttl[key] = datetime.now().timestamp() + ttl
            return True
        return False
    
    async def get_ttl(self, key: str) -> int:
        """Get the TTL for a key in seconds."""
        if not self.connected:
            raise RuntimeError("Not connected to Redis")
            
        if key not in self.data:
            return -2  # Key doesn't exist
        if key not in self.ttl:
            return -1  # No TTL set
            
        remaining = self.ttl[key] - datetime.now().timestamp()
        return int(remaining) if remaining > 0 else -1
    
    async def flushdb(self) -> bool:
        self.data.clear()
        self.ttl.clear()
        return True

@pytest_asyncio.fixture
async def redis_manager() -> AsyncGenerator[RedisManager, None]:
    """Create a test Redis manager."""
    manager = MockRedisManager(TEST_REDIS_URL)
    await manager.connect()
    await manager.flushdb()  # Clean before tests
    
    try:
        yield manager
    finally:
        # Cleanup
        await manager.close()

@pytest.fixture
def generate_id() -> str:
    """Generate a unique ID for tests."""
    return f"test_{uuid.uuid4().hex}"

@pytest.mark.asyncio
async def test_database_operations(db: Database):
    """Test basic database operations."""
    # Test data
    test_id = str(uuid.uuid4())
    test_data = {"key": "value"}
    
    # Test insert
    await db.execute(
        """
        INSERT INTO context_nodes (id, data, node_type, parent_id, tags, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        test_id,
        json.dumps(test_data),
        "test",
        None,
        json.dumps(["test"]),
        json.dumps({"test": True})
    )
    
    # Test select
    row = await db.fetchrow(
        "SELECT * FROM context_nodes WHERE id = ?",
        test_id
    )
    assert row is not None
    assert json.loads(row['data']) == test_data
    assert row['node_type'] == 'test'
    
    # Test update
    await db.execute(
        "UPDATE context_nodes SET data = ? WHERE id = ?",
        json.dumps({"key": "updated"}),
        test_id
    )
    
    row = await db.fetchrow(
        "SELECT data FROM context_nodes WHERE id = ?",
        test_id
    )
    assert json.loads(row['data']) == {"key": "updated"}
    
    # Test delete
    await db.execute("DELETE FROM context_nodes WHERE id = ?", test_id)
    row = await db.fetchrow("SELECT * FROM context_nodes WHERE id = ?", test_id)
    assert row is None

@pytest.mark.asyncio
async def test_redis_operations(redis_manager: RedisManager) -> None:
    """Test basic Redis operations."""
    test_key = f"test:key:{uuid.uuid4().hex}"
    test_value = {"test": "value"}
    
    # Set value
    result = await redis_manager.set(test_key, test_value)
    assert result is True
    
    # Get value
    retrieved = await redis_manager.get(test_key)
    assert retrieved == test_value
    
    # Check exists
    exists = await redis_manager.exists(test_key)
    assert exists is True
    
    # Set TTL
    await redis_manager.expire(test_key, 5)
    ttl = await redis_manager.get_ttl(test_key)
    assert 0 < ttl <= 5
    
    # Update value
    updated_value = {"test": "updated"}
    await redis_manager.set(test_key, updated_value)
    retrieved = await redis_manager.get(test_key)
    assert retrieved == updated_value
    
    # Delete
    await redis_manager.delete(test_key)
    exists = await redis_manager.exists(test_key)
    assert not exists
    
    # Test non-existent key
    non_existent = await redis_manager.get("non_existent_key")
    assert non_existent is None

@pytest.mark.asyncio
async def test_context_manager_with_persistence(
    db: Database, 
    redis_manager: RedisManager, 
    generate_id: str
) -> None:
    """Test EnhancedContextManager with persistence."""
    # Create context manager with database storage
    context_manager = EnhancedContextManager(db)
    
    # Test create and retrieve
    context_id = generate_id()
    
    # Create context
    created_id = await context_manager.create_context(
        data={"key": "value"},
        context_type="test",
        metadata={"test": True}
    )
    assert created_id is not None
    
    # Get context
    context = await context_manager.get_context(created_id)
    assert context is not None
    assert context["data"]["key"] == "value"
    
    # Update the context
    updates = {"key": "updated"}
    await context_manager.update_context(
        created_id,
        data=updates
    )
    
    # Verify update
    updated = await context_manager.get_context(created_id)
    assert updated["data"]["key"] == "updated"
    assert updated["version"] == 2  # Version should be incremented
    
    # Test with Redis cache
    cached_manager = EnhancedContextManager(redis_manager)
    await cached_manager.set(created_id, updated)
    
    # Get from cache
    cached = await cached_manager.get(created_id)
    assert cached["data"]["key"] == "updated"
    
    # Clean up
    await context_manager.delete_context(created_id)
    assert await context_manager.get_context(created_id) is None
    
    # Clean cache
    await cached_manager.delete(created_id)
    assert await cached_manager.get(created_id) is None

@pytest.mark.asyncio
async def test_context_ttl(redis_manager: RedisManager, generate_id: str) -> None:
    """Test TTL functionality with Redis."""
    # Create context manager with Redis storage
    context_manager = EnhancedContextManager(redis_manager)
    
    # Create with TTL (1 second)
    context_id = generate_id()
    test_data = {
        "id": context_id,
        "type": "ttl_test",
        "data": {"key": "value"},
        "metadata": {}
    }
    
    # Set with TTL
    await context_manager.set(context_id, test_data, ttl=1)
    
    # Should exist initially
    assert await context_manager.get(context_id) is not None
    
    # Wait for TTL to expire
    await asyncio.sleep(2)
    
    # Should be expired
    assert await context_manager.get(context_id) is None
    
    # Verify with direct Redis check
    assert not await redis_manager.exists(context_id)

@pytest.mark.asyncio
async def test_database_operations(db):
    """Test basic database operations."""
    # Test insert and retrieve
    test_key = "test:key"
    test_value = {"test": "value"}
    
    # Skip if using asyncpg directly
    if hasattr(db, 'pool'):
        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO context_nodes (id, data, node_type)
                VALUES ($1, $2, $3)
                ON CONFLICT (id) DO UPDATE SET data = $2
                """,
                test_key, json.dumps(test_value), "test"
            )
            
            # Retrieve
            result = await conn.fetchval(
                "SELECT data FROM context_nodes WHERE id = $1",
                test_key
            )
            assert json.loads(result) == test_value
            
            # Check exists
            exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM context_nodes WHERE id = $1)",
                test_key
            )
            assert exists is True
            
            # Delete
            await conn.execute(
                "DELETE FROM context_nodes WHERE id = $1",
                test_key
            )
            
            # Verify deleted
            exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM context_nodes WHERE id = $1)",
                test_key
            )
            assert exists is False
    else:
        pytest.skip("Direct database operations not supported with this backend")

@pytest.mark.asyncio
async def test_redis_operations(redis_manager):
    """Test basic Redis operations."""
    test_key = "test:key"
    test_value = {"test": "value"}

    # Set value
    await redis_manager.set(test_key, test_value)


    # Get value
    result = await redis_manager.get(test_key)
    assert result == test_value

    # Check exists
    assert await redis_manager.exists(test_key) is True

    # Set TTL
    await redis_manager.expire(test_key, 5)
    ttl = await redis_manager.get_ttl(test_key)
    assert 0 < ttl <= 5
    
    # Delete
    await redis_manager.delete(test_key)
    assert await redis_manager.exists(test_key) is False

@pytest.mark.asyncio
async def test_context_manager_with_persistence(db, redis_manager):
    """Test EnhancedContextManager with persistence."""
    # Create context manager with storage only (no cache for this test)
    context_manager = EnhancedContextManager(storage_backend=db)
    
    # Test create and retrieve
    context_id = await context_manager.create_context(
        data=TEST_CONTEXT,
        tags=["test"]
    )
    assert context_id is not None
    
    # Get context
    context = await context_manager.get_context(context_id)
    assert context is not None
    assert context["data"]["key"] == "value"
    
    # Update the context
    updates = {"data": {"key": "updated"}}
    await context_manager.update_context(context_id, updates)
    
    # Verify update
    updated = await context_manager.get_context(context_id)
    assert updated["data"]["key"] == "updated"
    
    # Create child context
    child_id = await context_manager.create_context(
        data={"type": "child"},
        parent_id=context_id
    )
    
    # Get with children
    with_children = await context_manager.get_context(context_id, include_children=True)
    assert "children" in with_children
    assert len(with_children["children"]) == 1
    
    # Clean up
    await context_manager.delete_context(context_id)
    assert await context_manager.get_context(context_id) is None

@pytest.mark.asyncio
async def test_context_ttl(db):
    """Test TTL functionality."""
    # Create context manager with storage only
    context_manager = EnhancedContextManager(storage_backend=db)
    
    # Create with TTL
    context_id = await context_manager.create_context(
        data={"type": "ttl_test"},
        ttl=1  # 1 second TTL
    )
    
    # Should exist initially
    assert await context_manager.get_context(context_id) is not None
    
    # Wait for TTL
    await asyncio.sleep(2)
    
    # Should be expired
    assert await context_manager.get_context(context_id) is None
