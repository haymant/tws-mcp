#!/usr/bin/env python3
"""
Subscribe to all news from your TWS watchlist.
This replicates the news you see in TWS Station's News tab.
"""
import json
import time
import urllib.request
import urllib.parse

BASE_URL = "http://localhost:8000/api/v1/mcp"

# YOUR WATCHLIST - Update this with the symbols you want to track!
# These should match the symbols in your TWS Station watchlist
WATCHLIST = [
    "AAPL",   # Apple
    "MSFT",   # Microsoft
    "GOOGL",  # Google
    "AMZN",   # Amazon
    "TSLA",   # Tesla
    "NVDA",   # NVIDIA
    "META",   # Meta (Facebook)
    "AMD",    # AMD
    "INTC",   # Intel
    "NFLX",   # Netflix
]

def call_tool(name, arguments):
    """Call an MCP tool."""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
        "id": 1
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        BASE_URL,
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        # Read error response
        error_body = e.read().decode('utf-8')
        print(f"   HTTP Error {e.code}: {error_body}")
        raise

def read_resource(uri):
    """Read an MCP resource."""
    payload = {
        "jsonrpc": "2.0",
        "method": "resources/read",
        "params": {"uri": uri},
        "id": 1
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        BASE_URL,
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        # Read error response
        error_body = e.read().decode('utf-8')
        print(f"   HTTP Error {e.code}: {error_body}")
        raise

def main():
    print("=" * 70)
    print("  Subscribing to News from TWS Watchlist")
    print("=" * 70)
    print()
    
    # 1. Connect to TWS
    print("Step 1: Connecting to TWS...")
    try:
        result = call_tool("ibkr_connect", {
            "host": "127.0.0.1",
            "port": 7497,
            "clientId": 10
        })
        
        if 'result' in result:
            response = json.loads(result['result'])
            status = response.get('status', 'unknown')
            
            if status == 'connected':
                print(f"   ✓ Status: {status}\n")
            elif 'already connected' in str(response).lower() or 'error' in response:
                # Already connected, check status instead
                print(f"   Already connected or connection attempt failed")
                print(f"   Checking connection status...\n")
                status_result = call_tool("ibkr_get_status", {})
                if 'result' in status_result:
                    status_data = json.loads(status_result['result'])
                    if status_data.get('is_connected'):
                        print(f"   ✓ TWS is connected\n")
                    else:
                        print(f"   ✗ TWS is not connected. Start TWS and try again.\n")
                        return
            else:
                print(f"   Status: {status}\n")
        else:
            error = result.get('error', {})
            print(f"   Note: {error.get('message', 'Connection issue')}")
            print(f"   Checking if already connected...\n")
            
            # Try to check status anyway
            status_result = call_tool("ibkr_get_status", {})
            if 'result' in status_result:
                status_data = json.loads(status_result['result'])
                if status_data.get('is_connected'):
                    print(f"   ✓ TWS is already connected, proceeding\n")
                else:
                    print(f"   ✗ TWS is not connected. Start TWS and try again.\n")
                    return
    except Exception as e:
        print(f"   Error during connection: {e}")
        print(f"   Checking if TWS is already connected...\n")
        try:
            status_result = call_tool("ibkr_get_status", {})
            if 'result' in status_result:
                status_data = json.loads(status_result['result'])
                if status_data.get('is_connected'):
                    print(f"   ✓ TWS is already connected, proceeding\n")
                else:
                    print(f"   ✗ TWS is not connected. Start TWS and try again.\n")
                    return
        except Exception as e2:
            print(f"   ✗ Cannot verify TWS connection: {e2}\n")
            return
    
    # 2. Subscribe to each symbol in watchlist
    print(f"Step 2: Subscribing to {len(WATCHLIST)} symbols from watchlist...")
    subscribed = []
    failed = []
    
    for symbol in WATCHLIST:
        try:
            print(f"   Subscribing to {symbol:6s}... ", end='', flush=True)
            result = call_tool("ibkr_start_tick_news_resource", {
                "symbol": symbol,
                "secType": "STK",
                "exchange": "SMART",
                "currency": "USD"
            })
            
            if 'result' in result:
                response = json.loads(result['result'])
                status = response.get('status', 'unknown')
                
                if status in ['subscribed', 'already_subscribed']:
                    print(f"✓ {status}")
                    subscribed.append(symbol)
                else:
                    print(f"✗ {status}")
                    failed.append(symbol)
            else:
                print(f"✗ Error")
                failed.append(symbol)
                
        except Exception as e:
            print(f"✗ {str(e)[:40]}")
            failed.append(symbol)
        
        time.sleep(0.1)  # Small delay between subscriptions
    
    print()
    print(f"   Subscribed: {len(subscribed)}/{len(WATCHLIST)} symbols")
    if failed:
        print(f"   Failed: {', '.join(failed)}")
    print()
    
    # 3. Enable aggregation
    print("Step 3: Enabling news aggregation mode...")
    result = call_tool("ibkr_start_tick_news_resource", {
        "symbol": "*"
    })
    
    if 'result' in result:
        response = json.loads(result['result'])
        print(f"   ✓ {response.get('message', 'Enabled')}")
        if 'warning' in response:
            print(f"   Note: {response['warning']}")
    print()
    
    # 4. Wait for news to arrive
    print("Step 4: Waiting for news to arrive...")
    print("   (News will appear in server logs as it streams in)")
    print("   Waiting 60 seconds...\n")
    
    for i in range(60, 0, -10):
        print(f"   {i} seconds remaining...")
        time.sleep(10)
    
    print()
    
    # 5. Read all aggregated news
    print("Step 5: Reading all news from subscribed symbols...")
    try:
        result = read_resource("ibkr://tick-news/*")
        
        if 'result' in result and 'contents' in result['result']:
            content = result['result']['contents'][0]['text']
            data = json.loads(content)
            
            total = data.get('total_count', 0)
            symbols = data.get('subscribed_symbols', [])
            items = data.get('news_items', [])
            
            print(f"   Total news items collected: {total}")
            print(f"   Symbols with subscriptions: {', '.join(symbols)}")
            print()
            
            if items:
                print("   Latest 15 headlines:")
                print("   " + "-" * 66)
                for i, item in enumerate(items[:15], 1):
                    symbol = item.get('symbol', '?')
                    headline = item.get('headline', 'N/A')
                    provider = item.get('providerCode', '?')
                    
                    # Truncate headline to fit
                    max_len = 60
                    if len(headline) > max_len:
                        headline = headline[:max_len-3] + "..."
                    
                    print(f"   {i:2d}. [{symbol:6s}] {headline}")
                    print(f"       Provider: {provider}")
                print("   " + "-" * 66)
            else:
                print("   No news items received yet.")
                print("   News may take a few minutes to start flowing.")
        else:
            print(f"   Error reading resource: {result}")
    
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    print("=" * 70)
    print("  Subscription Complete!")
    print("=" * 70)
    print()
    print("Your MCP server is now streaming news for your watchlist.")
    print("News notifications will arrive in real-time as headlines appear.")
    print()
    print("To read news anytime:")
    print("  - Symbol-specific: resources.read('ibkr://tick-news/AAPL')")
    print("  - All news:        resources.read('ibkr://tick-news/*')")
    print()
    print("To stop news for a symbol:")
    print("  tools.call('ibkr_stop_tick_news_resource', {symbol: 'AAPL'})")
    print()
    print("Check server logs to see news arriving: tail -f /tmp/mcp_server.log")
    print()

if __name__ == "__main__":
    main()
