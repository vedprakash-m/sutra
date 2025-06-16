# Sutra - AI Prompt Management & Multi-LLM Optimization

> **Status: MVP Complete** 🚀  
> Full-stack AI prompt management platform with multi-LLM integration and workflow automation.

**Weaving your AI solutions.**

Sutra is a comprehensive AI Prompt Management & Multi-LLM Optimization platform that enables systematic prompt engineering, model comparison, and AI workflow orchestration. Built with Azure serverless architecture for scalability and cost-effectiveness.

### Key Features

- **🎯 Intelligent Prompt Engineering**: Guided prompt creation with AI-powered suggestions
- **🔄 Multi-LLM Optimization**: Compare outputs from OpenAI, Anthropic, and Google models
- **📁 Prompt Management**: Organize prompts in collections with version control
- **⚡ Linear AI Workflows**: Create step-by-step automation playbooks
- **👥 Team Collaboration**: Share prompts and workflows across teams
- **🛡️ Admin Controls**: Budget management, usage monitoring, and system health
- **💰 Cost Optimization**: Two-tier Azure architecture for efficient resource management

## Tech Stack

### Frontend
- **React 18** with TypeScript
- **Tailwind CSS** for responsive design
- **React Router** for navigation
- **React Query** for data fetching
- **Vite** for fast development

### Backend
- **Azure Functions** (Python 3.12)
- **Cosmos DB** for data persistence
- **Azure Key Vault** for secrets management
- **Azure Storage** for file management

### DevOps
- **Docker Compose** for local development
- **Playwright** for E2E testing
- **Jest** for unit testing
- **GitHub Actions** for CI/CD

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.12+
- Azure Functions Core Tools
- Docker Desktop (optional, for full local setup)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/sutra.git
   cd sutra
   ```

2. **Install dependencies**
   ```bash
   # Frontend dependencies
   npm install
   
   # Backend dependencies (use CI requirements to avoid compilation issues)
   cd api
   pip install -r requirements-ci.txt
   cd ..
   ```
   
   > **Note**: If you encounter `grpcio` compilation errors, use `requirements-ci.txt` which excludes problematic dependencies that are provided by the Azure Functions runtime.

3. **Start development servers**
   ```bash
   # Terminal 1: Backend API
   cd api
   func start --host 0.0.0.0 --port 7071
   
   # Terminal 2: Frontend
   npm run dev
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:7071

### Environment Setup

Create `api/local.settings.json`:
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "DEVELOPMENT_MODE": "true",
    "COSMOS_DB_ENDPOINT": "your-cosmos-endpoint",
    "COSMOS_DB_KEY": "your-cosmos-key",
    "COSMOS_DB_DATABASE": "sutra-db"
  }
}
```

Create `.env.local`:
```env
VITE_API_URL=http://localhost:7071/api
VITE_ENVIRONMENT=development
```

## Features

### ✅ Completed (MVP Ready)

#### Backend Foundation
- [x] Azure Functions API with Python runtime
- [x] Cosmos DB integration with dev-mode fallback
- [x] Authentication and authorization system
- [x] Admin-controlled LLM integrations
- [x] Budget tracking and enforcement
- [x] Collections and Playbooks CRUD operations
- [x] LLM execution engine
- [x] Comprehensive error handling

#### Frontend Application
- [x] React application with TypeScript
- [x] Authentication flow (dev-mode ready)
- [x] Responsive design with Tailwind CSS
- [x] Prompt Builder with multi-LLM testing
- [x] Collections management interface
- [x] Playbook Builder with workflow creation
- [x] Admin Panel with system monitoring
- [x] Real-time API integration

#### DevOps & Testing
- [x] Local development environment
- [x] E2E testing with Playwright
- [x] API validation scripts
- [x] Docker Compose setup

### 🔄 In Progress

- [ ] Azure AD B2C integration for production auth
- [ ] Playbook execution engine
- [ ] Version history and diff view
- [ ] Advanced prompt suggestions (PromptCoach)
- [ ] User management interface

### 🎯 Planned

- [ ] Two-tier Azure deployment
- [ ] Advanced team collaboration
- [ ] Real-time collaboration features
- [ ] Performance optimization
- [ ] Monitoring and alerting
- **Database**: Azure Cosmos DB (Serverless)
- **Authentication**: Azure AD B2C
- **Infrastructure**: Two-tier resource groups for cost optimization

## 📁 Project Structure

```
sutra/
├── src/                    # Frontend React application
├── api/                    # Backend Azure Functions
├── infrastructure/         # Azure Bicep templates
├── tests/                  # End-to-end tests
├── local-dev/             # Local development setup
├── docs/                  # Documentation
└── tasks/                 # Project task management
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.12+
- Docker & Docker Compose
- Azure Functions Core Tools
- Azure CLI

### Local Development
```bash
# Start local development environment
npm run dev:local

# Run tests
npm run test:e2e
```

### End-to-End Testing

The Sutra application includes a comprehensive E2E testing suite for validating critical user flows locally before deployment.

**Quick Start:**
```bash
# Run full E2E test suite
npm run test:e2e

# Run E2E tests with UI for debugging
npm run test:e2e:ui

# Manual control of services
npm run e2e:setup    # Start services
npm run test:e2e:headed  # Run tests with browser visible
npm run e2e:cleanup  # Stop services
```

**Test Coverage:**
- 🔐 Authentication and session management
- 🎯 Prompt creation, editing, and multi-LLM testing
- 📁 Collection management and organization
- ⚡ Playbook workflow creation and execution
- 🧭 Navigation and responsive design

For detailed setup instructions, troubleshooting, and test development guidelines, see [E2E_TESTING.md](./E2E_TESTING.md).

## 🏗️ Resource Groups

### Persistent Resources (sutra-db-rg)
- `sutra-db` - Cosmos DB
- `sutra-kv` - Key Vault  
- `sutrasa99` - Storage Account

### Compute Resources (sutra-rg)
- `sutra-api` - Azure Functions
- `sutra-web` - Static Web App
- `sutra-fd` - Front Door
- `sutra-ai` - Application Insights

## 📖 Documentation

- [PRD](./docs/PRD-Sutra.md) - Product Requirements
- [Functional Spec](./docs/Functional_Spec_Sutra.md) - Detailed specifications
- [Technical Spec](./docs/Tech_Spec_Sutra.md) - Technical architecture
- [Task List](./tasks/tasks-sutra-mvp.md) - Development roadmap

## 🎯 MVP Features

- Intelligent Prompt Engineering & Multi-LLM Optimization
- Prompt Management & Team Collaboration
- Linear AI Workflow Orchestration (Playbooks)
- Admin-controlled LLM budgets and monitoring

---

*Built with ❤️ for systematic AI operations*
