// Log Analytics Workspace Module
// Task 1.3: Networking & Environment Bicep Module
// Provides centralized logging infrastructure for Container Apps and Application Insights

@description('Name of the Log Analytics Workspace')
@minLength(4)
@maxLength(63)
param name string

@description('Azure region for the Log Analytics Workspace')
param location string = resourceGroup().location

@description('Tags to apply to the Log Analytics Workspace')
param tags object = {}

@description('Workspace retention period in days')
@minValue(30)
@maxValue(730)
param retentionInDays int = 30

@description('Pricing tier for the workspace')
@allowed([
  'PerGB2018'
  'Free'
  'Standalone'
  'PerNode'
  'Premium'
])
param sku string = 'PerGB2018'

// ============================================================================
// LOG ANALYTICS WORKSPACE
// ============================================================================

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      name: sku
    }
    retentionInDays: retentionInDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    workspaceCapping: {
      dailyQuotaGb: -1  // No daily cap for MVP
    }
    publicNetworkAccessForIngestion: 'Enabled'  // Public ingress for MVP
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// ============================================================================
// OUTPUTS
// ============================================================================

@description('Resource ID of the Log Analytics Workspace')
output workspaceId string = logAnalyticsWorkspace.id

@description('Customer ID (Workspace ID) for Log Analytics')
output customerId string = logAnalyticsWorkspace.properties.customerId

@description('Primary shared key for Log Analytics (for Container Apps Environment)')
@secure()
output primarySharedKey string = logAnalyticsWorkspace.listKeys().primarySharedKey

@description('Name of the Log Analytics Workspace')
output workspaceName string = logAnalyticsWorkspace.name
