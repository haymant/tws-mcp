#!/usr/bin/env python3
"""Quick test of MCP server endpoints"""
import asyncio
import httpx

async def test():
    base = "http://localhost:8000"
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test SSE endpoint
        print("Testing /api/v1/sse endpoint...")
        try:
            response = await client.get(f"{base}/api/v1/sse")
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
