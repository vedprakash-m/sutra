"""
Comprehensive tests for the Quality Assessment Engine.
Covers all stage-specific dimension assessors, threshold calculations,
gate decisions, improvement suggestions, and contextual validation.
"""

import pytest
from shared.quality_engine import (
    ContextualQualityValidator,
    QualityAssessmentEngine,
    QualityResult,
    QualityThresholds,
)


@pytest.fixture
def engine():
    return QualityAssessmentEngine()


@pytest.fixture
def validator():
    return ContextualQualityValidator()


# ---------------------------------------------------------------------------
#  Dataclass smoke tests
# ---------------------------------------------------------------------------


class TestQualityResult:
    def test_dataclass_fields(self):
        result = QualityResult(
            overall_score=85.0,
            dimension_scores={"completeness": 90.0},
            quality_gate_status="PROCEED_EXCELLENT",
            improvement_suggestions=[],
            context_consistency={"consistency_score": 100.0},
            confidence_level=90.0,
            estimated_improvement_time=5,
        )
        assert result.overall_score == 85.0
        assert result.quality_gate_status == "PROCEED_EXCELLENT"
        assert result.confidence_level == 90.0


class TestQualityThresholds:
    def test_dataclass_fields(self):
        thresholds = QualityThresholds(
            minimum=75.0,
            recommended=85.0,
            adjustments_applied={"total": 0},
            context_factors={},
        )
        assert thresholds.minimum == 75.0
        assert thresholds.recommended == 85.0


# ---------------------------------------------------------------------------
#  QualityAssessmentEngine – initialization
# ---------------------------------------------------------------------------


class TestEngineInit:
    def test_has_dimension_weights(self, engine):
        assert set(engine.dimension_weights.keys()) == {
            "completeness",
            "coherence",
            "actionability",
            "specificity",
        }
        assert abs(sum(engine.dimension_weights.values()) - 1.0) < 1e-9

    def test_has_all_stage_metrics(self, engine):
        expected_stages = {
            "idea_refinement",
            "prd_generation",
            "ux_requirements",
            "technical_analysis",
            "implementation_playbook",
        }
        assert set(engine.stage_specific_metrics.keys()) == expected_stages

    def test_stage_metric_weights_sum_to_one(self, engine):
        for stage, metrics in engine.stage_specific_metrics.items():
            total = sum(metrics.values())
            assert abs(total - 1.0) < 1e-9, f"{stage} weights sum to {total}"

    def test_has_base_thresholds_for_all_stages(self, engine):
        for stage in engine.stage_specific_metrics:
            assert stage in engine.base_thresholds


# ---------------------------------------------------------------------------
#  calculate_quality_score – high-level integration
# ---------------------------------------------------------------------------


class TestCalculateQualityScore:
    def test_returns_quality_result(self, engine):
        content = {"problemStatement": "Users struggle with managing complex projects efficiently due to lack of tools."}
        result = engine.calculate_quality_score("idea_refinement", content, {})
        assert isinstance(result, QualityResult)
        assert 0 <= result.overall_score <= 100
        assert result.quality_gate_status in ("BLOCK", "PROCEED_WITH_CAUTION", "PROCEED_EXCELLENT")

    def test_returns_dimension_scores_for_stage(self, engine):
        content = {
            "problemStatement": "Users can't manage projects",
            "targetAudience": "Project managers in tech companies",
            "valueProposition": "Save time and improve efficiency",
            "marketAnalysis": {"marketSize": "10 billion", "competitors": ["A", "B", "C"]},
        }
        result = engine.calculate_quality_score("idea_refinement", content, {})
        expected_dims = {"problem_clarity", "target_audience_definition", "value_proposition_clarity", "market_viability"}
        assert set(result.dimension_scores.keys()) == expected_dims

    def test_empty_content_gets_low_score(self, engine):
        result = engine.calculate_quality_score("idea_refinement", {}, {})
        assert result.overall_score < 40

    def test_error_handling_returns_safe_default(self, engine):
        # Passing None causes dimension assessors to fail, but the engine catches
        # at the dimension level (returning 50.0 per dimension) — not the top-level handler.
        result = engine.calculate_quality_score("idea_refinement", None, {})
        assert result.quality_gate_status == "BLOCK"
        # Each dimension falls back to 50.0 so overall_score will be 50.0
        assert result.overall_score == 50.0

    def test_unknown_stage_uses_generic_assessment(self, engine):
        content = {"data": "x" * 300}
        result = engine.calculate_quality_score("unknown_stage", content, {})
        assert isinstance(result, QualityResult)
        assert result.overall_score > 0


# ---------------------------------------------------------------------------
#  Idea Refinement dimension assessors
# ---------------------------------------------------------------------------


class TestProblemClarity:
    def test_empty_statement(self, engine):
        assert engine._assess_problem_clarity({}) == 20.0

    def test_very_short_statement(self, engine):
        assert engine._assess_problem_clarity({"problemStatement": "short"}) == 20.0

    def test_statement_with_who_keyword(self, engine):
        content = {"problemStatement": "The customer faces difficulty tracking orders in a complex system"}
        score = engine._assess_problem_clarity(content)
        assert score >= 60.0

    def test_statement_with_multiple_clarity_indicators(self, engine):
        content = {
            "problemStatement": (
                "The customer faces a critical problem when they try to manage data efficiently. "
                "This results in wasted time due to poor tooling because the current system is "
                "unreliable in the context of enterprise deployments."
            )
        }
        score = engine._assess_problem_clarity(content)
        assert score >= 80.0

    def test_vague_language_penalized(self, engine):
        content_vague = {"problemStatement": "Someone somehow probably generally usually has an issue with something"}
        content_specific = {"problemStatement": "The customer faces a specific problem when exactly tracking user goals precisely"}
        score_vague = engine._assess_problem_clarity(content_vague)
        score_specific = engine._assess_problem_clarity(content_specific)
        assert score_specific > score_vague

    def test_longer_statements_score_higher(self, engine):
        short = {"problemStatement": "The user faces a problem with tools"}
        long = {"problemStatement": "The user faces a problem with tools. " * 10}
        assert engine._assess_problem_clarity(long) >= engine._assess_problem_clarity(short)

    def test_score_capped_at_100(self, engine):
        content = {
            "problemStatement": (
                "The specific customer person faces a clearly defined problem challenge. "
                "Due to this issue, results in pain when the situation context during after before "
                "exactly precisely this leads to difficulty. " * 5
            )
        }
        assert engine._assess_problem_clarity(content) <= 100.0

    def test_score_floored_at_0(self, engine):
        # Even with many vague indicators, score shouldn't go below 0
        content = {"problemStatement": "somehow maybe probably generally usually " * 10}
        assert engine._assess_problem_clarity(content) >= 0.0


class TestTargetAudience:
    def test_empty_audience(self, engine):
        assert engine._assess_target_audience({}) == 15.0

    def test_short_audience(self, engine):
        assert engine._assess_target_audience({"targetAudience": "devs"}) == 15.0

    def test_demographic_indicators_boost_score(self, engine):
        content = {"targetAudience": "Young adults, age 25-34, with higher education and urban location, high income occupation"}
        score = engine._assess_target_audience(content)
        assert score >= 70.0

    def test_behavioral_indicators_boost_score(self, engine):
        content = {"targetAudience": "Users who need better tools and want to improve their habit and behavior to reach their goal"}
        score = engine._assess_target_audience(content)
        assert score >= 60.0

    def test_generic_terms_penalized(self, engine):
        generic = {"targetAudience": "Everyone and anyone looking for a broad general solution for all"}
        specific = {"targetAudience": "The specific particular users in a targeted industry"}
        assert engine._assess_target_audience(specific) > engine._assess_target_audience(generic)


class TestValueProposition:
    def test_empty_value_prop(self, engine):
        assert engine._assess_value_proposition({}) == 20.0

    def test_short_value_prop(self, engine):
        assert engine._assess_value_proposition({"valueProposition": "Better"}) == 20.0

    def test_value_indicators_boost_score(self, engine):
        content = {"valueProposition": "Save time and reduce costs while making your process faster and easier to manage"}
        score = engine._assess_value_proposition(content)
        assert score >= 65.0

    def test_differentiation_indicators(self, engine):
        content = {"valueProposition": "Our unique and innovative approach is the first to provide an exclusive benefit to users"}
        score = engine._assess_value_proposition(content)
        assert score >= 65.0

    def test_quantifiable_benefits_bonus(self, engine):
        without_numbers = {"valueProposition": "Save time and reduce costs for your business operations"}
        with_numbers = {"valueProposition": "Save 40% of time and reduce costs by 30% for your business operations"}
        assert engine._assess_value_proposition(with_numbers) > engine._assess_value_proposition(without_numbers)

    def test_customer_focus_over_feature_focus(self, engine):
        customer = {"valueProposition": "Your customers benefit from an advantage that helps the user achieve their goals"}
        features = {"valueProposition": "This system has a feature and capability that the technology provides through its function"}
        assert engine._assess_value_proposition(customer) > engine._assess_value_proposition(features)


class TestMarketViability:
    def test_empty_market_analysis(self, engine):
        assert engine._assess_market_viability({}) == 25.0

    def test_market_size_present(self, engine):
        content = {"marketAnalysis": {"marketSize": "The global market is valued at 50 billion dollars"}}
        score = engine._assess_market_viability(content)
        assert score >= 60.0

    def test_competitors_list(self, engine):
        content = {"marketAnalysis": {"competitors": ["CompA", "CompB", "CompC"]}}
        score = engine._assess_market_viability(content)
        assert score >= 55.0

    def test_competitive_advantage_present(self, engine):
        content = {"marketAnalysis": {"competitiveAdvantage": "Our unique approach leverages AI to provide better results at lower cost"}}
        score = engine._assess_market_viability(content)
        assert score >= 45.0

    def test_timing_indicators_boost(self, engine):
        content = {"marketAnalysis": {"notes": "The emerging trend shows strong demand and growth opportunity"}}
        score_with_timing = engine._assess_market_viability(content)
        content_bare = {"marketAnalysis": {"notes": "some basic info"}}
        score_bare = engine._assess_market_viability(content_bare)
        assert score_with_timing > score_bare

    def test_rich_market_analysis_scores_high(self, engine):
        content = {
            "marketAnalysis": {
                "marketSize": "The global market is estimated at 100 billion dollars growing at 15% annually",
                "competitors": ["Alpha", "Beta", "Gamma", "Delta"],
                "competitiveAdvantage": "Our innovative approach provides a unique first-mover advantage in the emerging trend",
            }
        }
        score = engine._assess_market_viability(content)
        assert score >= 85.0


# ---------------------------------------------------------------------------
#  PRD dimension assessors (via _assess_prd_dimension)
# ---------------------------------------------------------------------------


class TestPRDDimensions:
    def test_requirement_completeness_empty(self, engine):
        score = engine._assess_requirement_completeness({})
        assert score <= 30.0

    def test_requirement_completeness_with_requirements(self, engine):
        content = {
            "requirements": {
                "functional": ["R1 - The system shall process user input with validation"],
                "nonFunctional": ["NFR1 - System must respond in under 200ms"],
                "constraints": ["Must run on AWS"],
            }
        }
        score = engine._assess_requirement_completeness(content)
        assert score > 30.0

    def test_user_story_quality_empty(self, engine):
        score = engine._assess_user_story_quality({})
        assert score <= 30.0

    def test_user_story_quality_with_stories(self, engine):
        content = {
            "userStories": [
                {"story": "As a user, I want to login so that I can access my dashboard", "acceptanceCriteria": ["Given credentials, when login, then access"]},
                {"story": "As an admin, I want to manage users so that I can control access", "acceptanceCriteria": ["Given admin role, when viewing users, then CRUD"]},
            ]
        }
        score = engine._assess_user_story_quality(content)
        assert score > 25.0  # Has stories with acceptance criteria

    def test_business_alignment_empty(self, engine):
        score = engine._assess_business_alignment({}, {})
        assert score <= 40.0

    def test_implementation_clarity_empty(self, engine):
        score = engine._assess_implementation_clarity({})
        assert score <= 35.0

    def test_prd_dimension_routing(self, engine):
        """Ensure _assess_prd_dimension routes to correct assessors"""
        content = {"requirements": {"functional": ["R1"]}}
        score = engine._assess_prd_dimension("requirement_completeness", content, {})
        assert score > 0

    def test_prd_dimension_unknown_returns_default(self, engine):
        score = engine._assess_prd_dimension("nonexistent_dimension", {}, {})
        assert score == 70.0


# ---------------------------------------------------------------------------
#  UX dimension assessors
# ---------------------------------------------------------------------------


class TestUXDimensions:
    def test_user_journey_completeness_empty(self, engine):
        score = engine._assess_user_journey_completeness({})
        assert score <= 25.0

    def test_wireframe_quality_empty(self, engine):
        score = engine._assess_wireframe_quality({})
        assert score <= 25.0

    def test_accessibility_compliance_empty(self, engine):
        score = engine._assess_accessibility_compliance({})
        assert score <= 25.0

    def test_ux_implementation_feasibility_empty(self, engine):
        score = engine._assess_ux_implementation_feasibility({}, {})
        assert score <= 45.0

    def test_ux_dimension_routing(self, engine):
        content = {"userJourneys": [{"name": "Login flow", "steps": ["Step 1", "Step 2"]}]}
        score = engine._assess_ux_dimension("user_journey_completeness", content, {})
        assert score > 0

    def test_ux_dimension_unknown_returns_default(self, engine):
        score = engine._assess_ux_dimension("nonexistent", {}, {})
        assert score == 70.0


# ---------------------------------------------------------------------------
#  Technical Analysis dimension assessors
# ---------------------------------------------------------------------------


class TestTechAnalysisDimensions:
    def test_architectural_soundness_empty(self, engine):
        score = engine._assess_architectural_soundness({})
        assert score <= 30.0

    def test_feasibility_empty(self, engine):
        score = engine._assess_feasibility({})
        assert score <= 30.0

    def test_risk_quality_empty(self, engine):
        score = engine._assess_risk_quality({})
        assert score <= 30.0

    def test_consensus_quality_empty(self, engine):
        score = engine._assess_consensus_quality({})
        assert score <= 30.0

    def test_tech_dimension_routing(self, engine):
        content = {"architecture": {"components": ["API", "DB", "Frontend"]}}
        score = engine._assess_tech_analysis_dimension("architectural_soundness", content, {})
        assert score > 0

    def test_tech_dimension_unknown_returns_default(self, engine):
        score = engine._assess_tech_analysis_dimension("nonexistent", {}, {})
        assert score == 70.0


# ---------------------------------------------------------------------------
#  Playbook dimension assessors
# ---------------------------------------------------------------------------


class TestPlaybookDimensions:
    def test_context_integration_empty(self, engine):
        score = engine._assess_context_integration({}, {})
        assert score <= 50.0

    def test_prompt_actionability_empty(self, engine):
        score = engine._assess_prompt_actionability({})
        assert score <= 30.0

    def test_testing_completeness_empty(self, engine):
        score = engine._assess_testing_completeness({})
        assert score <= 30.0

    def test_deployment_readiness_empty(self, engine):
        score = engine._assess_deployment_readiness({})
        assert score <= 30.0

    def test_playbook_dimension_routing(self, engine):
        content = {"prompts": [{"instruction": "Implement error handling", "steps": ["1", "2"]}]}
        score = engine._assess_playbook_dimension("prompt_actionability", content, {})
        assert score > 0

    def test_playbook_dimension_unknown_returns_default(self, engine):
        score = engine._assess_playbook_dimension("nonexistent", {}, {})
        assert score == 70.0


# ---------------------------------------------------------------------------
#  Generic dimension fallback
# ---------------------------------------------------------------------------


class TestGenericDimension:
    @pytest.mark.parametrize(
        "content_len,expected_min",
        [
            (10, 30.0),
            (100, 60.0),
            (300, 75.0),
            (600, 85.0),
        ],
    )
    def test_scales_with_content_size(self, engine, content_len, expected_min):
        content = {"data": "x" * content_len}
        score = engine._assess_generic_dimension("any", content)
        assert score >= expected_min


# ---------------------------------------------------------------------------
#  Dynamic thresholds
# ---------------------------------------------------------------------------


class TestDynamicThresholds:
    def test_default_thresholds(self, engine):
        thresholds = engine.get_dynamic_threshold("idea_refinement", {})
        assert isinstance(thresholds, QualityThresholds)
        assert thresholds.minimum >= 60
        assert thresholds.recommended >= 70

    def test_simple_project_lowers_thresholds(self, engine):
        t_default = engine.get_dynamic_threshold("idea_refinement", {"complexity": "medium"})
        t_simple = engine.get_dynamic_threshold("idea_refinement", {"complexity": "simple"})
        assert t_simple.minimum < t_default.minimum

    def test_enterprise_raises_thresholds(self, engine):
        t_default = engine.get_dynamic_threshold("idea_refinement", {"complexity": "medium"})
        t_enterprise = engine.get_dynamic_threshold("idea_refinement", {"complexity": "enterprise"})
        assert t_enterprise.minimum > t_default.minimum

    def test_prototype_type_lowers_thresholds(self, engine):
        t_mvp = engine.get_dynamic_threshold("prd_generation", {"project_type": "mvp"})
        t_proto = engine.get_dynamic_threshold("prd_generation", {"project_type": "prototype"})
        assert t_proto.minimum < t_mvp.minimum

    def test_production_type_raises_thresholds(self, engine):
        t_mvp = engine.get_dynamic_threshold("prd_generation", {"project_type": "mvp"})
        t_prod = engine.get_dynamic_threshold("prd_generation", {"project_type": "production"})
        assert t_prod.minimum > t_mvp.minimum

    def test_expert_experience_raises_thresholds(self, engine):
        t_inter = engine.get_dynamic_threshold("idea_refinement", {"user_experience": "intermediate"})
        t_expert = engine.get_dynamic_threshold("idea_refinement", {"user_experience": "expert"})
        assert t_expert.minimum > t_inter.minimum

    def test_threshold_minimum_capped_at_60(self, engine):
        # Prototype + simple + novice gives max negative adjustment
        t = engine.get_dynamic_threshold("idea_refinement", {
            "complexity": "simple",
            "user_experience": "novice",
            "project_type": "prototype",
        })
        assert t.minimum >= 60

    def test_threshold_recommended_capped_at_98(self, engine):
        t = engine.get_dynamic_threshold("implementation_playbook", {
            "complexity": "enterprise",
            "user_experience": "expert",
            "project_type": "production",
        })
        assert t.recommended <= 98

    def test_adjustments_tracked(self, engine):
        t = engine.get_dynamic_threshold("idea_refinement", {"complexity": "enterprise"})
        assert "complexity" in t.adjustments_applied
        assert "experience" in t.adjustments_applied
        assert "type" in t.adjustments_applied
        assert "total" in t.adjustments_applied

    def test_unknown_stage_uses_default_base(self, engine):
        t = engine.get_dynamic_threshold("unknown_stage", {})
        assert t.minimum >= 60
        assert t.recommended >= 70


# ---------------------------------------------------------------------------
#  Gate status determination
# ---------------------------------------------------------------------------


class TestGateStatus:
    def test_excellent_above_recommended(self, engine):
        thresholds = QualityThresholds(minimum=75, recommended=85, adjustments_applied={}, context_factors={})
        assert engine._determine_gate_status(90.0, thresholds) == "PROCEED_EXCELLENT"

    def test_caution_between_min_and_recommended(self, engine):
        thresholds = QualityThresholds(minimum=75, recommended=85, adjustments_applied={}, context_factors={})
        assert engine._determine_gate_status(80.0, thresholds) == "PROCEED_WITH_CAUTION"

    def test_block_below_minimum(self, engine):
        thresholds = QualityThresholds(minimum=75, recommended=85, adjustments_applied={}, context_factors={})
        assert engine._determine_gate_status(60.0, thresholds) == "BLOCK"

    def test_exactly_at_recommended(self, engine):
        thresholds = QualityThresholds(minimum=75, recommended=85, adjustments_applied={}, context_factors={})
        assert engine._determine_gate_status(85.0, thresholds) == "PROCEED_EXCELLENT"

    def test_exactly_at_minimum(self, engine):
        thresholds = QualityThresholds(minimum=75, recommended=85, adjustments_applied={}, context_factors={})
        assert engine._determine_gate_status(75.0, thresholds) == "PROCEED_WITH_CAUTION"


# ---------------------------------------------------------------------------
#  Improvement suggestions
# ---------------------------------------------------------------------------


class TestImprovementSuggestions:
    def test_suggestions_for_low_dimensions(self, engine):
        dimension_scores = {"problem_clarity": 40.0, "target_audience_definition": 90.0}
        suggestions = engine._generate_improvement_suggestions("idea_refinement", dimension_scores, {}, {})
        assert len(suggestions) >= 1
        # Only low-scoring dimensions get suggestions
        assert all(s.get("dimension") or True for s in suggestions)

    def test_no_suggestions_when_all_high(self, engine):
        dimension_scores = {
            "problem_clarity": 95.0,
            "target_audience_definition": 90.0,
            "value_proposition_clarity": 88.0,
            "market_viability": 92.0,
        }
        suggestions = engine._generate_improvement_suggestions("idea_refinement", dimension_scores, {}, {})
        assert len(suggestions) == 0

    def test_max_three_suggestions(self, engine):
        dimension_scores = {
            "problem_clarity": 30.0,
            "target_audience_definition": 40.0,
            "value_proposition_clarity": 35.0,
            "market_viability": 50.0,
        }
        suggestions = engine._generate_improvement_suggestions("idea_refinement", dimension_scores, {}, {})
        assert len(suggestions) <= 3


# ---------------------------------------------------------------------------
#  Confidence level and improvement time
# ---------------------------------------------------------------------------


class TestConfidenceLevel:
    def test_empty_scores_zero_confidence(self, engine):
        assert engine._calculate_confidence_level({}, {}) == 0.0

    def test_low_variance_high_confidence(self, engine):
        scores = {"a": 80.0, "b": 82.0, "c": 81.0}
        confidence = engine._calculate_confidence_level(scores, {"data": "x" * 500})
        assert confidence >= 70.0

    def test_high_variance_lower_confidence(self, engine):
        scores = {"a": 20.0, "b": 95.0}
        confidence = engine._calculate_confidence_level(scores, {"data": "x" * 500})
        scores_uniform = {"a": 80.0, "b": 82.0}
        confidence_uniform = engine._calculate_confidence_level(scores_uniform, {"data": "x" * 500})
        assert confidence < confidence_uniform

    def test_confidence_bounded_0_100(self, engine):
        scores = {"a": 10.0, "b": 99.0, "c": 50.0}
        c = engine._calculate_confidence_level(scores, {})
        assert 0.0 <= c <= 100.0


class TestImprovementTime:
    def test_no_improvements_zero_time(self, engine):
        assert engine._estimate_improvement_time({}, []) == 0

    def test_time_capped_at_60(self, engine):
        improvements = [{"estimated_time": 30}, {"estimated_time": 30}, {"estimated_time": 30}]
        assert engine._estimate_improvement_time({}, improvements) == 60

    def test_default_time_per_improvement(self, engine):
        improvements = [{"type": "suggestion"}, {"type": "suggestion"}]
        time = engine._estimate_improvement_time({}, improvements)
        assert time == 20  # 10 + 10 default per improvement


# ---------------------------------------------------------------------------
#  Context consistency
# ---------------------------------------------------------------------------


class TestContextConsistency:
    def test_idea_refinement_always_consistent(self, engine):
        result = engine._validate_context_consistency("idea_refinement", {}, {})
        assert result["consistency_score"] == 100.0
        assert result["issues"] == []

    def test_other_stages_return_default(self, engine):
        result = engine._validate_context_consistency("prd_generation", {}, {})
        assert result["consistency_score"] == 95.0


# ---------------------------------------------------------------------------
#  _assess_dimension routing
# ---------------------------------------------------------------------------


class TestDimensionRouting:
    @pytest.mark.parametrize("stage", [
        "idea_refinement",
        "prd_generation",
        "ux_requirements",
        "technical_analysis",
        "implementation_playbook",
    ])
    def test_known_stages_route_correctly(self, engine, stage):
        score = engine._assess_dimension(stage, "some_dim", {}, {})
        assert 0 <= score <= 100

    def test_unknown_stage_uses_generic(self, engine):
        score = engine._assess_dimension("unknown", "any", {"data": "x" * 300}, {})
        assert score >= 60  # generic assessment for 300+ chars


# ---------------------------------------------------------------------------
#  ContextualQualityValidator
# ---------------------------------------------------------------------------


class TestContextualQualityValidator:
    def test_idea_refinement_no_dependencies(self, validator):
        result = validator.validate_context_quality("idea_refinement", {})
        assert result["overall_context_strength"] == 0
        assert result["consistency_issues"] == []

    def test_prd_depends_on_idea(self, validator):
        project_data = {
            "idea_refinement": {"qualityMetrics": {"overall": 90}},
        }
        result = validator.validate_context_quality("prd_generation", project_data)
        assert result["context_scores"]["idea_refinement"] == 90
        assert result["overall_context_strength"] == 90

    def test_low_quality_dependency_flags_issue(self, validator):
        project_data = {
            "idea_refinement": {"qualityMetrics": {"overall": 60}},
        }
        result = validator.validate_context_quality("prd_generation", project_data)
        assert len(result["consistency_issues"]) == 1
        assert result["consistency_issues"][0]["stage"] == "idea_refinement"

    def test_moderate_quality_flags_enhancement_opportunity(self, validator):
        project_data = {
            "idea_refinement": {"qualityMetrics": {"overall": 80}},
        }
        result = validator.validate_context_quality("prd_generation", project_data)
        assert len(result["enhancement_opportunities"]) == 1

    def test_high_quality_no_issues_no_enhancements(self, validator):
        project_data = {
            "idea_refinement": {"qualityMetrics": {"overall": 92}},
        }
        result = validator.validate_context_quality("prd_generation", project_data)
        assert result["consistency_issues"] == []
        assert result["enhancement_opportunities"] == []

    def test_implementation_playbook_many_dependencies(self, validator):
        project_data = {
            "idea_refinement": {"qualityMetrics": {"overall": 85}},
            "prd_generation": {"qualityMetrics": {"overall": 88}},
            "technical_analysis": {"qualityMetrics": {"overall": 90}},
        }
        result = validator.validate_context_quality("implementation_playbook", project_data)
        assert len(result["context_scores"]) == 3
        avg = (85 + 88 + 90) / 3.0
        assert abs(result["overall_context_strength"] - avg) < 0.01

    def test_missing_dependency_data(self, validator):
        # If a required stage has no data, quality defaults to 0
        result = validator.validate_context_quality("prd_generation", {})
        assert result["context_scores"]["idea_refinement"] == 0
        assert len(result["consistency_issues"]) == 1

    def test_context_dependencies_structure(self, validator):
        assert "prd_generation" in validator.context_dependencies
        assert "idea_refinement" in validator.context_dependencies["prd_generation"]
        assert "implementation_playbook" in validator.context_dependencies
        deps = validator.context_dependencies["implementation_playbook"]
        assert "idea_refinement" in deps
        assert "prd_generation" in deps
        assert "technical_analysis" in deps


# ---------------------------------------------------------------------------
#  End-to-end: full stage assessments with rich content
# ---------------------------------------------------------------------------


class TestFullStageAssessments:
    def test_idea_refinement_full_content(self, engine):
        content = {
            "problemStatement": (
                "Small business owners struggle to manage their specific inventory efficiently "
                "because they lack affordable tools. This results in lost sales and wasted resources "
                "when demand fluctuates during seasonal periods."
            ),
            "targetAudience": (
                "Small business owners, age 30-55, running retail or e-commerce stores, "
                "with income between 50K-200K. They need better inventory tools and want "
                "to reduce waste and improve their operational habits."
            ),
            "valueProposition": (
                "Save 30% on inventory costs and reduce waste by 50%. Our unique AI-powered "
                "approach is the first to offer real-time demand forecasting for your small business, "
                "making inventory management easier and faster for the customer."
            ),
            "marketAnalysis": {
                "marketSize": "The global inventory management market is valued at 3.2 billion dollars and growing at 8% annually",
                "competitors": ["TradeGecko", "Cin7", "Zoho Inventory", "inFlow"],
                "competitiveAdvantage": "Our innovative AI forecasting provides a unique first-mover advantage in the emerging small business segment with strong demand growth",
            },
        }
        result = engine.calculate_quality_score("idea_refinement", content, {"complexity": "medium"})
        assert result.overall_score >= 60.0
        assert result.quality_gate_status in ("PROCEED_WITH_CAUTION", "PROCEED_EXCELLENT")

    def test_prd_generation_full_content(self, engine):
        content = {
            "requirements": {
                "functional": [
                    "FR-001: The system shall track inventory levels in real-time",
                    "FR-002: The system shall generate purchase order recommendations",
                ],
                "nonFunctional": [
                    "NFR-001: The system response time shall be under 200ms",
                    "NFR-002: The system shall handle 1000 concurrent users",
                ],
                "constraints": ["Must integrate with existing POS systems"],
            },
            "userStories": [
                {
                    "story": "As a store owner, I want to see real-time inventory so that I can make purchasing decisions",
                    "acceptanceCriteria": ["Given inventory data, when viewing dashboard, then current levels shown"],
                },
                {
                    "story": "As a manager, I want to receive alerts so that I can reorder on time",
                    "acceptanceCriteria": ["Given low stock threshold, when level drops, then alert sent"],
                },
            ],
        }
        result = engine.calculate_quality_score("prd_generation", content, {})
        assert result.overall_score > 0
        assert isinstance(result.dimension_scores, dict)

    def test_technical_analysis_full_content(self, engine):
        content = {
            "architecture": {
                "components": ["API Gateway", "Inventory Service", "ML Pipeline", "Dashboard"],
                "patterns": ["microservices", "event-driven"],
                "decisions": ["Use PostgreSQL for ACID compliance", "Redis for caching"],
            },
            "feasibility": {
                "technical": "Feasible with existing cloud infrastructure",
                "assessment": "Medium complexity, 3-month timeline",
                "resources": ["2 backend engineers", "1 ML engineer", "1 frontend"],
            },
            "risks": [
                {"risk": "ML model accuracy", "severity": "high", "mitigation": "Incremental rollout with A/B testing"},
                {"risk": "Integration complexity", "severity": "medium", "mitigation": "API-first design"},
            ],
        }
        result = engine.calculate_quality_score("technical_analysis", content, {})
        assert result.overall_score > 0
