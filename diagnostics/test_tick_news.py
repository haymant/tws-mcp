#!/usr/bin/env python3
"""
Test tick news streaming with real-time headlines.
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
    print("=== Testing Tick News (Real-Time Headlines) ===\n")
    
    # Step 1: Connect to TWS
    print("1. Connecting to TWS...")
    result = make_request("tools/call", {
        "name": "ibkr_connect",
        "arguments": {
            "host": "127.0.0.1",
            "port": 7497,
            "clientId": 3
        }
    })
    print(f"   Status: {result.get('result', {}).get('status', 'unknown')}\n")
    
    # Step 2: Start tick news for AAPL
    print("2. Starting tick news stream for AAPL...")
    result = make_request("tools/call", {
        "name": "ibkr_start_tick_news_resource",
        "arguments": {
            "symbol": "AAPL",
            "secType": "STK",
            "exchange": "SMART",
            "currency": "USD"
        }
    })
    print(f"   Result: {json.dumps(json.loads(result['result']), indent=2)}\n")
    
    # Step 3: Start tick news for MSFT
    print("3. Starting tick news stream for MSFT...")
    result = make_request("tools/call", {
        "name": "ibkr_start_tick_news_resource",
        "arguments": {
            "symbol": "MSFT"
        }
    })
    print(f"   Result: {json.dumps(json.loads(result['result']), indent=2)}\n")
    
    # Step 4: Enable "all news" aggregation
    print("4. Enabling all-news aggregation...")
    result = make_request("tools/call", {
        "name": "ibkr_start_tick_news_resource",
        "arguments": {
            "symbol": "*"
        }
    })
    print(f"   Result: {json.dumps(json.loads(result['result']), indent=2)}\n")
    
    # Step 5: Wait for news
    print("5. Waiting 60 seconds for news headlines...")
    print("   (News will appear as they arrive in real-time)")
    time.sleep(60)
    
    # Step 6: Read AAPL news
    print("\n6. Reading tick news for AAPL...")
    result = make_request("resources/read", {
        "uri": "ibkr://tick-news/AAPL"
    })
    if 'result' in result and 'contents' in result['result']:
        content = result['result']['contents'][0]['text']
        data = json.loads(content)
        print(f"   News count: {data.get('count', 0)}")
        if data.get('news_items'):
            print(f"   Latest headline: {data['news_items'][-1].get('headline', 'N/A')}\n")
    
    # Step 7: Read all news
    print("7. Reading all tick news...")
    result = make_request("resources/read", {
        "uri": "ibkr://tick-news/*"
    })
    if 'result' in result and 'contents' in result['result']:
        content = result['result']['contents'][0]['text']
        data = json.loads(content)
        print(f"   Total news items: {data.get('total_count', 0)}")
        print(f"   Subscribed symbols: {data.get('subscribed_symbols', [])}")
        if data.get('news_items'):
            print(f"\n   Latest 5 headlines:")
            for i, item in enumerate(data['news_items'][:5], 1):
                print(f"   {i}. [{item.get('symbol', '?')}] {item.get('headline', 'N/A')[:80]}...")
    
    # Step 8: List active streams
    print("\n8. Listing active streams...")
    result = make_request("tools/call", {
        "name": "ibkr_list_active_resource_streams",
        "arguments": {}
    })
    data = json.loads(result['result'])
    print(f"   Tick news streams: {data.get('tick_news', {}).get('count', 0)}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
