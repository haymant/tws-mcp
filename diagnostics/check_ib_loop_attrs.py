#!/usr/bin/env python3
"""Check what attributes ib_async.IB has for the event loop"""
import asyncio
from ib_async import IB

async def main():
    ib = IB()
    print(f"IB instance type: {type(ib)}")
    print(f"\nAll attributes of IB instance:")
    for attr in dir(ib):
        if not attr.startswith('_'):
            val = getattr(ib, attr, None)
            if not callable(val):
                print(f"  {attr}: {type(val).__name__}")
    
    print(f"\nPrivate attributes that might be loop-related:")
    for attr in dir(ib):
        if 'loop' in attr.lower() or 'event' in attr.lower():
            val = getattr(ib, attr, None)
            print(f"  {attr}: {val} (type: {type(val).__name__})")

if __name__ == "__main__":
    asyncio.run(main())
