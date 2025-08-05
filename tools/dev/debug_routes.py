#!/usr/bin/env python3
"""
Debug script to check what routes are registered.
"""
import sys
sys.path.insert(0, '/app')

from app.api.bots import router

print("Registered routes in bots router:")
for route in router.routes:
    print(f"- {route.methods} {route.path}")