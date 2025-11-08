#!/usr/bin/env python
"""
Test streaming tool behavior with FastMCP.

This script tests whether FastMCP properly handles async generator tools
and streams their results.
"""

import asyncio
from mcp.server.fastmcp import FastMCP
import json

# Create test server
mcp = FastMCP("test-streaming")

@mcp.tool()
async def test_normal_tool(value: str):
    """Normal tool that returns a single result."""
    return {"type": "result", "value": value}

@mcp.tool()
async def test_streaming_tool(value: str):
    """Streaming tool that yields multiple results."""
    yield {"type": "start", "value": value}
    await asyncio.sleep(0.1)
    yield {"type": "update1", "value": value}
    await asyncio.sleep(0.1)
    yield {"type": "update2", "value": value}
    await asyncio.sleep(0.1)
    yield {"type": "end", "value": value}

async def main():
    # Get the MCP server instance
    server = mcp._mcp_server
    
    print("=" * 60)
    print("Testing Normal Tool")
    print("=" * 60)
    
    # Call normal tool
    result = await test_normal_tool("test1")
    print(f"Normal tool result: {json.dumps(result, indent=2)}")
    
    print("\n" + "=" * 60)
    print("Testing Streaming Tool")
    print("=" * 60)
    
    # Call streaming tool
    result = test_streaming_tool("test2")
    print(f"Streaming tool returns: {result}")
    print(f"Type: {type(result)}")
    
    # Try to iterate
    if hasattr(result, '__aiter__'):
        print("\nIterating over async generator:")
        async for item in result:
            print(f"  Yielded: {json.dumps(item, indent=4)}")
    else:
        print(f"\nNot an async generator, result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
