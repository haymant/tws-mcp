#!/usr/bin/env python3
"""
Test news bulletins streaming with the MCP server.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1/mcp"

def make_request(method, params=None):
    """Make a JSON-RPC request to the MCP server."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1
    }
    
    response = requests.post(BASE_URL, json=payload)
    return response.json()

def main():
    print("=== Testing News Bulletins Streaming ===\n")
    
    # Step 1: Connect to TWS
    print("1. Connecting to TWS...")
    result = make_request("tools/call", {
        "name": "ibkr_connect",
        "arguments": {
            "host": "127.0.0.1",
            "port": 7496,
            "clientId": 1
        }
    })
    print(f"   Connection result: {json.dumps(result, indent=2)}\n")
    
    # Step 2: Start news resource
    print("2. Starting news bulletins resource...")
    result = make_request("tools/call", {
        "name": "ibkr_start_news_resource",
        "arguments": {
            "allMessages": True
        }
    })
    print(f"   Start result: {json.dumps(result, indent=2)}\n")
    
    # Step 3: Wait for news bulletins to arrive
    print("3. Waiting for news bulletins (30 seconds)...")
    print("   (Check TWS Station News tab to see if news is flowing)")
    time.sleep(30)
    
    # Step 4: Read the news resource
    print("\n4. Reading news bulletins resource...")
    result = make_request("resources/read", {
        "uri": "ibkr://news-bulletins"
    })
    print(f"   News bulletins: {json.dumps(result, indent=2)}\n")
    
    # Step 5: List active streams
    print("5. Listing active resource streams...")
    result = make_request("tools/call", {
        "name": "ibkr_list_active_resource_streams",
        "arguments": {}
    })
    print(f"   Active streams: {json.dumps(result, indent=2)}\n")
    
    print("=== Test Complete ===")

if __name__ == "__main__":
    main()
