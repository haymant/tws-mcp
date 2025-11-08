#!/usr/bin/env python3
"""Test script to verify the modular structure loads correctly."""

import sys
import asyncio
from pathlib import Path

# Add parent to path to allow 'from src.tools import ...'
sys.path.insert(0, str(Path(__file__).parent))

async def test_imports():
    """Test that all modules can be imported."""
    print("Testing modular structure imports...")
    
    try:
        # Test tool imports
        print("\n1. Testing tool module imports...")
        from src.tools import (
            register_connection_tools,
            register_contract_tools,
            register_market_data_tools,
            register_order_tools,
            register_account_tools,
            register_news_tools,
            register_options_tools,
            register_scanner_tools,
            register_advanced_tools
        )
        print("   ✅ All 9 tool modules imported successfully")
        
        # Test resource imports
        print("\n2. Testing resource module imports...")
        from src.resources import (
            register_market_data_resource,
            register_portfolio_resource,
            register_news_resource
        )
        print("   ✅ All 3 resource modules imported successfully")
        
        # Test models
        print("\n3. Testing models...")
        from src.models import AppContext
        print("   ✅ AppContext imported successfully")
        
        # Test server
        print("\n4. Testing server imports...")
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("Test Server")
        print("   ✅ FastMCP server created")
        
        # Register all tools
        print("\n5. Registering all tools...")
        register_connection_tools(mcp)
        register_contract_tools(mcp)
        register_market_data_tools(mcp)
        register_order_tools(mcp)
        register_account_tools(mcp)
        register_news_tools(mcp)
        register_options_tools(mcp)
        register_scanner_tools(mcp)
        register_advanced_tools(mcp)
        
        # Count registered tools
        tools = await mcp.list_tools()
        tool_count = len(tools)
        print(f"   ✅ Registered {tool_count} tools successfully")
        
        # List all tools by category
        print("\n6. Tool breakdown by category:")
        
        # Group by prefix
        categories = {}
        for tool in tools:
            name = tool.name
            if name.startswith('ibkr_'):
                # Extract category (connection, order, etc.)
                parts = name.split('_')[1:]
                if parts:
                    category = parts[0] if len(parts) > 1 else 'other'
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(name)
        
        for category, tool_names in sorted(categories.items()):
            print(f"   - {category}: {len(tool_names)} tools")
            for tool_name in sorted(tool_names):
                print(f"     • {tool_name}")
        
        print("\n" + "="*60)
        print("✅ MODULAR STRUCTURE TEST PASSED")
        print(f"   Total tools: {tool_count}")
        print(f"   Tool modules: 9")
        print(f"   Resource modules: 3")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the test."""
    success = asyncio.run(test_imports())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
