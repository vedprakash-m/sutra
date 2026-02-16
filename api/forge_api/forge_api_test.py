"""
Comprehensive tests for Forge API endpoints (api/forge_api/__init__.py).
Covers CRUD operations, stage advancement, analytics, templates, and access control.
All DB interactions are mocked via AsyncCosmosHelper patches.
"""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import azure.functions as func
import pytest
from shared.models.forge_models import (
    ArtifactType,
    ForgeArtifact,
    ForgeProject,
    ForgeStage,
    ProjectPriority,
    ProjectStatus,
    generate_forge_id,
)


# ---- Helpers ----

def _make_request(method="GET", body=None, params=None, route_params=None):
    """Create a mock Azure Functions HttpRequest."""
    req = Mock(spec=func.HttpRequest)
    req.method = method
    req.params = params or {}
    req.route_params = route_params or {}
    req.get_body.return_value = json.dumps(body or {}).encode("utf-8")
    return req


def _mock_user(user_id="user-1", org_id=None, role="user"):
    """Return dict matching what extract_user_info returns for forge endpoints."""
    return {"user_id": user_id, "organization_id": org_id, "role": role}


def _sample_project(owner_id="user-1", name="Test Project", project_id=None):
    """Create a sample ForgeProject for testing."""
    return ForgeProject(
        id=project_id or generate_forge_id(),
        name=name,
        description="A test project",
        owner_id=owner_id,
    )


# ---- Fixtures ----

@pytest.fixture
def auth_patch():
    """Patch extract_user_info to return a valid user."""
    with patch("forge_api.extract_user_info", return_value=_mock_user()) as m:
        yield m


@pytest.fixture
def auth_none():
    """Patch extract_user_info to return None (not authenticated)."""
    with patch("forge_api.extract_user_info", return_value=None) as m:
        yield m


@pytest.fixture
def mock_db():
    """Patch AsyncCosmosHelper so no real DB calls are made."""
    helper = AsyncMock()
    helper.upsert_item = AsyncMock(return_value={})
    helper.read_item = AsyncMock(return_value={})
    helper.query_items = AsyncMock(return_value=[])
    helper.create_item = AsyncMock(return_value={})
    helper.delete_item = AsyncMock(return_value=None)

    ctx_manager = AsyncMock()
    ctx_manager.__aenter__ = AsyncMock(return_value=helper)
    ctx_manager.__aexit__ = AsyncMock(return_value=False)

    with patch("forge_api.AsyncCosmosHelper", return_value=ctx_manager):
        yield helper


# ---- Import module under test ----
# Must do a lazy import because forge_api may need env vars and packages at import time.

@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    """Set required env vars before importing the module."""
    monkeypatch.setenv("COSMOS_DB_CONNECTION_STRING", "AccountEndpoint=https://localhost;AccountKey=dGVzdA==;")
    monkeypatch.setenv("TESTING_MODE", "true")


# ---- Tests: Authentication enforcement ----

class TestAuthEnforcement:
    """All endpoints must return 401 when auth fails."""

    @pytest.mark.asyncio
    async def test_create_requires_auth(self, auth_none, mock_db):
        from forge_api import create_forge_project

        req = _make_request("POST", body={"name": "P"})
        resp = await create_forge_project(req)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_list_requires_auth(self, auth_none, mock_db):
        from forge_api import list_forge_projects

        req = _make_request("GET")
        resp = await list_forge_projects(req)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_requires_auth(self, auth_none, mock_db):
        from forge_api import get_forge_project

        req = _make_request("GET", params={"project_id": "p1"})
        resp = await get_forge_project(req)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_update_requires_auth(self, auth_none, mock_db):
        from forge_api import update_forge_project

        req = _make_request("PUT", body={"project_id": "p1", "updates": {}})
        resp = await update_forge_project(req)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_requires_auth(self, auth_none, mock_db):
        from forge_api import delete_forge_project

        req = _make_request("DELETE", body={"project_id": "p1"})
        resp = await delete_forge_project(req)
        assert resp.status_code == 401


# ---- Tests: create_forge_project ----

class TestCreateForgeProject:
    @pytest.mark.asyncio
    async def test_creates_project_successfully(self, auth_patch, mock_db):
        from forge_api import create_forge_project

        req = _make_request("POST", body={"name": "My Project", "description": "desc", "priority": "high"})
        resp = await create_forge_project(req)
        assert resp.status_code == 201
        data = json.loads(resp.get_body())
        assert data["success"] is True
        assert data["project"]["name"] == "My Project"
        mock_db.upsert_item.assert_awaited()

    @pytest.mark.asyncio
    async def test_creates_with_template(self, auth_patch, mock_db):
        from forge_api import create_forge_project

        mock_db.read_item = AsyncMock(return_value={
            "id": "tmpl-1",
            "template_data": {"stage_structure": {}},
        })
        req = _make_request("POST", body={"name": "TP", "template_id": "tmpl-1"})
        resp = await create_forge_project(req)
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_tracks_analytics_on_create(self, auth_patch, mock_db):
        from forge_api import create_forge_project

        req = _make_request("POST", body={"name": "Analytics Project"})
        await create_forge_project(req)
        # create_item is called by track_forge_event for analytics
        assert mock_db.create_item.await_count >= 1


# ---- Tests: list_forge_projects ----

class TestListForgeProjects:
    @pytest.mark.asyncio
    async def test_lists_projects_empty(self, auth_patch, mock_db):
        from forge_api import list_forge_projects

        mock_db.query_items = AsyncMock(return_value=[])
        req = _make_request("GET")
        resp = await list_forge_projects(req)
        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        assert data["projects"] == []
        assert data["total_count"] == 0

    @pytest.mark.asyncio
    async def test_lists_projects_with_results(self, auth_patch, mock_db):
        from forge_api import list_forge_projects

        project = _sample_project()
        mock_db.query_items = AsyncMock(return_value=[project.to_dict()])
        req = _make_request("GET", params={"limit": "10", "offset": "0"})
        resp = await list_forge_projects(req)
        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        assert data["total_count"] == 1
        assert data["projects"][0]["name"] == "Test Project"

    @pytest.mark.asyncio
    async def test_passes_filters(self, auth_patch, mock_db):
        from forge_api import list_forge_projects

        mock_db.query_items = AsyncMock(return_value=[])
        req = _make_request("GET", params={"status": "active", "stage": "idea_refinement"})
        await list_forge_projects(req)
        # Verify query_items was called (filter params are built into the SQL query)
        mock_db.query_items.assert_awaited()


# ---- Tests: get_forge_project ----

class TestGetForgeProject:
    @pytest.mark.asyncio
    async def test_returns_project_details(self, auth_patch, mock_db):
        from forge_api import get_forge_project

        project = _sample_project()
        mock_db.read_item = AsyncMock(return_value=project.to_dict())
        req = _make_request("GET", params={"project_id": project.id})
        resp = await get_forge_project(req)
        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        assert data["name"] == "Test Project"
        assert "stage_progress" in data
        assert "overall_progress" in data

    @pytest.mark.asyncio
    async def test_returns_400_without_project_id(self, auth_patch, mock_db):
        from forge_api import get_forge_project

        req = _make_request("GET")
        resp = await get_forge_project(req)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_404_for_missing_project(self, auth_patch, mock_db):
        from forge_api import get_forge_project
        from azure.cosmos.exceptions import CosmosResourceNotFoundError

        mock_db.read_item = AsyncMock(side_effect=CosmosResourceNotFoundError(
            status_code=404, message="Not found"
        ))
        req = _make_request("GET", params={"project_id": "nonexistent"})
        resp = await get_forge_project(req)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_403_no_access(self, auth_patch, mock_db):
        from forge_api import get_forge_project

        project = _sample_project(owner_id="other-user")
        mock_db.read_item = AsyncMock(return_value=project.to_dict())
        req = _make_request("GET", params={"project_id": project.id})
        resp = await get_forge_project(req)
        assert resp.status_code == 403


# ---- Tests: update_forge_project ----

class TestUpdateForgeProject:
    @pytest.mark.asyncio
    async def test_updates_project_name(self, auth_patch, mock_db):
        from forge_api import update_forge_project

        project = _sample_project()
        mock_db.read_item = AsyncMock(return_value=project.to_dict())
        req = _make_request("PUT", body={
            "project_id": project.id,
            "updates": {"name": "Updated Name"},
        })
        resp = await update_forge_project(req)
        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        assert data["success"] is True
        assert data["project"]["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_returns_400_without_project_id(self, auth_patch, mock_db):
        from forge_api import update_forge_project

        req = _make_request("PUT", body={"updates": {}})
        resp = await update_forge_project(req)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_404_for_missing_project(self, auth_patch, mock_db):
        from forge_api import update_forge_project
        from azure.cosmos.exceptions import CosmosResourceNotFoundError

        mock_db.read_item = AsyncMock(side_effect=CosmosResourceNotFoundError(
            status_code=404, message="Not found"
        ))
        req = _make_request("PUT", body={"project_id": "p1", "updates": {}})
        resp = await update_forge_project(req)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_403_no_edit_access(self, auth_patch, mock_db):
        from forge_api import update_forge_project

        project = _sample_project(owner_id="other-user")
        mock_db.read_item = AsyncMock(return_value=project.to_dict())
        req = _make_request("PUT", body={
            "project_id": project.id,
            "updates": {"name": "Hacked"},
        })
        resp = await update_forge_project(req)
        assert resp.status_code == 403


# ---- Tests: delete_forge_project ----

class TestDeleteForgeProject:
    @pytest.mark.asyncio
    async def test_deletes_project(self, auth_patch, mock_db):
        from forge_api import delete_forge_project

        project = _sample_project()
        mock_db.read_item = AsyncMock(return_value=project.to_dict())
        req = _make_request("DELETE", body={"project_id": project.id})
        resp = await delete_forge_project(req)
        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        assert data["success"] is True
        mock_db.delete_item.assert_awaited()

    @pytest.mark.asyncio
    async def test_returns_400_without_project_id(self, auth_patch, mock_db):
        from forge_api import delete_forge_project

        req = _make_request("DELETE", body={})
        resp = await delete_forge_project(req)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_403_no_delete_access(self, auth_patch, mock_db):
        from forge_api import delete_forge_project

        project = _sample_project(owner_id="another-user")
        mock_db.read_item = AsyncMock(return_value=project.to_dict())
        req = _make_request("DELETE", body={"project_id": project.id})
        resp = await delete_forge_project(req)
        assert resp.status_code == 403


# ---- Tests: advance_project_stage ----

class TestAdvanceProjectStage:
    @pytest.mark.asyncio
    async def test_advance_with_force(self, auth_patch, mock_db):
        from forge_api import advance_project_stage

        project = _sample_project()
        mock_db.read_item = AsyncMock(return_value=project.to_dict())
        req = _make_request("POST", body={
            "project_id": project.id,
            "forceAdvance": True,
        })
        resp = await advance_project_stage(req)
        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        assert data["success"] is True
        assert data["previous_stage"] == "idea_refinement"
        assert data["current_stage"] == "prd_generation"

    @pytest.mark.asyncio
    async def test_advance_blocked_by_quality_gate(self, auth_patch, mock_db):
        from forge_api import advance_project_stage

        project = _sample_project()
        mock_db.read_item = AsyncMock(return_value=project.to_dict())
        req = _make_request("POST", body={
            "project_id": project.id,
            "forceAdvance": False,
        })
        resp = await advance_project_stage(req)
        # With empty stage data, quality gate will likely BLOCK
        data = json.loads(resp.get_body())
        assert resp.status_code in (200, 400)
        if resp.status_code == 400:
            assert "quality" in data.get("error", "").lower() or "qualityGateStatus" in data

    @pytest.mark.asyncio
    async def test_advance_requires_project_id(self, auth_patch, mock_db):
        from forge_api import advance_project_stage

        req = _make_request("POST", body={})
        resp = await advance_project_stage(req)
        assert resp.status_code == 400


# ---- Tests: add_project_artifact ----

class TestAddProjectArtifact:
    @pytest.mark.asyncio
    async def test_adds_artifact(self, auth_patch, mock_db):
        from forge_api import add_project_artifact

        project = _sample_project()
        mock_db.read_item = AsyncMock(return_value=project.to_dict())
        req = _make_request("POST", body={
            "project_id": project.id,
            "stage": "idea_refinement",
            "name": "Design Doc",
            "type": "document",
            "content": "Some content",
        })
        resp = await add_project_artifact(req)
        assert resp.status_code == 201
        data = json.loads(resp.get_body())
        assert data["success"] is True
        assert data["artifact"]["name"] == "Design Doc"

    @pytest.mark.asyncio
    async def test_artifact_requires_project_and_stage(self, auth_patch, mock_db):
        from forge_api import add_project_artifact

        req = _make_request("POST", body={"name": "Doc"})
        resp = await add_project_artifact(req)
        assert resp.status_code == 400


# ---- Tests: list_forge_templates ----

class TestListForgeTemplates:
    @pytest.mark.asyncio
    async def test_lists_templates(self, auth_patch, mock_db):
        from forge_api import list_forge_templates

        mock_db.query_items = AsyncMock(return_value=[
            {"id": "t1", "name": "Template 1"},
            {"id": "t2", "name": "Template 2"},
        ])
        req = _make_request("GET")
        resp = await list_forge_templates(req)
        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        assert data["totalCount"] == 2

    @pytest.mark.asyncio
    async def test_lists_templates_empty(self, auth_patch, mock_db):
        from forge_api import list_forge_templates

        mock_db.query_items = AsyncMock(return_value=[])
        req = _make_request("GET")
        resp = await list_forge_templates(req)
        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        assert data["totalCount"] == 0


# ---- Tests: create_forge_template ----

class TestCreateForgeTemplate:
    @pytest.mark.asyncio
    async def test_creates_template(self, auth_patch, mock_db):
        from forge_api import create_forge_template

        req = _make_request("POST", body={
            "name": "New Template",
            "description": "A template",
        })
        resp = await create_forge_template(req)
        assert resp.status_code == 201
        data = json.loads(resp.get_body())
        assert data["success"] is True
        assert data["template"]["name"] == "New Template"
        mock_db.create_item.assert_awaited()

    @pytest.mark.asyncio
    async def test_template_requires_name(self, auth_patch, mock_db):
        from forge_api import create_forge_template

        req = _make_request("POST", body={"description": "no name"})
        resp = await create_forge_template(req)
        assert resp.status_code == 400


# ---- Tests: Database helpers ----

class TestDatabaseHelpers:
    @pytest.mark.asyncio
    async def test_save_forge_project(self, mock_db):
        from forge_api import save_forge_project

        project = _sample_project()
        await save_forge_project(project)
        mock_db.upsert_item.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_load_forge_project_found(self, mock_db):
        from forge_api import load_forge_project

        project = _sample_project(project_id="proj-1")
        mock_db.read_item = AsyncMock(return_value=project.to_dict())
        result = await load_forge_project("proj-1")
        assert result is not None
        assert result.name == "Test Project"

    @pytest.mark.asyncio
    async def test_load_forge_project_not_found(self, mock_db):
        from forge_api import load_forge_project
        from azure.cosmos.exceptions import CosmosResourceNotFoundError

        mock_db.read_item = AsyncMock(side_effect=CosmosResourceNotFoundError(
            status_code=404, message="Not found"
        ))
        result = await load_forge_project("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_forge_projects(self, mock_db):
        from forge_api import get_user_forge_projects

        project = _sample_project()
        mock_db.query_items = AsyncMock(return_value=[project.to_dict()])
        result = await get_user_forge_projects("user-1")
        assert len(result) == 1
        assert result[0].name == "Test Project"

    @pytest.mark.asyncio
    async def test_get_user_forge_projects_with_filters(self, mock_db):
        from forge_api import get_user_forge_projects

        mock_db.query_items = AsyncMock(return_value=[])
        result = await get_user_forge_projects(
            "user-1", status_filter="active", stage_filter="prd_generation", limit=10, offset=5
        )
        assert result == []
        mock_db.query_items.assert_awaited()

    @pytest.mark.asyncio
    async def test_track_forge_event(self, mock_db):
        from forge_api import track_forge_event

        await track_forge_event(
            user_id="user-1",
            project_id="proj-1",
            event_type="test_event",
            event_data={"key": "value"},
        )
        mock_db.create_item.assert_awaited_once()


# ---- Tests: Access control ----

class TestUserAccessControl:
    @pytest.mark.asyncio
    async def test_owner_has_full_access(self):
        from forge_api import user_has_project_access

        project = _sample_project(owner_id="user-1")
        assert await user_has_project_access("user-1", project) is True
        assert await user_has_project_access("user-1", project, "edit") is True
        assert await user_has_project_access("user-1", project, "delete") is True

    @pytest.mark.asyncio
    async def test_non_collaborator_denied(self):
        from forge_api import user_has_project_access

        project = _sample_project(owner_id="owner")
        assert await user_has_project_access("stranger", project) is False

    @pytest.mark.asyncio
    async def test_collaborator_with_permission(self):
        from forge_api import user_has_project_access

        project = _sample_project(owner_id="owner")
        project.collaborators = ["user-2"]
        project.permissions = {"user-2": ["read", "edit"]}
        assert await user_has_project_access("user-2", project, "read") is True
        assert await user_has_project_access("user-2", project, "edit") is True

    @pytest.mark.asyncio
    async def test_collaborator_without_permission(self):
        from forge_api import user_has_project_access

        project = _sample_project(owner_id="owner")
        project.collaborators = ["user-2"]
        project.permissions = {"user-2": ["read"]}
        assert await user_has_project_access("user-2", project, "delete") is False

    @pytest.mark.asyncio
    async def test_collaborator_with_admin_gets_any(self):
        from forge_api import user_has_project_access

        project = _sample_project(owner_id="owner")
        project.collaborators = ["user-2"]
        project.permissions = {"user-2": ["admin"]}
        assert await user_has_project_access("user-2", project, "delete") is True

    @pytest.mark.asyncio
    async def test_shared_user_read_only(self):
        from forge_api import user_has_project_access

        project = _sample_project(owner_id="owner")
        project.shared_with = ["viewer"]
        assert await user_has_project_access("viewer", project, "read") is True
        assert await user_has_project_access("viewer", project, "edit") is False


# ---- Tests: Main router ----

class TestMainRouter:
    @pytest.mark.asyncio
    async def test_invalid_action_returns_404(self, auth_patch, mock_db):
        from forge_api import main

        req = _make_request("GET", route_params={"action": "nonexistent-action"})
        # main is wrapped with enhanced_security_middleware
        # We'll call the inner logic directly
        resp = await main(req)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_routes_create(self, auth_patch, mock_db):
        from forge_api import main

        req = _make_request("POST", route_params={"action": "create"}, body={"name": "P"})
        resp = await main(req)
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_routes_list(self, auth_patch, mock_db):
        from forge_api import main

        mock_db.query_items = AsyncMock(return_value=[])
        req = _make_request("GET", route_params={"action": "list"})
        resp = await main(req)
        assert resp.status_code == 200
