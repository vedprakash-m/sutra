// Persistent Infrastructure Template (sutra-db-rg)
// Contains all data and secrets that must persist across deployments
targetScope = 'resourceGroup'

@description('Location for all persistent resources')
param location string = resourceGroup().location

@description('Tags to apply to all resources')
param tags object = {
  environment: 'production'
  project: 'sutra'
  tier: 'persistent'
}

// =============================================================================
// PERSISTENT STORAGE (sutra-db)
// =============================================================================

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: 'sutra-db'
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    enableFreeTier: false
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
    backupPolicy: {
      type: 'Periodic'
      periodicModeProperties: {
        backupIntervalInMinutes: 240
        backupRetentionIntervalInHours: 168
        backupStorageRedundancy: 'Local'
      }
    }
  }
}

resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmosAccount
  name: 'sutra'
  properties: {
    resource: {
      id: 'sutra'
    }
  }
}

// Core collections for the application
resource promptsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'Prompts'
  properties: {
    resource: {
      id: 'Prompts'
      partitionKey: {
        paths: ['/userId']
        kind: 'Hash'
      }
      defaultTtl: -1
    }
  }
}

resource collectionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'Collections'
  properties: {
    resource: {
      id: 'Collections'
      partitionKey: {
        paths: ['/userId']
        kind: 'Hash'
      }
      defaultTtl: -1
    }
  }
}

resource playbooksContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'Playbooks'
  properties: {
    resource: {
      id: 'Playbooks'
      partitionKey: {
        paths: ['/userId']
        kind: 'Hash'
      }
      defaultTtl: -1
    }
  }
}

resource usersContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'Users'
  properties: {
    resource: {
      id: 'Users'
      partitionKey: {
        paths: ['/id']
        kind: 'Hash'
      }
      defaultTtl: -1
    }
  }
}

resource executionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'Executions'
  properties: {
    resource: {
      id: 'Executions'
      partitionKey: {
        paths: ['/userId']
        kind: 'Hash'
      }
      defaultTtl: -1
    }
  }
}

resource systemConfigContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'SystemConfig'
  properties: {
    resource: {
      id: 'SystemConfig'
      partitionKey: {
        paths: ['/type']
        kind: 'Hash'
      }
      defaultTtl: -1
    }
  }
}

resource auditLogContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'AuditLog'
  properties: {
    resource: {
      id: 'AuditLog'
      partitionKey: {
        paths: ['/userId']
        kind: 'Hash'
      }
      defaultTtl: 7776000 // 90 days retention for audit logs
    }
  }
}

resource usageContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'usage'
  properties: {
    resource: {
      id: 'usage'
      partitionKey: {
        paths: ['/date']
        kind: 'Hash'
      }
      defaultTtl: 2592000 // 30 days retention for usage data
    }
  }
}

resource guestSessionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'GuestSessions'
  properties: {
    resource: {
      id: 'GuestSessions'
      partitionKey: {
        paths: ['/ipAddress']
        kind: 'Hash'
      }
      defaultTtl: 86400 // 24 hours - matches PRD guest session lifetime
    }
  }
}

resource guestAnalyticsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'GuestAnalytics'
  properties: {
    resource: {
      id: 'GuestAnalytics'
      partitionKey: {
        paths: ['/date']
        kind: 'Hash'
      }
      defaultTtl: 2592000 // 30 days - for conversion analytics
    }
  }
}

resource budgetConfigsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'BudgetConfigs'
  properties: {
    resource: {
      id: 'BudgetConfigs'
      partitionKey: {
        paths: ['/entityType']
        kind: 'Hash'
      }
      defaultTtl: -1 // Persistent budget configurations
    }
  }
}

resource usageMetricsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'UsageMetrics'
  properties: {
    resource: {
      id: 'UsageMetrics'
      partitionKey: {
        paths: ['/userId']
        kind: 'Hash'
      }
      defaultTtl: 7776000 // 90 days - for cost management analytics
    }
  }
}

resource configContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'config'
  properties: {
    resource: {
      id: 'config'
      partitionKey: {
        paths: ['/type']
        kind: 'Hash'
      }
      defaultTtl: -1
    }
  }
}

// =============================================================================
// KEY VAULT (sutra-kv)
// =============================================================================

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'sutra-kv'
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enablePurgeProtection: true
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
    accessPolicies: []
  }
}

// =============================================================================
// STORAGE ACCOUNT (sutrasa99)
// =============================================================================

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: 'sutrasa99'
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    defaultToOAuthAuthentication: false
    allowCrossTenantReplication: false
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

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    cors: {
      corsRules: []
    }
    deleteRetentionPolicy: {
      allowPermanentDelete: false
      enabled: true
      days: 7
    }
  }
}

// Container for application files and backups
resource appContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'app-data'
  properties: {
    publicAccess: 'None'
  }
}

resource backupContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'backups'
  properties: {
    publicAccess: 'None'
  }
}

// =============================================================================
// OUTPUTS
// =============================================================================

@description('Cosmos DB account name')
output cosmosDbAccountName string = cosmosAccount.name

@description('Cosmos DB connection string')
@secure()
output cosmosDbConnectionString string = cosmosAccount.listConnectionStrings().connectionStrings[0].connectionString

@description('Key Vault name')
output keyVaultName string = keyVault.name

@description('Key Vault URI')
output keyVaultUri string = keyVault.properties.vaultUri

@description('Storage Account name')
output storageAccountName string = storageAccount.name

@description('Storage Account connection string')
@secure()
output storageConnectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'

@description('Resource Group ID for persistent resources')
output resourceGroupId string = resourceGroup().id
