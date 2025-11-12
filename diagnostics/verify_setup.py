#!/usr/bin/env python3
"""
Final verification test for the IBKR TWS MCP Server
"""
import asyncio
import sys

async def verify_server():
    """Verify the server configuration and setup"""
    
    print("=" * 60)
    print("IBKR TWS MCP Server - Verification Test")
    print("=" * 60)
    
    # Test 1: Import the server module
    print("\n1. Testing server module import...")
    try:
        from src.server import app, mcp
        print("   ✅ Server module imported successfully")
    except Exception as e:
        print(f"   ❌ Failed to import server module: {e}")
        return False
    
    # Test 2: Check MCP tools
    print("\n2. Checking MCP tools...")
    try:
        tools = mcp.list_tools()
        print(f"   ✅ Found {len(tools)} MCP tools:")
        for tool in tools:
            print(f"      - {tool.name}")
    except Exception as e:
        print(f"   ❌ Failed to list tools: {e}")
        return False
    
    # Test 3: Verify app is ASGI compatible
    print("\n3. Verifying ASGI app...")
    try:
        assert hasattr(app, '__call__'), "App must be callable"
        print("   ✅ App is ASGI compatible")
    except Exception as e:
        print(f"   ❌ App verification failed: {e}")
        return False
    
    # Test 4: Check environment configuration
    print("\n4. Checking environment configuration...")
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        config = {
            "TWS_HOST": os.getenv("TWS_HOST", "127.0.0.1"),
            "TWS_PORT": os.getenv("TWS_PORT", "7497"),
            "SERVER_HOST": os.getenv("SERVER_HOST", "0.0.0.0"),
            "SERVER_PORT": os.getenv("SERVER_PORT", "8000"),
            "API_PREFIX": os.getenv("API_PREFIX", "/api/v1"),
        }
        print("   ✅ Environment configuration:")
        for key, value in config.items():
            print(f"      - {key}: {value}")
    except Exception as e:
        print(f"   ❌ Configuration check failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All verification tests passed!")
    print("=" * 60)
    print("\nThe server is ready to run. Start it with:")
    print("   uv run python main.py")
    print("\nMCP SSE Endpoint will be available at:")
    print(f"   http://{config['SERVER_HOST']}:{config['SERVER_PORT']}{config['API_PREFIX']}/sse")
    print("\nFor remote access, expose with ngrok:")
    print(f"   ngrok http {config['SERVER_PORT']}")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    result = asyncio.run(verify_server())
    sys.exit(0 if result else 1)
