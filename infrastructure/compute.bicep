// Compute Infrastructure Template (sutra-rg)
// Direct access architecture optimized for small teams
targetScope = 'resourceGroup'

@description('Location for all compute resources')
param location string = resourceGroup().location

@description('Tags to apply to all resources')
param tags object = {
  environment: 'production'
  project: 'sutra'
  tier: 'compute'
}

@description('Cosmos DB connection string from persistent infrastructure')
@secure()
param cosmosDbConnectionString string

@description('Storage Account connection string from persistent infrastructure')
@secure()
param storageConnectionString string

@description('Key Vault URI from persistent infrastructure')
param keyVaultUri string

@description('Custom domain for the application (optional)')
param customDomain string = ''

// =============================================================================
// APPLICATION INSIGHTS (sutra-ai)
// =============================================================================

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'sutra-logs'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      searchVersion: 1
      legacy: 0
    }
  }
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'sutra-ai'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// =============================================================================
// AZURE FUNCTIONS (sutra-api)
// Enhanced for direct access with security
// =============================================================================

resource functionAppServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: 'sutra-api-plan'
  location: location
  tags: tags
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
    size: 'Y1'
    family: 'Y'
    capacity: 0
  }
  kind: 'functionapp'
  properties: {
    perSiteScaling: false
    elasticScaleEnabled: false
    maximumElasticWorkerCount: 1
    isSpot: false
    reserved: true // Linux
    isXenon: false
    hyperV: false
    targetWorkerCount: 0
    targetWorkerSizeId: 0
    zoneRedundant: false
  }
}

resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: 'sutra-api-${uniqueString(resourceGroup().id)}'
  location: location
  tags: tags
  kind: 'functionapp,linux'
  properties: {
    enabled: true
    serverFarmId: functionAppServicePlan.id
    reserved: true
    isXenon: false
    hyperV: false
    vnetRouteAllEnabled: false
    vnetImagePullEnabled: false
    vnetContentShareEnabled: false
    siteConfig: {
      numberOfWorkers: 1
      linuxFxVersion: 'Python|3.12'
      acrUseManagedIdentityCreds: false
      alwaysOn: false
      http20Enabled: true
      functionAppScaleLimit: 200
      minimumElasticInstanceCount: 0
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: storageConnectionString
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: storageConnectionString
        }
        {
          name: 'WEBSITE_CONTENTSHARE'
          value: toLower('sutra-api-${uniqueString(resourceGroup().id)}')
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: applicationInsights.properties.InstrumentationKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: applicationInsights.properties.ConnectionString
        }
        {
          name: 'COSMOS_DB_CONNECTION_STRING'
          value: cosmosDbConnectionString
        }
        {
          name: 'KEY_VAULT_URI'
          value: keyVaultUri
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
        {
          name: 'SUTRA_ENVIRONMENT'
          value: 'production'
        }
        {
          name: 'SUTRA_MAX_REQUESTS_PER_MINUTE'
          value: '100'
        }
      ]
      cors: {
        allowedOrigins: [
          // Static Web App will be added dynamically
          'https://sutra-web-${uniqueString(resourceGroup().id)}.azurestaticapps.net'
          'https://localhost:5173' // Development
          'https://localhost:3000' // Development alternative
          empty(customDomain) ? '' : 'https://${customDomain}'
        ]
        supportCredentials: true // Enable for authentication
      }
      use32BitWorkerProcess: false
      ftpsState: 'FtpsOnly'
      powerShellVersion: ''
      // Enhanced security for direct access
      ipSecurityRestrictions: [
        {
          ipAddress: '0.0.0.0/0'
          action: 'Allow'
          priority: 1000
          name: 'Allow all'
          description: 'Open access for small team (can be restricted later)'
        }
      ]
      minTlsVersion: '1.2'
      scmMinTlsVersion: '1.2'
    }
    scmSiteAlsoStopped: false
    clientAffinityEnabled: false
    clientCertEnabled: false
    clientCertMode: 'Required'
    hostNamesDisabled: false
    customDomainVerificationId: ''
    containerSize: 1536
    dailyMemoryTimeQuota: 0
    httpsOnly: true
    redundancyMode: 'None'
    publicNetworkAccess: 'Enabled'
    storageAccountRequired: false
    keyVaultReferenceIdentity: 'SystemAssigned'
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// =============================================================================
// STATIC WEB APP (sutra-web)
// Enhanced with authentication and routing for direct access
// =============================================================================

resource staticWebApp 'Microsoft.Web/staticSites@2023-12-01' = {
  name: 'sutra-web-${uniqueString(resourceGroup().id)}'
  location: 'West US 2' // Static Web Apps have limited regions
  tags: tags
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {
    repositoryUrl: ''
    branch: ''
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
    provider: 'None'
    enterpriseGradeCdnStatus: 'Enabled' // Use built-in CDN
    buildProperties: {
      appLocation: '/'
      apiLocation: '' // No API in Static Web App, using external Functions
      outputLocation: 'dist'
    }
  }
}

// Custom domain configuration (if provided)
resource staticWebAppCustomDomain 'Microsoft.Web/staticSites/customDomains@2023-12-01' = if (!empty(customDomain)) {
  parent: staticWebApp
  name: customDomain
  properties: {}
}

// =============================================================================
// ENHANCED SECURITY CONFIGURATION
// =============================================================================

// Function App - Enable detailed monitoring
resource functionAppDiagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'sutra-api-diagnostics'
  scope: functionApp
  properties: {
    workspaceId: logAnalyticsWorkspace.id
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

// Application Insights alerts for unusual activity
resource highErrorRateAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: 'sutra-high-error-rate'
  location: 'global'
  tags: tags
  properties: {
    description: 'Alert when error rate exceeds 5% for small team'
    severity: 2
    enabled: true
    scopes: [
      applicationInsights.id
    ]
    evaluationFrequency: 'PT1M'
    windowSize: 'PT5M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'High Error Rate'
          metricName: 'requests/failed'
          dimensions: []
          operator: 'GreaterThan'
          threshold: 5
          timeAggregation: 'Count'
          criterionType: 'StaticThresholdCriterion'
        }
      ]
    }
    actions: []
  }
}

resource highLatencyAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: 'sutra-high-latency'
  location: 'global'
  tags: tags
  properties: {
    description: 'Alert when response time exceeds 2 seconds'
    severity: 2
    enabled: true
    scopes: [
      applicationInsights.id
    ]
    evaluationFrequency: 'PT1M'
    windowSize: 'PT5M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'High Latency'
          metricName: 'requests/duration'
          dimensions: []
          operator: 'GreaterThan'
          threshold: 2000
          timeAggregation: 'Average'
          criterionType: 'StaticThresholdCriterion'
        }
      ]
    }
    actions: []
  }
}

// =============================================================================
// KEY VAULT ACCESS POLICIES
// Note: Key Vault is in sutra-db-rg, access policy will be set separately
// =============================================================================

// =============================================================================
// OUTPUTS
// =============================================================================

@description('Function App name')
output functionAppName string = functionApp.name

@description('Function App URL (direct access)')
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'

@description('Function App API base URL')
output apiBaseUrl string = 'https://${functionApp.properties.defaultHostName}/api'

@description('Static Web App name')
output staticWebAppName string = staticWebApp.name

@description('Static Web App URL')
output staticWebAppUrl string = 'https://${staticWebApp.properties.defaultHostname}'

@description('Static Web App default hostname')
output staticWebAppHostname string = staticWebApp.properties.defaultHostname

@description('Application Insights name')
output applicationInsightsName string = applicationInsights.name

@description('Application Insights Instrumentation Key')
output applicationInsightsInstrumentationKey string = applicationInsights.properties.InstrumentationKey

@description('Application Insights Connection String')
output applicationInsightsConnectionString string = applicationInsights.properties.ConnectionString

@description('Resource Group ID for compute resources')
output resourceGroupId string = resourceGroup().id

@description('Architecture type')
output architectureType string = 'direct-access'
