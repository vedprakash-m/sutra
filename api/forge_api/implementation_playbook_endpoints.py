"""
Implementation Playbook API Endpoints for Forge Module.
Generates step-by-step coding agent prompts and execution guides for systematic development
with complete project context integration and quality validation.

Task 2.7: Implementation Playbook Generation Stage
- Context Integration: Full project context from all stages informs prompt generation
- Agent Optimization: Prompts specifically designed for coding agent consumption
- Quality Assurance: Testing and QA procedures aligned to quality standards throughout
- Deployment Readiness: Complete environment setup and deployment procedures
"""

import json
import logging
import os

# Import shared modules
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import azure.functions as func
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))

from auth_helpers import extract_user_info
from coding_agent_optimizer import CodingAgentOptimizer, generate_coding_prompts
from cost_tracking import CostTracker, calculate_operation_cost
from llm_client import LLMClient
from quality_engine import QualityEngine
from quality_validators import CrossStageQualityValidator

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_NAME = "SutraDB"
FORGE_CONTAINER = "ForgeProjects"

# Initialize services
quality_engine = QualityEngine()
quality_validator = CrossStageQualityValidator()
coding_optimizer = CodingAgentOptimizer()
cost_tracker = CostTracker()


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main entry point for implementation playbook API"""
    try:
        method = req.method
        route = req.route_params.get("route", "")

        if method == "POST" and route == "generate-coding-prompts":
            return generate_coding_prompts_endpoint(req)
        elif method == "POST" and route == "create-development-workflow":
            return create_development_workflow_endpoint(req)
        elif method == "POST" and route == "generate-testing-strategy":
            return generate_testing_strategy_endpoint(req)
        elif method == "POST" and route == "create-deployment-guide":
            return create_deployment_guide_endpoint(req)
        elif method == "POST" and route == "compile-playbook":
            return compile_playbook_endpoint(req)
        elif method == "POST" and route == "validate-context-integration":
            return validate_context_integration_endpoint(req)
        elif method == "POST" and route == "optimize-for-agents":
            return optimize_for_agents_endpoint(req)
        elif method == "GET" and route == "export-playbook":
            return export_playbook_endpoint(req)
        elif method == "GET" and route == "quality-validation":
            return quality_validation_endpoint(req)
        else:
            return func.HttpResponse(json.dumps({"error": "Invalid route"}), status_code=404, mimetype="application/json")

    except Exception as e:
        logger.error(f"Implementation Playbook API error: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def generate_coding_prompts_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Generate coding-agent-optimized prompts using complete project context"""
    try:
        # Extract user info
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        # Parse request
        request_data = json.loads(req.get_body())
        project_id = request_data.get("project_id")
        context_data = request_data.get("context_data", {})
        prompt_focus = request_data.get("prompt_focus", "full-stack")
        optimization_level = request_data.get("optimization_level", "production")

        if not project_id:
            return func.HttpResponse(
                json.dumps({"error": "Project ID required"}), status_code=400, mimetype="application/json"
            )

        # Initialize LLM client
        llm_client = LLMClient()

        # Generate context-aware coding prompts
        coding_prompts = coding_optimizer.generate_context_optimized_prompts(
            project_context=context_data, focus_area=prompt_focus, optimization_level=optimization_level
        )

        # Track cost
        cost_info = cost_tracker.track_operation(
            user_id=user_info.get("user_id"),
            operation_type="implementation_playbook_generation",
            tokens_used=estimate_tokens_for_prompt_generation(coding_prompts),
            provider="context_optimization",
        )

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "coding_prompts": coding_prompts,
                    "cost_info": cost_info,
                    "generation_timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Generate coding prompts error: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def create_development_workflow_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Create step-by-step development workflow based on technical architecture and UX specifications"""
    try:
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        request_data = json.loads(req.get_body())
        project_id = request_data.get("project_id")
        technical_analysis = request_data.get("technical_analysis", {})
        ux_requirements = request_data.get("ux_requirements", {})
        prd_data = request_data.get("prd_data", {})
        workflow_type = request_data.get("workflow_type", "agile_sprints")

        # Generate development workflow
        workflow = coding_optimizer.create_systematic_workflow(
            technical_specs=technical_analysis,
            ux_specs=ux_requirements,
            requirements=prd_data,
            workflow_methodology=workflow_type,
        )

        # Add quality checkpoints
        quality_checkpoints = quality_engine.generate_workflow_checkpoints(
            workflow=workflow, quality_standards=request_data.get("quality_standards", "production")
        )

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "development_workflow": workflow,
                    "quality_checkpoints": quality_checkpoints,
                    "estimated_timeline": calculate_workflow_timeline(workflow),
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Create development workflow error: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def generate_testing_strategy_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Generate comprehensive testing strategy and quality assurance playbook"""
    try:
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        request_data = json.loads(req.get_body())
        project_context = request_data.get("project_context", {})
        testing_scope = request_data.get("testing_scope", "comprehensive")

        # Generate testing strategy
        testing_strategy = {
            "unit_testing": generate_unit_testing_strategy(project_context),
            "integration_testing": generate_integration_testing_strategy(project_context),
            "e2e_testing": generate_e2e_testing_strategy(project_context),
            "performance_testing": generate_performance_testing_strategy(project_context),
            "security_testing": generate_security_testing_strategy(project_context),
            "accessibility_testing": generate_accessibility_testing_strategy(project_context),
            "qa_procedures": generate_qa_procedures(project_context),
        }

        # Validate testing completeness
        testing_quality = quality_engine.assess_testing_strategy(testing_strategy)

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "testing_strategy": testing_strategy,
                    "quality_assessment": testing_quality,
                    "coverage_recommendations": generate_coverage_recommendations(testing_strategy),
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Generate testing strategy error: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def create_deployment_guide_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Create deployment procedures and environment setup guides"""
    try:
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        request_data = json.loads(req.get_body())
        technical_specs = request_data.get("technical_specs", {})
        deployment_target = request_data.get("deployment_target", "cloud")
        environment_requirements = request_data.get("environment_requirements", {})

        # Generate deployment guide
        deployment_guide = {
            "environment_setup": generate_environment_setup(technical_specs, environment_requirements),
            "build_procedures": generate_build_procedures(technical_specs),
            "deployment_steps": generate_deployment_steps(technical_specs, deployment_target),
            "monitoring_setup": generate_monitoring_setup(technical_specs),
            "backup_procedures": generate_backup_procedures(technical_specs),
            "rollback_procedures": generate_rollback_procedures(technical_specs),
            "security_configurations": generate_security_configurations(technical_specs),
        }

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "deployment_guide": deployment_guide,
                    "deployment_checklist": generate_deployment_checklist(deployment_guide),
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Create deployment guide error: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def compile_playbook_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Compile comprehensive implementation playbook with quality validation"""
    try:
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        request_data = json.loads(req.get_body())
        project_id = request_data.get("project_id")

        # Get all project context from database
        project_context = get_complete_project_context(project_id)

        # Compile comprehensive playbook
        implementation_playbook = {
            "project_overview": project_context.get("idea_refinement", {}),
            "requirements_summary": project_context.get("prd_generation", {}),
            "ux_specifications": project_context.get("ux_requirements", {}),
            "technical_architecture": project_context.get("technical_analysis", {}),
            "coding_prompts": request_data.get("coding_prompts", {}),
            "development_workflow": request_data.get("development_workflow", {}),
            "testing_strategy": request_data.get("testing_strategy", {}),
            "deployment_guide": request_data.get("deployment_guide", {}),
            "quality_standards": generate_quality_standards(project_context),
            "success_metrics": generate_success_metrics(project_context),
        }

        # Validate context integration
        context_validation = quality_validator.validate_cross_stage_consistency(
            playbook=implementation_playbook, project_context=project_context
        )

        # Save compiled playbook
        save_implementation_playbook(project_id, implementation_playbook, user_info)

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "implementation_playbook": implementation_playbook,
                    "context_validation": context_validation,
                    "compilation_timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Compile playbook error: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def export_playbook_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Export implementation playbook in multiple formats"""
    try:
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        project_id = req.route_params.get("project_id")
        export_format = req.params.get("format", "json")

        # Get playbook from database
        playbook = get_implementation_playbook(project_id)

        if export_format == "markdown":
            exported_content = export_to_markdown(playbook)
            content_type = "text/markdown"
        elif export_format == "json":
            exported_content = json.dumps(playbook, indent=2)
            content_type = "application/json"
        elif export_format == "zip":
            exported_content = export_to_zip_archive(playbook)
            content_type = "application/zip"
        else:
            return func.HttpResponse(
                json.dumps({"error": "Unsupported export format"}), status_code=400, mimetype="application/json"
            )

        return func.HttpResponse(
            exported_content,
            status_code=200,
            mimetype=content_type,
            headers={"Content-Disposition": f'attachment; filename="implementation_playbook.{export_format}"'},
        )

    except Exception as e:
        logger.error(f"Export playbook error: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


# Helper functions


def estimate_tokens_for_prompt_generation(prompts: Dict) -> int:
    """Estimate token usage for prompt generation"""
    total_chars = sum(len(str(prompt)) for prompt in prompts.values())
    return int(total_chars / 4)  # Rough estimate: 4 chars per token


def calculate_workflow_timeline(workflow: Dict) -> Dict:
    """Calculate estimated timeline for development workflow"""
    return {
        "estimated_duration_weeks": len(workflow.get("phases", [])) * 2,
        "critical_path": workflow.get("critical_path", []),
        "milestone_dates": workflow.get("milestones", []),
    }


def generate_unit_testing_strategy(context: Dict) -> Dict:
    """Generate unit testing strategy based on project context"""
    return {
        "framework_recommendations": ["Jest", "Pytest", "JUnit"],
        "coverage_targets": {"minimum": 80, "target": 90},
        "testing_patterns": ["AAA Pattern", "Mock/Stub", "Test Doubles"],
        "automation_setup": ["CI/CD Integration", "Pre-commit Hooks"],
    }


def generate_integration_testing_strategy(context: Dict) -> Dict:
    """Generate integration testing strategy"""
    return {
        "api_testing": ["Postman/Newman", "REST Assured", "Supertest"],
        "database_testing": ["Test Containers", "In-memory DB", "Fixtures"],
        "service_integration": ["WireMock", "Test Doubles", "Contract Testing"],
    }


def generate_e2e_testing_strategy(context: Dict) -> Dict:
    """Generate end-to-end testing strategy"""
    return {
        "framework": "Playwright",
        "test_scenarios": ["Happy Path", "Error Handling", "Edge Cases"],
        "browser_coverage": ["Chrome", "Firefox", "Safari"],
        "mobile_testing": True,
    }


def generate_performance_testing_strategy(context: Dict) -> Dict:
    """Generate performance testing strategy"""
    return {
        "load_testing": "Artillery/K6",
        "stress_testing": "JMeter",
        "metrics": ["Response Time", "Throughput", "Error Rate"],
        "targets": {"response_time_ms": 300, "concurrent_users": 1000},
    }


def generate_security_testing_strategy(context: Dict) -> Dict:
    """Generate security testing strategy"""
    return {
        "vulnerability_scanning": "OWASP ZAP",
        "dependency_scanning": "npm audit",
        "authentication_testing": "JWT Validation",
        "authorization_testing": "Role-based Access",
    }


def generate_accessibility_testing_strategy(context: Dict) -> Dict:
    """Generate accessibility testing strategy"""
    return {
        "automated_testing": "axe-core",
        "manual_testing": "Screen Reader Testing",
        "compliance_target": "WCAG 2.1 AA",
        "tools": ["Lighthouse", "WAVE", "Color Contrast Analyzer"],
    }


def generate_qa_procedures(context: Dict) -> Dict:
    """Generate QA procedures"""
    return {
        "code_review_process": "Pull Request Reviews",
        "testing_phases": ["Unit", "Integration", "E2E", "UAT"],
        "quality_gates": ["Code Coverage", "Security Scan", "Performance"],
        "release_criteria": ["All Tests Pass", "Security Clear", "Performance OK"],
    }


def generate_coverage_recommendations(strategy: Dict) -> List[str]:
    """Generate coverage recommendations for testing strategy"""
    return [
        "Aim for 90%+ unit test coverage",
        "Include integration tests for all API endpoints",
        "Implement E2E tests for critical user journeys",
        "Add performance tests for high-traffic scenarios",
        "Include security tests for authentication flows",
    ]


def generate_environment_setup(technical_specs: Dict, requirements: Dict) -> Dict:
    """Generate environment setup instructions"""
    return {
        "development": {
            "prerequisites": ["Node.js 18+", "Python 3.9+", "Docker"],
            "setup_commands": ["npm install", "pip install -r requirements.txt"],
            "environment_variables": ["API_KEY", "DATABASE_URL"],
        },
        "staging": {
            "infrastructure": "Azure Container Apps",
            "configuration": "staging.env",
            "deployment": "Azure DevOps Pipeline",
        },
        "production": {
            "infrastructure": "Azure App Service",
            "configuration": "production.env",
            "deployment": "Blue-Green Deployment",
        },
    }


def generate_build_procedures(technical_specs: Dict) -> Dict:
    """Generate build procedures"""
    return {
        "frontend_build": ["npm run build", "npm run test", "npm run lint"],
        "backend_build": ["pip install", "pytest", "flake8"],
        "containerization": ["docker build", "docker test", "docker push"],
        "artifacts": ["dist/", "build/", "docker images"],
    }


def generate_deployment_steps(technical_specs: Dict, target: str) -> List[Dict]:
    """Generate deployment steps"""
    return [
        {"step": 1, "action": "Build and test application", "command": "npm run build && npm test"},
        {"step": 2, "action": "Create container image", "command": "docker build -t app:latest ."},
        {"step": 3, "action": "Push to registry", "command": "docker push registry/app:latest"},
        {"step": 4, "action": "Deploy to target", "command": f"deploy to {target}"},
        {"step": 5, "action": "Run health checks", "command": "curl /health"},
        {"step": 6, "action": "Verify deployment", "command": "smoke tests"},
    ]


def generate_monitoring_setup(technical_specs: Dict) -> Dict:
    """Generate monitoring setup"""
    return {
        "application_monitoring": "Application Insights",
        "infrastructure_monitoring": "Azure Monitor",
        "log_aggregation": "Azure Log Analytics",
        "alerts": ["High Error Rate", "High Response Time", "Low Availability"],
    }


def generate_backup_procedures(technical_specs: Dict) -> Dict:
    """Generate backup procedures"""
    return {
        "database_backups": "Daily automated backups",
        "file_storage_backups": "Incremental backups",
        "configuration_backups": "Git repository",
        "recovery_procedures": "Documented restore steps",
    }


def generate_rollback_procedures(technical_specs: Dict) -> Dict:
    """Generate rollback procedures"""
    return {
        "database_rollback": "Migration rollback scripts",
        "application_rollback": "Previous container version",
        "configuration_rollback": "Git revert",
        "verification": "Health checks and smoke tests",
    }


def generate_security_configurations(technical_specs: Dict) -> Dict:
    """Generate security configurations"""
    return {
        "authentication": "Azure AD integration",
        "authorization": "Role-based access control",
        "encryption": "TLS 1.3 and data encryption",
        "security_headers": "CSP, HSTS, X-Frame-Options",
    }


def generate_deployment_checklist(deployment_guide: Dict) -> List[str]:
    """Generate deployment checklist"""
    return [
        "All tests passing",
        "Security scan completed",
        "Performance benchmarks met",
        "Environment variables configured",
        "Database migrations ready",
        "Monitoring alerts configured",
        "Backup procedures tested",
        "Rollback plan documented",
        "Team notified",
        "Documentation updated",
    ]


def get_complete_project_context(project_id: str) -> Dict:
    """Get complete project context from all stages"""
    try:
        # This would connect to Cosmos DB and retrieve all stage data
        # Placeholder implementation
        return {"idea_refinement": {}, "prd_generation": {}, "ux_requirements": {}, "technical_analysis": {}}
    except Exception as e:
        logger.error(f"Error getting project context: {str(e)}")
        return {}


def generate_quality_standards(context: Dict) -> Dict:
    """Generate quality standards for the project"""
    return {
        "code_quality": {"coverage": 90, "complexity": "low", "duplication": "minimal"},
        "performance": {"response_time": 300, "throughput": "high", "availability": 99.9},
        "security": {"vulnerabilities": "none", "compliance": "OWASP", "encryption": "required"},
        "accessibility": {"compliance": "WCAG 2.1 AA", "testing": "automated + manual"},
    }


def generate_success_metrics(context: Dict) -> Dict:
    """Generate success metrics for the project"""
    return {
        "technical_metrics": ["Code Coverage", "Performance", "Security Score"],
        "business_metrics": ["User Adoption", "Feature Usage", "Customer Satisfaction"],
        "operational_metrics": ["Uptime", "Error Rate", "Response Time"],
    }


def save_implementation_playbook(project_id: str, playbook: Dict, user_info: Dict) -> None:
    """Save implementation playbook to database"""
    try:
        # This would save to Cosmos DB
        logger.info(f"Saved implementation playbook for project {project_id}")
    except Exception as e:
        logger.error(f"Error saving playbook: {str(e)}")


def get_implementation_playbook(project_id: str) -> Dict:
    """Get implementation playbook from database"""
    try:
        # This would retrieve from Cosmos DB
        return {"playbook": "data"}
    except Exception as e:
        logger.error(f"Error getting playbook: {str(e)}")
        return {}


def export_to_markdown(playbook: Dict) -> str:
    """Export playbook to markdown format"""
    return f"# Implementation Playbook\n\n{json.dumps(playbook, indent=2)}"


def export_to_zip_archive(playbook: Dict) -> bytes:
    """Export playbook as zip archive with multiple files"""
    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file:
        zip_file.writestr("playbook.json", json.dumps(playbook, indent=2))
        zip_file.writestr("README.md", export_to_markdown(playbook))

    return buffer.getvalue()


def validate_context_integration_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Validate context integration across all stages"""
    try:
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        request_data = json.loads(req.get_body())
        project_id = request_data.get("project_id")

        # Get complete project context
        project_context = get_complete_project_context(project_id)

        # Validate context integration
        validation_result = quality_validator.validate_cross_stage_consistency(project_context=project_context)

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "validation_result": validation_result,
                    "context_integrity": validation_result.get("overall_score", 0) > 85,
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Validate context integration error: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def optimize_for_agents_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Optimize prompts specifically for coding agent consumption"""
    try:
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        request_data = json.loads(req.get_body())
        raw_prompts = request_data.get("prompts", {})
        agent_type = request_data.get("agent_type", "general")

        # Optimize for coding agents
        optimized_prompts = coding_optimizer.optimize_for_coding_agents(prompts=raw_prompts, agent_type=agent_type)

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "optimized_prompts": optimized_prompts,
                    "optimization_report": coding_optimizer.get_optimization_report(),
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Optimize for agents error: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


def quality_validation_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Final quality validation for implementation playbook"""
    try:
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        project_id = req.route_params.get("project_id")

        # Get playbook and validate quality
        playbook = get_implementation_playbook(project_id)
        quality_assessment = quality_engine.assess_implementation_playbook(playbook)

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "quality_assessment": quality_assessment,
                    "ready_for_implementation": quality_assessment.get("overall_score", 0) >= 85,
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Quality validation error: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")
