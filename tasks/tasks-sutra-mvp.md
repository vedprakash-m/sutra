# Task List: Sutra AI Operations Platform MVP

## Project Overview

Building Sutra, an AI Operations Platform that enables systematic prompt engineering, multi-LLM opt- [ ] 2.5 Create CI/CD pipelines for persistent and compute resource groups
- [ ] 2.6 Do- [ ] 12.4 Document manual procedures for cost-optimized resource lifecycle management
- [ ] 12.5 Complete admin documentation for resource group management
- [ ] 12.6 Create operational runbooks for manual cost optimization proceduresent manual operations procedures for cost-saving resource managementization, and AI workflow orchestration. This task list covers the MVP (Phase 1) implementation using Azure serverless architecture.

**Key MVP Features:**
- Intelligent Prompt Engineering & Multi-LLM Optimization
- Prompt Management & Team Collaboration  
- Linear AI Workflow Orchestration (Playbooks)
- Core Integrations & User Experience

## Relevant Files

### Frontend (React + TypeScript)
- `src/App.tsx` - Main application component with routing and layout
- `src/App.test.tsx` - Unit tests for main app component
- `src/components/layout/NavBar.tsx` - Navigation bar component
- `src/components/layout/NavBar.test.tsx` - Unit tests for navigation
- `src/components/prompt/PromptBuilder.tsx` - Core prompt creation interface
- `src/components/prompt/PromptBuilder.test.tsx` - Unit tests for prompt builder
- `src/components/prompt/PromptCoach.tsx` - AI-powered prompt suggestions widget
- `src/components/prompt/PromptCoach.test.tsx` - Unit tests for prompt coach
- `src/components/prompt/LLMOutputPanel.tsx` - Multi-LLM output comparison panel
- `src/components/prompt/LLMOutputPanel.test.tsx` - Unit tests for output panel
- `src/components/collections/CollectionsPage.tsx` - Prompt collections management
- `src/components/collections/CollectionsPage.test.tsx` - Unit tests for collections
- `src/components/collections/VersionHistory.tsx` - Prompt version history modal
- `src/components/collections/VersionHistory.test.tsx` - Unit tests for version history
- `src/components/playbooks/PlaybookBuilder.tsx` - Linear workflow creation interface
- `src/components/playbooks/PlaybookBuilder.test.tsx` - Unit tests for playbook builder
- `src/components/playbooks/PlaybookRunner.tsx` - Playbook execution interface
- `src/components/playbooks/PlaybookRunner.test.tsx` - Unit tests for playbook runner
- `src/components/integrations/IntegrationsPage.tsx` - LLM API key management
- `src/components/integrations/IntegrationsPage.test.tsx` - Unit tests for integrations
- `src/components/admin/AdminPanel.tsx` - Admin dashboard for system configuration
- `src/components/admin/AdminPanel.test.tsx` - Unit tests for admin panel
- `src/components/admin/LLMSettings.tsx` - Admin LLM configuration and budgets
- `src/components/admin/LLMSettings.test.tsx` - Unit tests for LLM settings
- `src/components/admin/UsageDashboard.tsx` - Admin usage monitoring and alerts
- `src/components/admin/UsageDashboard.test.tsx` - Unit tests for usage dashboard
- `src/components/dashboard/Dashboard.tsx` - Main dashboard with quick actions
- `src/components/dashboard/Dashboard.test.tsx` - Unit tests for dashboard
- `src/components/auth/AuthProvider.tsx` - Authentication context provider
- `src/components/auth/AuthProvider.test.tsx` - Unit tests for auth provider
- `src/hooks/useApi.ts` - Custom hook for API calls
- `src/hooks/useApi.test.ts` - Unit tests for API hook
- `src/hooks/useLLM.ts` - Custom hook for LLM integrations
- `src/hooks/useLLM.test.ts` - Unit tests for LLM hook
- `src/services/api.ts` - API service layer for backend communication
- `src/services/api.test.ts` - Unit tests for API service
- `src/services/llm.ts` - LLM provider integration service
- `src/services/llm.test.ts` - Unit tests for LLM service
- `src/types/index.ts` - TypeScript type definitions
- `src/utils/validation.ts` - Input validation utilities
- `src/utils/validation.test.ts` - Unit tests for validation utilities
- `src/styles/globals.css` - Global CSS styles

### Backend (Azure Functions + Python)
- `api/requirements.txt` - Python dependencies
- `api/host.json` - Azure Functions host configuration
- `api/local.settings.json` - Local development settings (gitignored)
- `api/shared/__init__.py` - Shared utilities and models
- `api/shared/auth.py` - Authentication and authorization utilities
- `api/shared/auth_test.py` - Unit tests for auth utilities
- `api/shared/models.py` - Pydantic data models
- `api/shared/models_test.py` - Unit tests for data models
- `api/shared/llm_client.py` - LLM provider client implementations
- `api/shared/llm_client_test.py` - Unit tests for LLM clients
- `api/shared/database.py` - Cosmos DB connection and utilities
- `api/shared/database_test.py` - Unit tests for database utilities
- `api/prompts/__init__.py` - Prompts API function
- `api/prompts/function.json` - Azure Function configuration for prompts
- `api/prompts/prompts_test.py` - Unit tests for prompts API
- `api/collections/__init__.py` - Collections API function
- `api/collections/function.json` - Azure Function configuration for collections
- `api/collections/collections_test.py` - Unit tests for collections API
- `api/playbooks/__init__.py` - Playbooks API function
- `api/playbooks/function.json` - Azure Function configuration for playbooks
- `api/playbooks/playbooks_test.py` - Unit tests for playbooks API
- `api/integrations/__init__.py` - Integrations API function
- `api/integrations/function.json` - Azure Function configuration for integrations
- `api/shared/budget.py` - Budget tracking and enforcement utilities
- `api/shared/budget_test.py` - Unit tests for budget utilities
- `api/admin/__init__.py` - Admin API functions
- `api/admin/function.json` - Azure Function configuration for admin
- `api/admin/admin_test.py` - Unit tests for admin API
- `api/usage/__init__.py` - Usage tracking and monitoring API
- `api/usage/function.json` - Azure Function configuration for usage
- `api/usage/usage_test.py` - Unit tests for usage API

- `api/llm_execute/__init__.py` - LLM execution function
- `api/llm_execute/function.json` - Azure Function configuration for LLM execution
- `api/llm_execute/llm_execute_test.py` - Unit tests for LLM execution

### Infrastructure & Configuration
- `infrastructure/persistent.bicep` - Persistent infrastructure template (sutra-db-rg)
- `infrastructure/compute.bicep` - Compute infrastructure template (sutra-rg)
- `infrastructure/modules/cosmosdb.bicep` - Cosmos DB module (sutra-db)
- `infrastructure/modules/keyvault.bicep` - Key Vault module (sutra-kv)
- `infrastructure/modules/storage.bicep` - Storage Account module (sutrasa99)
- `infrastructure/modules/staticwebapp.bicep` - Static Web App module (sutra-web)
- `infrastructure/modules/functions.bicep` - Azure Functions module (sutra-api)
- `infrastructure/modules/frontdoor.bicep` - Front Door module (sutra-fd)
- `infrastructure/modules/appinsights.bicep` - Application Insights module (sutra-ai)
- `infrastructure/parameters.json` - Infrastructure parameters (static naming)
- `.github/workflows/deploy-persistent.yml` - CI/CD pipeline for persistent resources
- `.github/workflows/deploy-compute.yml` - CI/CD pipeline for compute resources
- `docs/OPERATIONS.md` - Manual operations guide for resource management
- `docker-compose.yml` - Local development environment with services
- `docker-compose.override.yml` - Local development overrides
- `local-dev/cosmos-emulator.yml` - Local Cosmos DB emulator setup
- `local-dev/setup.sh` - Local environment setup script
- `package.json` - Frontend dependencies and scripts
- `tailwind.config.js` - Tailwind CSS configuration
- `vite.config.ts` - Vite configuration for development
- `tsconfig.json` - TypeScript configuration
- `jest.config.js` - Jest testing configuration
- `pytest.ini` - Python testing configuration
- `playwright.config.ts` - Playwright E2E testing configuration
- `tests/e2e/` - End-to-end test scenarios for local validation

### Documentation
- `README.md` - Project setup and development guide
- `docs/API.md` - API documentation
- `docs/DEPLOYMENT.md` - Deployment guide
- `docs/ARCHITECTURE.md` - System architecture documentation

### Notes

- Frontend uses React with TypeScript, Tailwind CSS, and Headless UI components
- Backend uses Azure Functions with Python 3.12 runtime
- **Two-tier Resource Group Architecture:**
  - **sutra-db-rg**: Persistent resources (sutra-db, sutra-kv, sutrasa99)
  - **sutra-rg**: Compute resources (sutra-api, sutra-web, sutra-fd, sutra-ai)
- **Static Resource Naming** for idempotent deployments:
  - Database: `sutra-db` (Cosmos DB)
  - Key Vault: `sutra-kv` 
  - Storage: `sutrasa99` (globally unique)
  - Functions: `sutra-api`
  - Static Web App: `sutra-web`
  - Front Door: `sutra-fd` (with custom domain support)
  - App Insights: `sutra-ai`
- Authentication uses Azure AD B2C with admin role support
- **Cost Optimization**: Manual deletion of sutra-rg during extended downtime
- **Local development** uses Docker Compose with Cosmos DB emulator and local Functions runtime
- **Extensive E2E testing** with Playwright runs locally before any deployment
- Unit tests use Jest for frontend and pytest for backend
- Use `npm run dev:local` for full local development environment
- Use `npm run test:e2e` for comprehensive end-to-end validation
- Admin users can configure LLM budgets, priorities, and usage alerts

## Tasks

- [x] 1.0 Project Foundation & Local Development Setup
  - [x] 1.1 Initialize project repository with proper structure
  - [x] 1.2 Set up comprehensive local development environment with Docker Compose
  - [x] 1.3 Configure Cosmos DB emulator and Azure Functions Core Tools locally
  - [x] 1.4 Set up Playwright for extensive E2E testing locally
  - [x] 1.5 Create local validation scripts and pre-deployment checks
  - [x] 1.6 Design two-tier Azure infrastructure with static resource naming (persistent vs compute)

- [ ] 2.0 Infrastructure & Authentication Setup
  - [ ] 2.1 Create persistent infrastructure (sutra-db-rg): sutra-db, sutra-kv, sutrastore
  - [ ] 2.2 Create compute infrastructure (sutra-rg): sutra-api, sutra-web, sutra-fd, sutra-ai
  - [ ] 2.3 Configure Azure AD B2C with admin role support
  - [ ] 2.4 Set up admin authentication and role-based access control
  - [ ] 2.5 Create CI/CD pipelines for persistent and compute resource groups
  - [ ] 2.6 Implement cleanup pipeline for cost-saving compute resource deletion

- [x] 2.0 Backend API Foundation
  - [x] 2.1 Set up Azure Functions project structure
  - [x] 2.2 Implement shared utilities (auth, models, database)
  - [x] 2.3 Create Cosmos DB connection and data access layer
  - [x] 2.4 Implement LLM provider client abstractions
  - [x] 2.5 Set up input validation and error handling
  - [x] 2.6 Create unit test framework and initial tests

- [x] 3.0 Core Prompt Management API
  - [x] 3.1 Implement Prompts CRUD API endpoints
  - [x] 3.2 Implement Collections CRUD API endpoints
  - [ ] 3.3 Add prompt versioning functionality
  - [ ] 3.4 Implement team collaboration and access control
  - [x] 3.5 Add search and filtering capabilities
  - [x] 3.6 Create comprehensive API tests

- [x] 4.0 Admin-Controlled LLM Integration & Budget Management
  - [x] 4.1 Implement admin-controlled OpenAI GPT integration with budget limits
  - [x] 4.2 Implement admin-controlled Google Gemini integration with priority settings
  - [x] 4.3 Implement admin-controlled Anthropic Claude integration with usage monitoring
  - [x] 4.4 Create admin interface for LLM configuration and API key management
  - [x] 4.5 Implement budget tracking, alerts, and automatic enforcement
  - [x] 4.6 Add admin dashboard for usage monitoring and cost optimization

- [x] 5.0 Playbooks (Linear Workflows) API
  - [x] 5.1 Implement Playbooks CRUD API endpoints
  - [x] 5.2 Create workflow execution engine
  - [x] 5.3 Implement step-by-step execution with pause/resume
  - [x] 5.4 Add manual review step functionality
  - [x] 5.5 Implement output parsing and variable passing
  - [x] 5.6 Create execution logging and audit trail

- [x] 6.0 Frontend Foundation & Authentication
  - [x] 6.1 Set up React project with TypeScript and Tailwind
  - [x] 6.2 Implement authentication flow with Azure AD B2C (dev-mode complete)
  - [x] 6.3 Create main application layout and navigation
  - [x] 6.4 Set up API service layer and error handling
  - [x] 6.5 Implement responsive design system
  - [x] 6.6 Create frontend testing framework (Playwright browsers installed, tests ready)

- [x] 7.0 Prompt Builder Interface
  - [x] 7.1 Create guided prompt creation form
  - [x] 7.2 Implement dynamic contextual details fields
  - [x] 7.3 Build editable prompt text area with variable support
  - [x] 7.4 Create PromptCoach suggestions widget (intelligent suggestions working)
  - [x] 7.5 Implement LLM selection interface
  - [x] 7.6 Build multi-LLM output comparison panel

- [x] 8.0 Collections Management Interface
  - [x] 8.1 Create collections sidebar navigation (integrated in main nav)
  - [x] 8.2 Implement prompt list with search and filters
  - [x] 8.3 Build collection creation and management flows
  - [x] 8.4 Create version history modal with diff view (comprehensive version comparison)
  - [x] 8.5 Implement import functionality for existing prompts (ChatGPT, text files, manual input)
  - [ ] 8.6 Add team collaboration features

- [x] 9.0 Playbook Builder & Runner Interface
  - [x] 9.1 Create drag-and-drop workflow canvas (step-based interface)
  - [x] 9.2 Implement step palette and configuration
  - [x] 9.3 Build linear workflow connection system
  - [x] 9.4 Create playbook execution interface (comprehensive PlaybookRunner with real-time status)
  - [x] 9.5 Implement real-time execution status and logging (execution timeline and logs)
  - [x] 9.6 Add manual review step interaction (approve/reject workflow)

- [x] 10.0 Admin Panel & System Management
  - [x] 10.1 Create comprehensive admin panel for system configuration
  - [x] 10.2 Implement LLM provider settings with budget and priority controls
  - [x] 10.3 Build usage dashboard with real-time monitoring and alerts
  - [ ] 10.4 Create user management interface for admin oversight (placeholder)
  - [x] 10.5 Implement system health monitoring and maintenance tools
  - [ ] 10.6 Add admin settings for global system configurations

- [ ] 11.0 Local E2E Validation & Quality Assurance
  - [ ] 11.1 Complete comprehensive Playwright E2E test suite for all user journeys
  - [ ] 11.2 Implement local validation pipeline that catches issues before deployment
  - [ ] 11.3 Create performance benchmarks and load testing scenarios locally
  - [ ] 11.4 Set up automated accessibility and security scanning
  - [ ] 11.5 Implement comprehensive error simulation and recovery testing
  - [ ] 11.6 Validate admin workflows and budget enforcement scenarios

- [ ] 12.0 Two-Tier Deployment & Cost Management
  - [ ] 12.1 Deploy persistent infrastructure (sutra-db-rg) with static resource names
  - [ ] 12.2 Deploy compute infrastructure (sutra-rg) with proper resource linking
  - [ ] 12.3 Configure production monitoring, alerts, and backup procedures
  - [ ] 12.4 Set up automated compute resource cleanup for cost savings
  - [ ] 12.5 Complete admin documentation for resource group management
  - [ ] 12.6 Create operational runbooks for cost-optimized resource lifecycle

## Implementation Strategy

### Phase 1: Local Development & Two-Tier Infrastructure (Tasks 1-2)
Set up comprehensive local development environment and design two-tier Azure infrastructure with static naming. Create persistent resource group (sutra-db-rg) and compute resource group (sutra-rg) with proper separation.

### Phase 2: Backend Core with Admin Controls (Tasks 3-5)  
Build complete backend API with admin-controlled LLM integrations, budget management, and playbook execution. Focus on cost control and usage monitoring from the start.

### Phase 3: Frontend Core with Admin Interface (Tasks 6-8)
Develop main user interfaces for prompt creation and management, plus comprehensive admin panel for system control and monitoring.

### Phase 4: Advanced Features & Admin Dashboard (Tasks 9-10)
Complete playbook workflows and admin management tools. Implement real-time usage monitoring and budget enforcement.

### Phase 5: Two-Tier Deployment & Cost Optimization (Tasks 11-12)
Extensive local E2E validation followed by two-tier production deployment with automated cost management through compute resource lifecycle.

## Success Criteria

- **Cost Optimization**: Two-tier resource architecture enables deleting compute resources (sutra-rg) during extended downtime while preserving all data in persistent resources (sutra-db-rg)
- **Idempotent Deployment**: Static resource naming ensures consistent, error-free CI/CD deployments
- **Rapid Development**: Comprehensive local validation with exact production mirroring
- **Admin Control**: Full administrative oversight of LLM providers, budgets, and resource lifecycle
- **Operational Simplicity**: Clear separation between persistent and compute resources with automated cleanup procedures

## Resource Architecture

### **Persistent Resource Group (sutra-db-rg)**
- `sutra-db` - Cosmos DB (retains all application data)
- `sutra-kv` - Key Vault (retains all secrets and API keys)
- `sutrasa99` - Storage Account (retains all files and backups)

### **Compute Resource Group (sutra-rg)**
- `sutra-api` - Azure Functions (can be deleted/recreated)
- `sutra-web` - Static Web App (can be deleted/recreated)
- `sutra-fd` - Front Door (can be deleted/recreated)
- `sutra-ai` - Application Insights (logs acceptable to lose during cleanup)

## Risk Mitigation

- **Cost Control**: Manual deletion of compute resources (sutra-rg) during downtime with zero data loss
- **Deployment Issues**: Static naming and idempotent infrastructure ensures consistent deployments
- **Data Persistence**: Critical data always preserved in sutra-db-rg regardless of compute resource state
- **Development Speed**: Local validation pipeline prevents costly cloud deployment iterations
- **Resource Management**: Clear manual procedures for cost-optimized resource lifecycle
