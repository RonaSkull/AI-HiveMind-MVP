import os
from dotenv import load_dotenv
from mcp.context_manager import MCPContextManager

def test_mcp_operations():
    print("Testing MCP Context Manager...")
    load_dotenv('.env.development')
    
    # Initialize MCP
    mcp = MCPContextManager()
    
    # Test 1: Basic Update and Get
    print("\nTest 1: Basic Update and Get")
    test_data = {"test": "data", "number": 42}
    
    # Store test value (synchronous)
    context_id = mcp.update("test_agent", test_data)
    print(f"✅ Stored test data with ID: {context_id}")
    
    # Retrieve test value (synchronous)
    retrieved = mcp.get(context_id)
    print(f"✅ Retrieved test data: {retrieved}")
    
    # Clean up (synchronous)
    mcp.clear(context_id)
    print("✅ Cleaned up test data")
    
    # Verify cleanup
    cleared = mcp.get(context_id)
    print(f"✅ Context after clear: {cleared}")
    
    return True

if __name__ == "__main__":
    test_mcp_operations()