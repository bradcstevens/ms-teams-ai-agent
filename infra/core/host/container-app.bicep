// Azure Container App Module
// Creates Container App with HTTPS ingress and container image configuration

@description('Name of the Container App')
@minLength(2)
@maxLength(32)
param containerAppName string

@description('Azure region for the container app')
param location string = resourceGroup().location

@description('Resource tags for organization and cost tracking')
param tags object = {}

@description('Container Apps Environment resource ID')
param containerAppsEnvironmentId string

@description('Container Registry name for image pulling')
param containerRegistryName string

@description('Container image name (with tag)')
param containerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Target port for container ingress')
param targetPort int = 3978

@description('Minimum number of replicas')
@minValue(0)
@maxValue(30)
param minReplicas int = 1

@description('Maximum number of replicas')
@minValue(1)
@maxValue(30)
param maxReplicas int = 3

@description('CPU cores allocated to container')
param cpuCores string = '0.5'

@description('Memory allocated to container')
param memorySize string = '1Gi'

@description('Environment variables for the container')
param environmentVariables array = []

@description('MCP server configurations (transformed from main.bicep)')
param mcpServers array = []

// ============================================================================
// VARIABLES
// ============================================================================

// Build MCP environment variables from server configurations
// Format: MCP_SERVER_<index>_NAME, MCP_SERVER_<index>_COMMAND, MCP_SERVER_<index>_ARGS
// Note: We manually build env vars for each server to avoid nested for-expressions
var mcpEnvVarsName = [for (server, i) in mcpServers: {
  name: 'MCP_SERVER_${i}_NAME'
  value: server.name
}]

var mcpEnvVarsCommand = [for (server, i) in mcpServers: {
  name: 'MCP_SERVER_${i}_COMMAND'
  value: server.command
}]

var mcpEnvVarsArgs = [for (server, i) in mcpServers: {
  name: 'MCP_SERVER_${i}_ARGS'
  value: string(server.args)
}]

// Build MCP_SERVER_COUNT to indicate how many servers are configured
var mcpCountEnvVar = empty(mcpServers) ? [] : [
  {
    name: 'MCP_SERVER_COUNT'
    value: string(length(mcpServers))
  }
]

// Build environment variable entries for server 0's env settings
var mcpServer0Env = length(mcpServers) > 0 ? mcpServers[0].env : {}
var mcpEnvVarsEnv0 = [for envKey in items(mcpServer0Env): {
  name: 'MCP_SERVER_0_ENV_${envKey.key}'
  value: string(envKey.value)
}]

// Build environment variable entries for server 1's env settings
var mcpServer1Env = length(mcpServers) > 1 ? mcpServers[1].env : {}
var mcpEnvVarsEnv1 = [for envKey in items(mcpServer1Env): {
  name: 'MCP_SERVER_1_ENV_${envKey.key}'
  value: string(envKey.value)
}]

// Build environment variable entries for server 2's env settings
var mcpServer2Env = length(mcpServers) > 2 ? mcpServers[2].env : {}
var mcpEnvVarsEnv2 = [for envKey in items(mcpServer2Env): {
  name: 'MCP_SERVER_2_ENV_${envKey.key}'
  value: string(envKey.value)
}]

// Combine all MCP environment variables (supports up to 3 MCP servers)
var mcpEnvVarsBase = concat(concat(mcpEnvVarsName, mcpEnvVarsCommand), mcpEnvVarsArgs)
var mcpEnvVarsWithEnv = concat(concat(concat(mcpEnvVarsBase, mcpEnvVarsEnv0), mcpEnvVarsEnv1), mcpEnvVarsEnv2)
var mcpEnvVars = concat(mcpCountEnvVar, mcpEnvVarsWithEnv)

// Combine with existing environment variables
var combinedEnvVars = concat(environmentVariables, mcpEnvVars)

// ============================================================================
// EXISTING RESOURCES
// ============================================================================

// Reference existing Container Registry for credentials
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: containerRegistryName
}

// ============================================================================
// CONTAINER APP
// ============================================================================

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironmentId
    configuration: {
      ingress: {
        external: true
        targetPort: targetPort
        transport: 'auto'
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          username: containerRegistry.listCredentials().username
          passwordSecretRef: 'registry-password'
        }
      ]
      secrets: [
        {
          name: 'registry-password'
          value: containerRegistry.listCredentials().passwords[0].value
        }
      ]
    }
    template: {
      containers: [
        {
          name: containerAppName
          image: containerImage
          resources: {
            cpu: json(cpuCores)
            memory: memorySize
          }
          env: combinedEnvVars
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// ============================================================================
// OUTPUTS
// ============================================================================

@description('Container App resource ID')
output containerAppId string = containerApp.id

@description('Container App name')
output containerAppName string = containerApp.name

@description('Container App fully qualified domain name')
output containerAppFqdn string = containerApp.properties.configuration.ingress.fqdn

@description('Container App HTTPS endpoint URL')
output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'

@description('Container App system-assigned managed identity principal ID')
output identityPrincipalId string = containerApp.identity.principalId

@description('Container App FQDN for output compatibility')
output fqdn string = containerApp.properties.configuration.ingress.fqdn
