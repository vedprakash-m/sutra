# Technical Specification: Sutra Multi-LLM Prompt Studio

Ved Mishra - July 2025 - Version: 1.0

## Overview

**Sutra** is a comprehensive Multi-LLM Prompt Studio that provides a systematic platform for designing, managing, and orchestrating effective AI prompts and workflows. The platform combines advanced prompt engineering capabilities with structured idea-to-implementation workflows through the integrated Forge feature.

**Core Platform Capabilities:**

- **Multi-LLM Prompt Engineering:** Advanced prompt creation, optimization, and A/B testing across GPT-4, Claude, Gemini, and custom models
- **Collections Management:** Hierarchical organization and sharing of prompts, templates, and project artifacts
- **Playbooks Orchestration:** Multi-step AI workflow execution and automation supporting both general workflows and structured product development
- **Forge Workflows:** Systematic idea-to-implementation process through five guided stages (Idea Refinement, PRD Generation, UX Requirements, Technical Analysis, Implementation Playbook)
- **Team Collaboration:** Real-time sharing, permissions, enterprise governance, and read-only project collaboration with commenting
- **Cost Management:** Intelligent budget tracking, automated LLM routing, and comprehensive usage analytics

**Technical Architecture:**

- **Frontend:** React 18/TypeScript interface with comprehensive prompt engineering tools and integrated Forge workspace
- **Backend:** Azure Functions (Python 3.12) API ecosystem supporting prompts, collections, playbooks, and structured product development workflows
- **Database:** Cosmos DB with collections for Users, Prompts, Collections, Playbooks (including Forge project data), and comprehensive cost tracking
- **Authentication:** Microsoft Entra ID integration with role-based access control (Agent, Contributor, PromptManager, Admin)
- **LLM Integration:** Multi-LLM orchestration supporting GPT-4, Claude, Gemini, and custom models with intelligent routing and cost optimization
- **Storage:** Azure Blob Storage for document exports, artifacts, and large file management

## 1. Architecture Overview

Sutra is built on a modern serverless, event-driven architecture that scales automatically with usage while maintaining enterprise-grade security and performance. The platform integrates advanced prompt engineering capabilities with systematic product development workflows, providing a comprehensive solution for AI-powered development teams.

**Core System Components:**

- **Frontend Application:** React 18/TypeScript SPA with responsive design supporting prompt engineering, collections management, playbooks orchestration, and integrated Forge project workspace
- **API Layer:** Azure Functions (Python 3.12) providing comprehensive REST endpoints for authentication, prompts, collections, playbooks, LLM execution, cost management, and administrative functions
- **Database Layer:** Cosmos DB collections supporting Users, Prompts, Collections, Playbooks (including Forge project schemas), execution tracking, budget configurations, and usage metrics
- **LLM Orchestration:** Multi-model support for GPT-4, Claude, Gemini, and custom models with intelligent routing, cost optimization, and parallel execution capabilities
- **Collaboration System:** Real-time sharing, role-based permissions, read-only project collaboration with commenting, and enterprise governance features
- **Export & Integration:** Markdown/PDF generation, GitHub integration, project management tool synchronization, and external documentation platform support

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SUTRA MULTI-LLM PROMPT STUDIO                        │
│                            (Complete System Architecture)                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   Prompt Eng.   │  │   Collections   │  │  Forge Projects │                │
│  │   Studio        │  │   Management    │  │   Workspace     │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   Playbooks     │  │  Collaboration  │  │   Analytics &   │                │
│  │   Orchestration │  │   & Sharing     │  │  Cost Tracking  │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│ Infrastructure: React UI | Azure Functions | Cosmos DB | Entra ID | Blob Storage│
│ LLM Integration: GPT-4 | Claude | Gemini | Custom Models | Cost Optimization   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Frontend Architecture

### 2.1. Application Structure

**Core Technology Stack:**

- React 18 with TypeScript for type safety and modern development practices
- Responsive design system supporting desktop, tablet, and mobile viewports
- Real-time collaboration infrastructure with WebSocket connections
- Comprehensive authentication and user management interfaces
- Multi-LLM selection and execution interfaces with cost tracking

**Primary Application Components:**

- **PromptStudio**: Advanced prompt creation, optimization, and A/B testing interface
- **CollectionsManager**: Hierarchical organization and sharing of prompts, templates, and project artifacts
- **PlaybooksOrchestrator**: Multi-step workflow execution interface supporting general workflows and structured development processes
- **ForgeWorkspace**: Integrated idea-to-implementation project interface with five guided stages
- **CollaborationHub**: Real-time sharing, permissions management, and read-only project collaboration with commenting
- **AnalyticsDashboard**: Cost tracking, usage analytics, and performance monitoring interface

**Application Navigation Structure:**

```typescript
// Complete Sutra application routing structure
/dashboard                      // Main dashboard with overview
/prompts                       // Prompt engineering studio
/prompts/:id                   // Individual prompt editor
/collections                   // Collections management
/collections/:id               // Collection viewer
/playbooks                     // Playbooks orchestration
/playbooks/:id                 // Playbook editor/executor
/forge                         // Forge project dashboard
/forge/project/:id             // Forge project workspace
/forge/:id/idea                // Idea refinement stage
/forge/:id/prd                 // PRD generation stage
/forge/:id/ux                  // UX requirements stage
/forge/:id/tech                // Technical specification stage
/forge/:id/playbook            // Implementation playbook stage
/analytics                     // Cost and usage analytics
/integrations                  // External tool integrations
/admin                         // Administrative functions
```

**State Management Architecture:**

- **React Query**: Server state management with intelligent caching and synchronization for Forge projects
- **Zustand**: Global client state for user preferences, UI state, and real-time collaboration
- **Context Providers**: Authentication context, theme context, and notification system

**Enhanced Forge State Management (Zustand):**

```typescript
interface ForgeState {
  // Current project state
  currentProject: ForgeProject | null;
  isLoading: boolean;
  error: string | null;

  // Stage management
  currentStage: ForgeStage;
  stageProgress: Record<ForgeStage, number>;
  stageValidation: Record<ForgeStage, ValidationResult>;

  // Real-time collaboration
  collaborators: CollaboratorInfo[];
  activeComments: Comment[];
  conflictResolution: ConflictState;

  // Optimistic updates
  pendingChanges: PendingChange[];
  lastSyncTimestamp: number;

  // Actions
  setCurrentProject: (project: ForgeProject) => void;
  updateStageData: (stage: ForgeStage, data: any) => void;
  progressToNextStage: (stage: ForgeStage) => Promise<void>;

  // Collaboration actions
  addCollaborator: (userId: string) => void;
  addComment: (stageId: string, comment: Comment) => void;
  resolveConflict: (conflictId: string, resolution: ConflictResolution) => void;

  // Optimistic update handling
  applyOptimisticUpdate: (change: PendingChange) => void;
  revertOptimisticUpdate: (changeId: string) => void;
  syncWithServer: () => Promise<void>;
}

// Real-time collaboration handling
interface CollaborationManager {
  handleIncomingUpdate: (update: CollaborationUpdate) => void;
  mergeConflictingChanges: (local: any, remote: any) => ConflictResolution;
  broadcastChange: (change: StageChange) => void;
}

// Optimistic update system
interface OptimisticUpdateManager {
  queueUpdate: (update: StageUpdate) => void;
  processQueue: () => Promise<void>;
  handleServerConflict: (conflict: ServerConflict) => ConflictResolution;
  rollbackToLastKnownGood: () => void;
}
```

### 2.2. Backend Architecture

**Core Technology Stack:**

- Azure Functions (Python 3.12) providing serverless, event-driven architecture
- Comprehensive API ecosystem with consistent authentication, error handling, and monitoring
- Robust logging, monitoring, and cost tracking infrastructure
- Integration with Azure Application Insights for observability and performance monitoring

**API Function Categories:**

**Authentication & User Management:**

- **auth_api**: User authentication, token validation, and session management
- **user_management**: User profiles, preferences, and account operations
- **role_management**: Role-based access control and permission management

**Core Platform Functions:**

- **prompts_api**: CRUD operations for prompt management, versioning, and optimization
- **collections_api**: Hierarchical organization, sharing, and template management
- **playbooks_api**: Multi-step workflow orchestration supporting both general and structured development workflows
- **llm_execute**: Multi-LLM orchestration, execution, and intelligent routing
- **cost_management_api**: Budget tracking, usage monitoring, and automated controls
- **admin_api**: Administrative functions, analytics, and system configuration

**Forge Project Functions:**

- **forge_project_api**: CRUD operations for Forge projects stored as specialized Playbooks
- **idea_refinement_api**: AI-powered idea validation and systematic questioning
- **prd_generation_api**: Structured PRD document generation from validated ideas
- **ux_requirements_api**: User experience requirements and design specification generation
- **tech_spec_analysis_api**: Multi-LLM technical architecture evaluation
- **playbook_generation_api**: Implementation guide and coding prompt generation
- **forge_export_api**: Markdown and PDF export functionality
- **forge_sharing_api**: Read-only sharing and comment management

**Integration Functions:**

- **integrations_api**: External tool connections (GitHub, Jira, Linear, Asana)
- **export_services**: Documentation platform integration (Confluence, Notion, GitBook)
- **webhooks_api**: Real-time notifications and external system callbacks

\*\*Common Function Architecture Pattern:```python

# Standard Azure Function structure used across all Sutra APIs

import azure.functions as func
from shared.auth import validate_token
from shared.llm_orchestrator import LLMOrchestrator
from shared.cosmos_client import CosmosClient
from shared.cost_tracker import CostTracker

async def main(req: func.HttpRequest) -> func.HttpResponse: # Authentication validation using Microsoft Entra ID (no guest access) # Request validation and input sanitization # Business logic execution with appropriate LLM selection # Cost tracking and usage monitoring # Response formatting with proper error handling and logging

````

### 2.3. Database Architecture

**Core Data Foundation:**
Sutra maintains a comprehensive Cosmos DB architecture optimized for multi-tenancy, global distribution, and automatic scaling. The database design supports both traditional prompt engineering workflows and structured product development processes.

**Database Collections:**

**Users Collection**: Complete user profiles and authentication data
```json
{
  "id": "user_guid",
  "email": "user@domain.com",
  "displayName": "User Name",
  "role": "contributor|promptmanager|admin",
  "preferences": {
    "defaultLLM": "gpt-4o|claude-3|gemini-flash",
    "theme": "light|dark",
    "monthlyBudget": 100.00
  },
  "usage": {
    "currentMonthCost": 45.60,
    "totalPrompts": 1247,
    "totalForgeProjects": 3
  },
  "createdAt": "datetime",
  "lastActive": "datetime"
}
````

**Prompts Collection**: Core prompt management supporting all AI interactions

```json
{
  "id": "prompt_guid",
  "title": "Marketing Email Template",
  "content": "Create a marketing email for...",
  "userId": "user_guid",
  "tags": ["marketing", "email"],
  "llmModel": "gpt-4o",
  "variables": [{ "name": "product_name", "type": "string" }],
  "performance": {
    "avgLatency": 1200,
    "successRate": 0.98,
    "avgCostPerExecution": 0.05,
    "totalExecutions": 24
  },
  "createdAt": "datetime",
  "updatedAt": "datetime"
}
```

**Collections Collection**: Hierarchical organization of templates and artifacts

```json
{
  "id": "collection_guid",
  "name": "Marketing Templates",
  "description": "Email and social media templates",
  "type": "standard|forge_template",
  "userId": "user_guid",
  "items": ["prompt_guid_1", "prompt_guid_2"],
  "sharing": {
    "isPublic": false,
    "sharedWith": [{ "userId": "user_guid", "permission": "read|write" }]
  },
  "usage": {
    "totalViews": 156,
    "totalUses": 45
  },
  "createdAt": "datetime",
  "updatedAt": "datetime"
}
```

**Playbooks Collection**: Multi-step workflow orchestration and Forge project data

```json
{
  "id": "playbook_guid",
  "name": "Customer Onboarding Workflow",
  "description": "Automated customer onboarding process",
  "type": "general|forge_project",
  "userId": "user_guid",
  "steps": [
    {
      "id": "step_1",
      "type": "prompt|integration|delay",
      "promptId": "prompt_guid",
      "llmModel": "gpt-4o",
      "order": 1,
      "conditions": { "if": "variable_value", "then": "next_step" }
    }
  ],
  "status": "draft|active|completed|archived",
  "executionHistory": [
    {
      "executedAt": "datetime",
      "status": "success|failed",
      "totalCost": 0.15,
      "duration": 1200
    }
  ],
  "sharing": {
    "isPublic": false,
    "sharedWith": [{ "userId": "user_guid", "permission": "read|execute" }]
  },
  "createdAt": "datetime",
  "updatedAt": "datetime"
}
```

#### Forge Project Extensions (Additional fields when type = "forge_project")

**CRITICAL IMPLEMENTATION NOTE:** This is the definitive `forgeData` schema. All Forge functionality must implement this exact structure.

```json
{
  "forgeData": {
    "selectedLLM": "gemini-flash|gpt-4|claude-sonnet",
    "projectMetadata": {
      "createdAt": "datetime",
      "lastModified": "datetime",
      "version": "1.0.0",
      "qualityGate": "passed|failed|pending"
    },
    "ideaRefinement": {
      "status": "completed|in_progress|pending",
      "initialConcept": "string",
      "refinedConcept": {
        "problemStatement": "string",
        "targetAudience": "string",
        "valueProposition": "string",
        "successMetrics": ["string"]
      },
      "marketAnalysis": {
        "marketSize": "string",
        "competitors": ["string"],
        "competitiveAdvantage": "string"
      },
      "qualityMetrics": {
        "problemDefinition": 95,
        "marketAnalysis": 88,
        "userFocus": 92,
        "technicalScope": 78,
        "competitiveEdge": 85,
        "overall": 87.6
      }
    },
    "prdGeneration": {
      "status": "completed|in_progress|pending|skipped",
      "selectedTemplate": "saas_mvp|mobile_app|enterprise_software",
      "sections": {
        "executiveSummary": {
          "content": "string",
          "status": "approved|pending_review|draft",
          "qualityScore": 89
        },
        "problemStatement": {
          "content": "string",
          "status": "approved",
          "qualityScore": 92
        },
        "targetUsers": {
          "content": "string",
          "status": "approved",
          "qualityScore": 88
        },
        "featureSpecifications": {
          "content": "string",
          "status": "pending_review",
          "qualityScore": 76
        },
        "successMetrics": {
          "content": "string",
          "status": "draft",
          "qualityScore": 65
        },
        "technicalRequirements": {
          "content": "string",
          "status": "pending",
          "qualityScore": 0
        }
      },
      "overallQualityScore": 81
    },
    "uxRequirements": {
      "status": "completed|in_progress|pending|skipped",
      "skipDecision": {
        "skipped": true,
        "reason": "external_ux_team|api_only_project|time_constraint",
        "qualityImpact": 25,
        "compensationApplied": "basic_ux_prompt|external_team_note|none"
      },
      "userJourneys": [
        {
          "id": "journey_guid",
          "name": "User Registration Flow",
          "steps": ["string"],
          "touchpoints": ["string"],
          "painPoints": ["string"]
        }
      ],
      "wireframes": [
        {
          "id": "wireframe_guid",
          "screenName": "Dashboard",
          "description": "string",
          "interactions": ["string"]
        }
      ],
      "designSystem": {
        "colorPalette": "string",
        "typography": "string",
        "componentLibrary": "string"
      }
    },
    "technicalAnalysis": {
      "status": "completed|in_progress|pending",
      "multiLLMAnalysis": {
        "gpt4Analysis": {
          "businessImpact": "string",
          "userExperience": "string",
          "recommendationScore": 85
        },
        "claudeAnalysis": {
          "technicalFeasibility": "string",
          "architectureAssessment": "string",
          "recommendationScore": 92
        },
        "geminiAnalysis": {
          "competitiveAnalysis": "string",
          "innovationOpportunities": "string",
          "recommendationScore": 78
        }
      },
      "recommendedStack": {
        "frontend": "React|Vue|Angular",
        "backend": "Node.js|Python|Java",
        "database": "PostgreSQL|MongoDB|MySQL",
        "deployment": "AWS|Azure|Vercel"
      },
      "architectureDecisions": [
        {
          "decision": "string",
          "rationale": "string",
          "alternatives": ["string"]
        }
      ]
    },
    "implementationPlaybook": {
      "status": "completed|in_progress|pending",
      "milestones": [
        {
          "id": "milestone_guid",
          "name": "MVP Development",
          "tasks": ["string"],
          "duration": "4 weeks",
          "dependencies": ["string"]
        }
      ],
      "testingStrategy": {
        "unitTests": "string",
        "integrationTests": "string",
        "e2eTests": "string"
      },
      "deploymentPlan": {
        "environment": "staging|production",
        "steps": ["string"],
        "rollbackPlan": "string"
      }
    },
    "costTracking": {
      "totalTokensUsed": 15420,
      "costByStage": {
        "ideaRefinement": 0.5,
        "prdGeneration": 2.1,
        "uxRequirements": 0.0,
        "technicalAnalysis": 1.2,
        "implementationPlaybook": 0.0
      },
      "totalCost": 3.8,
      "budgetLimit": 50.0,
      "projectedCost": 8.4
    },
    "collaboration": {
      "sharedWith": [
        {
          "userId": "user_guid",
          "role": "viewer|commenter|editor",
          "sharedAt": "datetime"
        }
      ],
      "comments": [
        {
          "id": "comment_guid",
          "userId": "user_guid_2",
          "stage": "technical_analysis",
          "content": "Consider scalability for mobile deployment",
          "createdAt": "datetime"
        }
      ]
    },
    "qualityAssurance": {
      "overallQualityScore": 84.2,
      "stageQualityBreakdown": {
        "ideaRefinement": 87.6,
        "prdGeneration": 81.0,
        "uxRequirements": 0.0,
        "technicalAnalysis": 85.0,
        "implementationPlaybook": 0.0
      },
      "qualityGates": {
        "minimumScore": 70,
        "currentStatus": "passed",
        "recommendations": ["Improve UX coverage", "Add security requirements"]
      }
    }
  }
}
```

          "problemDefinition": 95,
          "marketAnalysis": 88,
          "userFocus": 92,
          "technicalScope": 78,
          "competitiveEdge": 85,
          "overall": 87.6
        }
      },
      "prdGeneration": {
        "status": "completed|in_progress|pending|skipped",
        "selectedTemplate": "saas_mvp|mobile_app|enterprise_software",
        "sections": {
          "executiveSummary": {
            "content": "string",
            "status": "approved|pending_review|draft",
            "qualityScore": 89
          },
          "problemStatement": { "content": "string", "status": "approved", "qualityScore": 92 },
          "targetUsers": { "content": "string", "status": "approved", "qualityScore": 88 },
          "featureSpecifications": { "content": "string", "status": "pending_review", "qualityScore": 76 },
          "successMetrics": { "content": "string", "status": "draft", "qualityScore": 65 },
          "technicalRequirements": { "content": "string", "status": "pending", "qualityScore": 0 }
        },
        "overallQualityScore": 81
      },
      "uxRequirements": {
        "status": "skipped|completed|in_progress|pending",
        "skipDecision": {
          "userRequested": true,
          "skipReason": "api_service|external_ux_team|timeline_constraints",
          "compensationChoice": "comprehensive_ux_prompts|basic_ux_prompts|ux_research_tasks|no_compensation",
          "qualityImpactAccepted": 20,
          "estimatedAdditionalCost": 0.045,
          "userConfirmedAt": "datetime"
        },
        "qualityMetrics": {
          "promptDeterminismScore": 85.2,
          "specificityScore": 88.0,
          "actionabilityScore": 82.5,
          "completenessScore": 84.0,
          "clarityScore": 86.3
        },
        "platformRequirements": {
          "mobile": { "ios": true, "android": false, "requirements": ["touch-first", "offline-sync"] },
          "web": { "desktop": false, "tablet": false, "requirements": [] }
        },
        "userJourneys": [
          {
            "name": "User Registration",
            "steps": ["email_signup", "profile_setup", "team_invitation"],
            "status": "completed",
            "painPoints": ["Complex signup flow"],
            "pdsScore": 89.2
          }
        ],
        "accessibilityCompliance": {
          "standard": "WCAG 2.1 AA",
          "currentScore": 94,
          "requirements": ["screen_reader", "keyboard_navigation", "color_contrast"]
        }
      },
      "techAnalysis": {
        "status": "completed|in_progress|pending",
        "selectedLLMs": ["gemini-flash", "gpt-4o", "claude-3"],
        "architectureOptions": [
          {
            "name": "React Native + Node.js + MongoDB",
            "scores": {
              "scalability": 8.5,
              "developmentSpeed": 9.1,
              "maintenance": 8.0,
              "cost": 9.2,
              "teamFit": 8.9,
              "overall": 8.74
            },
            "recommended": true,
            "llmAnalysis": {
              "gemini": "Optimal for cross-platform development...",
              "gpt4": "Strong business case with proven scalability...",
              "claude": "Technical architecture is sound with good maintainability..."
            }
          }
        ],
        "finalRecommendation": {
          "architecture": "React Native + Node.js + MongoDB",
          "reasoning": "Best balance of development speed, cost, and team expertise"
        }
      },
      "implementationPlaybook": {
        "status": "completed|in_progress|pending",
        "developmentPhases": [
          {
            "name": "Foundation Setup",
            "duration": "2 weeks",
            "tasks": [
              {
                "title": "Project scaffolding",
                "description": "Set up React Native project structure",
                "estimatedHours": 8,
                "priority": "high",
                "codingPrompts": ["Create React Native project with TypeScript..."]
              }
            ]
          }
        ],
        "qualityGates": [
          {
            "phase": "Development",
            "criteria": ["Unit test coverage >80%", "Code review approval"],
            "tools": ["Jest", "ESLint", "SonarQube"]
          }
        ],
        "deploymentStrategy": {
          "environment": "Azure",
          "cicd": "GitHub Actions",
          "monitoring": "Application Insights"
        }
      }
    },
    "sharing": {
      "sharedWith": [
        {
          "userId": "user_guid",
          "email": "user@example.com",
          "access": "read_only",
          "sharedAt": "datetime"
        }
      ],
      "comments": [
        {
          "id": "comment_guid",
          "userId": "user_guid",
          "stage": "prd_generation",
          "section": "featureSpecifications",
          "content": "Consider adding mobile-specific features",
          "createdAt": "datetime",
          "resolved": false
        }
      ]
    },
    "costTracking": {
      "budgetAllocated": 25.00,
      "totalTokensUsed": 15420,
      "totalCost": 0.47,
      "costByStage": {
        "ideaRefinement": {"tokens": 2340, "cost": 0.12, "llm": "gemini-flash"},
        "prdGeneration": {"tokens": 5120, "cost": 0.18, "llm": "gemini-flash"},
        "uxRequirements": {"tokens": 1890, "cost": 0.05, "llm": "gemini-flash", "compensationCost": 0.015},
        "techAnalysis": {"tokens": 4200, "cost": 0.08, "multiLLM": true, "llmBreakdown": {
          "gemini-flash": {"tokens": 1400, "cost": 0.025},
          "gpt-4o": {"tokens": 1400, "cost": 0.035},
          "claude-3": {"tokens": 1400, "cost": 0.020}
        }},
        "implementationPlaybook": {"tokens": 1870, "cost": 0.04, "llm": "gemini-flash"}
      },
      "budgetAlerts": [
        {
          "threshold": 75,
          "triggeredAt": "datetime",
          "userNotified": true,
          "action": "warning_displayed"
        }
      ],
      "costPredictions": {
        "nextStageEstimate": 0.08,
        "projectCompletionEstimate": 0.62,
        "budgetSufficient": true
      }
    },
    "qualityMetrics": {
      "overallPDS": 87.4,
      "stageQuality": {
        "ideaRefinement": {"pds": 92.1, "completeness": 95, "actionability": 89.5},
        "prdGeneration": {"pds": 88.3, "completeness": 92, "actionability": 85.2},
        "uxRequirements": {"pds": 85.7, "completeness": 89, "actionability": 82.8},
        "techAnalysis": {"pds": 91.2, "completeness": 94, "actionability": 89.1},
        "implementationPlaybook": {"pds": 89.8, "completeness": 91, "actionability": 92.3}
      },
      "qualityTrends": {
        "improving": true,
        "lastUpdated": "datetime",
        "improvementSuggestions": ["Add more specific error handling requirements", "Include concrete user interface specifications"]
      }
    },
    "autoSaveState": {
      "lastSaved": "datetime",
      "currentStage": "tech_analysis",
      "recoveryPointsAvailable": 5,
      "autoSaveEnabled": true,
      "saveInterval": 30
    },
    "metadata": {
      "industry": "project_management",
      "complexity": "medium",
      "estimatedTimeline": "thorough",
      "tags": ["mobile", "collaboration", "mvp"]
    }

}
}

````

## 3. LLM Integration Architecture

### 3.1. Multi-LLM Orchestration System

Sutra provides comprehensive multi-LLM orchestration supporting GPT-4, Claude, Gemini, and custom models. The platform includes intelligent routing, cost optimization, model comparison, and enterprise-grade LLM management capabilities.

#### Forge Module LLM Strategy:
- **Default LLM for All Forge Stages:** Gemini Flash (optimal speed and cost for systematic development workflows)
- **One-time LLM Selection:** Selected at Forge project start and locked for consistency throughout all stages (default: Gemini Flash)
- **Stage 4 Multi-LLM Analysis:** Automatically uses all admin-configured LLMs for comprehensive technical evaluation
- **Platform LLM Flexibility:** Users maintain full LLM selection flexibility for all other Sutra features

**LLM Selection Strategy:**
```python
class SutraLLMOrchestrator:
    def __init__(self):
        self.forge_default_model = "gemini-flash"  # Default for all Forge stages
        self.admin_configured_models = ["gpt-4", "claude-3", "gemini-flash"]
        self.forge_locked_model = None  # Set at project start, locked for consistency

    def select_forge_llm(self, project_id: str, user_selection: str = None):
        """One-time LLM selection for Forge project consistency"""
        selected_model = user_selection or self.forge_default_model
        self.forge_locked_model = selected_model
        return selected_model

    def execute_forge_stage(self, stage: str, project_id: str):
        """Execute Forge stage with appropriate LLM strategy"""
        if stage == "technical_analysis":
            # Stage 4: Automatically use all admin-configured LLMs
            return self.multi_llm_analysis(self.admin_configured_models)
        else:
            # Stages 1-3, 5: Use locked model for consistency
            return self.single_llm_execution(self.forge_locked_model)
````

        self.default_model = 'gemini-flash'  # Optimal cost/performance ratio
        self.available_models = ['gemini-flash', 'gpt-4o', 'claude-3', 'custom-models']

    async def execute_general_workflow(self, playbook_id: str, step: str, data: dict):
        """Execute general playbook steps using user-selected or default LLM"""
        playbook = await self.get_playbook(playbook_id)
        selected_llm = playbook.get('preferredLLM', self.default_model)
        return await self.execute_with_model(selected_llm, step, data)

    async def execute_forge_workflow(self, project_id: str, stage: str, data: dict):
        """Execute Forge project stages with stage-specific LLM strategy"""
        project = await self.get_forge_project(project_id)
        selected_llm = project.forgeData.selectedLLM

        if stage == 'tech_analysis':
            # Automatically use all admin-configured LLMs for comprehensive technical evaluation
            return await self.multi_llm_technical_analysis(data)
        else:
            # Use project's selected LLM for consistency across stages
            return await self.execute_with_model(selected_llm, stage, data)

    async def multi_llm_technical_analysis(self, requirements: dict):
        """Multi-LLM technical analysis for comprehensive evaluation"""
        admin_configured_llms = await self.get_admin_configured_llms()
        results = {}

        for llm in admin_configured_llms:
            try:
                analysis = await self.execute_with_model(llm, 'technical_analysis', requirements)
                results[llm] = analysis
            except Exception as e:
                results[llm] = {"error": str(e), "status": "failed"}

        return await self.synthesize_tech_analysis(results)

````

### 3.2. Prompt Engineering Framework

**Comprehensive Prompt Library:**
Sutra maintains a sophisticated prompt engineering system supporting both general-purpose workflows and specialized product development processes.

**Core Prompt Categories:**
```python
class SutraPromptLibrary:
    # General prompt engineering templates
    OPTIMIZATION_PROMPTS = {
        "clarity_enhancement": "Analyze the following prompt for clarity...",
        "performance_tuning": "Optimize this prompt for better LLM performance...",
        "bias_detection": "Review this prompt for potential biases..."
    }

    # Forge-specific structured prompts for product development
    FORGE_PROMPTS = {
        "IDEA_REFINEMENT": """
        System: You are a product development expert helping refine a raw idea.

        Context: {idea_context}
        Current Understanding: {current_understanding}

        Task: Generate 5 clarifying questions focusing on {focus_area}

        Output Format:
        - Question 1: [Clear, specific question]
        - Question 2: [Clear, specific question]
        - Question 3: [Clear, specific question]
        - Question 4: [Clear, specific question]
        - Question 5: [Clear, specific question]
        """,

        "UX_REQUIREMENTS_ANALYSIS": """
        System: You are a UX/UI expert helping define user experience requirements.

        PRD Context: {prd_context}
        User Personas: {user_personas}
        Platform Requirements: {platform_requirements}

        Task: Analyze the product requirements and generate comprehensive UX requirements

        Focus Areas:
        1. User Journey Mapping
        2. Interface Design Requirements
        3. Accessibility Considerations
        4. Platform-Specific Guidelines
        5. Interaction Patterns

        Output Format:
        - User Journeys: [Detailed step-by-step user flows]
        - Design Requirements: [UI patterns, components, layouts]
        - Accessibility: [WCAG compliance, inclusive design]
        - Platform Considerations: [Web, mobile, desktop specific requirements]
        """,

        "TECH_STACK_ANALYSIS": """
        System: You are a senior software architect evaluating technical stack options.

        Requirements: {prd_requirements}
        UX Requirements: {ux_requirements}
        Team Context: {team_capabilities}
        Constraints: {technical_constraints}

        Task: Evaluate the following technical stack hypothesis:
        {tech_stack_hypothesis}

        Analyze across dimensions:
        1. Scalability (1-10 score + reasoning)
        2. Maintainability (1-10 score + reasoning)
        3. Development Speed (1-10 score + reasoning)
        4. Cost Efficiency (1-10 score + reasoning)
        5. Risk Level (1-10 score + reasoning)
        6. Team Fit (1-10 score + reasoning)

        Output JSON format with scores and detailed reasoning for each dimension.
        """
    }

    # Collaborative prompt optimization
    COLLABORATION_PROMPTS = {
        "peer_review": "Review this prompt for effectiveness and suggest improvements...",
        "version_comparison": "Compare these two prompt versions and recommend the better approach..."
    }
````

## 2.5. Quality Scoring Framework Implementation

**CRITICAL IMPLEMENTATION REQUIREMENT:** This framework provides concrete prompts and evaluation criteria for LLM agents to implement quality scoring consistently across all Forge stages.

#### Quality Metrics System

```python
class ForgeQualityScorer:
    """
    Concrete implementation of quality scoring for LLM agents.
    Each metric uses specific prompts and weighted evaluation criteria.
    """

    def calculate_idea_refinement_quality(self, idea_data: dict) -> dict:
        """
        Quality scoring for Stage 1: Idea Refinement
        Returns: quality_metrics with specific scores and overall calculation
        """
        scoring_prompts = {
            "problemDefinition": {
                "prompt": "Rate the problem clarity on scale 0-100. Consider: Is the problem specific, measurable, and clearly articulated? Does it identify a real pain point?",
                "criteria": ["specificity", "measurability", "urgency", "scope"],
                "weight": 0.25
            },
            "marketAnalysis": {
                "prompt": "Evaluate market understanding on scale 0-100. Consider: Is target market clearly defined? Are competitors identified? Is market size understood?",
                "criteria": ["target_market_clarity", "competitive_landscape", "market_size_estimate", "differentiation"],
                "weight": 0.20
            },
            "userFocus": {
                "prompt": "Rate user-centricity on scale 0-100. Consider: Are user needs clearly identified? Is target audience specific? Are user benefits articulated?",
                "criteria": ["user_persona_clarity", "needs_identification", "benefit_articulation", "user_validation"],
                "weight": 0.20
            },
            "technicalScope": {
                "prompt": "Assess technical feasibility understanding on scale 0-100. Consider: Is technical complexity acknowledged? Are constraints identified? Is scope realistic?",
                "criteria": ["complexity_awareness", "constraint_identification", "scope_realism", "technical_risks"],
                "weight": 0.20
            },
            "competitiveEdge": {
                "prompt": "Evaluate competitive advantage on scale 0-100. Consider: Is differentiation clear? Are unique value propositions identified? Is competitive positioning understood?",
                "criteria": ["differentiation_clarity", "unique_value_props", "positioning_strategy", "competitive_barriers"],
                "weight": 0.15
            }
        }

        # Implementation: Use these prompts to calculate individual scores
        scores = {}
        for metric, config in scoring_prompts.items():
            scores[metric] = self.llm_evaluate(
                prompt=config["prompt"],
                content=idea_data,
                criteria=config["criteria"]
            )

        # Weighted overall calculation
        overall_score = sum(scores[metric] * scoring_prompts[metric]["weight"]
                          for metric in scores)

        return {
            **scores,
            "overall": round(overall_score, 1),
            "calculation_method": "weighted_average",
            "quality_gate_threshold": 70.0
        }

    def calculate_prd_section_quality(self, section_content: str, section_type: str) -> float:
        """
        Quality scoring for Stage 2: PRD Generation sections
        Returns: Individual section quality score 0-100
        """
        section_prompts = {
            "executiveSummary": "Rate executive summary on scale 0-100. Consider: Is it concise yet comprehensive? Does it capture key value propositions? Is it stakeholder-ready?",
            "problemStatement": "Rate problem statement on scale 0-100. Consider: Is the problem clearly defined? Are pain points specific? Is urgency conveyed?",
            "targetUsers": "Rate target user definition on scale 0-100. Consider: Are user personas specific? Are use cases clear? Is target market quantified?",
            "featureSpecifications": "Rate feature specifications on scale 0-100. Consider: Are features clearly defined? Are requirements specific? Is scope manageable?",
            "successMetrics": "Rate success metrics on scale 0-100. Consider: Are metrics measurable? Are targets realistic? Are KPIs aligned with goals?",
            "technicalRequirements": "Rate technical requirements on scale 0-100. Consider: Are requirements specific? Are constraints identified? Is architecture outlined?"
        }

        return self.llm_evaluate(
            prompt=section_prompts.get(section_type, "Rate content quality on scale 0-100"),
            content=section_content,
            criteria=["clarity", "completeness", "actionability", "specificity"]
        )

    def calculate_overall_prd_quality(self, prd_sections: dict) -> float:
        """
        Calculate overall PRD quality from individual section scores
        """
        section_weights = {
            "executiveSummary": 0.15,
            "problemStatement": 0.20,
            "targetUsers": 0.20,
            "featureSpecifications": 0.25,
            "successMetrics": 0.15,
            "technicalRequirements": 0.05
        }

        weighted_score = 0
        total_weight = 0

        for section, data in prd_sections.items():
            if section in section_weights and data.get("qualityScore", 0) > 0:
                weighted_score += data["qualityScore"] * section_weights[section]
                total_weight += section_weights[section]

        return round(weighted_score / total_weight if total_weight > 0 else 0, 1)

    def evaluate_quality_gate(self, overall_score: float, minimum_threshold: float = 70.0) -> dict:
        """
        Quality gate evaluation with specific recommendations
        """
        status = "passed" if overall_score >= minimum_threshold else "failed"

        recommendations = []
        if overall_score < minimum_threshold:
            gap = minimum_threshold - overall_score
            if gap > 20:
                recommendations.append("Major improvements needed across multiple areas")
            elif gap > 10:
                recommendations.append("Moderate improvements needed in key areas")
            else:
                recommendations.append("Minor improvements needed to meet quality standards")

        return {
            "status": status,
            "score": overall_score,
            "threshold": minimum_threshold,
            "gap": max(0, minimum_threshold - overall_score),
            "recommendations": recommendations,
            "next_action": "proceed" if status == "passed" else "iterate"
        }

# Quality Scoring Implementation for LLM Integration
QUALITY_SCORING_SYSTEM = {
    "evaluation_model": "same_as_stage_llm",  # Use the locked Forge LLM for consistency
    "scoring_scale": "0-100",
    "quality_gate_threshold": 70.0,
    "minimum_scores_per_stage": {
        "idea_refinement": 70.0,
        "prd_generation": 70.0,
        "ux_requirements": 60.0,  # Lower threshold due to optional nature
        "technical_analysis": 75.0,  # Higher threshold for technical accuracy
        "implementation_playbook": 70.0
    },
    "auto_quality_checking": True,
    "quality_recommendations_enabled": True
}
```

### 2.6. Collaboration Conflict Resolution Framework

**CRITICAL IMPLEMENTATION REQUIREMENT:** This framework defines how real-time collaboration conflicts are detected, resolved, and synchronized across multiple users working on the same Forge project.

#### Conflict Detection and Resolution System

```python
class ForgeCollaborationManager:
    """
    Handles real-time collaboration conflicts for Forge projects
    Implements optimistic updates with conflict resolution strategies
    """

    def __init__(self):
        self.conflict_resolution_strategies = {
            "last_write_wins": self.resolve_last_write_wins,
            "merge_content": self.resolve_merge_content,
            "user_choice": self.resolve_user_choice,
            "admin_override": self.resolve_admin_override
        }
        self.update_buffer = {}  # Temporary storage for pending updates
        self.version_vector = {}  # Track document versions

    def detect_conflict(self, update: dict) -> dict:
        """
        Detect collaboration conflicts using vector clocks and content comparison
        """
        conflict_types = {
            "simultaneous_edit": self.check_simultaneous_edits(update),
            "version_mismatch": self.check_version_conflicts(update),
            "stage_progression": self.check_stage_conflicts(update),
            "quality_score_conflict": self.check_quality_conflicts(update)
        }

        active_conflicts = {k: v for k, v in conflict_types.items() if v}

        return {
            "has_conflict": bool(active_conflicts),
            "conflict_types": active_conflicts,
            "resolution_strategy": self.determine_resolution_strategy(active_conflicts),
            "affected_sections": self.identify_affected_sections(update),
            "conflicting_users": self.get_conflicting_users(update)
        }

    def resolve_last_write_wins(self, conflict_data: dict) -> dict:
        """
        Simple conflict resolution: Most recent update wins
        Used for: Non-critical updates, user preference changes, comment additions
        """
        latest_update = max(conflict_data["updates"], key=lambda x: x["timestamp"])

        return {
            "resolution_method": "last_write_wins",
            "winning_update": latest_update,
            "applied_changes": latest_update["changes"],
            "discarded_updates": [u for u in conflict_data["updates"] if u != latest_update],
            "notification_required": True
        }

    def resolve_merge_content(self, conflict_data: dict) -> dict:
        """
        Intelligent content merging for non-conflicting sections
        Used for: Different section updates, additive changes, comment threads
        """
        merged_content = {}
        conflict_sections = []

        for update in conflict_data["updates"]:
            for section, content in update["changes"].items():
                if section not in merged_content:
                    merged_content[section] = content
                elif self.can_merge_automatically(merged_content[section], content):
                    merged_content[section] = self.merge_section_content(
                        merged_content[section], content
                    )
                else:
                    conflict_sections.append({
                        "section": section,
                        "versions": [merged_content[section], content],
                        "requires_user_input": True
                    })

        return {
            "resolution_method": "merge_content",
            "merged_content": merged_content,
            "conflict_sections": conflict_sections,
            "auto_merged_sections": list(merged_content.keys()),
            "user_resolution_required": bool(conflict_sections)
        }

    def resolve_user_choice(self, conflict_data: dict) -> dict:
        """
        Present conflict to users for manual resolution
        Used for: Critical content conflicts, quality score disputes, stage progression conflicts
        """
        return {
            "resolution_method": "user_choice",
            "conflict_presentation": {
                "title": "Collaboration Conflict Detected",
                "description": f"Multiple users have modified the same content. Please choose how to proceed.",
                "options": [
                    {
                        "id": "version_a",
                        "label": f"Use {conflict_data['users'][0]}'s version",
                        "preview": conflict_data["updates"][0]["preview"],
                        "timestamp": conflict_data["updates"][0]["timestamp"]
                    },
                    {
                        "id": "version_b",
                        "label": f"Use {conflict_data['users'][1]}'s version",
                        "preview": conflict_data["updates"][1]["preview"],
                        "timestamp": conflict_data["updates"][1]["timestamp"]
                    },
                    {
                        "id": "merge_manual",
                        "label": "Manually merge changes",
                        "preview": "Open side-by-side editor for manual resolution"
                    }
                ]
            },
            "pending_resolution": True,
            "timeout": 300  # 5 minutes to resolve
        }

    def handle_optimistic_updates(self, project_id: str, user_update: dict) -> dict:
        """
        Implement optimistic updates with rollback capability
        """
        # 1. Apply update immediately for responsive UX
        optimistic_state = self.apply_update_locally(user_update)

        # 2. Send to server for validation and conflict detection
        server_response = self.send_update_to_server(project_id, user_update)

        # 3. Handle server response
        if server_response.get("conflict_detected"):
            # Rollback optimistic update and present conflict resolution
            rollback_state = self.rollback_optimistic_update(user_update)
            conflict_resolution = self.initiate_conflict_resolution(
                server_response["conflict_data"]
            )

            return {
                "status": "conflict",
                "local_state": rollback_state,
                "conflict_resolution": conflict_resolution,
                "user_action_required": True
            }
        else:
            # Confirm optimistic update was successful
            return {
                "status": "success",
                "local_state": optimistic_state,
                "server_confirmed": True,
                "user_action_required": False
            }

# Real-time Collaboration Event Handlers
class ForgeWebSocketHandler:
    """
    WebSocket handlers for real-time Forge collaboration
    """

    def __init__(self):
        self.collaboration_manager = ForgeCollaborationManager()
        self.active_sessions = {}  # Track active user sessions per project

    async def handle_forge_update(self, websocket, project_id: str, update_data: dict):
        """
        Handle real-time Forge project updates
        """
        # Track active user session
        user_id = update_data["user_id"]
        self.active_sessions[project_id] = self.active_sessions.get(project_id, set())
        self.active_sessions[project_id].add(user_id)

        # Process update with conflict detection
        conflict_check = self.collaboration_manager.detect_conflict(update_data)

        if conflict_check["has_conflict"]:
            # Handle conflict according to resolution strategy
            resolution = await self.resolve_conflict(conflict_check, update_data)
            await self.broadcast_conflict_resolution(project_id, resolution)
        else:
            # Broadcast successful update to all collaborators
            await self.broadcast_update(project_id, update_data, exclude_user=user_id)

        # Update project state in database
        await self.persist_project_state(project_id, update_data)

    async def broadcast_conflict_resolution(self, project_id: str, resolution: dict):
        """
        Broadcast conflict resolution to all active collaborators
        """
        notification = {
            "type": "collaboration_conflict",
            "project_id": project_id,
            "resolution": resolution,
            "timestamp": datetime.utcnow().isoformat(),
            "requires_action": resolution.get("user_resolution_required", False)
        }

        # Send to all active users in the project
        for user_id in self.active_sessions.get(project_id, set()):
            await self.send_to_user(user_id, notification)

# Collaboration Conflict Resolution API
async def handle_collaboration_conflict(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/forge/projects/{project_id}/collaboration/resolve-conflict

    Resolve collaboration conflicts with user input
    Input: {
        "conflict_id": "string",
        "resolution_choice": "version_a|version_b|merge_manual",
        "manual_merge_content": "object",  // Required if resolution_choice = merge_manual
        "user_id": "string"
    }
    Output: {
        "resolution_status": "resolved|pending|failed",
        "applied_changes": "object",
        "project_state": "object",
        "notification_sent": "boolean"
    }
    """
```

### 2.7. Forge-to-Playbook Transformation Logic

**CRITICAL IMPLEMENTATION REQUIREMENT:** This section defines the explicit mapping logic for transforming rich Forge project data into executable Sutra Playbooks.

#### Transformation Mapping Rules

```python
class ForgeToPlaybookTransformer:
    """
    Explicit transformation logic for converting Forge project data into executable Playbooks.
    LLM agents must implement these exact mapping rules for consistent output generation.
    """

    def transform_forge_to_playbook(self, forge_project: dict) -> dict:
        """
        Master transformation function that orchestrates the complete mapping process
        """
        playbook = {
            "name": f"Implementation Guide: {forge_project['name']}",
            "description": self.generate_playbook_description(forge_project),
            "type": "implementation_guide",
            "steps": [],
            "metadata": self.extract_metadata(forge_project)
        }

        # Sequential transformation based on completed stages
        if forge_project["forgeData"]["ideaRefinement"]["status"] == "completed":
            playbook["steps"].extend(self.transform_idea_refinement(forge_project))

        if forge_project["forgeData"]["prdGeneration"]["status"] == "completed":
            playbook["steps"].extend(self.transform_prd_generation(forge_project))

        if forge_project["forgeData"]["uxRequirements"]["status"] == "completed":
            playbook["steps"].extend(self.transform_ux_requirements(forge_project))
        elif forge_project["forgeData"]["uxRequirements"]["status"] == "skipped":
            playbook["steps"].extend(self.apply_ux_compensation(forge_project))

        if forge_project["forgeData"]["technicalAnalysis"]["status"] == "completed":
            playbook["steps"].extend(self.transform_technical_analysis(forge_project))

        # Final integration and validation steps
        playbook["steps"].extend(self.generate_integration_steps(forge_project))

        return playbook

    def transform_idea_refinement(self, forge_project: dict) -> list:
        """
        Stage 1: Idea Refinement → Playbook Introduction

        Mapping Rules:
        - refinedConcept.problemStatement → First step with context comment
        - refinedConcept.targetAudience → User persona definition step
        - refinedConcept.valueProposition → Value validation checkpoint
        - marketAnalysis → Competitive research task
        """
        idea_data = forge_project["forgeData"]["ideaRefinement"]

        steps = [
            {
                "id": "project_context",
                "type": "documentation",
                "title": "Project Context & Problem Definition",
                "description": f"# Problem Statement\n{idea_data['refinedConcept']['problemStatement']}\n\n# Target Audience\n{idea_data['refinedConcept']['targetAudience']}\n\n# Value Proposition\n{idea_data['refinedConcept']['valueProposition']}",
                "prompts": [
                    {
                        "content": f"You are implementing a solution for: {idea_data['refinedConcept']['problemStatement']}. Keep this core problem in mind throughout development.",
                        "llm": forge_project["forgeData"]["selectedLLM"]
                    }
                ]
            },
            {
                "id": "competitive_analysis_validation",
                "type": "research",
                "title": "Competitive Analysis Validation",
                "description": f"Validate competitive positioning based on: {idea_data['marketAnalysis']['competitiveAdvantage']}",
                "prompts": [
                    {
                        "content": f"Research and validate these competitors: {', '.join(idea_data['marketAnalysis']['competitors'])}. Ensure our solution addresses gaps identified in the competitive analysis.",
                        "llm": forge_project["forgeData"]["selectedLLM"]
                    }
                ]
            }
        ]

        return steps

    def transform_prd_generation(self, forge_project: dict) -> list:
        """
        Stage 2: PRD Generation → Development Requirements & User Stories

        Mapping Rules:
        - prdGeneration.sections.executiveSummary → Project overview comment
        - prdGeneration.sections.problemStatement → Detailed requirements documentation
        - prdGeneration.sections.targetUsers → User acceptance criteria
        - prdGeneration.sections.featureSpecifications → Individual feature implementation tasks
        - prdGeneration.sections.successMetrics → Testing and validation checkpoints
        """
        prd_data = forge_project["forgeData"]["prdGeneration"]

        steps = [
            {
                "id": "requirements_documentation",
                "type": "documentation",
                "title": "Project Requirements & Specifications",
                "description": f"# Executive Summary\n{prd_data['sections']['executiveSummary']['content']}\n\n# Detailed Problem Statement\n{prd_data['sections']['problemStatement']['content']}\n\n# Target Users\n{prd_data['sections']['targetUsers']['content']}",
                "requirements_quality_score": prd_data["overallQualityScore"]
            }
        ]

        # Generate feature implementation tasks from specifications
        if prd_data["sections"]["featureSpecifications"]["content"]:
            steps.append({
                "id": "feature_implementation",
                "type": "development",
                "title": "Core Feature Implementation",
                "description": f"Implement features based on specifications: {prd_data['sections']['featureSpecifications']['content']}",
                "prompts": [
                    {
                        "content": f"Implement these feature specifications step by step: {prd_data['sections']['featureSpecifications']['content']}. Ensure each feature meets the defined acceptance criteria.",
                        "llm": forge_project["forgeData"]["selectedLLM"]
                    }
                ]
            })

        # Generate validation tasks from success metrics
        if prd_data["sections"]["successMetrics"]["content"]:
            steps.append({
                "id": "success_validation",
                "type": "testing",
                "title": "Success Metrics Validation",
                "description": f"Implement validation for success metrics: {prd_data['sections']['successMetrics']['content']}",
                "validation_criteria": prd_data["sections"]["successMetrics"]["content"]
            })

        return steps

    def transform_ux_requirements(self, forge_project: dict) -> list:
        """
        Stage 3: UX Requirements → User Interface Implementation

        Mapping Rules:
        - userJourneys → User flow implementation tasks
        - wireframes → UI component development tasks
        - designSystem → Styling and theming setup
        """
        ux_data = forge_project["forgeData"]["uxRequirements"]

        steps = []

        # Transform user journeys into implementation tasks
        for journey in ux_data.get("userJourneys", []):
            steps.append({
                "id": f"user_journey_{journey['id']}",
                "type": "ui_development",
                "title": f"Implement User Journey: {journey['name']}",
                "description": f"Implement user journey with steps: {', '.join(journey['steps'])}",
                "touchpoints": journey["touchpoints"],
                "pain_points_addressed": journey["painPoints"],
                "prompts": [
                    {
                        "content": f"Create user interface flow for: {journey['name']}. Implement these steps: {', '.join(journey['steps'])}. Address these pain points: {', '.join(journey['painPoints'])}",
                        "llm": forge_project["forgeData"]["selectedLLM"]
                    }
                ]
            })

        # Transform wireframes into component tasks
        for wireframe in ux_data.get("wireframes", []):
            steps.append({
                "id": f"component_{wireframe['id']}",
                "type": "component_development",
                "title": f"Build Component: {wireframe['screenName']}",
                "description": wireframe["description"],
                "interactions": wireframe["interactions"],
                "prompts": [
                    {
                        "content": f"Implement UI component for {wireframe['screenName']}: {wireframe['description']}. Include these interactions: {', '.join(wireframe['interactions'])}",
                        "llm": forge_project["forgeData"]["selectedLLM"]
                    }
                ]
            })

        # Add design system implementation if specified
        if ux_data.get("designSystem"):
            steps.append({
                "id": "design_system_implementation",
                "type": "styling",
                "title": "Design System Implementation",
                "description": f"Implement design system with color palette: {ux_data['designSystem']['colorPalette']}, typography: {ux_data['designSystem']['typography']}, components: {ux_data['designSystem']['componentLibrary']}",
                "design_tokens": ux_data["designSystem"]
            })

        return steps

    def apply_ux_compensation(self, forge_project: dict) -> list:
        """
        Stage 3 Skipped: Apply selected compensation strategy

        Mapping Rules:
        - skipDecision.reason → Context comment explaining skip
        - skipDecision.compensationApplied → Specific compensation implementation
        """
        ux_data = forge_project["forgeData"]["uxRequirements"]
        compensation = ux_data["skipDecision"]["compensationApplied"]

        compensation_steps = {
            "comprehensive_ux_prompts": [
                {
                    "id": "comprehensive_ux_guidance",
                    "type": "documentation",
                    "title": "Comprehensive UX Implementation Guide",
                    "description": f"UX stage skipped due to: {ux_data['skipDecision']['reason']}. Quality impact: {ux_data['skipDecision']['qualityImpact']}%",
                    "prompts": [
                        {
                            "content": "When implementing user interfaces, ensure: 1) Intuitive navigation patterns, 2) Responsive design across devices, 3) Accessible interactions following WCAG guidelines, 4) Consistent visual hierarchy, 5) Clear error messaging and validation feedback",
                            "llm": forge_project["forgeData"]["selectedLLM"]
                        }
                    ]
                }
            ],
            "basic_ux_prompts": [
                {
                    "id": "basic_ux_guidance",
                    "type": "documentation",
                    "title": "Essential UX Implementation Notes",
                    "description": f"Basic UX guidance applied. Quality impact: {ux_data['skipDecision']['qualityImpact']}%",
                    "prompts": [
                        {
                            "content": "Include essential UX elements: clear navigation, responsive layout, basic error handling, and intuitive user interactions",
                            "llm": forge_project["forgeData"]["selectedLLM"]
                        }
                    ]
                }
            ],
            "ux_research_tasks": [
                {
                    "id": "ux_research_tasks",
                    "type": "research",
                    "title": "UX Research Tasks for External Team",
                    "description": "Generate actionable UX research tasks for external UX team",
                    "tasks": [
                        "Conduct user interviews for target audience validation",
                        "Create wireframes for key user journeys",
                        "Design responsive layouts for identified screen sizes",
                        "Validate accessibility requirements and compliance"
                    ]
                }
            ],
            "no_compensation": []
        }

        return compensation_steps.get(compensation, [])

    def transform_technical_analysis(self, forge_project: dict) -> list:
        """
        Stage 4: Technical Analysis → Architecture & Stack Implementation

        Mapping Rules:
        - recommendedStack → Environment setup and dependency installation tasks
        - architectureDecisions → Implementation guidance comments
        - multiLLMAnalysis → Quality checkpoints from different perspectives
        """
        tech_data = forge_project["forgeData"]["technicalAnalysis"]

        steps = [
            {
                "id": "environment_setup",
                "type": "setup",
                "title": "Development Environment Setup",
                "description": f"Set up development environment with recommended stack",
                "stack": tech_data["recommendedStack"],
                "prompts": [
                    {
                        "content": f"Set up development environment with: Frontend: {tech_data['recommendedStack']['frontend']}, Backend: {tech_data['recommendedStack']['backend']}, Database: {tech_data['recommendedStack']['database']}, Deployment: {tech_data['recommendedStack']['deployment']}",
                        "llm": forge_project["forgeData"]["selectedLLM"]
                    }
                ]
            }
        ]

        # Add architecture decision implementation steps
        for decision in tech_data.get("architectureDecisions", []):
            steps.append({
                "id": f"architecture_{decision['decision'].lower().replace(' ', '_')}",
                "type": "architecture",
                "title": f"Implement: {decision['decision']}",
                "description": f"Rationale: {decision['rationale']}",
                "alternatives_considered": decision["alternatives"],
                "prompts": [
                    {
                        "content": f"Implement architectural decision: {decision['decision']}. Rationale: {decision['rationale']}. Ensure implementation follows this guidance throughout development.",
                        "llm": forge_project["forgeData"]["selectedLLM"]
                    }
                ]
            })

        # Add multi-LLM perspective checkpoints
        if tech_data.get("multiLLMAnalysis"):
            steps.append({
                "id": "multi_perspective_validation",
                "type": "validation",
                "title": "Multi-Perspective Technical Validation",
                "description": "Validation checkpoints from comprehensive technical analysis",
                "gpt4_perspective": tech_data["multiLLMAnalysis"].get("gpt4Analysis", {}),
                "claude_perspective": tech_data["multiLLMAnalysis"].get("claudeAnalysis", {}),
                "gemini_perspective": tech_data["multiLLMAnalysis"].get("geminiAnalysis", {}),
                "validation_checklist": [
                    "Business impact aligns with user needs (GPT-4 perspective)",
                    "Technical implementation is feasible and scalable (Claude perspective)",
                    "Solution has competitive advantages and innovation opportunities (Gemini perspective)"
                ]
            })

        return steps

    def generate_integration_steps(self, forge_project: dict) -> list:
        """
        Final Steps: Integration, Testing, and Deployment

        Generates final integration steps based on all previous stages
        """
        steps = [
            {
                "id": "integration_testing",
                "type": "testing",
                "title": "System Integration & Testing",
                "description": "Comprehensive testing of all implemented features",
                "quality_gate": forge_project["forgeData"]["qualityAssurance"]["overallQualityScore"],
                "prompts": [
                    {
                        "content": f"Conduct comprehensive testing ensuring: 1) All features from PRD are functional, 2) User journeys work end-to-end, 3) Technical architecture performs as expected, 4) Quality standards meet minimum threshold of {forge_project['forgeData']['qualityAssurance']['qualityGates']['minimumScore']}%",
                        "llm": forge_project["forgeData"]["selectedLLM"]
                    }
                ]
            },
            {
                "id": "deployment_preparation",
                "type": "deployment",
                "title": "Production Deployment",
                "description": "Deploy to production environment with monitoring",
                "cost_tracking": forge_project["forgeData"]["costTracking"],
                "prompts": [
                    {
                        "content": f"Deploy application using {forge_project['forgeData']['technicalAnalysis']['recommendedStack']['deployment']} with proper monitoring, logging, and backup procedures. Ensure scalability for target audience identified in requirements.",
                        "llm": forge_project["forgeData"]["selectedLLM"]
                    }
                ]
            }
        ]

        return steps

# API Integration for Transformation
async def generate_implementation_playbook(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/forge/projects/{project_id}/playbook/generate

    Transforms completed Forge project into executable Playbook using defined mapping rules
    """
    project_id = req.route_params.get('project_id')
    forge_project = await get_forge_project(project_id)

    transformer = ForgeToPlaybookTransformer()
    playbook = transformer.transform_forge_to_playbook(forge_project)

    # Store as executable Playbook in Sutra system
    playbook_id = await create_playbook(playbook)

    return func.HttpResponse(
        json.dumps({
            "playbook_id": playbook_id,
            "transformation_summary": {
                "stages_transformed": len([stage for stage in forge_project["forgeData"] if forge_project["forgeData"][stage].get("status") == "completed"]),
                "total_steps_generated": len(playbook["steps"]),
                "quality_score": forge_project["forgeData"]["qualityAssurance"]["overallQualityScore"]
            }
        }),
        status_code=200
    )
```
