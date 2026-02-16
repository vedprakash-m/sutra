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
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import azure.functions as func
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from shared.async_database import AsyncCosmosHelper
from shared.auth_helpers import extract_user_info
from shared.cost_tracker import CostTracker
from shared.llm_client import LLMManager
from shared.coding_agent_optimizer import CodingAgentOptimizer
from shared.quality_engine import QualityAssessmentEngine
from shared.quality_validators import CrossStageQualityValidator

logger = logging.getLogger(__name__)

# Initialize services
quality_engine = QualityAssessmentEngine()
quality_validator = CrossStageQualityValidator()
coding_optimizer = CodingAgentOptimizer()
cost_tracker = CostTracker()


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main entry point for implementation playbook API"""
    try:
        method = req.method
        route = req.route_params.get("sub_action", "") or req.route_params.get("route", "")

        if method == "POST" and route == "generate-coding-prompts":
            return generate_coding_prompts_endpoint(req)
        elif method == "POST" and route == "create-development-workflow":
            return create_development_workflow_endpoint(req)
        elif method == "POST" and route == "generate-testing-strategy":
            return generate_testing_strategy_endpoint(req)
        elif method == "POST" and route == "create-deployment-guide":
            return create_deployment_guide_endpoint(req)
        elif method == "POST" and route == "compile-playbook":
            return await compile_playbook_endpoint(req)
        elif method == "POST" and route == "validate-context-integration":
            return await validate_context_integration_endpoint(req)
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
        llm_client = LLMManager()

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


async def compile_playbook_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Compile comprehensive implementation playbook with quality validation and full context integration"""
    try:
        user_info = extract_user_info(req)
        if not user_info:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}), status_code=401, mimetype="application/json"
            )

        request_data = json.loads(req.get_body())
        project_id = request_data.get("project_id")

        # Get complete project context from all Forge stages
        project_context = await get_complete_project_context(project_id)

        # Validate that all required stages are complete
        stage_completeness = validate_stage_completeness(project_context)
        if not stage_completeness["all_stages_complete"]:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "Incomplete Forge stages",
                        "missing_stages": stage_completeness["missing_stages"],
                        "message": "All Forge stages (1-4) must be completed before generating implementation playbook",
                    }
                ),
                status_code=400,
                mimetype="application/json",
            )

        # Generate context-optimized coding prompts
        coding_prompts = coding_optimizer.generate_context_optimized_prompts(
            project_context=project_context,
            focus_area=request_data.get("focus_area", "full-stack"),
            optimization_level=request_data.get("optimization_level", "production"),
        )

        # Generate systematic development workflow
        development_workflow = coding_optimizer.create_systematic_workflow(
            technical_specs=project_context.get("technical_analysis", {}),
            ux_specs=project_context.get("ux_requirements", {}),
            requirements=project_context.get("prd_generation", {}),
            workflow_methodology=request_data.get("workflow_methodology", "agile_sprints"),
        )

        # Generate comprehensive testing strategy
        testing_strategy = generate_comprehensive_testing_strategy(project_context)

        # Generate deployment guide with full context
        deployment_guide = generate_comprehensive_deployment_guide(project_context)

        # Compile comprehensive playbook with full context
        implementation_playbook = {
            "metadata": {
                "project_id": project_id,
                "compilation_timestamp": datetime.now(timezone.utc).isoformat(),
                "compiled_by": user_info.get("user_id"),
                "forge_version": "1.0.0",
                "context_quality_score": calculate_overall_context_quality(project_context),
            },
            "project_overview": {
                "idea_refinement": project_context.get("idea_refinement", {}),
                "problem_statement": project_context.get("idea_refinement", {}).get("problemStatement", ""),
                "value_proposition": project_context.get("idea_refinement", {}).get("valueProposition", ""),
                "target_audience": project_context.get("idea_refinement", {}).get("targetAudience", ""),
                "quality_score": project_context.get("idea_refinement", {}).get("qualityScore", 0),
            },
            "requirements_summary": {
                "prd_data": project_context.get("prd_generation", {}),
                "functional_requirements": project_context.get("prd_generation", {})
                .get("requirements", {})
                .get("functionalRequirements", []),
                "non_functional_requirements": project_context.get("prd_generation", {})
                .get("requirements", {})
                .get("nonFunctionalRequirements", []),
                "user_stories": project_context.get("prd_generation", {}).get("userStories", {}).get("stories", []),
                "quality_score": project_context.get("prd_generation", {}).get("qualityScore", 0),
            },
            "ux_specifications": {
                "design_system": project_context.get("ux_requirements", {}).get("designSystem", {}),
                "user_journeys": project_context.get("ux_requirements", {}).get("userJourneys", {}).get("journeys", []),
                "wireframes": project_context.get("ux_requirements", {}).get("wireframes", {}),
                "accessibility_requirements": project_context.get("ux_requirements", {}).get("accessibility", {}),
                "quality_score": project_context.get("ux_requirements", {}).get("qualityScore", 0),
            },
            "technical_architecture": {
                "architecture_recommendation": project_context.get("technical_analysis", {}).get(
                    "architecture_recommendation", {}
                ),
                "technology_stack": project_context.get("technical_analysis", {}).get("technology_stack", {}),
                "feasibility_assessment": project_context.get("technical_analysis", {}).get("feasibility_assessment", {}),
                "risk_analysis": project_context.get("technical_analysis", {}).get("risk_analysis", {}),
                "consensus_metadata": project_context.get("technical_analysis", {}).get("consensus_metadata", {}),
                "quality_score": project_context.get("technical_analysis", {}).get("qualityScore", 0),
            },
            "coding_prompts": coding_prompts,
            "development_workflow": development_workflow,
            "testing_strategy": testing_strategy,
            "deployment_guide": deployment_guide,
            "quality_standards": generate_quality_standards(project_context),
            "success_metrics": generate_success_metrics(project_context),
            "implementation_roadmap": generate_implementation_roadmap(project_context),
            "team_requirements": generate_team_requirements(project_context),
            "risk_mitigation": generate_risk_mitigation_plan(project_context),
            "monitoring_and_observability": generate_monitoring_strategy(project_context),
        }

        # Perform comprehensive context validation
        context_validation = quality_validator.validate_cross_stage_consistency(
            playbook=implementation_playbook, project_context=project_context
        )

        # Calculate final playbook quality score
        playbook_quality = calculate_playbook_quality(implementation_playbook, context_validation)

        # Save compiled playbook to database
        save_result = await save_implementation_playbook(project_id, implementation_playbook, user_info, playbook_quality)

        return func.HttpResponse(
            json.dumps(
                {
                    "success": True,
                    "implementation_playbook": implementation_playbook,
                    "context_validation": context_validation,
                    "playbook_quality": playbook_quality,
                    "save_status": save_result,
                    "compilation_timestamp": datetime.now(timezone.utc).isoformat(),
                    "export_options": {
                        "markdown": f"/api/forge/export-playbook?project_id={project_id}&format=markdown",
                        "json": f"/api/forge/export-playbook?project_id={project_id}&format=json",
                        "pdf": f"/api/forge/export-playbook?project_id={project_id}&format=pdf",
                        "zip": f"/api/forge/export-playbook?project_id={project_id}&format=zip",
                    },
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
        elif export_format == "pdf":
            exported_content = export_to_pdf(playbook)
            content_type = "application/pdf"
        elif export_format == "zip":
            exported_content = export_to_zip_archive(playbook)
            content_type = "application/zip"
        else:
            return func.HttpResponse(
                json.dumps({"error": "Unsupported export format. Supported: markdown, json, pdf, zip"}),
                status_code=400,
                mimetype="application/json",
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


async def get_complete_project_context(project_id: str) -> Dict:
    """Get complete project context from all Forge stages"""
    try:
        async with AsyncCosmosHelper() as db:
            try:
                project_doc = await db.read_item(project_id, partition_key=project_id)

                # Extract all stage data
                return {
                    "idea_refinement": project_doc.get("ideaRefinement", {}),
                    "prd_generation": project_doc.get("prdGeneration", {}),
                    "ux_requirements": project_doc.get("uxRequirements", {}),
                    "technical_analysis": project_doc.get("technicalAnalysis", {}),
                    "implementation_data": project_doc.get("implementationData", {}),
                }
            except CosmosResourceNotFoundError:
                logger.warning(f"Project {project_id} not found in database")
                return {}

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


# Note: save_implementation_playbook is defined below (line ~1726) with full Cosmos DB implementation.
# The stub that was previously here has been removed to eliminate the duplicate definition.


def export_to_markdown(playbook: Dict) -> str:
    """Export playbook to comprehensive markdown format"""
    md_content = []

    # Title
    metadata = playbook.get("metadata", {})
    md_content.append(f"# Implementation Playbook: {metadata.get('project_id', 'Unknown Project')}")
    md_content.append("")
    md_content.append(f"**Generated:** {metadata.get('compilation_timestamp', 'N/A')}")
    md_content.append(f"**Compiled By:** {metadata.get('compiled_by', 'N/A')}")
    md_content.append(f"**Context Quality:** {metadata.get('context_quality_score', 0):.1f}%")
    md_content.append("")
    md_content.append("---")
    md_content.append("")

    # Table of Contents
    md_content.append("## Table of Contents")
    md_content.append("")
    sections = [
        "Project Overview",
        "Requirements Summary",
        "UX Specifications",
        "Technical Architecture",
        "Coding Prompts",
        "Development Workflow",
        "Testing Strategy",
        "Deployment Guide",
        "Quality Standards",
        "Success Metrics",
        "Implementation Roadmap",
        "Team Requirements",
        "Risk Mitigation",
        "Monitoring & Observability",
    ]
    for i, section in enumerate(sections, 1):
        md_content.append(f"{i}. [{section}](#{section.lower().replace(' ', '-').replace('&', '')})")
    md_content.append("")
    md_content.append("---")
    md_content.append("")

    # 1. Project Overview
    md_content.append("## 1. Project Overview")
    md_content.append("")
    overview = playbook.get("project_overview", {})
    if overview.get("description"):
        md_content.append(f"**Description:** {overview.get('description')}")
        md_content.append("")
    if overview.get("goals"):
        md_content.append("**Goals:**")
        md_content.append("")
        for goal in overview.get("goals", []):
            md_content.append(f"- {goal}")
        md_content.append("")
    md_content.append(f"**Quality Score:** {overview.get('qualityScore', 0):.1f}%")
    md_content.append("")
    md_content.append("---")
    md_content.append("")

    # 2. Requirements Summary
    md_content.append("## 2. Requirements Summary")
    md_content.append("")
    requirements = playbook.get("requirements_summary", {})
    if requirements.get("functional_requirements"):
        md_content.append("### Functional Requirements")
        md_content.append("")
        for req in requirements.get("functional_requirements", []):
            md_content.append(f"- {req}")
        md_content.append("")
    if requirements.get("user_stories"):
        md_content.append("### User Stories")
        md_content.append("")
        for story in requirements.get("user_stories", [])[:10]:  # Top 10
            md_content.append(f"- **As a** {story.get('role', 'user')}, **I want** {story.get('goal', '...')}")
        md_content.append("")
    md_content.append("---")
    md_content.append("")

    # 3. UX Specifications
    md_content.append("## 3. UX Specifications")
    md_content.append("")
    ux = playbook.get("ux_specifications", {})
    if ux.get("design_system"):
        md_content.append("### Design System")
        md_content.append("")
        design = ux.get("design_system", {})
        if design.get("colors"):
            md_content.append(f"**Colors:** {', '.join(design.get('colors', []))}")
        if design.get("typography"):
            md_content.append(f"**Typography:** {', '.join(design.get('typography', []))}")
        md_content.append("")
    if ux.get("user_journeys"):
        md_content.append("### Key User Journeys")
        md_content.append("")
        for journey in ux.get("user_journeys", [])[:5]:  # Top 5
            md_content.append(f"- {journey.get('name', 'Unnamed Journey')}: {journey.get('steps', 'N/A')} steps")
        md_content.append("")
    md_content.append("---")
    md_content.append("")

    # 4. Technical Architecture
    md_content.append("## 4. Technical Architecture")
    md_content.append("")
    tech = playbook.get("technical_architecture", {})
    if tech.get("architecture_choice"):
        md_content.append(f"**Architecture:** {tech.get('architecture_choice', {}).get('value', 'N/A')}")
        md_content.append("")
    if tech.get("technology_stack"):
        md_content.append("### Technology Stack")
        md_content.append("")
        stack = tech.get("technology_stack", {})
        for category, tech_list in stack.items():
            if isinstance(tech_list, list):
                md_content.append(f"**{category.replace('_', ' ').title()}:** {', '.join(tech_list)}")
        md_content.append("")
    md_content.append("---")
    md_content.append("")

    # 5. Coding Prompts
    md_content.append("## 5. Coding Prompts")
    md_content.append("")
    md_content.append("Detailed AI coding assistant prompts are available in the full playbook JSON.")
    md_content.append("")
    md_content.append("---")
    md_content.append("")

    # 6. Development Workflow
    md_content.append("## 6. Development Workflow")
    md_content.append("")
    workflow = playbook.get("development_workflow", {})
    if workflow.get("methodology"):
        md_content.append(f"**Methodology:** {workflow.get('methodology', 'Agile')}")
        md_content.append("")
    if workflow.get("sprint_duration"):
        md_content.append(f"**Sprint Duration:** {workflow.get('sprint_duration', '2 weeks')}")
        md_content.append("")
    md_content.append("---")
    md_content.append("")

    # 7. Testing Strategy
    md_content.append("## 7. Testing Strategy")
    md_content.append("")
    testing = playbook.get("testing_strategy", {})
    for test_type in ["unit_testing", "integration_testing", "e2e_testing", "performance_testing", "security_testing"]:
        if test_type in testing:
            md_content.append(f"### {test_type.replace('_', ' ').title()}")
            md_content.append("")
            test_data = testing[test_type]
            if test_data.get("framework"):
                md_content.append(f"**Framework:** {test_data.get('framework')}")
            if test_data.get("coverage_targets"):
                md_content.append(f"**Coverage Targets:** {test_data.get('coverage_targets')}")
            md_content.append("")
    md_content.append("---")
    md_content.append("")

    # 8. Deployment Guide
    md_content.append("## 8. Deployment Guide")
    md_content.append("")
    deployment = playbook.get("deployment_guide", {})
    if deployment.get("deployment_strategy"):
        md_content.append(f"**Strategy:** {deployment.get('deployment_strategy')}")
        md_content.append("")
    if deployment.get("environment_setup"):
        md_content.append("### Environment Setup")
        md_content.append("")
        for env_type, env_data in deployment.get("environment_setup", {}).items():
            md_content.append(f"**{env_type.title()}:**")
            if isinstance(env_data, dict) and env_data.get("prerequisites"):
                for prereq in env_data.get("prerequisites", []):
                    md_content.append(f"  - {prereq}")
            md_content.append("")
    md_content.append("---")
    md_content.append("")

    # 9. Quality Standards
    md_content.append("## 9. Quality Standards")
    md_content.append("")
    quality = playbook.get("quality_standards", {})
    for standard_type in ["code_quality", "performance_standards", "security_standards"]:
        if standard_type in quality:
            md_content.append(f"### {standard_type.replace('_', ' ').title()}")
            md_content.append("")
            standard_data = quality[standard_type]
            if isinstance(standard_data, dict):
                for key, value in standard_data.items():
                    md_content.append(f"- **{key.replace('_', ' ').title()}:** {value}")
            md_content.append("")
    md_content.append("---")
    md_content.append("")

    # 10. Success Metrics
    md_content.append("## 10. Success Metrics")
    md_content.append("")
    metrics = playbook.get("success_metrics", {})
    for metric_category in ["technical_metrics", "business_metrics", "operational_metrics"]:
        if metric_category in metrics:
            md_content.append(f"### {metric_category.replace('_', ' ').title()}")
            md_content.append("")
            for metric in metrics[metric_category]:
                md_content.append(f"- {metric}")
            md_content.append("")
    md_content.append("---")
    md_content.append("")

    # 11. Implementation Roadmap
    md_content.append("## 11. Implementation Roadmap")
    md_content.append("")
    roadmap = playbook.get("implementation_roadmap", {})
    if roadmap.get("phases"):
        for phase in roadmap["phases"]:
            md_content.append(f"### {phase.get('name', 'Phase')}")
            md_content.append("")
            md_content.append(f"**Duration:** {phase.get('duration_percentage', 0)}% of timeline")
            md_content.append(f"**Focus:** {phase.get('focus', 'N/A')}")
            md_content.append("")
            if phase.get("deliverables"):
                md_content.append("**Deliverables:**")
                for deliverable in phase.get("deliverables", []):
                    md_content.append(f"- {deliverable}")
                md_content.append("")
    md_content.append("---")
    md_content.append("")

    # 12. Team Requirements
    md_content.append("## 12. Team Requirements")
    md_content.append("")
    team = playbook.get("team_requirements", {})
    if team.get("recommended_team_size"):
        md_content.append(f"**Recommended Team Size:** {team.get('recommended_team_size')} developers")
        md_content.append("")
    if team.get("key_roles"):
        md_content.append("### Key Roles")
        md_content.append("")
        for role in team.get("key_roles", []):
            md_content.append(f"- **{role.get('title', 'N/A')}:** {', '.join(role.get('skills', []))}")
        md_content.append("")
    md_content.append("---")
    md_content.append("")

    # 13. Risk Mitigation
    md_content.append("## 13. Risk Mitigation")
    md_content.append("")
    risks = playbook.get("risk_mitigation", {})
    if risks.get("risk_categories"):
        for category, risk_list in risks.get("risk_categories", {}).items():
            md_content.append(f"### {category.replace('_', ' ').title()}")
            md_content.append("")
            for risk in risk_list:
                md_content.append(f"- {risk}")
            md_content.append("")
    md_content.append("---")
    md_content.append("")

    # 14. Monitoring & Observability
    md_content.append("## 14. Monitoring & Observability")
    md_content.append("")
    monitoring = playbook.get("monitoring_and_observability", {})
    for monitor_type in ["application_monitoring", "infrastructure_monitoring", "log_management", "alerting"]:
        if monitor_type in monitoring:
            md_content.append(f"### {monitor_type.replace('_', ' ').title()}")
            md_content.append("")
            monitor_data = monitoring[monitor_type]
            if isinstance(monitor_data, dict):
                if monitor_data.get("metrics"):
                    md_content.append(f"**Metrics:** {', '.join(monitor_data.get('metrics', []))}")
                if monitor_data.get("tools"):
                    md_content.append(f"**Tools:** {', '.join(monitor_data.get('tools', []))}")
            md_content.append("")

    return "\n".join(md_content)


def export_to_pdf(playbook: Dict) -> bytes:
    """Export playbook to professional PDF format"""
    try:
        import io
        from datetime import datetime

        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
        from reportlab.lib.pagesizes import A4, letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            KeepTogether,
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)

        # Container for PDF elements
        story = []

        # Get styles
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1a365d"),
            spaceAfter=12,
            alignment=TA_CENTER,
        )

        subtitle_style = ParagraphStyle(
            "CustomSubtitle",
            parent=styles["Normal"],
            fontSize=12,
            textColor=colors.HexColor("#4a5568"),
            spaceAfter=20,
            alignment=TA_CENTER,
        )

        heading1_style = ParagraphStyle(
            "CustomHeading1",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#2d3748"),
            spaceAfter=12,
            spaceBefore=12,
        )

        heading2_style = ParagraphStyle(
            "CustomHeading2",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#4a5568"),
            spaceAfter=10,
            spaceBefore=10,
        )

        body_style = ParagraphStyle(
            "CustomBody", parent=styles["Normal"], fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=6
        )

        bullet_style = ParagraphStyle(
            "CustomBullet", parent=styles["Normal"], fontSize=10, leading=14, leftIndent=20, spaceAfter=4
        )

        # Cover Page
        metadata = playbook.get("metadata", {})
        story.append(Spacer(1, 2 * inch))
        story.append(Paragraph("Implementation Playbook", title_style))
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph(f"Project: {metadata.get('project_id', 'Unknown Project')}", subtitle_style))
        story.append(Spacer(1, 0.2 * inch))

        # Metadata table
        metadata_data = [
            ["Generated", metadata.get("compilation_timestamp", "N/A")],
            ["Compiled By", metadata.get("compiled_by", "N/A")],
            ["Context Quality", f"{metadata.get('context_quality_score', 0):.1f}%"],
            ["Forge Version", metadata.get("forge_version", "1.0.0")],
        ]
        metadata_table = Table(metadata_data, colWidths=[2 * inch, 4 * inch])
        metadata_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONT", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONT", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#2d3748")),
                    ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#4a5568")),
                ]
            )
        )
        story.append(metadata_table)
        story.append(PageBreak())

        # Table of Contents
        story.append(Paragraph("Table of Contents", heading1_style))
        story.append(Spacer(1, 0.2 * inch))

        toc_sections = [
            "1. Project Overview",
            "2. Requirements Summary",
            "3. UX Specifications",
            "4. Technical Architecture",
            "5. Coding Prompts",
            "6. Development Workflow",
            "7. Testing Strategy",
            "8. Deployment Guide",
            "9. Quality Standards",
            "10. Success Metrics",
            "11. Implementation Roadmap",
            "12. Team Requirements",
            "13. Risk Mitigation",
            "14. Monitoring & Observability",
        ]

        for section in toc_sections:
            story.append(Paragraph(f"• {section}", bullet_style))

        story.append(PageBreak())

        # Helper function to add sections
        def add_section(title, content_dict, key_mappings=None):
            story.append(Paragraph(title, heading1_style))
            story.append(Spacer(1, 0.1 * inch))

            if not content_dict:
                story.append(Paragraph("No data available", body_style))
                story.append(Spacer(1, 0.2 * inch))
                return

            if key_mappings:
                for display_name, dict_key in key_mappings.items():
                    value = content_dict.get(dict_key)
                    if value:
                        if isinstance(value, list):
                            story.append(Paragraph(f"<b>{display_name}:</b>", body_style))
                            for item in value[:10]:  # Limit to 10 items
                                if isinstance(item, dict):
                                    item_text = item.get("name") or item.get("title") or str(item)
                                else:
                                    item_text = str(item)
                                story.append(Paragraph(f"• {item_text}", bullet_style))
                        elif isinstance(value, dict):
                            story.append(Paragraph(f"<b>{display_name}:</b>", body_style))
                            for k, v in list(value.items())[:10]:
                                story.append(Paragraph(f"• {k}: {v}", bullet_style))
                        else:
                            story.append(Paragraph(f"<b>{display_name}:</b> {value}", body_style))
                        story.append(Spacer(1, 0.1 * inch))

            story.append(Spacer(1, 0.2 * inch))

        # 1. Project Overview
        overview = playbook.get("project_overview", {})
        add_section(
            "1. Project Overview",
            overview,
            {
                "Description": "description",
                "Goals": "goals",
                "Key Features": "key_features",
                "Quality Score": "qualityScore",
            },
        )

        # 2. Requirements Summary
        requirements = playbook.get("requirements_summary", {})
        add_section(
            "2. Requirements Summary",
            requirements,
            {
                "Functional Requirements": "functional_requirements",
                "Non-Functional Requirements": "non_functional_requirements",
                "User Stories": "user_stories",
            },
        )

        # 3. UX Specifications
        ux = playbook.get("ux_specifications", {})
        add_section(
            "3. UX Specifications",
            ux,
            {"Design System": "design_system", "User Journeys": "user_journeys", "Wireframes": "wireframes"},
        )

        # 4. Technical Architecture
        tech = playbook.get("technical_architecture", {})
        story.append(Paragraph("4. Technical Architecture", heading1_style))
        story.append(Spacer(1, 0.1 * inch))

        if tech.get("architecture_choice"):
            arch = tech["architecture_choice"]
            story.append(
                Paragraph(
                    f"<b>Architecture:</b> {arch.get('value', 'N/A')} (Consensus: {arch.get('consensus_score', 0):.1f}%)",
                    body_style,
                )
            )

        if tech.get("technology_stack"):
            story.append(Paragraph("<b>Technology Stack:</b>", body_style))
            stack = tech["technology_stack"]
            for category, tech_list in stack.items():
                if isinstance(tech_list, list):
                    story.append(Paragraph(f"• {category.replace('_', ' ').title()}: {', '.join(tech_list)}", bullet_style))

        if tech.get("feasibility_assessment"):
            story.append(Spacer(1, 0.1 * inch))
            feasibility = tech["feasibility_assessment"]
            story.append(Paragraph(f"<b>Feasibility Score:</b> {feasibility.get('overall_score', 0):.1f}%", body_style))

        story.append(Spacer(1, 0.2 * inch))

        # 5-14. Remaining sections
        sections_data = [
            ("5. Coding Prompts", "coding_prompts", "Context-optimized coding prompts for AI agents"),
            ("6. Development Workflow", "development_workflow", None),
            ("7. Testing Strategy", "testing_strategy", None),
            ("8. Deployment Guide", "deployment_guide", None),
            ("9. Quality Standards", "quality_standards", None),
            ("10. Success Metrics", "success_metrics", None),
            ("11. Implementation Roadmap", "implementation_roadmap", None),
            ("12. Team Requirements", "team_requirements", None),
            ("13. Risk Mitigation", "risk_mitigation", None),
            ("14. Monitoring & Observability", "monitoring_and_observability", None),
        ]

        for section_title, section_key, placeholder_text in sections_data:
            section_data = playbook.get(section_key, {})
            story.append(Paragraph(section_title, heading1_style))
            story.append(Spacer(1, 0.1 * inch))

            if not section_data:
                story.append(Paragraph(placeholder_text or "No data available for this section", body_style))
            else:
                # Generic section rendering
                if isinstance(section_data, dict):
                    for key, value in list(section_data.items())[:15]:  # Limit entries
                        formatted_key = key.replace("_", " ").title()
                        if isinstance(value, (list, dict)):
                            story.append(Paragraph(f"<b>{formatted_key}:</b>", body_style))
                            if isinstance(value, list):
                                for item in value[:10]:
                                    item_text = str(item) if not isinstance(item, dict) else item.get("name", str(item))
                                    story.append(Paragraph(f"• {item_text}", bullet_style))
                            else:
                                for k, v in list(value.items())[:10]:
                                    story.append(Paragraph(f"• {k}: {v}", bullet_style))
                        else:
                            story.append(Paragraph(f"<b>{formatted_key}:</b> {value}", body_style))
                        story.append(Spacer(1, 0.05 * inch))

            story.append(Spacer(1, 0.2 * inch))

        # Footer with generation info
        story.append(PageBreak())
        story.append(Spacer(1, 3 * inch))
        story.append(Paragraph("Generated by Sutra Multi-LLM Prompt Studio", subtitle_style))
        story.append(
            Paragraph(f"Forge Implementation Playbook System v{metadata.get('forge_version', '1.0.0')}", subtitle_style)
        )
        story.append(Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), subtitle_style))

        # Build PDF
        doc.build(story)

        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()

        return pdf_content

    except ImportError as e:
        logger.error(f"reportlab not installed: {str(e)}")
        raise Exception("PDF export requires reportlab library. Install with: pip install reportlab")
    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}")
        raise Exception(f"PDF generation failed: {str(e)}")


def export_to_zip_archive(playbook: Dict) -> bytes:
    """Export playbook as comprehensive zip archive with multiple files"""
    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Main playbook JSON
        zip_file.writestr("playbook.json", json.dumps(playbook, indent=2))

        # Comprehensive Markdown documentation
        zip_file.writestr("IMPLEMENTATION_PLAYBOOK.md", export_to_markdown(playbook))

        # Individual section exports
        sections_to_export = [
            ("technical_architecture", "ARCHITECTURE.json"),
            ("testing_strategy", "TESTING_STRATEGY.json"),
            ("deployment_guide", "DEPLOYMENT_GUIDE.json"),
            ("implementation_roadmap", "ROADMAP.json"),
            ("team_requirements", "TEAM_REQUIREMENTS.json"),
            ("risk_mitigation", "RISK_MITIGATION.json"),
            ("monitoring_and_observability", "MONITORING.json"),
        ]

        for section_key, filename in sections_to_export:
            if section_key in playbook:
                zip_file.writestr(filename, json.dumps(playbook[section_key], indent=2))

        # README with usage instructions
        readme_content = f"""# Implementation Playbook Export

**Project:** {playbook.get('metadata', {}).get('project_id', 'Unknown')}
**Generated:** {playbook.get('metadata', {}).get('compilation_timestamp', 'N/A')}
**Quality Score:** {playbook.get('metadata', {}).get('context_quality_score', 0):.1f}%

## Contents

### Main Files
- `playbook.json` - Complete playbook in JSON format
- `IMPLEMENTATION_PLAYBOOK.md` - Comprehensive Markdown documentation

### Component Files
- `ARCHITECTURE.json` - Technical architecture details
- `TESTING_STRATEGY.json` - Complete testing strategy
- `DEPLOYMENT_GUIDE.json` - Deployment procedures
- `ROADMAP.json` - Implementation timeline and phases
- `TEAM_REQUIREMENTS.json` - Team structure and roles
- `RISK_MITIGATION.json` - Risk analysis and mitigation plans
- `MONITORING.json` - Monitoring and observability setup

## Usage

1. **For Development Teams**: Start with `IMPLEMENTATION_PLAYBOOK.md` for complete overview
2. **For Technical Leads**: Review `ARCHITECTURE.json` and `ROADMAP.json`
3. **For DevOps**: Focus on `DEPLOYMENT_GUIDE.json` and `MONITORING.json`
4. **For QA Teams**: Use `TESTING_STRATEGY.json` as testing blueprint
5. **For Project Managers**: Review `TEAM_REQUIREMENTS.json` and `RISK_MITIGATION.json`

## Integration

Import `playbook.json` into your project management or documentation system for full integration.

---

Generated by Sutra Multi-LLM Prompt Studio - Forge Implementation Playbook System
"""
        zip_file.writestr("README.md", readme_content)

    return buffer.getvalue()


async def validate_context_integration_endpoint(req: func.HttpRequest) -> func.HttpResponse:
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
        project_context = await get_complete_project_context(project_id)

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


# New enhanced helper functions for comprehensive playbook compilation


def validate_stage_completeness(project_context: Dict) -> Dict[str, Any]:
    """Validate that all required Forge stages are complete"""
    required_stages = ["idea_refinement", "prd_generation", "ux_requirements", "technical_analysis"]
    missing_stages = []

    for stage in required_stages:
        stage_data = project_context.get(stage, {})
        if not stage_data or not stage_data.get("completed", False):
            missing_stages.append(stage)

    return {
        "all_stages_complete": len(missing_stages) == 0,
        "missing_stages": missing_stages,
        "completed_stages": [s for s in required_stages if s not in missing_stages],
    }


def calculate_overall_context_quality(project_context: Dict) -> float:
    """Calculate overall quality score across all Forge stages"""
    quality_scores = []

    for stage_name in ["idea_refinement", "prd_generation", "ux_requirements", "technical_analysis"]:
        stage_data = project_context.get(stage_name, {})
        quality_score = stage_data.get("qualityScore", 0)
        if quality_score > 0:
            quality_scores.append(quality_score)

    return sum(quality_scores) / len(quality_scores) if quality_scores else 0


def generate_comprehensive_testing_strategy(project_context: Dict) -> Dict[str, Any]:
    """Generate comprehensive testing strategy based on full project context"""
    tech_analysis = project_context.get("technical_analysis", {})
    requirements = project_context.get("prd_generation", {})
    ux_specs = project_context.get("ux_requirements", {})

    return {
        "unit_testing": {
            "framework_recommendations": ["Jest", "Pytest", "JUnit"],
            "coverage_targets": {"minimum": 80, "target": 90, "excellent": 95},
            "testing_patterns": ["AAA Pattern", "Mock/Stub", "Test Doubles"],
            "automation_setup": ["CI/CD Integration", "Pre-commit Hooks"],
            "critical_components": extract_critical_components(tech_analysis),
        },
        "integration_testing": {
            "api_testing": ["Postman/Newman", "REST Assured", "Supertest"],
            "database_testing": ["Test Containers", "In-memory DB", "Fixtures"],
            "service_integration": ["WireMock", "Test Doubles", "Contract Testing"],
            "api_endpoints": extract_api_endpoints(requirements),
        },
        "e2e_testing": {
            "framework": "Playwright",
            "test_scenarios": extract_user_journeys(ux_specs),
            "browser_coverage": ["Chrome", "Firefox", "Safari"],
            "mobile_testing": True,
            "critical_paths": identify_critical_user_paths(ux_specs),
        },
        "performance_testing": {
            "load_testing": "Artillery/K6",
            "stress_testing": "JMeter",
            "metrics": ["Response Time", "Throughput", "Error Rate"],
            "targets": extract_performance_targets(tech_analysis),
        },
        "security_testing": {
            "vulnerability_scanning": "OWASP ZAP",
            "dependency_scanning": "npm audit / pip-audit",
            "authentication_testing": "JWT Validation",
            "authorization_testing": "Role-based Access",
            "security_requirements": extract_security_requirements(tech_analysis),
        },
        "accessibility_testing": {
            "automated_testing": "axe-core",
            "manual_testing": "Screen Reader Testing",
            "compliance_target": ux_specs.get("accessibility", {}).get("compliance", "WCAG 2.1 AA"),
            "tools": ["Lighthouse", "WAVE", "Color Contrast Analyzer"],
        },
        "qa_procedures": {
            "code_review_process": "Pull Request Reviews",
            "testing_phases": ["Unit", "Integration", "E2E", "UAT"],
            "quality_gates": ["Code Coverage", "Security Scan", "Performance"],
            "release_criteria": ["All Tests Pass", "Security Clear", "Performance OK"],
        },
    }


def generate_comprehensive_deployment_guide(project_context: Dict) -> Dict[str, Any]:
    """Generate comprehensive deployment guide with full context"""
    tech_analysis = project_context.get("technical_analysis", {})
    tech_stack = tech_analysis.get("technology_stack", {})

    return {
        "environment_setup": {
            "development": {
                "prerequisites": extract_development_prerequisites(tech_stack),
                "setup_commands": generate_setup_commands(tech_stack),
                "environment_variables": extract_environment_variables(tech_analysis),
            },
            "staging": {
                "infrastructure": tech_stack.get("infrastructure", {}).get("name", "Cloud Platform"),
                "configuration": "staging.env",
                "deployment": "CI/CD Pipeline",
            },
            "production": {
                "infrastructure": tech_stack.get("infrastructure", {}).get("name", "Cloud Platform"),
                "configuration": "production.env",
                "deployment": "Blue-Green Deployment",
            },
        },
        "build_procedures": generate_build_procedures_from_context(tech_stack),
        "deployment_steps": generate_deployment_steps_from_context(tech_analysis),
        "monitoring_setup": {
            "application_monitoring": "Application Insights / New Relic",
            "infrastructure_monitoring": "Cloud Provider Monitoring",
            "log_aggregation": "ELK Stack / Cloud Logging",
            "alerts": extract_alert_requirements(tech_analysis),
        },
        "backup_procedures": {
            "database_backups": "Daily automated backups with 30-day retention",
            "file_storage_backups": "Incremental backups",
            "configuration_backups": "Git repository",
            "recovery_procedures": "Documented restore steps with RTO/RPO",
        },
        "rollback_procedures": {
            "database_rollback": "Migration rollback scripts",
            "application_rollback": "Previous container version / deployment slot",
            "configuration_rollback": "Git revert",
            "verification": "Health checks and smoke tests",
        },
        "security_configurations": extract_security_configurations(tech_analysis),
    }


def generate_implementation_roadmap(project_context: Dict) -> Dict[str, Any]:
    """Generate detailed implementation roadmap"""
    feasibility = project_context.get("technical_analysis", {}).get("feasibility_assessment", {})

    timeline_weeks = feasibility.get("estimated_timeline_weeks", 12)
    team_size = feasibility.get("recommended_team_size", 3)

    return {
        "total_timeline_weeks": timeline_weeks,
        "phases": [
            {
                "phase": 1,
                "name": "Foundation Setup",
                "duration_weeks": max(2, int(timeline_weeks * 0.15)),
                "deliverables": ["Project structure", "Core architecture", "Development environment"],
                "team_focus": "Full team collaboration",
            },
            {
                "phase": 2,
                "name": "Core Development",
                "duration_weeks": max(4, int(timeline_weeks * 0.45)),
                "deliverables": ["Main functionality", "API development", "Database implementation"],
                "team_focus": "Parallel frontend/backend development",
            },
            {
                "phase": 3,
                "name": "Integration & Testing",
                "duration_weeks": max(2, int(timeline_weeks * 0.25)),
                "deliverables": ["System integration", "Testing and QA", "Performance optimization"],
                "team_focus": "Full team integration",
            },
            {
                "phase": 4,
                "name": "Deployment & Launch",
                "duration_weeks": max(1, int(timeline_weeks * 0.15)),
                "deliverables": ["Production deployment", "Documentation", "Launch preparation"],
                "team_focus": "DevOps and testing focus",
            },
        ],
        "milestones": generate_milestones_from_requirements(project_context),
        "dependencies": identify_critical_dependencies(project_context),
    }


def generate_team_requirements(project_context: Dict) -> Dict[str, Any]:
    """Generate team structure and skill requirements"""
    feasibility = project_context.get("technical_analysis", {}).get("feasibility_assessment", {})
    tech_stack = project_context.get("technical_analysis", {}).get("technology_stack", {})

    return {
        "recommended_team_size": feasibility.get("recommended_team_size", 3),
        "key_roles": [
            {
                "role": "Frontend Developer",
                "skills": [tech_stack.get("frontend", {}).get("name", "React"), "TypeScript", "UI/UX Implementation"],
                "count": 1,
            },
            {
                "role": "Backend Developer",
                "skills": [tech_stack.get("backend", {}).get("name", "Python"), "API Development", "Database Design"],
                "count": 1,
            },
            {
                "role": "DevOps Engineer",
                "skills": ["CI/CD", tech_stack.get("infrastructure", {}).get("name", "Cloud"), "Monitoring"],
                "count": 1,
            },
        ],
        "skill_requirements": feasibility.get("skill_requirements", []),
        "team_structure": "Cross-functional agile team",
        "collaboration_tools": ["Git", "Slack/Teams", "Jira/Linear", "Figma"],
    }


def generate_risk_mitigation_plan(project_context: Dict) -> Dict[str, Any]:
    """Generate comprehensive risk mitigation plan"""
    risk_analysis = project_context.get("technical_analysis", {}).get("risk_analysis", {})

    return {
        "risk_categories": risk_analysis.get("risk_categories", {}),
        "top_risks": risk_analysis.get("top_risks", []),
        "mitigation_priority": risk_analysis.get("risk_mitigation_priority", []),
        "monitoring_recommendations": risk_analysis.get("monitoring_recommendations", []),
        "contingency_plans": generate_contingency_plans(risk_analysis),
        "escalation_procedures": "Project lead → Technical lead → Stakeholders",
    }


def generate_monitoring_strategy(project_context: Dict) -> Dict[str, Any]:
    """Generate monitoring and observability strategy"""
    tech_analysis = project_context.get("technical_analysis", {})

    return {
        "application_monitoring": {
            "metrics": ["Response time", "Error rate", "Throughput", "Availability"],
            "tools": ["Application Insights", "New Relic", "Datadog"],
            "dashboards": ["System health", "User activity", "Performance metrics"],
        },
        "infrastructure_monitoring": {
            "metrics": ["CPU", "Memory", "Disk", "Network"],
            "tools": ["Cloud provider monitoring", "Prometheus", "Grafana"],
            "alerts": ["Resource utilization", "Service health", "Cost anomalies"],
        },
        "log_management": {
            "aggregation": "Centralized logging system",
            "retention": "30 days hot, 1 year archive",
            "analysis": "Log analytics and pattern detection",
        },
        "alerting": {
            "critical": ["Service down", "Data loss", "Security breach"],
            "warning": ["High latency", "Resource pressure", "Cost threshold"],
            "info": ["Deployment", "Configuration change", "Usage milestone"],
        },
    }


def calculate_playbook_quality(playbook: Dict, validation_result: Dict) -> Dict[str, Any]:
    """Calculate comprehensive playbook quality score"""
    quality_dimensions = {
        "completeness": calculate_completeness_score(playbook),
        "context_integration": validation_result.get("overall_score", 0),
        "technical_depth": calculate_technical_depth(playbook),
        "actionability": calculate_actionability_score(playbook),
        "clarity": calculate_clarity_score(playbook),
    }

    overall_score = sum(quality_dimensions.values()) / len(quality_dimensions)

    return {
        "overall_score": round(overall_score, 2),
        "dimensions": quality_dimensions,
        "grade": get_quality_grade(overall_score),
        "ready_for_implementation": overall_score >= 85,
    }


async def save_implementation_playbook(project_id: str, playbook: Dict, user_info: Dict, quality: Dict) -> Dict[str, Any]:
    """Save implementation playbook to database with quality metadata"""
    try:
        async with AsyncCosmosHelper() as db:
            try:
                project_doc = await db.read_item(project_id, partition_key=project_id)
                project_doc["implementationData"] = {
                    "playbook": playbook,
                    "quality": quality,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "generated_by": user_info.get("user_id"),
                    "version": "1.0.0",
                }
                project_doc["lastModified"] = datetime.now(timezone.utc).isoformat()

                await db.upsert_item(project_doc)

                logger.info(f"Successfully saved implementation playbook for project {project_id}")
                return {"success": True, "message": "Playbook saved successfully"}

            except CosmosResourceNotFoundError:
                logger.error(f"Project {project_id} not found")
                return {"success": False, "error": "Project not found"}

    except Exception as e:
        logger.error(f"Error saving playbook: {str(e)}")
        return {"success": False, "error": str(e)}


# Additional extraction helper functions


def extract_critical_components(tech_analysis: Dict) -> List[str]:
    """Extract critical components from technical analysis"""
    components = []
    arch = tech_analysis.get("architecture_recommendation", {})
    if isinstance(arch, dict) and "components" in arch:
        components = arch.get("components", [])[:5]  # Top 5 critical components
    return components if components else ["Authentication", "Data Layer", "API Layer", "UI Components"]


def extract_api_endpoints(requirements: Dict) -> List[Dict]:
    """Extract API endpoints from requirements"""
    endpoints = requirements.get("api_requirements", [])
    if not endpoints:
        endpoints = requirements.get("requirements", {}).get("apiRequirements", [])
    return endpoints[:10] if endpoints else []  # Top 10 endpoints


def extract_user_journeys(ux_specs: Dict) -> List[str]:
    """Extract user journeys for E2E testing"""
    journeys = ux_specs.get("userJourneys", {}).get("journeys", [])
    return [j.get("name", f"Journey {i+1}") for i, j in enumerate(journeys[:5])]


def identify_critical_user_paths(ux_specs: Dict) -> List[str]:
    """Identify critical user paths"""
    journeys = ux_specs.get("userJourneys", {}).get("journeys", [])
    critical = [j.get("name") for j in journeys if j.get("importance") == "critical"]
    return critical if critical else ["User Registration", "Core Feature Usage", "Checkout Flow"]


def extract_performance_targets(tech_analysis: Dict) -> Dict[str, Any]:
    """Extract performance targets"""
    return {"response_time_ms": 300, "concurrent_users": 1000, "throughput_rps": 100, "availability_percent": 99.9}


def extract_security_requirements(tech_analysis: Dict) -> List[str]:
    """Extract security requirements"""
    risk_analysis = tech_analysis.get("risk_analysis", {})
    security_risks = risk_analysis.get("risk_categories", {}).get("security", {})
    return [security_risks.get("mitigation", "Implement standard security measures")]


def extract_development_prerequisites(tech_stack: Dict) -> List[str]:
    """Extract development prerequisites"""
    prereqs = []
    if tech_stack.get("frontend", {}).get("name"):
        prereqs.append(f"{tech_stack['frontend']['name']} development environment")
    if tech_stack.get("backend", {}).get("name"):
        prereqs.append(f"{tech_stack['backend']['name']} runtime")
    prereqs.extend(["Git", "Docker", "IDE/Editor"])
    return prereqs


def generate_setup_commands(tech_stack: Dict) -> List[str]:
    """Generate setup commands"""
    commands = []
    frontend = tech_stack.get("frontend", {}).get("name", "").lower()
    backend = tech_stack.get("backend", {}).get("name", "").lower()

    if "react" in frontend or "vue" in frontend or "angular" in frontend:
        commands.append("npm install")
    if "python" in backend:
        commands.append("pip install -r requirements.txt")
    elif "node" in backend:
        commands.append("npm install")

    commands.append("docker-compose up -d")
    return commands if commands else ["npm install", "pip install -r requirements.txt"]


def extract_environment_variables(tech_analysis: Dict) -> List[str]:
    """Extract required environment variables"""
    return ["DATABASE_URL", "API_KEY", "SECRET_KEY", "ENVIRONMENT"]


def generate_build_procedures_from_context(tech_stack: Dict) -> Dict[str, List[str]]:
    """Generate build procedures from context"""
    return {
        "frontend_build": ["npm run build", "npm run test", "npm run lint"],
        "backend_build": ["pytest", "flake8", "mypy"],
        "containerization": ["docker build", "docker test", "docker push"],
    }


def generate_deployment_steps_from_context(tech_analysis: Dict) -> List[Dict]:
    """Generate deployment steps from context"""
    return [
        {"step": 1, "action": "Build and test", "command": "npm run build && npm test"},
        {"step": 2, "action": "Create container", "command": "docker build -t app:latest ."},
        {"step": 3, "action": "Push to registry", "command": "docker push registry/app:latest"},
        {"step": 4, "action": "Deploy", "command": "kubectl apply -f deployment.yaml"},
        {"step": 5, "action": "Health check", "command": "curl /health"},
        {"step": 6, "action": "Smoke tests", "command": "npm run test:e2e"},
    ]


def extract_alert_requirements(tech_analysis: Dict) -> List[str]:
    """Extract alert requirements"""
    return ["High Error Rate", "High Response Time", "Low Availability", "Security Incidents"]


def extract_security_configurations(tech_analysis: Dict) -> Dict[str, str]:
    """Extract security configurations"""
    return {
        "authentication": "JWT/OAuth 2.0",
        "authorization": "Role-based access control (RBAC)",
        "encryption": "TLS 1.3 for transport, AES-256 for data at rest",
        "security_headers": "CSP, HSTS, X-Frame-Options, X-Content-Type-Options",
    }


def generate_milestones_from_requirements(project_context: Dict) -> List[Dict]:
    """Generate milestones from requirements"""
    return [
        {"milestone": "MVP Complete", "week": 6, "deliverables": ["Core features", "Basic UI", "API"]},
        {"milestone": "Beta Release", "week": 9, "deliverables": ["All features", "Testing", "Documentation"]},
        {"milestone": "Production Launch", "week": 12, "deliverables": ["Deployment", "Monitoring", "Support"]},
    ]


def identify_critical_dependencies(project_context: Dict) -> List[Dict]:
    """Identify critical dependencies"""
    return [
        {"dependency": "Authentication Service", "impact": "High", "mitigation": "Early implementation"},
        {"dependency": "Database Schema", "impact": "High", "mitigation": "Complete design first"},
        {"dependency": "API Contracts", "impact": "Medium", "mitigation": "OpenAPI specification"},
    ]


def generate_contingency_plans(risk_analysis: Dict) -> List[Dict]:
    """Generate contingency plans"""
    return [
        {"risk": "Technical complexity", "plan": "Incremental development with frequent validation"},
        {"risk": "Resource constraints", "plan": "Prioritize MVP features, defer nice-to-haves"},
        {"risk": "Timeline pressure", "plan": "Agile sprints with adjustable scope"},
    ]


def calculate_completeness_score(playbook: Dict) -> float:
    """Calculate playbook completeness score"""
    required_sections = [
        "project_overview",
        "requirements_summary",
        "technical_architecture",
        "coding_prompts",
        "development_workflow",
        "testing_strategy",
        "deployment_guide",
    ]
    present_sections = sum(1 for section in required_sections if playbook.get(section))
    return (present_sections / len(required_sections)) * 100


def calculate_technical_depth(playbook: Dict) -> float:
    """Calculate technical depth score"""
    tech_arch = playbook.get("technical_architecture", {})
    depth_indicators = ["architecture_recommendation", "technology_stack", "feasibility_assessment", "risk_analysis"]
    present_indicators = sum(1 for indicator in depth_indicators if tech_arch.get(indicator))
    return (present_indicators / len(depth_indicators)) * 100


def calculate_actionability_score(playbook: Dict) -> float:
    """Calculate actionability score"""
    actionable_sections = ["coding_prompts", "development_workflow", "testing_strategy", "deployment_guide"]
    action_scores = []
    for section in actionable_sections:
        section_data = playbook.get(section, {})
        if section_data and len(str(section_data)) > 100:  # Has substantial content
            action_scores.append(100)
        else:
            action_scores.append(0)
    return sum(action_scores) / len(action_scores) if action_scores else 0


def calculate_clarity_score(playbook: Dict) -> float:
    """Calculate clarity score"""
    # Simple heuristic: check if key sections have structured data
    clarity_indicators = 0
    total_indicators = 0

    for key, value in playbook.items():
        if isinstance(value, dict) and value:
            total_indicators += 1
            if len(value) >= 3:  # Has at least 3 subsections
                clarity_indicators += 1

    return (clarity_indicators / total_indicators * 100) if total_indicators > 0 else 50


def get_quality_grade(score: float) -> str:
    """Get quality grade from score"""
    if score >= 95:
        return "A+"
    elif score >= 90:
        return "A"
    elif score >= 85:
        return "B+"
    elif score >= 80:
        return "B"
    elif score >= 75:
        return "C+"
    elif score >= 70:
        return "C"
    else:
        return "D"
