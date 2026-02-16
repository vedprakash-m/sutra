"""
PRD Generation API endpoints for the Forge module.
Implements comprehensive Product Requirements Document generation with AI assistance
and progressive quality gates building on idea refinement context.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import azure.functions as func
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from shared.async_database import AsyncCosmosHelper
from shared.auth_helpers import extract_user_info
from shared.cost_tracker import CostTracker
from shared.llm_client import LLMManager
from shared.quality_engine import QualityAssessmentEngine
from shared.quality_validators import CrossStageQualityValidator

logger = logging.getLogger(__name__)

quality_engine = QualityAssessmentEngine()
quality_validator = CrossStageQualityValidator()


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main entry point for PRD Generation API endpoints."""
    try:
        # Extract method and route parameters
        method = req.method
        route_params = req.route_params
        action = route_params.get("sub_action", "") or route_params.get("action", "")
        project_id = route_params.get("project_id", "")

        logger.info(f"PRD Generation API - Method: {method}, Action: {action}, Project: {project_id}")

        # Route to appropriate handler
        if method == "POST" and action == "extract-requirements":
            return await extract_requirements(req, project_id)
        elif method == "POST" and action == "generate-user-stories":
            return await generate_user_stories(req, project_id)
        elif method == "POST" and action == "prioritize-features":
            return await prioritize_features(req, project_id)
        elif method == "GET" and action == "assessment":
            return await get_prd_quality_assessment(req, project_id)
        elif method == "POST" and action == "generate-document":
            return await generate_prd_document(req, project_id)
        elif method == "POST" and action == "complete":
            return await complete_prd_stage(req, project_id)
        else:
            return func.HttpResponse(
                json.dumps({"error": f"Unsupported operation: {method} {action}"}),
                status_code=405,
                headers={"Content-Type": "application/json"},
            )

    except Exception as e:
        logger.error(f"Error in PRD generation endpoint: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def extract_requirements(req: func.HttpRequest, project_id: str) -> func.HttpResponse:
    """Extract intelligent requirements based on idea refinement context"""
    try:
        # Extract user info and request data
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, headers={"Content-Type": "application/json"}
            )

        request_data = json.loads(req.get_body().decode("utf-8"))
        idea_context = request_data.get("ideaContext", {})
        requirement_focus = request_data.get("requirementFocus", [])
        selected_llm = request_data.get("model") or request_data.get("selectedLLM", "gemini-flash")
        provider_name = request_data.get("provider") or LLMManager.resolve_provider_from_model(selected_llm)

        # Validate idea refinement context
        validation_result = quality_validator.validate_stage_readiness(
            "prd_generation", {"forgeData": {"idea_refinement": idea_context}}
        )

        if not validation_result.is_consistent:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "Idea refinement context validation failed",
                        "validation_errors": validation_result.validation_errors,
                        "recommendations": validation_result.recommendations,
                    }
                ),
                status_code=400,
                headers={"Content-Type": "application/json"},
            )

        # Initialize cost tracking
        cost_tracker = CostTracker()

        # Create requirements extraction prompt
        extraction_prompt = _create_requirements_extraction_prompt(idea_context, requirement_focus)

        # Execute LLM call with cost tracking
        llm_client = LLMManager()

        await cost_tracker.track_llm_call_start(
            user_id=user_info.get("user_id"),
            operation="forge_prd_requirements_extraction",
            model=selected_llm,
            project_id=project_id,
        )

        try:
            response = await llm_client.execute_prompt(
                provider_name=provider_name, prompt=extraction_prompt, model=selected_llm, temperature=0.5, max_tokens=3000
            )

            await cost_tracker.track_llm_call_complete(
                operation_id=cost_tracker.current_operation_id,
                response=response,
                tokens_used=response.get("usage", {}).get("total_tokens", 0),
                cost=response.get("cost", 0.0),
            )

        except Exception as llm_error:
            await cost_tracker.track_llm_call_error(operation_id=cost_tracker.current_operation_id, error=str(llm_error))
            raise llm_error

        # Parse LLM response
        extracted_requirements = _parse_requirements_response(response.get("content", ""))

        # Perform quality assessment on extracted requirements
        quality_result = quality_engine.calculate_quality_score(
            stage="prd_generation", content=extracted_requirements, context=idea_context
        )

        # Prepare extraction result
        extraction_result = {
            "projectId": project_id,
            "extractionTimestamp": datetime.now(timezone.utc).isoformat(),
            "extractedRequirements": extracted_requirements,
            "qualityAssessment": {
                "overallScore": quality_result.overall_score,
                "dimensionScores": quality_result.dimension_scores,
                "qualityGateStatus": quality_result.quality_gate_status,
                "confidenceLevel": quality_result.confidence_level,
            },
            "contextValidation": {"consistencyScore": validation_result.consistency_score, "contextIntegration": "successful"},
            "costTracking": {
                "tokensUsed": response.get("usage", {}).get("total_tokens", 0),
                "cost": response.get("cost", 0.0),
                "model": selected_llm,
            },
            "improvementSuggestions": quality_result.improvement_suggestions,
        }

        return func.HttpResponse(json.dumps(extraction_result), status_code=200, headers={"Content-Type": "application/json"})

    except Exception as e:
        logger.error(f"Error extracting requirements: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to extract requirements", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def generate_user_stories(req: func.HttpRequest, project_id: str) -> func.HttpResponse:
    """Generate user stories with acceptance criteria based on requirements and idea context"""
    try:
        # Extract user info and request data
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, headers={"Content-Type": "application/json"}
            )

        request_data = json.loads(req.get_body().decode("utf-8"))
        requirements = request_data.get("requirements", {})
        idea_context = request_data.get("ideaContext", {})
        story_format = request_data.get("storyFormat", "standard")  # standard, gherkin, invest
        selected_llm = request_data.get("model") or request_data.get("selectedLLM", "claude-3-5-sonnet")
        provider_name = request_data.get("provider") or LLMManager.resolve_provider_from_model(selected_llm)

        # Initialize cost tracking
        cost_tracker = CostTracker()

        # Create user story generation prompt
        story_prompt = _create_user_story_prompt(requirements, idea_context, story_format)

        # Execute LLM call with cost tracking
        llm_client = LLMManager()

        await cost_tracker.track_llm_call_start(
            user_id=user_info.get("user_id"), operation="forge_prd_user_stories", model=selected_llm, project_id=project_id
        )

        try:
            response = await llm_client.execute_prompt(
                provider_name=provider_name, prompt=story_prompt, model=selected_llm, temperature=0.4, max_tokens=4000
            )

            await cost_tracker.track_llm_call_complete(
                operation_id=cost_tracker.current_operation_id,
                response=response,
                tokens_used=response.get("usage", {}).get("total_tokens", 0),
                cost=response.get("cost", 0.0),
            )

        except Exception as llm_error:
            await cost_tracker.track_llm_call_error(operation_id=cost_tracker.current_operation_id, error=str(llm_error))
            raise llm_error

        # Parse user stories response
        user_stories = _parse_user_stories_response(response.get("content", ""))

        # Validate user stories quality using INVEST criteria
        invest_scores = _validate_invest_criteria(user_stories)

        # Assess cross-stage consistency
        consistency_check = quality_validator.validate_cross_stage_consistency(
            "idea_refinement",
            "prd_generation",
            {"forgeData": {"idea_refinement": idea_context, "prd_generation": {"userStories": user_stories}}},
        )

        # Prepare user stories result
        stories_result = {
            "projectId": project_id,
            "generationTimestamp": datetime.now(timezone.utc).isoformat(),
            "userStories": user_stories,
            "investValidation": invest_scores,
            "consistencyCheck": {
                "isConsistent": consistency_check.is_consistent,
                "consistencyScore": consistency_check.consistency_score,
                "warnings": consistency_check.validation_warnings,
            },
            "costTracking": {
                "tokensUsed": response.get("usage", {}).get("total_tokens", 0),
                "cost": response.get("cost", 0.0),
                "model": selected_llm,
            },
            "storyMetrics": {
                "totalStories": len(user_stories.get("stories", [])),
                "averageInvestScore": sum(invest_scores.values()) / len(invest_scores) if invest_scores else 0,
                "storiesWithCriteria": len([s for s in user_stories.get("stories", []) if s.get("acceptanceCriteria")]),
            },
        }

        return func.HttpResponse(json.dumps(stories_result), status_code=200, headers={"Content-Type": "application/json"})

    except Exception as e:
        logger.error(f"Error generating user stories: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to generate user stories", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def prioritize_features(req: func.HttpRequest, project_id: str) -> func.HttpResponse:
    """Prioritize features with business impact scoring aligned to value proposition"""
    try:
        # Extract user info and request data
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, headers={"Content-Type": "application/json"}
            )

        request_data = json.loads(req.get_body().decode("utf-8"))
        features = request_data.get("features", [])
        user_stories = request_data.get("userStories", {})
        idea_context = request_data.get("ideaContext", {})
        prioritization_method = request_data.get("prioritizationMethod", "rice")  # rice, moscow, kano
        selected_llm = request_data.get("model") or request_data.get("selectedLLM", "gpt-4")
        provider_name = request_data.get("provider") or LLMManager.resolve_provider_from_model(selected_llm)

        # Initialize cost tracking
        cost_tracker = CostTracker()

        # Create feature prioritization prompt
        prioritization_prompt = _create_feature_prioritization_prompt(
            features, user_stories, idea_context, prioritization_method
        )

        # Execute LLM call with cost tracking
        llm_client = LLMManager()

        await cost_tracker.track_llm_call_start(
            user_id=user_info.get("user_id"),
            operation="forge_prd_feature_prioritization",
            model=selected_llm,
            project_id=project_id,
        )

        try:
            response = await llm_client.execute_prompt(
                provider_name=provider_name, prompt=prioritization_prompt, model=selected_llm, temperature=0.3, max_tokens=3000
            )

            await cost_tracker.track_llm_call_complete(
                operation_id=cost_tracker.current_operation_id,
                response=response,
                tokens_used=response.get("usage", {}).get("total_tokens", 0),
                cost=response.get("cost", 0.0),
            )

        except Exception as llm_error:
            await cost_tracker.track_llm_call_error(operation_id=cost_tracker.current_operation_id, error=str(llm_error))
            raise llm_error

        # Parse prioritization response
        prioritized_features = _parse_prioritization_response(response.get("content", ""), prioritization_method)

        # Calculate business impact alignment
        business_alignment = _calculate_business_alignment(prioritized_features, idea_context.get("valueProposition", ""))

        # Prepare prioritization result
        prioritization_result = {
            "projectId": project_id,
            "prioritizationTimestamp": datetime.now(timezone.utc).isoformat(),
            "prioritizedFeatures": prioritized_features,
            "prioritizationMethod": prioritization_method,
            "businessAlignment": business_alignment,
            "costTracking": {
                "tokensUsed": response.get("usage", {}).get("total_tokens", 0),
                "cost": response.get("cost", 0.0),
                "model": selected_llm,
            },
            "prioritizationMetrics": {
                "totalFeatures": len(prioritized_features.get("features", [])),
                "highPriorityFeatures": len(
                    [
                        f
                        for f in prioritized_features.get("features", [])
                        if f.get("priority", "").lower() in ["high", "must-have", "critical"]
                    ]
                ),
                "averageBusinessValue": sum(f.get("businessValue", 0) for f in prioritized_features.get("features", []))
                / max(len(prioritized_features.get("features", [])), 1),
            },
        }

        return func.HttpResponse(
            json.dumps(prioritization_result), status_code=200, headers={"Content-Type": "application/json"}
        )

    except Exception as e:
        logger.error(f"Error prioritizing features: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to prioritize features", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def get_prd_quality_assessment(req: func.HttpRequest, project_id: str) -> func.HttpResponse:
    """Get current quality assessment for the PRD generation stage"""
    try:
        # Extract user info
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, headers={"Content-Type": "application/json"}
            )

        # Get project from database
        async with AsyncCosmosHelper() as db:
            try:
                project = await db.read_item(project_id, partition_key=user_info["user_id"])
            except CosmosResourceNotFoundError:
                return func.HttpResponse(
                    json.dumps({"error": "Project not found"}), status_code=404, headers={"Content-Type": "application/json"}
                )

        # Extract PRD data
        forge_data = project.get("forgeData", {})
        prd_data = forge_data.get("prd_generation", {})
        idea_context = forge_data.get("idea_refinement", {})

        if not prd_data:
            return func.HttpResponse(
                json.dumps({"error": "No PRD generation data found"}),
                status_code=404,
                headers={"Content-Type": "application/json"},
            )

        # Perform quality assessment
        quality_result = quality_engine.calculate_quality_score(stage="prd_generation", content=prd_data, context=idea_context)

        # Get adaptive thresholds
        thresholds = quality_engine.get_dynamic_threshold("prd_generation", idea_context)

        # Cross-stage validation
        cross_stage_validation = quality_validator.validate_cross_stage_consistency(
            "idea_refinement", "prd_generation", project
        )

        # Prepare assessment result
        assessment_result = {
            "projectId": project_id,
            "assessmentTimestamp": datetime.now(timezone.utc).isoformat(),
            "currentQuality": {
                "overallScore": quality_result.overall_score,
                "dimensionScores": quality_result.dimension_scores,
                "qualityGateStatus": quality_result.quality_gate_status,
                "confidenceLevel": quality_result.confidence_level,
            },
            "thresholds": {
                "minimum": thresholds.minimum,
                "recommended": thresholds.recommended,
                "adjustmentsApplied": thresholds.adjustments_applied,
            },
            "crossStageValidation": {
                "isConsistent": cross_stage_validation.is_consistent,
                "consistencyScore": cross_stage_validation.consistency_score,
                "validationErrors": cross_stage_validation.validation_errors,
                "recommendations": cross_stage_validation.recommendations,
            },
            "improvementOpportunities": quality_result.improvement_suggestions,
            "estimatedImprovementTime": quality_result.estimated_improvement_time,
            "readyForNextStage": quality_result.quality_gate_status in ["PROCEED_WITH_CAUTION", "PROCEED_EXCELLENT"]
            and cross_stage_validation.is_consistent,
        }

        return func.HttpResponse(json.dumps(assessment_result), status_code=200, headers={"Content-Type": "application/json"})

    except Exception as e:
        logger.error(f"Error getting PRD quality assessment: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to get quality assessment", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def generate_prd_document(req: func.HttpRequest, project_id: str) -> func.HttpResponse:
    """Generate comprehensive PRD document compilation and export"""
    try:
        # Extract user info and request data
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, headers={"Content-Type": "application/json"}
            )

        request_data = json.loads(req.get_body().decode("utf-8"))
        prd_components = request_data.get("prdComponents", {})
        export_format = request_data.get("exportFormat", "markdown")  # markdown, docx, pdf
        template_style = request_data.get("templateStyle", "standard")  # standard, executive, technical

        # Generate PRD document structure
        prd_document = _generate_prd_document_structure(prd_components, template_style, export_format)

        # Validate document completeness
        completeness_check = _validate_prd_completeness(prd_document)

        # Generate export data based on format
        export_data = _generate_export_data(prd_document, export_format)

        # Prepare document result
        document_result = {
            "projectId": project_id,
            "generationTimestamp": datetime.now(timezone.utc).isoformat(),
            "documentStructure": prd_document,
            "exportData": export_data,
            "exportFormat": export_format,
            "templateStyle": template_style,
            "completenessCheck": completeness_check,
            "documentMetrics": {
                "totalSections": len(prd_document.get("sections", [])),
                "completedSections": len([s for s in prd_document.get("sections", []) if s.get("content")]),
                "wordCount": _calculate_word_count(prd_document),
                "readabilityScore": _calculate_readability_score(prd_document),
            },
        }

        return func.HttpResponse(json.dumps(document_result), status_code=200, headers={"Content-Type": "application/json"})

    except Exception as e:
        logger.error(f"Error generating PRD document: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to generate PRD document", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def complete_prd_stage(req: func.HttpRequest, project_id: str) -> func.HttpResponse:
    """Complete the PRD generation stage and prepare context for UX stage"""
    try:
        # Extract user info and request data
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, headers={"Content-Type": "application/json"}
            )

        request_data = json.loads(req.get_body().decode("utf-8"))
        final_prd_data = request_data.get("finalPRDData", {})
        force_complete = request_data.get("forceComplete", False)

        # Get project from database
        async with AsyncCosmosHelper() as db:
            try:
                project = await db.read_item(project_id, partition_key=user_info["user_id"])
            except CosmosResourceNotFoundError:
                return func.HttpResponse(
                    json.dumps({"error": "Project not found"}), status_code=404, headers={"Content-Type": "application/json"}
                )

            # Perform final quality assessment
            idea_context = project.get("forgeData", {}).get("idea_refinement", {})
            quality_result = quality_engine.calculate_quality_score(
                stage="prd_generation", content=final_prd_data, context=idea_context
            )

            # Get thresholds
            thresholds = quality_engine.get_dynamic_threshold("prd_generation", idea_context)

            # Cross-stage validation
            project_data_with_prd = {**project, "forgeData": {**project.get("forgeData", {}), "prd_generation": final_prd_data}}

            cross_stage_validation = quality_validator.validate_cross_stage_consistency(
                "idea_refinement", "prd_generation", project_data_with_prd
            )

            # Check if stage can be completed
            can_complete = (
                quality_result.quality_gate_status in ["PROCEED_WITH_CAUTION", "PROCEED_EXCELLENT"]
                and cross_stage_validation.is_consistent
            ) or force_complete

            if not can_complete:
                return func.HttpResponse(
                    json.dumps(
                        {
                            "error": "Quality threshold not met",
                            "currentScore": quality_result.overall_score,
                            "requiredScore": thresholds.minimum,
                            "consistencyIssues": cross_stage_validation.validation_errors,
                            "improvementSuggestions": quality_result.improvement_suggestions,
                            "canForceComplete": user_info.get("role") in ["expert", "admin"],
                        }
                    ),
                    status_code=400,
                    headers={"Content-Type": "application/json"},
                )

            # Prepare context handoff for UX stage
            ux_context_handoff = quality_validator.prepare_context_handoff(
                "prd_generation", "ux_requirements", project_data_with_prd
            )

            # Update project in database
            project["forgeData"]["prd_generation"] = {
                **final_prd_data,
                "status": "completed",
                "completedAt": datetime.now(timezone.utc).isoformat(),
                "qualityMetrics": {
                    "overall": quality_result.overall_score,
                    "dimensions": quality_result.dimension_scores,
                    "gateStatus": quality_result.quality_gate_status,
                    "forceCompleted": force_complete,
                },
                "contextForNextStage": ux_context_handoff.context_data,
            }

            project["updatedAt"] = datetime.now(timezone.utc).isoformat()

            # Save updated project
            await db.upsert_item(project)

            # Prepare completion result
            completion_result = {
                "projectId": project_id,
                "stageCompleted": "prd_generation",
                "completionTimestamp": datetime.now(timezone.utc).isoformat(),
                "finalQualityScore": quality_result.overall_score,
                "qualityGateStatus": quality_result.quality_gate_status,
                "crossStageConsistency": cross_stage_validation.is_consistent,
                "forceCompleted": force_complete,
                "readyForNextStage": True,
                "nextStage": "ux_requirements",
                "contextHandoff": {
                    "contextPrepared": True,
                    "consistencyScore": ux_context_handoff.consistency_score,
                    "handoffKeys": list(ux_context_handoff.context_data.keys()),
                },
                "qualityImpactOnNextStage": _predict_ux_quality_impact(quality_result, cross_stage_validation),
            }

            return func.HttpResponse(json.dumps(completion_result), status_code=200, headers={"Content-Type": "application/json"})

    except Exception as e:
        logger.error(f"Error completing PRD stage: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to complete stage", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


# Helper functions for PRD generation


def _create_requirements_extraction_prompt(idea_context: Dict[str, Any], focus_areas: List[str]) -> str:
    """Create LLM prompt for intelligent requirements extraction"""

    prompt = f"""
You are an expert product manager helping extract comprehensive requirements from a validated product idea.

VALIDATED IDEA CONTEXT:
Problem Statement: {idea_context.get('problemStatement', '')}
Target Audience: {idea_context.get('targetAudience', '')}
Value Proposition: {idea_context.get('valueProposition', '')}
Market Context: {json.dumps(idea_context.get('marketContext', {}), indent=2)}

EXTRACTION FOCUS AREAS:
{', '.join(focus_areas) if focus_areas else 'Comprehensive requirements analysis'}

Extract detailed requirements in the following JSON format:

{{
    "functionalRequirements": [
        {{
            "id": "FR001",
            "title": "Clear requirement title",
            "description": "Detailed description aligned to problem statement",
            "priority": "High/Medium/Low",
            "userStoryMapping": "Reference to target audience needs",
            "acceptanceCriteria": ["Specific measurable criteria"],
            "businessValue": "Direct connection to value proposition"
        }}
    ],
    "nonFunctionalRequirements": [
        {{
            "id": "NFR001",
            "category": "Performance/Security/Usability/Scalability",
            "requirement": "Specific measurable requirement",
            "rationale": "Connection to target audience needs",
            "testCriteria": "How to validate this requirement"
        }}
    ],
    "businessRules": [
        {{
            "rule": "Clear business rule statement",
            "rationale": "Why this rule exists",
            "impact": "Effect on user experience and business"
        }}
    ],
    "constraints": [
        {{
            "type": "Technical/Business/Legal/Time",
            "constraint": "Specific limitation",
            "impact": "How this affects requirements"
        }}
    ],
    "assumptions": [
        {{
            "assumption": "What we're assuming to be true",
            "riskLevel": "High/Medium/Low",
            "validationMethod": "How to verify this assumption"
        }}
    ]
}}

Ensure all requirements directly align with the validated idea context and target audience needs.
"""

    return prompt.strip()


def _create_user_story_prompt(requirements: Dict[str, Any], idea_context: Dict[str, Any], story_format: str) -> str:
    """Create LLM prompt for user story generation"""

    format_instructions = {
        "standard": "Standard 'As a [user], I want [goal] so that [benefit]' format",
        "gherkin": "Gherkin format with Given/When/Then scenarios",
        "invest": "INVEST criteria focus (Independent, Negotiable, Valuable, Estimable, Small, Testable)",
    }

    prompt = f"""
You are an expert product manager creating user stories from requirements with validated user context.

VALIDATED USER CONTEXT:
Target Audience: {idea_context.get('targetAudience', '')}
Value Proposition: {idea_context.get('valueProposition', '')}
Problem Statement: {idea_context.get('problemStatement', '')}

FUNCTIONAL REQUIREMENTS:
{json.dumps(requirements.get('functionalRequirements', []), indent=2)}

STORY FORMAT: {format_instructions.get(story_format, 'Standard format')}

Generate user stories in this JSON format:

{{
    "userPersonas": [
        {{
            "name": "Primary User Type",
            "description": "Based on target audience",
            "goals": ["What they want to achieve"],
            "painPoints": ["Current problems they face"]
        }}
    ],
    "stories": [
        {{
            "id": "US001",
            "title": "Clear story title",
            "asA": "User type from personas",
            "iWant": "Specific functionality needed",
            "soThat": "Clear benefit tied to value proposition",
            "acceptanceCriteria": [
                "Specific, testable criteria",
                "Measurable success conditions"
            ],
            "priority": "High/Medium/Low",
            "estimatedEffort": "Story points or time estimate",
            "businessValue": "Connection to value proposition",
            "requirementMapping": ["FR001", "FR002"],
            "investValidation": {{
                "independent": true/false,
                "negotiable": true/false,
                "valuable": true/false,
                "estimable": true/false,
                "small": true/false,
                "testable": true/false
            }}
        }}
    ],
    "epicGrouping": [
        {{
            "epicName": "Related functionality group",
            "storyIds": ["US001", "US002"],
            "businessObjective": "High-level goal alignment"
        }}
    ]
}}

Ensure all stories align with the validated target audience and directly support the value proposition.
"""

    return prompt.strip()


def _create_feature_prioritization_prompt(features: List[Dict], user_stories: Dict, idea_context: Dict, method: str) -> str:
    """Create LLM prompt for feature prioritization"""

    method_instructions = {
        "rice": "RICE scoring (Reach, Impact, Confidence, Effort)",
        "moscow": "MoSCoW prioritization (Must have, Should have, Could have, Won't have)",
        "kano": "Kano model (Basic, Performance, Excitement features)",
    }

    prompt = f"""
You are an expert product strategist prioritizing features using {method_instructions.get(method, 'RICE')} methodology.

VALUE PROPOSITION CONTEXT:
{idea_context.get('valueProposition', '')}

TARGET AUDIENCE:
{idea_context.get('targetAudience', '')}

FEATURES TO PRIORITIZE:
{json.dumps(features, indent=2)}

USER STORIES CONTEXT:
{json.dumps(user_stories.get('stories', [])[:5], indent=2)}  # First 5 stories for context

Use {method.upper()} methodology to prioritize features in this JSON format:

{{
    "prioritizationMethod": "{method}",
    "features": [
        {{
            "featureId": "Original feature ID",
            "featureName": "Feature name",
            "description": "Feature description",
            "priority": "Priority level based on method",
            "businessValue": "1-10 scale value to business",
            "userValue": "1-10 scale value to users",
            "alignmentScore": "1-10 alignment with value proposition",
            "rationale": "Why this priority level",
            "dependencies": ["Other features this depends on"],
            "risks": ["Potential risks or challenges"],
            "mvpCandidate": true/false,
            "methodSpecificScoring": {{
                // For RICE: "reach": X, "impact": X, "confidence": X, "effort": X, "score": X
                // For MoSCoW: "category": "Must/Should/Could/Won't", "justification": "reason"
                // For Kano: "category": "Basic/Performance/Excitement", "satisfactionImpact": X
            }}
        }}
    ],
    "prioritySummary": {{
        "highPriorityCount": X,
        "mvpFeatureCount": X,
        "totalBusinessValue": X,
        "recommendations": ["Strategic recommendations"]
    }}
}}

Ensure prioritization directly supports the value proposition and target audience needs.
"""

    return prompt.strip()


def _parse_requirements_response(response_content: str) -> Dict[str, Any]:
    """Parse and validate LLM response for requirements extraction"""
    try:
        import re

        json_match = re.search(r"\{.*\}", response_content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return {
                "functionalRequirements": [],
                "nonFunctionalRequirements": [],
                "businessRules": [],
                "constraints": [],
                "assumptions": [],
                "extractionNotes": "Response parsing required manual review",
            }
    except Exception as e:
        logger.warning(f"Error parsing requirements response: {str(e)}")
        return {"functionalRequirements": [], "nonFunctionalRequirements": [], "extractionError": str(e)}


def _parse_user_stories_response(response_content: str) -> Dict[str, Any]:
    """Parse and validate LLM response for user stories"""
    try:
        import re

        json_match = re.search(r"\{.*\}", response_content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return {
                "userPersonas": [],
                "stories": [],
                "epicGrouping": [],
                "parsingNotes": "Response parsing required manual review",
            }
    except Exception as e:
        logger.warning(f"Error parsing user stories response: {str(e)}")
        return {"stories": [], "parsingError": str(e)}


def _parse_prioritization_response(response_content: str, method: str) -> Dict[str, Any]:
    """Parse and validate LLM response for feature prioritization"""
    try:
        import re

        json_match = re.search(r"\{.*\}", response_content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return {
                "prioritizationMethod": method,
                "features": [],
                "prioritySummary": {},
                "parsingNotes": "Response parsing required manual review",
            }
    except Exception as e:
        logger.warning(f"Error parsing prioritization response: {str(e)}")
        return {"prioritizationMethod": method, "features": [], "parsingError": str(e)}


def _validate_invest_criteria(user_stories: Dict[str, Any]) -> Dict[str, float]:
    """Validate user stories against INVEST criteria"""
    invest_scores = {"independent": 0.0, "negotiable": 0.0, "valuable": 0.0, "estimable": 0.0, "small": 0.0, "testable": 0.0}

    stories = user_stories.get("stories", [])
    if not stories:
        return invest_scores

    for story in stories:
        invest_data = story.get("investValidation", {})
        for criteria in invest_scores.keys():
            if invest_data.get(criteria, False):
                invest_scores[criteria] += 1

    # Convert to percentages
    story_count = len(stories)
    for criteria in invest_scores.keys():
        invest_scores[criteria] = (invest_scores[criteria] / story_count) * 100 if story_count > 0 else 0

    return invest_scores


def _calculate_business_alignment(prioritized_features: Dict[str, Any], value_proposition: str) -> Dict[str, Any]:
    """Calculate business alignment metrics"""
    features = prioritized_features.get("features", [])
    if not features:
        return {"averageAlignment": 0, "highAlignmentCount": 0}

    alignments = [f.get("alignmentScore", 0) for f in features]
    avg_alignment = sum(alignments) / len(alignments)
    high_alignment_count = len([a for a in alignments if a >= 8])

    return {
        "averageAlignment": avg_alignment,
        "highAlignmentCount": high_alignment_count,
        "totalFeatures": len(features),
        "alignmentDistribution": {
            "high": len([a for a in alignments if a >= 8]),
            "medium": len([a for a in alignments if 5 <= a < 8]),
            "low": len([a for a in alignments if a < 5]),
        },
    }


def _generate_prd_document_structure(components: Dict[str, Any], style: str, format: str) -> Dict[str, Any]:
    """Generate PRD document structure"""
    return {
        "title": components.get("title", "Product Requirements Document"),
        "version": "1.0",
        "sections": [
            {"name": "Executive Summary", "content": components.get("executiveSummary", "")},
            {"name": "Problem Statement", "content": components.get("problemStatement", "")},
            {"name": "User Personas", "content": components.get("userPersonas", [])},
            {"name": "Functional Requirements", "content": components.get("functionalRequirements", [])},
            {"name": "User Stories", "content": components.get("userStories", [])},
            {"name": "Feature Prioritization", "content": components.get("featurePrioritization", {})},
            {"name": "Non-Functional Requirements", "content": components.get("nonFunctionalRequirements", [])},
            {"name": "Business Rules", "content": components.get("businessRules", [])},
            {"name": "Assumptions & Constraints", "content": components.get("assumptions", [])},
        ],
        "style": style,
        "format": format,
    }


def _validate_prd_completeness(document: Dict[str, Any]) -> Dict[str, Any]:
    """Validate PRD document completeness"""
    required_sections = ["Executive Summary", "Problem Statement", "Functional Requirements", "User Stories"]
    sections = document.get("sections", [])
    section_names = [s.get("name") for s in sections]

    missing_sections = [req for req in required_sections if req not in section_names]
    incomplete_sections = [s.get("name") for s in sections if not s.get("content")]

    completeness_score = ((len(required_sections) - len(missing_sections)) / len(required_sections)) * 100

    return {
        "completenessScore": completeness_score,
        "missingSections": missing_sections,
        "incompleteSections": incomplete_sections,
        "isComplete": len(missing_sections) == 0 and len(incomplete_sections) == 0,
    }


def _generate_export_data(document: Dict[str, Any], format: str) -> Dict[str, Any]:
    """Generate export data based on format"""
    if format == "markdown":
        return {"content": _convert_to_markdown(document), "mimeType": "text/markdown"}
    elif format == "json":
        return {"content": json.dumps(document, indent=2), "mimeType": "application/json"}
    else:
        return {"content": str(document), "mimeType": "text/plain"}


def _convert_to_markdown(document: Dict[str, Any]) -> str:
    """Convert document to Markdown format"""
    markdown = f"# {document.get('title', 'PRD')}\n\n"

    for section in document.get("sections", []):
        markdown += f"## {section.get('name', '')}\n\n"
        content = section.get("content", "")
        if isinstance(content, list):
            for item in content:
                markdown += f"- {item}\n"
        else:
            markdown += f"{content}\n"
        markdown += "\n"

    return markdown


def _calculate_word_count(document: Dict[str, Any]) -> int:
    """Calculate word count of document"""
    total_words = 0
    for section in document.get("sections", []):
        content = str(section.get("content", ""))
        total_words += len(content.split())
    return total_words


def _calculate_readability_score(document: Dict[str, Any]) -> float:
    """Calculate readability score (simplified)"""
    # Simplified readability calculation
    total_chars = 0
    total_words = 0

    for section in document.get("sections", []):
        content = str(section.get("content", ""))
        total_chars += len(content)
        total_words += len(content.split())

    if total_words == 0:
        return 0

    avg_word_length = total_chars / total_words if total_words > 0 else 0
    readability = max(0, min(100, 100 - (avg_word_length * 10)))  # Simplified score

    return readability


def _predict_ux_quality_impact(quality_result: Any, consistency_validation: Any) -> Dict[str, Any]:
    """Predict how PRD quality will impact UX requirements stage"""
    base_prediction = 82.0  # Base expectation for UX stage

    # Quality foundation impact
    quality_bonus = (quality_result.overall_score - 80) * 0.4

    # Consistency impact
    consistency_bonus = consistency_validation.consistency_score * 5

    # Dimension-specific impacts
    req_completeness = quality_result.dimension_scores.get("requirement_completeness", 80)
    user_story_quality = quality_result.dimension_scores.get("user_story_quality", 80)

    if req_completeness > 90:
        quality_bonus += 3
    if user_story_quality > 85:
        quality_bonus += 2

    predicted_ux_quality = min(95, base_prediction + quality_bonus + consistency_bonus)

    return {
        "predictedUXQuality": predicted_ux_quality,
        "qualityImpact": quality_bonus,
        "consistencyImpact": consistency_bonus,
        "strongFoundations": req_completeness > 85 and user_story_quality > 80,
        "recommendations": [
            "Use validated user stories for journey mapping",
            "Leverage functional requirements for wireframe details",
            "Build on business alignment for design decisions",
        ],
    }
