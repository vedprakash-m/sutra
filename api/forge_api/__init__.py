"""
Forge API endpoints for project management and workflow operations.
Handles all CRUD operations for Forge projects, artifacts, and stage management.
"""

import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

import azure.functions as func
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from shared.async_database import FORGE_ANALYTICS_CONTAINER, FORGE_TEMPLATES_CONTAINER, AsyncCosmosHelper
from shared.auth_helpers import extract_user_info
from shared.cost_tracker import CostTracker
from shared.llm_client import LLMManager
from shared.middleware import enhanced_security_middleware
from shared.models.forge_models import (
    ArtifactType,
    ForgeAnalytics,
    ForgeArtifact,
    ForgeProject,
    ForgeStage,
    ForgeTemplate,
    ProjectPriority,
    ProjectStatus,
    calculate_stage_completion_percentage,
    generate_forge_id,
    validate_stage_transition,
)
from shared.quality_engine import QualityAssessmentEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration is centralized in shared.async_database

# Initialize services
quality_engine = QualityAssessmentEngine()


def _serialize_for_json(obj):
    """Recursively convert enums, datetimes, and Decimals for JSON serialization."""
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_for_json(v) for v in obj]
    return obj


@enhanced_security_middleware
async def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main entry point for Forge API endpoints."""
    try:
        # Extract method and action from route
        method = req.method
        route_params = req.route_params
        action = route_params.get("action", "")

        logger.info(f"Forge API - Method: {method}, Action: {action}")

        # Route to appropriate handler
        if method == "POST" and action == "create":
            return await create_forge_project(req)
        elif method == "GET" and action == "list":
            return await list_forge_projects(req)
        elif method == "GET" and action == "get":
            return await get_forge_project(req)
        elif method == "PUT" and action == "update":
            return await update_forge_project(req)
        elif method == "DELETE" and action == "delete":
            return await delete_forge_project(req)
        elif method == "POST" and action == "advance-stage":
            return await advance_project_stage(req)
        elif method == "POST" and action == "add-artifact":
            return await add_project_artifact(req)
        elif method == "GET" and action == "artifacts":
            return await get_project_artifacts(req)
        elif method == "POST" and action == "ai-enhance":
            return await ai_enhance_project(req)
        elif method == "GET" and action == "analytics":
            return await get_project_analytics(req)
        elif method == "GET" and action == "templates":
            return await list_forge_templates(req)
        elif method == "POST" and action == "create-template":
            return await create_forge_template(req)
        # Idea Refinement Stage endpoints
        elif action.startswith("idea-refinement"):
            from .idea_refinement_endpoints import main as idea_refinement_main

            return await idea_refinement_main(req)
        # PRD Generation Stage endpoints
        elif action.startswith("prd-generation"):
            from .prd_generation_endpoints import main as prd_generation_main

            return await prd_generation_main(req)
        # UX Requirements Stage endpoints
        elif action.startswith("ux-requirements"):
            from .ux_requirements_endpoints import main as ux_requirements_main

            return await ux_requirements_main(req)
        # Technical Analysis Stage endpoints
        elif action.startswith("technical-analysis"):
            from .technical_analysis_endpoints import main as technical_analysis_main

            return await technical_analysis_main(req)
        # Implementation Playbook Stage endpoints
        elif action.startswith("implementation-playbook") or action in [
            "generate-coding-prompts",
            "create-development-workflow",
            "generate-testing-strategy",
            "create-deployment-guide",
            "compile-playbook",
            "validate-context-integration",
            "optimize-for-agents",
            "export-playbook",
            "quality-validation",
        ]:
            from .implementation_playbook_endpoints import main as implementation_playbook_main

            return await implementation_playbook_main(req)
        else:
            return func.HttpResponse(
                json.dumps({"error": "Invalid endpoint or method"}), status_code=404, mimetype="application/json"
            )

    except Exception as e:
        logger.error(f"Forge API error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error", "details": str(e)}), status_code=500, mimetype="application/json"
        )


async def create_forge_project(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new Forge project."""
    try:
        # Extract user information
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        # Parse request body
        body = json.loads(req.get_body().decode("utf-8"))

        # Create new project
        project = ForgeProject(
            id=generate_forge_id(),
            name=body.get("name", ""),
            description=body.get("description", ""),
            owner_id=user_info["user_id"],
            organization_id=user_info.get("organization_id"),
            priority=ProjectPriority(body.get("priority", "medium")),
            tags=body.get("tags", []),
            custom_fields=body.get("custom_fields", {}),
        )

        # Apply template if specified
        template_id = body.get("template_id")
        if template_id:
            await apply_project_template(project, template_id)

        # Save to database
        await save_forge_project(project)

        # Track analytics
        await track_forge_event(
            user_id=user_info["user_id"],
            project_id=project.id,
            event_type="project_created",
            event_data={"name": project.name, "template_id": template_id},
        )

        logger.info(f"Created Forge project: {project.name} ({project.id})")

        return func.HttpResponse(
            json.dumps(
                {"success": True, "project": project.to_dict(), "message": f"Project '{project.name}' created successfully"}
            ),
            status_code=201,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error creating Forge project: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to create project", "details": str(e)}), status_code=500, mimetype="application/json"
        )


async def list_forge_projects(req: func.HttpRequest) -> func.HttpResponse:
    """List Forge projects for the authenticated user."""
    try:
        # Extract user information
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        # Parse query parameters
        params = dict(req.params)
        status_filter = params.get("status")
        stage_filter = params.get("stage")
        limit = int(params.get("limit", 50))
        offset = int(params.get("offset", 0))

        # Get projects from database
        projects = await get_user_forge_projects(
            user_id=user_info["user_id"],
            organization_id=user_info.get("organization_id"),
            status_filter=status_filter,
            stage_filter=stage_filter,
            limit=limit,
            offset=offset,
        )

        # Calculate progress for each project
        project_summaries = []
        for project in projects:
            summary = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "current_stage": project.current_stage.value,
                "status": project.status.value,
                "priority": project.priority.value,
                "progress_percentage": project.calculate_overall_progress(),
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
                "tags": project.tags,
                "collaborators_count": len(project.collaborators),
                "artifacts_count": sum(len(artifacts) for artifacts in project.artifacts.values()),
            }
            project_summaries.append(summary)

        return func.HttpResponse(
            json.dumps(
                {"projects": project_summaries, "total_count": len(project_summaries), "limit": limit, "offset": offset}
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error listing Forge projects: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to list projects", "details": str(e)}), status_code=500, mimetype="application/json"
        )


async def get_forge_project(req: func.HttpRequest) -> func.HttpResponse:
    """Get a specific Forge project with all details."""
    try:
        # Extract user information
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        # Get project ID from query parameters
        project_id = req.params.get("project_id")
        if not project_id:
            return func.HttpResponse(
                json.dumps({"error": "Project ID required"}), status_code=400, mimetype="application/json"
            )

        # Load project from database
        project = await load_forge_project(project_id)
        if not project:
            return func.HttpResponse(json.dumps({"error": "Project not found"}), status_code=404, mimetype="application/json")

        # Check access permissions
        if not await user_has_project_access(user_info["user_id"], project):
            return func.HttpResponse(json.dumps({"error": "Access denied"}), status_code=403, mimetype="application/json")

        # Calculate stage completion percentages
        stage_progress = {}
        for stage in ForgeStage:
            stage_progress[stage.value] = calculate_stage_completion_percentage(project, stage)

        # Prepare response with full project details
        response_data = project.to_dict()
        response_data["stage_progress"] = stage_progress
        response_data["overall_progress"] = project.calculate_overall_progress()

        return func.HttpResponse(json.dumps(response_data), status_code=200, mimetype="application/json")

    except Exception as e:
        logger.error(f"Error getting Forge project: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to get project", "details": str(e)}), status_code=500, mimetype="application/json"
        )


async def update_forge_project(req: func.HttpRequest) -> func.HttpResponse:
    """Update a Forge project."""
    try:
        # Extract user information
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        # Parse request body
        body = json.loads(req.get_body().decode("utf-8"))
        project_id = body.get("project_id") or req.params.get("project_id") or req.route_params.get("project_id")

        if not project_id:
            return func.HttpResponse(
                json.dumps({"error": "Project ID required"}), status_code=400, mimetype="application/json"
            )

        # Load existing project
        project = await load_forge_project(project_id)
        if not project:
            return func.HttpResponse(json.dumps({"error": "Project not found"}), status_code=404, mimetype="application/json")

        # Check permissions
        if not await user_has_project_access(user_info["user_id"], project, required_permission="edit"):
            return func.HttpResponse(json.dumps({"error": "Edit access denied"}), status_code=403, mimetype="application/json")

        # Update project fields
        updates = body.get("updates", {})
        if not updates:
            updates = {key: value for key, value in body.items() if key not in ["project_id", "updates"]}

        # Update basic fields
        if "name" in updates:
            project.name = updates["name"]
        if "description" in updates:
            project.description = updates["description"]
        if "priority" in updates:
            project.priority = ProjectPriority(updates["priority"])
        if "status" in updates:
            project.status = ProjectStatus(updates["status"])
        if "tags" in updates:
            project.tags = updates["tags"]
        if "custom_fields" in updates:
            project.custom_fields.update(updates["custom_fields"])

        # Update stage-specific data
        if "stage_data" in updates:
            stage_data = updates["stage_data"]
            current_stage = project.current_stage

            if current_stage == ForgeStage.IDEA_REFINEMENT and "idea_refinement_data" in stage_data:
                for key, value in stage_data["idea_refinement_data"].items():
                    setattr(project.idea_refinement_data, key, value)
            elif current_stage == ForgeStage.PRD_GENERATION and "prd_generation_data" in stage_data:
                for key, value in stage_data["prd_generation_data"].items():
                    setattr(project.prd_generation_data, key, value)
            elif current_stage == ForgeStage.UX_REQUIREMENTS and "ux_requirements_data" in stage_data:
                for key, value in stage_data["ux_requirements_data"].items():
                    setattr(project.ux_requirements_data, key, value)
            elif current_stage == ForgeStage.TECHNICAL_ANALYSIS and "technical_analysis_data" in stage_data:
                for key, value in stage_data["technical_analysis_data"].items():
                    setattr(project.technical_analysis_data, key, value)
            elif current_stage == ForgeStage.IMPLEMENTATION_PLAYBOOK and "implementation_playbook_data" in stage_data:
                for key, value in stage_data["implementation_playbook_data"].items():
                    setattr(project.implementation_playbook_data, key, value)

        # Update timestamp and version
        project.updated_at = datetime.now(timezone.utc)
        project.version += 1

        # Save updated project
        await save_forge_project(project)

        # Track analytics
        await track_forge_event(
            user_id=user_info["user_id"],
            project_id=project.id,
            event_type="project_updated",
            event_data={"updates": list(updates.keys())},
        )

        logger.info(f"Updated Forge project: {project.name} ({project.id})")

        return func.HttpResponse(
            json.dumps({"success": True, "project": project.to_dict(), "message": "Project updated successfully"}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error updating Forge project: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to update project", "details": str(e)}), status_code=500, mimetype="application/json"
        )


async def advance_project_stage(req: func.HttpRequest) -> func.HttpResponse:
    """Advance a project to the next stage."""
    try:
        request_id = req.headers.get("x-request-id") or req.headers.get("x-correlation-id") or generate_forge_id()

        # Extract user information
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        # Parse request body
        body = json.loads(req.get_body().decode("utf-8"))
        project_id = body.get("project_id") or req.params.get("project_id") or req.route_params.get("project_id")
        requested_next_stage = (
            body.get("next_stage_id")
            or body.get("nextStageId")
            or req.params.get("next_stage_id")
            or req.params.get("nextStageId")
        )

        if not project_id:
            return func.HttpResponse(
                json.dumps({"error": "Project ID required"}), status_code=400, mimetype="application/json"
            )

        # Load project
        project = await load_forge_project(project_id)
        if not project:
            return func.HttpResponse(json.dumps({"error": "Project not found"}), status_code=404, mimetype="application/json")

        # Check permissions
        if not await user_has_project_access(user_info["user_id"], project, required_permission="edit"):
            return func.HttpResponse(json.dumps({"error": "Edit access denied"}), status_code=403, mimetype="application/json")

        # Attempt to advance stage
        current_stage = project.current_stage
        force_advance = body.get("forceAdvance", False)

        # Quality gate check — verify current stage meets quality threshold
        stage_name = current_stage.value
        stage_data = project.get_current_stage_data() if hasattr(project, "get_current_stage_data") else {}
        if stage_data is None:
            stage_data = {}

        # Get previous stage context for quality assessment
        stages_order = list(ForgeStage)
        current_idx = stages_order.index(current_stage)
        previous_context = {}
        if current_idx > 0:
            prev_stage = stages_order[current_idx - 1]
            forge_data = getattr(project, "forge_data", {}) or {}
            if isinstance(forge_data, dict):
                previous_context = forge_data.get(prev_stage.value, {})

        quality_result = quality_engine.calculate_quality_score(stage=stage_name, content=stage_data, context=previous_context)
        thresholds = quality_engine.get_dynamic_threshold(stage_name, previous_context)

        quality_passes = quality_result.quality_gate_status in ["PROCEED_WITH_CAUTION", "PROCEED_EXCELLENT"]
        if not quality_passes and not force_advance:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "Quality threshold not met for current stage",
                        "currentStage": stage_name,
                        "currentScore": quality_result.overall_score,
                        "requiredScore": thresholds.minimum,
                        "qualityGateStatus": quality_result.quality_gate_status,
                        "improvementSuggestions": quality_result.improvement_suggestions,
                        "canForceAdvance": user_info.get("role") in ["expert", "admin"],
                    }
                ),
                status_code=400,
                mimetype="application/json",
            )

        # Validate requested transition if explicitly provided
        if requested_next_stage:
            stages_order = list(ForgeStage)
            current_index = stages_order.index(current_stage)
            if current_index < len(stages_order) - 1:
                expected_next_stage = stages_order[current_index + 1].value
                if requested_next_stage != expected_next_stage:
                    return func.HttpResponse(
                        json.dumps(
                            {
                                "error": "Invalid next stage requested",
                                "currentStage": current_stage.value,
                                "requestedNextStage": requested_next_stage,
                                "expectedNextStage": expected_next_stage,
                            }
                        ),
                        status_code=400,
                        mimetype="application/json",
                    )

        success = project.advance_stage()

        if not success:
            return func.HttpResponse(
                json.dumps({"error": "Cannot advance stage - already at final stage"}),
                status_code=400,
                mimetype="application/json",
            )

        # Save updated project
        await save_forge_project(project)

        # Track analytics
        await track_forge_event(
            user_id=user_info["user_id"],
            project_id=project.id,
            event_type="stage_advance",
            event_data={
                "from_stage": current_stage.value,
                "to_stage": project.current_stage.value,
                "requested_next_stage": requested_next_stage,
                "request_id": request_id,
            },
        )

        logger.info(f"Advanced project {project.name} from {current_stage.value} to {project.current_stage.value}")

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "project": project.to_dict(),
                    "message": f"Project advanced to {project.current_stage.value} stage",
                    "previous_stage": current_stage.value,
                    "current_stage": project.current_stage.value,
                    "request_id": request_id,
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error advancing project stage: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to advance stage", "details": str(e)}), status_code=500, mimetype="application/json"
        )


async def add_project_artifact(req: func.HttpRequest) -> func.HttpResponse:
    """Add an artifact to a project stage."""
    try:
        # Extract user information
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        # Parse request body
        body = json.loads(req.get_body().decode("utf-8"))
        project_id = body.get("project_id")
        stage = body.get("stage")

        if not project_id or not stage:
            return func.HttpResponse(
                json.dumps({"error": "Project ID and stage required"}), status_code=400, mimetype="application/json"
            )

        # Load project
        project = await load_forge_project(project_id)
        if not project:
            return func.HttpResponse(json.dumps({"error": "Project not found"}), status_code=404, mimetype="application/json")

        # Check permissions
        if not await user_has_project_access(user_info["user_id"], project, required_permission="edit"):
            return func.HttpResponse(json.dumps({"error": "Edit access denied"}), status_code=403, mimetype="application/json")

        # Create artifact
        artifact = ForgeArtifact(
            id=generate_forge_id(),
            name=body.get("name", ""),
            type=ArtifactType(body.get("type", "document")),
            content=body.get("content", ""),
            description=body.get("description", ""),
            file_path=body.get("file_path"),
            file_size=body.get("file_size"),
            mime_type=body.get("mime_type"),
            tags=body.get("tags", []),
            metadata=body.get("metadata", {}),
            created_by=user_info["user_id"],
        )

        # Add artifact to project
        forge_stage = ForgeStage(stage)
        project.add_artifact(forge_stage, artifact)

        # Save updated project
        await save_forge_project(project)

        # Track analytics
        await track_forge_event(
            user_id=user_info["user_id"],
            project_id=project.id,
            event_type="artifact_created",
            event_data={"artifact_id": artifact.id, "artifact_type": artifact.type.value, "stage": stage},
        )

        logger.info(f"Added artifact {artifact.name} to project {project.name} ({stage} stage)")

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "artifact": _serialize_for_json(asdict(artifact)),
                    "message": f"Artifact '{artifact.name}' added to {stage} stage",
                }
            ),
            status_code=201,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error adding project artifact: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to add artifact", "details": str(e)}), status_code=500, mimetype="application/json"
        )


async def ai_enhance_project(req: func.HttpRequest) -> func.HttpResponse:
    """Use AI to enhance project content and provide suggestions."""
    try:
        # Extract user information
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        # Parse request body
        body = json.loads(req.get_body().decode("utf-8"))
        project_id = body.get("project_id")
        enhancement_type = body.get(
            "enhancement_type"
        )  # "idea_improvement", "validation_criteria", "planning_suggestions", etc.
        context = body.get("context", "")

        if not project_id or not enhancement_type:
            return func.HttpResponse(
                json.dumps({"error": "Project ID and enhancement type required"}), status_code=400, mimetype="application/json"
            )

        # Load project
        project = await load_forge_project(project_id)
        if not project:
            return func.HttpResponse(json.dumps({"error": "Project not found"}), status_code=404, mimetype="application/json")

        # Check permissions
        if not await user_has_project_access(user_info["user_id"], project, required_permission="edit"):
            return func.HttpResponse(json.dumps({"error": "Edit access denied"}), status_code=403, mimetype="application/json")

        # Generate AI enhancement
        llm_client = LLMManager()
        enhancement_result = await generate_ai_enhancement(
            llm_client=llm_client,
            project=project,
            enhancement_type=enhancement_type,
            context=context,
            user_id=user_info["user_id"],
        )

        # Track AI interaction
        project.ai_interactions_count += 1
        await save_forge_project(project)

        # Track analytics
        await track_forge_event(
            user_id=user_info["user_id"],
            project_id=project.id,
            event_type="ai_interaction",
            event_data={"enhancement_type": enhancement_type, "stage": project.current_stage.value},
        )

        logger.info(f"Generated AI enhancement for project {project.name}: {enhancement_type}")

        return func.HttpResponse(
            json.dumps(
                {"success": True, "enhancement": enhancement_result, "message": "AI enhancement generated successfully"}
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error generating AI enhancement: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to generate enhancement", "details": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


# Database helper functions


async def save_forge_project(project: ForgeProject) -> None:
    """Save a Forge project to the database."""
    try:
        async with AsyncCosmosHelper() as db:
            await db.upsert_item(project.to_dict())
    except Exception as e:
        logger.error(f"Error saving Forge project: {str(e)}")
        raise


async def load_forge_project(project_id: str) -> Optional[ForgeProject]:
    """Load a Forge project from the database."""
    try:
        async with AsyncCosmosHelper() as db:
            item = await db.read_item(project_id, partition_key=project_id)
            return ForgeProject.from_dict(item)
    except CosmosResourceNotFoundError:
        return None
    except Exception as e:
        logger.error(f"Error loading Forge project: {str(e)}")
        raise


async def get_user_forge_projects(
    user_id: str,
    organization_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    stage_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[ForgeProject]:
    """Get Forge projects for a user with filtering."""
    try:
        # Build query
        query = "SELECT * FROM c WHERE (c.owner_id = @user_id OR ARRAY_CONTAINS(c.collaborators, @user_id))"
        parameters = [{"name": "@user_id", "value": user_id}]

        if organization_id:
            query += " AND c.organization_id = @org_id"
            parameters.append({"name": "@org_id", "value": organization_id})

        if status_filter:
            query += " AND c.status = @status"
            parameters.append({"name": "@status", "value": status_filter})

        if stage_filter:
            query += " AND c.current_stage = @stage"
            parameters.append({"name": "@stage", "value": stage_filter})

        query += f" ORDER BY c.updated_at DESC OFFSET {offset} LIMIT {limit}"

        async with AsyncCosmosHelper() as db:
            items = await db.query_items(query=query, parameters=parameters)
            return [ForgeProject.from_dict(item) for item in items]

    except Exception as e:
        logger.error(f"Error getting user Forge projects: {str(e)}")
        raise


async def user_has_project_access(user_id: str, project: ForgeProject, required_permission: str = "read") -> bool:
    """Check if user has access to a project."""
    # Owner has full access
    if project.owner_id == user_id:
        return True

    # Check collaborators
    if user_id in project.collaborators:
        # Check specific permissions if required
        user_permissions = project.permissions.get(user_id, [])
        if required_permission in user_permissions or "admin" in user_permissions:
            return True

    # Check shared access
    if user_id in project.shared_with:
        return required_permission == "read"  # Shared users get read-only access

    return False


async def track_forge_event(user_id: str, project_id: str, event_type: str, event_data: Dict[str, Any]) -> None:
    """Track analytics event for Forge usage."""
    try:
        analytics = ForgeAnalytics(
            id=generate_forge_id(), user_id=user_id, project_id=project_id, event_type=event_type, event_data=event_data
        )

        async with AsyncCosmosHelper() as db:
            await db.create_item(asdict(analytics), container_name=FORGE_ANALYTICS_CONTAINER)

    except Exception as e:
        logger.error(f"Error tracking Forge event: {str(e)}")
        # Don't raise - analytics failures shouldn't break main functionality


async def generate_ai_enhancement(
    llm_client: LLMManager, project: ForgeProject, enhancement_type: str, context: str, user_id: str
) -> Dict[str, Any]:
    """Generate AI-powered enhancement for project content."""

    # Stage-specific enhancement prompts
    enhancement_prompts = {
        "idea_improvement": """
        Based on this project idea, provide specific suggestions to improve and enhance it:

        Project: {project_name}
        Description: {project_description}
        Current Stage: {current_stage}
        Context: {context}

        Provide 3-5 concrete improvement suggestions focusing on:
        1. Clarity and specificity
        2. Market potential
        3. Technical feasibility
        4. Unique value proposition
        5. Implementation approach
        """,
        "validation_criteria": """
        Generate comprehensive validation criteria for this project:

        Project: {project_name}
        Description: {project_description}
        Target Audience: {target_audience}
        Context: {context}

        Create 5-7 validation criteria with:
        1. Clear success metrics
        2. Methods to validate each criterion
        3. Evidence required
        4. Priority/weight for each criterion
        """,
        "planning_suggestions": """
        Provide detailed planning suggestions for this project:

        Project: {project_name}
        Description: {project_description}
        Validation Results: {validation_status}
        Context: {context}

        Suggest:
        1. Key milestones and timeline
        2. Resource requirements
        3. Technology stack recommendations
        4. Risk mitigation strategies
        5. Success metrics and KPIs
        """,
    }

    # Get appropriate prompt
    prompt_template = enhancement_prompts.get(enhancement_type, enhancement_prompts["idea_improvement"])

    # Format prompt with project data
    prompt = prompt_template.format(
        project_name=project.name,
        project_description=project.description,
        current_stage=project.current_stage.value,
        target_audience=getattr(project.idea_refinement_data, "target_audience", "Not specified"),
        validation_status=getattr(project.prd_generation_data, "validation_status", "Not started"),
        context=context,
    )

    # Generate enhancement using LLM
    try:
        response = await llm_client.execute_prompt_with_cost_tracking(
            prompt=prompt,
            user_id=user_id,
            provider="openai",  # Default to OpenAI for consistency
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000,
        )

        return {
            "enhancement_type": enhancement_type,
            "suggestions": response["content"],
            "cost": str(response.get("cost", "0")),
            "model_used": response.get("model", "gpt-4"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error generating AI enhancement: {str(e)}")
        return {"enhancement_type": enhancement_type, "error": "Failed to generate AI enhancement", "details": str(e)}


# Additional helper endpoints
async def get_project_analytics(req: func.HttpRequest) -> func.HttpResponse:
    """Get analytics for a project."""
    try:
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        project_id = req.route_params.get("project_id") or req.params.get("project_id")
        if not project_id:
            return func.HttpResponse(
                json.dumps({"error": "Project ID required"}), status_code=400, mimetype="application/json"
            )

        project = await load_forge_project(project_id)
        if not project:
            return func.HttpResponse(json.dumps({"error": "Project not found"}), status_code=404, mimetype="application/json")

        if not await user_has_project_access(user_info["user_id"], project, required_permission="view"):
            return func.HttpResponse(json.dumps({"error": "Access denied"}), status_code=403, mimetype="application/json")

        # Query analytics from Cosmos DB
        try:
            query = "SELECT * FROM c WHERE c.project_id = @project_id ORDER BY c.timestamp DESC"
            async with AsyncCosmosHelper() as db:
                events = await db.query_items(
                    query=query,
                    parameters=[{"name": "@project_id", "value": project_id}],
                    container_name=FORGE_ANALYTICS_CONTAINER,
                )
        except Exception:
            events = []

        return func.HttpResponse(
            json.dumps(
                {
                    "projectId": project_id,
                    "projectName": project.name,
                    "currentStage": project.current_stage.value,
                    "stageCompletionPercentage": calculate_stage_completion_percentage(project),
                    "events": events[-50:],  # Last 50 events
                    "totalEvents": len(events),
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error getting project analytics: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to get analytics", "details": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


async def get_project_artifacts(req: func.HttpRequest) -> func.HttpResponse:
    """Get artifacts for a project stage."""
    try:
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        project_id = req.route_params.get("project_id") or req.params.get("project_id")
        stage = req.params.get("stage")
        if not project_id:
            return func.HttpResponse(
                json.dumps({"error": "Project ID required"}), status_code=400, mimetype="application/json"
            )

        project = await load_forge_project(project_id)
        if not project:
            return func.HttpResponse(json.dumps({"error": "Project not found"}), status_code=404, mimetype="application/json")

        if not await user_has_project_access(user_info["user_id"], project, required_permission="view"):
            return func.HttpResponse(json.dumps({"error": "Access denied"}), status_code=403, mimetype="application/json")

        # Get artifacts, optionally filtered by stage
        artifacts = project.artifacts if hasattr(project, "artifacts") else []
        if stage:
            artifacts = [a for a in artifacts if getattr(a, "stage", None) == stage]

        artifact_list = [asdict(a) if hasattr(a, "__dataclass_fields__") else a for a in artifacts]

        return func.HttpResponse(
            json.dumps(
                {
                    "projectId": project_id,
                    "stage": stage,
                    "artifacts": artifact_list,
                    "totalCount": len(artifact_list),
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error getting project artifacts: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to get artifacts", "details": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


async def list_forge_templates(req: func.HttpRequest) -> func.HttpResponse:
    """List available Forge templates."""
    try:
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        try:
            query = "SELECT * FROM c ORDER BY c.created_at DESC"
            async with AsyncCosmosHelper() as db:
                templates = await db.query_items(
                    query=query,
                    container_name=FORGE_TEMPLATES_CONTAINER,
                )
        except Exception:
            templates = []

        return func.HttpResponse(
            json.dumps(
                {
                    "templates": templates,
                    "totalCount": len(templates),
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to list templates", "details": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


async def create_forge_template(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new Forge template from a project."""
    try:
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        body = json.loads(req.get_body().decode("utf-8"))
        template_name = body.get("name")
        template_description = body.get("description", "")
        source_project_id = body.get("sourceProjectId")

        if not template_name:
            return func.HttpResponse(
                json.dumps({"error": "Template name required"}), status_code=400, mimetype="application/json"
            )

        template_data = {
            "id": generate_forge_id(),
            "name": template_name,
            "description": template_description,
            "created_by": user_info["user_id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_project_id": source_project_id,
            "template_data": body.get("templateData", {}),
        }

        # If a source project is specified, extract its structure
        if source_project_id:
            project = await load_forge_project(source_project_id)
            if project:
                template_data["template_data"] = {
                    "stage_structure": {s.value: {} for s in ForgeStage},
                    "project_type": getattr(project, "project_type", "general"),
                }

        async with AsyncCosmosHelper() as db:
            await db.create_item(template_data, container_name=FORGE_TEMPLATES_CONTAINER)

        return func.HttpResponse(
            json.dumps({"success": True, "template": template_data}),
            status_code=201,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to create template", "details": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


async def apply_project_template(project: ForgeProject, template_id: str) -> None:
    """Apply a template to a project."""
    try:
        async with AsyncCosmosHelper() as db:
            template = await db.read_item(template_id, partition_key=template_id, container_name=FORGE_TEMPLATES_CONTAINER)

            template_data = template.get("template_data", {})
            if template_data:
                logger.info(f"Applied template {template_id} to project {project.name}")
    except Exception as e:
        logger.error(f"Error applying template: {str(e)}")


async def delete_forge_project(req: func.HttpRequest) -> func.HttpResponse:
    """Delete a Forge project."""
    try:
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        body = json.loads(req.get_body().decode("utf-8"))
        project_id = body.get("project_id")
        if not project_id:
            return func.HttpResponse(
                json.dumps({"error": "Project ID required"}), status_code=400, mimetype="application/json"
            )

        project = await load_forge_project(project_id)
        if not project:
            return func.HttpResponse(json.dumps({"error": "Project not found"}), status_code=404, mimetype="application/json")

        if not await user_has_project_access(user_info["user_id"], project, required_permission="delete"):
            return func.HttpResponse(
                json.dumps({"error": "Delete access denied"}), status_code=403, mimetype="application/json"
            )

        # Delete from Cosmos DB
        async with AsyncCosmosHelper() as db:
            await db.delete_item(project_id, partition_key=user_info["user_id"])

        # Track deletion event
        await track_forge_event(
            user_id=user_info["user_id"],
            project_id=project_id,
            event_type="project_deleted",
            event_data={"project_name": project.name},
        )

        logger.info(f"Deleted project {project.name} (ID: {project_id})")

        return func.HttpResponse(
            json.dumps({"success": True, "message": f"Project '{project.name}' deleted"}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to delete project", "details": str(e)}),
            status_code=500,
            mimetype="application/json",
        )
