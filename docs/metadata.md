# Sutra AI Operations Platform - Project Metadata

## Project Overview

Sutra is a serverless AI operations platform built on Microsoft Azure, designed with a cost-optimized two-tier architecture that enables reliable operations with startup-friendly economics.

## Architecture

### Two-Tier Resource Architecture

**Persistent Tier (sutra-db-rg)** - Always Running, Critical Data:
- `sutra-db` - Cosmos DB (serverless, all application data)
- `sutra-kv` - Key Vault (secrets and API keys)
- `sutrasa99` - Storage Account (files and backups)

**Compute Tier (sutra-rg)** - Can Be Deleted for Cost Savings:
- `sutra-api` - Azure Functions (Python 3.12, serverless backend)
- `sutra-web` - Static Web App (React frontend)
- `sutra-fd` - Front Door (CDN, global routing, WAF)
- `sutra-ai` - Application Insights (monitoring and logs)

### Technology Stack

- **Frontend**: React with TypeScript, hosted on Azure Static Web Apps
- **Backend**: Azure Functions (Python 3.12) with serverless architecture
- **Database**: Azure Cosmos DB (NoSQL, serverless mode)
- **API Gateway**: Azure Front Door Standard with WAF protection
- **Authentication**: Azure Active Directory B2C
- **Storage**: Azure Blob Storage for files and backups
- **Monitoring**: Application Insights with Log Analytics
- **Infrastructure**: Bicep templates for Infrastructure as Code

### Data Model

The platform manages these core entities in Cosmos DB:
- **Prompts**: AI prompt templates with versioning
- **Collections**: Organized prompt groups
- **Playbooks**: Multi-step AI workflows
- **Usage**: Tracking and analytics data (30-day retention)
- **Config**: Application configuration settings

## Cost Optimization Strategy

### Core Principle
The architecture enables **complete compute resource deletion** during downtime (weekends, holidays) while preserving all data in the persistent tier. This can reduce costs to near-zero during extended periods.

### Resource Management
- **Persistent tier costs**: ~$10-30/month (Cosmos DB serverless, Key Vault, Storage)
- **Compute tier costs**: ~$50-200/month (Functions, Static Web App, Front Door)
- **Weekend shutdown**: Delete entire compute tier, save 70-80% on monthly costs
- **Recovery time**: ~10 minutes to restore full functionality

### Automated Operations
- All resources use static, globally consistent naming for idempotent deployments
- Infrastructure templates support complete teardown and recreation
- Connection strings and secrets automatically reconnect on restoration

## Development & Testing

### Local Development
- Docker Compose environment with Cosmos DB emulator
- Azurite for local storage emulation
- Full backend/frontend development stack

### Testing Strategy
- **Unit Tests**: Jest (frontend), pytest (backend)
- **E2E Tests**: Playwright with multi-browser support
- **CI/CD Tests**: Minimal dependency validation for fast builds

### Dependencies
- **Frontend**: React, TypeScript, Tailwind CSS, Vite
- **Backend**: Azure Functions, Cosmos SDK, httpx, pydantic
- **Infrastructure**: Bicep, Azure CLI

## Security & Compliance

### Authentication & Authorization
- Azure AD B2C for user authentication
- JWT token validation on all API endpoints
- Role-based access control (Agent, Contributor, PromptManager, Admin)
- System-assigned managed identity for Azure service access

### Data Protection
- All data encrypted at rest (Cosmos DB, Storage)
- HTTPS/TLS encryption in transit
- Secrets stored in Azure Key Vault
- No hardcoded credentials in codebase

### Network Security
- Azure Front Door WAF protection
- CORS configured for frontend domain only
- Public blob access disabled on storage accounts
- HTTPS-only enforcement across all services

## Deployment & Operations

### Infrastructure Deployment
Two-phase deployment process:
1. **Persistent Infrastructure**: Deploy `persistent.bicep` to `sutra-db-rg`
2. **Compute Infrastructure**: Deploy `compute.bicep` to `sutra-rg`

### Resource Naming Convention
All resources use static names for consistency:
- Database tier: `sutra-db`, `sutra-kv`, `sutrasa99`
- Compute tier: `sutra-api`, `sutra-web`, `sutra-fd`, `sutra-ai`

### Operational Procedures

**Daily Operations**:
- Health checks via Azure CLI commands
- Cost monitoring and usage analysis
- Automated startup/shutdown procedures

**Cost Management**:
- Weekend compute tier deletion for maximum savings
- Holiday extended shutdown procedures
- Automated recovery with data integrity validation

**Monitoring**:
- Application Insights telemetry with 30-day retention
- Structured logging with correlation IDs
- Performance monitoring and alerting

## Validation Scripts

The project includes comprehensive validation tooling:
- `scripts/validate-ci-cd.sh` - CI/CD pipeline validation
- `scripts/validate-e2e.sh` - End-to-end testing validation
- `scripts/test-backend-deps.sh` - Backend dependency validation
- `local-dev/health-check.sh` - Local development health checks

## File Structure

### Core Infrastructure
- `infrastructure/persistent.bicep` - Persistent tier template
- `infrastructure/compute.bicep` - Compute tier template
- `infrastructure/parameters.*.json` - Deployment parameters

### Application Code
- `src/` - React frontend application
- `api/` - Azure Functions backend
- `tests/e2e/` - Playwright end-to-end tests

### Configuration
- `docker-compose.yml` - Local development environment
- `playwright.config.ts` - E2E testing configuration
- `package.json` - Frontend dependencies and scripts
- `api/requirements.txt` - Backend Python dependencies

# Sutra AI Operations Platform - Project Metadata

## Project Overview

Sutra is a serverless AI operations platform built on Microsoft Azure, designed with a cost-optimized two-tier architecture that enables reliable operations with startup-friendly economics. The platform provides systematic prompt engineering, multi-LLM orchestration, and workflow automation capabilities.

## Architecture

### Two-Tier Resource Architecture

**Persistent Tier (sutra-db-rg)** - Always Running, Critical Data:
- `sutra-db` - Cosmos DB (serverless, all application data)
- `sutra-kv` - Key Vault (secrets and API keys)
- `sutrasa99` - Storage Account (files and backups)

**Compute Tier (sutra-rg)** - Can Be Deleted for Cost Savings:
- `sutra-api` - Azure Functions (Python 3.12, serverless backend)
- `sutra-web` - Static Web App (React frontend)
- `sutra-fd` - Front Door (CDN, global routing, WAF)
- `sutra-ai` - Application Insights (monitoring and logs)

### Technology Stack

**Frontend (React + TypeScript)**:
- **Framework**: React 18 with TypeScript, Vite build system
- **Styling**: Tailwind CSS with responsive design
- **State Management**: React Query for server state, Zustand for client state
- **Routing**: React Router DOM with protected routes
- **Components**: Modular architecture with reusable UI components
- **Authentication**: Context-based auth with development mode simulation

**Backend (Azure Functions + Python)**:
- **Runtime**: Python 3.12 on Azure Functions v4
- **Framework**: Azure Functions with HTTP triggers
- **Architecture**: Serverless microservices with shared utilities
- **Authentication**: JWT validation with Azure AD B2C integration ready
- **Database**: Cosmos DB SDK with connection pooling
- **Error Handling**: Comprehensive error handling with request correlation

**Data Layer**:
- **Database**: Azure Cosmos DB (NoSQL, serverless mode)
- **Containers**: `prompts`, `collections`, `playbooks`, `usage`, `config`
- **Partitioning**: User-based partitioning for performance
- **Indexing**: Optimized for query patterns
- **Backup**: Automated with point-in-time restore

### Data Model

The platform manages these core entities in Cosmos DB:

**Core Models** (defined in `api/shared/models.py`):
- **User**: Authentication and role management (user, admin roles)
- **PromptTemplate**: AI prompt templates with versioning and variables
- **Collection**: Organized prompt groups with type-based access control
- **Playbook**: Multi-step AI workflows with conditional logic
- **PlaybookExecution**: Execution tracking and results
- **LLMIntegration**: Multi-provider LLM configurations
- **Usage**: Analytics and cost tracking (30-day retention)

**Enums**:
- `UserRole`: USER, ADMIN
- `PromptStatus`: DRAFT, ACTIVE, ARCHIVED  
- `PlaybookStatus`: DRAFT, RUNNING, PAUSED, COMPLETED, FAILED
- `LLMProvider`: OPENAI, ANTHROPIC, GOOGLE

## Frontend Architecture

### Component Structure
```
src/components/
├── auth/                   # Authentication system
│   ├── AuthProvider.tsx    # Context provider with localStorage persistence
│   └── LoginPage.tsx       # Development mode login with role selection
├── dashboard/              # Main dashboard views
│   ├── Dashboard.tsx       # Primary dashboard with quick actions
│   └── Dashboard-new.tsx   # Alternative dashboard layout
├── admin/                  # Administrative interfaces
│   └── AdminPanel.tsx      # System management with tabbed interface
├── collections/            # Collection management
│   ├── CollectionsPage.tsx # Collection CRUD operations
│   ├── VersionHistory.tsx  # Prompt version management
│   └── ImportModal.tsx     # Bulk import functionality
├── prompt/                 # Prompt engineering tools
│   ├── PromptBuilder.tsx   # Multi-LLM prompt testing interface
│   └── PromptCoach.tsx     # AI-powered prompt suggestions
├── playbooks/             # Workflow automation
│   ├── PlaybookBuilder.tsx # Visual workflow editor
│   └── PlaybookRunner.tsx  # Execution interface
├── layout/                # Shared layout components
│   └── NavBar.tsx         # Main navigation with role-based access
└── shared/               # Reusable UI components
```

### Key Frontend Features
- **Responsive Design**: Mobile-first with Tailwind CSS
- **Real-time Updates**: React Query for efficient data fetching
- **Role-based UI**: Dynamic navigation and features based on user roles
- **Development Mode**: Mock authentication for local development
- **Error Boundaries**: Comprehensive error handling and user feedback

### API Service Layer (`src/services/api.ts`)
```typescript
// Centralized API configuration
const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:7071/api'

// Type-safe API interfaces
interface Collection { id, name, description, type, owner_id, ... }
interface Prompt { id, title, content, collection_id, version, ... }
interface Playbook { id, name, steps, creator_id, visibility, ... }

// Organized API endpoints
collectionsApi: { list, get, create, update, delete }
playbooksApi: { list, get, create, update, delete, execute }
integrationsApi: { listLLM, saveLLM, deleteLLM }
adminApi: { getLLMSettings, getSystemHealth, getUsageStats }
llmApi: { execute }
```

## Backend Architecture

### API Structure
```
api/
├── shared/                 # Common utilities and models
│   ├── models.py          # Pydantic models and enums
│   ├── database.py        # Cosmos DB manager with connection pooling
│   ├── auth.py           # JWT authentication and authorization
│   ├── error_handling.py # Centralized error handling
│   ├── validation.py     # Input validation and sanitization
│   ├── llm_client.py     # Multi-LLM provider abstraction
│   └── budget.py         # Cost tracking and budget enforcement
├── prompts/              # Prompt management API
├── collections_api/      # Collection CRUD operations
├── playbooks_api/        # Playbook workflow management
├── llm_execute_api/      # LLM execution engine
├── integrations_api/     # LLM provider integrations
└── admin_api/           # Administrative endpoints
```

### Key Backend Features
- **Authentication**: JWT-based with Azure AD B2C ready
- **Authorization**: Role-based access control with resource-level permissions
- **Error Handling**: Comprehensive with request correlation IDs
- **Validation**: Input sanitization and business logic validation
- **Database**: Connection pooling with automatic failover
- **Monitoring**: Structured logging with Application Insights integration

### Database Schema (Cosmos DB)

**Container: prompts**
```json
{
  "id": "uuid",
  "userId": "partition-key",
  "title": "string",
  "content": "string", 
  "variables": [{"name", "type", "required", "default"}],
  "status": "draft|active|archived",
  "version": "number",
  "parentId": "uuid|null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Container: collections**
```json
{
  "id": "uuid",
  "userId": "partition-key",
  "name": "string",
  "description": "string",
  "type": "private|shared_team|public_marketplace",
  "promptCount": "number",
  "tags": ["string"],
  "created_at": "datetime"
}
```

**Container: playbooks**
```json
{
  "id": "uuid", 
  "userId": "partition-key",
  "name": "string",
  "description": "string",
  "steps": [{"type": "prompt|review|variable", "promptId", "content", "order"}],
  "visibility": "private|shared",
  "created_at": "datetime"
}
```

## Cost Optimization Strategy

### Core Principle
The architecture enables **complete compute resource deletion** during downtime (weekends, holidays) while preserving all data in the persistent tier. This can reduce costs to near-zero during extended periods.

### Resource Management
- **Persistent tier costs**: ~$10-30/month (Cosmos DB serverless, Key Vault, Storage)
- **Compute tier costs**: ~$50-200/month (Functions, Static Web App, Front Door)
- **Weekend shutdown**: Delete entire compute tier, save 70-80% monthly costs
- **Recovery time**: ~10 minutes to restore full functionality

### Automated Operations
- All resources use static, globally consistent naming for idempotent deployments
- Infrastructure templates support complete teardown and recreation
- Connection strings and secrets automatically reconnect on restoration

## Development & Testing

### Local Development Environment
**Docker Compose Stack** (`docker-compose.yml`):
- **cosmos-emulator**: Local Cosmos DB with persistence
- **functions-api**: Azure Functions runtime
- **azurite**: Azure Storage emulator
- **frontend**: React development server

**Configuration**:
- Frontend proxy: `/api` → `http://localhost:7071`
- Backend environment: Development mode with mock authentication
- Database: Local emulator with test data isolation

### Testing Strategy

**End-to-End Testing** (Playwright):
- **Configuration**: Single worker mode for data isolation
- **Coverage**: Authentication, CRUD operations, navigation
- **Browsers**: Chromium, Firefox, WebKit
- **Helpers**: Reusable test utilities in `tests/e2e/helpers.ts`

**Unit Testing**:
- **Frontend**: Jest with React Testing Library
- **Backend**: pytest with async support
- **Coverage**: Component logic, API endpoints, utility functions

**Integration Testing**:
- **API Validation**: `scripts/test-backend-deps.sh`
- **Namespace Collision**: `scripts/test-namespace-collisions.sh`
- **CI/CD Validation**: `scripts/validate-ci-cd.sh`

### Dependencies

**Frontend Dependencies** (`package.json`):
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-router-dom": "^6.8.0", 
    "react-query": "^3.39.0",
    "axios": "^1.6.0",
    "zustand": "^4.4.0",
    "@headlessui/react": "^1.7.17",
    "@heroicons/react": "^2.0.18"
  },
  "devDependencies": {
    "@playwright/test": "^1.40.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.3.0"
  }
}
```

**Backend Dependencies** (`api/requirements.txt`):
```txt
azure-functions==1.18.0
azure-cosmos==4.5.1  
azure-identity==1.15.0
azure-keyvault-secrets==4.7.0
pydantic==2.5.2
httpx==0.25.2
pytest>=7.4.0
```

## Security & Compliance

### Authentication & Authorization
- **Development Mode**: Mock JWT tokens with role simulation
- **Production Ready**: Azure AD B2C integration prepared
- **Role-based Access**: Granular permissions (read, write, execute, manage)
- **Token Management**: Secure token storage and refresh handling

### Data Protection
- **Encryption**: All data encrypted at rest (Cosmos DB, Storage)
- **Transport**: HTTPS/TLS encryption in transit
- **Secrets**: Azure Key Vault for API keys and connection strings
- **Access Control**: System-assigned managed identity for Azure services

### Network Security
- **Azure Front Door**: WAF protection against common attacks
- **CORS**: Configured for frontend domain only
- **Storage**: Public blob access disabled
- **Functions**: HTTPS-only enforcement

## Deployment & Operations

### Infrastructure Deployment
Two-phase deployment process using Bicep IaC:

**Phase 1: Persistent Infrastructure** (`infrastructure/persistent.bicep`):
```bash
az deployment group create \
  --resource-group sutra-db-rg \
  --template-file infrastructure/persistent.bicep \
  --parameters @infrastructure/parameters.persistent.json
```

**Phase 2: Compute Infrastructure** (`infrastructure/compute.bicep`):
```bash  
az deployment group create \
  --resource-group sutra-rg \
  --template-file infrastructure/compute.bicep \
  --parameters @infrastructure/parameters.compute.json
```

### Resource Naming Convention
All resources use static names for consistency:
- **Database tier**: `sutra-db`, `sutra-kv`, `sutrasa99`
- **Compute tier**: `sutra-api`, `sutra-web`, `sutra-fd`, `sutra-ai`

### Operational Procedures

**Daily Operations**:
- Health checks via Azure CLI commands
- Cost monitoring and usage analysis
- Automated startup/shutdown procedures

**Cost Management**:
- Weekend compute tier deletion for maximum savings
- Holiday extended shutdown procedures
- Automated recovery with data integrity validation

**Monitoring**:
- Application Insights telemetry with 30-day retention
- Structured logging with correlation IDs
- Performance monitoring and alerting

## Common Development Patterns

### Frontend Patterns

**API Integration**:
```typescript
// Custom hook for API calls with loading states
const { data, loading, error, refetch } = useApi(
  () => collectionsApi.list({ search: searchTerm }),
  [searchTerm]
)

// Async action handling
const { loading, error, execute } = useAsyncAction()
await execute(() => collectionsApi.create(newCollection))
```

**Authentication Context**:
```typescript
const { user, isAuthenticated, isAdmin, login, logout } = useAuth()

// Role-based rendering
{isAdmin && (
  <AdminPanel />
)}

// Protected routes
<Route path="/admin" element={<AdminPanel />} />
```

### Backend Patterns

**API Endpoint Structure**:
```python
@handle_api_errors
async def main(req: func.HttpRequest) -> func.HttpResponse:
    request_id = extract_request_id(req)
    
    if req.method == 'GET':
        return await handle_get_operation(req, request_id)
    # ... other methods

@require_auth(resource="prompts", action="read")
async def handle_get_operation(req, request_id):
    user = await get_current_user(req)
    db_manager = get_database_manager()
    # ... operation logic
```

**Database Operations**:
```python
# Connection management
db_manager = get_database_manager()

# CRUD operations with validation
result = await db_manager.read_item(
    container_name="prompts",
    item_id=prompt_id,
    partition_key=user_id
)

await db_manager.upsert_item(
    container_name="prompts", 
    item=prompt_data
)
```

## Validation Scripts

The project includes comprehensive validation tooling:
- `scripts/validate-ci-cd.sh` - CI/CD pipeline validation  
- `scripts/validate-e2e.sh` - End-to-end testing validation
- `scripts/test-backend-deps.sh` - Backend dependency validation
- `scripts/test-namespace-collisions.sh` - Python namespace conflict detection
- `local-dev/health-check.sh` - Local development health checks

## File Structure

### Core Infrastructure
- `infrastructure/persistent.bicep` - Persistent tier template
- `infrastructure/compute.bicep` - Compute tier template
- `infrastructure/parameters.*.json` - Deployment parameters

### Application Code
- `src/` - React frontend application with modular components
- `api/` - Azure Functions backend with shared utilities
- `tests/e2e/` - Playwright end-to-end tests with helpers

### Configuration Files
- `docker-compose.yml` - Local development environment
- `playwright.config.ts` - E2E testing configuration (single worker mode)
- `vite.config.ts` - Frontend build configuration with API proxy
- `package.json` - Frontend dependencies and scripts
- `api/requirements.txt` - Backend Python dependencies
- `tailwind.config.js` - Styling configuration

### Development Workflow Commands
```bash
# Local development
npm run dev:local              # Start full Docker environment
npm run dev                    # Frontend only (requires backend running)

# Testing  
npm run test:e2e              # Full E2E test suite
npm run test:e2e:ui           # Interactive E2E testing
npm run backend:test-deps     # Backend dependency validation

# Validation
npm run ci:validate           # CI/CD validation
./scripts/validate-e2e.sh     # E2E environment validation
```

## Key Integration Points

### Frontend ↔ Backend API
- **Base URL**: Configurable via `VITE_API_URL` environment variable
- **Authentication**: JWT tokens in Authorization headers
- **Error Handling**: Centralized error boundaries with user feedback
- **Type Safety**: Shared TypeScript interfaces for API contracts

### Backend ↔ Azure Services  
- **Cosmos DB**: Connection string from Key Vault via managed identity
- **Storage**: Integrated for file uploads and large data
- **Application Insights**: Structured logging with correlation tracking
- **Key Vault**: Secure credential storage and retrieval

This architecture provides enterprise-grade reliability with startup-friendly cost optimization, enabling teams to scale operations efficiently while maintaining strict cost control.
