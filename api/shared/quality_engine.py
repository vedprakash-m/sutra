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
        }

        self.base_thresholds = {
            "idea_refinement": {"minimum": 75, "recommended": 85},
            "prd_generation": {"minimum": 80, "recommended": 90},
            "ux_requirements": {"minimum": 82, "recommended": 90},
            "technical_analysis": {"minimum": 85, "recommended": 92},
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
                return self._assess_generic_dimension(dimension, content)  # TODO: Implement in Task 2.4
            elif stage == "ux_requirements":
                return self._assess_generic_dimension(dimension, content)  # TODO: Implement in Task 2.5
            elif stage == "technical_analysis":
                return self._assess_generic_dimension(dimension, content)  # TODO: Implement in Task 2.6
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
            }
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
