// Azure Infrastructure as Code - Main Bicep Template
// Azure AI Agent Framework for Microsoft Teams - MVP
// Orchestrates all infrastructure modules for Container Apps, Azure OpenAI, Bot Service, and monitoring
//
// Security Note: For production deployments, consider adding:
// - Azure Front Door with WAF policy for DDoS protection and global load balancing
// - Application Gateway with WAF for regional deployments
// - See docs/ARCHITECTURE.md for security enhancement options

targetScope = 'subscription'

// ============================================================================
// PARAMETERS
// ============================================================================

@description('Environment name identifier (e.g., dev, test, prod)')
@minLength(1)
@maxLength(64)
param environmentName string

@description('Primary Azure region for resources')
param location string = deployment().location

@description('Service principal ID for RBAC assignments (leave empty for interactive deployments)')
param principalId string = ''

@description('Principal type for RBAC role assignments')
@allowed([
  'User'
  'Group'
  'ServicePrincipal'
])
param principalType string = 'User'

@description('Azure OpenAI service region (must support GPT-5)')
@allowed([
  'eastus'
  'eastus2'
  'southcentralus'
  'westus'
  'westus3'
  'australiaeast'
  'canadaeast'
  'francecentral'
  'japaneast'
  'northcentralus'
  'swedencentral'
  'switzerlandnorth'
  'uksouth'
])
param openAiLocation string = 'eastus'

@description('Azure OpenAI model name for deployment')
param openAiModelName string = 'gpt-5'

@description('Azure OpenAI model version')
param openAiModelVersion string = '2024-08-06'

@description('Display name for the Teams bot')
@minLength(1)
@maxLength(256)
param botDisplayName string = 'AI Agent for Teams'

@description('Bot App Registration ID (leave empty to skip bot service deployment)')
param botAppId string = ''

@description('Bot App Tenant ID for SingleTenant auth')
param botTenantId string = ''

@description('Current timestamp for deployment tracking')
param deploymentTimestamp string = utcNow()

@description('MCP server configurations as JSON array (optional)')
param mcpServers array = []

// ============================================================================
// VARIABLES
// ============================================================================

// Resource abbreviations following Azure naming conventions
var abbrs = {
  resourceGroup: 'rg'
  containerAppsEnvironment: 'cae'
  containerApps: 'ca'
  containerRegistry: 'cr'
  openAiAccount: 'oai'
  botService: 'bot'
  keyVault: 'kv'
  logAnalytics: 'log'
  appInsights: 'appi'
}

// Generate unique resource token from subscription, environment, and location
// This ensures globally unique names across deployments
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))

// Resource naming convention: abbr-projectname-env-token
var resourceGroupName = '${abbrs.resourceGroup}-${environmentName}-${resourceToken}'

// Tags applied to all resources for organization and cost tracking
var tags = {
  'azd-env-name': environmentName
  project: 'azure-ai-agent-teams'
  purpose: 'AI agent framework MVP'
  'deployment-method': 'azd'
  'deployment-timestamp': deploymentTimestamp
}

// Transform MCP servers array - ensure required fields exist with defaults
// Each server gets: MCP_SERVER_<index>_NAME, MCP_SERVER_<index>_COMMAND, MCP_SERVER_<index>_ARGS, MCP_SERVER_<index>_ENV_*
var mcpEnvironmentVariables = [for server in mcpServers: {
  name: contains(server, 'name') ? server.name : 'unnamed-server'
  command: contains(server, 'command') ? server.command : ''
  args: contains(server, 'args') ? server.args : []
  env: contains(server, 'env') ? server.env : {}
}]

// ============================================================================
// RESOURCE GROUP
// ============================================================================

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

// ============================================================================
// MODULE ORCHESTRATION
// ============================================================================

// Log Analytics Workspace for centralized logging
module logAnalytics './core/monitor/loganalytics.bicep' = {
  name: 'loganalytics-${resourceToken}'
  scope: rg
  params: {
    name: '${abbrs.logAnalytics}-${environmentName}-${resourceToken}'
    location: location
    tags: tags
    retentionInDays: 30
    sku: 'PerGB2018'
  }
}

// Application Insights for application monitoring and telemetry
module applicationInsights './core/monitor/applicationinsights.bicep' = {
  name: 'appinsights-${resourceToken}'
  scope: rg
  params: {
    name: '${abbrs.appInsights}-${environmentName}-${resourceToken}'
    location: location
    tags: tags
    workspaceId: logAnalytics.outputs.workspaceId
    applicationType: 'web'
    retentionInDays: 90
  }
}

// Container Apps Environment with public ingress (VNet deferred to post-MVP)
module containerAppsEnvironment './core/host/container-apps-environment.bicep' = {
  name: 'container-env-${resourceToken}'
  scope: rg
  params: {
    name: '${abbrs.containerAppsEnvironment}-${environmentName}-${resourceToken}'
    location: location
    tags: tags
    logAnalyticsCustomerId: logAnalytics.outputs.customerId
    logAnalyticsPrimarySharedKey: logAnalytics.outputs.primarySharedKey
    zoneRedundant: 'Disabled'
  }
}

// Azure Container Registry and Container App
module containerRegistry './core/host/container-registry.bicep' = {
  name: 'registry-${resourceToken}'
  scope: rg
  params: {
    containerRegistryName: '${abbrs.containerRegistry}${replace(environmentName, '-', '')}${resourceToken}'
    location: location
    tags: tags
  }
}

module containerApp './core/host/container-app.bicep' = {
  name: 'container-app-${resourceToken}'
  scope: rg
  params: {
    containerAppName: '${abbrs.containerApps}-${environmentName}-${resourceToken}'
    containerAppsEnvironmentId: containerAppsEnvironment.outputs.id
    containerRegistryName: containerRegistry.outputs.containerRegistryName
    location: location
    tags: union(tags, { 'azd-service-name': 'api' })
    targetPort: 8000
    mcpServers: mcpEnvironmentVariables
  }
  dependsOn: [
    containerAppsEnvironment
    containerRegistry
  ]
}

// Azure OpenAI Service with GPT-5 deployment
module openAi './ai/openai.bicep' = {
  name: 'openai-${resourceToken}'
  scope: rg
  params: {
    openAiAccountName: '${abbrs.openAiAccount}-${environmentName}-${resourceToken}'
    location: openAiLocation
    modelName: openAiModelName
    modelVersion: openAiModelVersion
    tags: tags
  }
}

// Azure Bot Service and Key Vault
// Bot Service is only deployed when botAppId is provided
// For MVP: Run create-bot-registration.sh first, then redeploy with botAppId
module botService './bot/bot-service.bicep' = if (!empty(botAppId)) {
  name: 'bot-${resourceToken}'
  scope: rg
  params: {
    botName: '${abbrs.botService}-${environmentName}-${resourceToken}'
    botDisplayName: botDisplayName
    botEndpoint: 'https://${containerApp.outputs.containerAppFqdn}/api/messages'
    microsoftAppId: botAppId
    microsoftAppTenantId: botTenantId
    location: 'global'
    tags: tags
  }
  dependsOn: [
    containerApp
  ]
}

module keyVault './security/key-vault.bicep' = {
  name: 'keyvault-${resourceToken}'
  scope: rg
  params: {
    // Key Vault names max 24 chars, so use shortened format: kv-<resourceToken>
    keyVaultName: '${abbrs.keyVault}-${resourceToken}'
    location: location
    principalId: principalId
    principalType: principalType
    tags: tags
  }
}

// ============================================================================
// OUTPUTS
// ============================================================================
// These outputs map to environment variables in azure.yaml

@description('Azure OpenAI service endpoint URL')
output AZURE_OPENAI_ENDPOINT string = openAi.outputs.endpoint

@description('Azure OpenAI GPT-5 deployment name')
output AZURE_OPENAI_DEPLOYMENT_NAME string = openAi.outputs.deploymentName

@description('Azure Bot Service application ID')
output BOT_ID string = !empty(botAppId) ? botService.outputs.botId : ''

@description('Bot tenant ID for SingleTenant authentication')
output BOT_TENANT_ID string = botTenantId

@description('Key Vault name for secrets storage')
output KEY_VAULT_NAME string = keyVault.outputs.keyVaultName

@description('Key Vault URI')
output KEY_VAULT_URI string = keyVault.outputs.keyVaultUri

@description('Application Insights connection string')
output APPLICATIONINSIGHTS_CONNECTION_STRING string = applicationInsights.outputs.connectionString

@description('Azure Container Registry login server endpoint')
output CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.outputs.loginServer

@description('Azure Container Registry endpoint for azd')
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.outputs.loginServer

@description('Azure Container Registry name')
output CONTAINER_REGISTRY_NAME string = containerRegistry.outputs.containerRegistryName

@description('Container App name for the API service')
output CONTAINER_APP_NAME string = containerApp.outputs.containerAppName

@description('Container App name for azd service mapping (api service)')
output SERVICE_API_NAME string = containerApp.outputs.containerAppName

@description('Container App URL')
output CONTAINER_APP_URL string = containerApp.outputs.containerAppUrl

@description('Container App FQDN')
output CONTAINER_APP_FQDN string = containerApp.outputs.containerAppFqdn

@description('Container Apps Environment name')
output CONTAINER_APP_ENVIRONMENT_NAME string = containerAppsEnvironment.outputs.name

@description('Resource group name for all resources')
output AZURE_RESOURCE_GROUP string = resourceGroupName

@description('Azure region where resources are deployed')
output AZURE_LOCATION string = location

@description('Azure OpenAI region where OpenAI service is deployed')
output AZURE_OPENAI_LOCATION string = openAiLocation

@description('Unique resource token for naming')
output RESOURCE_TOKEN string = resourceToken
