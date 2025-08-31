from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserRole(str, Enum):
    """User roles in the system - simplified to match UX specification."""

    USER = "user"  # Standard user role for all personas (Content Creator, Developer, PM, CS)
    ADMIN = "admin"  # System administrator role for LLM config, budgets, user management


class PromptStatus(str, Enum):
    """Status of a prompt."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class PlaybookStatus(str, Enum):
    """Status of a playbook execution."""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


# =============================================================================
# USER MODELS
# =============================================================================


class User(BaseModel):
    """User model with email-based primary key and Microsoft Entra ID integration."""

    id: str  # Email address serves as primary key
    email: str  # Same as id for consistency
    name: str
    tenant_id: Optional[str] = None  # Microsoft Entra ID tenant ID
    object_id: Optional[str] = None  # Azure AD object ID
    role: UserRole = UserRole.USER
    preferences: Dict[str, Any] = Field(default_factory=dict)
    usage: Dict[str, int] = Field(
        default_factory=lambda: {"total_prompts": 0, "total_collections": 0, "total_playbooks": 0, "total_forge_projects": 0}
    )
    created_at: datetime
    last_active: datetime
    is_active: bool = True

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("id", "email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Ensure id and email are valid email addresses."""
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Must be a valid email address")
        return v.lower()  # Normalize to lowercase


# =============================================================================
# PROMPT MODELS
# =============================================================================


class PromptVariable(BaseModel):
    """Variable definition for prompts."""

    name: str
    description: str
    type: str = "string"  # string, number, boolean
    required: bool = True
    default_value: Optional[Union[str, int, float, bool]] = None


class PromptTemplate(BaseModel):
    """Prompt template model."""

    id: str
    user_id: str
    title: str
    description: str
    content: str
    variables: List[PromptVariable] = []
    tags: List[str] = []
    status: PromptStatus = PromptStatus.DRAFT
    version: int = 1
    parent_id: Optional[str] = None  # For versioning
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(use_enum_values=True)


class PromptExecution(BaseModel):
    """Record of a prompt execution."""

    id: str
    prompt_id: str
    user_id: str
    provider: LLMProvider
    prompt_content: str
    response: str
    variables: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    cost: float = 0.0
    tokens_used: int = 0
    execution_time_ms: int = 0
    created_at: datetime

    model_config = ConfigDict(use_enum_values=True)


# =============================================================================
# COLLECTION MODELS
# =============================================================================


class Collection(BaseModel):
    """Prompt collection model."""

    id: str
    user_id: str
    name: str
    description: str
    prompt_ids: List[str] = []
    tags: List[str] = []
    is_public: bool = False
    created_at: datetime
    updated_at: datetime


class CollectionShare(BaseModel):
    """Collection sharing model."""

    id: str
    collection_id: str
    shared_by_user_id: str
    shared_with_user_id: str
    permissions: List[str] = ["read"]  # read, write, admin
    created_at: datetime


# =============================================================================
# PLAYBOOK MODELS
# =============================================================================


class PlaybookStep(BaseModel):
    """Individual step in a playbook."""

    id: str
    step_number: int
    name: str
    description: str
    prompt_id: Optional[str] = None
    prompt_content: Optional[str] = None
    llm_providers: List[LLMProvider] = []
    requires_manual_review: bool = False
    auto_proceed: bool = True
    variables_mapping: Dict[str, str] = {}  # Maps output vars to input vars of next step
    conditions: Dict[str, Any] = {}  # Conditional logic

    model_config = ConfigDict(use_enum_values=True)


class Playbook(BaseModel):
    """Playbook (workflow) model."""

    id: str
    user_id: str
    name: str
    description: str
    steps: List[PlaybookStep] = []
    status: PlaybookStatus = PlaybookStatus.DRAFT
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(use_enum_values=True)


class PlaybookExecution(BaseModel):
    """Playbook execution instance."""

    id: str
    playbook_id: str
    user_id: str
    status: PlaybookStatus = PlaybookStatus.RUNNING
    current_step: int = 0
    step_results: List[Dict[str, Any]] = []
    variables: Dict[str, Any] = {}
    total_cost: float = 0.0
    total_tokens: int = 0
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)


# =============================================================================
# ADMIN MODELS
# =============================================================================


class LLMProviderConfig(BaseModel):
    """LLM provider configuration."""

    provider: LLMProvider
    enabled: bool = False
    api_key_secret_name: str
    budget_limit: float = 0.0
    priority: int = 1
    provider_config: Dict[str, Any] = {}
    rate_limits: Dict[str, Any] = {}

    model_config = ConfigDict(use_enum_values=True)


class UsageRecord(BaseModel):
    """Usage tracking record."""

    id: str
    user_id: str
    provider: LLMProvider
    operation: str  # prompt_execution, playbook_step, etc.
    cost: float
    tokens_used: int
    execution_time_ms: int
    date: str  # YYYY-MM-DD for partitioning
    timestamp: datetime
    metadata: Dict[str, Any] = {}

    model_config = ConfigDict(use_enum_values=True)


class SystemConfig(BaseModel):
    """System-wide configuration."""

    id: str = "system_config"
    type: str = "system"
    llm_providers: List[LLMProviderConfig] = []
    global_budget_limit: float = 0.0
    max_prompts_per_user: int = 1000
    max_collections_per_user: int = 100
    max_playbooks_per_user: int = 50
    maintenance_mode: bool = False
    allowed_domains: List[str] = []
    updated_at: datetime
    updated_by: str


# =============================================================================
# API REQUEST/RESPONSE MODELS
# =============================================================================


class CreatePromptRequest(BaseModel):
    """Request to create a new prompt."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., max_length=1000)
    content: str = Field(..., min_length=1)
    variables: List[PromptVariable] = []
    tags: List[str] = []
    collection_id: Optional[str] = None  # Allow prompts to be created in specific collections

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        return [tag.strip().lower() for tag in v if tag.strip()]


class UpdatePromptRequest(BaseModel):
    """Request to update an existing prompt."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    content: Optional[str] = Field(None, min_length=1)
    variables: Optional[List[PromptVariable]] = None
    tags: Optional[List[str]] = None
    status: Optional[PromptStatus] = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            return [tag.strip().lower() for tag in v if tag.strip()]
        return v


class ExecutePromptRequest(BaseModel):
    """Request to execute a prompt."""

    prompt_id: Optional[str] = None
    prompt_content: Optional[str] = None
    variables: Dict[str, Any] = {}
    providers: List[LLMProvider] = []

    @field_validator("providers")
    @classmethod
    def validate_providers(cls, v: List[LLMProvider]) -> List[LLMProvider]:
        if not v:
            return [LLMProvider.OPENAI]  # Default to OpenAI
        return v

    model_config = ConfigDict(use_enum_values=True)


class PromptExecutionResponse(BaseModel):
    """Response from prompt execution."""

    execution_id: str
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]] = []
    total_cost: float
    total_tokens: int
    execution_time_ms: int


class CreateCollectionRequest(BaseModel):
    """Request to create a new collection."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., max_length=1000)
    prompt_ids: List[str] = []
    tags: List[str] = []
    is_public: bool = False


class CreatePlaybookRequest(BaseModel):
    """Request to create a new playbook."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., max_length=1000)
    steps: List[PlaybookStep] = []
    tags: List[str] = []


class ExecutePlaybookRequest(BaseModel):
    """Request to execute a playbook."""

    playbook_id: str
    variables: Dict[str, Any] = {}
    auto_proceed: bool = True


# =============================================================================
# EXCEPTION MODELS
# =============================================================================


class ValidationError(Exception):
    """Exception raised when validation fails."""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


# =============================================================================
# ERROR MODELS
# =============================================================================


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ValidationErrorResponse(BaseModel):
    """Validation error response."""

    error: str = "validation_error"
    message: str
    field_errors: Dict[str, List[str]]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
