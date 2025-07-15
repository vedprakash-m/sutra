"""
Idea Refinement API endpoints for the Forge module.
Implements systematic idea clarification and multi-dimensional analysis with quality gates.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import azure.functions as func
from azure.cosmos.aio import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from shared.auth_helpers import extract_user_info
from shared.llm_client import LLMClient
from shared.cost_tracker import CostTracker
from shared.quality_engine import QualityAssessmentEngine, ContextualQualityValidator

logger = logging.getLogger(__name__)

# Database configuration
COSMOS_CONNECTION_STRING = "your_cosmos_connection_string_here"
DATABASE_NAME = "SutraDB"
PLAYBOOKS_CONTAINER = "Playbooks"  # Forge projects are stored as specialized playbooks

quality_engine = QualityAssessmentEngine()
context_validator = ContextualQualityValidator()


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main entry point for Idea Refinement API endpoints."""
    try:
        # Extract method and route parameters
        method = req.method
        route_params = req.route_params
        action = route_params.get('action', '')
        project_id = route_params.get('project_id', '')
        
        logger.info(f"Idea Refinement API - Method: {method}, Action: {action}, Project: {project_id}")
        
        # Route to appropriate handler
        if method == "POST" and action == "analyze":
            return await analyze_idea(req, project_id)
        elif method == "POST" and action == "refine":
            return await refine_idea_with_llm(req, project_id)
        elif method == "GET" and action == "assessment":
            return await get_quality_assessment(req, project_id)
        elif method == "POST" and action == "complete":
            return await complete_stage(req, project_id)
        else:
            return func.HttpResponse(
                json.dumps({"error": f"Unsupported operation: {method} {action}"}),
                status_code=405,
                headers={"Content-Type": "application/json"}
            )
            
    except Exception as e:
        logger.error(f"Error in idea refinement endpoint: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )


async def analyze_idea(req: func.HttpRequest, project_id: str) -> func.HttpResponse:
    """Analyze idea with multi-dimensional quality assessment"""
    try:
        # Extract user info and request data
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}),
                status_code=401,
                headers={"Content-Type": "application/json"}
            )
            
        request_data = json.loads(req.get_body().decode('utf-8'))
        idea_data = request_data.get('ideaData', {})
        project_context = request_data.get('projectContext', {})
        
        # Validate required fields
        if not idea_data.get('initialIdea'):
            return func.HttpResponse(
                json.dumps({"error": "Initial idea is required"}),
                status_code=400,
                headers={"Content-Type": "application/json"}
            )
        
        # Perform quality assessment
        quality_result = quality_engine.calculate_quality_score(
            stage="idea_refinement",
            content=idea_data,
            context=project_context
        )
        
        # Get adaptive thresholds
        thresholds = quality_engine.get_dynamic_threshold("idea_refinement", project_context)
        
        # Prepare analysis result
        analysis_result = {
            "projectId": project_id,
            "analysisTimestamp": datetime.now(timezone.utc).isoformat(),
            "qualityAssessment": {
                "overallScore": quality_result.overall_score,
                "dimensionScores": quality_result.dimension_scores,
                "qualityGateStatus": quality_result.quality_gate_status,
                "confidenceLevel": quality_result.confidence_level,
                "thresholds": {
                    "minimum": thresholds.minimum,
                    "recommended": thresholds.recommended,
                    "adjustmentsApplied": thresholds.adjustments_applied
                }
            },
            "improvementSuggestions": quality_result.improvement_suggestions,
            "estimatedImprovementTime": quality_result.estimated_improvement_time,
            "contextValidation": quality_result.context_consistency,
            "nextSteps": _generate_next_steps(quality_result, thresholds)
        }
        
        return func.HttpResponse(
            json.dumps(analysis_result),
            status_code=200,
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        logger.error(f"Error analyzing idea: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to analyze idea", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )


async def refine_idea_with_llm(req: func.HttpRequest, project_id: str) -> func.HttpResponse:
    """Use LLM to refine and enhance idea based on quality assessment"""
    try:
        # Extract user info and request data
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}),
                status_code=401,
                headers={"Content-Type": "application/json"}
            )
            
        request_data = json.loads(req.get_body().decode('utf-8'))
        current_idea = request_data.get('currentIdea', {})
        improvement_focus = request_data.get('improvementFocus', [])
        selected_llm = request_data.get('selectedLLM', 'gemini-flash')
        project_context = request_data.get('projectContext', {})
        
        # Initialize cost tracking
        cost_tracker = CostTracker()
        
        # Create refinement prompt based on quality assessment
        refinement_prompt = _create_refinement_prompt(current_idea, improvement_focus, project_context)
        
        # Execute LLM call with cost tracking
        llm_client = LLMClient()
        
        # Track cost before execution
        await cost_tracker.track_llm_call_start(
            user_id=user_info.get('user_id'),
            operation="forge_idea_refinement",
            model=selected_llm,
            project_id=project_id
        )
        
        try:
            response = await llm_client.execute_prompt(
                prompt=refinement_prompt,
                model=selected_llm,
                temperature=0.7,
                max_tokens=2000
            )
            
            # Track successful completion
            await cost_tracker.track_llm_call_complete(
                operation_id=cost_tracker.current_operation_id,
                response=response,
                tokens_used=response.get('usage', {}).get('total_tokens', 0),
                cost=response.get('cost', 0.0)
            )
            
        except Exception as llm_error:
            # Track failed execution
            await cost_tracker.track_llm_call_error(
                operation_id=cost_tracker.current_operation_id,
                error=str(llm_error)
            )
            raise llm_error
        
        # Parse LLM response
        refined_content = _parse_llm_refinement_response(response.get('content', ''))
        
        # Re-assess quality after refinement
        post_refinement_quality = quality_engine.calculate_quality_score(
            stage="idea_refinement",
            content=refined_content,
            context=project_context
        )
        
        # Prepare refinement result
        refinement_result = {
            "projectId": project_id,
            "refinementTimestamp": datetime.now(timezone.utc).isoformat(),
            "refinedIdea": refined_content,
            "qualityImprovement": {
                "beforeScore": current_idea.get('qualityScore', 0),
                "afterScore": post_refinement_quality.overall_score,
                "improvement": post_refinement_quality.overall_score - current_idea.get('qualityScore', 0),
                "newDimensionScores": post_refinement_quality.dimension_scores
            },
            "costTracking": {
                "tokensUsed": response.get('usage', {}).get('total_tokens', 0),
                "cost": response.get('cost', 0.0),
                "model": selected_llm
            },
            "qualityGateStatus": post_refinement_quality.quality_gate_status,
            "remainingSuggestions": post_refinement_quality.improvement_suggestions
        }
        
        return func.HttpResponse(
            json.dumps(refinement_result),
            status_code=200,
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        logger.error(f"Error refining idea with LLM: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to refine idea", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )


async def get_quality_assessment(req: func.HttpRequest, project_id: str) -> func.HttpResponse:
    """Get current quality assessment for the idea refinement stage"""
    try:
        # Extract user info
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}),
                status_code=401,
                headers={"Content-Type": "application/json"}
            )
        
        # Get project from database
        async with CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING) as client:
            database = client.get_database_client(DATABASE_NAME)
            container = database.get_container_client(PLAYBOOKS_CONTAINER)
            
            try:
                project = await container.read_item(item=project_id, partition_key=user_info['user_id'])
            except CosmosResourceNotFoundError:
                return func.HttpResponse(
                    json.dumps({"error": "Project not found"}),
                    status_code=404,
                    headers={"Content-Type": "application/json"}
                )
        
        # Extract idea refinement data
        forge_data = project.get('forgeData', {})
        idea_data = forge_data.get('ideaRefinement', {})
        project_context = forge_data.get('projectContext', {})
        
        if not idea_data:
            return func.HttpResponse(
                json.dumps({"error": "No idea refinement data found"}),
                status_code=404,
                headers={"Content-Type": "application/json"}
            )
        
        # Perform quality assessment
        quality_result = quality_engine.calculate_quality_score(
            stage="idea_refinement",
            content=idea_data,
            context=project_context
        )
        
        # Get adaptive thresholds
        thresholds = quality_engine.get_dynamic_threshold("idea_refinement", project_context)
        
        # Prepare assessment result
        assessment_result = {
            "projectId": project_id,
            "assessmentTimestamp": datetime.now(timezone.utc).isoformat(),
            "currentQuality": {
                "overallScore": quality_result.overall_score,
                "dimensionScores": quality_result.dimension_scores,
                "qualityGateStatus": quality_result.quality_gate_status,
                "confidenceLevel": quality_result.confidence_level
            },
            "thresholds": {
                "minimum": thresholds.minimum,
                "recommended": thresholds.recommended,
                "adjustmentsApplied": thresholds.adjustments_applied,
                "contextFactors": thresholds.context_factors
            },
            "improvementOpportunities": quality_result.improvement_suggestions,
            "estimatedImprovementTime": quality_result.estimated_improvement_time,
            "readyForNextStage": quality_result.quality_gate_status in ["PROCEED_WITH_CAUTION", "PROCEED_EXCELLENT"]
        }
        
        return func.HttpResponse(
            json.dumps(assessment_result),
            status_code=200,
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        logger.error(f"Error getting quality assessment: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to get quality assessment", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )


async def complete_stage(req: func.HttpRequest, project_id: str) -> func.HttpResponse:
    """Complete the idea refinement stage and prepare for PRD generation"""
    try:
        # Extract user info and request data
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}),
                status_code=401,
                headers={"Content-Type": "application/json"}
            )
            
        request_data = json.loads(req.get_body().decode('utf-8'))
        final_idea_data = request_data.get('finalIdeaData', {})
        force_complete = request_data.get('forceComplete', False)  # Expert override
        project_context = request_data.get('projectContext', {})
        
        # Perform final quality assessment
        quality_result = quality_engine.calculate_quality_score(
            stage="idea_refinement",
            content=final_idea_data,
            context=project_context
        )
        
        # Get thresholds
        thresholds = quality_engine.get_dynamic_threshold("idea_refinement", project_context)
        
        # Check if stage can be completed
        can_complete = (
            quality_result.quality_gate_status in ["PROCEED_WITH_CAUTION", "PROCEED_EXCELLENT"] or
            force_complete
        )
        
        if not can_complete:
            return func.HttpResponse(
                json.dumps({
                    "error": "Quality threshold not met",
                    "currentScore": quality_result.overall_score,
                    "requiredScore": thresholds.minimum,
                    "improvementSuggestions": quality_result.improvement_suggestions,
                    "canForceComplete": user_info.get('role') in ['expert', 'admin']
                }),
                status_code=400,
                headers={"Content-Type": "application/json"}
            )
        
        # Update project in database
        async with CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING) as client:
            database = client.get_database_client(DATABASE_NAME)
            container = database.get_container_client(PLAYBOOKS_CONTAINER)
            
            try:
                project = await container.read_item(item=project_id, partition_key=user_info['user_id'])
            except CosmosResourceNotFoundError:
                return func.HttpResponse(
                    json.dumps({"error": "Project not found"}),
                    status_code=404,
                    headers={"Content-Type": "application/json"}
                )
            
            # Update forge data
            if 'forgeData' not in project:
                project['forgeData'] = {}
            
            project['forgeData']['ideaRefinement'] = {
                **final_idea_data,
                "status": "completed",
                "completedAt": datetime.now(timezone.utc).isoformat(),
                "qualityMetrics": {
                    "overall": quality_result.overall_score,
                    "dimensions": quality_result.dimension_scores,
                    "gateStatus": quality_result.quality_gate_status,
                    "forceCompleted": force_complete
                },
                "contextForNextStage": _prepare_context_for_prd(final_idea_data, quality_result)
            }
            
            # Update project status
            project['updatedAt'] = datetime.now(timezone.utc).isoformat()
            
            # Save updated project
            await container.replace_item(item=project['id'], body=project)
        
        # Prepare completion result
        completion_result = {
            "projectId": project_id,
            "stageCompleted": "idea_refinement",
            "completionTimestamp": datetime.now(timezone.utc).isoformat(),
            "finalQualityScore": quality_result.overall_score,
            "qualityGateStatus": quality_result.quality_gate_status,
            "forceCompleted": force_complete,
            "readyForNextStage": True,
            "nextStage": "prd_generation",
            "contextPrepared": True,
            "qualityImpactOnNextStage": _predict_prd_quality_impact(quality_result)
        }
        
        return func.HttpResponse(
            json.dumps(completion_result),
            status_code=200,
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        logger.error(f"Error completing stage: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to complete stage", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )


def _generate_next_steps(quality_result: Any, thresholds: Any) -> List[Dict[str, Any]]:
    """Generate contextual next steps based on quality assessment"""
    next_steps = []
    
    if quality_result.quality_gate_status == "BLOCK":
        next_steps.append({
            "action": "improve_quality",
            "priority": "high",
            "message": "Address quality issues before proceeding",
            "estimatedTime": quality_result.estimated_improvement_time
        })
    elif quality_result.quality_gate_status == "PROCEED_WITH_CAUTION":
        next_steps.extend([
            {
                "action": "improve_quality",
                "priority": "medium",
                "message": "Consider improving quality for better results",
                "estimatedTime": quality_result.estimated_improvement_time
            },
            {
                "action": "proceed_to_prd",
                "priority": "medium",
                "message": "Proceed to PRD generation with current quality"
            }
        ])
    else:  # PROCEED_EXCELLENT
        next_steps.append({
            "action": "proceed_to_prd",
            "priority": "high",
            "message": "Excellent quality! Ready for PRD generation"
        })
    
    return next_steps


def _create_refinement_prompt(current_idea: Dict[str, Any], improvement_focus: List[str], 
                            project_context: Dict[str, Any]) -> str:
    """Create LLM prompt for idea refinement based on quality assessment"""
    
    prompt = f"""
You are an expert product strategist helping refine a product idea. 

CURRENT IDEA:
{json.dumps(current_idea, indent=2)}

IMPROVEMENT FOCUS AREAS:
{', '.join(improvement_focus)}

PROJECT CONTEXT:
- Complexity: {project_context.get('complexity', 'medium')}
- Type: {project_context.get('project_type', 'mvp')}
- User Experience Level: {project_context.get('user_experience', 'intermediate')}

Please refine this idea by addressing the focus areas. Provide your response in this JSON format:

{{
    "problemStatement": "Clear, specific problem statement with who, what, when, where, why",
    "targetAudience": "Detailed target audience with demographics and behaviors",
    "valueProposition": "Quantified value proposition with specific benefits",
    "marketAnalysis": {{
        "marketSize": "Market size with research or estimates",
        "competitors": ["competitor1", "competitor2", "competitor3"],
        "competitiveAdvantage": "Specific competitive advantages"
    }},
    "refinementNotes": "Explanation of improvements made"
}}

Focus on making the idea more specific, actionable, and market-validated.
"""
    
    return prompt.strip()


def _parse_llm_refinement_response(response_content: str) -> Dict[str, Any]:
    """Parse and validate LLM response for idea refinement"""
    try:
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            # Fallback: create structured response from text
            return {
                "problemStatement": response_content[:200] + "...",
                "targetAudience": "Extracted from LLM response",
                "valueProposition": "Extracted from LLM response",
                "marketAnalysis": {
                    "marketSize": "Analysis needed",
                    "competitors": [],
                    "competitiveAdvantage": "Extracted from LLM response"
                },
                "refinementNotes": "LLM response parsing fallback"
            }
    except Exception as e:
        logger.warning(f"Error parsing LLM response: {str(e)}")
        return {
            "problemStatement": "Parsing error occurred",
            "targetAudience": "Please review manually",
            "valueProposition": "Please review manually",
            "marketAnalysis": {
                "marketSize": "Unknown",
                "competitors": [],
                "competitiveAdvantage": "Please analyze manually"
            },
            "refinementNotes": f"Error: {str(e)}"
        }


def _prepare_context_for_prd(idea_data: Dict[str, Any], quality_result: Any) -> Dict[str, Any]:
    """Prepare context from idea refinement for PRD generation stage"""
    return {
        "validatedProblem": idea_data.get("problemStatement", ""),
        "targetUsers": idea_data.get("targetAudience", ""),
        "coreValue": idea_data.get("valueProposition", ""),
        "marketContext": idea_data.get("marketAnalysis", {}),
        "qualityFoundation": {
            "overallScore": quality_result.overall_score,
            "strongDimensions": [
                dim for dim, score in quality_result.dimension_scores.items() 
                if score > 85
            ],
            "improvementAreas": [
                dim for dim, score in quality_result.dimension_scores.items() 
                if score < 75
            ]
        }
    }


def _predict_prd_quality_impact(quality_result: Any) -> Dict[str, Any]:
    """Predict how idea refinement quality will impact PRD generation"""
    base_prediction = 75.0
    
    # Quality foundation impact
    quality_bonus = (quality_result.overall_score - 75) * 0.3
    
    # Dimension-specific impacts
    problem_clarity = quality_result.dimension_scores.get("problem_clarity", 75)
    audience_clarity = quality_result.dimension_scores.get("target_audience_definition", 75)
    
    if problem_clarity > 85:
        quality_bonus += 5
    if audience_clarity > 85:
        quality_bonus += 3
    
    predicted_prd_quality = min(95, base_prediction + quality_bonus)
    
    return {
        "predictedPRDQuality": predicted_prd_quality,
        "qualityImpact": quality_bonus,
        "strongFoundations": problem_clarity > 85 and audience_clarity > 85,
        "recommendations": [
            "Use validated problem statement for requirements",
            "Leverage target audience insights for user stories",
            "Build on competitive analysis for feature prioritization"
        ]
    }
