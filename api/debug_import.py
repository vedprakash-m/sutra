#!/usr/bin/env python3

import sys
import traceback

print("Starting import test...")

try:
    print("1. Importing json...")
    import json

    print("   ✓ json imported")

    print("2. Importing logging...")
    import logging

    print("   ✓ logging imported")

    print("3. Importing os...")
    import os

    print("   ✓ os imported")

    print("4. Importing datetime...")
    from datetime import datetime, timezone

    print("   ✓ datetime imported")

    print("5. Importing functools...")
    from functools import wraps

    print("   ✓ functools imported")

    print("6. Importing typing...")
    from typing import Any, Dict, List, Optional

    print("   ✓ typing imported")

    print("7. Importing azure.functions...")
    import azure.functions as func

    print("   ✓ azure.functions imported")

    print("8. Importing jwt...")
    import jwt

    print("   ✓ jwt imported")

    print("9. Importing requests...")
    import requests

    print("   ✓ requests imported")

    print("10. Importing azure.identity...")
    from azure.identity import DefaultAzureCredential

    print("   ✓ azure.identity imported")

    print("11. Importing azure.keyvault.secrets...")
    from azure.keyvault.secrets import SecretClient

    print("   ✓ azure.keyvault.secrets imported")

    print("12. Importing cachetools...")
    from cachetools import TTLCache

    print("   ✓ cachetools imported")

    print("13. Importing shared.models...")
    from shared.models import User, UserRole

    print("   ✓ shared.models imported")

    print("14. Importing shared.database...")
    from shared.database import DatabaseManager

    print("   ✓ shared.database imported")

    print("15. Now trying full entra_auth import...")
    import shared.entra_auth

    print("   ✓ shared.entra_auth imported")
    print(f"   Available attributes: {[attr for attr in dir(shared.entra_auth) if not attr.startswith('_')]}")

    print("16. Trying to access validate_request_headers...")
    if hasattr(shared.entra_auth, "validate_request_headers"):
        print("   ✓ validate_request_headers found")
    else:
        print("   ✗ validate_request_headers NOT found")

except Exception as e:
    print(f"ERROR at step: {e}")
    traceback.print_exc()
