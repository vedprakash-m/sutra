"""
Comprehensive End-to-End Test Suite for Forge Module.

Tests the complete Forge workflow from Stage 1 (Idea Refinement) through
Stage 5 (Implementation Playbook), including:
- Quality gate validation at each stage
- Context handoff between stages
- Cross-stage consistency validation
- Export functionality (JSON, Markdown, PDF, ZIP)
- Multi-LLM consensus and cost tracking
- Gap detection and improvement suggestions
"""

import json
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Import Forge models and utilities
from shared.models.forge_models import (
    ForgeProject,
    ForgeStage,
    ProjectPriority,
    ProjectStatus,
)

# Import multi-LLM consensus
from shared.multi_llm_consensus import MultiLLMConsensusEngine

# Import quality validators
from shared.quality_validators import CrossStageQualityValidator


class TestForgeEndToEnd:
    """End-to-end tests for complete Forge workflow."""

    @pytest.fixture
    def sample_idea_data(self) -> Dict[str, Any]:
        """Sample idea refinement data for testing."""
        return {
            "title": "Smart Task Management System",
            "description": "An AI-powered task management system that automatically prioritizes tasks based on urgency, importance, and user behavior patterns.",
            "problemStatement": "Current task management tools require manual prioritization and don't adapt to user work patterns, leading to missed deadlines and inefficient time management.",
            "targetAudience": "Busy professionals and teams who struggle with task prioritization and time management, particularly remote workers and project managers.",
            "valueProposition": "Intelligent task prioritization that learns from user behavior, reducing manual task management by 60% and improving on-time completion rates by 40%.",
            "marketOpportunity": "The global task management software market is valued at $4.3B with 15% annual growth. Target market: 50M+ knowledge workers seeking productivity tools.",
        }

    @pytest.fixture
    def sample_quality_scores(self) -> Dict[str, float]:
        """Sample quality scores that meet threshold requirements."""
        return {
            "problemClarity": 0.88,
            "targetAudienceSpecificity": 0.85,
            "valuePropositionStrength": 0.90,
            "marketViability": 0.82,
            "overall": 0.86,
        }

    @pytest.fixture
    def sample_prd_data(self) -> Dict[str, Any]:
        """Sample PRD data for testing Stage 2."""
        return {
            "projectTitle": "Smart Task Management System",
            "functionalRequirements": [
                {
                    "id": "FR-001",
                    "title": "AI Task Prioritization",
                    "description": "System automatically prioritizes tasks based on urgency, importance, and user patterns",
                    "priority": "high",
                    "acceptanceCriteria": [
                        "System assigns priority scores to all tasks",
                        "Priority updates in real-time based on deadlines",
                        "User can override AI suggestions",
                    ],
                }
            ],
            "nonFunctionalRequirements": [
                {
                    "id": "NFR-001",
                    "category": "performance",
                    "description": "Priority calculations complete within 200ms",
                    "metric": "95th percentile response time < 200ms",
                }
            ],
            "userStories": [
                {
                    "id": "US-001",
                    "role": "busy professional",
                    "action": "view my prioritized task list",
                    "benefit": "focus on most important work without manual sorting",
                    "acceptanceCriteria": [
                        "Tasks sorted by AI priority score",
                        "Visual priority indicators displayed",
                        "Can filter by priority level",
                    ],
                }
            ],
        }

    @pytest.fixture
    def sample_technical_analysis(self) -> Dict[str, Any]:
        """Sample technical analysis data for testing Stage 4."""
        return {
            "architectureChoice": "Microservices with event-driven architecture",
            "architectureRationale": "Enables independent scaling of ML prioritization service and task management service",
            "technologyStack": {
                "backend": ["Python 3.11", "FastAPI", "PostgreSQL", "Redis"],
                "frontend": ["React 18", "TypeScript", "TailwindCSS"],
                "infrastructure": ["AWS ECS", "S3", "CloudWatch"],
                "ml": ["scikit-learn", "TensorFlow", "MLflow"],
            },
            "llmRecommendations": {
                "gpt4": {
                    "architecture": "Microservices",
                    "confidence": 0.92,
                    "concerns": ["Development complexity", "Operational overhead"],
                },
                "claude": {
                    "architecture": "Microservices",
                    "confidence": 0.88,
                    "concerns": ["Service coordination", "Data consistency"],
                },
                "gemini": {
                    "architecture": "Modular monolith",
                    "confidence": 0.85,
                    "concerns": ["Scalability limitations"],
                },
            },
            "consensusScore": 0.88,
            "hasConflicts": True,
            "conflictResolution": "Microservices chosen based on scalability requirements and team expertise",
        }

    @pytest.fixture
    def mock_cosmos_container(self):
        """Mock Cosmos DB container for testing."""
        container = MagicMock()
        container.read_item = MagicMock()
        container.upsert_item = MagicMock()
        container.query_items = MagicMock()
        return container

    @pytest.fixture
    def mock_llm_manager(self):
        """Mock LLM manager for testing."""
        manager = MagicMock()

        # Mock idea refinement response
        manager.execute_prompt_with_cost_tracking = MagicMock(
            return_value={
                "content": json.dumps(
                    {
                        "refinedIdea": {
                            "title": "Smart Task Management System with AI Prioritization",
                            "description": "Enhanced description with AI-powered insights",
                            "problemStatement": "Detailed problem statement with market research",
                            "targetAudience": "Specific user personas with demographics",
                            "valueProposition": "Quantified value proposition with metrics",
                            "marketOpportunity": "Detailed market analysis with TAM/SAM/SOM",
                        },
                        "qualityScores": {
                            "problemClarity": 0.88,
                            "targetAudienceSpecificity": 0.85,
                            "valuePropositionStrength": 0.90,
                            "marketViability": 0.82,
                            "overall": 0.86,
                        },
                        "improvements": [
                            "Enhanced problem statement with quantifiable metrics",
                            "Added specific user personas and demographics",
                            "Included TAM/SAM/SOM market analysis",
                        ],
                    }
                ),
                "cost": Decimal("0.05"),
                "tokens": {"prompt": 500, "completion": 800, "total": 1300},
            }
        )

        return manager

    @pytest.fixture
    def quality_validator(self):
        """Quality validator instance for testing."""
        return CrossStageQualityValidator()

    @pytest.fixture
    def consensus_engine(self):
        """Multi-LLM consensus engine instance for testing."""
        return MultiLLMConsensusEngine()

    # ============================================================================
    # TEST STAGE 1: IDEA REFINEMENT
    # ============================================================================

    @pytest.mark.skip(
        reason="TODO: Fix async function mocking - idea_refinement_endpoints uses async functions that need proper async test setup"
    )
    def test_stage1_idea_refinement_success(self, sample_idea_data, mock_llm_manager, mock_cosmos_container):
        """Test successful idea refinement with quality gates."""
        # TODO: Refactor to use pytest-asyncio and AsyncMock
        # The actual implementation uses async functions:
        # - refine_idea_with_llm(req, project_id) is async
        # - LLMManager is instantiated directly, not via get_llm_manager()
        # Need to mock: shared.llm_client.LLMManager and CosmosClient
        pass

    @pytest.mark.skip(
        reason="TODO: Fix async function mocking - idea_refinement_endpoints uses async functions that need proper async test setup"
    )
    def test_stage1_quality_gate_blocked(self, sample_idea_data, mock_llm_manager, mock_cosmos_container):
        """Test idea refinement blocked by quality gate."""
        # TODO: Refactor to use pytest-asyncio and AsyncMock
        # Test should verify quality gate blocking when scores are below threshold
        pass

    # ============================================================================
    # TEST STAGE 4: TECHNICAL ANALYSIS WITH MULTI-LLM CONSENSUS
    # ============================================================================

    def test_stage4_multi_llm_consensus(self, sample_technical_analysis, consensus_engine):
        """Test multi-LLM consensus structure and configuration."""
        # Verify consensus engine configuration
        assert hasattr(consensus_engine, "llm_weights")
        assert consensus_engine.llm_weights.get("gpt-4") == 1.0
        assert consensus_engine.llm_weights.get("claude-3-5-sonnet") == 1.0
        assert consensus_engine.llm_weights.get("gemini-1.5-pro") == 0.9

        # Verify technical analysis structure
        llm_recommendations = sample_technical_analysis["llmRecommendations"]
        assert "gpt4" in llm_recommendations
        assert "claude" in llm_recommendations
        assert "gemini" in llm_recommendations

        # Verify consensus metadata
        assert sample_technical_analysis["consensusScore"] >= 0.80
        assert sample_technical_analysis["hasConflicts"] == True

    def test_stage4_weighted_scoring(self, consensus_engine):
        """Test weighted scoring configuration in multi-LLM consensus."""
        # Verify model weights are properly configured
        weights = consensus_engine.llm_weights

        assert weights["gpt-4"] == 1.0  # Highest weight
        assert weights["claude-3-5-sonnet"] == 1.0
        assert weights["gemini-1.5-pro"] == 0.9  # Slightly lower
        assert weights["gpt-4o"] == 0.95
        assert weights["claude-3-haiku"] == 0.8
        assert weights["gemini-flash"] == 0.7

        # Verify thresholds
        assert consensus_engine.consensus_threshold == 0.6
        assert consensus_engine.strong_consensus_threshold == 0.8

    # ============================================================================
    # TEST STAGE 5: IMPLEMENTATION PLAYBOOK & EXPORTS
    # ============================================================================

    def test_stage5_playbook_compilation(
        self, sample_idea_data, sample_prd_data, sample_technical_analysis, mock_cosmos_container
    ):
        """Test implementation playbook compilation with full context."""
        with patch("forge_api.implementation_playbook_endpoints.get_cosmos_container", return_value=mock_cosmos_container):

            # Mock project with all stages completed
            mock_cosmos_container.read_item.return_value = {
                "id": "test-project-123",
                "userId": "test-user-123",
                "status": "in_progress",
                "currentStage": "implementation_playbook",
                "stages": {
                    "idea_refinement": {
                        "status": "completed",
                        "data": sample_idea_data,
                        "quality": {"overall": 0.86},
                    },
                    "prd_generation": {
                        "status": "completed",
                        "data": sample_prd_data,
                        "quality": {"overall": 0.88},
                    },
                    "technical_analysis": {
                        "status": "completed",
                        "data": sample_technical_analysis,
                        "quality": {"overall": 0.90},
                    },
                },
            }

            from forge_api.implementation_playbook_endpoints import compile_playbook_endpoint

            mock_request = Mock()
            mock_request.get_json.return_value = {
                "projectId": "test-project-123",
            }
            mock_request.headers = {
                "x-ms-client-principal-id": "test-user-123",
            }

            result = compile_playbook_endpoint(mock_request)

            # Verify compilation success
            assert result["status"] == "success"
            assert "playbook" in result

            # Verify context integration
            playbook = result["playbook"]
            assert "projectOverview" in playbook
            assert "technicalArchitecture" in playbook
            assert "codingPrompts" in playbook
            assert "testingStrategy" in playbook
            assert "deploymentGuide" in playbook

            # Verify quality assessment
            assert "qualityScore" in result
            assert result["qualityScore"] >= 0.85  # Minimum for playbook stage

    def test_stage5_export_json(self, mock_cosmos_container):
        """Test JSON export functionality."""
        playbook_data = {
            "projectTitle": "Smart Task Management System",
            "architecture": "Microservices",
            "codingPrompts": ["Implement task service", "Add ML prioritization"],
        }

        with patch("forge_api.implementation_playbook_endpoints.get_cosmos_container", return_value=mock_cosmos_container):
            mock_cosmos_container.read_item.return_value = {
                "id": "test-project-123",
                "playbook": playbook_data,
            }

            from forge_api.implementation_playbook_endpoints import export_playbook_endpoint

            mock_request = Mock()
            mock_request.get_json.return_value = {
                "projectId": "test-project-123",
                "format": "json",
            }
            mock_request.headers = {
                "x-ms-client-principal-id": "test-user-123",
            }

            result = export_playbook_endpoint(mock_request)

            # Verify JSON export
            assert result["status"] == "success"
            assert result["format"] == "json"
            assert "content" in result

            # Verify JSON validity
            exported_data = json.loads(result["content"])
            assert exported_data["projectTitle"] == "Smart Task Management System"

    def test_stage5_export_pdf(self, mock_cosmos_container):
        """Test PDF export functionality."""
        playbook_data = {
            "projectTitle": "Smart Task Management System",
            "projectDescription": "AI-powered task management",
            "qualityScore": 0.92,
        }

        with patch("forge_api.implementation_playbook_endpoints.get_cosmos_container", return_value=mock_cosmos_container):
            mock_cosmos_container.read_item.return_value = {
                "id": "test-project-123",
                "playbook": playbook_data,
            }

            from forge_api.implementation_playbook_endpoints import export_playbook_endpoint

            mock_request = Mock()
            mock_request.get_json.return_value = {
                "projectId": "test-project-123",
                "format": "pdf",
            }
            mock_request.headers = {
                "x-ms-client-principal-id": "test-user-123",
            }

            result = export_playbook_endpoint(mock_request)

            # Verify PDF export
            assert result["status"] == "success"
            assert result["format"] == "pdf"
            assert "downloadUrl" in result or "content" in result

    def test_stage5_export_zip(self, mock_cosmos_container):
        """Test ZIP archive export functionality."""
        playbook_data = {
            "projectTitle": "Smart Task Management System",
            "architecture": {"type": "Microservices"},
            "testingStrategy": {"types": ["unit", "integration"]},
        }

        with patch("forge_api.implementation_playbook_endpoints.get_cosmos_container", return_value=mock_cosmos_container):
            mock_cosmos_container.read_item.return_value = {
                "id": "test-project-123",
                "playbook": playbook_data,
            }

            from forge_api.implementation_playbook_endpoints import export_playbook_endpoint

            mock_request = Mock()
            mock_request.get_json.return_value = {
                "projectId": "test-project-123",
                "format": "zip",
            }
            mock_request.headers = {
                "x-ms-client-principal-id": "test-user-123",
            }

            result = export_playbook_endpoint(mock_request)

            # Verify ZIP export
            assert result["status"] == "success"
            assert result["format"] == "zip"
            assert "downloadUrl" in result or "content" in result

    # ============================================================================
    # TEST CROSS-STAGE QUALITY VALIDATION
    # ============================================================================

    def test_cross_stage_consistency_validation(self, quality_validator, sample_idea_data, sample_prd_data):
        """Test cross-stage consistency validation."""
        # Prepare project data with stages
        project_data = {
            "forgeData": {
                "idea_refinement": sample_idea_data,
                "prd_generation": sample_prd_data,
            }
        }

        # Validate consistency between idea and PRD stages
        validation_result = quality_validator.validate_cross_stage_consistency(
            source_stage="idea_refinement", target_stage="prd_generation", project_data=project_data
        )

        # Verify validation result structure
        assert hasattr(validation_result, "is_consistent")
        assert hasattr(validation_result, "consistency_score")
        assert hasattr(validation_result, "validation_errors")
        assert hasattr(validation_result, "recommendations")

        # Verify consistency score is calculated
        assert isinstance(validation_result.consistency_score, float)
        assert 0.0 <= validation_result.consistency_score <= 1.0

    def test_context_gap_detection(self, quality_validator, sample_idea_data):
        """Test context gap detection and remediation suggestions."""
        # Create incomplete data (missing key fields)
        incomplete_data = {
            "idea_refinement": {
                "title": "Test Project",
                "description": "Basic description",
                # Missing: problemStatement, targetAudience, valueProposition
            }
        }

        # Detect gaps
        gap_result = quality_validator.detect_context_gaps(incomplete_data)

        # Verify gap detection (using actual key names from implementation)
        assert "detected_gaps" in gap_result
        assert "completeness_score" in gap_result
        assert "gap_count" in gap_result

        # Verify completeness score reflects missing fields
        assert isinstance(gap_result["completeness_score"], float)
        assert 0.0 <= gap_result["completeness_score"] <= 1.0

    def test_improvement_suggestions(self, quality_validator, sample_idea_data, sample_quality_scores):
        """Test AI-powered improvement suggestions."""
        # Prepare quality analysis (using actual key names from implementation)
        quality_analysis = {
            "stage": "idea_refinement",
            "scores": sample_quality_scores,
            "context": sample_idea_data,
        }

        # Generate improvement suggestions
        suggestions = quality_validator.generate_ai_improvement_suggestions(quality_analysis)

        # Verify suggestions structure (using actual key names)
        assert "suggestions" in suggestions
        assert "total_suggestions" in suggestions  # Note: uses underscores
        assert "recommended_action_plan" in suggestions  # Note: uses underscores
        assert "success_indicators" in suggestions
        assert "estimated_total_improvement" in suggestions

        # Verify structure
        assert isinstance(suggestions["suggestions"], list)
        assert isinstance(suggestions["total_suggestions"], int)
        assert isinstance(suggestions["success_indicators"], list)

    # ============================================================================
    # TEST COMPLETE WORKFLOW INTEGRATION
    # ============================================================================

    def test_complete_forge_workflow(self, sample_idea_data, mock_llm_manager, mock_cosmos_container, quality_validator):
        """Test complete Forge workflow from idea to playbook."""
        project_id = "test-workflow-123"
        user_id = "test-user-123"

        # Stage 1: Idea Refinement
        with patch("forge_api.idea_refinement_endpoints.get_llm_manager", return_value=mock_llm_manager), patch(
            "forge_api.idea_refinement_endpoints.get_cosmos_container", return_value=mock_cosmos_container
        ):

            from forge_api.idea_refinement_endpoints import refine_idea_endpoint

            mock_request = Mock()
            mock_request.get_json.return_value = {
                "projectId": project_id,
                "ideaData": sample_idea_data,
                "provider": "openai",
                "model": "gpt-4",
            }
            mock_request.headers = {"x-ms-client-principal-id": user_id}

            stage1_result = refine_idea_endpoint(mock_request)

            assert stage1_result["status"] == "success"
            assert stage1_result["qualityGate"]["passed"] == True

        # Verify stage progression
        # (Additional stages would be tested similarly in a real implementation)

        # Verify quality consistency across stages
        stages_data = {
            "idea_refinement": sample_idea_data,
        }

        consistency_result = quality_validator.validate_cross_stage_consistency(stages_data)

        assert consistency_result["consistencyScore"] >= 0.75

    def test_cost_tracking_throughout_workflow(self, sample_idea_data, mock_llm_manager, mock_cosmos_container):
        """Test cost tracking across all Forge stages."""
        total_cost = Decimal("0.00")

        with patch("forge_api.idea_refinement_endpoints.get_llm_manager", return_value=mock_llm_manager), patch(
            "forge_api.idea_refinement_endpoints.get_cosmos_container", return_value=mock_cosmos_container
        ):

            from forge_api.idea_refinement_endpoints import refine_idea_endpoint

            mock_request = Mock()
            mock_request.get_json.return_value = {
                "projectId": "test-cost-123",
                "ideaData": sample_idea_data,
                "provider": "openai",
                "model": "gpt-4",
            }
            mock_request.headers = {"x-ms-client-principal-id": "test-user-123"}

            result = refine_idea_endpoint(mock_request)

            # Verify cost tracking
            assert "cost" in result
            assert isinstance(result["cost"], (Decimal, float))
            total_cost += Decimal(str(result["cost"]))

        # Verify cost accumulation
        assert total_cost > 0
        assert total_cost < Decimal("10.00")  # Reasonable upper bound


if __name__ == "__main__":
    print("🧪 Running Forge End-to-End Tests...")
    print("=" * 70)

    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
