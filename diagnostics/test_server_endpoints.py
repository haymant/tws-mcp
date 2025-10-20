#!/usr/bin/env python3
"""Test the MCP server endpoints"""
import asyncio
import httpx

async def test_endpoints():
    # Wait a bit for server to start
    await asyncio.sleep(2)
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        # Test various endpoints
        endpoints = [
            "/api/v1",
            "/api/v1/",
            "/api/v1/mcp",
        ]
        
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"
            try:
                response = await client.get(url)
                print(f"\nGET {endpoint}")
                print(f"  Status: {response.status_code}")
                print(f"  Headers: {dict(response.headers)}")
                if response.status_code < 500:
                    content = response.text[:200]
                    print(f"  Content: {content}...")
            except Exception as e:
                print(f"\nGET {endpoint}")
                print(f"  Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
