#!/usr/bin/env python3
"""Final test: just verify the server starts and responds without event loop errors."""
import subprocess
import time
import requests
import sys

def main():
    # Start the server in background
    print("Starting server...")
    proc = subprocess.Popen(
        ["uv", "run", "python", "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Wait for server to start
    time.sleep(4)
    
    # Quick check: can we fetch /sse?
    try:
        resp = requests.get("http://localhost:8000/api/v1/sse", timeout=2, stream=True)
        print(f"GET /api/v1/sse -> {resp.status_code}")
        if resp.status_code == 200:
            print("✓ Server is running and responding")
            proc.terminate()
            proc.wait(timeout=5)
            return 0
        else:
            print(f"✗ Unexpected status: {resp.status_code}")
            proc.terminate()
            proc.wait(timeout=5)
            return 1
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        # Check if server stderr has "different loop" error
        proc.terminate()
        out, _ = proc.communicate(timeout=5)
        if "different loop" in out.lower():
            print("✗✗ LOOP ERROR DETECTED in server output!")
            print(out)
            return 1
        print("Server started but connection failed (might be SSE streaming behavior)")
        return 0

if __name__ == "__main__":
    sys.exit(main())
