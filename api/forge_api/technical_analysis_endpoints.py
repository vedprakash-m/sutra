"""
Technical Analysis API Endpoints for Forge Module.
Implements multi-LLM consensus scoring and comprehensive technical architecture evaluation
with 85% quality threshold and detailed feasibility assessment.
"""

import json
import logging
import os

# Import shared modules
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import azure.functions as func
from azure.cosmos import CosmosClient

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))

from cost_tracking import CostTracker, calculate_operation_cost
from llm_client import LLMClient
from multi_llm_consensus import MultiLLMConsensusEngine, evaluate_technical_architecture
from quality_engine import QualityEngine
from quality_validators import CrossStageQualityValidator

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main entry point for technical analysis API"""
    try:
        method = req.method
        route = req.route_params.get("route", "")

        if method == "POST" and route == "evaluate-architecture":
            return evaluate_architecture_endpoint(req)
        elif method == "POST" and route == "generate-technical-specs":
            return generate_technical_specs_endpoint(req)
        elif method == "POST" and route == "assess-feasibility":
            return assess_feasibility_endpoint(req)
        elif method == "POST" and route == "analyze-risks":
            return analyze_risks_endpoint(req)
        elif method == "GET" and route == "consensus-models":
            return get_consensus_models_endpoint(req)
        elif method == "POST" and route == "implementation-roadmap":
            return generate_implementation_roadmap_endpoint(req)
        elif method == "POST" and route == "export-technical-analysis":
            return export_technical_analysis_endpoint(req)
        elif method == "GET" and route == "quality-check":
            return quality_check_endpoint(req)
        else:
            return func.HttpResponse(json.dumps({"error": "Route not found"}), status_code=404, mimetype="application/json")

    except Exception as e:
        logger.error(f"Error in technical analysis API: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def evaluate_architecture_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint: POST /api/forge/technical-analysis/evaluate-architecture

    Performs multi-LLM technical architecture evaluation with consensus scoring.
    Implements the core of Task 2.6 with 85% quality threshold.
    """
    try:
        request_data = req.get_json()
        user_id = request_data.get("user_id")
        session_id = request_data.get("session_id")
        project_context = request_data.get("project_context", {})
        selected_models = request_data.get("selected_models", ["gpt-4", "claude-3-5-sonnet", "gemini-1.5-pro"])
        evaluation_params = request_data.get("evaluation_params", {})

        if not user_id or not session_id:
            return func.HttpResponse(
                json.dumps({"error": "Missing user_id or session_id"}), status_code=400, mimetype="application/json"
            )

        # Initialize services
        llm_client = LLMClient()
        cost_tracker = CostTracker()
        quality_engine = QualityEngine()
        cross_stage_validator = CrossStageQualityValidator()
        consensus_engine = MultiLLMConsensusEngine()

        # Validate project context completeness
        context_validation = cross_stage_validator.validate_stage_context("technical_analysis", project_context)

        if not context_validation["is_valid"]:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "Incomplete project context",
                        "validation_errors": context_validation["errors"],
                        "required_stages": context_validation["required_stages"],
                    }
                ),
                status_code=400,
                mimetype="application/json",
            )

        # Track operation start
        operation_id = cost_tracker.start_operation(
            user_id=user_id,
            operation_type="technical_architecture_evaluation",
            metadata={"session_id": session_id, "selected_models": selected_models, "evaluation_params": evaluation_params},
        )

        # Perform multi-LLM consensus evaluation
        import asyncio

        async def run_evaluation():
            return await consensus_engine.evaluate_technical_architecture(
                project_context=project_context, selected_models=selected_models, llm_client=llm_client
            )

        technical_evaluation = asyncio.run(run_evaluation())

        # Calculate operation cost
        total_cost = technical_evaluation.consensus_metadata.total_cost
        cost_tracker.update_operation_cost(operation_id, total_cost)

        # Validate quality score meets 85% threshold
        quality_threshold = 85.0
        quality_score = technical_evaluation.quality_score

        if quality_score < quality_threshold:
            logger.warning(f"Technical evaluation quality score {quality_score:.1f}% below threshold {quality_threshold}%")

            # Attempt quality improvement with additional model
            if len(selected_models) < 4:
                additional_models = ["gpt-4o"] if "gpt-4o" not in selected_models else ["claude-3-haiku"]

                enhanced_evaluation = asyncio.run(
                    consensus_engine.evaluate_technical_architecture(
                        project_context=project_context,
                        selected_models=selected_models + additional_models[:1],
                        llm_client=llm_client,
                    )
                )

                if enhanced_evaluation.quality_score > technical_evaluation.quality_score:
                    technical_evaluation = enhanced_evaluation
                    total_cost += enhanced_evaluation.consensus_metadata.total_cost
                    cost_tracker.update_operation_cost(operation_id, total_cost)

        # Perform cross-stage quality validation
        quality_assessment = quality_engine.assess_quality(
            content=technical_evaluation.architecture_recommendation,
            quality_type="technical_analysis",
            context={
                "consensus_level": technical_evaluation.consensus_metadata.consensus_level.value,
                "agreement_score": technical_evaluation.consensus_metadata.agreement_score,
                "quality_score": technical_evaluation.quality_score,
                "models_used": len(selected_models),
            },
        )

        # Store results in Cosmos DB
        cosmos_client = CosmosClient.from_connection_string(os.environ["COSMOS_CONNECTION_STRING"])
        database = cosmos_client.get_database_client("SutraDB")
        container = database.get_container_client("ForgeResults")

        result_document = {
            "id": f"{session_id}_technical_analysis_{operation_id}",
            "user_id": user_id,
            "session_id": session_id,
            "stage": "technical_analysis",
            "operation_id": operation_id,
            "architecture_recommendation": technical_evaluation.architecture_recommendation,
            "technology_stack": technical_evaluation.technology_stack,
            "feasibility_assessment": technical_evaluation.feasibility_assessment,
            "risk_analysis": technical_evaluation.risk_analysis,
            "implementation_roadmap": technical_evaluation.implementation_roadmap,
            "consensus_metadata": {
                "consensus_level": technical_evaluation.consensus_metadata.consensus_level.value,
                "agreement_score": technical_evaluation.consensus_metadata.agreement_score,
                "confidence_level": technical_evaluation.consensus_metadata.confidence_level,
                "total_cost": technical_evaluation.consensus_metadata.total_cost,
                "models_used": selected_models,
                "conflict_areas": technical_evaluation.consensus_metadata.conflict_areas,
            },
            "quality_assessment": {
                "overall_score": technical_evaluation.quality_score,
                "quality_engine_score": quality_assessment.overall_score,
                "meets_threshold": technical_evaluation.quality_score >= quality_threshold,
                "threshold": quality_threshold,
                "individual_metrics": quality_assessment.individual_scores,
            },
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "processing_time": sum(
                    r.processing_time for r in technical_evaluation.consensus_metadata.individual_responses
                ),
                "total_tokens": sum(r.tokens_used for r in technical_evaluation.consensus_metadata.individual_responses),
                "context_validation": context_validation,
            },
        }

        container.create_item(result_document)

        # Complete operation tracking
        cost_tracker.complete_operation(operation_id)

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "operation_id": operation_id,
                    "architecture_evaluation": {
                        "architecture_recommendation": technical_evaluation.architecture_recommendation,
                        "technology_stack": technical_evaluation.technology_stack,
                        "feasibility_assessment": technical_evaluation.feasibility_assessment,
                        "risk_analysis": technical_evaluation.risk_analysis,
                        "implementation_roadmap": technical_evaluation.implementation_roadmap,
                    },
                    "consensus_analysis": {
                        "consensus_level": technical_evaluation.consensus_metadata.consensus_level.value,
                        "agreement_score": technical_evaluation.consensus_metadata.agreement_score,
                        "confidence_level": technical_evaluation.consensus_metadata.confidence_level,
                        "conflict_areas": technical_evaluation.consensus_metadata.conflict_areas,
                        "models_used": selected_models,
                    },
                    "quality_metrics": {
                        "overall_score": technical_evaluation.quality_score,
                        "meets_threshold": technical_evaluation.quality_score >= quality_threshold,
                        "threshold": quality_threshold,
                        "quality_engine_assessment": quality_assessment.overall_score,
                    },
                    "cost_summary": {
                        "total_cost": total_cost,
                        "cost_per_model": [
                            {"model": r.model, "cost": r.cost}
                            for r in technical_evaluation.consensus_metadata.individual_responses
                        ],
                    },
                },
                default=str,
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error in architecture evaluation: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def generate_technical_specs_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint: POST /api/forge/technical-analysis/generate-technical-specs

    Generates comprehensive technical specifications from architecture evaluation
    """
    try:
        request_data = req.get_json()
        user_id = request_data.get("user_id")
        session_id = request_data.get("session_id")
        architecture_evaluation = request_data.get("architecture_evaluation", {})
        spec_requirements = request_data.get("spec_requirements", {})

        if not user_id or not session_id or not architecture_evaluation:
            return func.HttpResponse(
                json.dumps({"error": "Missing required parameters"}), status_code=400, mimetype="application/json"
            )

        # Initialize services
        llm_client = LLMClient()
        cost_tracker = CostTracker()

        # Track operation
        operation_id = cost_tracker.start_operation(
            user_id=user_id, operation_type="technical_specs_generation", metadata={"session_id": session_id}
        )

        # Generate detailed technical specifications
        specs_prompt = create_technical_specs_prompt(architecture_evaluation, spec_requirements)

        response = llm_client.execute_prompt(prompt=specs_prompt, model="gpt-4", temperature=0.1, max_tokens=6000)

        # Parse and structure technical specifications
        import re

        json_match = re.search(r"\{.*\}", response.get("content", ""), re.DOTALL)
        if json_match:
            technical_specs = json.loads(json_match.group())
        else:
            technical_specs = {"error": "Failed to parse technical specifications"}

        # Calculate cost and complete operation
        total_cost = response.get("cost", 0.0)
        cost_tracker.update_operation_cost(operation_id, total_cost)
        cost_tracker.complete_operation(operation_id)

        # Store in Cosmos DB
        cosmos_client = CosmosClient.from_connection_string(os.environ["COSMOS_CONNECTION_STRING"])
        database = cosmos_client.get_database_client("SutraDB")
        container = database.get_container_client("ForgeResults")

        spec_document = {
            "id": f"{session_id}_technical_specs_{operation_id}",
            "user_id": user_id,
            "session_id": session_id,
            "stage": "technical_specifications",
            "operation_id": operation_id,
            "technical_specifications": technical_specs,
            "architecture_evaluation_reference": architecture_evaluation,
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "cost": total_cost,
                "tokens_used": response.get("usage", {}).get("total_tokens", 0),
            },
        }

        container.create_item(spec_document)

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "operation_id": operation_id,
                    "technical_specifications": technical_specs,
                    "cost": total_cost,
                },
                default=str,
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error generating technical specs: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def assess_feasibility_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint: POST /api/forge/technical-analysis/assess-feasibility

    Performs detailed feasibility assessment with resource estimation
    """
    try:
        request_data = req.get_json()
        user_id = request_data.get("user_id")
        project_requirements = request_data.get("project_requirements", {})
        constraints = request_data.get("constraints", {})

        if not user_id or not project_requirements:
            return func.HttpResponse(
                json.dumps({"error": "Missing project requirements"}), status_code=400, mimetype="application/json"
            )

        # Initialize services
        llm_client = LLMClient()
        cost_tracker = CostTracker()

        # Track operation
        operation_id = cost_tracker.start_operation(
            user_id=user_id, operation_type="feasibility_assessment", metadata={"constraints": constraints}
        )

        # Generate feasibility assessment prompt
        feasibility_prompt = create_feasibility_assessment_prompt(project_requirements, constraints)

        response = llm_client.execute_prompt(prompt=feasibility_prompt, model="gpt-4", temperature=0.2, max_tokens=4000)

        # Parse feasibility assessment
        import re

        json_match = re.search(r"\{.*\}", response.get("content", ""), re.DOTALL)
        if json_match:
            feasibility_assessment = json.loads(json_match.group())
        else:
            feasibility_assessment = {"error": "Failed to parse feasibility assessment"}

        # Calculate cost and complete operation
        total_cost = response.get("cost", 0.0)
        cost_tracker.update_operation_cost(operation_id, total_cost)
        cost_tracker.complete_operation(operation_id)

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "operation_id": operation_id,
                    "feasibility_assessment": feasibility_assessment,
                    "cost": total_cost,
                },
                default=str,
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error in feasibility assessment: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def analyze_risks_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint: POST /api/forge/technical-analysis/analyze-risks

    Performs comprehensive risk analysis with mitigation strategies
    """
    try:
        request_data = req.get_json()
        user_id = request_data.get("user_id")
        technical_context = request_data.get("technical_context", {})
        risk_categories = request_data.get("risk_categories", ["technical", "security", "scalability", "operational"])

        if not user_id or not technical_context:
            return func.HttpResponse(
                json.dumps({"error": "Missing technical context"}), status_code=400, mimetype="application/json"
            )

        # Initialize services
        llm_client = LLMClient()
        cost_tracker = CostTracker()

        # Track operation
        operation_id = cost_tracker.start_operation(
            user_id=user_id, operation_type="risk_analysis", metadata={"risk_categories": risk_categories}
        )

        # Generate risk analysis prompt
        risk_prompt = create_risk_analysis_prompt(technical_context, risk_categories)

        response = llm_client.execute_prompt(
            prompt=risk_prompt,
            model="claude-3-5-sonnet",  # Claude often excels at risk analysis
            temperature=0.2,
            max_tokens=5000,
        )

        # Parse risk analysis
        import re

        json_match = re.search(r"\{.*\}", response.get("content", ""), re.DOTALL)
        if json_match:
            risk_analysis = json.loads(json_match.group())
        else:
            risk_analysis = {"error": "Failed to parse risk analysis"}

        # Calculate cost and complete operation
        total_cost = response.get("cost", 0.0)
        cost_tracker.update_operation_cost(operation_id, total_cost)
        cost_tracker.complete_operation(operation_id)

        return func.HttpResponse(
            json.dumps(
                {"success": True, "operation_id": operation_id, "risk_analysis": risk_analysis, "cost": total_cost},
                default=str,
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error in risk analysis: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def get_consensus_models_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint: GET /api/forge/technical-analysis/consensus-models

    Returns available LLM models for consensus evaluation with their capabilities
    """
    try:
        available_models = {
            "models": [
                {
                    "id": "gpt-4",
                    "name": "GPT-4",
                    "provider": "OpenAI",
                    "strengths": ["General architecture", "Problem solving", "Code generation"],
                    "cost_per_1k_tokens": 0.03,
                    "recommended_for": ["Architecture design", "System integration"],
                    "weight": 1.0,
                },
                {
                    "id": "claude-3-5-sonnet",
                    "name": "Claude 3.5 Sonnet",
                    "provider": "Anthropic",
                    "strengths": ["Risk analysis", "Technical writing", "Security assessment"],
                    "cost_per_1k_tokens": 0.015,
                    "recommended_for": ["Risk assessment", "Documentation", "Security review"],
                    "weight": 1.0,
                },
                {
                    "id": "gemini-1.5-pro",
                    "name": "Gemini 1.5 Pro",
                    "provider": "Google",
                    "strengths": ["Scalability analysis", "Performance optimization", "Multi-modal reasoning"],
                    "cost_per_1k_tokens": 0.0125,
                    "recommended_for": ["Scalability planning", "Performance analysis"],
                    "weight": 0.9,
                },
                {
                    "id": "gpt-4o",
                    "name": "GPT-4o",
                    "provider": "OpenAI",
                    "strengths": ["Fast reasoning", "Cost efficiency", "Technical accuracy"],
                    "cost_per_1k_tokens": 0.025,
                    "recommended_for": ["Quick evaluations", "Cost-conscious analysis"],
                    "weight": 0.95,
                },
                {
                    "id": "claude-3-haiku",
                    "name": "Claude 3 Haiku",
                    "provider": "Anthropic",
                    "strengths": ["Speed", "Concise analysis", "Cost efficiency"],
                    "cost_per_1k_tokens": 0.008,
                    "recommended_for": ["Quick assessments", "Budget-conscious projects"],
                    "weight": 0.8,
                },
            ],
            "recommended_combinations": [
                {
                    "name": "Balanced Consensus",
                    "models": ["gpt-4", "claude-3-5-sonnet", "gemini-1.5-pro"],
                    "use_case": "Comprehensive technical evaluation with strong consensus",
                    "estimated_cost_range": "$0.15 - $0.25 per evaluation",
                },
                {
                    "name": "Cost-Effective Analysis",
                    "models": ["gpt-4o", "claude-3-haiku", "gemini-1.5-pro"],
                    "use_case": "Budget-conscious evaluation with good coverage",
                    "estimated_cost_range": "$0.08 - $0.15 per evaluation",
                },
                {
                    "name": "Premium Evaluation",
                    "models": ["gpt-4", "claude-3-5-sonnet", "gemini-1.5-pro", "gpt-4o"],
                    "use_case": "Maximum consensus confidence for critical projects",
                    "estimated_cost_range": "$0.20 - $0.35 per evaluation",
                },
            ],
            "consensus_thresholds": {
                "strong_agreement": "80%+ model agreement",
                "moderate_agreement": "60-79% model agreement",
                "weak_agreement": "40-59% model agreement",
                "no_consensus": "<40% model agreement",
            },
        }

        return func.HttpResponse(json.dumps(available_models, default=str), status_code=200, mimetype="application/json")

    except Exception as e:
        logger.error(f"Error getting consensus models: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def generate_implementation_roadmap_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint: POST /api/forge/technical-analysis/implementation-roadmap

    Generates detailed implementation roadmap based on technical analysis
    """
    try:
        request_data = req.get_json()
        user_id = request_data.get("user_id")
        technical_analysis = request_data.get("technical_analysis", {})
        project_constraints = request_data.get("project_constraints", {})

        if not user_id or not technical_analysis:
            return func.HttpResponse(
                json.dumps({"error": "Missing technical analysis data"}), status_code=400, mimetype="application/json"
            )

        # Initialize services
        llm_client = LLMClient()
        cost_tracker = CostTracker()

        # Track operation
        operation_id = cost_tracker.start_operation(
            user_id=user_id, operation_type="implementation_roadmap", metadata={"constraints": project_constraints}
        )

        # Generate roadmap
        roadmap_prompt = create_implementation_roadmap_prompt(technical_analysis, project_constraints)

        response = llm_client.execute_prompt(prompt=roadmap_prompt, model="gpt-4", temperature=0.2, max_tokens=5000)

        # Parse implementation roadmap
        import re

        json_match = re.search(r"\{.*\}", response.get("content", ""), re.DOTALL)
        if json_match:
            roadmap = json.loads(json_match.group())
        else:
            roadmap = {"error": "Failed to parse implementation roadmap"}

        # Calculate cost and complete operation
        total_cost = response.get("cost", 0.0)
        cost_tracker.update_operation_cost(operation_id, total_cost)
        cost_tracker.complete_operation(operation_id)

        return func.HttpResponse(
            json.dumps(
                {"success": True, "operation_id": operation_id, "implementation_roadmap": roadmap, "cost": total_cost},
                default=str,
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error generating implementation roadmap: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def export_technical_analysis_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint: POST /api/forge/technical-analysis/export-technical-analysis

    Exports complete technical analysis as structured document
    """
    try:
        request_data = req.get_json()
        user_id = request_data.get("user_id")
        session_id = request_data.get("session_id")
        export_format = request_data.get("export_format", "markdown")
        include_sections = request_data.get(
            "include_sections", ["architecture", "technology_stack", "feasibility", "risks", "roadmap"]
        )

        if not user_id or not session_id:
            return func.HttpResponse(
                json.dumps({"error": "Missing user_id or session_id"}), status_code=400, mimetype="application/json"
            )

        # Retrieve technical analysis data from Cosmos DB
        cosmos_client = CosmosClient.from_connection_string(os.environ["COSMOS_CONNECTION_STRING"])
        database = cosmos_client.get_database_client("SutraDB")
        container = database.get_container_client("ForgeResults")

        query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.session_id = @session_id AND c.stage = 'technical_analysis'"
        items = list(
            container.query_items(
                query=query, parameters=[{"name": "@user_id", "value": user_id}, {"name": "@session_id", "value": session_id}]
            )
        )

        if not items:
            return func.HttpResponse(
                json.dumps({"error": "No technical analysis found for session"}), status_code=404, mimetype="application/json"
            )

        technical_data = items[0]  # Get most recent

        # Generate export document
        if export_format == "markdown":
            exported_content = generate_markdown_export(technical_data, include_sections)
        elif export_format == "json":
            exported_content = generate_json_export(technical_data, include_sections)
        else:
            return func.HttpResponse(
                json.dumps({"error": f"Unsupported export format: {export_format}"}),
                status_code=400,
                mimetype="application/json",
            )

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "exported_content": exported_content,
                    "export_format": export_format,
                    "sections_included": include_sections,
                    "export_timestamp": datetime.now(timezone.utc).isoformat(),
                },
                default=str,
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error exporting technical analysis: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def quality_check_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint: GET /api/forge/technical-analysis/quality-check

    Performs quality check on technical analysis stage
    """
    try:
        user_id = req.params.get("user_id")
        session_id = req.params.get("session_id")

        if not user_id or not session_id:
            return func.HttpResponse(
                json.dumps({"error": "Missing user_id or session_id parameters"}), status_code=400, mimetype="application/json"
            )

        # Initialize quality validator
        cross_stage_validator = CrossStageQualityValidator()

        # Retrieve session data
        cosmos_client = CosmosClient.from_connection_string(os.environ["COSMOS_CONNECTION_STRING"])
        database = cosmos_client.get_database_client("SutraDB")
        container = database.get_container_client("ForgeResults")

        query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.session_id = @session_id ORDER BY c.metadata.created_at DESC"
        items = list(
            container.query_items(
                query=query, parameters=[{"name": "@user_id", "value": user_id}, {"name": "@session_id", "value": session_id}]
            )
        )

        if not items:
            return func.HttpResponse(
                json.dumps({"error": "No session data found"}), status_code=404, mimetype="application/json"
            )

        # Perform quality check
        technical_items = [item for item in items if item.get("stage") == "technical_analysis"]

        if not technical_items:
            quality_check = {
                "stage_completed": False,
                "quality_score": 0.0,
                "issues": ["Technical analysis stage not completed"],
                "recommendations": ["Complete technical architecture evaluation"],
                "meets_threshold": False,
            }
        else:
            latest_technical = technical_items[0]
            quality_assessment = latest_technical.get("quality_assessment", {})

            quality_check = {
                "stage_completed": True,
                "quality_score": quality_assessment.get("overall_score", 0.0),
                "quality_engine_score": quality_assessment.get("quality_engine_score", 0.0),
                "meets_threshold": quality_assessment.get("meets_threshold", False),
                "threshold": quality_assessment.get("threshold", 85.0),
                "consensus_level": latest_technical.get("consensus_metadata", {}).get("consensus_level", "unknown"),
                "models_used": latest_technical.get("consensus_metadata", {}).get("models_used", []),
                "conflict_areas": latest_technical.get("consensus_metadata", {}).get("conflict_areas", []),
                "issues": [],
                "recommendations": [],
            }

            # Add specific recommendations based on quality metrics
            if not quality_check["meets_threshold"]:
                quality_check["issues"].append(f"Quality score {quality_check['quality_score']:.1f}% below threshold")
                quality_check["recommendations"].append("Consider re-running with additional LLM models")

            if quality_check["conflict_areas"]:
                quality_check["issues"].append(f"Consensus conflicts in: {', '.join(quality_check['conflict_areas'])}")
                quality_check["recommendations"].append("Review conflict areas and consider expert consultation")

        return func.HttpResponse(json.dumps(quality_check, default=str), status_code=200, mimetype="application/json")

    except Exception as e:
        logger.error(f"Error in quality check: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


# Helper functions for prompt generation


def create_technical_specs_prompt(architecture_evaluation: Dict[str, Any], spec_requirements: Dict[str, Any]) -> str:
    """Create prompt for generating detailed technical specifications"""

    return f"""
Generate comprehensive technical specifications based on the architecture evaluation.

ARCHITECTURE EVALUATION:
{json.dumps(architecture_evaluation, indent=2)}

SPECIFICATION REQUIREMENTS:
{json.dumps(spec_requirements, indent=2)}

Generate detailed technical specifications in this JSON format:

{{
    "system_architecture": {{
        "overview": "High-level architecture description",
        "components": [
            {{
                "name": "Component Name",
                "type": "Frontend/Backend/Database/Service",
                "description": "Component description",
                "responsibilities": ["List of responsibilities"],
                "interfaces": ["API endpoints or connections"],
                "technologies": ["Specific technologies used"]
            }}
        ],
        "data_flow": "Description of data flow between components",
        "security_model": "Security architecture and considerations"
    }},
    "technical_requirements": {{
        "performance_requirements": {{
            "response_time": "Target response times",
            "throughput": "Expected throughput",
            "scalability": "Scaling requirements",
            "availability": "Uptime requirements"
        }},
        "security_requirements": {{
            "authentication": "Authentication approach",
            "authorization": "Authorization model",
            "data_protection": "Data protection measures",
            "compliance": "Compliance requirements"
        }},
        "integration_requirements": {{
            "external_apis": ["List of external APIs"],
            "third_party_services": ["Third-party services"],
            "data_sources": ["Data sources and formats"]
        }}
    }},
    "implementation_details": {{
        "development_environment": {{
            "languages": ["Programming languages"],
            "frameworks": ["Frameworks and libraries"],
            "tools": ["Development tools"],
            "version_control": "Version control strategy"
        }},
        "deployment_architecture": {{
            "infrastructure": "Infrastructure setup",
            "deployment_strategy": "Deployment approach",
            "monitoring": "Monitoring and logging",
            "ci_cd": "CI/CD pipeline"
        }}
    }}
}}
"""


def create_feasibility_assessment_prompt(project_requirements: Dict[str, Any], constraints: Dict[str, Any]) -> str:
    """Create prompt for feasibility assessment"""

    return f"""
Perform comprehensive feasibility assessment for the project.

PROJECT REQUIREMENTS:
{json.dumps(project_requirements, indent=2)}

CONSTRAINTS:
{json.dumps(constraints, indent=2)}

Provide feasibility assessment in this JSON format:

{{
    "overall_feasibility": {{
        "score": 8.5,
        "assessment": "Highly feasible with moderate complexity",
        "key_factors": ["Factors affecting feasibility"]
    }},
    "resource_estimation": {{
        "timeline": {{
            "total_weeks": 16,
            "phases": [
                {{
                    "phase": "Planning & Setup",
                    "duration_weeks": 2,
                    "deliverables": ["Deliverable list"]
                }}
            ]
        }},
        "team_requirements": {{
            "size": 4,
            "roles": ["Required roles"],
            "skill_levels": ["Junior/Mid/Senior requirements"]
        }},
        "budget_estimation": {{
            "development_cost": "Estimated development cost",
            "infrastructure_cost": "Monthly infrastructure cost",
            "third_party_costs": "Third-party service costs"
        }}
    }},
    "risk_factors": {{
        "technical_risks": ["List of technical risks"],
        "resource_risks": ["Resource-related risks"],
        "timeline_risks": ["Schedule risks"],
        "mitigation_strategies": ["Risk mitigation approaches"]
    }},
    "success_criteria": {{
        "technical_criteria": ["Technical success measures"],
        "business_criteria": ["Business success measures"],
        "quality_criteria": ["Quality benchmarks"]
    }}
}}
"""


def create_risk_analysis_prompt(technical_context: Dict[str, Any], risk_categories: List[str]) -> str:
    """Create prompt for comprehensive risk analysis"""

    return f"""
Perform comprehensive risk analysis for the technical implementation.

TECHNICAL CONTEXT:
{json.dumps(technical_context, indent=2)}

RISK CATEGORIES TO ANALYZE:
{risk_categories}

Provide detailed risk analysis in this JSON format:

{{
    "overall_risk_assessment": {{
        "risk_level": 6.5,
        "risk_profile": "Medium risk with manageable challenges",
        "confidence": 0.85
    }},
    "category_analysis": {{
        "technical": {{
            "severity": 7.0,
            "probability": 0.6,
            "impact": "High impact if realized",
            "specific_risks": ["List of technical risks"],
            "mitigation_strategies": ["How to mitigate"],
            "monitoring_indicators": ["What to monitor"]
        }}
    }},
    "risk_prioritization": [
        {{
            "risk": "Specific risk description",
            "category": "technical/security/scalability/operational",
            "severity": 8.0,
            "probability": 0.7,
            "risk_score": 5.6,
            "immediate_actions": ["Actions to take now"],
            "contingency_plans": ["Backup plans"]
        }}
    ],
    "risk_monitoring": {{
        "key_metrics": ["Metrics to track"],
        "review_frequency": "How often to review",
        "escalation_triggers": ["When to escalate"],
        "responsible_parties": ["Who monitors what"]
    }}
}}
"""


def create_implementation_roadmap_prompt(technical_analysis: Dict[str, Any], project_constraints: Dict[str, Any]) -> str:
    """Create prompt for implementation roadmap generation"""

    return f"""
Generate detailed implementation roadmap based on technical analysis.

TECHNICAL ANALYSIS:
{json.dumps(technical_analysis, indent=2)}

PROJECT CONSTRAINTS:
{json.dumps(project_constraints, indent=2)}

Generate implementation roadmap in this JSON format:

{{
    "roadmap_overview": {{
        "total_duration": "16 weeks",
        "team_size": 4,
        "methodology": "Agile/Scrum",
        "key_milestones": ["Major milestones"]
    }},
    "phases": [
        {{
            "phase_number": 1,
            "name": "Foundation Setup",
            "duration_weeks": 2,
            "objectives": ["Phase objectives"],
            "deliverables": ["What gets delivered"],
            "team_focus": ["Who does what"],
            "success_criteria": ["How to measure success"],
            "risks": ["Phase-specific risks"],
            "dependencies": ["What this depends on"]
        }}
    ],
    "resource_planning": {{
        "team_composition": {{
            "roles": ["Frontend Dev", "Backend Dev", "DevOps"],
            "allocation": ["How time is allocated"],
            "skill_requirements": ["Required skills"]
        }},
        "infrastructure_needs": {{
            "development": "Dev environment requirements",
            "staging": "Staging environment needs",
            "production": "Production setup"
        }},
        "tools_and_licenses": ["Required tools and licenses"]
    }},
    "quality_assurance": {{
        "testing_strategy": "Overall testing approach",
        "quality_gates": ["Quality checkpoints"],
        "review_processes": ["Code review, design review, etc."],
        "documentation_requirements": ["Required documentation"]
    }},
    "risk_management": {{
        "critical_path": ["Critical path items"],
        "buffer_time": "Built-in buffer time",
        "contingency_plans": ["Backup plans"],
        "regular_checkpoints": ["Review schedule"]
    }}
}}
"""


def generate_markdown_export(technical_data: Dict[str, Any], include_sections: List[str]) -> str:
    """Generate markdown export of technical analysis"""

    markdown_content = "# Technical Analysis Report\n\n"
    markdown_content += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    markdown_content += f"**Session ID:** {technical_data.get('session_id', 'Unknown')}\n\n"

    if "architecture" in include_sections:
        arch = technical_data.get("architecture_recommendation", {})
        markdown_content += "## Architecture Recommendation\n\n"
        markdown_content += f"**Pattern:** {arch.get('pattern', 'Not specified')}\n\n"
        markdown_content += f"**Rationale:** {arch.get('rationale', 'Not provided')}\n\n"

    if "technology_stack" in include_sections:
        stack = technical_data.get("technology_stack", {})
        markdown_content += "## Technology Stack\n\n"
        for category, tech in stack.items():
            if isinstance(tech, dict):
                markdown_content += f"### {category.title()}\n"
                markdown_content += f"- **Technology:** {tech.get('name', 'Not specified')}\n"
                markdown_content += f"- **Score:** {tech.get('weighted_score', 0):.2f}\n"
                if tech.get("reasons"):
                    markdown_content += f"- **Reasons:** {', '.join(tech['reasons'])}\n"
                markdown_content += "\n"

    if "feasibility" in include_sections:
        feasibility = technical_data.get("feasibility_assessment", {})
        markdown_content += "## Feasibility Assessment\n\n"
        markdown_content += f"**Overall Score:** {feasibility.get('overall_feasibility_score', 0):.1f}/10\n\n"
        markdown_content += f"**Timeline:** {feasibility.get('estimated_timeline_weeks', 0)} weeks\n\n"
        markdown_content += f"**Team Size:** {feasibility.get('recommended_team_size', 0)} people\n\n"

    if "risks" in include_sections:
        risks = technical_data.get("risk_analysis", {})
        markdown_content += "## Risk Analysis\n\n"
        markdown_content += f"**Overall Risk Level:** {risks.get('overall_risk_level', 0):.1f}/10\n\n"
        risk_categories = risks.get("risk_categories", {})
        for category, risk_data in risk_categories.items():
            if isinstance(risk_data, dict):
                markdown_content += f"### {category.title()} Risk\n"
                markdown_content += f"- **Severity:** {risk_data.get('severity', 0):.1f}/10\n"
                markdown_content += f"- **Confidence:** {risk_data.get('confidence', 0):.1f}\n\n"

    if "roadmap" in include_sections:
        roadmap = technical_data.get("implementation_roadmap", {})
        markdown_content += "## Implementation Roadmap\n\n"
        phases = roadmap.get("phases", [])
        for phase in phases:
            markdown_content += f"### Phase {phase.get('phase', 'Unknown')}: {phase.get('name', 'Unnamed')}\n"
            markdown_content += f"**Duration:** {phase.get('duration_weeks', 0)} weeks\n\n"
            deliverables = phase.get("deliverables", [])
            if deliverables:
                markdown_content += "**Deliverables:**\n"
                for deliverable in deliverables:
                    markdown_content += f"- {deliverable}\n"
                markdown_content += "\n"

    # Add consensus metadata
    consensus = technical_data.get("consensus_metadata", {})
    markdown_content += "## Consensus Analysis\n\n"
    markdown_content += f"**Consensus Level:** {consensus.get('consensus_level', 'Unknown')}\n\n"
    markdown_content += f"**Agreement Score:** {consensus.get('agreement_score', 0):.1%}\n\n"
    markdown_content += f"**Models Used:** {', '.join(consensus.get('models_used', []))}\n\n"

    conflict_areas = consensus.get("conflict_areas", [])
    if conflict_areas:
        markdown_content += "**Areas of Conflict:**\n"
        for conflict in conflict_areas:
            markdown_content += f"- {conflict}\n"
        markdown_content += "\n"

    # Add quality metrics
    quality = technical_data.get("quality_assessment", {})
    markdown_content += "## Quality Metrics\n\n"
    markdown_content += f"**Overall Score:** {quality.get('overall_score', 0):.1f}%\n\n"
    markdown_content += f"**Meets Threshold:** {'Yes' if quality.get('meets_threshold', False) else 'No'}\n\n"
    markdown_content += f"**Quality Threshold:** {quality.get('threshold', 85)}%\n\n"

    return markdown_content


def generate_json_export(technical_data: Dict[str, Any], include_sections: List[str]) -> Dict[str, Any]:
    """Generate JSON export of technical analysis"""

    export_data = {
        "export_metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "session_id": technical_data.get("session_id"),
            "user_id": technical_data.get("user_id"),
            "sections_included": include_sections,
        }
    }

    if "architecture" in include_sections:
        export_data["architecture_recommendation"] = technical_data.get("architecture_recommendation", {})

    if "technology_stack" in include_sections:
        export_data["technology_stack"] = technical_data.get("technology_stack", {})

    if "feasibility" in include_sections:
        export_data["feasibility_assessment"] = technical_data.get("feasibility_assessment", {})

    if "risks" in include_sections:
        export_data["risk_analysis"] = technical_data.get("risk_analysis", {})

    if "roadmap" in include_sections:
        export_data["implementation_roadmap"] = technical_data.get("implementation_roadmap", {})

    export_data["consensus_metadata"] = technical_data.get("consensus_metadata", {})
    export_data["quality_assessment"] = technical_data.get("quality_assessment", {})

    return export_data
