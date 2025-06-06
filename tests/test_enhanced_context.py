"""
Tests for the enhanced context management system.
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from mcp.enhanced_context import ContextNode, EnhancedContextManager

@pytest.fixture
def sample_node():
    """Create a sample context node for testing."""
    return ContextNode(
        node_id="test123",
        data={"message": "Hello, world!"},
        node_type="test",
        tags={"test", "example"},
        metadata={"source": "test"}
    )

@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = AsyncMock()
    mock.get.return_value = None
    return mock

@pytest.mark.asyncio
async def test_context_node_creation(sample_node):
    """Test creating a context node."""
    assert sample_node.node_id == "test123"
    assert sample_node.data["message"] == "Hello, world!"
    assert sample_node.node_type == "test"
    assert "test" in sample_node.tags
    assert "example" in sample_node.tags
    assert sample_node.metadata["source"] == "test"
    assert sample_node.version == 1

@pytest.mark.asyncio
async def test_node_update(sample_node):
    """Test updating a node's data."""
    sample_node.update({"message": "Updated!"})
    assert sample_node.data["message"] == "Updated!"
    assert sample_node.version == 2

@pytest.mark.asyncio
async def test_node_serialization(sample_node):
    """Test serializing and deserializing a node."""
    node_dict = sample_node.to_dict()
    assert node_dict["node_id"] == "test123"
    assert node_dict["data"]["message"] == "Hello, world!"
    
    # Test deserialization
    new_node = ContextNode.from_dict(node_dict)
    assert new_node.node_id == sample_node.node_id
    assert new_node.data == sample_node.data
    assert new_node.version == sample_node.version

@pytest.mark.asyncio
async def test_create_context():
    """Test creating a new context."""
    manager = EnhancedContextManager()
    context_id = await manager.create_context(
        data={"message": "Test context"},
        context_type="test",
        tags=["test"],
        metadata={"source": "test"}
    )
    
    assert context_id is not None
    assert context_id.startswith("ctx_")
    
    # Verify the context was stored
    context = await manager.get_context(context_id)
    assert context is not None
    assert context["data"]["message"] == "Test context"
    assert context["node_type"] == "test"
    assert "test" in context["tags"]
    assert context["metadata"]["source"] == "test"

@pytest.mark.asyncio
async def test_update_context():
    """Test updating an existing context."""
    manager = EnhancedContextManager()
    context_id = await manager.create_context({"message": "Original"})
    
    # Update the context
    updated = await manager.update_context(
        context_id,
        {"message": "Updated"}
    )
    assert updated is True
    
    # Verify the update
    context = await manager.get_context(context_id)
    assert context["data"]["message"] == "Updated"
    assert context["version"] == 2

@pytest.mark.asyncio
async def test_add_context_tag():
    """Test adding a tag to a context."""
    manager = EnhancedContextManager()
    context_id = await manager.create_context({"test": "data"})
    
    # Add a tag
    added = await manager.add_context_tag(context_id, "important")
    assert added is True
    
    # Verify the tag was added
    context = await manager.get_context(context_id)
    assert "important" in context["tags"]

@pytest.mark.asyncio
async def test_find_by_tag():
    """Test finding contexts by tag."""
    manager = EnhancedContextManager()
    
    # Create some test contexts
    context1 = await manager.create_context(
        {"message": "First"},
        tags=["test", "important"]
    )
    context2 = await manager.create_context(
        {"message": "Second"},
        tags=["test"]
    )
    
    # Find by tag
    important = await manager.find_contexts_by_tag("important")
    assert len(important) == 1
    assert important[0]["node_id"] == context1
    
    test = await manager.find_contexts_by_tag("test")
    assert len(test) == 2

@pytest.mark.asyncio
async def test_hierarchical_context():
    """Test parent-child context relationships."""
    manager = EnhancedContextManager()
    
    # Create parent context
    parent_id = await manager.create_context(
        {"type": "conversation", "topic": "AI"},
        context_type="conversation"
    )
    
    # Create child context
    child_id = await manager.create_context(
        {"message": "Hello!"},
        context_type="message",
        parent_id=parent_id
    )
    
    # Verify the hierarchy
    child = await manager.get_context(child_id)
    assert child["parent_id"] == parent_id
    
    # The parent data should be included in the child's data
    assert "parent" in child["data"]
    assert child["data"]["parent"]["data"]["topic"] == "AI"

@pytest.mark.asyncio
async def test_redis_integration(mock_redis):
    """Test integration with Redis backend."""
    # Set up mock Redis response
    test_data = {
        "node_id": "test123",
        "node_type": "test",
        "parent_id": None,
        "data": {"message": "Hello, Redis!"},
        "tags": ["test"],
        "metadata": {},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "version": 1
    }
    mock_redis.get.return_value = json.dumps(test_data)
    
    # Initialize with mock Redis
    manager = EnhancedContextManager(mock_redis)
    
    # Test get_context
    context = await manager.get_context("test123")
    assert context is not None
    assert context["data"]["message"] == "Hello, Redis!"
    mock_redis.get.assert_called_with("context:test123")
    
    # Test update_context
    mock_redis.get.return_value = json.dumps(test_data)
    await manager.update_context("test123", {"message": "Updated"})
    
    # Verify set was called with updated data
    args, kwargs = mock_redis.set.call_args
    assert args[0] == "context:test123"
    updated_data = json.loads(args[1])
    assert updated_data["data"]["message"] == "Updated"
    assert updated_data["version"] == 2

@pytest.mark.asyncio
async def test_concurrent_updates():
    """Test handling of concurrent context updates."""
    manager = EnhancedContextManager()
    context_id = await manager.create_context({"counter": 0})
    
    async def update_counter():
        for _ in range(10):
            context = await manager.get_context(context_id)
            counter = context["data"].get("counter", 0)
            await manager.update_context(context_id, {"counter": counter + 1})
            await asyncio.sleep(0.01)  # Simulate work
    
    # Run multiple updates concurrently
    await asyncio.gather(*[update_counter() for _ in range(5)])
    
    # Verify the final counter value
    context = await manager.get_context(context_id)
    assert context["data"]["counter"] == 50  # 5 tasks * 10 updates each

if __name__ == "__main__":
    import pytest
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
