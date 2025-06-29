"""
Debug test for auth system
"""

import pytest
from conftest import create_auth_request
from shared.unified_auth import get_auth_provider


@pytest.mark.asyncio
async def test_auth_debug(auth_test_user):
    """Debug test to verify auth system works."""
    # Check if the auth provider has the user
    auth_provider = get_auth_provider()
    print(f"Auth provider: {auth_provider}")
    print(f"Testing provider: {auth_provider.provider}")
    print(f"Current user: {auth_provider.provider._current_user}")

    # Create a request and try to get user
    req = create_auth_request(method="GET", url="http://localhost/test")
    user = await auth_provider.get_user_from_request(req)

    print(f"Retrieved user: {user}")
    assert user is not None
    assert user.id == "test-user-123"
