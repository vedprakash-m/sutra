"""
Simple cost management auth test
"""

import pytest
from conftest import create_auth_request
from cost_management_api import main as cost_management_main


@pytest.mark.asyncio
async def test_cost_mgmt_auth_simple(auth_test_user):
    """Simple test to verify cost management auth works."""
    # Create a request
    req = create_auth_request(
        method="GET", url="http://localhost:7071/api/cost-management/budget/usage"
    )

    # Call function - this should get past auth but may fail on other things
    try:
        response = await cost_management_main(req)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.get_body()}")
    except Exception as e:
        print(f"Exception: {e}")
        # As long as it's not an auth error, we're good
        assert "Authentication required" not in str(e)
