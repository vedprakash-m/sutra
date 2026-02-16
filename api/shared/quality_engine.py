"""
Quality Engine - Multi-dimensional quality assessment system for Forge stages.
Implements adaptive quality measurement with context-aware thresholds and intelligent improvement suggestions.
"""

import logging
import re
import statistics
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class QualityResult:
    """Comprehensive quality assessment result"""

    overall_score: float
    dimension_scores: Dict[str, float]
    quality_gate_status: str  # "BLOCK", "PROCEED_WITH_CAUTION", "PROCEED_EXCELLENT"
    improvement_suggestions: List[Dict[str, Any]]
    context_consistency: Dict[str, Any]
    confidence_level: float
    estimated_improvement_time: int  # minutes


@dataclass
class QualityThresholds:
    """Adaptive quality thresholds for a stage"""

    minimum: float
    recommended: float
    adjustments_applied: Dict[str, float]
    context_factors: Dict[str, Any]


class QualityAssessmentEngine:
    """Multi-dimensional quality scoring engine with adaptive thresholds"""

    def __init__(self):
        """Initialize quality assessment engine with stage-specific metrics"""
        self.dimension_weights = {
            "completeness": 0.3,  # Content coverage and depth
            "coherence": 0.25,  # Logical consistency and flow
            "actionability": 0.25,  # Clear next steps and implementation guidance
            "specificity": 0.2,  # Concrete details vs. vague statements
        }

        self.stage_specific_metrics = {
            "idea_refinement": {
                "problem_clarity": 0.25,
                "target_audience_definition": 0.25,
                "value_proposition_clarity": 0.25,
                "market_viability": 0.25,
            },
            "prd_generation": {
                "requirement_completeness": 0.30,
                "user_story_quality": 0.25,
                "business_alignment": 0.25,
                "implementation_clarity": 0.20,
            },
            "ux_requirements": {
                "user_journey_completeness": 0.30,
                "wireframe_quality": 0.25,
                "accessibility_compliance": 0.25,
                "implementation_feasibility": 0.20,
            },
            "technical_analysis": {
                "architectural_soundness": 0.35,
                "feasibility_assessment": 0.25,
                "risk_assessment": 0.25,
                "multi_llm_consensus": 0.15,
            },
            "implementation_playbook": {
                "context_integration": 0.30,
                "prompt_actionability": 0.25,
                "testing_completeness": 0.25,
                "deployment_readiness": 0.20,
            },
        }

        self.base_thresholds = {
            "idea_refinement": {"minimum": 75, "recommended": 85},
            "prd_generation": {"minimum": 80, "recommended": 90},
            "ux_requirements": {"minimum": 82, "recommended": 90},
            "technical_analysis": {"minimum": 85, "recommended": 92},
            "implementation_playbook": {"minimum": 88, "recommended": 95},
        }

        self.adjustment_factors = {
            "project_complexity": {
                "simple": -10,  # More forgiving for simple projects
                "medium": 0,  # Standard thresholds
                "complex": +5,  # Slightly higher standards
                "enterprise": +15,  # Significantly higher standards
            },
            "user_experience": {
                "novice": -5,  # More guidance for new users
                "intermediate": 0,  # Standard expectations
                "expert": +5,  # Higher expectations for experienced users
            },
            "project_type": {
                "prototype": -15,  # Rapid iteration focus
                "mvp": -5,  # Balanced approach
                "production": +10,  # Production-ready standards
            },
        }

    def calculate_quality_score(self, stage: str, content: Dict[str, Any], context: Dict[str, Any]) -> QualityResult:
        """Calculate comprehensive quality score with contextual adjustments"""
        try:
            # Get stage-specific metrics
            metrics = self.stage_specific_metrics.get(stage, self.dimension_weights)

            # Assess each dimension
            dimension_scores = {}
            for dimension, weight in metrics.items():
                score = self._assess_dimension(stage, dimension, content, context)
                dimension_scores[dimension] = score

            # Calculate weighted overall score
            overall_score = 0.0
            for dimension in dimension_scores:
                if dimension in metrics:
                    overall_score += dimension_scores[dimension] * metrics[dimension]

            # Get adaptive thresholds
            thresholds = self.get_dynamic_threshold(stage, context)

            # Determine quality gate status
            gate_status = self._determine_gate_status(overall_score, thresholds)

            # Generate improvement suggestions
            improvements = self._generate_improvement_suggestions(stage, dimension_scores, content, context)

            # Validate context consistency
            context_consistency = self._validate_context_consistency(stage, content, context)

            # Calculate confidence level
            confidence = self._calculate_confidence_level(dimension_scores, content)

            # Estimate improvement time
            improvement_time = self._estimate_improvement_time(dimension_scores, improvements)

            return QualityResult(
                overall_score=overall_score,
                dimension_scores=dimension_scores,
                quality_gate_status=gate_status,
                improvement_suggestions=improvements,
                context_consistency=context_consistency,
                confidence_level=confidence,
                estimated_improvement_time=improvement_time,
            )

        except Exception as e:
            logger.error(f"Error calculating quality score for stage {stage}: {str(e)}")
            # Return default low-quality result for safety
            return QualityResult(
                overall_score=50.0,
                dimension_scores={},
                quality_gate_status="BLOCK",
                improvement_suggestions=[{"type": "error", "message": "Quality assessment failed"}],
                context_consistency={"error": str(e)},
                confidence_level=0.0,
                estimated_improvement_time=30,
            )

    def _assess_dimension(self, stage: str, dimension: str, content: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Assess a specific quality dimension"""
        try:
            if stage == "idea_refinement":
                return self._assess_idea_refinement_dimension(dimension, content, context)
            elif stage == "prd_generation":
                return self._assess_prd_dimension(dimension, content, context)
            elif stage == "ux_requirements":
                return self._assess_ux_dimension(dimension, content, context)
            elif stage == "technical_analysis":
                return self._assess_tech_analysis_dimension(dimension, content, context)
            elif stage == "implementation_playbook":
                return self._assess_playbook_dimension(dimension, content, context)
            else:
                # Generic assessment for unknown stages
                return self._assess_generic_dimension(dimension, content)

        except Exception as e:
            logger.warning(f"Error assessing dimension {dimension} for stage {stage}: {str(e)}")
            return 50.0  # Default mid-range score

    def _assess_idea_refinement_dimension(self, dimension: str, content: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Assess idea refinement specific dimensions"""
        if dimension == "problem_clarity":
            return self._assess_problem_clarity(content)
        elif dimension == "target_audience_definition":
            return self._assess_target_audience(content)
        elif dimension == "value_proposition_clarity":
            return self._assess_value_proposition(content)
        elif dimension == "market_viability":
            return self._assess_market_viability(content)
        else:
            return 70.0  # Default score for unknown dimensions

    def _assess_problem_clarity(self, content: Dict[str, Any]) -> float:
        """Assess how clearly the problem is defined"""
        problem_statement = content.get("problemStatement", "")

        if not problem_statement or len(problem_statement.strip()) < 20:
            return 20.0

        score = 50.0  # Base score

        # Check for specific problem elements
        clarity_indicators = [
            ("who", ["user", "customer", "person", "people", "team", "business"]),
            ("what", ["problem", "issue", "challenge", "difficulty", "pain"]),
            ("when", ["when", "during", "while", "after", "before"]),
            ("where", ["where", "context", "environment", "situation"]),
            ("why", ["because", "due to", "causes", "results in", "leads to"]),
        ]

        for category, keywords in clarity_indicators:
            if any(keyword in problem_statement.lower() for keyword in keywords):
                score += 10.0

        # Check for specific vs vague language
        specific_indicators = ["specific", "exactly", "precisely", "clearly", "defined"]
        vague_indicators = ["somehow", "maybe", "probably", "generally", "usually"]

        specific_count = sum(1 for word in specific_indicators if word in problem_statement.lower())
        vague_count = sum(1 for word in vague_indicators if word in problem_statement.lower())

        score += (specific_count * 5) - (vague_count * 3)

        # Check length and detail
        if len(problem_statement) > 100:
            score += 5.0
        if len(problem_statement) > 200:
            score += 5.0

        return min(100.0, max(0.0, score))

    def _assess_target_audience(self, content: Dict[str, Any]) -> float:
        """Assess target audience definition quality"""
        target_audience = content.get("targetAudience", "")

        if not target_audience or len(target_audience.strip()) < 10:
            return 15.0

        score = 40.0  # Base score

        # Check for demographic details
        demographic_indicators = ["age", "gender", "income", "education", "location", "occupation"]
        for indicator in demographic_indicators:
            if indicator in target_audience.lower():
                score += 8.0

        # Check for behavioral details
        behavioral_indicators = ["use", "need", "want", "prefer", "habit", "behavior", "goal"]
        for indicator in behavioral_indicators:
            if indicator in target_audience.lower():
                score += 7.0

        # Check for specific vs generic
        specific_terms = ["specific", "particular", "exact", "precise"]
        generic_terms = ["everyone", "anyone", "all", "general", "broad"]

        specific_count = sum(1 for term in specific_terms if term in target_audience.lower())
        generic_count = sum(1 for term in generic_terms if term in target_audience.lower())

        score += (specific_count * 8) - (generic_count * 5)

        return min(100.0, max(0.0, score))

    def _assess_value_proposition(self, content: Dict[str, Any]) -> float:
        """Assess value proposition clarity and strength"""
        value_prop = content.get("valueProposition", "")

        if not value_prop or len(value_prop.strip()) < 15:
            return 20.0

        score = 45.0  # Base score

        # Check for value indicators
        value_indicators = ["save", "reduce", "increase", "improve", "faster", "easier", "better", "efficient"]
        for indicator in value_indicators:
            if indicator in value_prop.lower():
                score += 6.0

        # Check for competitive differentiation
        diff_indicators = ["unique", "different", "only", "first", "exclusive", "innovative"]
        for indicator in diff_indicators:
            if indicator in value_prop.lower():
                score += 8.0

        # Check for quantifiable benefits
        if any(char.isdigit() for char in value_prop):
            score += 10.0

        # Check for customer focus vs feature focus
        customer_focus = ["customer", "user", "you", "your", "benefit", "advantage"]
        feature_focus = ["feature", "function", "capability", "technology", "system"]

        customer_count = sum(1 for term in customer_focus if term in value_prop.lower())
        feature_count = sum(1 for term in feature_focus if term in value_prop.lower())

        if customer_count > feature_count:
            score += 10.0

        return min(100.0, max(0.0, score))

    def _assess_market_viability(self, content: Dict[str, Any]) -> float:
        """Assess market viability analysis quality"""
        market_analysis = content.get("marketAnalysis", {})

        if not market_analysis:
            return 25.0

        score = 30.0  # Base score

        # Check for market size information
        market_size = market_analysis.get("marketSize", "")
        if market_size and len(market_size.strip()) > 10:
            score += 20.0
            if any(char.isdigit() for char in market_size):
                score += 10.0

        # Check for competitor analysis
        competitors = market_analysis.get("competitors", [])
        if competitors:
            score += 15.0
            if len(competitors) >= 3:
                score += 10.0

        # Check for competitive advantage
        advantage = market_analysis.get("competitiveAdvantage", "")
        if advantage and len(advantage.strip()) > 20:
            score += 15.0

        # Check for market timing considerations
        timing_indicators = ["trend", "timing", "opportunity", "demand", "growth", "emerging"]
        market_text = str(market_analysis).lower()
        for indicator in timing_indicators:
            if indicator in market_text:
                score += 5.0

        return min(100.0, max(0.0, score))

    def _assess_prd_dimension(self, dimension: str, content: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Assess PRD generation specific dimensions"""
        if dimension == "requirement_completeness":
            return self._assess_requirement_completeness(content)
        elif dimension == "user_story_quality":
            return self._assess_user_story_quality(content)
        elif dimension == "business_alignment":
            return self._assess_business_alignment(content, context)
        elif dimension == "implementation_clarity":
            return self._assess_implementation_clarity(content)
        else:
            return 70.0

    def _assess_requirement_completeness(self, content: Dict[str, Any]) -> float:
        """Assess completeness of functional and non-functional requirements"""
        score = 30.0
        reqs = content.get("requirements", content.get("functionalRequirements", []))
        if isinstance(reqs, dict):
            func_reqs = reqs.get("functionalRequirements", [])
            non_func = reqs.get("nonFunctionalRequirements", [])
            constraints = reqs.get("constraints", [])
            assumptions = reqs.get("assumptions", [])
        else:
            func_reqs = reqs if isinstance(reqs, list) else []
            non_func = content.get("nonFunctionalRequirements", [])
            constraints = content.get("constraints", [])
            assumptions = content.get("assumptions", [])

        # Check functional requirements
        if func_reqs:
            score += min(25, len(func_reqs) * 3)
            # Check for acceptance criteria
            with_criteria = sum(1 for r in func_reqs if isinstance(r, dict) and r.get("acceptanceCriteria"))
            if func_reqs:
                score += (with_criteria / len(func_reqs)) * 15

        # Check non-functional requirements
        if non_func:
            score += min(15, len(non_func) * 3)

        # Check for constraints and assumptions
        if constraints:
            score += 5
        if assumptions:
            score += 5

        return min(100.0, max(0.0, score))

    def _assess_user_story_quality(self, content: Dict[str, Any]) -> float:
        """Assess quality of user stories using INVEST criteria"""
        score = 25.0
        stories = content.get("userStories", [])
        if isinstance(stories, dict):
            stories = stories.get("stories", stories.get("userStories", []))

        if not stories:
            return 15.0

        score += min(20, len(stories) * 2)

        invest_scores = []
        for story in stories:
            if not isinstance(story, dict):
                continue
            story_score = 0
            # Check for role/action/benefit structure
            has_role = bool(story.get("role") or story.get("asA"))
            has_action = bool(story.get("action") or story.get("iWant"))
            has_benefit = bool(story.get("benefit") or story.get("soThat"))
            if has_role: story_score += 15
            if has_action: story_score += 15
            if has_benefit: story_score += 15
            # Check acceptance criteria
            criteria = story.get("acceptanceCriteria", [])
            if criteria:
                story_score += min(25, len(criteria) * 5)
            # Check priority
            if story.get("priority"):
                story_score += 10
            # Check INVEST validation
            invest = story.get("investValidation", {})
            if invest:
                invest_count = sum(1 for v in invest.values() if v)
                story_score += invest_count * 3
            invest_scores.append(min(100, story_score))

        if invest_scores:
            avg_story = sum(invest_scores) / len(invest_scores)
            score += avg_story * 0.55

        return min(100.0, max(0.0, score))

    def _assess_business_alignment(self, content: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Assess alignment of PRD with business goals from idea refinement"""
        score = 40.0
        idea_data = context.get("idea_refinement", context.get("ideaRefinement", {}))

        # Check that value proposition is reflected
        value_prop = idea_data.get("valueProposition", "")
        content_str = str(content).lower()
        if value_prop and len(value_prop) > 10:
            vp_words = set(value_prop.lower().split())
            matches = sum(1 for w in vp_words if len(w) > 4 and w in content_str)
            score += min(20, matches * 4)

        # Check for prioritization
        features = content.get("prioritizedFeatures", {})
        if features:
            score += 15
            if isinstance(features, dict) and features.get("features"):
                mvp_count = sum(1 for f in features["features"] if isinstance(f, dict) and f.get("mvpCandidate"))
                if mvp_count > 0:
                    score += 10

        # Check for success metrics
        if content.get("successMetrics") or content.get("prdDocument", {}).get("successMetrics"):
            score += 15

        return min(100.0, max(0.0, score))

    def _assess_implementation_clarity(self, content: Dict[str, Any]) -> float:
        """Assess how clearly the PRD guides implementation"""
        score = 30.0
        prd = content.get("prdDocument", content)

        # Check for technical notes
        reqs = prd.get("functionalRequirements", [])
        if isinstance(reqs, list):
            with_tech_notes = sum(1 for r in reqs if isinstance(r, dict) and r.get("technicalNotes"))
            if reqs:
                score += (with_tech_notes / len(reqs)) * 20

        # Check for constraints/assumptions clarity
        if prd.get("constraints"):
            score += 10
        if prd.get("outOfScope"):
            score += 10

        # Check for success metrics with measurement methods
        metrics = prd.get("successMetrics", [])
        if metrics:
            score += min(15, len(metrics) * 3)
            with_method = sum(1 for m in metrics if isinstance(m, dict) and m.get("measurementMethod"))
            if metrics:
                score += (with_method / len(metrics)) * 15

        return min(100.0, max(0.0, score))

    def _assess_ux_dimension(self, dimension: str, content: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Assess UX requirements specific dimensions"""
        if dimension == "user_journey_completeness":
            return self._assess_user_journey_completeness(content)
        elif dimension == "wireframe_quality":
            return self._assess_wireframe_quality(content)
        elif dimension == "accessibility_compliance":
            return self._assess_accessibility_compliance(content)
        elif dimension == "implementation_feasibility":
            return self._assess_ux_implementation_feasibility(content, context)
        else:
            return 70.0

    def _assess_user_journey_completeness(self, content: Dict[str, Any]) -> float:
        """Assess completeness and quality of user journey maps"""
        score = 20.0
        journeys = content.get("userJourneys", [])
        if not journeys:
            return 10.0

        score += min(20, len(journeys) * 5)

        journey_scores = []
        for journey in journeys:
            if not isinstance(journey, dict):
                continue
            j_score = 0
            if journey.get("name") or journey.get("journeyName"):
                j_score += 10
            if journey.get("persona") or journey.get("userPersona"):
                j_score += 15
            steps = journey.get("steps", [])
            if steps:
                j_score += min(30, len(steps) * 5)
                # Check step detail
                detailed = sum(1 for s in steps if isinstance(s, dict) and
                               (s.get("userActions") or s.get("action")) and
                               (s.get("systemResponses") or s.get("systemResponse")))
                if steps:
                    j_score += (detailed / len(steps)) * 20
            if journey.get("painPoints") or journey.get("opportunities"):
                j_score += 15
            if journey.get("successCriteria"):
                j_score += 10
            journey_scores.append(min(100, j_score))

        if journey_scores:
            score += (sum(journey_scores) / len(journey_scores)) * 0.60

        return min(100.0, max(0.0, score))

    def _assess_wireframe_quality(self, content: Dict[str, Any]) -> float:
        """Assess quality of wireframe specifications"""
        score = 20.0
        wireframes = content.get("wireframes", [])
        if not wireframes:
            return 10.0

        score += min(15, len(wireframes) * 3)

        wf_scores = []
        for wf in wireframes:
            if not isinstance(wf, dict):
                continue
            w_score = 0
            if wf.get("name") or wf.get("screenName"):
                w_score += 10
            if wf.get("screenType"):
                w_score += 10
            elements = wf.get("elements", [])
            if elements:
                w_score += min(25, len(elements) * 3)
            interactions = wf.get("interactions", [])
            if interactions:
                w_score += min(25, len(interactions) * 5)
            if wf.get("responsive") or wf.get("notes"):
                w_score += 10
            if wf.get("userStoryIds") or wf.get("userJourneyRef"):
                w_score += 10
            wf_scores.append(min(100, w_score))

        if wf_scores:
            score += (sum(wf_scores) / len(wf_scores)) * 0.65

        return min(100.0, max(0.0, score))

    def _assess_accessibility_compliance(self, content: Dict[str, Any]) -> float:
        """Assess WCAG accessibility compliance quality"""
        score = 20.0

        # Check accessibility checklist
        checklist = content.get("accessibilityChecklist", [])
        if checklist:
            score += min(20, len(checklist) * 2)
            validated = sum(1 for item in checklist if isinstance(item, dict) and item.get("validated"))
            if checklist:
                score += (validated / len(checklist)) * 30

        # Check component specs for accessibility
        specs = content.get("componentSpecs", [])
        with_a11y = sum(1 for s in specs if isinstance(s, dict) and s.get("accessibility"))
        if specs:
            score += (with_a11y / len(specs)) * 20

        # Check for WCAG level compliance
        report = content.get("accessibilityReport", content.get("qualityAssessment", {}))
        if isinstance(report, dict):
            compliance = report.get("wcagCompliance", "")
            if compliance == "AAA":
                score += 15
            elif compliance == "AA":
                score += 10
            elif compliance == "A":
                score += 5

        return min(100.0, max(0.0, score))

    def _assess_ux_implementation_feasibility(self, content: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Assess UX feasibility based on technical constraints"""
        score = 40.0

        # Check component specs exist with implementation details
        specs = content.get("componentSpecs", [])
        if specs:
            score += min(15, len(specs) * 2)
            with_deps = sum(1 for s in specs if isinstance(s, dict) and s.get("dependencies"))
            with_responsive = sum(1 for s in specs if isinstance(s, dict) and
                                  (s.get("responsive") or s.get("responsiveness")))
            if specs:
                score += (with_deps / len(specs)) * 15
                score += (with_responsive / len(specs)) * 15

        # Check design system completeness
        design_system = content.get("designSystem", {})
        if design_system:
            ds_sections = ["colors", "typography", "spacing"]
            present = sum(1 for s in ds_sections if design_system.get(s))
            score += present * 5

        return min(100.0, max(0.0, score))

    def _assess_tech_analysis_dimension(self, dimension: str, content: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Assess technical analysis specific dimensions"""
        if dimension == "architectural_soundness":
            return self._assess_architectural_soundness(content)
        elif dimension == "feasibility_assessment":
            return self._assess_feasibility(content)
        elif dimension == "risk_assessment":
            return self._assess_risk_quality(content)
        elif dimension == "multi_llm_consensus":
            return self._assess_consensus_quality(content)
        else:
            return 70.0

    def _assess_architectural_soundness(self, content: Dict[str, Any]) -> float:
        """Assess quality of architecture recommendation"""
        score = 25.0
        arch = content.get("architectureRecommendation", content.get("architecture_recommendation", {}))

        if isinstance(arch, dict):
            if arch.get("pattern"):
                score += 15
            if arch.get("rationale"):
                score += 15
            if arch.get("consensusStrength", arch.get("consensus_strength", 0)) > 0.7:
                score += 10

        # Check technology stack
        stack = content.get("technologyStack", content.get("technology_stack", {}))
        if stack:
            category_count = len(stack) if isinstance(stack, dict) else 0
            score += min(20, category_count * 4)

        # Check for data model
        if content.get("dataModel") or content.get("data_model"):
            score += 10

        return min(100.0, max(0.0, score))

    def _assess_feasibility(self, content: Dict[str, Any]) -> float:
        """Assess quality of feasibility assessment"""
        score = 25.0
        feasibility = content.get("feasibilityAssessment", content.get("feasibility_assessment", {}))

        if isinstance(feasibility, dict):
            if feasibility.get("overallFeasibilityScore", feasibility.get("overall_feasibility_score")):
                score += 20
            if feasibility.get("estimatedTimelineWeeks", feasibility.get("estimated_timeline_weeks")):
                score += 15
            if feasibility.get("recommendedTeamSize", feasibility.get("recommended_team_size")):
                score += 10
            challenges = feasibility.get("keyChallenges", feasibility.get("key_challenges", []))
            if challenges:
                score += min(15, len(challenges) * 3)
            factors = feasibility.get("successFactors", feasibility.get("success_factors", []))
            if factors:
                score += min(15, len(factors) * 3)

        return min(100.0, max(0.0, score))

    def _assess_risk_quality(self, content: Dict[str, Any]) -> float:
        """Assess quality of risk assessment"""
        score = 25.0
        risks = content.get("riskAnalysis", content.get("risk_analysis", {}))

        if isinstance(risks, dict):
            risk_level = risks.get("overallRiskLevel", risks.get("overall_risk_level"))
            if risk_level is not None:
                score += 15
            top_risks = risks.get("topRisks", risks.get("top_risks", []))
            if top_risks:
                score += min(20, len(top_risks) * 4)
            categories = risks.get("riskCategories", risks.get("risk_categories", {}))
            if categories:
                score += min(15, len(categories) * 3)
            mitigation = risks.get("riskMitigationPriority", risks.get("risk_mitigation_priority", []))
            if mitigation:
                score += min(15, len(mitigation) * 3)
            monitoring = risks.get("monitoringRecommendations", risks.get("monitoring_recommendations", []))
            if monitoring:
                score += 10

        return min(100.0, max(0.0, score))

    def _assess_consensus_quality(self, content: Dict[str, Any]) -> float:
        """Assess quality of multi-LLM consensus analysis"""
        score = 30.0
        consensus = content.get("consensusResult", content.get("consensus_analysis", {}))

        if isinstance(consensus, dict):
            agreement = consensus.get("agreementScore", consensus.get("agreement_score", 0))
            if isinstance(agreement, (int, float)):
                score += agreement * 0.3

            confidence = consensus.get("confidenceLevel", consensus.get("confidence_level", 0))
            if isinstance(confidence, (int, float)):
                score += confidence * 0.2

            models = consensus.get("modelsUsed", consensus.get("models_used", []))
            if len(models) >= 3:
                score += 15
            elif len(models) >= 2:
                score += 10

            if consensus.get("conflictAreas", consensus.get("conflict_areas")):
                score += 5  # Having identified conflicts shows thoroughness

        return min(100.0, max(0.0, score))

    def _assess_playbook_dimension(self, dimension: str, content: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Assess implementation playbook specific dimensions"""
        if dimension == "context_integration":
            return self._assess_context_integration(content, context)
        elif dimension == "prompt_actionability":
            return self._assess_prompt_actionability(content)
        elif dimension == "testing_completeness":
            return self._assess_testing_completeness(content)
        elif dimension == "deployment_readiness":
            return self._assess_deployment_readiness(content)
        else:
            return 70.0

    def _assess_context_integration(self, content: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Assess how well the playbook integrates context from all stages"""
        score = 30.0
        integration = content.get("contextIntegration", content.get("context_integration", {}))

        if isinstance(integration, dict):
            if integration.get("allStagesIntegrated"):
                score += 25
            completeness = integration.get("completeness", 0)
            if isinstance(completeness, (int, float)):
                score += completeness * 0.3
            gaps = integration.get("gaps", [])
            if not gaps:
                score += 15
            elif len(gaps) <= 2:
                score += 5

        # Check if the playbook references previous stage outputs
        content_str = str(content).lower()
        stage_refs = ["idea", "prd", "requirement", "ux", "wireframe", "architecture", "technical"]
        ref_count = sum(1 for ref in stage_refs if ref in content_str)
        score += min(10, ref_count * 2)

        return min(100.0, max(0.0, score))

    def _assess_prompt_actionability(self, content: Dict[str, Any]) -> float:
        """Assess quality and actionability of coding prompts"""
        score = 20.0
        prompts = content.get("codingPrompts", content.get("coding_prompts", []))

        if not prompts:
            return 10.0

        score += min(15, len(prompts) * 2)

        prompt_scores = []
        for prompt in prompts:
            if not isinstance(prompt, dict):
                continue
            p_score = 0
            if prompt.get("title"):
                p_score += 10
            if prompt.get("description"):
                p_score += 10
            prompt_text = prompt.get("promptText", prompt.get("prompt_text", ""))
            if prompt_text:
                p_score += 15
                if len(prompt_text) > 100:
                    p_score += 10
            if prompt.get("expectedOutput", prompt.get("expected_output")):
                p_score += 15
            if prompt.get("estimatedTime", prompt.get("estimated_time")):
                p_score += 10
            if prompt.get("dependencies"):
                p_score += 10
            if prompt.get("complexity"):
                p_score += 5
            prompt_scores.append(min(100, p_score))

        if prompt_scores:
            score += (sum(prompt_scores) / len(prompt_scores)) * 0.65

        return min(100.0, max(0.0, score))

    def _assess_testing_completeness(self, content: Dict[str, Any]) -> float:
        """Assess completeness of testing strategy"""
        score = 20.0
        strategy = content.get("testingStrategy", content.get("testing_strategy", {}))

        if isinstance(strategy, dict):
            test_types = ["unitTests", "integrationTests", "e2eTests", "performanceTests", "securityTests"]
            for test_type in test_types:
                snake_type = re.sub(r'([A-Z])', r'_\1', test_type).lower().lstrip('_')
                tests = strategy.get(test_type, strategy.get(snake_type, []))
                if tests:
                    score += 10
                    if isinstance(tests, list) and len(tests) >= 3:
                        score += 5

            if strategy.get("coverageTarget", strategy.get("coverage_target", 0)):
                score += 10

        return min(100.0, max(0.0, score))

    def _assess_deployment_readiness(self, content: Dict[str, Any]) -> float:
        """Assess completeness of deployment guide"""
        score = 20.0
        guide = content.get("deploymentGuide", content.get("deployment_guide", {}))

        if isinstance(guide, dict):
            if guide.get("prerequisites"):
                score += 15
            steps = guide.get("steps", [])
            if steps:
                score += min(20, len(steps) * 4)
                detailed = sum(1 for s in steps if isinstance(s, dict) and s.get("commands"))
                if steps:
                    score += (detailed / len(steps)) * 15
            if guide.get("rollbackProcedure", guide.get("rollback_procedure")):
                score += 15
            if guide.get("postDeploymentValidation", guide.get("post_deployment_validation")):
                score += 10
            if guide.get("monitoring"):
                score += 5

        return min(100.0, max(0.0, score))

    def _assess_generic_dimension(self, dimension: str, content: Dict[str, Any]) -> float:
        """Generic dimension assessment for fallback"""
        # Simple content length and complexity assessment
        content_str = str(content)

        if len(content_str) < 50:
            return 30.0
        elif len(content_str) < 200:
            return 60.0
        elif len(content_str) < 500:
            return 75.0
        else:
            return 85.0

    def get_dynamic_threshold(self, stage: str, project_context: Dict[str, Any]) -> QualityThresholds:
        """Calculate context-aware quality thresholds"""
        base = self.base_thresholds.get(stage, {"minimum": 75, "recommended": 85})

        # Apply contextual adjustments
        complexity_adj = self.adjustment_factors["project_complexity"].get(project_context.get("complexity", "medium"), 0)
        experience_adj = self.adjustment_factors["user_experience"].get(
            project_context.get("user_experience", "intermediate"), 0
        )
        type_adj = self.adjustment_factors["project_type"].get(project_context.get("project_type", "mvp"), 0)

        total_adjustment = (complexity_adj + experience_adj + type_adj) / 3

        return QualityThresholds(
            minimum=max(60, min(95, base["minimum"] + total_adjustment)),
            recommended=max(70, min(98, base["recommended"] + total_adjustment)),
            adjustments_applied={
                "complexity": complexity_adj,
                "experience": experience_adj,
                "type": type_adj,
                "total": total_adjustment,
            },
            context_factors=project_context,
        )

    def _determine_gate_status(self, overall_score: float, thresholds: QualityThresholds) -> str:
        """Determine quality gate decision"""
        if overall_score >= thresholds.recommended:
            return "PROCEED_EXCELLENT"
        elif overall_score >= thresholds.minimum:
            return "PROCEED_WITH_CAUTION"
        else:
            return "BLOCK"

    def _generate_improvement_suggestions(
        self, stage: str, dimension_scores: Dict[str, float], content: Dict[str, Any], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate AI-powered improvement suggestions"""
        suggestions = []

        # Find lowest scoring dimensions
        sorted_dimensions = sorted(dimension_scores.items(), key=lambda x: x[1])

        for dimension, score in sorted_dimensions:
            if score < 80:  # Suggest improvements for scores below 80
                suggestion = self._get_dimension_improvement_suggestion(stage, dimension, score, content)
                if suggestion:
                    suggestions.append(suggestion)

        return suggestions[:3]  # Return top 3 suggestions

    def _get_dimension_improvement_suggestion(
        self, stage: str, dimension: str, score: float, content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get specific improvement suggestion for a dimension"""
        suggestions_map = {
            "idea_refinement": {
                "problem_clarity": {
                    "message": "Add more specific details about who experiences this problem and when",
                    "action": "Include specific user types, contexts, and problem scenarios",
                    "estimated_time": 10,
                },
                "target_audience_definition": {
                    "message": "Define your target audience with more demographic and behavioral details",
                    "action": "Add age range, occupation, income level, and specific needs",
                    "estimated_time": 8,
                },
                "value_proposition_clarity": {
                    "message": "Quantify the benefits and make the value more concrete",
                    "action": "Include specific metrics, percentages, or time savings",
                    "estimated_time": 12,
                },
                "market_viability": {
                    "message": "Research and add more market size and competitor information",
                    "action": "Include market research data and competitive analysis",
                    "estimated_time": 20,
                },
            },
            "prd_generation": {
                "requirement_completeness": {
                    "message": "Add more functional and non-functional requirements with acceptance criteria",
                    "action": "Define at least 8 functional requirements each with measurable acceptance criteria",
                    "estimated_time": 15,
                },
                "user_story_quality": {
                    "message": "Improve user stories with proper INVEST format and acceptance criteria",
                    "action": "Ensure each story has role/action/benefit structure plus 2-3 acceptance criteria",
                    "estimated_time": 12,
                },
                "business_alignment": {
                    "message": "Strengthen the connection between PRD requirements and business goals",
                    "action": "Map each major requirement to a business objective or value proposition",
                    "estimated_time": 10,
                },
                "implementation_clarity": {
                    "message": "Add technical notes, constraints, and measurement methods to requirements",
                    "action": "Include implementation guidance, out-of-scope items, and measurable success metrics",
                    "estimated_time": 15,
                },
            },
            "ux_requirements": {
                "user_journey_completeness": {
                    "message": "Add more detailed user journey maps with pain points and opportunities",
                    "action": "Map at least 3 key journeys with steps, user actions, system responses, and pain points",
                    "estimated_time": 20,
                },
                "wireframe_quality": {
                    "message": "Improve wireframe specs with more UI elements and interaction details",
                    "action": "Define elements, interactions, and responsive behavior for each screen",
                    "estimated_time": 25,
                },
                "accessibility_compliance": {
                    "message": "Add WCAG compliance checklist and accessibility annotations",
                    "action": "Include WCAG 2.1 AA checklist items with validation status for each component",
                    "estimated_time": 15,
                },
                "implementation_feasibility": {
                    "message": "Add implementation details like dependencies and responsive specs to components",
                    "action": "Define component dependencies, responsive breakpoints, and design system tokens",
                    "estimated_time": 15,
                },
            },
            "technical_analysis": {
                "architectural_soundness": {
                    "message": "Provide clearer architecture rationale and technology stack details",
                    "action": "Include architecture pattern, rationale, consensus strength, and detailed tech stack",
                    "estimated_time": 20,
                },
                "feasibility_assessment": {
                    "message": "Add timeline estimates, team sizing, and key challenges",
                    "action": "Include estimated weeks, team size, key challenges, and success factors",
                    "estimated_time": 15,
                },
                "risk_assessment": {
                    "message": "Expand risk analysis with mitigation strategies and monitoring recommendations",
                    "action": "Categorize risks by type, add mitigation priority and monitoring plan",
                    "estimated_time": 15,
                },
                "multi_llm_consensus": {
                    "message": "Increase consensus quality by using more LLM models",
                    "action": "Use at least 3 models and document agreement scores and conflict areas",
                    "estimated_time": 10,
                },
            },
            "implementation_playbook": {
                "context_integration": {
                    "message": "Improve integration of outputs from all previous stages",
                    "action": "Reference and incorporate key decisions from idea, PRD, UX, and tech stages",
                    "estimated_time": 15,
                },
                "prompt_actionability": {
                    "message": "Make coding prompts more specific and actionable",
                    "action": "Add expected outputs, time estimates, dependencies, and complexity to each prompt",
                    "estimated_time": 20,
                },
                "testing_completeness": {
                    "message": "Expand testing strategy to cover more test types and targets",
                    "action": "Include unit, integration, e2e, performance, and security test plans with coverage targets",
                    "estimated_time": 15,
                },
                "deployment_readiness": {
                    "message": "Add deployment prerequisites, rollback procedures, and post-deploy validation",
                    "action": "Define step-by-step deployment with commands, rollback plan, and monitoring setup",
                    "estimated_time": 15,
                },
            },
        }

        stage_suggestions = suggestions_map.get(stage, {})
        dimension_suggestion = stage_suggestions.get(dimension)

        if dimension_suggestion:
            return {
                "dimension": dimension,
                "current_score": score,
                "potential_gain": min(20, 85 - score),
                **dimension_suggestion,
            }

        return None

    def _validate_context_consistency(self, stage: str, content: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate consistency with previous stages"""
        # For idea refinement stage, no previous context to validate
        if stage == "idea_refinement":
            return {"consistency_score": 100.0, "issues": []}

        # For other stages, check against previous stage data
        # This would be implemented as the other stages are developed
        return {"consistency_score": 95.0, "issues": []}

    def _calculate_confidence_level(self, dimension_scores: Dict[str, float], content: Dict[str, Any]) -> float:
        """Calculate confidence level in the quality assessment"""
        if not dimension_scores:
            return 0.0

        # Base confidence on score variance and content completeness
        score_variance = statistics.variance(dimension_scores.values()) if len(dimension_scores) > 1 else 0
        content_completeness = min(100, len(str(content)) / 10)  # Simple completeness measure

        # Lower variance means higher confidence
        variance_confidence = max(0, 100 - score_variance)

        # Combine factors
        confidence = (variance_confidence * 0.7) + (content_completeness * 0.3)

        return min(100.0, max(0.0, confidence))

    def _estimate_improvement_time(self, dimension_scores: Dict[str, float], improvements: List[Dict[str, Any]]) -> int:
        """Estimate time needed for improvements"""
        if not improvements:
            return 0

        total_time = sum(improvement.get("estimated_time", 10) for improvement in improvements)
        return min(60, total_time)  # Cap at 60 minutes


class ContextualQualityValidator:
    """Validates quality across multiple stages for consistency"""

    def __init__(self):
        self.context_dependencies = {
            "prd_generation": ["idea_refinement"],
            "ux_requirements": ["idea_refinement", "prd_generation"],
            "technical_analysis": ["idea_refinement", "prd_generation", "ux_requirements"],
            "implementation_playbook": ["idea_refinement", "prd_generation", "technical_analysis"],
        }

    def validate_context_quality(self, current_stage: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure current stage builds on high-quality previous work"""
        required_stages = self.context_dependencies.get(current_stage, [])

        context_quality_scores = {}
        consistency_issues = []
        enhancement_opportunities = []

        for required_stage in required_stages:
            stage_data = project_data.get(required_stage, {})
            stage_quality = stage_data.get("qualityMetrics", {}).get("overall", 0)

            context_quality_scores[required_stage] = stage_quality

            # Check for consistency issues
            if stage_quality < 75:
                consistency_issues.append(
                    {
                        "stage": required_stage,
                        "issue": "Low quality foundation may impact current stage",
                        "recommendation": "Consider improving previous stage before proceeding",
                    }
                )

            # Identify enhancement opportunities
            if stage_quality < 85:
                enhancement_opportunities.append(
                    {
                        "stage": required_stage,
                        "opportunity": f"Improving {required_stage} quality could enhance {current_stage} outcomes",
                        "potential_impact": f"+{(85 - stage_quality) * 0.3:.1f} quality points",
                    }
                )

        overall_context_strength = (
            sum(context_quality_scores.values()) / len(context_quality_scores) if context_quality_scores else 0
        )

        return {
            "context_scores": context_quality_scores,
            "consistency_issues": consistency_issues,
            "enhancement_opportunities": enhancement_opportunities,
            "overall_context_strength": overall_context_strength,
        }
