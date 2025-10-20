#!/usr/bin/env python3
"""
Script to inspect the IB() instance structure to understand event loop handling.
"""

import asyncio
from ib_async import IB

async def inspect_ib_instance():
    """Inspect the IB instance to see what attributes it has."""
    
    print("=" * 70)
    print("Inspecting IB() instance attributes")
    print("=" * 70)
    
    ib = IB()
    
    print("\n1. Direct attributes on IB instance:")
    print("-" * 70)
    interesting_attrs = ['loop', '_loop', 'client', 'wrapper', 'conn']
    for attr in interesting_attrs:
        has_it = hasattr(ib, attr)
        print(f"  ib.{attr:<20} : {has_it}")
        if has_it:
            val = getattr(ib, attr)
            print(f"    └─ Type: {type(val).__name__}")
            print(f"    └─ Value: {val}")
    
    print("\n2. All attributes containing 'loop' or 'event':")
    print("-" * 70)
    all_attrs = dir(ib)
    loop_attrs = [a for a in all_attrs if 'loop' in a.lower() or 'event' in a.lower()]
    for attr in loop_attrs:
        try:
            val = getattr(ib, attr)
            if not callable(val):
                print(f"  ib.{attr:<20} : {type(val).__name__} = {val}")
        except Exception as e:
            print(f"  ib.{attr:<20} : Error accessing - {e}")
    
    # Check if client exists
    if hasattr(ib, 'client'):
        print("\n3. Attributes on ib.client:")
        print("-" * 70)
        client = ib.client
        print(f"  Type: {type(client).__name__}")
        for attr in interesting_attrs:
            has_it = hasattr(client, attr)
            print(f"  client.{attr:<16} : {has_it}")
            if has_it:
                val = getattr(client, attr)
                print(f"    └─ Type: {type(val).__name__}")
                print(f"    └─ Value: {val}")
    
    # Check wrapper
    if hasattr(ib, 'wrapper'):
        print("\n4. Attributes on ib.wrapper:")
        print("-" * 70)
        wrapper = ib.wrapper
        print(f"  Type: {type(wrapper).__name__}")
        for attr in interesting_attrs:
            has_it = hasattr(wrapper, attr)
            print(f"  wrapper.{attr:<16} : {has_it}")
            if has_it:
                val = getattr(wrapper, attr)
                print(f"    └─ Type: {type(val).__name__}")
                print(f"    └─ Value: {val}")
    
    print("\n5. Current event loop:")
    print("-" * 70)
    try:
        loop = asyncio.get_running_loop()
        print(f"  Current loop: {loop}")
        print(f"  Loop ID: {id(loop)}")
    except RuntimeError as e:
        print(f"  No running loop: {e}")
    
    print("\n" + "=" * 70)
    print("Inspection complete")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(inspect_ib_instance())
