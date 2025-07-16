"""
UX Requirements API endpoints for the Forge module.
Implements comprehensive user experience specification generation with AI assistance,
accessibility compliance checking, and 82% quality threshold enforcement.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import azure.functions as func
from azure.cosmos.aio import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from shared.accessibility_validator import AccessibilityValidator
from shared.auth_helpers import extract_user_info
from shared.cost_tracker import CostTracker
from shared.llm_client import LLMClient
from shared.quality_engine import QualityAssessmentEngine
from shared.quality_validators import CrossStageQualityValidator

logger = logging.getLogger(__name__)

# Database configuration
COSMOS_CONNECTION_STRING = "your_cosmos_connection_string_here"
DATABASE_NAME = "SutraDB"
PLAYBOOKS_CONTAINER = "Playbooks"

quality_engine = QualityAssessmentEngine()
quality_validator = CrossStageQualityValidator()
accessibility_validator = AccessibilityValidator()


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main entry point for UX Requirements API endpoints."""
    try:
        # Extract method and route parameters
        method = req.method
        route_params = req.route_params
        action = route_params.get("action", "")
        project_id = route_params.get("project_id", "")

        logger.info(f"UX Requirements API - Method: {method}, Action: {action}, Project: {project_id}")

        # Route to appropriate handler
        if method == "POST" and action == "map-user-journeys":
            return await map_user_journeys(req, project_id)
        elif method == "POST" and action == "generate-wireframes":
            return await generate_wireframes(req, project_id)
        elif method == "POST" and action == "check-accessibility":
            return await check_accessibility_compliance(req, project_id)
        elif method == "POST" and action == "specify-interactions":
            return await specify_interactions(req, project_id)
        elif method == "GET" and action == "assessment":
            return await get_ux_quality_assessment(req, project_id)
        elif method == "POST" and action == "generate-document":
            return await generate_ux_document(req, project_id)
        elif method == "POST" and action == "complete":
            return await complete_ux_stage(req, project_id)
        else:
            return func.HttpResponse(
                json.dumps({"error": f"Unsupported operation: {method} {action}"}),
                status_code=405,
                headers={"Content-Type": "application/json"},
            )

    except Exception as e:
        logger.error(f"Error in UX requirements endpoint: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def map_user_journeys(req: func.HttpRequest, project_id: str) -> func.HttpResponse:
    """Map user journeys based on PRD user stories and personas"""
    try:
        # Extract user info and request data
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, headers={"Content-Type": "application/json"}
            )

        request_data = json.loads(req.get_body().decode("utf-8"))
        prd_context = request_data.get("prdContext", {})
        journey_focus = request_data.get("journeyFocus", [])
        selected_llm = request_data.get("selectedLLM", "claude-3-5-sonnet")

        # Validate PRD context
        validation_result = quality_validator.validate_stage_readiness(
            "ux_requirements", {"forgeData": {"prd_generation": prd_context}}
        )

        if not validation_result.is_consistent:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "PRD context validation failed",
                        "validation_errors": validation_result.validation_errors,
                        "recommendations": validation_result.recommendations,
                    }
                ),
                status_code=400,
                headers={"Content-Type": "application/json"},
            )

        # Initialize cost tracking
        cost_tracker = CostTracker()

        # Create user journey mapping prompt
        journey_prompt = _create_user_journey_prompt(prd_context, journey_focus)

        # Execute LLM call with cost tracking
        llm_client = LLMClient()

        await cost_tracker.track_llm_call_start(
            user_id=user_info.get("user_id"), operation="forge_ux_user_journeys", model=selected_llm, project_id=project_id
        )

        try:
            response = await llm_client.execute_prompt(
                prompt=journey_prompt, model=selected_llm, temperature=0.4, max_tokens=4000
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

        # Parse user journeys response
        user_journeys = _parse_user_journeys_response(response.get("content", ""))

        # Assess journey quality and accessibility considerations
        journey_quality = _assess_journey_quality(user_journeys, prd_context)

        # Validate cross-stage consistency
        consistency_check = quality_validator.validate_cross_stage_consistency(
            "prd_generation",
            "ux_requirements",
            {"forgeData": {"prd_generation": prd_context, "ux_requirements": {"userJourneys": user_journeys}}},
        )

        # Prepare journey mapping result
        journey_result = {
            "projectId": project_id,
            "mappingTimestamp": datetime.now(timezone.utc).isoformat(),
            "userJourneys": user_journeys,
            "qualityAssessment": journey_quality,
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
            "journeyMetrics": {
                "totalJourneys": len(user_journeys.get("journeys", [])),
                "averageSteps": _calculate_average_steps(user_journeys),
                "accessibilityConsiderations": len(user_journeys.get("accessibilityPaths", [])),
                "errorRecoveryPaths": len(user_journeys.get("errorRecovery", [])),
            },
        }

        return func.HttpResponse(json.dumps(journey_result), status_code=200, headers={"Content-Type": "application/json"})

    except Exception as e:
        logger.error(f"Error mapping user journeys: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to map user journeys", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def generate_wireframes(req: func.HttpRequest, project_id: str) -> func.HttpResponse:
    """Generate wireframes and design system specifications based on user journeys"""
    try:
        # Extract user info and request data
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, headers={"Content-Type": "application/json"}
            )

        request_data = json.loads(req.get_body().decode("utf-8"))
        user_journeys = request_data.get("userJourneys", {})
        prd_context = request_data.get("prdContext", {})
        design_preferences = request_data.get("designPreferences", {})
        selected_llm = request_data.get("selectedLLM", "gpt-4")

        # Initialize cost tracking
        cost_tracker = CostTracker()

        # Create wireframe generation prompt
        wireframe_prompt = _create_wireframe_prompt(user_journeys, prd_context, design_preferences)

        # Execute LLM call with cost tracking
        llm_client = LLMClient()

        await cost_tracker.track_llm_call_start(
            user_id=user_info.get("user_id"), operation="forge_ux_wireframes", model=selected_llm, project_id=project_id
        )

        try:
            response = await llm_client.execute_prompt(
                prompt=wireframe_prompt, model=selected_llm, temperature=0.3, max_tokens=5000
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

        # Parse wireframes response
        wireframes = _parse_wireframes_response(response.get("content", ""))

        # Validate design system consistency
        design_validation = _validate_design_system_consistency(wireframes)

        # Perform initial accessibility check
        initial_accessibility = accessibility_validator.validate_ux_requirements(
            {"wireframes": wireframes.get("wireframes", []), "designSystem": wireframes.get("designSystem", {})}
        )

        # Prepare wireframes result
        wireframes_result = {
            "projectId": project_id,
            "generationTimestamp": datetime.now(timezone.utc).isoformat(),
            "wireframes": wireframes,
            "designValidation": design_validation,
            "initialAccessibility": {
                "score": initial_accessibility.overall_score,
                "complianceLevel": initial_accessibility.compliance_level.value,
                "criticalIssues": len(
                    [c for c in initial_accessibility.checks if c.status.value == "fail" and c.priority <= 2]
                ),
            },
            "costTracking": {
                "tokensUsed": response.get("usage", {}).get("total_tokens", 0),
                "cost": response.get("cost", 0.0),
                "model": selected_llm,
            },
            "wireframeMetrics": {
                "totalWireframes": len(wireframes.get("wireframes", [])),
                "componentsSpecified": len(wireframes.get("designSystem", {}).get("components", [])),
                "responsiveBreakpoints": len(wireframes.get("responsiveSpecs", [])),
                "accessibilityFeatures": len(wireframes.get("accessibilityFeatures", [])),
            },
        }

        return func.HttpResponse(json.dumps(wireframes_result), status_code=200, headers={"Content-Type": "application/json"})

    except Exception as e:
        logger.error(f"Error generating wireframes: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to generate wireframes", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def check_accessibility_compliance(req: func.HttpRequest, project_id: str) -> func.HttpResponse:
    """Perform comprehensive accessibility compliance checking with WCAG 2.1 AA enforcement"""
    try:
        # Extract user info and request data
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, headers={"Content-Type": "application/json"}
            )

        request_data = json.loads(req.get_body().decode("utf-8"))
        ux_requirements = request_data.get("uxRequirements", {})

        # Perform comprehensive accessibility validation
        accessibility_assessment = accessibility_validator.validate_ux_requirements(ux_requirements)

        # Check if minimum 90% accessibility threshold is met
        meets_minimum = accessibility_assessment.overall_score >= 90.0

        # Generate actionable recommendations
        actionable_recommendations = _generate_actionable_accessibility_recommendations(accessibility_assessment)

        # Prepare compliance result
        compliance_result = {
            "projectId": project_id,
            "assessmentTimestamp": datetime.now(timezone.utc).isoformat(),
            "accessibilityScore": accessibility_assessment.overall_score,
            "complianceLevel": accessibility_assessment.compliance_level.value,
            "meetsMinimumThreshold": meets_minimum,
            "summary": accessibility_assessment.summary,
            "detailedChecks": [
                {
                    "checkId": check.check_id,
                    "guideline": check.guideline,
                    "successCriterion": check.success_criterion,
                    "level": check.level.value,
                    "status": check.status.value,
                    "confidence": check.confidence,
                    "description": check.description,
                    "recommendation": check.recommendation,
                    "impact": check.impact,
                    "priority": check.priority,
                }
                for check in accessibility_assessment.checks
            ],
            "actionableRecommendations": actionable_recommendations,
            "manualChecksNeeded": accessibility_assessment.manual_checks_needed,
            "estimatedRemediationTime": accessibility_assessment.estimated_remediation_time,
            "complianceGaps": [
                check.description
                for check in accessibility_assessment.checks
                if check.status.value == "fail" and check.priority <= 2
            ],
        }

        return func.HttpResponse(json.dumps(compliance_result), status_code=200, headers={"Content-Type": "application/json"})

    except Exception as e:
        logger.error(f"Error checking accessibility compliance: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to check accessibility", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def specify_interactions(req: func.HttpRequest, project_id: str) -> func.HttpResponse:
    """Specify detailed interaction patterns and micro-interactions with feasibility assessment"""
    try:
        # Extract user info and request data
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, headers={"Content-Type": "application/json"}
            )

        request_data = json.loads(req.get_body().decode("utf-8"))
        wireframes = request_data.get("wireframes", {})
        user_journeys = request_data.get("userJourneys", {})
        interaction_focus = request_data.get("interactionFocus", "standard")  # standard, advanced, minimal
        selected_llm = request_data.get("selectedLLM", "claude-3-5-sonnet")

        # Initialize cost tracking
        cost_tracker = CostTracker()

        # Create interaction specification prompt
        interaction_prompt = _create_interaction_prompt(wireframes, user_journeys, interaction_focus)

        # Execute LLM call with cost tracking
        llm_client = LLMClient()

        await cost_tracker.track_llm_call_start(
            user_id=user_info.get("user_id"), operation="forge_ux_interactions", model=selected_llm, project_id=project_id
        )

        try:
            response = await llm_client.execute_prompt(
                prompt=interaction_prompt, model=selected_llm, temperature=0.3, max_tokens=4000
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

        # Parse interaction specifications
        interactions = _parse_interaction_response(response.get("content", ""))

        # Assess interaction feasibility
        feasibility_assessment = _assess_interaction_feasibility(interactions)

        # Validate accessibility for interactions
        interaction_accessibility = accessibility_validator.validate_ux_requirements(
            {"interactions": interactions.get("interactions", [])}
        )

        # Prepare interactions result
        interactions_result = {
            "projectId": project_id,
            "specificationTimestamp": datetime.now(timezone.utc).isoformat(),
            "interactionSpecifications": interactions,
            "feasibilityAssessment": feasibility_assessment,
            "accessibilityValidation": {
                "score": interaction_accessibility.overall_score,
                "criticalIssues": len([c for c in interaction_accessibility.checks if c.status.value == "fail"]),
            },
            "costTracking": {
                "tokensUsed": response.get("usage", {}).get("total_tokens", 0),
                "cost": response.get("cost", 0.0),
                "model": selected_llm,
            },
            "interactionMetrics": {
                "totalInteractions": len(interactions.get("interactions", [])),
                "microInteractions": len(interactions.get("microInteractions", [])),
                "animationSpecs": len(interactions.get("animations", [])),
                "responsiveInteractions": len(interactions.get("responsiveBehaviors", [])),
            },
        }

        return func.HttpResponse(
            json.dumps(interactions_result), status_code=200, headers={"Content-Type": "application/json"}
        )

    except Exception as e:
        logger.error(f"Error specifying interactions: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to specify interactions", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def get_ux_quality_assessment(req: func.HttpRequest, project_id: str) -> func.HttpResponse:
    """Get current quality assessment for the UX requirements stage"""
    try:
        # Extract user info
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, headers={"Content-Type": "application/json"}
            )

        # Get project from database
        async with CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING) as client:
            database = client.get_database_client(DATABASE_NAME)
            container = database.get_container_client(PLAYBOOKS_CONTAINER)

            try:
                project = await container.read_item(item=project_id, partition_key=user_info["user_id"])
            except CosmosResourceNotFoundError:
                return func.HttpResponse(
                    json.dumps({"error": "Project not found"}), status_code=404, headers={"Content-Type": "application/json"}
                )

        # Extract UX data
        forge_data = project.get("forgeData", {})
        ux_data = forge_data.get("ux_requirements", {})
        prd_context = forge_data.get("prd_generation", {})

        if not ux_data:
            return func.HttpResponse(
                json.dumps({"error": "No UX requirements data found"}),
                status_code=404,
                headers={"Content-Type": "application/json"},
            )

        # Perform quality assessment
        quality_result = quality_engine.calculate_quality_score(stage="ux_requirements", content=ux_data, context=prd_context)

        # Get adaptive thresholds
        thresholds = quality_engine.get_dynamic_threshold("ux_requirements", prd_context)

        # Cross-stage validation
        cross_stage_validation = quality_validator.validate_cross_stage_consistency(
            "prd_generation", "ux_requirements", project
        )

        # Accessibility assessment
        accessibility_assessment = accessibility_validator.validate_ux_requirements(ux_data)
        accessibility_meets_minimum = accessibility_assessment.overall_score >= 90.0

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
            "accessibilityCompliance": {
                "score": accessibility_assessment.overall_score,
                "complianceLevel": accessibility_assessment.compliance_level.value,
                "meetsMinimum": accessibility_meets_minimum,
                "criticalIssues": len(
                    [c for c in accessibility_assessment.checks if c.status.value == "fail" and c.priority <= 2]
                ),
            },
            "crossStageValidation": {
                "isConsistent": cross_stage_validation.is_consistent,
                "consistencyScore": cross_stage_validation.consistency_score,
                "validationErrors": cross_stage_validation.validation_errors,
                "recommendations": cross_stage_validation.recommendations,
            },
            "improvementOpportunities": quality_result.improvement_suggestions,
            "estimatedImprovementTime": quality_result.estimated_improvement_time,
            "readyForNextStage": (
                quality_result.quality_gate_status in ["PROCEED_WITH_CAUTION", "PROCEED_EXCELLENT"]
                and cross_stage_validation.is_consistent
                and accessibility_meets_minimum
            ),
        }

        return func.HttpResponse(json.dumps(assessment_result), status_code=200, headers={"Content-Type": "application/json"})

    except Exception as e:
        logger.error(f"Error getting UX quality assessment: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to get quality assessment", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def generate_ux_document(req: func.HttpRequest, project_id: str) -> func.HttpResponse:
    """Generate comprehensive UX requirements document with accessibility specifications"""
    try:
        # Extract user info and request data
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, headers={"Content-Type": "application/json"}
            )

        request_data = json.loads(req.get_body().decode("utf-8"))
        ux_components = request_data.get("uxComponents", {})
        export_format = request_data.get("exportFormat", "markdown")
        include_accessibility_report = request_data.get("includeAccessibilityReport", True)

        # Generate UX document structure
        ux_document = _generate_ux_document_structure(ux_components, export_format, include_accessibility_report)

        # Validate document completeness
        completeness_check = _validate_ux_document_completeness(ux_document)

        # Generate export data based on format
        export_data = _generate_ux_export_data(ux_document, export_format)

        # Prepare document result
        document_result = {
            "projectId": project_id,
            "generationTimestamp": datetime.now(timezone.utc).isoformat(),
            "documentStructure": ux_document,
            "exportData": export_data,
            "exportFormat": export_format,
            "completenessCheck": completeness_check,
            "documentMetrics": {
                "totalSections": len(ux_document.get("sections", [])),
                "completedSections": len([s for s in ux_document.get("sections", []) if s.get("content")]),
                "wireframeCount": len(ux_document.get("wireframes", [])),
                "interactionCount": len(ux_document.get("interactions", [])),
                "accessibilityChecks": len(ux_document.get("accessibilityReport", {}).get("checks", [])),
            },
        }

        return func.HttpResponse(json.dumps(document_result), status_code=200, headers={"Content-Type": "application/json"})

    except Exception as e:
        logger.error(f"Error generating UX document: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to generate UX document", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def complete_ux_stage(req: func.HttpRequest, project_id: str) -> func.HttpResponse:
    """Complete the UX requirements stage and prepare context for technical analysis"""
    try:
        # Extract user info and request data
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, headers={"Content-Type": "application/json"}
            )

        request_data = json.loads(req.get_body().decode("utf-8"))
        final_ux_data = request_data.get("finalUXData", {})
        force_complete = request_data.get("forceComplete", False)

        # Get project from database
        async with CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING) as client:
            database = client.get_database_client(DATABASE_NAME)
            container = database.get_container_client(PLAYBOOKS_CONTAINER)

            try:
                project = await container.read_item(item=project_id, partition_key=user_info["user_id"])
            except CosmosResourceNotFoundError:
                return func.HttpResponse(
                    json.dumps({"error": "Project not found"}), status_code=404, headers={"Content-Type": "application/json"}
                )

        # Perform final quality assessment
        prd_context = project.get("forgeData", {}).get("prd_generation", {})
        quality_result = quality_engine.calculate_quality_score(
            stage="ux_requirements", content=final_ux_data, context=prd_context
        )

        # Get thresholds
        thresholds = quality_engine.get_dynamic_threshold("ux_requirements", prd_context)

        # Accessibility compliance check
        accessibility_assessment = accessibility_validator.validate_ux_requirements(final_ux_data)
        accessibility_meets_minimum = accessibility_assessment.overall_score >= 90.0

        # Cross-stage validation
        project_data_with_ux = {**project, "forgeData": {**project.get("forgeData", {}), "ux_requirements": final_ux_data}}

        cross_stage_validation = quality_validator.validate_cross_stage_consistency(
            "prd_generation", "ux_requirements", project_data_with_ux
        )

        # Check if stage can be completed
        can_complete = (
            quality_result.quality_gate_status in ["PROCEED_WITH_CAUTION", "PROCEED_EXCELLENT"]
            and cross_stage_validation.is_consistent
            and accessibility_meets_minimum
        ) or force_complete

        if not can_complete:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "Quality thresholds not met",
                        "currentScore": quality_result.overall_score,
                        "requiredScore": thresholds.minimum,
                        "accessibilityScore": accessibility_assessment.overall_score,
                        "accessibilityRequired": 90.0,
                        "consistencyIssues": cross_stage_validation.validation_errors,
                        "improvementSuggestions": quality_result.improvement_suggestions,
                        "accessibilityRecommendations": accessibility_assessment.recommendations,
                        "canForceComplete": user_info.get("role") in ["expert", "admin"],
                    }
                ),
                status_code=400,
                headers={"Content-Type": "application/json"},
            )

        # Prepare context handoff for technical analysis stage
        tech_context_handoff = quality_validator.prepare_context_handoff(
            "ux_requirements", "technical_analysis", project_data_with_ux
        )

        # Update project in database
        project["forgeData"]["ux_requirements"] = {
            **final_ux_data,
            "status": "completed",
            "completedAt": datetime.now(timezone.utc).isoformat(),
            "qualityMetrics": {
                "overall": quality_result.overall_score,
                "dimensions": quality_result.dimension_scores,
                "gateStatus": quality_result.quality_gate_status,
                "forceCompleted": force_complete,
            },
            "accessibilityCompliance": {
                "score": accessibility_assessment.overall_score,
                "complianceLevel": accessibility_assessment.compliance_level.value,
                "criticalIssueCount": len(
                    [c for c in accessibility_assessment.checks if c.status.value == "fail" and c.priority <= 2]
                ),
            },
            "contextForNextStage": tech_context_handoff.context_data,
        }

        project["updatedAt"] = datetime.now(timezone.utc).isoformat()

        # Save updated project
        await container.replace_item(item=project["id"], body=project)

        # Prepare completion result
        completion_result = {
            "projectId": project_id,
            "stageCompleted": "ux_requirements",
            "completionTimestamp": datetime.now(timezone.utc).isoformat(),
            "finalQualityScore": quality_result.overall_score,
            "qualityGateStatus": quality_result.quality_gate_status,
            "accessibilityCompliance": {
                "score": accessibility_assessment.overall_score,
                "complianceLevel": accessibility_assessment.compliance_level.value,
                "meetsMinimum": accessibility_meets_minimum,
            },
            "crossStageConsistency": cross_stage_validation.is_consistent,
            "forceCompleted": force_complete,
            "readyForNextStage": True,
            "nextStage": "technical_analysis",
            "contextHandoff": {
                "contextPrepared": True,
                "consistencyScore": tech_context_handoff.consistency_score,
                "handoffKeys": list(tech_context_handoff.context_data.keys()),
            },
            "qualityImpactOnNextStage": _predict_technical_quality_impact(
                quality_result, accessibility_assessment, cross_stage_validation
            ),
        }

        return func.HttpResponse(json.dumps(completion_result), status_code=200, headers={"Content-Type": "application/json"})

    except Exception as e:
        logger.error(f"Error completing UX stage: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to complete stage", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


# Helper functions for UX requirements generation


def _create_user_journey_prompt(prd_context: Dict[str, Any], focus_areas: List[str]) -> str:
    """Create LLM prompt for user journey mapping"""

    user_stories = prd_context.get("userStories", {}).get("stories", [])
    personas = prd_context.get("userStories", {}).get("userPersonas", [])
    features = prd_context.get("prioritizedFeatures", {}).get("features", [])

    prompt = f"""
You are an expert UX designer creating comprehensive user journey maps based on validated PRD data.

VALIDATED PRD CONTEXT:
User Personas: {json.dumps(personas, indent=2)}
User Stories: {json.dumps(user_stories[:5], indent=2)}  # Top 5 for context
Prioritized Features: {json.dumps(features[:3], indent=2)}  # Top 3 MVP features

JOURNEY FOCUS AREAS:
{', '.join(focus_areas) if focus_areas else 'Core user flows and accessibility considerations'}

Create comprehensive user journeys in the following JSON format:

{{
    "journeys": [
        {{
            "id": "journey_001",
            "title": "Primary User Goal Achievement",
            "persona": "Reference to persona from PRD",
            "triggerEvent": "What initiates this journey",
            "goal": "What user wants to accomplish",
            "steps": [
                {{
                    "stepNumber": 1,
                    "action": "Specific user action",
                    "touchpoint": "Where this happens (web, mobile, etc.)",
                    "userThoughts": "What user is thinking/feeling",
                    "painPoints": ["Potential friction points"],
                    "opportunities": ["Improvement opportunities"],
                    "successCriteria": "How to measure success"
                }}
            ],
            "alternativePaths": [
                {{
                    "condition": "When this path is taken",
                    "steps": ["Modified journey steps"],
                    "accessibilityConsiderations": ["Screen reader paths", "Keyboard navigation", "Motor disability accommodations"]
                }}
            ],
            "errorRecovery": [
                {{
                    "errorType": "What can go wrong",
                    "recoveryAction": "How user can recover",
                    "preventionStrategy": "How to prevent this error"
                }}
            ],
            "emotionalJourney": {{
                "startEmotion": "User's emotional state at start",
                "endEmotion": "Desired emotional state at end",
                "emotionalLowPoints": ["Where user might feel frustrated"],
                "emotionalHighPoints": ["Where user feels accomplished"]
            }},
            "accessibilityRequirements": [
                "WCAG 2.1 AA considerations for this journey",
                "Keyboard navigation requirements",
                "Screen reader accommodations",
                "Motor disability considerations"
            ]
        }}
    ],
    "crossJourneyPatterns": [
        {{
            "pattern": "Common navigation pattern",
            "journeys": ["journey_001", "journey_002"],
            "designImplication": "What this means for design"
        }}
    ],
    "accessibilityPaths": [
        {{
            "assistiveTechnology": "Screen reader/Keyboard/Voice control",
            "modifiedJourney": "How journey changes with this technology",
            "criticalRequirements": ["Must-have accessibility features"]
        }}
    ]
}}

Ensure all journeys directly support the PRD user stories and prioritized features.
Include comprehensive accessibility considerations for WCAG 2.1 AA compliance.
"""

    return prompt.strip()


def _create_wireframe_prompt(journeys: Dict[str, Any], prd_context: Dict[str, Any], preferences: Dict[str, Any]) -> str:
    """Create LLM prompt for wireframe generation"""

    prompt = f"""
You are an expert UX/UI designer creating detailed wireframes and design system specifications.

USER JOURNEY CONTEXT:
{json.dumps(journeys.get('journeys', [])[:3], indent=2)}  # Top 3 journeys

PRD REQUIREMENTS:
Functional Requirements: {json.dumps(prd_context.get('requirements', {}).get('functionalRequirements', [])[:5], indent=2)}

DESIGN PREFERENCES:
{json.dumps(preferences, indent=2)}

Create comprehensive wireframes and design system in this JSON format:

{{
    "wireframes": [
        {{
            "id": "wireframe_001",
            "title": "Screen/Page Title",
            "type": "Landing/Form/Dashboard/etc.",
            "journeyContext": ["Which journeys this supports"],
            "layout": {{
                "structure": "Header, main content, sidebar, footer layout description",
                "gridSystem": "12-column/CSS Grid specification",
                "responsiveBreakpoints": ["mobile: 320px", "tablet: 768px", "desktop: 1024px"]
            }},
            "headings": [
                {{
                    "level": 1,
                    "text": "Page heading",
                    "purpose": "Primary page title"
                }},
                {{
                    "level": 2,
                    "text": "Section heading",
                    "purpose": "Content organization"
                }}
            ],
            "content": [
                {{
                    "type": "text/image/form/button",
                    "description": "Content description",
                    "accessibility": {{
                        "altText": "For images",
                        "ariaLabel": "For interactive elements",
                        "role": "ARIA role if needed"
                    }}
                }}
            ],
            "interactiveElements": [
                {{
                    "id": "element_001",
                    "type": "button/link/input",
                    "label": "Element label",
                    "function": "What it does",
                    "focusIndicator": "How focus is shown",
                    "keyboardBehavior": "How it works with keyboard",
                    "touchTarget": "Minimum 44x44px for mobile"
                }}
            ],
            "images": [
                {{
                    "id": "img_001",
                    "description": "Image content description",
                    "altText": "Descriptive alt text",
                    "decorative": false,
                    "purpose": "Why this image is needed"
                }}
            ],
            "colorScheme": {{
                "primary": "#color-hex",
                "secondary": "#color-hex",
                "background": "#color-hex",
                "text": "#color-hex",
                "contrastRatios": {{
                    "primaryOnBackground": "4.5:1 minimum",
                    "textOnBackground": "4.5:1 minimum"
                }}
            }},
            "navigation": {{
                "primary": ["Home", "Features", "Contact"],
                "breadcrumbs": "If applicable",
                "skipLinks": ["Skip to main content", "Skip to navigation"],
                "keyboardNavigation": "Tab order specification"
            }}
        }}
    ],
    "designSystem": {{
        "typography": {{
            "fontFamilies": ["Primary font", "Fallback fonts"],
            "fontSizes": [16, 18, 20, 24, 32, 48],
            "lineHeights": ["1.4 for body", "1.2 for headings"],
            "fontWeights": [400, 600, 700]
        }},
        "colorPalette": {{
            "primary": {{
                "50": "#lightest",
                "500": "#main",
                "900": "#darkest"
            }},
            "semantic": {{
                "success": "#green",
                "warning": "#yellow",
                "error": "#red",
                "info": "#blue"
            }},
            "neutral": {{
                "white": "#ffffff",
                "gray-100": "#f5f5f5",
                "gray-900": "#1a1a1a"
            }}
        }},
        "spacing": {{
            "scale": [4, 8, 12, 16, 24, 32, 48, 64],
            "touchTargets": {{
                "minimum": 44,
                "recommended": 48,
                "comfortable": 56
            }}
        }},
        "components": [
            {{
                "name": "Button",
                "variants": ["primary", "secondary", "outline"],
                "states": ["default", "hover", "focus", "disabled"],
                "accessibilityFeatures": ["Focus ring", "High contrast mode support"]
            }}
        ]
    }},
    "responsiveSpecs": [
        {{
            "breakpoint": "mobile",
            "maxWidth": "767px",
            "layoutChanges": "Stack elements vertically",
            "interactionChanges": "Touch-optimized controls"
        }}
    ],
    "accessibilityFeatures": [
        "Semantic HTML structure",
        "ARIA landmarks and labels",
        "Keyboard navigation support",
        "Screen reader optimization",
        "High contrast mode support",
        "Reduced motion options"
    ]
}}

Ensure all wireframes support the user journeys and meet WCAG 2.1 AA standards.
"""

    return prompt.strip()


def _create_interaction_prompt(wireframes: Dict[str, Any], journeys: Dict[str, Any], focus: str) -> str:
    """Create LLM prompt for interaction specification"""

    prompt = f"""
You are an expert interaction designer specifying detailed interaction patterns and micro-interactions.

WIREFRAME CONTEXT:
{json.dumps(wireframes.get('wireframes', [])[:2], indent=2)}  # Top 2 wireframes

USER JOURNEY CONTEXT:
{json.dumps(journeys.get('journeys', [])[:2], indent=2)}  # Top 2 journeys

INTERACTION FOCUS: {focus}

Create detailed interaction specifications in this JSON format:

{{
    "interactions": [
        {{
            "id": "interaction_001",
            "name": "Interaction name",
            "type": "click/hover/scroll/gesture/voice",
            "element": "What element triggers this",
            "trigger": "What initiates the interaction",
            "response": "What happens in response",
            "feedback": {{
                "visual": "Visual feedback description",
                "audio": "Sound feedback if applicable",
                "haptic": "Vibration/tactile feedback for mobile"
            }},
            "timing": {{
                "duration": "Animation/transition duration",
                "delay": "Any delay before response",
                "easing": "Animation easing function"
            }},
            "keyboardAlternative": "How to achieve same result with keyboard",
            "screenReaderExperience": "How screen reader users experience this",
            "reducedMotionAlternative": "Static alternative for users who prefer reduced motion",
            "states": ["idle", "loading", "success", "error"],
            "accessibility": {{
                "focusManagement": "How focus is handled",
                "announcements": "What screen reader announces",
                "keyboardShortcuts": "Any relevant shortcuts"
            }}
        }}
    ],
    "microInteractions": [
        {{
            "element": "Button/Link/Input",
            "interaction": "Hover/Focus/Active",
            "effect": "Color change/Scale/Glow",
            "duration": "200ms",
            "purpose": "Why this micro-interaction exists"
        }}
    ],
    "animations": [
        {{
            "name": "Page transition",
            "type": "entrance/exit/transition",
            "elements": ["Which elements animate"],
            "keyframes": "Animation keyframe description",
            "duration": "500ms",
            "respectsReducedMotion": true
        }}
    ],
    "responsiveBehaviors": [
        {{
            "breakpoint": "mobile",
            "interactionChanges": "How interactions change on mobile",
            "touchOptimizations": "Touch-specific improvements"
        }}
    ],
    "errorStates": [
        {{
            "errorType": "Form validation error",
            "visualIndication": "Red border and icon",
            "textualDescription": "Clear error message",
            "recoveryAction": "How user can fix the error",
            "focusManagement": "Where focus goes after error"
        }}
    ],
    "loadingStates": [
        {{
            "context": "When this loading state appears",
            "indicator": "Spinner/skeleton/progress bar",
            "duration": "Expected loading time",
            "accessibleLabel": "Loading announcement for screen readers"
        }}
    ]
}}

Ensure all interactions have keyboard alternatives and support assistive technologies.
Follow platform conventions for interaction patterns.
"""

    return prompt.strip()


def _parse_user_journeys_response(response_content: str) -> Dict[str, Any]:
    """Parse and validate LLM response for user journeys"""
    try:
        import re

        json_match = re.search(r"\{.*\}", response_content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return {
                "journeys": [],
                "crossJourneyPatterns": [],
                "accessibilityPaths": [],
                "parsingNotes": "Response parsing required manual review",
            }
    except Exception as e:
        logger.warning(f"Error parsing user journeys response: {str(e)}")
        return {"journeys": [], "parsingError": str(e)}


def _parse_wireframes_response(response_content: str) -> Dict[str, Any]:
    """Parse and validate LLM response for wireframes"""
    try:
        import re

        json_match = re.search(r"\{.*\}", response_content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return {
                "wireframes": [],
                "designSystem": {},
                "responsiveSpecs": [],
                "accessibilityFeatures": [],
                "parsingNotes": "Response parsing required manual review",
            }
    except Exception as e:
        logger.warning(f"Error parsing wireframes response: {str(e)}")
        return {"wireframes": [], "parsingError": str(e)}


def _parse_interaction_response(response_content: str) -> Dict[str, Any]:
    """Parse and validate LLM response for interactions"""
    try:
        import re

        json_match = re.search(r"\{.*\}", response_content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return {
                "interactions": [],
                "microInteractions": [],
                "animations": [],
                "responsiveBehaviors": [],
                "parsingNotes": "Response parsing required manual review",
            }
    except Exception as e:
        logger.warning(f"Error parsing interaction response: {str(e)}")
        return {"interactions": [], "parsingError": str(e)}


def _assess_journey_quality(journeys: Dict[str, Any], prd_context: Dict[str, Any]) -> Dict[str, Any]:
    """Assess quality of user journey mapping"""
    journey_list = journeys.get("journeys", [])

    # Calculate completeness metrics
    total_journeys = len(journey_list)
    journeys_with_accessibility = len([j for j in journey_list if j.get("accessibilityRequirements")])
    journeys_with_error_recovery = len([j for j in journey_list if j.get("errorRecovery")])
    journeys_with_alternatives = len([j for j in journey_list if j.get("alternativePaths")])

    # Quality scoring
    completeness_score = (
        (journeys_with_accessibility / max(total_journeys, 1)) * 30
        + (journeys_with_error_recovery / max(total_journeys, 1)) * 25
        + (journeys_with_alternatives / max(total_journeys, 1)) * 25
        + (total_journeys > 0) * 20  # Basic existence check
    )

    return {
        "completenessScore": completeness_score,
        "totalJourneys": total_journeys,
        "accessibilityIntegration": (journeys_with_accessibility / max(total_journeys, 1)) * 100,
        "errorRecoveryPlanning": (journeys_with_error_recovery / max(total_journeys, 1)) * 100,
        "alternativePathsPlanning": (journeys_with_alternatives / max(total_journeys, 1)) * 100,
        "recommendations": _generate_journey_quality_recommendations(
            total_journeys, journeys_with_accessibility, journeys_with_error_recovery
        ),
    }


def _calculate_average_steps(journeys: Dict[str, Any]) -> float:
    """Calculate average number of steps across all journeys"""
    journey_list = journeys.get("journeys", [])
    if not journey_list:
        return 0.0

    total_steps = sum(len(j.get("steps", [])) for j in journey_list)
    return total_steps / len(journey_list)


def _validate_design_system_consistency(wireframes: Dict[str, Any]) -> Dict[str, Any]:
    """Validate design system consistency across wireframes"""
    design_system = wireframes.get("designSystem", {})
    wireframe_list = wireframes.get("wireframes", [])

    # Check color consistency
    system_colors = design_system.get("colorPalette", {})
    wireframe_colors = []
    for wf in wireframe_list:
        if wf.get("colorScheme"):
            wireframe_colors.append(wf["colorScheme"])

    # Check typography consistency
    system_fonts = design_system.get("typography", {}).get("fontSizes", [])
    consistent_typography = len(system_fonts) > 0

    # Check spacing consistency
    system_spacing = design_system.get("spacing", {}).get("scale", [])
    consistent_spacing = len(system_spacing) > 0

    consistency_score = (
        (len(wireframe_colors) > 0) * 25  # Colors defined
        + consistent_typography * 25  # Typography system
        + consistent_spacing * 25  # Spacing system
        + (len(design_system.get("components", [])) > 0) * 25  # Components defined
    )

    return {
        "consistencyScore": consistency_score,
        "colorSystemDefined": len(system_colors) > 0,
        "typographySystemDefined": consistent_typography,
        "spacingSystemDefined": consistent_spacing,
        "componentLibraryDefined": len(design_system.get("components", [])) > 0,
        "recommendations": (
            [
                "Ensure all wireframes use design system colors",
                "Validate typography scale consistency",
                "Check spacing scale implementation",
            ]
            if consistency_score < 80
            else ["Design system consistency is good"]
        ),
    }


def _assess_interaction_feasibility(interactions: Dict[str, Any]) -> Dict[str, Any]:
    """Assess feasibility of interaction specifications"""
    interaction_list = interactions.get("interactions", [])

    # Assess complexity
    complex_interactions = len([i for i in interaction_list if i.get("type") in ["gesture", "voice", "multi-touch"]])

    # Check accessibility coverage
    keyboard_accessible = len([i for i in interaction_list if i.get("keyboardAlternative")])

    # Check performance considerations
    animated_interactions = len([i for i in interaction_list if i.get("timing", {}).get("duration")])

    feasibility_score = (
        min(100, max(0, 100 - (complex_interactions * 10))) * 0.3  # Complexity penalty
        + (keyboard_accessible / max(len(interaction_list), 1)) * 100 * 0.4  # Accessibility
        + (animated_interactions > 0) * 30  # Performance considerations
    )

    return {
        "feasibilityScore": feasibility_score,
        "complexityLevel": "High" if complex_interactions > 3 else "Medium" if complex_interactions > 0 else "Low",
        "accessibilityCompliance": (keyboard_accessible / max(len(interaction_list), 1)) * 100,
        "performanceConsiderations": animated_interactions > 0,
        "implementationRisk": "High" if feasibility_score < 60 else "Medium" if feasibility_score < 80 else "Low",
        "recommendations": [
            (
                f"Simplify {complex_interactions} complex interactions"
                if complex_interactions > 2
                else "Interaction complexity is manageable"
            ),
            (
                f"Add keyboard alternatives for {len(interaction_list) - keyboard_accessible} interactions"
                if keyboard_accessible < len(interaction_list)
                else "Keyboard accessibility is complete"
            ),
        ],
    }


def _generate_actionable_accessibility_recommendations(assessment: Any) -> List[str]:
    """Generate actionable accessibility recommendations"""
    recommendations = []

    failed_checks = [c for c in assessment.checks if c.status.value == "fail"]
    high_priority = [c for c in failed_checks if c.priority <= 2]

    for check in high_priority[:5]:  # Top 5 priorities
        recommendations.append(f"🔴 Critical: {check.recommendation}")

    medium_priority = [c for c in failed_checks if c.priority == 3]
    for check in medium_priority[:3]:  # Top 3 medium priorities
        recommendations.append(f"🟡 Important: {check.recommendation}")

    if assessment.overall_score < 90:
        recommendations.insert(
            0, f"📊 Overall accessibility score is {assessment.overall_score:.1f}%. Target is 90%+ for WCAG 2.1 AA compliance."
        )

    return recommendations


def _generate_ux_document_structure(components: Dict[str, Any], format: str, include_accessibility: bool) -> Dict[str, Any]:
    """Generate UX document structure"""
    sections = [
        {"name": "Executive Summary", "content": components.get("executiveSummary", "")},
        {"name": "User Journey Maps", "content": components.get("userJourneys", [])},
        {"name": "Wireframes & Layout", "content": components.get("wireframes", [])},
        {"name": "Design System", "content": components.get("designSystem", {})},
        {"name": "Interaction Specifications", "content": components.get("interactions", [])},
        {"name": "Responsive Design", "content": components.get("responsiveSpecs", [])},
    ]

    if include_accessibility:
        sections.append({"name": "Accessibility Compliance Report", "content": components.get("accessibilityReport", {})})

    return {
        "title": components.get("title", "UX Requirements Document"),
        "version": "1.0",
        "sections": sections,
        "wireframes": components.get("wireframes", []),
        "interactions": components.get("interactions", []),
        "accessibilityReport": components.get("accessibilityReport", {}) if include_accessibility else {},
        "format": format,
    }


def _validate_ux_document_completeness(document: Dict[str, Any]) -> Dict[str, Any]:
    """Validate UX document completeness"""
    required_sections = ["User Journey Maps", "Wireframes & Layout", "Design System", "Interaction Specifications"]
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
        "hasAccessibilityReport": "Accessibility Compliance Report" in section_names,
    }


def _generate_ux_export_data(document: Dict[str, Any], format: str) -> Dict[str, Any]:
    """Generate export data based on format"""
    if format == "markdown":
        return {"content": _convert_ux_to_markdown(document), "mimeType": "text/markdown"}
    elif format == "json":
        return {"content": json.dumps(document, indent=2), "mimeType": "application/json"}
    else:
        return {"content": str(document), "mimeType": "text/plain"}


def _convert_ux_to_markdown(document: Dict[str, Any]) -> str:
    """Convert UX document to Markdown format"""
    markdown = f"# {document.get('title', 'UX Requirements')}\n\n"

    for section in document.get("sections", []):
        markdown += f"## {section.get('name', '')}\n\n"
        content = section.get("content", "")

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    markdown += f"### {item.get('title', 'Item')}\n"
                    markdown += f"{item.get('description', str(item))}\n\n"
                else:
                    markdown += f"- {item}\n"
        else:
            markdown += f"{content}\n"
        markdown += "\n"

    return markdown


def _generate_journey_quality_recommendations(total: int, accessibility: int, error_recovery: int) -> List[str]:
    """Generate journey quality recommendations"""
    recommendations = []

    if total == 0:
        recommendations.append("Create at least one primary user journey")
    elif total < 3:
        recommendations.append("Consider mapping additional user journeys for completeness")

    if accessibility < total:
        recommendations.append(f"Add accessibility requirements to {total - accessibility} journeys")

    if error_recovery < total:
        recommendations.append(f"Define error recovery paths for {total - error_recovery} journeys")

    return recommendations if recommendations else ["Journey mapping quality is excellent"]


def _predict_technical_quality_impact(
    quality_result: Any, accessibility_assessment: Any, consistency_validation: Any
) -> Dict[str, Any]:
    """Predict how UX quality will impact technical analysis stage"""
    base_prediction = 85.0  # Base expectation for technical stage

    # Quality foundation impact
    quality_bonus = (quality_result.overall_score - 82) * 0.3

    # Accessibility impact (critical for technical feasibility)
    accessibility_bonus = (accessibility_assessment.overall_score - 90) * 0.2

    # Consistency impact
    consistency_bonus = consistency_validation.consistency_score * 3

    # UX-specific bonuses
    wireframe_quality = quality_result.dimension_scores.get("wireframe_quality", 82)
    interaction_feasibility = quality_result.dimension_scores.get("implementation_feasibility", 82)

    if wireframe_quality > 90:
        quality_bonus += 2
    if interaction_feasibility > 85:
        quality_bonus += 3

    predicted_tech_quality = min(95, base_prediction + quality_bonus + accessibility_bonus + consistency_bonus)

    return {
        "predictedTechnicalQuality": predicted_tech_quality,
        "qualityImpact": quality_bonus,
        "accessibilityImpact": accessibility_bonus,
        "consistencyImpact": consistency_bonus,
        "strongFoundations": wireframe_quality > 85
        and interaction_feasibility > 80
        and accessibility_assessment.overall_score >= 90,
        "recommendations": [
            "Use detailed wireframes for accurate technical estimations",
            "Leverage interaction specifications for implementation planning",
            "Build on accessibility compliance for robust technical architecture",
            "Utilize design system for consistent technical implementation",
        ],
    }
