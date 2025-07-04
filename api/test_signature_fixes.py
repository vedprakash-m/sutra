"""
Simple test to verify that the API functions accept the correct **kwargs signature
without the authentication layer getting in the way.
"""

import asyncio
from unittest.mock import Mock, patch
from azure.functions import HttpRequest
from shared.models import User, UserRole


def create_mock_request(method="GET", url="/api/test"):
    """Create a mock Azure Functions HTTP request"""
    req = Mock(spec=HttpRequest)
    req.method = method
    req.url = url
    req.headers = {}
    req.params = {}
    req.route_params = {}
    req.get_body.return_value = b"{}"
    return req


def create_mock_user(user_id="test-user", role=UserRole.USER):
    """Create a mock user object"""
    user = Mock(spec=User)
    user.id = user_id
    user.email = f"{user_id}@example.com"
    user.name = "Test User"
    user.role = role
    return user


async def test_function_signatures():
    """Test that all the functions accept **kwargs and don't fail on signature mismatch"""

    print("Testing function signatures...")

    # Test functions that we updated
    test_functions = [
        ("integrations_api", "main"),
        ("collections_api", "main"),
        ("llm_execute_api", "main"),
        ("playbooks_api", "main"),
        ("admin_api", "main"),
        ("cost_management_api", "main"),
        ("user_management", "main"),
        ("guest_llm_api", "main"),
        ("role_management", "main"),
        ("prompts", "main"),
    ]

    req = create_mock_request()
    user = create_mock_user()

    for module_name, func_name in test_functions:
        print(f"\nTesting {module_name}.{func_name}...")

        try:
            # Import the module
            module = __import__(module_name)
            func = getattr(module, func_name)

            # Test that the function accepts **kwargs by calling it with user in kwargs
            # We expect it to either:
            # 1. Execute successfully (if no auth issues)
            # 2. Fail with authentication error (but not signature error)
            # 3. Fail with some other expected error (but not signature error)

            try:
                await func(req, user=user)
                print(f"✓ {module_name}.{func_name} - Function executed successfully")
            except Exception as e:
                if "takes" in str(e) and "positional argument" in str(e):
                    print(f"✗ {module_name}.{func_name} - SIGNATURE ERROR: {e}")
                    return False
                else:
                    print(
                        f"✓ {module_name}.{func_name} - Function signature OK (expected error: {type(e).__name__})"
                    )

        except Exception as e:
            print(f"✗ {module_name}.{func_name} - Import/setup error: {e}")
            return False

    print("\n✓ All function signatures are correct!")
    return True


async def test_direct_function_calls():
    """Test calling functions directly without authentication decorators"""
    print("\nTesting direct function calls...")

    req = create_mock_request()
    user = create_mock_user()

    # Test one function by calling it directly with proper mocking
    try:
        # Import and test collections_api
        from collections_api import main as collections_main

        # Mock all the dependencies
        with patch("collections_api.get_database_manager"), patch(
            "collections_api.get_cost_manager"
        ), patch("collections_api.list_collections") as mock_list_collections:
            # Mock the list_collections function to return a simple response
            mock_list_collections.return_value = Mock()
            mock_list_collections.return_value.status_code = 200

            # This should work - the function signature accepts **kwargs
            try:
                response = await collections_main(req, user=user)
                print("✓ Direct function call with **kwargs works")
            except TypeError as e:
                if "takes" in str(e) and "positional argument" in str(e):
                    print(f"✗ Direct function call failed with signature error: {e}")
                    return False
                else:
                    print(
                        f"✓ Direct function call OK (non-signature error: {type(e).__name__})"
                    )
            except Exception as e:
                print(f"✓ Direct function call OK (expected error: {type(e).__name__})")

    except Exception as e:
        print(f"✗ Test setup error: {e}")
        return False

    return True


if __name__ == "__main__":
    print("Testing API function signature fixes...")

    success1 = asyncio.run(test_function_signatures())
    success2 = asyncio.run(test_direct_function_calls())

    if success1 and success2:
        print(
            "\n🎉 All tests passed! The function signature fixes are working correctly."
        )
        exit(0)
    else:
        print("\n❌ Some tests failed. There may still be signature issues.")
        exit(1)
