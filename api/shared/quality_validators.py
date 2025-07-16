"""
Cross-stage quality validators for the Forge module.
Ensures consistency and quality progression between development stages.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from shared.quality_engine import QualityAssessmentEngine, QualityAssessmentResult

logger = logging.getLogger(__name__)


@dataclass
class CrossStageValidationResult:
    """Result of cross-stage validation check"""

    is_consistent: bool
    consistency_score: float
    validation_errors: List[str]
    validation_warnings: List[str]
    context_gaps: List[str]
    recommendations: List[str]
    quality_impact: str  # "positive", "neutral", "negative"


@dataclass
class ContextHandoff:
    """Context information passed between stages"""

    source_stage: str
    target_stage: str
    context_data: Dict[str, Any]
    quality_metrics: Dict[str, float]
    validation_timestamp: str
    consistency_score: float


class CrossStageQualityValidator:
    """Validates quality and consistency across Forge development stages"""

    def __init__(self):
        self.quality_engine = QualityAssessmentEngine()

        # Define stage dependencies and required context
        self.stage_dependencies = {
            "prd_generation": {
                "requires": ["idea_refinement"],
                "context_keys": ["problemStatement", "targetAudience", "valueProposition", "marketContext", "qualityMetrics"],
                "quality_threshold": 75.0,
            },
            "ux_requirements": {
                "requires": ["idea_refinement", "prd_generation"],
                "context_keys": [
                    "problemStatement",
                    "targetAudience",
                    "userStories",
                    "functionalRequirements",
                    "qualityMetrics",
                ],
                "quality_threshold": 80.0,
            },
            "technical_analysis": {
                "requires": ["idea_refinement", "prd_generation", "ux_requirements"],
                "context_keys": [
                    "problemStatement",
                    "functionalRequirements",
                    "userJourneys",
                    "designSpecs",
                    "qualityMetrics",
                ],
                "quality_threshold": 82.0,
            },
            "implementation_playbook": {
                "requires": ["idea_refinement", "prd_generation", "ux_requirements", "technical_analysis"],
                "context_keys": [
                    "problemStatement",
                    "technicalArchitecture",
                    "designSpecs",
                    "implementationSpecs",
                    "qualityMetrics",
                ],
                "quality_threshold": 85.0,
            },
        }

        # Define context consistency rules
        self.consistency_rules = {
            ("idea_refinement", "prd_generation"): {
                "target_audience_alignment": {
                    "source_key": "targetAudience",
                    "target_key": "userPersonas",
                    "similarity_threshold": 0.8,
                    "weight": 0.3,
                },
                "problem_consistency": {
                    "source_key": "problemStatement",
                    "target_key": "problemDefinition",
                    "similarity_threshold": 0.85,
                    "weight": 0.4,
                },
                "value_proposition_alignment": {
                    "source_key": "valueProposition",
                    "target_key": "businessObjectives",
                    "similarity_threshold": 0.75,
                    "weight": 0.3,
                },
            },
            ("prd_generation", "ux_requirements"): {
                "user_story_consistency": {
                    "source_key": "userStories",
                    "target_key": "userJourneys",
                    "similarity_threshold": 0.8,
                    "weight": 0.4,
                },
                "functional_requirement_alignment": {
                    "source_key": "functionalRequirements",
                    "target_key": "featureSpecs",
                    "similarity_threshold": 0.85,
                    "weight": 0.6,
                },
            },
        }

    def validate_stage_readiness(self, target_stage: str, project_data: Dict[str, Any]) -> CrossStageValidationResult:
        """Validate that a project is ready to progress to the target stage"""

        if target_stage not in self.stage_dependencies:
            return CrossStageValidationResult(
                is_consistent=False,
                consistency_score=0.0,
                validation_errors=[f"Unknown target stage: {target_stage}"],
                validation_warnings=[],
                context_gaps=[],
                recommendations=[],
                quality_impact="negative",
            )

        stage_config = self.stage_dependencies[target_stage]
        validation_errors = []
        validation_warnings = []
        context_gaps = []
        recommendations = []

        # Check prerequisite stages exist and meet quality thresholds
        for required_stage in stage_config["requires"]:
            stage_data = project_data.get("forgeData", {}).get(required_stage)

            if not stage_data:
                validation_errors.append(f"Missing required stage: {required_stage}")
                continue

            # Check quality threshold
            stage_quality = stage_data.get("qualityMetrics", {}).get("overall", 0)
            required_quality = stage_config["quality_threshold"]

            if stage_quality < required_quality:
                validation_errors.append(
                    f"Stage {required_stage} quality ({stage_quality:.1f}%) below required threshold ({required_quality:.1f}%)"
                )
                recommendations.append(f"Improve {required_stage} quality before proceeding to {target_stage}")

        # Check context completeness
        available_context = self._extract_available_context(project_data)
        for required_key in stage_config["context_keys"]:
            if required_key not in available_context or not available_context[required_key]:
                context_gaps.append(f"Missing context: {required_key}")

        # Calculate consistency score
        consistency_score = self._calculate_stage_readiness_score(target_stage, project_data, validation_errors, context_gaps)

        # Determine quality impact
        quality_impact = "positive" if consistency_score >= 0.8 else "neutral" if consistency_score >= 0.6 else "negative"

        return CrossStageValidationResult(
            is_consistent=len(validation_errors) == 0 and consistency_score >= 0.7,
            consistency_score=consistency_score,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings,
            context_gaps=context_gaps,
            recommendations=recommendations,
            quality_impact=quality_impact,
        )

    def validate_cross_stage_consistency(
        self, source_stage: str, target_stage: str, project_data: Dict[str, Any]
    ) -> CrossStageValidationResult:
        """Validate consistency between two specific stages"""

        stage_pair = (source_stage, target_stage)
        if stage_pair not in self.consistency_rules:
            return CrossStageValidationResult(
                is_consistent=True,
                consistency_score=1.0,
                validation_errors=[],
                validation_warnings=[f"No consistency rules defined for {source_stage} -> {target_stage}"],
                context_gaps=[],
                recommendations=[],
                quality_impact="neutral",
            )

        rules = self.consistency_rules[stage_pair]
        source_data = project_data.get("forgeData", {}).get(source_stage, {})
        target_data = project_data.get("forgeData", {}).get(target_stage, {})

        validation_errors = []
        validation_warnings = []
        recommendations = []
        total_score = 0.0
        total_weight = 0.0

        for rule_name, rule_config in rules.items():
            source_value = source_data.get(rule_config["source_key"])
            target_value = target_data.get(rule_config["target_key"])

            if not source_value or not target_value:
                validation_warnings.append(f"Missing data for consistency check: {rule_name}")
                continue

            # Calculate similarity score
            similarity = self._calculate_content_similarity(source_value, target_value)
            threshold = rule_config["similarity_threshold"]
            weight = rule_config["weight"]

            if similarity < threshold:
                validation_errors.append(
                    f"Consistency issue in {rule_name}: similarity {similarity:.2f} below threshold {threshold:.2f}"
                )
                recommendations.append(
                    f"Review {rule_config['target_key']} to ensure alignment with {rule_config['source_key']}"
                )

            total_score += similarity * weight
            total_weight += weight

        consistency_score = total_score / total_weight if total_weight > 0 else 0.0
        quality_impact = "positive" if consistency_score >= 0.8 else "neutral" if consistency_score >= 0.6 else "negative"

        return CrossStageValidationResult(
            is_consistent=len(validation_errors) == 0,
            consistency_score=consistency_score,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings,
            context_gaps=[],
            recommendations=recommendations,
            quality_impact=quality_impact,
        )

    def prepare_context_handoff(self, source_stage: str, target_stage: str, project_data: Dict[str, Any]) -> ContextHandoff:
        """Prepare context data for handoff between stages"""

        source_data = project_data.get("forgeData", {}).get(source_stage, {})

        # Extract relevant context based on target stage requirements
        if target_stage in self.stage_dependencies:
            required_keys = self.stage_dependencies[target_stage]["context_keys"]
            available_context = self._extract_available_context(project_data)

            context_data = {key: available_context.get(key) for key in required_keys if key in available_context}
        else:
            context_data = source_data

        # Extract quality metrics
        quality_metrics = source_data.get("qualityMetrics", {})

        # Calculate consistency score
        consistency_validation = self.validate_cross_stage_consistency(source_stage, target_stage, project_data)

        return ContextHandoff(
            source_stage=source_stage,
            target_stage=target_stage,
            context_data=context_data,
            quality_metrics=quality_metrics,
            validation_timestamp=datetime.now(timezone.utc).isoformat(),
            consistency_score=consistency_validation.consistency_score,
        )

    def validate_quality_progression(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate quality progression across all completed stages"""

        forge_data = project_data.get("forgeData", {})
        completed_stages = [stage for stage in forge_data.keys() if forge_data[stage].get("status") == "completed"]

        quality_progression = []
        quality_regression_warnings = []
        overall_trajectory = "improving"

        for i, stage in enumerate(completed_stages):
            stage_quality = forge_data[stage].get("qualityMetrics", {}).get("overall", 0)
            expected_threshold = self.stage_dependencies.get(stage, {}).get("quality_threshold", 75)

            quality_progression.append(
                {
                    "stage": stage,
                    "quality_score": stage_quality,
                    "expected_threshold": expected_threshold,
                    "meets_threshold": stage_quality >= expected_threshold,
                    "order": i + 1,
                }
            )

            # Check for quality regression
            if i > 0 and stage_quality < quality_progression[i - 1]["quality_score"] - 5:
                quality_regression_warnings.append(
                    f"Quality regression detected: {stage} ({stage_quality:.1f}%) lower than previous stage"
                )
                overall_trajectory = "declining"

        # Calculate overall project quality health
        if quality_progression:
            avg_quality = sum(stage["quality_score"] for stage in quality_progression) / len(quality_progression)
            quality_trend = (
                "increasing"
                if len(quality_progression) < 2
                else (
                    "increasing"
                    if quality_progression[-1]["quality_score"] > quality_progression[0]["quality_score"]
                    else (
                        "stable"
                        if abs(quality_progression[-1]["quality_score"] - quality_progression[0]["quality_score"]) < 3
                        else "decreasing"
                    )
                )
            )
        else:
            avg_quality = 0
            quality_trend = "unknown"

        return {
            "quality_progression": quality_progression,
            "quality_regression_warnings": quality_regression_warnings,
            "overall_trajectory": overall_trajectory,
            "average_quality": avg_quality,
            "quality_trend": quality_trend,
            "completed_stages_count": len(completed_stages),
            "recommendations": self._generate_progression_recommendations(quality_progression),
        }

    def _extract_available_context(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract all available context from project data"""
        context = {}
        forge_data = project_data.get("forgeData", {})

        for stage_name, stage_data in forge_data.items():
            if isinstance(stage_data, dict):
                # Extract key information from each stage
                if stage_name == "idea_refinement":
                    context.update(
                        {
                            "problemStatement": stage_data.get("problemStatement"),
                            "targetAudience": stage_data.get("targetAudience"),
                            "valueProposition": stage_data.get("valueProposition"),
                            "marketContext": stage_data.get("marketContext"),
                        }
                    )
                elif stage_name == "prd_generation":
                    context.update(
                        {
                            "userStories": stage_data.get("userStories"),
                            "functionalRequirements": stage_data.get("functionalRequirements"),
                            "businessObjectives": stage_data.get("businessObjectives"),
                            "userPersonas": stage_data.get("userPersonas"),
                        }
                    )
                elif stage_name == "ux_requirements":
                    context.update(
                        {
                            "userJourneys": stage_data.get("userJourneys"),
                            "featureSpecs": stage_data.get("featureSpecs"),
                            "designSpecs": stage_data.get("designSpecs"),
                        }
                    )

                # Always include quality metrics
                if "qualityMetrics" in stage_data:
                    context["qualityMetrics"] = stage_data["qualityMetrics"]

        return context

    def _calculate_content_similarity(self, content1: Any, content2: Any) -> float:
        """Calculate similarity between two pieces of content"""
        if not content1 or not content2:
            return 0.0

        # Convert to strings for comparison
        str1 = str(content1).lower()
        str2 = str(content2).lower()

        # Simple similarity calculation based on common words and phrases
        words1 = set(str1.split())
        words2 = set(str2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _calculate_stage_readiness_score(
        self, target_stage: str, project_data: Dict[str, Any], validation_errors: List[str], context_gaps: List[str]
    ) -> float:
        """Calculate readiness score for progressing to target stage"""

        base_score = 1.0

        # Penalize for validation errors
        error_penalty = len(validation_errors) * 0.2
        base_score -= min(error_penalty, 0.6)  # Max 60% penalty for errors

        # Penalize for context gaps
        gap_penalty = len(context_gaps) * 0.1
        base_score -= min(gap_penalty, 0.3)  # Max 30% penalty for gaps

        # Check prerequisite stage qualities
        stage_config = self.stage_dependencies.get(target_stage, {})
        quality_bonus = 0.0

        for required_stage in stage_config.get("requires", []):
            stage_data = project_data.get("forgeData", {}).get(required_stage, {})
            stage_quality = stage_data.get("qualityMetrics", {}).get("overall", 0)

            if stage_quality > 85:
                quality_bonus += 0.1  # Bonus for high quality prerequisites

        final_score = max(0.0, min(1.0, base_score + quality_bonus))
        return final_score

    def _generate_progression_recommendations(self, quality_progression: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on quality progression"""

        recommendations = []

        if not quality_progression:
            return ["Complete at least one stage to receive quality recommendations"]

        # Check for stages below threshold
        below_threshold = [stage for stage in quality_progression if not stage["meets_threshold"]]
        if below_threshold:
            recommendations.append(f"Improve quality in {len(below_threshold)} stage(s) below threshold")

        # Check quality trend
        if len(quality_progression) >= 2:
            latest_quality = quality_progression[-1]["quality_score"]
            previous_quality = quality_progression[-2]["quality_score"]

            if latest_quality < previous_quality:
                recommendations.append("Quality is declining - review recent stage implementation for improvements")
            elif latest_quality > previous_quality + 10:
                recommendations.append("Excellent quality improvement trend - maintain current practices")

        # Check overall quality level
        avg_quality = sum(stage["quality_score"] for stage in quality_progression) / len(quality_progression)
        if avg_quality < 75:
            recommendations.append("Overall project quality below recommended level - consider stage reviews")
        elif avg_quality > 90:
            recommendations.append("Exceptional quality achieved - excellent for production readiness")

        return recommendations
