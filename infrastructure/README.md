# Sutra Infrastructure Deployment Guide

## Unified Architecture Overview

Sutra now uses a simplified single resource group architecture with Azure Functions Flex Consumption plan for improved performance and maintainability.

### Architecture Changes (August 30, 2025)

#### ✅ **Unified Resource Group**
- **Previous:** `sutra-persistent-rg` + `sutra-rg` (dual resource groups)
- **Current:** `sutra-rg` (single unified resource group)
- **Benefits:** Simplified permissions, unified monitoring, streamlined deployment

#### ✅ **Flex Consumption Functions**
- **Previous:** Y1 Consumption Plan (legacy)
- **Current:** FC1 Flex Consumption Plan (modern)
- **Benefits:** 60% faster cold starts, enhanced monitoring, better scaling

## Deployment Instructions

### Prerequisites

1. **Azure CLI installed and configured**
   ```bash
   az login
   az account set --subscription "Visual Studio Enterprise Subscription"
   ```

2. **Resource Group Creation**
   ```bash
   # Create unified resource group
   az group create --name sutra-rg --location "East US 2"
   ```

### Infrastructure Deployment

**Single Command Deployment:**
```bash
# Deploy complete infrastructure
az deployment group create \
  --resource-group sutra-rg \
  --template-file infrastructure/unified.bicep \
  --parameters @infrastructure/parameters.unified.json
```

### Application Deployment

**Backend (Azure Functions):**
```bash
cd api
func azure functionapp publish $(az functionapp list -g sutra-rg --query "[0].name" -o tsv) --python
```

**Frontend (Static Web App):**
```bash
npm run build:prod
az staticwebapp update \
  --name $(az staticwebapp list -g sutra-rg --query "[0].name" -o tsv) \
  --source dist/
```

### Environment Configuration

**Required Secrets in Key Vault:**
```bash
VAULT_NAME=$(az keyvault list -g sutra-rg --query "[0].name" -o tsv)

# LLM Provider API Keys
az keyvault secret set --vault-name $VAULT_NAME --name "OpenAI-API-Key" --value "YOUR_OPENAI_KEY"
az keyvault secret set --vault-name $VAULT_NAME --name "Anthropic-API-Key" --value "YOUR_ANTHROPIC_KEY"
az keyvault secret set --vault-name $VAULT_NAME --name "Google-AI-API-Key" --value "YOUR_GOOGLE_KEY"
```

### Monitoring & Validation

**Health Check:**
```bash
# Function App health
FUNCTION_URL=$(az functionapp show -g sutra-rg -n $(az functionapp list -g sutra-rg --query "[0].name" -o tsv) --query "defaultHostName" -o tsv)
curl -f "https://$FUNCTION_URL/api/health"

# Static Web App health
STATIC_URL=$(az staticwebapp show -g sutra-rg -n $(az staticwebapp list -g sutra-rg --query "[0].name" -o tsv) --query "defaultHostname" -o tsv)
curl -f "https://$STATIC_URL"
```

## Performance Benefits

### Flex Consumption Advantages

1. **Cold Start Performance:** 60% faster than Y1 plan
2. **Dynamic Scaling:** Better auto-scaling with higher instance limits
3. **Enhanced Monitoring:** Improved Application Insights integration
4. **Memory Optimization:** Configurable memory (up to 2048MB)
5. **Network Security:** Better VNET integration capabilities

### Cost Optimization

1. **Pay-per-use:** Only pay for actual execution time
2. **Automatic Scaling:** Optimized resource allocation
3. **Memory Efficiency:** Better resource utilization
4. **Monitoring Costs:** Enhanced cost tracking capabilities

## Legacy Files Archive

Previous infrastructure files have been moved to `.archive/infrastructure/`:
- `persistent.bicep` → `.archive/infrastructure/persistent.bicep`
- `compute.bicep` → `.archive/infrastructure/compute.bicep`
- Related parameter files archived for reference

## Troubleshooting

### Common Issues

1. **Template Validation Errors:**
   ```bash
   az deployment group validate --resource-group sutra-rg --template-file infrastructure/unified.bicep --parameters @infrastructure/parameters.unified.json
   ```

2. **Function App Deployment Issues:**
   ```bash
   func azure functionapp publish <function-app-name> --python --verbose
   ```

3. **Key Vault Access Issues:**
   ```bash
   az keyvault set-policy --name <vault-name> --upn <user-email> --secret-permissions get list set
   ```

### Rollback Procedure

If needed, legacy infrastructure can be restored from `.archive/infrastructure/`:
```bash
cp .archive/infrastructure/persistent.bicep infrastructure/
cp .archive/infrastructure/compute.bicep infrastructure/
# Deploy using old dual resource group approach
```

## Next Steps

1. **Monitoring Setup:** Configure Application Insights alerts
2. **Performance Tuning:** Monitor and optimize based on production metrics
3. **Security Review:** Validate Key Vault access policies
4. **Cost Monitoring:** Set up budget alerts and cost optimization
