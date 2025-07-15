"""
Test suite for Idea Refinement Stage API endpoints and quality assessment.
Validates multi-dimensional quality scoring, LLM integration, and stage progression logic.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from api.forge_api.idea_refinement_endpoints import (
    analyze_idea, refine_idea_with_llm, get_quality_assessment, complete_stage
)
from api.shared.quality_engine import QualityAssessmentEngine, ContextualQualityValidator


class MockHttpRequest:
    """Mock Azure Functions HttpRequest for testing"""
    def __init__(self, method='POST', body=None, route_params=None, headers=None):
        self.method = method
        self._body = body or {}
        self.route_params = route_params or {}
        self.headers = headers or {}
    
    def get_body(self):
        return json.dumps(self._body).encode('utf-8')


@pytest.fixture
def mock_user_info():
    return {
        'user_id': 'test-user-123',
        'organization_id': 'test-org-456',
        'role': 'developer'
    }


@pytest.fixture
def sample_idea_data():
    return {
        'initialIdea': 'A marketplace app that connects local farmers with consumers',
        'problemStatement': 'Consumers want fresh, local produce but struggle to find reliable sources, while farmers lack direct sales channels',
        'targetAudience': 'Health-conscious urban consumers aged 25-45 with disposable income',
        'valueProposition': 'Direct farm-to-table delivery with 50% cost savings and 100% freshness guarantee',
        'marketContext': {
            'marketSize': '$50B local food market in US',
            'competitors': ['Farmers Market', 'Instacart', 'Local Harvest'],
            'competitiveAdvantage': 'Hyperlocal focus with direct farmer relationships'
        }
    }


@pytest.fixture
def sample_project_context():
    return {
        'complexity': 'medium',
        'project_type': 'mvp',
        'user_experience': 'intermediate'
    }


class TestQualityEngine:
    """Test quality assessment engine functionality"""
    
    def test_quality_assessment_engine_initialization(self):
        """Test that quality engine initializes correctly"""
        engine = QualityAssessmentEngine()
        assert engine is not None
        assert hasattr(engine, 'calculate_quality_score')
    
    def test_idea_quality_scoring(self, sample_idea_data, sample_project_context):
        """Test multi-dimensional quality scoring for idea refinement"""
        engine = QualityAssessmentEngine()
        
        result = engine.calculate_quality_score(
            stage="idea_refinement",
            content=sample_idea_data,
            context=sample_project_context
        )
        
        # Verify result structure
        assert hasattr(result, 'overall_score')
        assert hasattr(result, 'dimension_scores')
        assert hasattr(result, 'quality_gate_status')
        assert hasattr(result, 'improvement_suggestions')
        
        # Verify score ranges
        assert 0 <= result.overall_score <= 100
        assert all(0 <= score <= 100 for score in result.dimension_scores.values())
        
        # Verify quality gate status
        assert result.quality_gate_status in ['BLOCK', 'PROCEED_WITH_CAUTION', 'PROCEED_EXCELLENT']
    
    def test_adaptive_thresholds(self, sample_project_context):
        """Test that thresholds adapt based on project context"""
        engine = QualityAssessmentEngine()
        
        # Test different complexity levels
        simple_context = {**sample_project_context, 'complexity': 'simple'}
        complex_context = {**sample_project_context, 'complexity': 'enterprise'}
        
        simple_threshold = engine.get_dynamic_threshold("idea_refinement", simple_context)
        complex_threshold = engine.get_dynamic_threshold("idea_refinement", complex_context)
        
        # Complex projects should have higher thresholds
        assert complex_threshold.minimum > simple_threshold.minimum
    
    def test_improvement_suggestions(self, sample_idea_data, sample_project_context):
        """Test that quality engine provides actionable improvement suggestions"""
        engine = QualityAssessmentEngine()
        
        # Create intentionally weak idea data
        weak_idea = {
            'initialIdea': 'An app',
            'problemStatement': 'People need things',
            'targetAudience': 'Everyone',
            'valueProposition': 'It will be good'
        }
        
        result = engine.calculate_quality_score(
            stage="idea_refinement",
            content=weak_idea,
            context=sample_project_context
        )
        
        # Should have improvement suggestions for weak content
        assert len(result.improvement_suggestions) > 0
        assert result.overall_score < 50  # Should score poorly


class TestIdeaRefinementEndpoints:
    """Test API endpoints for idea refinement stage"""
    
    @patch('api.forge_api.idea_refinement_endpoints.extract_user_info')
    @patch('api.forge_api.idea_refinement_endpoints.quality_engine')
    async def test_analyze_idea_success(self, mock_quality_engine, mock_extract_user, mock_user_info, sample_idea_data, sample_project_context):
        """Test successful idea analysis with quality assessment"""
        # Setup mocks
        mock_extract_user.return_value = mock_user_info
        
        mock_quality_result = MagicMock()
        mock_quality_result.overall_score = 82.5
        mock_quality_result.dimension_scores = {
            'problem_clarity': 85,
            'target_audience_definition': 80,
            'value_proposition_strength': 85,
            'market_viability': 80
        }
        mock_quality_result.quality_gate_status = 'PROCEED_EXCELLENT'
        mock_quality_result.confidence_level = 0.85
        mock_quality_result.improvement_suggestions = []
        mock_quality_result.estimated_improvement_time = "30 minutes"
        mock_quality_result.context_consistency = True
        
        mock_quality_engine.calculate_quality_score.return_value = mock_quality_result
        
        mock_thresholds = MagicMock()
        mock_thresholds.minimum = 75
        mock_thresholds.recommended = 85
        mock_thresholds.adjustments_applied = []
        mock_quality_engine.get_dynamic_threshold.return_value = mock_thresholds
        
        # Create request
        request_body = {
            'ideaData': sample_idea_data,
            'projectContext': sample_project_context
        }
        
        request = MockHttpRequest(
            method='POST',
            body=request_body,
            route_params={'project_id': 'test-project-123'}
        )
        
        # Test endpoint
        response = await analyze_idea(request, 'test-project-123')
        
        # Verify response
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        
        assert response_data['projectId'] == 'test-project-123'
        assert response_data['qualityAssessment']['overallScore'] == 82.5
        assert response_data['qualityAssessment']['qualityGateStatus'] == 'PROCEED_EXCELLENT'
        assert 'nextSteps' in response_data
    
    @patch('api.forge_api.idea_refinement_endpoints.extract_user_info')
    async def test_analyze_idea_authentication_required(self, mock_extract_user):
        """Test that analysis requires authentication"""
        mock_extract_user.return_value = None
        
        request = MockHttpRequest(method='POST', route_params={'project_id': 'test-project'})
        response = await analyze_idea(request, 'test-project')
        
        assert response.status_code == 401
        response_data = json.loads(response.get_body())
        assert 'Authentication required' in response_data['error']
    
    @patch('api.forge_api.idea_refinement_endpoints.extract_user_info')
    @patch('api.forge_api.idea_refinement_endpoints.LLMClient')
    @patch('api.forge_api.idea_refinement_endpoints.CostTracker')
    async def test_refine_idea_with_llm_success(self, mock_cost_tracker, mock_llm_client, mock_extract_user, mock_user_info, sample_idea_data):
        """Test successful LLM-powered idea refinement"""
        # Setup mocks
        mock_extract_user.return_value = mock_user_info
        
        mock_llm_instance = AsyncMock()
        mock_llm_response = {
            'content': json.dumps({
                'problemStatement': 'Enhanced problem statement with market data',
                'targetAudience': 'Refined target audience with demographics',
                'valueProposition': 'Quantified value proposition with metrics',
                'marketAnalysis': {
                    'marketSize': '$50B local food market with 15% annual growth',
                    'competitors': ['FarmBox', 'LocalHarvest', 'Thrive Market'],
                    'competitiveAdvantage': 'Hyperlocal 2-hour delivery with farmer partnerships'
                },
                'refinementNotes': 'Added market data and competitive analysis'
            }),
            'usage': {'total_tokens': 1500},
            'cost': 0.003
        }
        mock_llm_instance.execute_prompt.return_value = mock_llm_response
        mock_llm_client.return_value = mock_llm_instance
        
        mock_cost_tracker_instance = AsyncMock()
        mock_cost_tracker.return_value = mock_cost_tracker_instance
        mock_cost_tracker_instance.current_operation_id = 'test-operation-123'
        
        # Create request
        request_body = {
            'currentIdea': sample_idea_data,
            'improvementFocus': ['market_analysis', 'competitive_positioning'],
            'selectedLLM': 'gemini-flash',
            'projectContext': {'complexity': 'medium'}
        }
        
        request = MockHttpRequest(
            method='POST',
            body=request_body,
            route_params={'project_id': 'test-project-123'}
        )
        
        # Test endpoint
        response = await refine_idea_with_llm(request, 'test-project-123')
        
        # Verify response
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        
        assert response_data['projectId'] == 'test-project-123'
        assert 'refinedIdea' in response_data
        assert 'qualityImprovement' in response_data
        assert 'costTracking' in response_data
        assert response_data['costTracking']['model'] == 'gemini-flash'


class TestQualityGateLogic:
    """Test quality gate decision logic and stage progression"""
    
    def test_quality_gate_blocking_logic(self):
        """Test that low quality scores block progression"""
        engine = QualityAssessmentEngine()
        
        weak_idea = {
            'initialIdea': 'App',
            'problemStatement': 'Problem',
            'targetAudience': 'Users',
            'valueProposition': 'Value'
        }
        
        result = engine.calculate_quality_score(
            stage="idea_refinement",
            content=weak_idea,
            context={'complexity': 'medium'}
        )
        
        # Should block progression for very low quality
        if result.overall_score < 65:
            assert result.quality_gate_status == 'BLOCK'
    
    def test_quality_gate_excellence_logic(self):
        """Test that high quality scores enable excellent progression"""
        engine = QualityAssessmentEngine()
        
        excellent_idea = {
            'initialIdea': 'A comprehensive marketplace platform connecting organic farmers directly with health-conscious urban consumers, featuring real-time inventory, quality guarantees, and sustainable delivery networks',
            'problemStatement': 'Urban consumers struggle to access fresh, verified organic produce while paying premium prices to intermediaries, while small organic farmers lack efficient direct-to-consumer sales channels and struggle with 30% post-harvest waste',
            'targetAudience': 'Health-conscious urban professionals aged 28-45, household income $75k+, who prioritize organic food and are willing to pay premium for quality and sustainability',
            'valueProposition': 'Guaranteed farm-fresh organic produce with 40% cost savings vs retail, delivered within 24 hours of harvest, with farmer transparency and carbon-neutral delivery options',
            'marketContext': {
                'marketSize': '$52B organic food market in US with 14% annual growth',
                'competitors': ['Whole Foods', 'Instacart Organic', 'Thrive Market', 'Local farm stands'],
                'competitiveAdvantage': 'Direct farmer relationships, real-time harvest tracking, and hyperlocal delivery optimization'
            }
        }
        
        result = engine.calculate_quality_score(
            stage="idea_refinement",
            content=excellent_idea,
            context={'complexity': 'medium'}
        )
        
        # Should enable excellent progression for high quality
        if result.overall_score >= 90:
            assert result.quality_gate_status == 'PROCEED_EXCELLENT'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
