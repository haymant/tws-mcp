#!/usr/bin/env python3
"""
Test script to verify the P&L tools fix.

This script tests that ibkr_get_pnl and ibkr_get_pnl_single
now properly wait for P&L data instead of returning null values.

Requirements:
- TWS/Gateway must be running on localhost:7497
- Account must have at least one open position
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tws_client import TWSClient


async def test_pnl():
    """Test P&L methods."""
    client = TWSClient()
    
    try:
        print("Connecting to TWS...")
        await client.connect('127.0.0.1', 7497, 1)
        print("✓ Connected")
        
        # Get positions first
        print("\nGetting positions...")
        positions = await client.get_positions()
        print(f"✓ Found {len(positions)} positions")
        
        if not positions:
            print("\n⚠ No positions found - P&L tests require open positions")
            return
        
        # Get account from first position
        account = positions[0]['account']
        print(f"\nUsing account: {account}")
        
        # Test overall P&L
        print("\n--- Testing ibkr_get_pnl ---")
        try:
            pnl = await client.get_pnl(account, '')
            print(f"✓ Received P&L data:")
            print(f"  Account: {pnl.get('account')}")
            print(f"  Daily P&L: {pnl.get('dailyPnL')}")
            print(f"  Unrealized P&L: {pnl.get('unrealizedPnL')}")
            print(f"  Realized P&L: {pnl.get('realizedPnL')}")
            
            # Check if we got real data (not null)
            if pnl.get('dailyPnL') is None and pnl.get('unrealizedPnL') is None:
                print("✗ FAILED: P&L values are still null!")
            else:
                print("✓ SUCCESS: P&L values are populated!")
        except Exception as e:
            print(f"✗ FAILED: {e}")
        
        # Test single position P&L
        print("\n--- Testing ibkr_get_pnl_single ---")
        conId = positions[0]['contract']['conId']
        symbol = positions[0]['contract'].get('symbol', 'Unknown')
        print(f"Testing with position: {symbol} (conId: {conId})")
        
        try:
            pnl_single = await client.get_pnl_single(account, '', conId)
            print(f"✓ Received single P&L data:")
            print(f"  Account: {pnl_single.get('account')}")
            print(f"  Contract ID: {pnl_single.get('conId')}")
            print(f"  Position: {pnl_single.get('position')}")
            print(f"  Daily P&L: {pnl_single.get('dailyPnL')}")
            print(f"  Unrealized P&L: {pnl_single.get('unrealizedPnL')}")
            print(f"  Realized P&L: {pnl_single.get('realizedPnL')}")
            print(f"  Value: {pnl_single.get('value')}")
            
            # Check if we got real data (not null)
            if pnl_single.get('position') == 0 or pnl_single.get('value') is None:
                print("✗ FAILED: P&L values are still null or position is 0!")
            else:
                print("✓ SUCCESS: Single P&L values are populated!")
        except Exception as e:
            print(f"✗ FAILED: {e}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\nDisconnecting...")
        client.disconnect()
        print("✓ Disconnected")


if __name__ == "__main__":
    print("=" * 60)
    print("P&L Tools Fix Test")
    print("=" * 60)
    asyncio.run(test_pnl())
    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)
