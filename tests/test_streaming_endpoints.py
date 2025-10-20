#!/usr/bin/env python3
"""
Test script for HTTP streaming and WebSocket endpoints.

This script tests:
1. Health check endpoint
2. MCP HTTP streaming endpoint
3. WebSocket streaming endpoints
"""

import asyncio
import httpx
import websockets
import json
import sys


async def test_health_check():
    """Test the /health endpoint."""
    print("\n📋 Testing Health Check...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                data = response.json()
                print("✅ Health check passed!")
                print(f"   Status: {data['status']}")
                print(f"   TWS Connected: {data.get('tws_connected', 'unknown')}")
                print(f"   Endpoints: {list(data['endpoints'].keys())}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


async def test_mcp_http():
    """Test the MCP HTTP streaming endpoint."""
    print("\n📡 Testing MCP HTTP Endpoint...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test ibkr_get_status tool
            response = await client.post(
                "http://localhost:8000/api/v1/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "ibkr_get_status"
                    },
                    "id": 1
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ MCP HTTP endpoint working!")
                print(f"   Response: {result}")
                return True
            else:
                print(f"❌ MCP HTTP failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
    except Exception as e:
        print(f"❌ MCP HTTP error: {e}")
        return False


async def test_websocket_market_data():
    """Test the WebSocket market data endpoint."""
    print("\n📊 Testing WebSocket Market Data...")
    try:
        async with websockets.connect('ws://localhost:8000/api/v1/stream/market-data') as ws:
            # Receive connection message
            msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(msg)
            
            if data.get("type") == "connected":
                print("✅ WebSocket market data endpoint connected!")
                print(f"   Message: {data.get('message', '')}")
                
                # Test ping/pong
                await ws.send(json.dumps({"action": "ping"}))
                pong = await asyncio.wait_for(ws.recv(), timeout=5.0)
                pong_data = json.loads(pong)
                
                if pong_data.get("type") == "pong":
                    print("✅ Ping/pong working!")
                    return True
                else:
                    print(f"❌ Unexpected pong response: {pong_data}")
                    return False
            else:
                print(f"❌ Unexpected connection message: {data}")
                return False
    except asyncio.TimeoutError:
        print("❌ WebSocket connection timeout")
        return False
    except Exception as e:
        print(f"❌ WebSocket market data error: {e}")
        return False


async def test_websocket_portfolio():
    """Test the WebSocket portfolio endpoint."""
    print("\n💼 Testing WebSocket Portfolio...")
    try:
        async with websockets.connect('ws://localhost:8000/api/v1/stream/portfolio') as ws:
            # Receive connection message
            msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(msg)
            
            if data.get("type") == "connected":
                print("✅ WebSocket portfolio endpoint connected!")
                print(f"   Message: {data.get('message', '')}")
                return True
            else:
                print(f"❌ Unexpected connection message: {data}")
                return False
    except asyncio.TimeoutError:
        print("❌ WebSocket connection timeout")
        return False
    except Exception as e:
        print(f"❌ WebSocket portfolio error: {e}")
        return False


async def test_websocket_news():
    """Test the WebSocket news endpoint."""
    print("\n📰 Testing WebSocket News...")
    try:
        async with websockets.connect('ws://localhost:8000/api/v1/stream/news') as ws:
            # Receive connection message
            msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(msg)
            
            if data.get("type") == "connected":
                print("✅ WebSocket news endpoint connected!")
                print(f"   Message: {data.get('message', '')}")
                return True
            else:
                print(f"❌ Unexpected connection message: {data}")
                return False
    except asyncio.TimeoutError:
        print("❌ WebSocket connection timeout")
        return False
    except Exception as e:
        print(f"❌ WebSocket news error: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("HTTP Streaming & WebSocket Test Suite")
    print("=" * 60)
    print("\nMake sure the server is running: uv run python main.py")
    print("=" * 60)
    
    results = []
    
    # Test health check
    results.append(("Health Check", await test_health_check()))
    
    # Test MCP HTTP
    results.append(("MCP HTTP", await test_mcp_http()))
    
    # Test WebSocket endpoints
    results.append(("WebSocket Market Data", await test_websocket_market_data()))
    results.append(("WebSocket Portfolio", await test_websocket_portfolio()))
    results.append(("WebSocket News", await test_websocket_news()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"Total: {passed + failed} tests, {passed} passed, {failed} failed")
    print("=" * 60)
    
    # Exit with error code if any tests failed
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
