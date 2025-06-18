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

This architecture provides enterprise-grade reliability with startup-friendly cost optimization, enabling teams to scale operations efficiently while maintaining strict cost control.
