# Operations Manual: Cost-Optimized Resource Management

## Overview

This manual provides step-by-step procedures for managing Sutra's two-tier Azure infrastructure to optimize costs while maintaining data integrity and system reliability.

## Resource Architecture

### Persistent Tier (sutra-db-rg)
**Always Running - Critical Data**
- `sutra-db` - Cosmos DB (all application data)
- `sutra-kv` - Key Vault (secrets and API keys)
- `sutrasa99` - Storage Account (files and backups)

### Compute Tier (sutra-rg)
**Can Be Deleted - No Data Loss**
- `sutra-api` - Azure Functions (backend API)
- `sutra-web` - Static Web App (frontend)
- `sutra-fd` - Front Door (CDN and routing)
- `sutra-ai` - Application Insights (logs and metrics)

## Daily Operations

### Morning Startup Checklist

When starting the workday, verify system status:

```bash
# Check if compute tier is running
az group exists --name sutra-rg

# If false, recreate compute resources
if [ $? -ne 0 ]; then
    echo "Recreating compute tier..."
    az group create --name sutra-rg --location "East US 2"
    az deployment group create \
        --resource-group sutra-rg \
        --template-file infrastructure/compute.bicep \
        --parameters @infrastructure/parameters.compute.json
fi

# Verify all services are healthy
az functionapp show --name sutra-api --resource-group sutra-rg --query 'state'
az staticwebapp show --name sutra-web --resource-group sutra-rg --query 'state'
```

### Evening Shutdown Procedure

Save costs by stopping compute resources during off-hours:

```bash
# Option 1: Stop Function App (saves ~80% of compute costs)
az functionapp stop --name sutra-api --resource-group sutra-rg

# Option 2: Delete entire compute tier (saves 100% of compute costs)
# Only do this if no usage expected for extended period
az group delete --name sutra-rg --yes --no-wait
```

## Weekly Operations

### Cost Review (Every Monday)

Review costs and usage patterns:

```bash
# Get cost information for both tiers
echo "=== Persistent Tier Costs ==="
az consumption usage list \
    --scope /subscriptions/$(az account show --query id -o tsv)/resourceGroups/sutra-db-rg \
    --start-date $(date -d '7 days ago' +%Y-%m-%d) \
    --end-date $(date +%Y-%m-%d)

echo "=== Compute Tier Costs ==="
az consumption usage list \
    --scope /subscriptions/$(az account show --query id -o tsv)/resourceGroups/sutra-rg \
    --start-date $(date -d '7 days ago' +%Y-%m-%d) \
    --end-date $(date +%Y-%m-%d)
```

### Usage Analysis (Every Friday)

Analyze usage patterns to optimize shutdown windows:

```bash
# Query Application Insights for usage patterns
az monitor app-insights query \
    --app sutra-ai \
    --analytics-query "
    requests 
    | where timestamp > ago(7d)
    | summarize RequestCount = count() by bin(timestamp, 1h)
    | render timechart
    "
```

## Weekend Operations

### Friday Evening Shutdown

For weekend cost savings:

```bash
#!/bin/bash
# friday-shutdown.sh

echo "🌅 Starting weekend shutdown procedure..."

# Check if it's Friday
if [ $(date +%u) -eq 5 ]; then
    echo "📅 It's Friday - proceeding with shutdown"
    
    # Stop Function App
    echo "⏹️  Stopping Function App..."
    az functionapp stop --name sutra-api --resource-group sutra-rg
    
    # Optional: Delete entire compute tier for maximum savings
    read -p "🗑️  Delete entire compute tier for weekend? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Deleting compute tier..."
        az group delete --name sutra-rg --yes --no-wait
        echo "✅ Compute tier deletion initiated"
        echo "💰 Weekend cost savings activated"
    fi
else
    echo "📅 Not Friday - skipping shutdown"
fi

echo "✅ Weekend shutdown procedure complete"
```

### Monday Morning Startup

For weekend recovery:

```bash
#!/bin/bash
# monday-startup.sh

echo "🌅 Starting Monday morning startup procedure..."

# Check if compute tier exists
if az group exists --name sutra-rg; then
    echo "✅ Compute tier exists - checking Function App status"
    
    # Start Function App if stopped
    STATE=$(az functionapp show --name sutra-api --resource-group sutra-rg --query 'state' -o tsv)
    if [ "$STATE" = "Stopped" ]; then
        echo "▶️  Starting Function App..."
        az functionapp start --name sutra-api --resource-group sutra-rg
    fi
else
    echo "🏗️  Compute tier not found - recreating..."
    
    # Recreate compute tier
    az group create --name sutra-rg --location "East US 2"
    az deployment group create \
        --resource-group sutra-rg \
        --template-file infrastructure/compute.bicep \
        --parameters @infrastructure/parameters.compute.json
    
    echo "✅ Compute tier recreated"
fi

# Health check
echo "🔍 Running health checks..."
./local-dev/health-check.sh

echo "✅ Monday startup procedure complete"
```

## Holiday Operations

### Extended Shutdown (Holidays/Vacations)

For multi-day shutdowns:

```bash
#!/bin/bash
# holiday-shutdown.sh

echo "🏖️  Starting holiday shutdown procedure..."

# Backup current deployment parameters
cp infrastructure/parameters.compute.json infrastructure/parameters.compute.backup.json

# Delete compute tier
echo "🗑️  Deleting compute tier for extended period..."
az group delete --name sutra-rg --yes

# Wait for deletion to complete
echo "⏳ Waiting for deletion to complete..."
while az group exists --name sutra-rg; do
    echo "⏳ Still deleting..."
    sleep 30
done

echo "✅ Holiday shutdown complete"
echo "💰 Maximum cost savings active"
echo "📋 To restore: run holiday-restore.sh"
```

### Holiday Recovery

Restore after extended downtime:

```bash
#!/bin/bash
# holiday-restore.sh

echo "🏖️  Starting holiday restore procedure..."

# Restore compute tier
echo "🏗️  Recreating compute tier..."
az group create --name sutra-rg --location "East US 2"

# Deploy with backup parameters
az deployment group create \
    --resource-group sutra-rg \
    --template-file infrastructure/compute.bicep \
    --parameters @infrastructure/parameters.compute.backup.json

echo "✅ Holiday restore complete"
echo "🚀 System is back online"
```

## Emergency Procedures

### Rapid Recovery

If the system needs to be brought online quickly:

```bash
#!/bin/bash
# emergency-restore.sh

echo "🚨 Emergency restore procedure initiated..."

# Create resource group if missing
if ! az group exists --name sutra-rg; then
    echo "🏗️  Creating resource group..."
    az group create --name sutra-rg --location "East US 2"
fi

# Deploy compute resources with high priority
echo "⚡ Deploying compute resources..."
az deployment group create \
    --resource-group sutra-rg \
    --template-file infrastructure/compute.bicep \
    --parameters @infrastructure/parameters.compute.json \
    --mode Complete

# Force restart all services
echo "🔄 Restarting all services..."
az functionapp restart --name sutra-api --resource-group sutra-rg

echo "✅ Emergency restore complete"
```

### Data Integrity Check

After any restore operation:

```bash
#!/bin/bash
# data-integrity-check.sh

echo "🔍 Running data integrity checks..."

# Check Cosmos DB connectivity
COSMOS_STATUS=$(az cosmosdb show --name sutra-db --resource-group sutra-db-rg --query 'documentEndpoint' -o tsv)
if [ -n "$COSMOS_STATUS" ]; then
    echo "✅ Cosmos DB: Accessible"
else
    echo "❌ Cosmos DB: Issue detected"
fi

# Check Key Vault connectivity
KV_STATUS=$(az keyvault show --name sutra-kv --query 'properties.vaultUri' -o tsv)
if [ -n "$KV_STATUS" ]; then
    echo "✅ Key Vault: Accessible"
else
    echo "❌ Key Vault: Issue detected"
fi

# Check Storage Account connectivity
STORAGE_STATUS=$(az storage account show --name sutrasa99 --resource-group sutra-db-rg --query 'primaryEndpoints.blob' -o tsv)
if [ -n "$STORAGE_STATUS" ]; then
    echo "✅ Storage: Accessible"
else
    echo "❌ Storage: Issue detected"
fi

echo "✅ Data integrity check complete"
```

## Cost Monitoring and Alerts

### Set Up Cost Alerts

Configure automatic cost monitoring:

```bash
# Create cost alert for compute tier
az consumption budget create \
    --budget-name "sutra-compute-budget" \
    --amount 100 \
    --time-grain Monthly \
    --start-date $(date +%Y-%m-01) \
    --end-date $(date -d '+1 year' +%Y-%m-01) \
    --resource-group sutra-rg

# Create cost alert for persistent tier
az consumption budget create \
    --budget-name "sutra-persistent-budget" \
    --amount 50 \
    --time-grain Monthly \
    --start-date $(date +%Y-%m-01) \
    --end-date $(date -d '+1 year' +%Y-%m-01) \
    --resource-group sutra-db-rg
```

### Daily Cost Check

Quick cost check for daily operations:

```bash
#!/bin/bash
# daily-cost-check.sh

echo "💰 Daily cost summary for $(date +%Y-%m-%d)"

# Get yesterday's costs
YESTERDAY=$(date -d '1 day ago' +%Y-%m-%d)

echo "=== Persistent Tier ==="
az consumption usage list \
    --scope /subscriptions/$(az account show --query id -o tsv)/resourceGroups/sutra-db-rg \
    --start-date $YESTERDAY \
    --end-date $(date +%Y-%m-%d) \
    --query '[].{Service: meterName, Cost: pretaxCost.amount}' \
    --output table

echo "=== Compute Tier ==="
if az group exists --name sutra-rg; then
    az consumption usage list \
        --scope /subscriptions/$(az account show --query id -o tsv)/resourceGroups/sutra-rg \
        --start-date $YESTERDAY \
        --end-date $(date +%Y-%m-%d) \
        --query '[].{Service: meterName, Cost: pretaxCost.amount}' \
        --output table
else
    echo "Compute tier offline - $0 cost"
fi
```

## Automation Scripts

### Cron Job Setup

Automate weekend shutdowns and startups:

```bash
# Add to crontab (crontab -e)

# Friday 6 PM - Stop compute resources
0 18 * * 5 /path/to/friday-shutdown.sh

# Monday 8 AM - Start compute resources
0 8 * * 1 /path/to/monday-startup.sh

# Daily 9 AM - Cost check
0 9 * * * /path/to/daily-cost-check.sh
```

### Slack/Teams Integration

Send notifications for cost events:

```bash
#!/bin/bash
# notify-cost-event.sh

WEBHOOK_URL="your-slack-webhook-url"
MESSAGE="$1"

curl -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"💰 Sutra Cost Alert: $MESSAGE\"}" \
    $WEBHOOK_URL
```

## Best Practices

### Do's ✅
- Always verify persistent tier health before compute operations
- Test restore procedures in development environment first
- Monitor costs daily during initial setup
- Document any manual changes to infrastructure
- Keep infrastructure templates in version control

### Don'ts ❌
- Never delete the persistent tier (sutra-db-rg)
- Don't modify resources manually in Azure portal
- Don't store secrets outside Key Vault
- Don't skip data integrity checks after restore
- Don't automate deletion without human approval

## Troubleshooting

### Common Issues and Solutions

1. **Compute tier won't start**
   - Check Key Vault access policies
   - Verify connection strings in Key Vault
   - Check subscription limits and quotas

2. **Function App deployment fails**
   - Verify storage account connectivity
   - Check Application Insights configuration
   - Review deployment logs

3. **Static Web App not accessible**
   - Check Front Door configuration
   - Verify DNS settings
   - Review routing rules

4. **High costs despite shutdown**
   - Check for orphaned resources
   - Review Front Door charges
   - Verify storage account usage

### Support Contacts

- **Azure Support**: Use Azure portal support tickets
- **Development Team**: Internal escalation procedures
- **Operations Team**: 24/7 on-call rotation

This operations manual ensures reliable, cost-effective management of the Sutra platform while maintaining enterprise-grade reliability and data protection.
