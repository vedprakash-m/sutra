# Infrastructure Deployment Guide

## Overview

Sutra uses a **two-tier Azure resource group architecture** designed for cost optimization and operational simplicity:

- **sutra-db-rg** (Persistent): Data, secrets, and storage that must persist
- **sutra-rg** (Compute): Application services that can be deleted/recreated

## Architecture Principles

### Cost Optimization Strategy
- **Persistent Tier**: Always running, contains all critical data
- **Compute Tier**: Can be deleted during extended downtime (weekends, holidays)
- **Static Resource Naming**: Ensures consistent, idempotent deployments

### Resource Naming Convention
All resources use static, globally consistent names:
- `sutra-db` - Cosmos DB (persistent)
- `sutra-kv` - Key Vault (persistent)
- `sutrasa99` - Storage Account (persistent, globally unique)
- `sutra-api` - Azure Functions (compute)
- `sutra-web` - Static Web App (compute)
- `sutra-fd` - Front Door (compute)
- `sutra-ai` - Application Insights (compute)

## Prerequisites

1. **Azure CLI** installed and authenticated
2. **Azure subscription** with appropriate permissions
3. **Resource groups** created:
   ```bash
   az group create --name sutra-db-rg --location "East US 2"
   az group create --name sutra-rg --location "East US 2"
   ```

## Deployment Steps

### Step 1: Deploy Persistent Infrastructure

Deploy the persistent tier that contains all data and secrets:

```bash
# Deploy persistent resources (Cosmos DB, Key Vault, Storage)
az deployment group create \
  --resource-group sutra-db-rg \
  --template-file infrastructure/persistent.bicep \
  --parameters @infrastructure/parameters.persistent.json
```

This creates:
- **sutra-db**: Cosmos DB with all application containers
- **sutra-kv**: Key Vault for secrets management
- **sutrasa99**: Storage Account for files and backups

### Step 2: Store Connection Strings in Key Vault

After persistent deployment, store the connection strings in Key Vault:

```bash
# Get the connection strings from deployment output
COSMOS_CONNECTION=$(az cosmosdb keys list --name sutra-db --resource-group sutra-db-rg --type connection-strings --query 'connectionStrings[0].connectionString' -o tsv)
STORAGE_CONNECTION=$(az storage account show-connection-string --name sutrasa99 --resource-group sutra-db-rg --query 'connectionString' -o tsv)

# Store in Key Vault
az keyvault secret set --vault-name sutra-kv --name cosmos-db-connection-string --value "$COSMOS_CONNECTION"
az keyvault secret set --vault-name sutra-kv --name storage-connection-string --value "$STORAGE_CONNECTION"
```

### Step 3: Deploy Compute Infrastructure

Deploy the compute tier that can be deleted for cost savings:

```bash
# Update the parameters file with your subscription ID
sed -i 's/{subscription-id}/'$(az account show --query id -o tsv)'/g' infrastructure/parameters.compute.json

# Deploy compute resources (Functions, Static Web App, Front Door)
az deployment group create \
  --resource-group sutra-rg \
  --template-file infrastructure/compute.bicep \
  --parameters @infrastructure/parameters.compute.json
```

This creates:
- **sutra-api**: Azure Functions for the backend API
- **sutra-web**: Static Web App for the frontend
- **sutra-fd**: Front Door for CDN and routing
- **sutra-ai**: Application Insights for monitoring

## Cost Management Operations

### Deleting Compute Resources (Cost Savings)

During extended downtime (weekends, holidays), delete the compute resource group:

```bash
# Delete compute resources to save costs
az group delete --name sutra-rg --yes --no-wait

# Data is preserved in sutra-db-rg
```

**What happens:**
- ✅ All data remains safe in sutra-db-rg
- ✅ Secrets remain in Key Vault
- ✅ Storage and backups remain intact
- 💰 Compute costs drop to $0

### Recreating Compute Resources

Recreate the compute tier when needed:

```bash
# Recreate the resource group
az group create --name sutra-rg --location "East US 2"

# Redeploy compute infrastructure
az deployment group create \
  --resource-group sutra-rg \
  --template-file infrastructure/compute.bicep \
  --parameters @infrastructure/parameters.compute.json
```

**What happens:**
- ✅ All data is automatically reconnected
- ✅ Application works exactly as before
- ✅ Zero data loss
- ⚡ Deployment takes ~10 minutes

## Monitoring and Maintenance

### Health Checks

Monitor the health of both tiers:

```bash
# Check persistent tier health
az cosmosdb show --name sutra-db --resource-group sutra-db-rg --query 'documentEndpoint'
az keyvault show --name sutra-kv --query 'properties.vaultUri'
az storage account show --name sutrasa99 --resource-group sutra-db-rg --query 'primaryEndpoints.blob'

# Check compute tier health (when deployed)
az functionapp show --name sutra-api --resource-group sutra-rg --query 'defaultHostName'
az staticwebapp show --name sutra-web --resource-group sutra-rg --query 'defaultHostname'
```

### Backup Verification

Verify Cosmos DB backups are working:

```bash
# Check backup policy
az cosmosdb show --name sutra-db --resource-group sutra-db-rg --query 'backupPolicy'

# List restore points (if needed)
az cosmosdb restorable-database-account list --location "East US 2"
```

### Cost Monitoring

Monitor costs for both resource groups:

```bash
# Get cost information
az consumption usage list --scope /subscriptions/$(az account show --query id -o tsv)/resourceGroups/sutra-db-rg
az consumption usage list --scope /subscriptions/$(az account show --query id -o tsv)/resourceGroups/sutra-rg
```

## Security Considerations

### Access Control
- Function App uses **System Assigned Managed Identity**
- Key Vault access is granted via **Access Policies**
- Storage Account uses **Azure AD authentication** where possible

### Network Security
- All resources use **HTTPS only**
- Storage Account has **public blob access disabled**
- Front Door enforces **HTTPS redirects**

### Secrets Management
- Connection strings stored in **Key Vault**
- Function App retrieves secrets via **Managed Identity**
- No hardcoded secrets in configuration

## Troubleshooting

### Common Issues

1. **Deployment Failures**
   - Check resource name availability (especially sutrasa99)
   - Verify subscription limits and quotas
   - Check Azure AD permissions

2. **Key Vault Access Issues**
   - Verify Managed Identity is assigned
   - Check Key Vault access policies
   - Ensure correct Key Vault URI

3. **Function App Not Starting**
   - Check Application Insights for errors
   - Verify all app settings are configured
   - Check storage account connectivity

### Support Commands

```bash
# Get deployment status
az deployment group show --name <deployment-name> --resource-group <rg-name>

# Check resource status
az resource list --resource-group sutra-db-rg --output table
az resource list --resource-group sutra-rg --output table

# Get logs
az monitor activity-log list --resource-group sutra-rg
```

## Maintenance Schedule

### Regular Tasks
- **Weekly**: Review cost reports and usage
- **Monthly**: Verify backup retention and restore points
- **Quarterly**: Review and update access policies

### Cost Optimization Windows
- **Weekends**: Consider deleting compute tier if no usage expected
- **Holidays**: Plan for extended compute tier deletion
- **Off-hours**: Use Application Insights to identify low-usage periods

## Recovery Procedures

### Disaster Recovery
1. Persistent tier automatically handles regional failover
2. Compute tier can be redeployed to any region
3. Front Door provides global traffic management

### Data Recovery
1. Cosmos DB has automatic point-in-time backups
2. Storage Account has soft delete enabled
3. Key Vault has soft delete and purge protection

This architecture provides enterprise-grade reliability with startup-friendly cost optimization.
