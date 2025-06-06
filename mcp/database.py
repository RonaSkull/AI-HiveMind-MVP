"""
Database module for persistent storage of context data.
"""

import os
import re
import json
import logging
import asyncpg
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from contextlib import asynccontextmanager
from datetime import datetime
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

def parse_dsn(dsn: str) -> dict:
    """Parse a database connection string into connection parameters."""
    if not dsn:
        return {}
    
    # Handle SQLAlchemy-style URLs
    if dsn.startswith('postgresql+asyncpg://'):
        dsn = dsn.replace('postgresql+asyncpg://', 'postgresql://')
    
    # Parse the URL
    parsed = urlparse(dsn)
    
    # Extract connection parameters
    params = {
        'user': parsed.username or None,
        'password': parsed.password or None,
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 5432,
        'database': parsed.path.lstrip('/') if parsed.path else None,
    }
    
    # Parse query parameters
    query_params = parse_qs(parsed.query)
    for key, value in query_params.items():
        if len(value) == 1:
            params[key] = value[0]
    
    return params

class Database:
    """
    Database handler for persistent storage of context data.
    """
    
    def __init__(self, dsn: Optional[str] = None, **kwargs):
        """
        Initialize the database connection.
        
        Args:
            dsn: PostgreSQL connection string or URL
            **kwargs: Additional connection parameters
        """
        self.dsn = dsn or os.getenv("DATABASE_URL")
        self.pool = None
        self._connection_params = kwargs
        
        if not self.dsn:
            raise ValueError("Database connection string (DATABASE_URL) not provided")
    
    async def connect(self) -> None:
        """Establish a connection pool to the database."""
        max_retries = 3
        retry_delay = 1  # seconds
        
        # Parse DSN if it's a URL
        if '://' in self.dsn:
            conn_params = parse_dsn(self.dsn)
            conn_params.update(self._connection_params)
            dsn = None
        else:
            conn_params = self._connection_params
            dsn = self.dsn
        
        last_error = None
        for attempt in range(max_retries):
            try:
                self.pool = await asyncpg.create_pool(
                    dsn=dsn,
                    min_size=1,
                    max_size=10,
                    **conn_params
                )
                # Test the connection
                async with self.pool.acquire() as conn:
                    await conn.execute('SELECT 1')
                logger.info("Database connection pool established")
                return
            except (asyncpg.PostgresError, OSError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Connection attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {retry_delay} seconds..."
                    )
                    import asyncio
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to connect to database after {max_retries} attempts")
                    raise RuntimeError(f"Failed to connect to database: {last_error}") from last_error
    
    async def close(self) -> None:
        """Close the database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query and return the status."""
        async with self.pool.acquire() as conn:
            result = await conn.execute(query, *args)
            return result
    
    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """Execute a query and return all results."""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Execute a query and return one row."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def migrate(self) -> None:
        """Apply database migrations."""
        await self._create_schema()
        await self._apply_migrations()
    
    async def _create_schema(self) -> None:
        """Create the database schema if it doesn't exist."""
        schema_sql = """
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
        
        CREATE TABLE IF NOT EXISTS migrations (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_context_nodes_tags ON context_nodes USING GIN(tags);
        CREATE INDEX IF NOT EXISTS idx_context_nodes_node_type ON context_nodes(node_type);
        CREATE INDEX IF NOT EXISTS idx_context_nodes_parent_id ON context_nodes(parent_id);
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(schema_sql)
        
        logger.info("Database schema created/validated")
    
    async def _apply_migrations(self) -> None:
        """Apply any pending migrations."""
        migrations = [
            self._migration_initial_schema,
            # Add future migrations here
        ]
        
        async with self.pool.acquire() as conn:
            for migration in migrations:
                migration_name = migration.__name__
                
                # Check if migration was already applied
                applied = await conn.fetchval(
                    "SELECT 1 FROM migrations WHERE name = $1",
                    migration_name
                )
                
                if not applied:
                    logger.info(f"Applying migration: {migration_name}")
                    try:
                        await migration(conn)
                        await conn.execute(
                            "INSERT INTO migrations (name) VALUES ($1)",
                            migration_name
                        )
                        logger.info(f"Applied migration: {migration_name}")
                    except Exception as e:
                        logger.error(f"Failed to apply migration {migration_name}: {e}")
                        raise
    
    async def _migration_initial_schema(self, conn) -> None:
        """Initial schema migration."""
        # This is a no-op since we create the schema in _create_schema
        pass


@asynccontextmanager
async def get_database(dsn: Optional[str] = None, **kwargs) -> AsyncGenerator[Database, None]:
    """Context manager for database connections."""
    db = Database(dsn, **kwargs)
    try:
        await db.connect()
        await db.migrate()
        yield db
    finally:
        await db.close()


class DatabaseContextManager:
    """
    Database-backed context manager that implements the context storage interface.
    """
    
    def __init__(self, db: Database):
        """
        Initialize with a database instance.
        
        Args:
            db: Database instance
        """
        self.db = db
    
    async def get(self, key: str) -> Optional[str]:
        """Get a value from the database."""
        result = await self.db.fetchrow(
            "SELECT data FROM context_nodes WHERE id = $1",
            key
        )
        return json.dumps(result["data"]) if result else None
    
    async def set(self, key: str, value: str, **kwargs) -> None:
        """Set a value in the database."""
        data = json.loads(value)
        now = datetime.utcnow()
        
        # Check if the key exists
        exists = await self.db.fetchval(
            "SELECT 1 FROM context_nodes WHERE id = $1",
            key
        )
        
        if exists:
            # Update existing
            await self.db.execute(
                """
                UPDATE context_nodes 
                SET data = $1, 
                    updated_at = $2,
                    version = version + 1
                WHERE id = $3
                """,
                data, now, key
            )
        else:
            # Insert new
            await self.db.execute(
                """
                INSERT INTO context_nodes (id, data, node_type, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                key, data, data.get("type", "generic"), now, now
            )
    
    async def delete(self, key: str) -> None:
        """Delete a value from the database."""
        await self.db.execute(
            "DELETE FROM context_nodes WHERE id = $1",
            key
        )
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in the database."""
        return await self.db.fetchval(
            "SELECT EXISTS(SELECT 1 FROM context_nodes WHERE id = $1)",
            key
        )
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching a pattern."""
        # Simple pattern matching - for more complex patterns, consider using full-text search
        if pattern == "*":
            rows = await self.db.fetch("SELECT id FROM context_nodes")
        else:
            # Convert glob pattern to SQL LIKE pattern
            like_pattern = pattern.replace('*', '%').replace('?', '_')
            rows = await self.db.fetch(
                "SELECT id FROM context_nodes WHERE id LIKE $1",
                like_pattern
            )
        return [row["id"] for row in rows]
