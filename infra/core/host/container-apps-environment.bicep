// Container Apps Environment Module
// Task 1.3: Networking & Environment Bicep Module
// Provides serverless container hosting environment with public ingress (VNet deferred to post-MVP)

@description('Name of the Container Apps Environment')
@minLength(2)
@maxLength(64)
param name string

@description('Azure region for the Container Apps Environment')
param location string = resourceGroup().location

@description('Tags to apply to the Container Apps Environment')
param tags object = {}

@description('Customer ID of the Log Analytics Workspace')
param logAnalyticsCustomerId string

@description('Primary shared key of the Log Analytics Workspace')
@secure()
param logAnalyticsPrimarySharedKey string

@description('Zone redundancy mode for high availability')
@allowed([
  'Disabled'
  'Enabled'
])
param zoneRedundant string = 'Disabled'  // Disabled for MVP to reduce costs

// ============================================================================
// CONTAINER APPS ENVIRONMENT
// ============================================================================

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    // Log Analytics configuration
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsPrimarySharedKey
      }
    }

    // Dapr configuration (optional)
    daprAIInstrumentationKey: null
    daprAIConnectionString: null

    // Zone redundancy
    zoneRedundant: zoneRedundant == 'Enabled'

    // VNet configuration (deferred to post-MVP)
    // vnetConfiguration is optional - omit for public ingress MVP
  }
}

// ============================================================================
// OUTPUTS
// ============================================================================

@description('Resource ID of the Container Apps Environment')
output id string = containerAppsEnvironment.id

@description('Name of the Container Apps Environment')
output name string = containerAppsEnvironment.name

@description('Default domain for Container Apps in this environment')
output defaultDomain string = containerAppsEnvironment.properties.defaultDomain

@description('Static IP address of the Container Apps Environment')
output staticIp string = containerAppsEnvironment.properties.staticIp
