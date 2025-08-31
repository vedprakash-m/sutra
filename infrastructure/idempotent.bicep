// Sutra Production Infrastructure - Idempotent Template
// References existing consolidated resources with proper naming
targetScope = 'resourceGroup'

// =============================================================================
// EXISTING CONSOLIDATED RESOURCES (Reference only)
// =============================================================================

resource existingCosmosDb 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' existing = {
  name: 'sutra-db'
}

resource existingKeyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: 'sutra-kv'
}

resource existingStorage 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: 'sutrasa99'
}

resource existingLogAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: 'sutra-logs'
}

resource existingAppInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: 'sutra-ai'
}

resource existingAppServicePlan 'Microsoft.Web/serverfarms@2023-12-01' existing = {
  name: 'sutra-flex-plan'
}

resource existingFunctionApp 'Microsoft.Web/sites@2023-12-01' existing = {
  name: 'sutra-flex-api-hvyqgbrvnx4ii'
}

resource existingStaticWebApp 'Microsoft.Web/staticSites@2023-12-01' existing = {
  name: 'sutra-frontend-hvyqgbrvnx4ii'
}

// =============================================================================
// RBAC PERMISSIONS (Idempotent - will only create if not exists)
// =============================================================================

// Key Vault access for Function App
resource functionAppKeyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(existingKeyVault.id, existingFunctionApp.id, 'Key Vault Secrets User')
  scope: existingKeyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: existingFunctionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Storage access for Function App
resource functionAppStorageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(existingStorage.id, existingFunctionApp.id, 'Storage Blob Data Contributor')
  scope: existingStorage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: existingFunctionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// =============================================================================
// OUTPUTS
// =============================================================================

output functionAppName string = existingFunctionApp.name
output functionAppUrl string = 'https://${existingFunctionApp.properties.defaultHostName}'
output apiBaseUrl string = 'https://${existingFunctionApp.properties.defaultHostName}/api'
output staticWebAppName string = existingStaticWebApp.name
output staticWebAppUrl string = 'https://${existingStaticWebApp.properties.defaultHostname}'
output appServicePlanName string = existingAppServicePlan.name
output keyVaultUrl string = existingKeyVault.properties.vaultUri
output storageAccountUrl string = existingStorage.properties.primaryEndpoints.blob
output cosmosDbEndpoint string = existingCosmosDb.properties.documentEndpoint

// =============================================================================
// RESOURCE SUMMARY
// =============================================================================

output resourceSummary object = {
  consolidated: true
  singleResourceGroup: true
  singleSlot: true
  singleEnvironment: true
  costOptimized: true
  resources: {
    cosmosDb: existingCosmosDb.name
    keyVault: existingKeyVault.name
    storageAccount: existingStorage.name
    functionApp: existingFunctionApp.name
    appServicePlan: existingAppServicePlan.name
    staticWebApp: existingStaticWebApp.name
    logAnalytics: existingLogAnalytics.name
    appInsights: existingAppInsights.name
  }
}
