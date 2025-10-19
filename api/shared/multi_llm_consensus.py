"""
Multi-LLM Consensus System for Technical Analysis.
Implements parallel LLM execution, consensus scoring, and conflict resolution
for reliable technical architecture evaluation and recommendation.
"""

import asyncio
import json
import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ConsensusLevel(Enum):
    """Consensus agreement levels"""

    STRONG_AGREEMENT = "strong_agreement"  # 80%+ agreement
    MODERATE_AGREEMENT = "moderate_agreement"  # 60-79% agreement
    WEAK_AGREEMENT = "weak_agreement"  # 40-59% agreement
    NO_CONSENSUS = "no_consensus"  # <40% agreement


class ConflictResolutionStrategy(Enum):
    """Strategies for resolving LLM conflicts"""

    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_AVERAGE = "weighted_average"
    EXPERT_MODEL_PRIORITY = "expert_model_priority"
    CONSERVATIVE_APPROACH = "conservative_approach"


@dataclass
class LLMResponse:
    """Individual LLM response with metadata"""

    model: str
    response_content: str
    confidence_score: float
    processing_time: float
    cost: float
    tokens_used: int
    technical_scores: Dict[str, float]
    recommendations: List[str]
    risk_assessment: Dict[str, Any]
    timestamp: str


@dataclass
class ConsensusResult:
    """Result of multi-LLM consensus analysis"""

    consensus_level: ConsensusLevel
    agreement_score: float
    final_recommendation: Dict[str, Any]
    individual_responses: List[LLMResponse]
    conflict_areas: List[str]
    resolution_strategy: ConflictResolutionStrategy
    confidence_level: float
    quality_metrics: Dict[str, float]
    total_cost: float
    processing_metadata: Dict[str, Any]


@dataclass
class TechnicalEvaluation:
    """Comprehensive technical evaluation result"""

    architecture_recommendation: Dict[str, Any]
    technology_stack: Dict[str, Any]
    feasibility_assessment: Dict[str, Any]
    risk_analysis: Dict[str, Any]
    consensus_metadata: ConsensusResult
    implementation_roadmap: Dict[str, Any]
    quality_score: float


class MultiLLMConsensusEngine:
    """Multi-LLM consensus engine for technical analysis"""

    def __init__(self):
        self.llm_weights = {
            "gpt-4": 1.0,
            "claude-3-5-sonnet": 1.0,
            "gemini-1.5-pro": 0.9,
            "gpt-4o": 0.95,
            "claude-3-haiku": 0.8,
            "gemini-flash": 0.7,
        }
        self.consensus_threshold = 0.6  # 60% agreement minimum
        self.strong_consensus_threshold = 0.8  # 80% for strong agreement

    async def evaluate_technical_architecture(
        self, project_context: Dict[str, Any], selected_models: List[str], llm_client: Any
    ) -> TechnicalEvaluation:
        """
        Perform multi-LLM technical architecture evaluation with consensus scoring

        Args:
            project_context: Complete project context from all previous stages
            selected_models: List of LLM models to use for evaluation
            llm_client: LLM client for API calls

        Returns:
            TechnicalEvaluation with consensus results and recommendations
        """

        # Generate technical evaluation prompts for each LLM
        evaluation_prompt = self._create_technical_evaluation_prompt(project_context)

        # Execute parallel LLM calls
        llm_responses = await self._execute_parallel_analysis(evaluation_prompt, selected_models, llm_client)

        # Calculate consensus on architecture recommendations
        architecture_consensus = self._calculate_architecture_consensus(llm_responses)

        # Evaluate technology stack recommendations
        stack_consensus = self._calculate_technology_stack_consensus(llm_responses)

        # Assess feasibility and risks
        feasibility_consensus = self._calculate_feasibility_consensus(llm_responses)
        risk_consensus = self._calculate_risk_consensus(llm_responses)

        # Generate final consensus result
        final_consensus = self._generate_final_consensus(
            architecture_consensus, stack_consensus, feasibility_consensus, risk_consensus
        )

        # Create implementation roadmap
        roadmap = self._generate_implementation_roadmap(final_consensus, project_context)

        # Calculate overall quality score
        quality_score = self._calculate_technical_quality_score(final_consensus, llm_responses)

        return TechnicalEvaluation(
            architecture_recommendation=architecture_consensus.final_recommendation,
            technology_stack=stack_consensus.final_recommendation,
            feasibility_assessment=feasibility_consensus.final_recommendation,
            risk_analysis=risk_consensus.final_recommendation,
            consensus_metadata=final_consensus,
            implementation_roadmap=roadmap,
            quality_score=quality_score,
        )

    async def _execute_parallel_analysis(self, prompt: str, models: List[str], llm_client: Any) -> List[LLMResponse]:
        """Execute technical analysis across multiple LLMs in parallel"""

        async def analyze_with_model(model: str) -> LLMResponse:
            start_time = datetime.now()

            try:
                response = await llm_client.execute_prompt(
                    prompt=prompt, model=model, temperature=0.2, max_tokens=4000  # Lower temperature for technical analysis
                )

                processing_time = (datetime.now() - start_time).total_seconds()

                # Parse technical response
                parsed_response = self._parse_technical_response(response.get("content", ""))

                return LLMResponse(
                    model=model,
                    response_content=response.get("content", ""),
                    confidence_score=parsed_response.get("confidence", 0.7),
                    processing_time=processing_time,
                    cost=response.get("cost", 0.0),
                    tokens_used=response.get("usage", {}).get("total_tokens", 0),
                    technical_scores=parsed_response.get("technicalScores", {}),
                    recommendations=parsed_response.get("recommendations", []),
                    risk_assessment=parsed_response.get("riskAssessment", {}),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

            except Exception as e:
                logger.error(f"Error analyzing with {model}: {str(e)}")
                return LLMResponse(
                    model=model,
                    response_content=f"Error: {str(e)}",
                    confidence_score=0.0,
                    processing_time=0.0,
                    cost=0.0,
                    tokens_used=0,
                    technical_scores={},
                    recommendations=[],
                    risk_assessment={},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

        # Execute all models in parallel
        tasks = [analyze_with_model(model) for model in models]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return valid responses
        valid_responses = [r for r in responses if isinstance(r, LLMResponse)]

        return valid_responses

    def _calculate_architecture_consensus(self, responses: List[LLMResponse]) -> ConsensusResult:
        """Calculate consensus on architecture recommendations with enhanced weighted scoring"""

        # Extract architecture patterns from each response with model context
        architecture_patterns = []
        model_weights = {}

        for response in responses:
            patterns = self._extract_architecture_patterns(response)
            architecture_patterns.append(patterns)

            # Store model weight for weighted consensus calculation
            model_name = response.model.lower()
            if "gpt-4" in model_name or "gpt4" in model_name:
                model_weights[response.model] = 1.0  # GPT-4: Full weight
            elif "claude" in model_name:
                model_weights[response.model] = 1.0  # Claude: Full weight
            elif "gemini" in model_name:
                model_weights[response.model] = 0.9  # Gemini: Slightly lower weight
            else:
                model_weights[response.model] = 0.85  # Other models: Conservative weight

        # Calculate weighted pattern scores with model-specific weights
        pattern_scores = {}
        total_weight = sum(model_weights.values())

        for idx, patterns in enumerate(architecture_patterns):
            response_weight = model_weights.get(responses[idx].model, 0.85)
            response_confidence = responses[idx].confidence_score

            # Combined weight: model weight * response confidence
            combined_weight = response_weight * response_confidence

            for pattern in patterns:
                if pattern not in pattern_scores:
                    pattern_scores[pattern] = {
                        "weighted_votes": 0.0,
                        "raw_votes": 0,
                        "supporting_models": [],
                        "confidence_scores": [],
                    }

                pattern_scores[pattern]["weighted_votes"] += combined_weight
                pattern_scores[pattern]["raw_votes"] += 1
                pattern_scores[pattern]["supporting_models"].append(responses[idx].model)
                pattern_scores[pattern]["confidence_scores"].append(response_confidence)

        # Calculate normalized weighted agreement scores
        if not pattern_scores:
            consensus_level = ConsensusLevel.NO_CONSENSUS
            agreement_score = 0.0
            weighted_agreement_score = 0.0
        else:
            # Find pattern with highest weighted score
            best_pattern = max(pattern_scores.items(), key=lambda x: x[1]["weighted_votes"])
            max_weighted_votes = best_pattern[1]["weighted_votes"]
            weighted_agreement_score = max_weighted_votes / total_weight

            # Also calculate raw vote percentage for comparison
            max_raw_votes = max(p["raw_votes"] for p in pattern_scores.values())
            raw_agreement = max_raw_votes / len(responses)

            # Final agreement score combines weighted and raw scores (70% weighted, 30% raw)
            agreement_score = (weighted_agreement_score * 0.7) + (raw_agreement * 0.3)

            # Determine consensus level based on agreement score
            if agreement_score >= self.strong_consensus_threshold:
                consensus_level = ConsensusLevel.STRONG_AGREEMENT
            elif agreement_score >= self.consensus_threshold:
                consensus_level = ConsensusLevel.MODERATE_AGREEMENT
            elif agreement_score >= 0.4:
                consensus_level = ConsensusLevel.WEAK_AGREEMENT
            else:
                consensus_level = ConsensusLevel.NO_CONSENSUS

        # Generate final recommendation using enhanced conflict resolution
        final_recommendation = self._resolve_architecture_conflicts_enhanced(
            pattern_scores, responses, consensus_level, model_weights
        )

        # Identify conflict areas with detailed analysis
        conflict_areas = self._identify_architecture_conflicts_enhanced(pattern_scores, len(responses), total_weight)

        return ConsensusResult(
            consensus_level=consensus_level,
            agreement_score=agreement_score,
            final_recommendation=final_recommendation,
            individual_responses=responses,
            conflict_areas=conflict_areas,
            resolution_strategy=ConflictResolutionStrategy.MAJORITY_VOTE,
            confidence_level=self._calculate_confidence_level(responses, agreement_score),
            quality_metrics=self._calculate_consensus_quality_metrics(responses),
            total_cost=sum(r.cost for r in responses),
            processing_metadata={
                "total_models": len(responses),
                "successful_responses": len([r for r in responses if r.confidence_score > 0]),
                "average_processing_time": statistics.mean([r.processing_time for r in responses]),
                "total_tokens": sum(r.tokens_used for r in responses),
            },
        )

    def _calculate_technology_stack_consensus(self, responses: List[LLMResponse]) -> ConsensusResult:
        """Calculate consensus on technology stack recommendations with enhanced weighted scoring"""

        # Extract technology recommendations with model weights
        tech_recommendations = []
        model_weights = {}

        for response in responses:
            techs = self._extract_technology_recommendations(response)
            tech_recommendations.append(techs)

            # Apply model-specific weights
            model_name = response.model.lower()
            if "gpt-4" in model_name or "gpt4" in model_name:
                model_weights[response.model] = 1.0
            elif "claude" in model_name:
                model_weights[response.model] = 1.0
            elif "gemini" in model_name:
                model_weights[response.model] = 0.9
            else:
                model_weights[response.model] = 0.85

        # Calculate weighted technology consensus
        tech_scores = {}
        total_responses = len(responses)
        total_weight = sum(model_weights.values())

        for idx, techs in enumerate(tech_recommendations):
            response_weight = model_weights.get(responses[idx].model, 0.85)
            response_confidence = responses[idx].confidence_score
            combined_weight = response_weight * response_confidence

            for category, technology in techs.items():
                if category not in tech_scores:
                    tech_scores[category] = {}

                tech_name = technology.get("name", "unknown")
                if tech_name not in tech_scores[category]:
                    tech_scores[category][tech_name] = {
                        "count": 0,
                        "weighted_votes": 0.0,
                        "total_score": 0.0,
                        "reasons": [],
                        "supporting_models": [],
                        "confidence_scores": [],
                    }

                tech_scores[category][tech_name]["count"] += 1
                tech_scores[category][tech_name]["weighted_votes"] += combined_weight
                tech_scores[category][tech_name]["total_score"] += technology.get("score", 5.0)
                tech_scores[category][tech_name]["reasons"].extend(technology.get("reasons", []))
                tech_scores[category][tech_name]["supporting_models"].append(responses[idx].model)
                tech_scores[category][tech_name]["confidence_scores"].append(response_confidence)

        # Calculate category-level consensus with weighted scoring
        category_consensus = {}
        overall_agreement = 0.0

        for category, technologies in tech_scores.items():
            if technologies:
                # Find technology with highest weighted votes in this category
                max_weighted_votes = max(tech["weighted_votes"] for tech in technologies.values())
                weighted_agreement = max_weighted_votes / total_weight

                # Also track raw vote percentage
                max_count = max(tech["count"] for tech in technologies.values())
                raw_agreement = max_count / total_responses

                # Combine weighted and raw (70% weighted, 30% raw)
                category_agreement = (weighted_agreement * 0.7) + (raw_agreement * 0.3)
                category_consensus[category] = {
                    "agreement": category_agreement,
                    "weighted_agreement": weighted_agreement,
                    "raw_agreement": raw_agreement,
                }
                overall_agreement += category_agreement

        if category_consensus:
            overall_agreement /= len(category_consensus)

        # Determine consensus level
        if overall_agreement >= self.strong_consensus_threshold:
            consensus_level = ConsensusLevel.STRONG_AGREEMENT
        elif overall_agreement >= self.consensus_threshold:
            consensus_level = ConsensusLevel.MODERATE_AGREEMENT
        elif overall_agreement >= 0.4:
            consensus_level = ConsensusLevel.WEAK_AGREEMENT
        else:
            consensus_level = ConsensusLevel.NO_CONSENSUS

        # Generate final technology stack recommendation with enhanced conflict resolution
        final_stack = self._resolve_technology_conflicts_enhanced(
            tech_scores, responses, consensus_level, model_weights, total_weight
        )

        # Identify areas of conflict with detailed analysis
        conflict_areas = []
        for category, consensus_data in category_consensus.items():
            if consensus_data["agreement"] < self.consensus_threshold:
                conflict_areas.append(
                    f"Low consensus on {category} technology choice " f"({consensus_data['agreement']:.1%} agreement)"
                )
            elif consensus_data["weighted_agreement"] < 0.5 and consensus_data["raw_agreement"] > 0.6:
                conflict_areas.append(f"Model disagreement on {category}: popular choice has low expert model support")

        return ConsensusResult(
            consensus_level=consensus_level,
            agreement_score=overall_agreement,
            final_recommendation=final_stack,
            individual_responses=responses,
            conflict_areas=conflict_areas,
            resolution_strategy=ConflictResolutionStrategy.WEIGHTED_AVERAGE,
            confidence_level=self._calculate_confidence_level(responses, overall_agreement),
            quality_metrics=self._calculate_consensus_quality_metrics(responses),
            total_cost=sum(r.cost for r in responses),
            processing_metadata={
                "categories_analyzed": len(category_consensus),
                "consensus_by_category": category_consensus,
                "total_technologies_considered": sum(len(techs) for techs in tech_scores.values()),
            },
        )

    def _calculate_feasibility_consensus(self, responses: List[LLMResponse]) -> ConsensusResult:
        """Calculate consensus on feasibility assessment"""

        # Extract feasibility metrics from each response
        feasibility_scores = []
        implementation_estimates = []
        resource_requirements = []

        for response in responses:
            feasibility = self._extract_feasibility_assessment(response)
            feasibility_scores.append(feasibility.get("overall_score", 5.0))
            implementation_estimates.append(feasibility.get("timeline_weeks", 12))
            resource_requirements.append(feasibility.get("team_size", 3))

        # Calculate consensus metrics
        if feasibility_scores:
            avg_feasibility = statistics.mean(feasibility_scores)
            feasibility_variance = statistics.variance(feasibility_scores) if len(feasibility_scores) > 1 else 0.0

            avg_timeline = statistics.mean(implementation_estimates)
            timeline_variance = statistics.variance(implementation_estimates) if len(implementation_estimates) > 1 else 0.0

            avg_team_size = statistics.mean(resource_requirements)

            # Calculate agreement based on variance (lower variance = higher agreement)
            feasibility_agreement = max(0.0, 1.0 - (feasibility_variance / 10.0))  # Normalized variance
            timeline_agreement = max(0.0, 1.0 - (timeline_variance / 100.0))  # Timeline variance in weeks

            overall_agreement = (feasibility_agreement + timeline_agreement) / 2.0
        else:
            avg_feasibility = 5.0
            avg_timeline = 12
            avg_team_size = 3
            overall_agreement = 0.0

        # Determine consensus level
        if overall_agreement >= self.strong_consensus_threshold:
            consensus_level = ConsensusLevel.STRONG_AGREEMENT
        elif overall_agreement >= self.consensus_threshold:
            consensus_level = ConsensusLevel.MODERATE_AGREEMENT
        elif overall_agreement >= 0.4:
            consensus_level = ConsensusLevel.WEAK_AGREEMENT
        else:
            consensus_level = ConsensusLevel.NO_CONSENSUS

        # Generate final feasibility recommendation
        final_feasibility = {
            "overall_feasibility_score": avg_feasibility,
            "estimated_timeline_weeks": avg_timeline,
            "recommended_team_size": round(avg_team_size),
            "confidence_level": overall_agreement,
            "key_challenges": self._extract_common_challenges(responses),
            "success_factors": self._extract_success_factors(responses),
            "risk_mitigation": self._extract_risk_mitigation_strategies(responses),
        }

        # Identify conflict areas
        conflict_areas = []
        if feasibility_variance > 2.0:
            conflict_areas.append("Feasibility score assessment")
        if timeline_variance > 16.0:  # More than 4 weeks variance
            conflict_areas.append("Implementation timeline estimation")

        return ConsensusResult(
            consensus_level=consensus_level,
            agreement_score=overall_agreement,
            final_recommendation=final_feasibility,
            individual_responses=responses,
            conflict_areas=conflict_areas,
            resolution_strategy=ConflictResolutionStrategy.WEIGHTED_AVERAGE,
            confidence_level=self._calculate_confidence_level(responses, overall_agreement),
            quality_metrics=self._calculate_consensus_quality_metrics(responses),
            total_cost=sum(r.cost for r in responses),
            processing_metadata={
                "feasibility_variance": feasibility_variance,
                "timeline_variance": timeline_variance,
                "score_range": (
                    f"{min(feasibility_scores):.1f} - {max(feasibility_scores):.1f}" if feasibility_scores else "N/A"
                ),
            },
        )

    def _calculate_risk_consensus(self, responses: List[LLMResponse]) -> ConsensusResult:
        """Calculate consensus on risk assessment"""

        # Extract risk assessments from each response
        risk_categories = {}
        overall_risk_scores = []

        for response in responses:
            risks = self._extract_risk_assessment(response)
            overall_risk_scores.append(risks.get("overall_risk_level", 5.0))

            for category, risk_data in risks.get("categories", {}).items():
                if category not in risk_categories:
                    risk_categories[category] = []
                risk_categories[category].append(risk_data.get("severity", 3.0))

        # Calculate consensus for each risk category
        category_consensus = {}
        for category, severity_scores in risk_categories.items():
            if severity_scores:
                avg_severity = statistics.mean(severity_scores)
                variance = statistics.variance(severity_scores) if len(severity_scores) > 1 else 0.0
                agreement = max(0.0, 1.0 - (variance / 5.0))  # Normalized variance for 1-10 scale

                category_consensus[category] = {
                    "average_severity": avg_severity,
                    "agreement_level": agreement,
                    "variance": variance,
                }

        # Calculate overall risk consensus
        if overall_risk_scores:
            avg_risk = statistics.mean(overall_risk_scores)
            risk_variance = statistics.variance(overall_risk_scores) if len(overall_risk_scores) > 1 else 0.0
            overall_agreement = max(0.0, 1.0 - (risk_variance / 10.0))
        else:
            avg_risk = 5.0
            overall_agreement = 0.0

        # Determine consensus level
        if overall_agreement >= self.strong_consensus_threshold:
            consensus_level = ConsensusLevel.STRONG_AGREEMENT
        elif overall_agreement >= self.consensus_threshold:
            consensus_level = ConsensusLevel.MODERATE_AGREEMENT
        elif overall_agreement >= 0.4:
            consensus_level = ConsensusLevel.WEAK_AGREEMENT
        else:
            consensus_level = ConsensusLevel.NO_CONSENSUS

        # Generate final risk assessment
        final_risk_assessment = {
            "overall_risk_level": avg_risk,
            "risk_categories": {
                category: {
                    "severity": data["average_severity"],
                    "confidence": data["agreement_level"],
                    "mitigation_strategies": self._extract_category_mitigations(responses, category),
                }
                for category, data in category_consensus.items()
            },
            "top_risks": self._identify_top_risks(category_consensus),
            "risk_mitigation_priority": self._prioritize_risk_mitigation(category_consensus),
            "monitoring_recommendations": self._generate_risk_monitoring_recommendations(responses),
        }

        # Identify conflict areas
        conflict_areas = []
        for category, data in category_consensus.items():
            if data["agreement_level"] < self.consensus_threshold:
                conflict_areas.append(f"Risk assessment for {category}")

        return ConsensusResult(
            consensus_level=consensus_level,
            agreement_score=overall_agreement,
            final_recommendation=final_risk_assessment,
            individual_responses=responses,
            conflict_areas=conflict_areas,
            resolution_strategy=ConflictResolutionStrategy.CONSERVATIVE_APPROACH,
            confidence_level=self._calculate_confidence_level(responses, overall_agreement),
            quality_metrics=self._calculate_consensus_quality_metrics(responses),
            total_cost=sum(r.cost for r in responses),
            processing_metadata={
                "risk_categories_analyzed": len(category_consensus),
                "overall_risk_variance": risk_variance if overall_risk_scores else 0.0,
                "high_risk_categories": len([c for c in category_consensus.values() if c["average_severity"] > 7.0]),
            },
        )

    def _generate_final_consensus(
        self, architecture: ConsensusResult, stack: ConsensusResult, feasibility: ConsensusResult, risk: ConsensusResult
    ) -> ConsensusResult:
        """Generate final consensus result across all evaluation dimensions"""

        # Calculate weighted overall consensus
        dimension_weights = {"architecture": 0.35, "technology_stack": 0.25, "feasibility": 0.25, "risk_assessment": 0.15}

        weighted_agreement = (
            architecture.agreement_score * dimension_weights["architecture"]
            + stack.agreement_score * dimension_weights["technology_stack"]
            + feasibility.agreement_score * dimension_weights["feasibility"]
            + risk.agreement_score * dimension_weights["risk_assessment"]
        )

        # Determine overall consensus level
        if weighted_agreement >= self.strong_consensus_threshold:
            overall_consensus = ConsensusLevel.STRONG_AGREEMENT
        elif weighted_agreement >= self.consensus_threshold:
            overall_consensus = ConsensusLevel.MODERATE_AGREEMENT
        elif weighted_agreement >= 0.4:
            overall_consensus = ConsensusLevel.WEAK_AGREEMENT
        else:
            overall_consensus = ConsensusLevel.NO_CONSENSUS

        # Aggregate all conflict areas
        all_conflicts = architecture.conflict_areas + stack.conflict_areas + feasibility.conflict_areas + risk.conflict_areas

        # Calculate overall confidence
        dimension_confidences = [
            architecture.confidence_level,
            stack.confidence_level,
            feasibility.confidence_level,
            risk.confidence_level,
        ]
        overall_confidence = statistics.mean(dimension_confidences)

        # Aggregate quality metrics
        overall_quality_metrics = {
            "architecture_consensus": architecture.agreement_score,
            "technology_stack_consensus": stack.agreement_score,
            "feasibility_consensus": feasibility.agreement_score,
            "risk_consensus": risk.agreement_score,
            "weighted_overall_consensus": weighted_agreement,
            "confidence_level": overall_confidence,
        }

        # Generate consolidated final recommendation
        final_recommendation = {
            "architecture": architecture.final_recommendation,
            "technology_stack": stack.final_recommendation,
            "feasibility_assessment": feasibility.final_recommendation,
            "risk_analysis": risk.final_recommendation,
            "consensus_metadata": {
                "overall_agreement": weighted_agreement,
                "strongest_consensus": max(
                    [architecture, stack, feasibility, risk], key=lambda x: x.agreement_score
                ).consensus_level.value,
                "weakest_consensus": min(
                    [architecture, stack, feasibility, risk], key=lambda x: x.agreement_score
                ).consensus_level.value,
                "total_cost": architecture.total_cost,  # Same responses used for all
                "recommendation_confidence": overall_confidence,
            },
        }

        return ConsensusResult(
            consensus_level=overall_consensus,
            agreement_score=weighted_agreement,
            final_recommendation=final_recommendation,
            individual_responses=architecture.individual_responses,  # Use architecture responses as base
            conflict_areas=list(set(all_conflicts)),  # Remove duplicates
            resolution_strategy=ConflictResolutionStrategy.WEIGHTED_AVERAGE,
            confidence_level=overall_confidence,
            quality_metrics=overall_quality_metrics,
            total_cost=architecture.total_cost,
            processing_metadata={
                "dimension_agreements": {
                    "architecture": architecture.agreement_score,
                    "technology_stack": stack.agreement_score,
                    "feasibility": feasibility.agreement_score,
                    "risk_assessment": risk.agreement_score,
                },
                "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
                "models_used": len(architecture.individual_responses),
                "total_conflicts": len(all_conflicts),
            },
        )

    def _generate_implementation_roadmap(self, consensus: ConsensusResult, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate implementation roadmap based on consensus results"""

        final_rec = consensus.final_recommendation
        feasibility = final_rec.get("feasibility_assessment", {})

        # Generate phased implementation plan
        phases = [
            {
                "phase": 1,
                "name": "Foundation Setup",
                "duration_weeks": 2,
                "deliverables": [
                    "Development environment setup",
                    "Core architecture implementation",
                    "Basic project structure",
                ],
                "dependencies": [],
                "risk_level": "Low",
            },
            {
                "phase": 2,
                "name": "Core Development",
                "duration_weeks": feasibility.get("estimated_timeline_weeks", 12) * 0.6,
                "deliverables": ["Main functionality implementation", "API development", "Database setup"],
                "dependencies": ["Phase 1"],
                "risk_level": "Medium",
            },
            {
                "phase": 3,
                "name": "Integration & Testing",
                "duration_weeks": feasibility.get("estimated_timeline_weeks", 12) * 0.3,
                "deliverables": ["System integration", "Testing and QA", "Performance optimization"],
                "dependencies": ["Phase 2"],
                "risk_level": "Medium",
            },
            {
                "phase": 4,
                "name": "Deployment & Launch",
                "duration_weeks": 1,
                "deliverables": ["Production deployment", "Documentation", "Launch preparation"],
                "dependencies": ["Phase 3"],
                "risk_level": "High",
            },
        ]

        return {
            "phases": phases,
            "total_timeline_weeks": feasibility.get("estimated_timeline_weeks", 12),
            "team_requirements": {
                "recommended_size": feasibility.get("recommended_team_size", 3),
                "key_roles": ["Frontend Developer", "Backend Developer", "DevOps Engineer"],
                "skill_requirements": self._extract_skill_requirements(final_rec),
            },
            "success_criteria": feasibility.get("success_factors", []),
            "quality_gates": [
                {"phase": 1, "criteria": "Architecture validation and setup completion"},
                {"phase": 2, "criteria": "Core functionality working and tested"},
                {"phase": 3, "criteria": "Integration tests passing and performance targets met"},
                {"phase": 4, "criteria": "Production deployment successful and stable"},
            ],
            "risk_mitigation": final_rec.get("risk_analysis", {}).get("risk_mitigation_priority", []),
        }

    def _calculate_technical_quality_score(self, consensus: ConsensusResult, responses: List[LLMResponse]) -> float:
        """Calculate overall technical quality score based on consensus and individual assessments"""

        # Base score from consensus strength
        consensus_score = consensus.agreement_score * 100

        # Confidence adjustment
        confidence_adjustment = consensus.confidence_level * 10

        # Individual model quality scores
        individual_scores = []
        for response in responses:
            technical_scores = response.technical_scores
            if technical_scores:
                avg_score = statistics.mean(technical_scores.values())
                individual_scores.append(avg_score)

        individual_avg = statistics.mean(individual_scores) if individual_scores else 70.0

        # Combine scores with weights
        final_score = (
            consensus_score * 0.4  # 40% weight to consensus
            + confidence_adjustment * 0.2  # 20% weight to confidence
            + individual_avg * 0.4  # 40% weight to individual assessments
        )

        return min(100.0, max(0.0, final_score))

    # Helper methods for parsing and extraction

    def _create_technical_evaluation_prompt(self, project_context: Dict[str, Any]) -> str:
        """Create comprehensive technical evaluation prompt"""

        idea_context = project_context.get("idea_refinement", {})
        prd_context = project_context.get("prd_generation", {})
        ux_context = project_context.get("ux_requirements", {})

        prompt = f"""
You are a senior software architect performing comprehensive technical analysis for a software project.

COMPLETE PROJECT CONTEXT:
Problem Statement: {idea_context.get('problemStatement', '')}
Target Audience: {idea_context.get('targetAudience', '')}
Value Proposition: {idea_context.get('valueProposition', '')}

Functional Requirements: {json.dumps(prd_context.get('requirements', {}).get('functionalRequirements', [])[:5], indent=2)}
User Stories: {json.dumps(prd_context.get('userStories', {}).get('stories', [])[:3], indent=2)}

UX Requirements: {json.dumps(ux_context.get('userJourneys', {}).get('journeys', [])[:2], indent=2)}
Design System: {json.dumps(ux_context.get('designSystem', {}), indent=2)}

Provide comprehensive technical analysis in this JSON format:

{{
    "architectureRecommendation": {{
        "pattern": "Microservices/Monolith/Serverless/Hybrid",
        "rationale": "Detailed reasoning for this choice",
        "scalabilityAssessment": "How this scales with user growth",
        "maintainabilityScore": 8.5,
        "performanceImplications": "Expected performance characteristics",
        "alternativePatterns": ["Other viable options with trade-offs"]
    }},
    "technologyStack": {{
        "frontend": {{
            "name": "React/Vue/Angular/etc",
            "version": "Latest stable version",
            "score": 8.5,
            "reasons": ["Why this technology fits the requirements"],
            "alternatives": ["Other options considered"]
        }},
        "backend": {{
            "name": "Node.js/Python/Java/etc",
            "version": "Latest LTS version",
            "score": 9.0,
            "reasons": ["Why this technology fits"],
            "alternatives": ["Other options"]
        }},
        "database": {{
            "name": "PostgreSQL/MongoDB/etc",
            "type": "SQL/NoSQL/Hybrid",
            "score": 8.0,
            "reasons": ["Why this database choice"],
            "alternatives": ["Other database options"]
        }},
        "infrastructure": {{
            "name": "AWS/Azure/GCP/Kubernetes",
            "score": 8.5,
            "reasons": ["Why this infrastructure choice"],
            "alternatives": ["Other infrastructure options"]
        }}
    }},
    "feasibilityAssessment": {{
        "overall_score": 8.2,
        "timeline_weeks": 16,
        "team_size": 4,
        "complexity_factors": ["What makes this complex"],
        "technical_challenges": ["Specific technical challenges"],
        "skill_requirements": ["Required team skills"],
        "success_factors": ["What needs to go right"],
        "assumptions": ["Key assumptions made"]
    }},
    "riskAssessment": {{
        "overall_risk_level": 6.5,
        "categories": {{
            "technical": {{
                "severity": 7.0,
                "description": "Technical implementation risks",
                "mitigation": "How to mitigate these risks"
            }},
            "scalability": {{
                "severity": 5.0,
                "description": "Scaling challenges",
                "mitigation": "Scaling mitigation strategies"
            }},
            "security": {{
                "severity": 6.0,
                "description": "Security considerations",
                "mitigation": "Security measures needed"
            }},
            "performance": {{
                "severity": 5.5,
                "description": "Performance risks",
                "mitigation": "Performance optimization strategies"
            }}
        }},
        "critical_dependencies": ["External systems or services"],
        "single_points_of_failure": ["Potential failure points"],
        "monitoring_requirements": ["What needs monitoring"]
    }},
    "technicalScores": {{
        "architecture_soundness": 8.5,
        "technology_fit": 8.0,
        "scalability_potential": 7.5,
        "maintainability": 8.5,
        "security_robustness": 7.0,
        "development_velocity": 8.0,
        "operational_complexity": 6.5
    }},
    "recommendations": [
        "Start with MVP approach focusing on core features",
        "Implement comprehensive monitoring from day one",
        "Plan for horizontal scaling from the beginning"
    ],
    "confidence": 0.85
}}

Base your analysis on the complete project context and ensure recommendations align with the identified user needs and business requirements.
"""

        return prompt.strip()

    def _parse_technical_response(self, response_content: str) -> Dict[str, Any]:
        """Parse and validate LLM technical response"""
        try:
            import re

            json_match = re.search(r"\{.*\}", response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "architectureRecommendation": {},
                    "technologyStack": {},
                    "feasibilityAssessment": {"overall_score": 5.0, "timeline_weeks": 12, "team_size": 3},
                    "riskAssessment": {"overall_risk_level": 5.0},
                    "technicalScores": {},
                    "recommendations": [],
                    "confidence": 0.5,
                    "parsingNotes": "Response parsing required manual review",
                }
        except Exception as e:
            logger.warning(f"Error parsing technical response: {str(e)}")
            return {
                "architectureRecommendation": {},
                "technologyStack": {},
                "feasibilityAssessment": {"overall_score": 5.0},
                "riskAssessment": {"overall_risk_level": 5.0},
                "technicalScores": {},
                "recommendations": [],
                "confidence": 0.0,
                "parsingError": str(e),
            }

    def _extract_architecture_patterns(self, response: LLMResponse) -> List[str]:
        """Extract architecture patterns from LLM response"""
        parsed = self._parse_technical_response(response.response_content)
        arch_rec = parsed.get("architectureRecommendation", {})

        patterns = []
        if arch_rec.get("pattern"):
            patterns.append(arch_rec["pattern"])

        alternatives = arch_rec.get("alternativePatterns", [])
        patterns.extend(alternatives[:2])  # Include top 2 alternatives

        return patterns

    def _extract_technology_recommendations(self, response: LLMResponse) -> Dict[str, Dict[str, Any]]:
        """Extract technology recommendations from LLM response"""
        parsed = self._parse_technical_response(response.response_content)
        return parsed.get("technologyStack", {})

    def _extract_feasibility_assessment(self, response: LLMResponse) -> Dict[str, Any]:
        """Extract feasibility assessment from LLM response"""
        parsed = self._parse_technical_response(response.response_content)
        return parsed.get("feasibilityAssessment", {})

    def _extract_risk_assessment(self, response: LLMResponse) -> Dict[str, Any]:
        """Extract risk assessment from LLM response"""
        parsed = self._parse_technical_response(response.response_content)
        return parsed.get("riskAssessment", {})

    def _resolve_architecture_conflicts(
        self, pattern_counts: Dict[str, int], responses: List[LLMResponse], consensus_level: ConsensusLevel
    ) -> Dict[str, Any]:
        """Resolve conflicts in architecture recommendations (legacy method for backward compatibility)"""

        if not pattern_counts:
            return {"pattern": "Monolithic", "rationale": "Default recommendation due to lack of consensus"}

        # Use majority vote
        most_recommended = max(pattern_counts.items(), key=lambda x: x[1])
        pattern = most_recommended[0]
        votes = most_recommended[1]

        # Get rationale from responses that recommended this pattern
        rationales = []
        for response in responses:
            parsed = self._parse_technical_response(response.response_content)
            arch_rec = parsed.get("architectureRecommendation", {})
            if arch_rec.get("pattern") == pattern:
                rationales.append(arch_rec.get("rationale", ""))

        return {
            "pattern": pattern,
            "votes": votes,
            "total_responses": len(responses),
            "consensus_strength": votes / len(responses),
            "rationale": "; ".join(filter(None, rationales[:2])),  # Top 2 rationales
            "resolution_method": "majority_vote",
        }

    def _resolve_architecture_conflicts_enhanced(
        self,
        pattern_scores: Dict[str, Dict[str, Any]],
        responses: List[LLMResponse],
        consensus_level: ConsensusLevel,
        model_weights: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Enhanced conflict resolution using sophisticated weighted scoring and multiple strategies

        Strategies applied:
        1. Weighted majority vote (primary)
        2. Confidence-adjusted scoring
        3. Expert model priority when scores are close
        4. Conservative approach for high-risk decisions
        """

        if not pattern_scores:
            return {
                "pattern": "Monolithic",
                "rationale": "Default recommendation due to lack of consensus",
                "resolution_strategy": "default",
                "confidence": 0.3,
            }

        # Sort patterns by weighted votes
        sorted_patterns = sorted(pattern_scores.items(), key=lambda x: x[1]["weighted_votes"], reverse=True)

        # Get top pattern and runner-up
        top_pattern = sorted_patterns[0]
        pattern_name = top_pattern[0]
        pattern_data = top_pattern[1]

        # Check if there's a close runner-up (within 10% of top pattern's score)
        has_close_runner_up = False
        runner_up_pattern = None

        if len(sorted_patterns) > 1:
            runner_up = sorted_patterns[1]
            vote_difference = (top_pattern[1]["weighted_votes"] - runner_up[1]["weighted_votes"]) / top_pattern[1][
                "weighted_votes"
            ]
            if vote_difference < 0.10:  # Less than 10% difference
                has_close_runner_up = True
                runner_up_pattern = runner_up[0]

        # Collect detailed rationales from supporting models
        rationales = []
        trade_off_analysis = {}
        scalability_scores = []
        maintainability_scores = []

        for response in responses:
            parsed = self._parse_technical_response(response.response_content)
            arch_rec = parsed.get("architectureRecommendation", {})

            if arch_rec.get("pattern") == pattern_name:
                # Collect rationale
                rationale = arch_rec.get("rationale", "")
                if rationale and rationale not in rationales:
                    rationales.append(rationale)

                # Collect technical scores
                if "maintainabilityScore" in arch_rec:
                    maintainability_scores.append(arch_rec["maintainabilityScore"])

                # Collect scalability assessment
                scalability_assessment = arch_rec.get("scalabilityAssessment", "")
                if scalability_assessment:
                    # Extract numeric score if possible (simplified - could be enhanced)
                    scalability_scores.append(8.0)  # Default good score if mentioned

        # Calculate average confidence from supporting models
        avg_confidence = statistics.mean(pattern_data["confidence_scores"]) if pattern_data["confidence_scores"] else 0.5

        # Build comprehensive recommendation
        recommendation = {
            "pattern": pattern_name,
            "weighted_votes": pattern_data["weighted_votes"],
            "raw_votes": pattern_data["raw_votes"],
            "supporting_models": pattern_data["supporting_models"],
            "consensus_strength": pattern_data["weighted_votes"] / sum(model_weights.values()),
            "confidence_level": avg_confidence,
            "rationale": " | ".join(rationales[:3]) if rationales else "Recommended based on consensus analysis",
            "resolution_strategy": self._determine_resolution_strategy(consensus_level, has_close_runner_up, avg_confidence),
        }

        # Add trade-off analysis if close runner-up exists
        if has_close_runner_up and runner_up_pattern:
            recommendation["alternative_consideration"] = {
                "pattern": runner_up_pattern,
                "votes": sorted_patterns[1][1]["raw_votes"],
                "note": f"Close alternative with strong support. Consider trade-offs carefully.",
                "score_difference": f"{(vote_difference * 100):.1f}%",
            }

        # Add technical scoring details
        if maintainability_scores:
            recommendation["maintainability_score"] = statistics.mean(maintainability_scores)
        if scalability_scores:
            recommendation["scalability_score"] = statistics.mean(scalability_scores)

        return recommendation

    def _identify_architecture_conflicts_enhanced(
        self, pattern_scores: Dict[str, Dict[str, Any]], total_responses: int, total_weight: float
    ) -> List[str]:
        """Enhanced conflict identification with detailed analysis"""
        conflicts = []

        if not pattern_scores:
            conflicts.append("No architecture patterns identified from LLM responses")
            return conflicts

        # Sort patterns by weighted votes
        sorted_patterns = sorted(pattern_scores.items(), key=lambda x: x[1]["weighted_votes"], reverse=True)

        # Check overall consensus strength
        top_pattern_score = sorted_patterns[0][1]["weighted_votes"] / total_weight

        if top_pattern_score < 0.4:
            conflicts.append(f"Very low consensus on architecture pattern (only {top_pattern_score:.1%} weighted agreement)")
        elif top_pattern_score < 0.6:
            conflicts.append(
                f"Moderate consensus concerns on architecture pattern ({top_pattern_score:.1%} weighted agreement)"
            )

        # Check for competing patterns with similar scores
        if len(sorted_patterns) > 1:
            for i in range(1, min(3, len(sorted_patterns))):  # Check up to top 3 patterns
                vote_ratio = sorted_patterns[i][1]["weighted_votes"] / sorted_patterns[0][1]["weighted_votes"]
                if vote_ratio > 0.75:  # Runner-up has 75%+ of top pattern's votes
                    conflicts.append(
                        f"Strong competition between '{sorted_patterns[0][0]}' and '{sorted_patterns[i][0]}' "
                        f"({vote_ratio:.1%} vote similarity) - requires careful trade-off analysis"
                    )

        # Check for model disagreement (different models favoring different patterns)
        model_pattern_map = {}
        for pattern_name, pattern_data in pattern_scores.items():
            for model in pattern_data["supporting_models"]:
                if model not in model_pattern_map:
                    model_pattern_map[model] = []
                model_pattern_map[model].append(pattern_name)

        # Identify if high-weight models disagree
        gpt4_patterns = [patterns for model, patterns in model_pattern_map.items() if "gpt-4" in model.lower()]
        claude_patterns = [patterns for model, patterns in model_pattern_map.items() if "claude" in model.lower()]

        if gpt4_patterns and claude_patterns:
            gpt4_set = set(gpt4_patterns[0]) if gpt4_patterns else set()
            claude_set = set(claude_patterns[0]) if claude_patterns else set()
            if gpt4_set and claude_set and not gpt4_set.intersection(claude_set):
                conflicts.append("Expert model disagreement: GPT-4 and Claude favor different architecture patterns")

        # Check confidence variance across supporting models
        for pattern_name, pattern_data in pattern_scores.items():
            if pattern_data["confidence_scores"] and len(pattern_data["confidence_scores"]) > 1:
                confidence_variance = statistics.variance(pattern_data["confidence_scores"])
                if confidence_variance > 0.15:  # High variance in confidence
                    conflicts.append(
                        f"High confidence variance for '{pattern_name}' pattern "
                        f"(σ²={confidence_variance:.2f}) - models have varying certainty"
                    )

        return conflicts

    def _determine_resolution_strategy(
        self, consensus_level: ConsensusLevel, has_close_runner_up: bool, avg_confidence: float
    ) -> str:
        """Determine which conflict resolution strategy was used"""

        if consensus_level == ConsensusLevel.STRONG_AGREEMENT:
            return "weighted_majority_vote"
        elif consensus_level == ConsensusLevel.MODERATE_AGREEMENT:
            if has_close_runner_up:
                return "expert_model_priority_with_trade_off_analysis"
            else:
                return "confidence_weighted_consensus"
        elif consensus_level == ConsensusLevel.WEAK_AGREEMENT:
            if avg_confidence > 0.7:
                return "confidence_adjusted_majority"
            else:
                return "conservative_approach_with_alternatives"
        else:
            return "default_recommendation_due_to_no_consensus"

    def _resolve_technology_conflicts(
        self, tech_scores: Dict[str, Dict[str, Dict[str, Any]]], responses: List[LLMResponse], consensus_level: ConsensusLevel
    ) -> Dict[str, Any]:
        """Resolve conflicts in technology stack recommendations (legacy method for backward compatibility)"""

        final_stack = {}

        for category, technologies in tech_scores.items():
            if not technologies:
                continue

            # Calculate weighted scores
            weighted_scores = {}
            for tech_name, tech_data in technologies.items():
                count = tech_data["count"]
                avg_score = tech_data["total_score"] / count
                weighted_score = (count / len(responses)) * 0.6 + (avg_score / 10.0) * 0.4
                weighted_scores[tech_name] = {
                    "weighted_score": weighted_score,
                    "vote_count": count,
                    "average_score": avg_score,
                    "reasons": list(set(tech_data["reasons"])),  # Unique reasons
                }

            # Select highest weighted score
            if weighted_scores:
                best_tech = max(weighted_scores.items(), key=lambda x: x[1]["weighted_score"])
                final_stack[category] = {
                    "name": best_tech[0],
                    "weighted_score": best_tech[1]["weighted_score"],
                    "vote_count": best_tech[1]["vote_count"],
                    "average_score": best_tech[1]["average_score"],
                    "reasons": best_tech[1]["reasons"],
                    "consensus_strength": best_tech[1]["vote_count"] / len(responses),
                }

        return final_stack

    def _resolve_technology_conflicts_enhanced(
        self,
        tech_scores: Dict[str, Dict[str, Dict[str, Any]]],
        responses: List[LLMResponse],
        consensus_level: ConsensusLevel,
        model_weights: Dict[str, float],
        total_weight: float,
    ) -> Dict[str, Any]:
        """
        Enhanced technology stack conflict resolution with sophisticated weighted scoring

        Resolves technology choices per category with:
        1. Model-weighted voting
        2. Confidence-adjusted scores
        3. Technical fit scoring
        4. Alternative consideration for close races
        """

        final_stack = {}

        for category, technologies in tech_scores.items():
            if not technologies:
                continue

            # Sort technologies by weighted votes
            sorted_techs = sorted(technologies.items(), key=lambda x: x[1]["weighted_votes"], reverse=True)

            if not sorted_techs:
                continue

            # Get top technology
            top_tech_name = sorted_techs[0][0]
            top_tech_data = sorted_techs[0][1]

            # Calculate comprehensive scores
            avg_confidence = statistics.mean(top_tech_data["confidence_scores"]) if top_tech_data["confidence_scores"] else 0.5

            avg_tech_score = top_tech_data["total_score"] / top_tech_data["count"] if top_tech_data["count"] > 0 else 5.0

            # Normalize weighted votes to 0-1 scale
            weighted_consensus = top_tech_data["weighted_votes"] / total_weight
            raw_consensus = top_tech_data["count"] / len(responses)

            # Check for close alternatives (within 15% of top technology's weighted votes)
            alternatives = []
            if len(sorted_techs) > 1:
                for i in range(1, min(3, len(sorted_techs))):  # Check up to 2 alternatives
                    alt_tech_name = sorted_techs[i][0]
                    alt_tech_data = sorted_techs[i][1]
                    vote_ratio = alt_tech_data["weighted_votes"] / top_tech_data["weighted_votes"]

                    if vote_ratio > 0.85:  # Within 15%
                        alt_avg_score = (
                            alt_tech_data["total_score"] / alt_tech_data["count"] if alt_tech_data["count"] > 0 else 5.0
                        )
                        alternatives.append(
                            {
                                "name": alt_tech_name,
                                "weighted_votes": alt_tech_data["weighted_votes"],
                                "vote_count": alt_tech_data["count"],
                                "score": alt_avg_score,
                                "vote_ratio": f"{vote_ratio:.1%}",
                                "supporting_models": alt_tech_data["supporting_models"],
                                "reasons": list(set(alt_tech_data["reasons"]))[:3],  # Top 3 unique reasons
                            }
                        )

            # Build comprehensive recommendation for this category
            category_recommendation = {
                "name": top_tech_name,
                "category": category,
                "weighted_votes": top_tech_data["weighted_votes"],
                "raw_votes": top_tech_data["count"],
                "weighted_consensus": weighted_consensus,
                "raw_consensus": raw_consensus,
                "combined_consensus": (weighted_consensus * 0.7) + (raw_consensus * 0.3),
                "confidence_level": avg_confidence,
                "technical_score": avg_tech_score,
                "supporting_models": top_tech_data["supporting_models"],
                "reasons": list(set(top_tech_data["reasons"]))[:5],  # Top 5 unique reasons
                "resolution_strategy": self._determine_tech_resolution_strategy(
                    weighted_consensus, raw_consensus, len(alternatives), avg_confidence
                ),
            }

            # Add alternatives if they exist
            if alternatives:
                category_recommendation["close_alternatives"] = alternatives
                category_recommendation["recommendation_note"] = (
                    f"Strong alternatives exist for {category}. Consider trade-offs carefully based on "
                    f"specific project requirements and team expertise."
                )

            final_stack[category] = category_recommendation

        return final_stack

    def _determine_tech_resolution_strategy(
        self, weighted_consensus: float, raw_consensus: float, num_alternatives: int, confidence: float
    ) -> str:
        """Determine which resolution strategy was used for technology selection"""

        if weighted_consensus > 0.75 and raw_consensus > 0.7:
            return "strong_weighted_consensus"
        elif num_alternatives > 0:
            if confidence > 0.75:
                return "confidence_weighted_selection_with_alternatives"
            else:
                return "majority_vote_with_close_alternatives"
        elif weighted_consensus > raw_consensus + 0.15:
            return "expert_model_preference"
        elif raw_consensus > weighted_consensus + 0.15:
            return "popular_vote_with_lower_expert_confidence"
        else:
            return "balanced_weighted_consensus"

    def _identify_architecture_conflicts(self, pattern_counts: Dict[str, int], total_responses: int) -> List[str]:
        """Identify areas of conflict in architecture recommendations"""
        conflicts = []

        if not pattern_counts:
            conflicts.append("No architecture patterns identified")
            return conflicts

        max_votes = max(pattern_counts.values())
        max_consensus = max_votes / total_responses

        if max_consensus < self.consensus_threshold:
            conflicts.append("Low consensus on architecture pattern")

        # Check for ties
        patterns_with_max_votes = [pattern for pattern, votes in pattern_counts.items() if votes == max_votes]
        if len(patterns_with_max_votes) > 1:
            conflicts.append(f"Tie between architecture patterns: {', '.join(patterns_with_max_votes)}")

        return conflicts

    def _calculate_confidence_level(self, responses: List[LLMResponse], agreement_score: float) -> float:
        """Calculate confidence level based on individual response confidence and agreement"""
        if not responses:
            return 0.0

        individual_confidences = [r.confidence_score for r in responses if r.confidence_score > 0]

        if not individual_confidences:
            return agreement_score * 0.5  # Lower confidence if no individual confidence scores

        avg_individual_confidence = statistics.mean(individual_confidences)

        # Combine individual confidence with agreement score
        return (avg_individual_confidence * 0.6) + (agreement_score * 0.4)

    def _calculate_consensus_quality_metrics(self, responses: List[LLMResponse]) -> Dict[str, float]:
        """Calculate quality metrics for consensus analysis"""
        if not responses:
            return {}

        # Response quality metrics
        avg_confidence = statistics.mean([r.confidence_score for r in responses if r.confidence_score > 0])
        avg_processing_time = statistics.mean([r.processing_time for r in responses])
        total_cost = sum(r.cost for r in responses)
        total_tokens = sum(r.tokens_used for r in responses)

        # Technical scoring consistency
        all_technical_scores = []
        for response in responses:
            if response.technical_scores:
                all_technical_scores.extend(response.technical_scores.values())

        score_consistency = 1.0 - (statistics.variance(all_technical_scores) / 25.0) if len(all_technical_scores) > 1 else 1.0
        score_consistency = max(0.0, min(1.0, score_consistency))

        return {
            "average_confidence": avg_confidence,
            "response_consistency": score_consistency,
            "average_processing_time": avg_processing_time,
            "cost_efficiency": total_tokens / max(total_cost, 0.001),  # Tokens per dollar
            "response_quality": avg_confidence * 0.5 + score_consistency * 0.5,
        }

    def _extract_common_challenges(self, responses: List[LLMResponse]) -> List[str]:
        """Extract commonly mentioned challenges across responses"""
        all_challenges = []

        for response in responses:
            parsed = self._parse_technical_response(response.response_content)
            feasibility = parsed.get("feasibilityAssessment", {})
            challenges = feasibility.get("technical_challenges", [])
            all_challenges.extend(challenges)

        # Count challenge frequencies
        challenge_counts = {}
        for challenge in all_challenges:
            challenge_counts[challenge] = challenge_counts.get(challenge, 0) + 1

        # Return challenges mentioned by at least 2 responses
        min_mentions = max(2, len(responses) // 2)
        common_challenges = [challenge for challenge, count in challenge_counts.items() if count >= min_mentions]

        return common_challenges[:5]  # Top 5 common challenges

    def _extract_success_factors(self, responses: List[LLMResponse]) -> List[str]:
        """Extract commonly mentioned success factors"""
        all_factors = []

        for response in responses:
            parsed = self._parse_technical_response(response.response_content)
            feasibility = parsed.get("feasibilityAssessment", {})
            factors = feasibility.get("success_factors", [])
            all_factors.extend(factors)

        # Similar logic to challenges
        factor_counts = {}
        for factor in all_factors:
            factor_counts[factor] = factor_counts.get(factor, 0) + 1

        min_mentions = max(2, len(responses) // 2)
        common_factors = [factor for factor, count in factor_counts.items() if count >= min_mentions]

        return common_factors[:5]

    def _extract_risk_mitigation_strategies(self, responses: List[LLMResponse]) -> List[str]:
        """Extract risk mitigation strategies"""
        all_strategies = []

        for response in responses:
            parsed = self._parse_technical_response(response.response_content)
            risk_assessment = parsed.get("riskAssessment", {})

            # Extract mitigation strategies from each risk category
            categories = risk_assessment.get("categories", {})
            for category_data in categories.values():
                if isinstance(category_data, dict) and "mitigation" in category_data:
                    all_strategies.append(category_data["mitigation"])

        # Remove duplicates and return unique strategies
        unique_strategies = list(set(all_strategies))
        return unique_strategies[:8]  # Top 8 unique strategies

    def _extract_category_mitigations(self, responses: List[LLMResponse], category: str) -> List[str]:
        """Extract mitigation strategies for specific risk category"""
        mitigations = []

        for response in responses:
            parsed = self._parse_technical_response(response.response_content)
            risk_assessment = parsed.get("riskAssessment", {})
            categories = risk_assessment.get("categories", {})

            if category in categories and isinstance(categories[category], dict):
                mitigation = categories[category].get("mitigation", "")
                if mitigation:
                    mitigations.append(mitigation)

        return mitigations

    def _identify_top_risks(self, category_consensus: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """Identify top risks based on severity and consensus"""
        risks = []

        for category, data in category_consensus.items():
            risks.append(
                {
                    "category": category,
                    "severity": data["average_severity"],
                    "confidence": data["agreement_level"],
                    "priority_score": data["average_severity"] * data["agreement_level"],
                }
            )

        # Sort by priority score (severity * confidence)
        risks.sort(key=lambda x: x["priority_score"], reverse=True)

        return risks[:5]  # Top 5 risks

    def _prioritize_risk_mitigation(self, category_consensus: Dict[str, Dict[str, float]]) -> List[str]:
        """Prioritize risk mitigation based on severity and impact"""
        top_risks = self._identify_top_risks(category_consensus)

        return [
            f"High priority: Mitigate {risk['category']} risks (severity: {risk['severity']:.1f})" for risk in top_risks[:3]
        ]

    def _generate_risk_monitoring_recommendations(self, responses: List[LLMResponse]) -> List[str]:
        """Generate risk monitoring recommendations"""
        all_monitoring = []

        for response in responses:
            parsed = self._parse_technical_response(response.response_content)
            risk_assessment = parsed.get("riskAssessment", {})
            monitoring = risk_assessment.get("monitoring_requirements", [])
            all_monitoring.extend(monitoring)

        # Remove duplicates and return unique recommendations
        unique_monitoring = list(set(all_monitoring))
        return unique_monitoring[:6]  # Top 6 monitoring recommendations

    def _extract_skill_requirements(self, final_recommendation: Dict[str, Any]) -> List[str]:
        """Extract skill requirements from final recommendation"""
        skills = set()

        # Extract from technology stack
        tech_stack = final_recommendation.get("technology_stack", {})
        for category, tech_info in tech_stack.items():
            if isinstance(tech_info, dict) and "name" in tech_info:
                skills.add(f"{tech_info['name']} development")

        # Extract from feasibility assessment
        feasibility = final_recommendation.get("feasibility_assessment", {})
        skill_reqs = feasibility.get("skill_requirements", [])
        skills.update(skill_reqs)

        return list(skills)[:8]  # Limit to 8 key skills


async def evaluate_technical_architecture(
    project_context: Dict[str, Any], selected_models: List[str], llm_client: Any
) -> TechnicalEvaluation:
    """
    Convenience function for technical architecture evaluation

    Args:
        project_context: Complete project context from all previous stages
        selected_models: List of LLM models to use for evaluation
        llm_client: LLM client for API calls

    Returns:
        TechnicalEvaluation with consensus results and recommendations
    """
    engine = MultiLLMConsensusEngine()
    return await engine.evaluate_technical_architecture(project_context, selected_models, llm_client)
