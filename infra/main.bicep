// Azure Infrastructure as Code - Main Bicep Template
// Task 1.2: Core Bicep Infrastructure Module (main.bicep)
// Azure AI Agent Framework for Microsoft Teams - MVP
// Orchestrates all infrastructure modules for Container Apps, Azure OpenAI, Bot Service, and monitoring

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

@description('Azure OpenAI service region (must support GPT-4)')
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
param openAiModelName string = 'gpt-4'

@description('Azure OpenAI model version')
param openAiModelVersion string = '0613'

@description('Display name for the Teams bot')
@minLength(1)
@maxLength(256)
param botDisplayName string = 'AI Agent for Teams'

@description('Current timestamp for deployment tracking')
param deploymentTimestamp string = utcNow()

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
// These modules will be implemented in subsequent tasks (1.3-1.7)
// Module structure is defined here to establish dependency graph

// Task 1.3: Networking & Environment Module
// Log Analytics Workspace and Container Apps Environment
// module monitoring './core/monitor/monitoring.bicep' = {
//   name: 'monitoring-${resourceToken}'
//   scope: rg
//   params: {
//     logAnalyticsName: '${abbrs.logAnalytics}-${environmentName}-${resourceToken}'
//     applicationInsightsName: '${abbrs.appInsights}-${environmentName}-${resourceToken}'
//     location: location
//     tags: tags
//   }
// }

// module containerAppsEnvironment './core/host/container-apps-environment.bicep' = {
//   name: 'container-env-${resourceToken}'
//   scope: rg
//   params: {
//     containerAppsEnvironmentName: '${abbrs.containerAppsEnvironment}-${environmentName}-${resourceToken}'
//     logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
//     location: location
//     tags: tags
//   }
// }

// Task 1.4: Container Infrastructure Module
// Azure Container Registry and Container App
// module containerRegistry './core/host/container-registry.bicep' = {
//   name: 'registry-${resourceToken}'
//   scope: rg
//   params: {
//     containerRegistryName: '${abbrs.containerRegistry}${replace(environmentName, '-', '')}${resourceToken}'
//     location: location
//     tags: tags
//   }
// }

// module containerApp './core/host/container-app.bicep' = {
//   name: 'container-app-${resourceToken}'
//   scope: rg
//   params: {
//     containerAppName: '${abbrs.containerApps}-${environmentName}-${resourceToken}'
//     containerAppsEnvironmentId: containerAppsEnvironment.outputs.containerAppsEnvironmentId
//     containerRegistryName: containerRegistry.outputs.containerRegistryName
//     location: location
//     tags: tags
//   }
//   dependsOn: [
//     containerAppsEnvironment
//     containerRegistry
//   ]
// }

// Task 1.5: AI Services Module
// Azure OpenAI Service with GPT-4 deployment
// module openAi './ai/openai.bicep' = {
//   name: 'openai-${resourceToken}'
//   scope: rg
//   params: {
//     openAiAccountName: '${abbrs.openAiAccount}-${environmentName}-${resourceToken}'
//     location: openAiLocation
//     modelName: openAiModelName
//     modelVersion: openAiModelVersion
//     tags: tags
//   }
// }

// Task 1.6: Bot Service & Security Module
// Azure Bot Service and Key Vault
// module botService './bot/bot-service.bicep' = {
//   name: 'bot-${resourceToken}'
//   scope: rg
//   params: {
//     botName: '${abbrs.botService}-${environmentName}-${resourceToken}'
//     botDisplayName: botDisplayName
//     botEndpoint: 'https://${containerApp.outputs.containerAppFqdn}/api/messages'
//     location: 'global'
//     tags: tags
//   }
//   dependsOn: [
//     containerApp
//   ]
// }

// module keyVault './security/key-vault.bicep' = {
//   name: 'keyvault-${resourceToken}'
//   scope: rg
//   params: {
//     keyVaultName: '${abbrs.keyVault}-${environmentName}-${resourceToken}'
//     location: location
//     principalId: principalId
//     tags: tags
//   }
// }

// ============================================================================
// OUTPUTS
// ============================================================================
// These outputs map to environment variables in azure.yaml
// They will be populated when modules are implemented in subsequent tasks

@description('Azure OpenAI service endpoint URL')
output AZURE_OPENAI_ENDPOINT string = 'https://placeholder-openai-endpoint.openai.azure.com/'
// Future: output AZURE_OPENAI_ENDPOINT string = openAi.outputs.endpoint

@description('Azure OpenAI GPT-4 deployment name')
output AZURE_OPENAI_DEPLOYMENT_NAME string = openAiModelName
// Future: output AZURE_OPENAI_DEPLOYMENT_NAME string = openAi.outputs.deploymentName

@description('Azure Bot Service application ID')
output BOT_ID string = 'placeholder-bot-id'
// Future: output BOT_ID string = botService.outputs.botId

@description('Key Vault name for secrets storage')
output KEY_VAULT_NAME string = '${abbrs.keyVault}-${environmentName}-${resourceToken}'
// Future: output KEY_VAULT_NAME string = keyVault.outputs.keyVaultName

@description('Application Insights connection string')
output APPLICATIONINSIGHTS_CONNECTION_STRING string = 'InstrumentationKey=placeholder-key'
// Future: output APPLICATIONINSIGHTS_CONNECTION_STRING string = monitoring.outputs.applicationInsightsConnectionString

@description('Azure Container Registry login server endpoint')
output CONTAINER_REGISTRY_ENDPOINT string = '${abbrs.containerRegistry}${replace(environmentName, '-', '')}${resourceToken}.azurecr.io'
// Future: output CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.outputs.loginServer

@description('Container App name for the API service')
output CONTAINER_APP_NAME string = '${abbrs.containerApps}-${environmentName}-${resourceToken}'
// Future: output CONTAINER_APP_NAME string = containerApp.outputs.containerAppName

@description('Container Apps Environment name')
output CONTAINER_APP_ENVIRONMENT_NAME string = '${abbrs.containerAppsEnvironment}-${environmentName}-${resourceToken}'
// Future: output CONTAINER_APP_ENVIRONMENT_NAME string = containerAppsEnvironment.outputs.containerAppsEnvironmentName

@description('Resource group name for all resources')
output AZURE_RESOURCE_GROUP string = resourceGroupName

@description('Azure region where resources are deployed')
output AZURE_LOCATION string = location

@description('Unique resource token for naming')
output RESOURCE_TOKEN string = resourceToken
