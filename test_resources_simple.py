#!/usr/bin/env python3
"""Simple test to check resources list via curl-like request"""

import asyncio
import httpx
import json
import re

async def test():
    url = "http://localhost:8000/api/v1/mcp"
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Initialize
        print("=== INITIALIZING ===")
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"resources": {"subscribe": True}},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        }
        resp = await client.post(url, json=init_req, headers=headers)
        session_id = resp.headers.get("Mcp-Session-Id")
        print(f"Session ID: {session_id}\n")
        
        # List resources
        print("=== LISTING RESOURCES ===")
        headers["Mcp-Session-Id"] = session_id
        list_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "resources/list",
            "params": {}
        }
        resp = await client.post(url, json=list_req, headers=headers)
        print(f"Status: {resp.status_code}")
        
        # Parse SSE
        text = resp.text
        if "event: message" in text:
            # Extract JSON from SSE
            match = re.search(r'data: (.+)', text)
            if match:
                data = json.loads(match.group(1))
                if "result" in data:
                    resources = data["result"].get("resources", [])
                    print(f"Number of resources: {len(resources)}")
                    for res in resources:
                        print(f"  - {res.get('uri')} ({res.get('name')})")
                        if res.get('description'):
                            print(f"    {res['description'][:80]}...")
                else:
                    print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Raw response: {text[:500]}")

if __name__ == "__main__":
    asyncio.run(test())
