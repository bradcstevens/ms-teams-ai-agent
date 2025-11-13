// Azure Container Registry Module
// Task 1.4: Container Infrastructure Bicep Module
// Creates Azure Container Registry with admin credentials for container image storage

@description('Name of the Azure Container Registry (alphanumeric only, globally unique)')
@minLength(5)
@maxLength(50)
param containerRegistryName string

@description('Azure region for the container registry')
param location string = resourceGroup().location

@description('Resource tags for organization and cost tracking')
param tags object = {}

@description('Container Registry SKU')
@allowed([
  'Basic'
  'Standard'
  'Premium'
])
param sku string = 'Basic'

@description('Enable admin user for registry authentication')
param adminUserEnabled bool = true

// ============================================================================
// AZURE CONTAINER REGISTRY
// ============================================================================

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: containerRegistryName
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: adminUserEnabled
    publicNetworkAccess: 'Enabled'
    // Premium SKU features (deferred to post-MVP)
    // - zoneRedundancy: 'Enabled'
    // - networkRuleSet: {}
    // - encryption: {}
  }
}

// ============================================================================
// OUTPUTS
// ============================================================================

@description('Container Registry resource ID')
output containerRegistryId string = containerRegistry.id

@description('Container Registry name')
output containerRegistryName string = containerRegistry.name

@description('Container Registry login server URL')
output loginServer string = containerRegistry.properties.loginServer

@description('Container Registry resource name for module references')
output name string = containerRegistry.name
