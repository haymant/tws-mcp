#!/usr/bin/env python3
"""
Diagnostic script to test TWS connection directly with ib_async.
This helps debug connection issues outside of the MCP context.
"""

import asyncio
import sys
from ib_async import IB

async def test_tws_connection(host="127.0.0.1", port=7497, client_id=1):
    """Test direct connection to TWS/IB Gateway."""

    print("=" * 70)
    print("TWS Connection Diagnostic Tool")
    print("=" * 70)
    print(f"\nConnection Parameters:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Client ID: {client_id}")
    print(f"\nAttempting to connect...\n")
    
    ib = IB()
    
    # Enable verbose logging for ib_async
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        # Try to connect with a longer timeout
        print("⏳ Connecting (timeout: 20 seconds)...")
        print("   (Verbose logging enabled - you'll see detailed connection info below)\n")
        await asyncio.wait_for(
            ib.connectAsync(host, port, clientId=client_id, timeout=5),
            timeout=5.0
        )
        
        print("✅ CONNECTION SUCCESSFUL!")
        print(f"\n📊 Connection Details:")
        print(f"  Connected: {ib.isConnected()}")
        print(f"  Client ID: {ib.client.clientId}")
        
        # Try to get some basic info
        try:
            accounts = ib.managedAccounts()
            print(f"  Accounts: {accounts}")
        except Exception as e:
            print(f"  Accounts: Error - {e}")
        
        # Disconnect
        print("\n🔌 Disconnecting...")
        ib.disconnect()
        print("✅ Disconnected successfully")
        
        return True
        
    except asyncio.TimeoutError as e:
        print("❌ CONNECTION TIMEOUT")
        print(f"\nTimeout after 20 seconds - connection handshake did not complete.")
        print(f"\nThis means TWS is listening BUT not completing the IB API handshake.")
        print("\n🔍 Possible Causes:")
        print("  1. TWS API is disabled in settings")
        print("  2. Client ID conflict (another client using the same ID)")
        print("  3. TWS needs to be restarted")
        print("  4. TWS version compatibility issue")
        print("\n💡 Quick Fixes to Try:")
        print("  • Restart TWS completely")
        print("  • Try client ID 0 (master client)")
        print("  • Check TWS API Configuration:")
        print("    Edit → Global Configuration → API → Settings")
        print("    ✓ Enable 'Enable ActiveX and Socket Clients'")
        print("    ✓ Add '127.0.0.1' to Trusted IPs if using 'localhost only' mode")
        return False
        
    except asyncio.CancelledError:
        print("❌ CONNECTION CANCELLED")
        print("\nThe connection was cancelled - this shouldn't happen in direct testing.")
        return False
        
    except ConnectionRefusedError:
        print("❌ CONNECTION REFUSED")
        print(f"\n🔍 TWS/IB Gateway is not listening on {host}:{port}")
        print("\nTroubleshooting:")
        print("  1. Make sure TWS/IB Gateway is running")
        print("  2. Verify the correct port:")
        print("     - TWS Live: 7497")
        print("     - TWS Paper: 7497")
        print("     - IB Gateway Live: 4001")
        print("     - IB Gateway Paper: 4002")
        return False
        
    except Exception as e:
        print(f"❌ CONNECTION FAILED: {type(e).__name__}")
        print(f"\nError Details: {str(e)}")
        print(f"\n🔍 Error Type: {type(e).__module__}.{type(e).__name__}")
        
        # Print full traceback for debugging
        import traceback
        print("\n📋 Full Traceback:")
        traceback.print_exc()
        return False
        
    finally:
        # Ensure cleanup
        try:
            if ib.isConnected():
                ib.disconnect()
        except Exception:
            pass

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test TWS/IB Gateway connection")
    parser.add_argument("--host", default="127.0.0.1", help="TWS host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=7497, help="TWS port (default: 7497)")
    parser.add_argument("--client-id", type=int, default=1, help="Client ID (default: 1)")
    
    args = parser.parse_args()
    
    try:
        success = asyncio.run(test_tws_connection(args.host, args.port, args.client_id))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)

if __name__ == "__main__":
    main()
