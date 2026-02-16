import types

from shared import auth_helpers


class MockRequest:
    def __init__(self):
        self.headers = {}


def test_extract_user_info_returns_none_without_token(monkeypatch):
    req = MockRequest()

    monkeypatch.setattr(auth_helpers, "extract_token_from_request", lambda _req: None)

    result = auth_helpers.extract_user_info(req)

    assert result is None


def test_extract_user_info_returns_canonical_keys(monkeypatch):
    req = MockRequest()

    class MockUser:
        id = "user-123"
        email = "user@example.com"
        name = "Test User"
        role = types.SimpleNamespace(value="admin")
        given_name = "Test"
        family_name = "User"
        organization_id = "org-789"

    class MockAuthManager:
        @staticmethod
        def get_user_from_token(_token):
            return MockUser()

    monkeypatch.setattr(auth_helpers, "extract_token_from_request", lambda _req: "token")
    monkeypatch.setattr(auth_helpers, "get_auth_manager", lambda: MockAuthManager())

    result = auth_helpers.extract_user_info(req)

    assert result is not None
    assert result["id"] == "user-123"
    assert result["user_id"] == "user-123"
    assert result["email"] == "user@example.com"
    assert result["role"] == "admin"
    assert result["organization_id"] == "org-789"
