# Test Compatibility Patches for Azure Static Web Apps Authentication Migration

These patches allow existing tests to continue working while we transition from JWT-based authentication to Azure Static Web Apps decorator-based authentication.

## Problem

The new authentication system uses decorators (@require_auth, @require_admin) that execute before test mocks can be applied, causing tests to fail with 401 errors.

## Solution

Mock the decorators themselves to bypass authentication during testing.

## Usage in Test Files

```python
from unittest.mock import patch, Mock

class TestAPI:
    @pytest.fixture
    def mock_auth_success(self):
        """Mock successful authentication for decorator-based auth."""
        with patch("api.your_module.require_auth") as mock_decorator:
            # Make the decorator return the original function unchanged
            mock_decorator.side_effect = lambda **kwargs: lambda func: func

            # Mock the request.current_user that the function expects
            def mock_request_with_user(*args, **kwargs):
                req = args[0] if args else Mock()
                req.current_user = Mock()
                req.current_user.id = "test-user-123"
                return args, kwargs

            yield mock_decorator

    @pytest.mark.asyncio
    async def test_endpoint(self, mock_auth_success):
        # Your test code here
        pass
```

## Migration Status

- ✅ admin_api: Migrated to @require_admin
- ✅ integrations_api: Migrated to @require_auth
- ✅ llm_execute_api: Migrated to @require_auth
- ✅ playbooks_api: Migrated to @require_auth
- ✅ collections_api: Already using @require_auth

All modules include legacy compatibility imports for gradual test migration.
