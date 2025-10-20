#!/usr/bin/env python3
"""
Test script to verify streaming tools event loop fix.

This script tests:
1. ibkr_stream_market_data completes within 10 seconds
2. ibkr_stream_account_updates doesn't throw event loop error
3. Session remains stable after streaming tools complete
"""

import asyncio
import time
from src.tws_client import TWSClient
from src.models import ContractRequest

async def test_stream_market_data():
    """Test that stream_market_data uses non-blocking callback approach."""
    print("=" * 80)
    print("TEST 1: stream_market_data non-blocking callback")
    print("=" * 80)
    
    client = TWSClient()
    
    try:
        # Connect
        print("Connecting to TWS...")
        await client.connect()
        print(f"Connected: {client.is_connected()}")
        
        # Test market data streaming
        req = ContractRequest(symbol="AAPL", secType="STK", exchange="SMART", currency="USD")
        
        print(f"\nStreaming market data for AAPL (10 seconds)...")
        start = time.monotonic()
        update_count = 0
        
        async for update in client.stream_market_data(req):
            elapsed = time.monotonic() - start
            if elapsed >= 10:
                print(f"Duration limit reached: {elapsed:.1f}s")
                break
            
            if update:  # Non-empty update
                update_count += 1
                print(f"  [{elapsed:.1f}s] Update {update_count}: {update}")
            
            # Check if we're over time
            if elapsed > 12:
                print("WARNING: Exceeded 12 seconds, breaking")
                break
        
        elapsed = time.monotonic() - start
        print(f"\nCompleted in {elapsed:.1f} seconds")
        print(f"Total updates: {update_count}")
        
        if elapsed <= 12:
            print("✅ PASS: Completed within time limit")
        else:
            print("❌ FAIL: Took too long")
        
    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if client.is_connected():
            await client.disconnect()
            print("Disconnected")

async def test_stream_account_updates():
    """Test that stream_account_updates doesn't block event loop."""
    print("\n" + "=" * 80)
    print("TEST 2: stream_account_updates event loop fix")
    print("=" * 80)
    
    client = TWSClient()
    
    try:
        # Connect
        print("Connecting to TWS...")
        await client.connect()
        print(f"Connected: {client.is_connected()}")
        
        # Get account
        account_summary = await client.get_account_summary()
        if not account_summary:
            print("No accounts found, skipping test")
            return
        
        account = account_summary[0].get("account", "")
        print(f"Using account: {account}")
        
        # Test account updates streaming
        print(f"\nStreaming account updates (10 seconds)...")
        start = time.monotonic()
        update_count = 0
        
        async for update in client.stream_account_updates(account):
            elapsed = time.monotonic() - start
            if elapsed >= 10:
                print(f"Duration limit reached: {elapsed:.1f}s")
                break
            
            if update:  # Non-empty update
                update_count += 1
                update_type = update.get("type", "unknown")
                print(f"  [{elapsed:.1f}s] Update {update_count}: type={update_type}")
            
            # Check if we're over time
            if elapsed > 12:
                print("WARNING: Exceeded 12 seconds, breaking")
                break
        
        elapsed = time.monotonic() - start
        print(f"\nCompleted in {elapsed:.1f} seconds")
        print(f"Total updates: {update_count}")
        
        if elapsed <= 12:
            print("✅ PASS: Completed within time limit, no event loop error")
        else:
            print("❌ FAIL: Took too long")
        
    except RuntimeError as e:
        if "event loop is already running" in str(e):
            print(f"❌ FAIL: Event loop error: {e}")
        else:
            print(f"❌ FAIL: {e}")
    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if client.is_connected():
            await client.disconnect()
            print("Disconnected")

async def test_session_stability():
    """Test that session remains stable after streaming."""
    print("\n" + "=" * 80)
    print("TEST 3: Session stability after streaming")
    print("=" * 80)
    
    client = TWSClient()
    
    try:
        # Connect
        print("Connecting to TWS...")
        await client.connect()
        print(f"Connected: {client.is_connected()}")
        
        # 1. Stream market data
        req = ContractRequest(symbol="AAPL", secType="STK", exchange="SMART", currency="USD")
        print("\n1. Streaming market data for 5 seconds...")
        start = time.monotonic()
        async for update in client.stream_market_data(req):
            if (time.monotonic() - start) >= 5:
                break
        print(f"   Completed in {time.monotonic() - start:.1f}s")
        
        # 2. Test regular tool immediately after
        print("\n2. Testing regular tool (get_positions)...")
        positions = await client.get_positions()
        print(f"   Got {len(positions)} positions")
        
        # 3. Stream again
        print("\n3. Streaming market data again for 5 seconds...")
        start = time.monotonic()
        async for update in client.stream_market_data(req):
            if (time.monotonic() - start) >= 5:
                break
        print(f"   Completed in {time.monotonic() - start:.1f}s")
        
        # 4. Test regular tool again
        print("\n4. Testing regular tool again (get_account_summary)...")
        account_summary = await client.get_account_summary()
        print(f"   Got {len(account_summary)} accounts")
        
        print("\n✅ PASS: Session remained stable through multiple streaming calls")
        
    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if client.is_connected():
            await client.disconnect()
            print("Disconnected")

async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("STREAMING TOOLS EVENT LOOP FIX - TEST SUITE")
    print("=" * 80)
    print("\nThis test suite verifies:")
    print("1. Market data streaming completes within time limit")
    print("2. Account updates streaming doesn't block event loop")
    print("3. Session remains stable after streaming operations")
    print("\n" + "=" * 80 + "\n")
    
    # Run tests sequentially
    await test_stream_market_data()
    await asyncio.sleep(2)  # Brief pause between tests
    
    await test_stream_account_updates()
    await asyncio.sleep(2)
    
    await test_session_stability()
    
    print("\n" + "=" * 80)
    print("TEST SUITE COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
