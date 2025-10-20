#!/usr/bin/env python3
"""Check what the MCP SSE app provides"""
import asyncio
from mcp.server.fastmcp import FastMCP

async def main():
    mcp = FastMCP("Test Server")
    
    # Add a simple tool
    @mcp.tool()
    async def test_tool() -> dict:
        """A test tool"""
        return {"status": "ok"}
    
    # Get the SSE app
    sse_app = mcp.sse_app()
    
    print(f"SSE app type: {type(sse_app)}")
    print(f"SSE app class: {sse_app.__class__.__name__}")
    
    # Check if it has routes
    if hasattr(sse_app, 'routes'):
        print(f"\nRoutes in SSE app:")
        for route in sse_app.routes:
            print(f"  - Path: {route.path if hasattr(route, 'path') else 'N/A'}")
            print(f"    Name: {route.name if hasattr(route, 'name') else 'N/A'}")
            print(f"    Methods: {route.methods if hasattr(route, 'methods') else 'N/A'}")
    
    # Check available attributes
    print(f"\nAttributes on SSE app:")
    for attr in dir(sse_app):
        if not attr.startswith('_') and 'route' in attr.lower():
            print(f"  - {attr}")

if __name__ == "__main__":
    asyncio.run(main())
