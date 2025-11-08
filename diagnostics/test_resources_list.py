#!/usr/bin/env python3
"""Test script to check resources/list endpoint"""

import asyncio
import httpx
import json

async def test_resources_list():
    url = "http://localhost:8000/api/v1/mcp"
    
    # First, initialize the session
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "resources": {"subscribe": True}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    # Headers required by StreamableHTTP
    base_headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        print("1. Initializing session...")
        init_response = await client.post(url, json=init_request, headers=base_headers)
        print(f"Init status: {init_response.status_code}")
        print(f"Content-Type: {init_response.headers.get('Content-Type')}")
        print(f"Raw content (first 200 chars): {init_response.text[:200]}")
        
        # Parse SSE if needed
        if "text/event-stream" in init_response.headers.get("Content-Type", ""):
            print("Response is SSE format, parsing...")
            lines = init_response.text.strip().split("\n")
            for line in lines[:10]:
                print(f"  {line}")
        else:
            init_data = init_response.json()
            print(f"Init response: {json.dumps(init_data, indent=2)}")
        
        # Get session ID from headers or response
        session_id = init_response.headers.get("Mcp-Session-Id")
        print(f"Session ID: {session_id}")
        
        # Now list resources
        print("\n2. Listing resources...")
        list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "resources/list",
            "params": {}
        }
        
        headers = base_headers.copy()
        if session_id:
            headers["Mcp-Session-Id"] = session_id
            
        list_response = await client.post(url, json=list_request, headers=headers)
        print(f"List status: {list_response.status_code}")
        list_data = list_response.json()
        print(f"List response: {json.dumps(list_data, indent=2)}")
        
        # List tools for comparison
        print("\n3. Listing tools...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/list",
            "params": {}
        }
        tools_response = await client.post(url, json=tools_request, headers=headers)
        print(f"Tools status: {tools_response.status_code}")
        tools_data = tools_response.json()
        if "result" in tools_data and "tools" in tools_data["result"]:
            print(f"Number of tools: {len(tools_data['result']['tools'])}")
            # Show first few tools
            for tool in tools_data["result"]["tools"][:3]:
                print(f"  - {tool.get('name')}")
        else:
            print(f"Tools response: {json.dumps(tools_data, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_resources_list())
