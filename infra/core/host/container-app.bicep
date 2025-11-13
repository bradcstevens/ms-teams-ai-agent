// Azure Container App Module
// Task 1.4: Container Infrastructure Bicep Module
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
          env: environmentVariables
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
