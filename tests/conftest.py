"""
Pytest configuration and fixtures for testing.
"""

import os
import pytest
import asyncio
import asyncpg
from typing import AsyncGenerator

# Test database configuration
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_hivemind")
TEST_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.WindowsSelectorEventLoopPolicy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def setup_test_database():
    """Set up test database with schema."""
    # Parse the database URL to get connection parameters
    db_params = {
        'user': 'postgres',
        'password': 'postgres',
        'host': 'localhost',
        'port': 5432,
        'database': 'postgres'  # Connect to default database first
    }
    
    # Connect to default database to create test database
    conn = await asyncpg.connect(**{k: v for k, v in db_params.items() if v is not None})
    
    try:
        # Create test database if it doesn't exist
        await conn.execute(f"""
            SELECT 'CREATE DATABASE test_hivemind'
            WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'test_hivemind')""")
    finally:
        await conn.close()
    
    # Now connect to the test database
    test_conn = await asyncpg.connect(
        host=db_params['host'],
        port=db_params['port'],
        user=db_params['user'],
        password=db_params['password'],
        database='test_hivemind'
    )
    
    try:
        # Create schema
        await test_conn.execute("""
            DROP SCHEMA public CASCADE;
            CREATE SCHEMA public;
            GRANT ALL ON SCHEMA public TO postgres;
            GRANT ALL ON SCHEMA public TO public;
        """)
        
        # Create tables
        await test_conn.execute("""
            CREATE TABLE IF NOT EXISTS context_nodes (
                id TEXT PRIMARY KEY,
                data JSONB NOT NULL,
                node_type TEXT NOT NULL,
                parent_id TEXT REFERENCES context_nodes(id) ON DELETE CASCADE,
                tags TEXT[] DEFAULT '{}',
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                version INTEGER DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS context_relationships (
                parent_id TEXT REFERENCES context_nodes(id) ON DELETE CASCADE,
                child_id TEXT REFERENCES context_nodes(id) ON DELETE CASCADE,
                relationship_type TEXT DEFAULT 'child',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (parent_id, child_id)
            );
        """)
        
        yield
        
    finally:
        # Clean up
        await test_conn.execute("""
            DROP TABLE IF EXISTS context_relationships CASCADE;
            DROP TABLE IF EXISTS context_nodes CASCADE;
        """)
        await test_conn.close()

@pytest.fixture(scope="function")
async def db(setup_test_database) -> AsyncGenerator[asyncpg.Connection, None]:
    """Database connection fixture."""
    conn = await asyncpg.connect(TEST_DATABASE_URL)
    try:
        # Start a transaction
        await conn.set_builtin_server_parameter('statement_timeout', '1000')  # 1 second timeout
        tr = conn.transaction()
        await tr.start()
        
        yield conn
        
        # Rollback after test
        await tr.rollback()
    finally:
        await conn.close()

@pytest.fixture(scope="function")
async def redis_manager() -> AsyncGenerator['RedisManager', None]:
    """Redis manager fixture."""
    from mcp.redis_manager import RedisManager
    
    manager = RedisManager(TEST_REDIS_URL)
    try:
        await manager.connect()
        # Clear any existing data
        await manager.flushdb()
        yield manager
    finally:
        await manager.close()
