// Application Insights Module
// Task 1.3: Networking & Environment Bicep Module
// Provides application performance monitoring and telemetry for the AI agent

@description('Name of the Application Insights resource')
@minLength(1)
@maxLength(255)
param name string

@description('Azure region for Application Insights')
param location string = resourceGroup().location

@description('Tags to apply to the Application Insights resource')
param tags object = {}

@description('Resource ID of the Log Analytics Workspace to link to')
param workspaceId string

@description('Application type for Application Insights')
@allowed([
  'web'
  'other'
])
param applicationType string = 'web'

@description('Ingestion mode for Application Insights')
@allowed([
  'LogAnalytics'
  'ApplicationInsights'
  'ApplicationInsightsWithDiagnosticSettings'
])
param ingestionMode string = 'LogAnalytics'

@description('Data retention period in days')
@minValue(30)
@maxValue(730)
param retentionInDays int = 90

// ============================================================================
// APPLICATION INSIGHTS
// ============================================================================

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: name
  location: location
  tags: tags
  kind: applicationType
  properties: {
    Application_Type: applicationType
    WorkspaceResourceId: workspaceId
    IngestionMode: ingestionMode
    RetentionInDays: retentionInDays
    publicNetworkAccessForIngestion: 'Enabled'  // Public ingress for MVP
    publicNetworkAccessForQuery: 'Enabled'
    DisableIpMasking: false  // Enable IP masking for privacy
    DisableLocalAuth: false  // Allow connection string auth for MVP
  }
}

// ============================================================================
// OUTPUTS
// ============================================================================

@description('Resource ID of Application Insights')
output id string = applicationInsights.id

@description('Name of Application Insights resource')
output name string = applicationInsights.name

@description('Application Insights connection string')
output connectionString string = applicationInsights.properties.ConnectionString

@description('Application Insights instrumentation key')
output instrumentationKey string = applicationInsights.properties.InstrumentationKey
