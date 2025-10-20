#!/usr/bin/env python3
"""Check IB.client for loop references"""
import asyncio
from ib_async import IB

async def main():
    ib = IB()
    
    print("=== Checking IB.client ===")
    print(f"client type: {type(ib.client)}")
    for attr in dir(ib.client):
        if 'loop' in attr.lower():
            val = getattr(ib.client, attr, None)
            print(f"  {attr}: {val} (type: {type(val).__name__})")
    
    print("\n=== Checking IB.wrapper ===")
    print(f"wrapper type: {type(ib.wrapper)}")
    for attr in dir(ib.wrapper):
        if 'loop' in attr.lower():
            val = getattr(ib.wrapper, attr, None)
            print(f"  {attr}: {val} (type: {type(val).__name__})")
    
    # Check if there's a loop stored anywhere
    print("\n=== Attempting to find stored loop ===")
    current_loop = asyncio.get_running_loop()
    print(f"Current loop: {current_loop}")
    
    # Try common private attributes
    for obj_name, obj in [("IB", ib), ("client", ib.client), ("wrapper", ib.wrapper)]:
        for attr in ['_loop', 'loop', '_eventLoop', 'eventLoop']:
            if hasattr(obj, attr):
                val = getattr(obj, attr)
                print(f"{obj_name}.{attr}: {val}")

if __name__ == "__main__":
    asyncio.run(main())
