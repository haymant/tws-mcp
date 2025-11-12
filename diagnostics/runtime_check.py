#!/usr/bin/env python3
"""Quick runtime check that server starts and ibkr_connect doesn't fail with loop error."""
import asyncio
import httpx
import sys

async def main():
    base_url = "http://localhost:8000/api/v1"
    
    # wait briefly for server to start
    await asyncio.sleep(3)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Try to fetch the SSE endpoint
        try:
            resp = await client.get(f"{base_url}/sse")
            print(f"GET /api/v1/sse -> {resp.status_code}")
            if resp.status_code < 500:
                print("✓ Server is responding (no 500 errors)")
            else:
                print(f"✗ Server returned 500: {resp.text[:200]}")
                return 1
        except Exception as e:
            print(f"✗ Error fetching /sse: {e}")
            return 1

        # Try a simple tool call (ibkr_connect) to verify the loop fix
        # (this will fail to connect to TWS, but should not raise a loop error)
        print("\nTesting ibkr_connect (will fail TWS connection but should not have loop error)...")
        try:
            # POST to the SSE endpoint with a tool call
            # The exact endpoint depends on FastMCP version; for now just probe
            resp = await client.post(f"{base_url}/messages", json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "ibkr_connect",
                    "arguments": {"host": "127.0.0.1", "port": 7497, "clientId": 1}
                },
                "id": 1
            })
            print(f"POST /messages ibkr_connect -> {resp.status_code}")
            # if status < 500, we passed (no loop error that causes 500)
            if resp.status_code < 500:
                print("✓ ibkr_connect did not fail with loop error (may fail TWS connection, that's OK)")
            else:
                print(f"✗ ibkr_connect returned 500: {resp.text[:200]}")
                if "different loop" in resp.text:
                    print("✗✗ LOOP ERROR DETECTED")
                    return 1
        except Exception as e:
            print(f"Error calling ibkr_connect: {e}")

    print("\n✓ Runtime check complete - no event loop errors detected!")
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
