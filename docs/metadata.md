# Sutra Project Metadata - Source of Truth

## Project Status: **🚀 PRODUCTION DEPLOYED - ACTIVE**

**Last Updated:** June 23, 2025
**Current Phase:** 🚀 LIVE PRODUCTION WITH MICROSOFT ENTRA EXTERNAL ID
**Overall Health:** 🟢 EXCEPTIONAL (Production Active)

---

## 🚀 **PROJECT OVERVIEW**

**Sutra: Multi-LLM Prompt Studio** - Enterprise-grade platform for prompt engineering, multi-LLM optimization, and AI workflow orchestration. Delivers consistent, high-quality AI outputs through intelligent prompt management and collaborative workflows.

### **Architecture Stack**

- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS
- **Backend:** Azure Functions (Python 3.11+) + FastAPI (local dev)
- **Database:** Azure Cosmos DB (NoSQL, serverless mode)
- **Authentication:** Microsoft Entra External ID (vedid.onmicrosoft.com)
- **Testing:** Jest (Frontend: 92.39%), Pytest (Backend: 92%), Playwright (E2E)
- **CI/CD:** GitHub Actions + Azure DevOps integration
- **Infrastructure:** Azure Bicep templates + Key Vault secrets management

---

## 🌐 **PRODUCTION DEPLOYMENT - LIVE**

### **✅ Active Production Environment**

- **Static Web App**: `sutra-web-hvyqgbrvnx4ii`
- **Live URL**: https://zealous-flower-04bbe021e.2.azurestaticapps.net
- **Function App**: `sutra-api-hvyqgbrvnx4ii`
- **Resource Group**: `sutra-rg` (East US 2)
- **Status**: Fully operational with monitoring

### **🔐 Authentication System**

**Microsoft Entra External ID Configuration:**

- **Tenant Domain**: `vedid.onmicrosoft.com`
- **App Registration**: `sutra-web-app`
- **Client ID**: `61084964-08b8-49ea-b624-4859c4dc37de`
- **Integration**: Static Web Apps native authentication
- **Security Model**: Header-based validation (no MSAL in backend)
- **Session Management**: Azure platform handles token validation
- **CSRF Protection**: Built-in Azure Static Web Apps security

**Authentication Flow:**

```
User → Static Web App → Entra External ID → Token Validation →
Session Creation → Role Assignment (/api/getroles) → API Access
```

**Migration Achievement:**

- Successfully migrated from Azure AD B2C to Entra External ID
- Cost optimization: $1.00 → $0.05 per MAU (95% cost reduction)
- Enhanced security with modern identity platform
- Social login support (Google, Facebook, GitHub, Apple)

### **🏗️ Infrastructure Architecture**

**Two-Tier Cost-Optimized Design:**

| Component            | Tier       | Purpose        | Cost Impact             |
| -------------------- | ---------- | -------------- | ----------------------- |
| Static Web App       | Compute    | React Frontend | Auto-scale, pay-per-use |
| Azure Functions      | Compute    | Python APIs    | Serverless consumption  |
| Application Insights | Compute    | Monitoring     | Usage-based billing     |
| Cosmos DB            | Persistent | NoSQL Database | Serverless mode         |
| Key Vault            | Persistent | Secrets        | Always-on, minimal cost |
| Storage Account      | Persistent | File Storage   | Always-on, minimal cost |

**Infrastructure as Code:**

- **Primary Template**: `infrastructure/compute.bicep`
- **Persistent Services**: `infrastructure/persistent.bicep`
- **Parameters**: Environment-specific JSON files
- **Deployment**: Automated via GitHub Actions

**Cost Benefits:**

- 70-80% savings during development downtime
- Auto-scaling based on actual usage
- Zero data loss with persistent tier architecture

---

## ✅ **PRODUCTION READINESS - VALIDATED**

### **🎯 Test Coverage Excellence**

**Backend Coverage: 92% Overall** (477/477 tests passing)

| Module            | Coverage | Status              |
| ----------------- | -------- | ------------------- |
| Admin API         | 80%      | ✅ Production Ready |
| Collections API   | 81%      | ✅ Exceeds Target   |
| Integrations API  | 83%      | ✅ Excellent        |
| Playbooks API     | 81%      | ✅ Exceeds Target   |
| LLM Execute API   | 80%      | ✅ Production Ready |
| Health API        | 100%     | ✅ Perfect          |
| Shared Components | 90%+     | ✅ Excellent        |

**Frontend Coverage: 92.39%** (351/351 tests passing)

### **🐳 E2E Validation - PASSED**

- **Docker Desktop Integration**: ✅ ARM64 Mac compatibility resolved
- **Container Build Process**: ✅ Functions API builds successfully
- **Health Endpoints**: ✅ All systems operational
- **Platform Compatibility**: ✅ Cross-platform validated

### **🔒 Security Validation**

- **Azure Key Vault Integration**: ✅ Secrets management active
- **Authentication Flow**: ✅ Entra External ID operational
- **API Security**: ✅ Rate limiting and validation
- **Data Encryption**: ✅ At rest and in transit
- **Header-based Auth**: ✅ No sensitive tokens in backend

---

## 🚀 **CORE FEATURES - PRODUCTION ACTIVE**

### **🎯 Intelligent Prompt Engineering**

- Multi-LLM comparison (GPT-4, Claude 3.5, Gemini Pro)
- AI-powered PromptCoach suggestions and optimization
- Dynamic variable system with `{{placeholder}}` support
- Real-time validation and performance feedback

### **📁 Advanced Prompt Management**

- Hierarchical collections with tagging and categorization
- Team collaboration with role-based access control
- Version control and prompt history tracking
- Import/export functionality for enterprise workflows

### **🤖 Workflow Automation**

- Playbook runner for multi-step AI workflows
- Template system for reusable prompt patterns
- Batch processing and bulk operations
- Integration APIs for external systems

### **👥 Enterprise Collaboration**

- User/Admin role management via Entra External ID
- Team workspace sharing and permissions
- Activity logging and audit trails
- Performance analytics and usage insights

---

## 🛠️ **DEVELOPMENT WORKFLOW**

### **Local Development Setup**

```bash
# Full local environment
npm run dev:local          # Docker Compose + hot reload
docker-compose up -d       # Cosmos DB emulator + storage
npm run dev               # Frontend development server
cd api && func start     # Azure Functions local runtime
```

### **Testing & Validation**

```bash
# Comprehensive testing
npm run test              # Frontend unit tests
npm run test:coverage     # Frontend coverage report
cd api && python -m pytest --cov=. --cov-report=xml  # Backend coverage
npm run test:e2e          # Playwright E2E tests
npm run ci:local          # Complete validation pipeline
```

### **Authentication Development**

- **Static Web Apps Headers**: Pre-validated user information
- **Role Assignment**: `/api/getroles` endpoint for permission management
- **No MSAL Required**: Azure platform handles token validation
- **Session Management**: Automatic via Static Web Apps

### **Deployment Commands**

```bash
# Infrastructure deployment
./scripts/deploy-infrastructure.sh  # Bicep template deployment
./scripts/deploy-authentication.sh  # Authentication configuration
npm run validate:infra              # Infrastructure validation
./scripts/validate-ci-cd.sh         # CI/CD pipeline validation
```

---

## 🔐 **SECRET MANAGEMENT SYSTEM**

### **Hybrid Security Architecture**

- **Local Development**: .env files with sync indicators
- **Production**: Azure Key Vault as single source of truth
- **Sync States**: 🟢 Actual Value, 🔄 Synced, 🔴 Empty
- **Git Protection**: Confidential/ folder excluded from commits

### **Environment Variables**

**Authentication Configuration:**

- `VED_EXTERNAL_ID_CLIENT_ID`: 61084964-08b8-49ea-b624-4859c4dc37de
- `VED_EXTERNAL_ID_DOMAIN`: vedid.onmicrosoft.com
- `VED_EXTERNAL_ID_CLIENT_SECRET`: (Azure Key Vault managed)

**Service Endpoints:**

- `AZURE_FUNCTIONS_URL`: https://sutra-api-hvyqgbrvnx4ii.azurewebsites.net
- `AZURE_STATIC_WEB_APP_URL`: https://zealous-flower-04bbe021e.2.azurestaticapps.net

### **Secret Management Commands**

```bash
# Available in Confidential/ directory
./setup_azure_integration.sh     # Initial Azure setup
./sync_secrets_to_azure.sh       # Upload to Key Vault
./sync_to_local_env.sh           # Download for development
./check_and_update_secrets.sh    # Validation and updates
```

---

## 📊 **QUALITY METRICS - PRODUCTION STANDARDS**

### **Performance Benchmarks**

- **API Response Time**: <500ms average (✅ Achieved)
- **Database Queries**: <100ms average (✅ Achieved)
- **LLM Integration**: <10s timeout with failover (✅ Achieved)
- **Frontend Load**: <2s initial load (✅ Achieved)

### **Reliability Standards**

- **Uptime Target**: 99.9% (Static Web Apps SLA)
- **Error Rate**: <1% (monitored via Application Insights)
- **Test Success Rate**: 100% (828/828 total tests passing)
- **Security Score**: A+ (Azure Security Center validated)

---

## 🗂️ **PROJECT STRUCTURE**

```
sutra/
├── api/                          # Azure Functions backend
│   ├── admin_api/               # Admin management endpoints
│   ├── collections_api/         # Prompt collection management
│   ├── integrations_api/        # LLM provider integrations
│   ├── llm_execute_api/         # Prompt execution engine
│   ├── playbooks_api/           # Workflow automation
│   ├── getroles/                # Role assignment endpoint
│   ├── user_management/         # User profile management
│   └── shared/                  # Common utilities and models
├── src/                         # React frontend application
│   ├── components/              # Reusable UI components
│   ├── pages/                   # Application pages
│   ├── hooks/                   # Custom React hooks
│   └── utils/                   # Frontend utilities
├── infrastructure/              # Azure Bicep IaC templates
│   ├── compute.bicep           # Main compute infrastructure
│   ├── persistent.bicep        # Persistent services
│   └── parameters.*.json       # Environment-specific parameters
├── scripts/                     # Automation and deployment scripts
│   ├── deploy-infrastructure.sh # Infrastructure deployment
│   ├── deploy-authentication.sh # Authentication setup
│   ├── local-validation.sh     # Local development validation
│   └── validate-ci-cd.sh       # CI/CD pipeline validation
├── tests/e2e/                  # Playwright end-to-end tests
├── docs/                       # Technical documentation
│   ├── Functional_Spec_Sutra.md   # Product requirements
│   ├── Tech_Spec_Sutra.md         # Technical architecture
│   ├── User_Experience.md         # UX/UI guidelines
│   └── PRD-Sutra.md              # Product requirements document
├── Confidential/               # Secure secret management (git-ignored)
└── .github/workflows/          # CI/CD pipeline definitions
```

---

## 🎯 **NEXT MILESTONES**

### **Current Focus (Q2 2025)**

1. **User Onboarding Optimization** - Enhanced first-time experience
2. **Performance Monitoring** - Real-world usage analytics
3. **Feature Expansion** - Based on production user feedback
4. **Integration Ecosystem** - Additional LLM providers and tools

### **Future Roadmap (Q3-Q4 2025)**

1. **Enterprise Features** - Advanced compliance and governance
2. **API Marketplace** - Third-party integration platform
3. **AI Assistant** - Intelligent prompt suggestion system
4. **Global Expansion** - Multi-region deployment optimization

---

## ⚡ **QUICK REFERENCE**

### **Production URLs**

- **Application**: https://zealous-flower-04bbe021e.2.azurestaticapps.net
- **API Health**: https://sutra-api-hvyqgbrvnx4ii.azurewebsites.net/api/health
- **Azure Portal**: https://portal.azure.com (Resource Group: sutra-rg)

### **Key Identifiers**

- **Tenant**: vedid.onmicrosoft.com
- **Client ID**: 61084964-08b8-49ea-b624-4859c4dc37de
- **Resource Group**: sutra-rg
- **Region**: East US 2

### **Support Contacts**

- **Technical Issues**: GitHub Issues
- **Authentication**: Azure Entra External ID documentation
- **Infrastructure**: Azure Support

---

**Project Health:** 🟢 **EXCELLENT** - Production deployed with exceptional quality metrics

**Implementation Status:** Live production environment serving users with 100% test success rate

**Security Status:** Enterprise-grade with Microsoft Entra External ID and Azure Key Vault

**Next Review:** July 15, 2025 (Monthly production health review)
