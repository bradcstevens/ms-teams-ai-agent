// Azure OpenAI Service Module
// Task 1.5: AI Services Bicep Module
// Creates Azure OpenAI account with GPT-4 deployment and managed identity authentication

@description('Name of the Azure OpenAI account')
@minLength(2)
@maxLength(64)
param openAiAccountName string

@description('Azure region for OpenAI service (must support GPT-4)')
param location string

@description('Resource tags for organization and cost tracking')
param tags object = {}

@description('Azure OpenAI SKU')
@allowed([
  'S0'
])
param sku string = 'S0'

@description('Model name for deployment (e.g., gpt-4, gpt-35-turbo)')
param modelName string = 'gpt-4'

@description('Model version')
param modelVersion string = '0613'

@description('Deployment name for the model')
param deploymentName string = modelName

@description('Model capacity in thousands of tokens per minute')
@minValue(1)
@maxValue(1000)
param modelCapacity int = 10

@description('Public network access setting')
@allowed([
  'Enabled'
  'Disabled'
])
param publicNetworkAccess string = 'Enabled'

// ============================================================================
// AZURE OPENAI ACCOUNT
// ============================================================================

resource openAiAccount 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: openAiAccountName
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: sku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: openAiAccountName
    publicNetworkAccess: publicNetworkAccess
    networkAcls: {
      defaultAction: 'Allow'
      // Premium features (deferred to post-MVP)
      // ipRules: []
      // virtualNetworkRules: []
    }
  }
}

// ============================================================================
// MODEL DEPLOYMENT
// ============================================================================

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openAiAccount
  name: deploymentName
  sku: {
    name: 'Standard'
    capacity: modelCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
    raiPolicyName: 'Microsoft.Default'
  }
}

// ============================================================================
// OUTPUTS
// ============================================================================

@description('Azure OpenAI account resource ID')
output openAiAccountId string = openAiAccount.id

@description('Azure OpenAI account name')
output openAiAccountName string = openAiAccount.name

@description('Azure OpenAI service endpoint URL')
output endpoint string = openAiAccount.properties.endpoint

@description('Azure OpenAI model deployment name')
output deploymentName string = modelDeployment.name

@description('Azure OpenAI system-assigned managed identity principal ID')
output identityPrincipalId string = openAiAccount.identity.principalId

@description('Azure OpenAI account endpoint (alternative output name)')
output openAiEndpoint string = openAiAccount.properties.endpoint

@description('Azure OpenAI deployment name (alternative output name)')
output openAiDeploymentName string = modelDeployment.name
