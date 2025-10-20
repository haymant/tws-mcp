#!/usr/bin/env python3
"""Check what the MCP HTTP app provides"""
import asyncio
from mcp.server.fastmcp import FastMCP

async def main():
    mcp = FastMCP("Test Server")
    
    # Add a simple tool
    @mcp.tool()
    async def test_tool() -> dict:
        """A test tool"""
        return {"status": "ok"}
    
    # Get the HTTP app
    http_app = mcp.streamable_http_app()
    
    print(f"HTTP app type: {type(http_app)}")
    print(f"HTTP app class: {http_app.__class__.__name__}")
    
    # Check if it has routes
    if hasattr(http_app, 'routes'):
        print(f"\nRoutes in HTTP app:")
        for route in http_app.routes:
            print(f"  - {route}")
    
    # Check available attributes
    print(f"\nAttributes on HTTP app:")
    for attr in dir(http_app):
        if not attr.startswith('_'):
            print(f"  - {attr}")

if __name__ == "__main__":
    asyncio.run(main())
