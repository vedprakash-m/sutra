"""
Cross-stage quality validators for the Forge module.
Ensures consistency and quality progression between development stages.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from shared.quality_engine import QualityAssessmentEngine, QualityResult

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
            ("ux_requirements", "technical_analysis"): {
                "design_feasibility": {
                    "source_key": "designSpecs",
                    "target_key": "implementationSpecs",
                    "similarity_threshold": 0.8,
                    "weight": 0.3,
                },
                "user_journey_technical_mapping": {
                    "source_key": "userJourneys",
                    "target_key": "technicalFlows",
                    "similarity_threshold": 0.75,
                    "weight": 0.4,
                },
                "accessibility_compliance": {
                    "source_key": "accessibilityRequirements",
                    "target_key": "accessibilityImplementation",
                    "similarity_threshold": 0.9,
                    "weight": 0.3,
                },
            },
            ("technical_analysis", "implementation_playbook"): {
                "architecture_consistency": {
                    "source_key": "technicalArchitecture",
                    "target_key": "implementationArchitecture",
                    "similarity_threshold": 0.95,
                    "weight": 0.4,
                },
                "technology_stack_alignment": {
                    "source_key": "technologyStack",
                    "target_key": "implementationTechStack",
                    "similarity_threshold": 0.95,
                    "weight": 0.3,
                },
                "risk_mitigation_coverage": {
                    "source_key": "riskAssessment",
                    "target_key": "riskMitigationPlan",
                    "similarity_threshold": 0.85,
                    "weight": 0.3,
                },
            },
            # Cross-stage validation (idea -> ux)
            ("idea_refinement", "ux_requirements"): {
                "target_audience_to_personas": {
                    "source_key": "targetAudience",
                    "target_key": "userPersonas",
                    "similarity_threshold": 0.85,
                    "weight": 0.5,
                },
                "value_proposition_to_features": {
                    "source_key": "valueProposition",
                    "target_key": "coreFeatures",
                    "similarity_threshold": 0.75,
                    "weight": 0.5,
                },
            },
            # Cross-stage validation (idea -> technical)
            ("idea_refinement", "technical_analysis"): {
                "problem_to_solution_alignment": {
                    "source_key": "problemStatement",
                    "target_key": "solutionApproach",
                    "similarity_threshold": 0.8,
                    "weight": 0.4,
                },
                "market_to_scalability": {
                    "source_key": "marketContext",
                    "target_key": "scalabilityRequirements",
                    "similarity_threshold": 0.7,
                    "weight": 0.3,
                },
                "viability_to_feasibility": {
                    "source_key": "marketViability",
                    "target_key": "technicalFeasibility",
                    "similarity_threshold": 0.75,
                    "weight": 0.3,
                },
            },
            # Cross-stage validation (prd -> technical)
            ("prd_generation", "technical_analysis"): {
                "requirements_to_architecture": {
                    "source_key": "functionalRequirements",
                    "target_key": "architecturalComponents",
                    "similarity_threshold": 0.85,
                    "weight": 0.5,
                },
                "non_functional_to_technical": {
                    "source_key": "nonFunctionalRequirements",
                    "target_key": "technicalConstraints",
                    "similarity_threshold": 0.8,
                    "weight": 0.5,
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

    def detect_context_gaps(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect missing context information across stages with AI-powered gap analysis.

        Returns comprehensive gap detection with:
        - Missing required fields per stage
        - Cross-stage context inconsistencies
        - Quality impact assessment
        - Specific remediation suggestions
        """

        forge_data = project_data.get("forgeData", {})
        detected_gaps = []
        impact_analysis = {}
        remediation_suggestions = []

        # Check each completed stage for context completeness
        for stage_name, stage_config in self.stage_dependencies.items():
            stage_data = forge_data.get(stage_name, {})
            if not stage_data:
                continue

            required_context = stage_config.get("context_keys", [])
            available_context = self._extract_available_context(project_data)

            missing_keys = []
            for required_key in required_context:
                if required_key not in available_context or not available_context[required_key]:
                    missing_keys.append(required_key)

            if missing_keys:
                gap_severity = "high" if len(missing_keys) > 3 else "medium" if len(missing_keys) > 1 else "low"

                detected_gaps.append(
                    {
                        "stage": stage_name,
                        "missing_context_keys": missing_keys,
                        "severity": gap_severity,
                        "impact": self._assess_gap_impact(stage_name, missing_keys),
                        "required_for_next_stages": self._identify_dependent_stages(stage_name),
                    }
                )

                # Generate specific remediation suggestions
                for key in missing_keys:
                    remediation_suggestions.append(self._generate_remediation_suggestion(stage_name, key))

        # Analyze cross-stage consistency gaps
        consistency_gaps = self._detect_consistency_gaps(project_data)

        # Calculate overall context completeness score
        total_required_context = sum(len(config.get("context_keys", [])) for config in self.stage_dependencies.values())
        available_context = self._extract_available_context(project_data)
        provided_context = sum(1 for value in available_context.values() if value)

        completeness_score = (provided_context / total_required_context * 100) if total_required_context > 0 else 0

        return {
            "detected_gaps": detected_gaps,
            "consistency_gaps": consistency_gaps,
            "completeness_score": completeness_score,
            "gap_count": len(detected_gaps),
            "high_severity_gaps": len([g for g in detected_gaps if g["severity"] == "high"]),
            "remediation_suggestions": remediation_suggestions,
            "quality_impact_summary": self._summarize_quality_impact(detected_gaps),
            "recommendation": self._generate_overall_gap_recommendation(completeness_score, detected_gaps),
        }

    def generate_ai_improvement_suggestions(
        self, project_data: Dict[str, Any], target_stage: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate AI-powered improvement suggestions based on project quality analysis.

        Provides:
        - Specific improvement actions per stage
        - Priority-ranked suggestions
        - Estimated quality impact
        - Implementation effort estimation
        - Success probability scoring
        """

        forge_data = project_data.get("forgeData", {})
        suggestions = []

        # Analyze each stage for improvement opportunities
        stages_to_analyze = [target_stage] if target_stage else forge_data.keys()

        for stage_name in stages_to_analyze:
            stage_data = forge_data.get(stage_name, {})
            if not stage_data:
                continue

            quality_metrics = stage_data.get("qualityMetrics", {})
            overall_quality = quality_metrics.get("overall", 0)

            # Generate suggestions based on quality dimensions
            for dimension, score in quality_metrics.items():
                if dimension == "overall":
                    continue

                if score < 80:  # Below recommended threshold
                    suggestion = self._generate_dimension_improvement(stage_name, dimension, score, stage_data)
                    if suggestion:
                        suggestions.append(suggestion)

        # Add cross-stage consistency improvements
        consistency_improvements = self._generate_consistency_improvements(project_data)
        suggestions.extend(consistency_improvements)

        # Add quality progression improvements
        progression_analysis = self.validate_quality_progression(project_data)
        if progression_analysis.get("quality_regression_warnings"):
            suggestions.append(
                {
                    "type": "quality_regression",
                    "priority": "high",
                    "title": "Address Quality Regression",
                    "description": "Recent stages show declining quality compared to earlier stages",
                    "actions": self._generate_regression_recovery_actions(progression_analysis),
                    "estimated_impact": "+15-25% quality improvement",
                    "implementation_effort": "medium",
                    "success_probability": 0.85,
                }
            )

        # Sort suggestions by priority and impact
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        suggestions.sort(key=lambda x: (priority_order.get(x.get("priority", "medium"), 2), -x.get("success_probability", 0)))

        return {
            "suggestions": suggestions,
            "total_suggestions": len(suggestions),
            "high_priority_count": len([s for s in suggestions if s.get("priority") == "high"]),
            "estimated_total_improvement": self._calculate_total_improvement_potential(suggestions),
            "recommended_action_plan": self._generate_action_plan(suggestions),
            "success_indicators": self._define_success_indicators(suggestions),
        }

    def _detect_consistency_gaps(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect gaps in cross-stage consistency"""

        consistency_gaps = []
        forge_data = project_data.get("forgeData", {})

        for (source_stage, target_stage), rules in self.consistency_rules.items():
            if source_stage not in forge_data or target_stage not in forge_data:
                continue

            validation = self.validate_cross_stage_consistency(source_stage, target_stage, project_data)

            if validation.validation_errors:
                consistency_gaps.append(
                    {
                        "source_stage": source_stage,
                        "target_stage": target_stage,
                        "consistency_score": validation.consistency_score,
                        "issues": validation.validation_errors,
                        "impact": validation.quality_impact,
                        "recommendations": validation.recommendations,
                    }
                )

        return consistency_gaps

    def _assess_gap_impact(self, stage_name: str, missing_keys: List[str]) -> str:
        """Assess the impact of missing context keys"""

        critical_keys = {
            "idea_refinement": ["problemStatement", "targetAudience", "valueProposition"],
            "prd_generation": ["functionalRequirements", "userStories"],
            "ux_requirements": ["userJourneys", "designSpecs"],
            "technical_analysis": ["technicalArchitecture", "technologyStack"],
        }

        stage_critical = critical_keys.get(stage_name, [])
        critical_missing = [key for key in missing_keys if key in stage_critical]

        if critical_missing:
            return "High - Critical context missing, will severely impact subsequent stages"
        elif len(missing_keys) > 3:
            return "Medium - Multiple context elements missing, may cause quality issues"
        else:
            return "Low - Minor gaps, can be addressed during stage refinement"

    def _identify_dependent_stages(self, stage_name: str) -> List[str]:
        """Identify stages that depend on the given stage"""

        dependent_stages = []
        for target_stage, config in self.stage_dependencies.items():
            if stage_name in config.get("requires", []):
                dependent_stages.append(target_stage)
        return dependent_stages

    def _generate_remediation_suggestion(self, stage_name: str, missing_key: str) -> Dict[str, str]:
        """Generate specific remediation suggestion for missing context"""

        remediation_templates = {
            "problemStatement": {
                "action": "Define clear problem statement",
                "guidance": "Articulate the core problem your solution addresses, including who faces this problem and why it matters",
                "example": "Small businesses struggle to manage customer relationships effectively, leading to lost sales opportunities",
            },
            "targetAudience": {
                "action": "Identify target audience",
                "guidance": "Define specific user segments, demographics, behaviors, and pain points",
                "example": "Small business owners (10-50 employees) in retail and services sectors",
            },
            "valueProposition": {
                "action": "Articulate unique value proposition",
                "guidance": "Explain what makes your solution valuable and different from alternatives",
                "example": "Automated CRM that requires zero setup and learns from existing customer interactions",
            },
            "functionalRequirements": {
                "action": "Document functional requirements",
                "guidance": "List specific capabilities and features the system must provide",
                "example": "System must allow users to create, read, update, and delete customer records with contact history",
            },
            "userJourneys": {
                "action": "Map user journeys",
                "guidance": "Document step-by-step flows for key user interactions and workflows",
                "example": "New user onboarding: Sign up → Profile setup → Import data → First interaction → Success confirmation",
            },
            "technicalArchitecture": {
                "action": "Define technical architecture",
                "guidance": "Specify system architecture, components, data flow, and integration patterns",
                "example": "Microservices architecture with React frontend, Node.js APIs, PostgreSQL database, Redis cache",
            },
        }

        template = remediation_templates.get(
            missing_key,
            {
                "action": f"Provide {missing_key}",
                "guidance": f"Add detailed information for {missing_key} in {stage_name}",
                "example": "Refer to stage documentation for requirements",
            },
        )

        return {
            "stage": stage_name,
            "missing_field": missing_key,
            "action": template["action"],
            "guidance": template["guidance"],
            "example": template["example"],
        }

    def _summarize_quality_impact(self, detected_gaps: List[Dict[str, Any]]) -> str:
        """Summarize overall quality impact of detected gaps"""

        if not detected_gaps:
            return "No significant gaps detected - excellent context completeness"

        high_severity = len([g for g in detected_gaps if g["severity"] == "high"])
        medium_severity = len([g for g in detected_gaps if g["severity"] == "medium"])

        if high_severity > 2:
            return "Critical - Multiple high-severity gaps will significantly impact project quality and subsequent stages"
        elif high_severity > 0 or medium_severity > 3:
            return "Moderate - Some important context missing, recommended to address before proceeding"
        else:
            return "Minor - Small gaps present, can be addressed incrementally"

    def _generate_overall_gap_recommendation(self, completeness_score: float, detected_gaps: List[Dict[str, Any]]) -> str:
        """Generate overall recommendation based on gap analysis"""

        high_severity_count = len([g for g in detected_gaps if g["severity"] == "high"])

        if completeness_score >= 90 and high_severity_count == 0:
            return "Excellent context completeness - proceed with confidence to next stages"
        elif completeness_score >= 75:
            return "Good context foundation - address minor gaps for optimal quality"
        elif completeness_score >= 60:
            return "Adequate context provided - recommend addressing medium-priority gaps before advancing"
        else:
            return "Insufficient context - strongly recommend completing missing information before proceeding"

    def _generate_dimension_improvement(
        self, stage_name: str, dimension: str, current_score: float, stage_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate improvement suggestion for a specific quality dimension"""

        improvement_templates = {
            "problemClarity": {
                "title": "Enhance Problem Statement Clarity",
                "description": "Refine problem definition with specific examples and quantifiable impact",
                "actions": [
                    "Add specific user pain points with real examples",
                    "Quantify the problem impact (time lost, costs, frustration)",
                    "Include context about when and where the problem occurs",
                    "Explain why existing solutions are inadequate",
                ],
                "estimated_impact": "+10-15% quality improvement",
                "implementation_effort": "low",
            },
            "targetAudienceSpecificity": {
                "title": "Refine Target Audience Definition",
                "description": "Add demographic, psychographic, and behavioral details",
                "actions": [
                    "Define specific demographic characteristics (age, location, industry)",
                    "Describe behavioral patterns and preferences",
                    "Identify key pain points and motivations",
                    "Segment audience if multiple user types exist",
                ],
                "estimated_impact": "+12-18% quality improvement",
                "implementation_effort": "low",
            },
            "requirementCompleteness": {
                "title": "Complete Functional Requirements",
                "description": "Add missing requirements and edge cases",
                "actions": [
                    "Review each user story for completeness",
                    "Add acceptance criteria for ambiguous requirements",
                    "Include error handling and edge case requirements",
                    "Specify non-functional requirements (performance, security)",
                ],
                "estimated_impact": "+15-25% quality improvement",
                "implementation_effort": "medium",
            },
            "userJourneyCompleteness": {
                "title": "Enhance User Journey Documentation",
                "description": "Map complete end-to-end user flows with decision points",
                "actions": [
                    "Document all user entry points and workflows",
                    "Add decision points and alternate paths",
                    "Include error states and recovery flows",
                    "Specify success criteria for each journey",
                ],
                "estimated_impact": "+10-20% quality improvement",
                "implementation_effort": "medium",
            },
            "architecturalSoundness": {
                "title": "Strengthen Technical Architecture",
                "description": "Add architectural patterns, scalability considerations, and trade-off analysis",
                "actions": [
                    "Document architectural patterns and their rationale",
                    "Add scalability and performance considerations",
                    "Include security and compliance requirements",
                    "Perform trade-off analysis for major decisions",
                ],
                "estimated_impact": "+20-30% quality improvement",
                "implementation_effort": "high",
            },
        }

        template = improvement_templates.get(dimension)
        if not template:
            return None

        # Calculate priority based on score gap
        score_gap = 85 - current_score  # 85 is recommended threshold
        priority = "high" if score_gap > 15 else "medium" if score_gap > 5 else "low"

        # Estimate success probability based on current score
        success_probability = min(0.95, 0.6 + (current_score / 100 * 0.35))

        return {
            "type": "dimension_improvement",
            "stage": stage_name,
            "dimension": dimension,
            "current_score": current_score,
            "priority": priority,
            "title": template["title"],
            "description": template["description"],
            "actions": template["actions"],
            "estimated_impact": template["estimated_impact"],
            "implementation_effort": template["implementation_effort"],
            "success_probability": success_probability,
        }

    def _generate_consistency_improvements(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate suggestions for improving cross-stage consistency"""

        improvements = []
        consistency_gaps = self._detect_consistency_gaps(project_data)

        for gap in consistency_gaps:
            if gap["consistency_score"] < 0.75:
                improvements.append(
                    {
                        "type": "consistency_improvement",
                        "priority": "high" if gap["consistency_score"] < 0.6 else "medium",
                        "title": f"Align {gap['source_stage']} with {gap['target_stage']}",
                        "description": f"Improve consistency between stages (current: {gap['consistency_score']:.1%})",
                        "actions": gap["recommendations"],
                        "estimated_impact": f"+{(0.85 - gap['consistency_score']) * 100:.0f}% consistency improvement",
                        "implementation_effort": "medium",
                        "success_probability": 0.8,
                    }
                )

        return improvements

    def _generate_regression_recovery_actions(self, progression_analysis: Dict[str, Any]) -> List[str]:
        """Generate actions to recover from quality regression"""

        return [
            "Review recent stage implementation for completeness",
            "Compare with higher-quality earlier stages for best practices",
            "Re-run quality assessment with enhanced criteria",
            "Engage additional LLM models for consensus validation",
            "Add missing context or details identified in gap analysis",
        ]

    def _calculate_total_improvement_potential(self, suggestions: List[Dict[str, Any]]) -> str:
        """Calculate total potential quality improvement from all suggestions"""

        if not suggestions:
            return "No improvements needed - quality already optimal"

        # Estimate cumulative impact (with diminishing returns)
        high_priority = len([s for s in suggestions if s.get("priority") == "high"])
        medium_priority = len([s for s in suggestions if s.get("priority") == "medium"])

        base_improvement = high_priority * 15 + medium_priority * 8
        diminished_improvement = base_improvement * 0.7  # Account for diminishing returns

        return f"+{diminished_improvement:.0f}-{base_improvement:.0f}% potential quality improvement"

    def _generate_action_plan(self, suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate prioritized action plan from suggestions"""

        # Group by implementation effort
        quick_wins = [s for s in suggestions if s.get("implementation_effort") == "low"]
        medium_efforts = [s for s in suggestions if s.get("implementation_effort") == "medium"]
        major_efforts = [s for s in suggestions if s.get("implementation_effort") == "high"]

        action_plan = []

        if quick_wins:
            action_plan.append(
                {
                    "phase": "Immediate Actions (Quick Wins)",
                    "duration": "1-2 hours",
                    "items": [s["title"] for s in quick_wins[:3]],
                    "expected_impact": "Quick quality boost with minimal effort",
                }
            )

        if medium_efforts:
            action_plan.append(
                {
                    "phase": "Short-term Improvements",
                    "duration": "1-3 days",
                    "items": [s["title"] for s in medium_efforts[:3]],
                    "expected_impact": "Significant quality enhancement",
                }
            )

        if major_efforts:
            action_plan.append(
                {
                    "phase": "Strategic Enhancements",
                    "duration": "1-2 weeks",
                    "items": [s["title"] for s in major_efforts[:2]],
                    "expected_impact": "Transformative quality improvement",
                }
            )

        return action_plan

    def _define_success_indicators(self, suggestions: List[Dict[str, Any]]) -> List[str]:
        """Define success indicators for improvement implementation"""

        return [
            "Quality scores increase by at least 10% in targeted dimensions",
            "Cross-stage consistency scores above 85%",
            "Context completeness score reaches 90%+",
            "Zero high-severity gaps remaining",
            "All stages meet or exceed recommended quality thresholds",
            "Positive quality progression trend across all stages",
        ]
