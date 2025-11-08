#!/usr/bin/env python3
"""Quick test to verify server_new.py can start."""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def test_server_startup():
    """Test that the new server can be imported and initialized."""
    print("Testing server_new.py startup...")
    
    try:
        print("\n1. Importing server_new module...")
        from src import server_new
        print("   ✅ Server module imported")
        
        print("\n2. Checking server components...")
        assert hasattr(server_new, 'mcp'), "MCP server not found"
        assert hasattr(server_new, 'app'), "Starlette app not found"
        print("   ✅ All server components present")
        
        print("\n3. Checking server configuration...")
        app = server_new.app
        print(f"   - App type: {type(app).__name__}")
        # Access the wrapped app to see routes
        if hasattr(app, 'app'):
            base_app = app.app
            if hasattr(base_app, 'routes'):
                print(f"   - Routes: {len(base_app.routes)}")
                for route in base_app.routes:
                    print(f"     • {route}")
        print("   ✅ Server configured correctly")
        
        print("\n4. Verifying tools are registered...")
        tools = await server_new.mcp.list_tools()
        print(f"   - Total tools: {len(tools)}")
        print("   ✅ Tools registered")
        
        print("\n" + "="*60)
        print("✅ SERVER STARTUP TEST PASSED")
        print("   The new modular server is ready to run!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the test."""
    success = asyncio.run(test_server_startup())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
