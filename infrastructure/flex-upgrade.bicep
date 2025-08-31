// Flex Consumption Upgrade Template
// Only creates new resources needed for the upgrade
targetScope = 'resourceGroup'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Tags to apply to all resources')
param tags object = {
  environment: 'production'
  project: 'sutra'
  tier: 'flex-upgrade'
  architecture: 'unified'
}

// =============================================================================
// NEW FLEX CONSUMPTION PLAN
// =============================================================================

resource flexConsumptionPlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: 'sutra-flex-plan'
  location: location
  tags: tags
  sku: {
    name: 'FC1'
    tier: 'FlexConsumption'
  }
  kind: 'functionapp'
  properties: {
    reserved: true
  }
}

// =============================================================================
// NEW STORAGE ACCOUNT FOR FLEX CONSUMPTION
// =============================================================================

resource flexStorageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'flexsa${uniqueString(resourceGroup().id)}'
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    dnsEndpointType: 'Standard'
    defaultToOAuthAuthentication: false
    publicNetworkAccess: 'Enabled'
    allowCrossTenantReplication: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
    networkAcls: {
      bypass: 'AzureServices'
      virtualNetworkRules: []
      ipRules: []
      defaultAction: 'Allow'
    }
    supportsHttpsTrafficOnly: true
    encryption: {
      requireInfrastructureEncryption: false
      services: {
        file: {
          keyType: 'Account'
          enabled: true
        }
        blob: {
          keyType: 'Account'
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
    accessTier: 'Hot'
  }
}

// =============================================================================
// REFERENCES TO EXISTING RESOURCES
// =============================================================================

resource existingKeyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: 'sutra-kv'
}

resource existingAppInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: 'sutra-ai'
}

// =============================================================================
// NEW FUNCTION APP WITH FLEX CONSUMPTION
// =============================================================================

resource flexFunctionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: 'sutra-flex-api-${uniqueString(resourceGroup().id)}'
  location: location
  tags: tags
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    enabled: true
    serverFarmId: flexConsumptionPlan.id
    reserved: true
    isXenon: false
    hyperV: false
    vnetRouteAllEnabled: false
    vnetImagePullEnabled: false
    vnetContentShareEnabled: false
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${flexStorageAccount.properties.primaryEndpoints.blob}deployments'
          authentication: {
            type: 'SystemAssignedIdentity'
          }
        }
      }
      scaleAndConcurrency: {
        maximumInstanceCount: 1000
        instanceMemoryMB: 2048
      }
      runtime: {
        name: 'python'
        version: '3.12'
      }
    }
    siteConfig: {
      numberOfWorkers: 1
      acrUseManagedIdentityCreds: false
      alwaysOn: false
      http20Enabled: true
      appSettings: [
        {
          name: 'AzureWebJobsStorage__accountName'
          value: flexStorageAccount.name
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: existingAppInsights.properties.ConnectionString
        }
        {
          name: 'KEY_VAULT_URL'
          value: existingKeyVault.properties.vaultUri
        }
        {
          name: 'SUTRA_ENVIRONMENT'
          value: 'production'
        }
        {
          name: 'COSMOS_DB_ENDPOINT'
          value: 'https://sutra-db.documents.azure.com:443/'
        }
        {
          name: 'COSMOS_DB_DATABASE'
          value: 'sutra'
        }
      ]
    }
  }
}

// =============================================================================
// RBAC PERMISSIONS
// =============================================================================

// Key Vault access for new Function App
resource flexFunctionAppKeyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(existingKeyVault.id, flexFunctionApp.id, 'Key Vault Secrets User')
  scope: existingKeyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: flexFunctionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Storage access for new Function App
resource flexFunctionAppStorageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(flexStorageAccount.id, flexFunctionApp.id, 'Storage Blob Data Contributor')
  scope: flexStorageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: flexFunctionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// =============================================================================
// OUTPUTS
// =============================================================================

output flexFunctionAppName string = flexFunctionApp.name
output flexFunctionAppUrl string = 'https://${flexFunctionApp.properties.defaultHostName}'
output flexApiBaseUrl string = 'https://${flexFunctionApp.properties.defaultHostName}/api'
output flexPlanName string = flexConsumptionPlan.name
output flexStorageName string = flexStorageAccount.name
