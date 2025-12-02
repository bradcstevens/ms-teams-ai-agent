// Azure Bot Service Module
// Creates Azure Bot Service with Teams channel integration

@description('Name of the Azure Bot Service')
@minLength(2)
@maxLength(64)
param botName string

@description('Display name for the bot')
@minLength(1)
@maxLength(256)
param botDisplayName string

@description('Bot endpoint URL for receiving messages')
param botEndpoint string

@description('Azure region for bot service (note: Bot Service uses global)')
param location string = 'global'

@description('Resource tags for organization and cost tracking')
param tags object = {}

@description('Bot SKU')
@allowed([
  'F0'  // Free tier
  'S1'  // Standard tier
])
param sku string = 'F0'

@description('Microsoft App ID (MSI) for the bot')
param microsoftAppId string = ''

@description('Microsoft App Tenant ID for SingleTenant auth')
param microsoftAppTenantId string = ''

@description('Bot authentication type - MultiTenant deprecated as of 2025')
@allowed([
  'SingleTenant'
  'UserAssignedMSI'
])
param microsoftAppType string = 'SingleTenant'

// ============================================================================
// BOT SERVICE
// ============================================================================

resource botService 'Microsoft.BotService/botServices@2022-09-15' = {
  name: botName
  location: location
  tags: tags
  sku: {
    name: sku
  }
  kind: 'azurebot'
  properties: {
    displayName: botDisplayName
    endpoint: botEndpoint
    msaAppId: microsoftAppId
    msaAppType: microsoftAppType
    msaAppTenantId: microsoftAppTenantId
    // Microsoft Teams specific configuration
    schemaTransformationVersion: '1.3'

    // Post-MVP: Advanced features
    // publicNetworkAccess: 'Enabled'
    // isStreamingSupported: true
    // developerAppInsightKey: appInsightsKey
    // developerAppInsightsApiKey: appInsightsApiKey
    // developerAppInsightsApplicationId: appInsightsAppId
  }
}

// ============================================================================
// MICROSOFT TEAMS CHANNEL
// ============================================================================

resource teamsChannel 'Microsoft.BotService/botServices/channels@2022-09-15' = {
  parent: botService
  name: 'MsTeamsChannel'
  location: location
  properties: {
    channelName: 'MsTeamsChannel'
    properties: {
      enableCalling: false
      isEnabled: true
      // Post-MVP: Advanced Teams features
      // incomingCallRoute: 'ChatBot'
      // acceptedTerms: true
    }
  }
}

// ============================================================================
// OUTPUTS
// ============================================================================

@description('Bot Service resource ID')
output botServiceId string = botService.id

@description('Bot Service name')
output botServiceName string = botService.name

@description('Microsoft App ID for the bot')
output botId string = botService.properties.msaAppId

@description('Bot endpoint URL')
output botEndpoint string = botService.properties.endpoint

@description('Teams channel resource ID')
output teamsChannelId string = teamsChannel.id
