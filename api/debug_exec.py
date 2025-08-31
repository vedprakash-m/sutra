#!/usr/bin/env python3

# Let's try to execute the entra_auth.py file step by step to find the issue

print("Step 1: Reading entra_auth.py file...")

try:
    with open("shared/entra_auth.py", "r") as f:
        content = f.read()

    print("Step 2: Compiling the code...")
    compiled_code = compile(content, "shared/entra_auth.py", "exec")
    print("   ✓ Code compiles successfully")

    print("Step 3: Creating a namespace to execute...")
    namespace = {}

    print("Step 4: Executing the code...")
    exec(compiled_code, namespace)
    print("   ✓ Code executed successfully")

    print("Step 5: Checking available symbols...")
    symbols = [name for name in namespace.keys() if not name.startswith("__")]
    print(f"   Available symbols: {symbols}")

    if "validate_request_headers" in namespace:
        print("   ✓ validate_request_headers found!")
    else:
        print("   ✗ validate_request_headers NOT found")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback

    traceback.print_exc()
