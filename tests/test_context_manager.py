"""Tests for the MCP Context Manager."""
import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from mcp.context_manager import MCPContextManager

# Test data
TEST_AGENT_ID = "test_agent_1"
TEST_DATA = {"key": "value", "nested": {"a": 1, "b": 2}}

@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = MagicMock()
    mock.get.return_value = None
    return mock

def test_update_and_get_in_memory():
    """Test updating and getting context with in-memory storage."""
    mcp = MCPContextManager()
    
    # Test update
    context_id = mcp.update(TEST_AGENT_ID, TEST_DATA)
    assert context_id is not None
    
    # Test get
    result = mcp.get(context_id)
    assert result is not None
    assert result["data"] == TEST_DATA
    assert result["metadata"]["agent_id"] == TEST_AGENT_ID

def test_update_and_get_redis(mock_redis):
    """Test updating and getting context with Redis backend."""
    # Setup mock
    test_context = {
        "data": TEST_DATA,
        "metadata": {
            "agent_id": TEST_AGENT_ID,
            "timestamp": datetime.utcnow().isoformat(),
            "context_id": "test_context_123",
            "version": "1.0"
        }
    }
    mock_redis.get.return_value = json.dumps(test_context)
    
    # Test with Redis
    mcp = MCPContextManager(redis_client=mock_redis)
    
    # Test update
    context_id = mcp.update(TEST_AGENT_ID, TEST_DATA)
    assert context_id is not None
    
    # Verify Redis was called correctly
    mock_redis.set.assert_called_once()
    mock_redis.lpush.assert_called_once()
    
    # Test get
    result = mcp.get("test_context_123")
    assert result == test_context
    mock_redis.get.assert_called_with("mcp:test_context_123")

def test_search_by_agent_id(mock_redis):
    """Test searching for context by agent ID."""
    # Setup mock
    test_contexts = []
    for i in range(3):
        context_id = f"test_context_{i}"
        context = {
            "data": {"data": f"test_{i}"},
            "metadata": {
                "agent_id": TEST_AGENT_ID,
                "timestamp": datetime.utcnow().isoformat(),
                "context_id": context_id,
                "version": "1.0"
            }
        }
        test_contexts.append(context)
        
        # Mock Redis get for this context
            
    # Mock Redis lrange to return the context IDs
    mock_redis.lrange.return_value = [
        context["metadata"]["context_id"].encode() 
        for context in test_contexts
    ]
    
    # Mock Redis get to return the appropriate context
    def mock_get(key):
        if key.startswith("mcp:test_context_"):
            ctx_id = key.split(":")[1]
            for ctx in test_contexts:
                if ctx["metadata"]["context_id"] == ctx_id:
                    return json.dumps(ctx)
        return None
        
    mock_redis.get.side_effect = mock_get
    
    # Initialize MCP with mocked Redis
    mcp = MCPContextManager(redis_client=mock_redis)
    
    # Search for agent's context with limit 2
    results = mcp.search(agent_id=TEST_AGENT_ID, limit=2)
    
    # Verify results
    assert len(results) == 2  # Should respect limit
    assert all(
        result["metadata"]["agent_id"] == TEST_AGENT_ID 
        for result in results
    )
    
    # Verify Redis was called correctly
    mock_redis.lrange.assert_called_once_with(
        f"mcp:agent:{TEST_AGENT_ID}:history", 0, 1  # 0 to limit-1
    )

def test_clear_context():
    """Test clearing context entries."""
    mcp = MCPContextManager()
    
    # Add test data
    context_id = mcp.update(TEST_AGENT_ID, TEST_DATA)
    assert mcp.get(context_id) is not None
    
    # Clear specific context
    assert mcp.clear(context_id) is True
    assert mcp.get(context_id) is None
    
    # Clear all
    mcp.update(TEST_AGENT_ID, TEST_DATA)
    assert mcp.clear() is True
    assert len(mcp.search(agent_id=TEST_AGENT_ID)) == 0

@pytest.mark.asyncio
async def test_base_agent_lifecycle():
    """Test the base agent lifecycle."""
    from agents.base_agent import BaseAgent, AgentState
    
    class TestAgent(BaseAgent):
        async def _setup(self):
            self.test_setup = True
            
        async def _execute(self, task):
            return {"result": "success", "task": task}
    
    # Initialize
    mcp = MCPContextManager()
    agent = TestAgent("test_agent", mcp)
    
    # Test initialization
    assert not hasattr(agent, 'test_setup')
    await agent.initialize()
    assert agent.test_setup is True
    assert agent.get_state().status == "ready"
    
    # Test execution
    task = {"task_id": "test_task_1", "action": "test"}
    result = await agent.execute(task)
    assert result["status"] == "success"
    assert result["result"]["task"] == task
    
    # Test cleanup
    await agent.cleanup()
    assert agent.get_state().status == "stopped"

if __name__ == "__main__":
    pytest.main(["-v", "tests/test_context_manager.py"])
