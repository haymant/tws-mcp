#!/usr/bin/env python3
"""Check FastMCP available methods"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Test")

print("Available methods on FastMCP instance:")
for attr in dir(mcp):
    if not attr.startswith('_'):
        print(f"  - {attr}")

print("\nMethods containing 'app' or 'http':")
for attr in dir(mcp):
    if 'app' in attr.lower() or 'http' in attr.lower():
        print(f"  - {attr}: {type(getattr(mcp, attr))}")
