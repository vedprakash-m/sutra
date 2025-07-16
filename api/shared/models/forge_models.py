"""
Forge module database models and schemas.
Comprehensive data models for the Forge workflow system covering all 5 stages:
Conception → Validation → Planning → Implementation → Deployment
"""

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class ForgeStage(Enum):
    """Forge workflow stages."""

    CONCEPTION = "conception"
    VALIDATION = "validation"
    PLANNING = "planning"
    IMPLEMENTATION = "implementation"
    DEPLOYMENT = "deployment"


class ProjectStatus(Enum):
    """Overall project status."""

    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


class ProjectPriority(Enum):
    """Project priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ArtifactType(Enum):
    """Types of artifacts that can be stored."""

    DOCUMENT = "document"
    DIAGRAM = "diagram"
    CODE = "code"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    SPECIFICATION = "specification"
    PLAN = "plan"
    REPORT = "report"
    PROTOTYPE = "prototype"
    DEPLOYMENT_GUIDE = "deployment_guide"


class ValidationStatus(Enum):
    """Validation assessment status."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_REVISION = "needs_revision"


class TaskStatus(Enum):
    """Implementation task status."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class DeploymentStatus(Enum):
    """Deployment status."""

    NOT_STARTED = "not_started"
    PREPARING = "preparing"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    ROLLED_BACK = "rolled_back"


@dataclass
class ForgeArtifact:
    """Individual artifact within a project stage."""

    id: str
    name: str
    type: ArtifactType
    content: str
    description: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = ""
    version: int = 1


@dataclass
class ConceptionData:
    """Data specific to the Conception stage."""

    initial_idea: str = ""
    problem_statement: str = ""
    target_audience: str = ""
    success_metrics: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    ai_enhancement_suggestions: List[str] = field(default_factory=list)
    feasibility_score: Optional[float] = None
    feasibility_notes: str = ""
    market_potential: Optional[str] = None
    competitor_analysis: List[str] = field(default_factory=list)
    initial_scope: str = ""


@dataclass
class ValidationCriteria:
    """Individual validation criterion."""

    id: str
    name: str
    description: str
    weight: float  # 0.0 to 1.0
    status: ValidationStatus
    evidence: List[str] = field(default_factory=list)
    notes: str = ""
    validated_by: Optional[str] = None
    validated_at: Optional[datetime] = None


@dataclass
class ValidationData:
    """Data specific to the Validation stage."""

    validation_criteria: List[ValidationCriteria] = field(default_factory=list)
    market_research: str = ""
    competitive_analysis: str = ""
    user_research_plan: str = ""
    user_research_results: str = ""
    technical_feasibility: str = ""
    financial_feasibility: str = ""
    risk_assessment: str = ""
    validation_score: Optional[float] = None
    validation_status: ValidationStatus = ValidationStatus.NOT_STARTED
    validation_summary: str = ""
    next_steps: List[str] = field(default_factory=list)


@dataclass
class ProjectResource:
    """Resource estimation for planning."""

    id: str
    name: str
    type: str  # "human", "technology", "financial", "time"
    quantity: float
    unit: str  # "hours", "days", "people", "dollars"
    cost_per_unit: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    availability: str = ""
    notes: str = ""


@dataclass
class ProjectMilestone:
    """Project milestone definition."""

    id: str
    name: str
    description: str
    due_date: datetime
    dependencies: List[str] = field(default_factory=list)  # IDs of other milestones
    deliverables: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.TODO
    completion_percentage: float = 0.0
    actual_completion_date: Optional[datetime] = None
    notes: str = ""


@dataclass
class PlanningData:
    """Data specific to the Planning stage."""

    project_scope: str = ""
    technical_specifications: str = ""
    architecture_overview: str = ""
    technology_stack: List[str] = field(default_factory=list)
    resource_requirements: List[ProjectResource] = field(default_factory=list)
    timeline_estimate: str = ""
    milestones: List[ProjectMilestone] = field(default_factory=list)
    risk_mitigation_plan: str = ""
    quality_assurance_plan: str = ""
    budget_estimate: Optional[Decimal] = None
    team_structure: str = ""
    communication_plan: str = ""
    success_metrics: List[str] = field(default_factory=list)


@dataclass
class ImplementationTask:
    """Individual implementation task."""

    id: str
    name: str
    description: str
    assigned_to: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: ProjectPriority = ProjectPriority.MEDIUM
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)  # Task IDs
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    progress_percentage: float = 0.0
    blockers: List[str] = field(default_factory=list)


@dataclass
class ImplementationData:
    """Data specific to the Implementation stage."""

    implementation_approach: str = ""
    development_methodology: str = ""
    tasks: List[ImplementationTask] = field(default_factory=list)
    progress_tracking: str = ""
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    testing_strategy: str = ""
    code_repositories: List[str] = field(default_factory=list)
    build_artifacts: List[str] = field(default_factory=list)
    performance_benchmarks: Dict[str, Any] = field(default_factory=dict)
    issue_tracking: str = ""
    team_velocity: Optional[float] = None
    burn_down_data: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DeploymentEnvironment:
    """Deployment environment configuration."""

    id: str
    name: str  # "development", "staging", "production"
    url: Optional[str] = None
    status: DeploymentStatus = DeploymentStatus.NOT_STARTED
    version: Optional[str] = None
    deployed_at: Optional[datetime] = None
    health_check_url: Optional[str] = None
    monitoring_urls: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""


@dataclass
class DeploymentData:
    """Data specific to the Deployment stage."""

    deployment_strategy: str = ""
    infrastructure_requirements: str = ""
    environments: List[DeploymentEnvironment] = field(default_factory=list)
    rollback_plan: str = ""
    monitoring_setup: str = ""
    performance_monitoring: str = ""
    security_considerations: str = ""
    maintenance_plan: str = ""
    user_training_plan: str = ""
    support_documentation: str = ""
    go_live_checklist: List[str] = field(default_factory=list)
    post_launch_activities: List[str] = field(default_factory=list)


@dataclass
class ForgeProject:
    """Main Forge project entity containing all stages and data."""

    id: str
    name: str
    description: str
    owner_id: str
    organization_id: Optional[str] = None
    current_stage: ForgeStage = ForgeStage.CONCEPTION
    status: ProjectStatus = ProjectStatus.DRAFT
    priority: ProjectPriority = ProjectPriority.MEDIUM

    # Stage-specific data
    conception_data: ConceptionData = field(default_factory=ConceptionData)
    validation_data: ValidationData = field(default_factory=ValidationData)
    planning_data: PlanningData = field(default_factory=PlanningData)
    implementation_data: ImplementationData = field(default_factory=ImplementationData)
    deployment_data: DeploymentData = field(default_factory=DeploymentData)

    # Artifacts by stage
    artifacts: Dict[str, List[ForgeArtifact]] = field(default_factory=dict)

    # Collaboration and sharing
    collaborators: List[str] = field(default_factory=list)  # User IDs
    shared_with: List[str] = field(default_factory=list)  # User/Group IDs
    permissions: Dict[str, List[str]] = field(default_factory=dict)  # {user_id: [permissions]}

    # Version control
    version: int = 1
    version_history: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    stage_completed_at: Dict[str, datetime] = field(default_factory=dict)

    # Analytics and tracking
    time_spent_per_stage: Dict[str, float] = field(default_factory=dict)  # Hours
    ai_interactions_count: int = 0
    total_cost: Optional[Decimal] = None

    def __post_init__(self):
        """Initialize default artifacts structure."""
        if not self.artifacts:
            self.artifacts = {stage.value: [] for stage in ForgeStage}

    def get_current_stage_data(
        self,
    ) -> Union[ConceptionData, ValidationData, PlanningData, ImplementationData, DeploymentData]:
        """Get data for the current stage."""
        stage_data_map = {
            ForgeStage.CONCEPTION: self.conception_data,
            ForgeStage.VALIDATION: self.validation_data,
            ForgeStage.PLANNING: self.planning_data,
            ForgeStage.IMPLEMENTATION: self.implementation_data,
            ForgeStage.DEPLOYMENT: self.deployment_data,
        }
        return stage_data_map[self.current_stage]

    def get_stage_artifacts(self, stage: ForgeStage) -> List[ForgeArtifact]:
        """Get artifacts for a specific stage."""
        return self.artifacts.get(stage.value, [])

    def add_artifact(self, stage: ForgeStage, artifact: ForgeArtifact) -> None:
        """Add an artifact to a specific stage."""
        if stage.value not in self.artifacts:
            self.artifacts[stage.value] = []
        self.artifacts[stage.value].append(artifact)
        self.updated_at = datetime.now(timezone.utc)

    def advance_stage(self) -> bool:
        """Advance to the next stage if possible."""
        stages = list(ForgeStage)
        current_index = stages.index(self.current_stage)

        if current_index < len(stages) - 1:
            # Mark current stage as completed
            self.stage_completed_at[self.current_stage.value] = datetime.now(timezone.utc)

            # Advance to next stage
            self.current_stage = stages[current_index + 1]
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

    def calculate_overall_progress(self) -> float:
        """Calculate overall project progress as percentage."""
        stages = list(ForgeStage)
        completed_stages = len(self.stage_completed_at)
        current_stage_index = stages.index(self.current_stage)

        # Base progress from completed stages
        base_progress = (completed_stages / len(stages)) * 100

        # Add partial progress for current stage (estimate 50% if in progress)
        if completed_stages < len(stages):
            base_progress += 50 / len(stages)

        return min(base_progress, 100.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        data = asdict(self)

        # Convert datetime objects to ISO strings
        for field_name, field_value in data.items():
            if isinstance(field_value, datetime):
                data[field_name] = field_value.isoformat()
            elif isinstance(field_value, dict):
                for key, value in field_value.items():
                    if isinstance(value, datetime):
                        data[field_name][key] = value.isoformat()

        # Convert enums to values
        data["current_stage"] = self.current_stage.value
        data["status"] = self.status.value
        data["priority"] = self.priority.value

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ForgeProject":
        """Create instance from dictionary."""
        # Convert ISO strings back to datetime objects
        for field_name, field_value in data.items():
            if field_name.endswith("_at") and isinstance(field_value, str):
                try:
                    data[field_name] = datetime.fromisoformat(field_value.replace("Z", "+00:00"))
                except ValueError:
                    pass

        # Convert enum strings back to enums
        if "current_stage" in data:
            data["current_stage"] = ForgeStage(data["current_stage"])
        if "status" in data:
            data["status"] = ProjectStatus(data["status"])
        if "priority" in data:
            data["priority"] = ProjectPriority(data["priority"])

        # Handle nested dataclass objects
        if "conception_data" in data and isinstance(data["conception_data"], dict):
            data["conception_data"] = ConceptionData(**data["conception_data"])
        if "validation_data" in data and isinstance(data["validation_data"], dict):
            # Handle nested ValidationCriteria objects
            validation_dict = data["validation_data"].copy()
            if "validation_criteria" in validation_dict:
                criteria_list = []
                for criteria_dict in validation_dict["validation_criteria"]:
                    if isinstance(criteria_dict, dict):
                        # Convert enum strings back to enums
                        if "status" in criteria_dict:
                            criteria_dict["status"] = ValidationStatus(criteria_dict["status"])
                        criteria_list.append(ValidationCriteria(**criteria_dict))
                    else:
                        criteria_list.append(criteria_dict)
                validation_dict["validation_criteria"] = criteria_list

            # Convert enum strings back to enums
            if "validation_status" in validation_dict:
                validation_dict["validation_status"] = ValidationStatus(validation_dict["validation_status"])

            data["validation_data"] = ValidationData(**validation_dict)

        if "planning_data" in data and isinstance(data["planning_data"], dict):
            planning_dict = data["planning_data"].copy()
            # Handle nested objects
            if "resource_requirements" in planning_dict:
                resources = []
                for resource_dict in planning_dict["resource_requirements"]:
                    if isinstance(resource_dict, dict):
                        resources.append(ProjectResource(**resource_dict))
                    else:
                        resources.append(resource_dict)
                planning_dict["resource_requirements"] = resources

            if "milestones" in planning_dict:
                milestones = []
                for milestone_dict in planning_dict["milestones"]:
                    if isinstance(milestone_dict, dict):
                        # Convert datetime strings back to datetime objects
                        if "due_date" in milestone_dict and isinstance(milestone_dict["due_date"], str):
                            milestone_dict["due_date"] = datetime.fromisoformat(
                                milestone_dict["due_date"].replace("Z", "+00:00")
                            )
                        if "actual_completion_date" in milestone_dict and isinstance(
                            milestone_dict["actual_completion_date"], str
                        ):
                            milestone_dict["actual_completion_date"] = datetime.fromisoformat(
                                milestone_dict["actual_completion_date"].replace("Z", "+00:00")
                            )
                        # Convert enum strings back to enums
                        if "status" in milestone_dict:
                            milestone_dict["status"] = TaskStatus(milestone_dict["status"])
                        milestones.append(ProjectMilestone(**milestone_dict))
                    else:
                        milestones.append(milestone_dict)
                planning_dict["milestones"] = milestones

            data["planning_data"] = PlanningData(**planning_dict)

        if "implementation_data" in data and isinstance(data["implementation_data"], dict):
            impl_dict = data["implementation_data"].copy()
            # Handle nested task objects
            if "tasks" in impl_dict:
                tasks = []
                for task_dict in impl_dict["tasks"]:
                    if isinstance(task_dict, dict):
                        # Convert datetime strings back to datetime objects
                        for date_field in ["start_date", "due_date", "completion_date"]:
                            if date_field in task_dict and isinstance(task_dict[date_field], str):
                                task_dict[date_field] = datetime.fromisoformat(task_dict[date_field].replace("Z", "+00:00"))
                        # Convert enum strings back to enums
                        if "status" in task_dict:
                            task_dict["status"] = TaskStatus(task_dict["status"])
                        if "priority" in task_dict:
                            task_dict["priority"] = ProjectPriority(task_dict["priority"])
                        tasks.append(ImplementationTask(**task_dict))
                    else:
                        tasks.append(task_dict)
                impl_dict["tasks"] = tasks

            data["implementation_data"] = ImplementationData(**impl_dict)

        if "deployment_data" in data and isinstance(data["deployment_data"], dict):
            deploy_dict = data["deployment_data"].copy()
            # Handle nested environment objects
            if "environments" in deploy_dict:
                environments = []
                for env_dict in deploy_dict["environments"]:
                    if isinstance(env_dict, dict):
                        # Convert datetime strings back to datetime objects
                        if "deployed_at" in env_dict and isinstance(env_dict["deployed_at"], str):
                            env_dict["deployed_at"] = datetime.fromisoformat(env_dict["deployed_at"].replace("Z", "+00:00"))
                        # Convert enum strings back to enums
                        if "status" in env_dict:
                            env_dict["status"] = DeploymentStatus(env_dict["status"])
                        environments.append(DeploymentEnvironment(**env_dict))
                    else:
                        environments.append(env_dict)
                deploy_dict["environments"] = environments

            data["deployment_data"] = DeploymentData(**deploy_dict)

        # Handle artifacts dictionary
        if "artifacts" in data and isinstance(data["artifacts"], dict):
            artifacts_dict = {}
            for stage_name, artifacts_list in data["artifacts"].items():
                artifact_objects = []
                for artifact_dict in artifacts_list:
                    if isinstance(artifact_dict, dict):
                        # Convert datetime strings back to datetime objects
                        for date_field in ["created_at", "updated_at"]:
                            if date_field in artifact_dict and isinstance(artifact_dict[date_field], str):
                                try:
                                    artifact_dict[date_field] = datetime.fromisoformat(
                                        artifact_dict[date_field].replace("Z", "+00:00")
                                    )
                                except ValueError:
                                    pass
                        # Convert enum strings back to enums
                        if "type" in artifact_dict and isinstance(artifact_dict["type"], str):
                            artifact_dict["type"] = ArtifactType(artifact_dict["type"])
                        artifact_objects.append(ForgeArtifact(**artifact_dict))
                    else:
                        artifact_objects.append(artifact_dict)
                artifacts_dict[stage_name] = artifact_objects
            data["artifacts"] = artifacts_dict

        return cls(**data)


@dataclass
class ForgeTemplate:
    """Reusable project templates."""

    id: str
    name: str
    description: str
    category: str
    template_data: Dict[str, Any]  # Serialized project structure
    usage_count: int = 0
    rating: Optional[float] = None
    created_by: str = ""
    is_public: bool = False
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ForgeAnalytics:
    """Analytics data for Forge usage."""

    id: str
    user_id: str
    project_id: str
    event_type: str  # "stage_advance", "artifact_created", "ai_interaction", etc.
    event_data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: Optional[str] = None
    duration_ms: Optional[int] = None


# Helper functions for model validation and utilities


def generate_forge_id() -> str:
    """Generate a unique ID for Forge entities."""
    return f"forge_{uuid.uuid4().hex[:12]}"


def validate_stage_transition(current_stage: ForgeStage, target_stage: ForgeStage) -> bool:
    """Validate if stage transition is allowed."""
    stages = list(ForgeStage)
    current_index = stages.index(current_stage)
    target_index = stages.index(target_stage)

    # Can only move forward one stage at a time, or stay in same stage
    return target_index <= current_index + 1


def calculate_stage_completion_percentage(project: ForgeProject, stage: ForgeStage) -> float:
    """Calculate completion percentage for a specific stage."""
    # This is a simplified calculation - can be enhanced with more sophisticated logic
    stage_data = {
        ForgeStage.CONCEPTION: project.conception_data,
        ForgeStage.VALIDATION: project.validation_data,
        ForgeStage.PLANNING: project.planning_data,
        ForgeStage.IMPLEMENTATION: project.implementation_data,
        ForgeStage.DEPLOYMENT: project.deployment_data,
    }[stage]

    # Count non-empty fields as indicators of completion
    total_fields = len(asdict(stage_data))
    completed_fields = sum(
        1 for value in asdict(stage_data).values() if value and (not isinstance(value, (list, dict)) or value)
    )

    return (completed_fields / total_fields) * 100 if total_fields > 0 else 0
