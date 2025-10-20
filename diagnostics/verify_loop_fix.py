#!/usr/bin/env python3
"""
Verification test: Demonstrate that TWSClient.connect() now works
across different event loops without "Future attached to different loop" errors.
"""
import asyncio
from src.tws_client import TWSClient

async def test_in_loop_1():
    """Simulate server startup - creates TWSClient in one loop"""
    print("Loop 1: Creating TWSClient...")
    client = TWSClient()
    print(f"  - Created IB instance: {client.ib}")
    return client

async def test_in_loop_2(client):
    """Simulate MCP tool call - uses TWSClient in different loop"""
    print("\nLoop 2: Calling connect() from different loop...")
    print(f"  - Existing IB instance: {client.ib}")
    
    try:
        # This would fail with "different loop" error before the fix
        # Now it works because connect() recreates the IB instance
        await client.connect("127.0.0.1", 7496, 1)
        print("  ✗ Connect succeeded (TWS not running - unexpected)")
    except ConnectionError as e:
        # Expected: connection fails because TWS is not running
        # But importantly, NO "different loop" error!
        print(f"  ✓ Connect failed as expected (TWS not running)")
        print(f"  ✓ No 'different loop' error!")
        print(f"  - Error was: {str(e)[:100]}")
        return True
    except RuntimeError as e:
        if "different loop" in str(e):
            print(f"  ✗ FAILED: Still getting 'different loop' error!")
            print(f"  - Error: {e}")
            return False
        else:
            raise

def main():
    print("=== Testing TWSClient across different event loops ===\n")
    
    # Simulate server startup in loop 1
    client = asyncio.run(test_in_loop_1())
    
    # Simulate MCP tool invocation in loop 2
    success = asyncio.run(test_in_loop_2(client))
    
    if success:
        print("\n✓ SUCCESS: TWSClient works across different event loops!")
        return 0
    else:
        print("\n✗ FAILURE: Event loop error still present")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
