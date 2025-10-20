#!/usr/bin/env python3
"""
Minimal test to verify TWS API is working.
This is the simplest possible connection test.
"""
import asyncio
from ib_async import IB

async def test():
    ib = IB()
    try:
        print("=" * 60)
        print("Minimal TWS API Connection Test")
        print("=" * 60)
        print("\n⏳ Attempting connection to 127.0.0.1:7496...")
        print("   Using Client ID: 999")
        print("   Timeout: 20 seconds\n")
        
        await ib.connectAsync('127.0.0.1', 7496, clientId=999, timeout=20)
        
        print("✅ SUCCESS! API connection established.")
        print(f"\n📊 Connected accounts: {ib.managedAccounts()}")
        print(f"📊 Connection state: {ib.isConnected()}")
        
        print("\n🔌 Disconnecting...")
        ib.disconnect()
        print("✅ Disconnected cleanly.\n")
        print("=" * 60)
        print("✅ TWS API IS WORKING CORRECTLY")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}")
        print(f"   Error: {e}\n")
        print("=" * 60)
        print("❌ TWS API IS NOT RESPONDING")
        print("=" * 60)
        print("\n📖 See docs/TWS_API_HANDSHAKE_TIMEOUT.md for troubleshooting")
        raise

if __name__ == "__main__":
    asyncio.run(test())
