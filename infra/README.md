# Infrastructure Documentation

Azure Infrastructure as Code (IaC) for the Azure AI Agent Framework for Microsoft Teams. Built with Bicep templates and designed for Azure Developer CLI (azd) deployment.

## Overview

This directory contains Bicep templates that define all Azure infrastructure required for the AI agent framework:

- **Azure Container Apps**: Serverless container hosting for the FastAPI bot application
- **Azure OpenAI Service**: GPT-4 model deployment for AI capabilities
- **Azure Bot Service**: Microsoft Teams integration and bot registration
- **Azure Container Registry**: Container image storage and management
- **Azure Key Vault**: Secure secrets and configuration management
- **Application Insights**: Application performance monitoring and telemetry
- **Log Analytics Workspace**: Centralized logging infrastructure

## Architecture

### Deployment Scope

The main template uses **subscription-level** deployment (`targetScope = 'subscription'`) to create:
1. Resource group with standardized naming and tagging
2. All Azure resources within the resource group via modular Bicep files

### Resource Dependencies

```
Resource Group (rg)
├── Log Analytics Workspace (Task 1.3)
├── Application Insights (Task 1.3)
│   └── depends on: Log Analytics
├── Container Apps Environment (Task 1.3)
│   └── depends on: Log Analytics
├── Container Registry (Task 1.4)
├── Container App (Task 1.4)
│   └── depends on: Container Apps Environment, Container Registry
├── Azure OpenAI (Task 1.5)
├── Bot Service (Task 1.6)
│   └── depends on: Container App (for endpoint URL)
└── Key Vault (Task 1.6)
```

## File Structure

```
infra/
├── main.bicep                  # Main orchestration template (Task 1.2) ✅
├── main.parameters.json        # Parameter file template (Task 1.2) ✅
├── abbreviations.json          # Resource naming reference (Task 1.2) ✅
├── validate-bicep.sh           # Bicep validation test script (Task 1.2) ✅
├── README.md                   # This file (Task 1.2) ✅
│
├── core/                       # Core infrastructure modules
│   ├── host/
│   │   ├── container-apps-environment.bicep  # Task 1.3 ✅
│   │   ├── container-registry.bicep          # Task 1.4 ✅
│   │   └── container-app.bicep               # Task 1.4 ✅
│   └── monitor/
│       ├── loganalytics.bicep                # Task 1.3 ✅
│       └── applicationinsights.bicep         # Task 1.3 ✅
│
├── ai/
│   └── openai.bicep                          # Task 1.5 ✅
│
├── bot/
│   └── bot-service.bicep                     # Task 1.6 ✅
│
└── security/
    └── key-vault.bicep                       # Task 1.6 ✅
```

## Parameters

### Required Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `environmentName` | string | Environment identifier (dev/test/prod) | - (required) |

### Optional Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `location` | string | Primary Azure region | deployment().location |
| `principalId` | string | Service principal for RBAC | '' (empty) |
| `openAiLocation` | string | Azure OpenAI region | 'eastus' |
| `openAiModelName` | string | OpenAI model name | 'gpt-4' |
| `openAiModelVersion` | string | Model version | '0613' |
| `botDisplayName` | string | Teams bot display name | 'AI Agent for Teams' |

### Parameter File Usage

Parameters can be set via environment variables using the `main.parameters.json` template:

```bash
# Set environment variables
export AZURE_ENV_NAME="dev"
export AZURE_LOCATION="eastus"
export AZURE_OPENAI_LOCATION="eastus"

# azd will automatically substitute these during deployment
azd up
```

## Naming Conventions

All resources follow a standardized naming pattern:

```
{abbreviation}-{environment}-{resourceToken}
```

### Resource Token Generation

The resource token is generated using Bicep's `uniqueString()` function:

```bicep
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
```

This ensures:
- **Uniqueness**: Different subscriptions/environments/regions produce different tokens
- **Consistency**: Same inputs always produce the same token
- **Brevity**: Short alphanumeric string suitable for naming constraints

### Abbreviations

See `abbreviations.json` for the complete list. Key abbreviations:

- **rg**: Resource Group
- **cae**: Container Apps Environment
- **ca**: Container App
- **cr**: Container Registry
- **oai**: OpenAI Account
- **bot**: Bot Service
- **kv**: Key Vault
- **log**: Log Analytics Workspace
- **appi**: Application Insights

### Special Naming Considerations

1. **Container Registry**: Names cannot contain hyphens
   - Pattern: `{abbr}{environment}{resourceToken}` (no separators)
   - Example: `crdevabc123xyz`

2. **Key Vault**: Must be 3-24 characters, globally unique
   - Pattern: `{abbr}-{env}-{token}` (truncated if needed)
   - Example: `kv-dev-abc123xyz`

## Tagging Strategy

All resources are tagged with:

```bicep
{
  'azd-env-name': environmentName,
  'project': 'azure-ai-agent-teams',
  'purpose': 'AI agent framework MVP',
  'deployment-method': 'azd',
  'deployment-timestamp': deploymentTimestamp
}
```

Tags enable:
- **Cost tracking**: Filter billing by environment and project
- **Resource organization**: Identify resources by purpose
- **Deployment tracking**: Audit when resources were created
- **azd integration**: Required for `azd` resource management

## Outputs

The main template exposes outputs that map directly to environment variables in `azure.yaml`:

| Output | Description | Environment Variable |
|--------|-------------|---------------------|
| `AZURE_OPENAI_ENDPOINT` | OpenAI service URL | `AZURE_OPENAI_ENDPOINT` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | GPT-4 deployment name | `AZURE_OPENAI_DEPLOYMENT_NAME` |
| `BOT_ID` | Bot Service app ID | `BOT_ID` |
| `KEY_VAULT_NAME` | Key Vault name | `KEY_VAULT_NAME` |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | App Insights connection | `APPLICATIONINSIGHTS_CONNECTION_STRING` |
| `CONTAINER_REGISTRY_ENDPOINT` | ACR login server | - |
| `CONTAINER_APP_NAME` | Container App name | - |
| `CONTAINER_APP_ENVIRONMENT_NAME` | CAE name | - |
| `AZURE_RESOURCE_GROUP` | Resource group name | - |
| `AZURE_LOCATION` | Deployment region | - |

## Validation

### Bicep Compilation

Validate that Bicep templates compile without errors:

```bash
# Validate main template
az bicep build --file infra/main.bicep

# Validate specific module (when implemented)
az bicep build --file infra/core/host/container-app.bicep
```

### Template Validation (What-If)

Preview changes before deployment:

```bash
# Subscription-level what-if
az deployment sub what-if \
  --location eastus \
  --template-file infra/main.bicep \
  --parameters environmentName=dev
```

### Test Script

Run the comprehensive validation test suite:

```bash
./infra/validate-bicep.sh
```

This validates:
- Bicep file exists
- Compilation succeeds
- All required parameters defined
- All required outputs defined
- Tagging strategy implemented
- Resource naming conventions used
- No hardcoded values present

## Deployment

### Using Azure Developer CLI (Recommended)

```bash
# Initialize azd environment (first time only)
azd init

# Deploy infrastructure and application
azd up

# Deploy infrastructure changes only
azd provision

# View deployment outputs
azd env get-values
```

### Using Azure CLI Directly

```bash
# Deploy at subscription scope
az deployment sub create \
  --location eastus \
  --template-file infra/main.bicep \
  --parameters environmentName=dev

# Get deployment outputs
az deployment sub show \
  --name main \
  --query properties.outputs
```

## Task 1.3: Networking & Environment Modules (COMPLETED)

### Log Analytics Workspace (loganalytics.bicep)

**Purpose**: Centralized logging infrastructure for Container Apps and Application Insights.

**Parameters**:
- `name` (string): Name of the Log Analytics Workspace
- `location` (string): Azure region for deployment
- `tags` (object): Resource tags
- `retentionInDays` (int): Log retention period (default: 30 days, range: 30-730)
- `sku` (string): Pricing tier (default: 'PerGB2018')

**Outputs**:
- `workspaceId`: Resource ID for linking other resources
- `customerId`: Workspace ID for Container Apps Environment
- `primarySharedKey`: Shared key for Container Apps (marked as `@secure()`)
- `workspaceName`: Name of the workspace

**Configuration**:
- Public network access enabled for ingestion and query (MVP)
- No daily quota cap configured
- Resource-based permissions enabled

### Application Insights (applicationinsights.bicep)

**Purpose**: Application performance monitoring and telemetry for the AI agent.

**Parameters**:
- `name` (string): Name of the Application Insights resource
- `location` (string): Azure region for deployment
- `tags` (object): Resource tags
- `workspaceId` (string): Resource ID of Log Analytics Workspace
- `applicationType` (string): Application type (default: 'web')
- `retentionInDays` (int): Data retention period (default: 90 days, range: 30-730)

**Outputs**:
- `id`: Resource ID
- `name`: Resource name
- `connectionString`: Full connection string for SDK integration
- `instrumentationKey`: Legacy instrumentation key

**Configuration**:
- Linked to Log Analytics Workspace for unified logging
- Public network access enabled (MVP)
- IP masking enabled for privacy
- Connection string authentication enabled

### Container Apps Environment (container-apps-environment.bicep)

**Purpose**: Serverless container hosting environment with public ingress.

**Parameters**:
- `name` (string): Name of the Container Apps Environment
- `location` (string): Azure region for deployment
- `tags` (object): Resource tags
- `logAnalyticsCustomerId`: Customer ID from Log Analytics
- `logAnalyticsPrimarySharedKey`: Shared key from Log Analytics (marked as `@secure()`)
- `zoneRedundant` (string): Zone redundancy setting (default: 'Disabled' for MVP)

**Outputs**:
- `id`: Resource ID of the environment
- `name`: Name of the environment
- `defaultDomain`: Default domain for Container Apps
- `staticIp`: Static IP address assigned to the environment

**Configuration**:
- Public ingress (no VNet integration for MVP)
- Zone redundancy disabled for cost optimization
- Logs sent to Log Analytics Workspace
- Dapr disabled for MVP (can be enabled post-MVP)

### Dependency Chain

```
Log Analytics Workspace
      ↓
Application Insights (requires workspaceId)
      ↓
Container Apps Environment (requires customerId + sharedKey)
```

### Integration with main.bicep

The modules are orchestrated in main.bicep with proper dependency ordering:

```bicep
module logAnalytics './core/monitor/loganalytics.bicep' = { ... }
module applicationInsights './core/monitor/applicationinsights.bicep' = {
  // depends on: logAnalytics.outputs.workspaceId
}
module containerAppsEnvironment './core/host/container-apps-environment.bicep' = {
  // depends on: logAnalytics.outputs.customerId and primarySharedKey
}
```

**Output Mapping**:
- `APPLICATIONINSIGHTS_CONNECTION_STRING` → applicationInsights.outputs.connectionString
- `CONTAINER_APP_ENVIRONMENT_NAME` → containerAppsEnvironment.outputs.name

### Validation

All modules validated with 29 passing tests:
```bash
./validate-networking.sh
```

Tests cover:
- Module file existence
- Bicep compilation
- Parameter definitions
- Output definitions
- Main template integration
- API version compliance

## Module Implementation Status

| Task | Module | Status | Description |
|------|--------|--------|-------------|
| 1.2 | main.bicep | ✅ Complete | Main orchestration template |
| 1.3 | loganalytics.bicep | ✅ Complete | Log Analytics Workspace |
| 1.3 | applicationinsights.bicep | ✅ Complete | Application Insights |
| 1.3 | container-apps-environment.bicep | ✅ Complete | Container Apps Environment |
| 1.4 | container-registry.bicep | ✅ Complete | Azure Container Registry |
| 1.4 | container-app.bicep | ✅ Complete | Container App definition |
| 1.5 | openai.bicep | ✅ Complete | Azure OpenAI Service |
| 1.6 | bot-service.bicep | ✅ Complete | Azure Bot Service |
| 1.6 | key-vault.bicep | ✅ Complete | Azure Key Vault |
| 1.7 | validate-structure.sh | ✅ Complete | Structure validation script |
| 1.7 | validate-bicep.sh | ✅ Complete | Bicep compilation validation |

## Best Practices

### 1. Avoid Cyclic Dependencies

The module structure carefully avoids circular dependencies:
- Bot Service depends on Container App (needs endpoint URL)
- Container App depends on Container Apps Environment and Registry
- Monitoring resources are independent

### 2. Use Latest API Versions

All resource definitions use 2024+ API versions for latest features and security:
```bicep
resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  // ...
}
```

### 3. Parameter Descriptions

Every parameter includes `@description` decorator for documentation:
```bicep
@description('Environment name identifier (e.g., dev, test, prod)')
param environmentName string
```

### 4. Parameter Validation

Use decorators to enforce constraints:
```bicep
@minLength(1)
@maxLength(64)
@allowed(['eastus', 'westus', 'centralus'])
```

### 5. Symbolic Resource Names

Use clear, descriptive symbolic names:
```bicep
resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  // Good: 'rg' clearly indicates resource group
}
```

## Troubleshooting

### Bicep Compilation Errors

**Error**: "The language expression property '...' doesn't exist"
- **Cause**: Trying to reference a module output before module is implemented
- **Solution**: Check that all referenced modules are uncommented and deployed

**Error**: "A parameter cannot have a default value of empty string"
- **Cause**: Using `= ''` for parameters that require values
- **Solution**: Remove default value or use more appropriate default

### Deployment Errors

**Error**: "Resource name not globally unique"
- **Cause**: Resource token collision or manual name conflict
- **Solution**: Change `environmentName` or `location` to generate new token

**Error**: "Quota exceeded for resource type"
- **Cause**: Subscription limits reached
- **Solution**: Request quota increase or use different region

**Error**: "Template validation failed: Circular dependency"
- **Cause**: Resource A depends on B, which depends on A
- **Solution**: Review `dependsOn` clauses and remove circular references

## Security Considerations

1. **Principal ID**: Leave empty for local development, provide service principal for CI/CD
2. **Key Vault Access**: Managed identities used for secure secret access
3. **Container Registry**: Admin credentials generated but stored in Key Vault
4. **Public Endpoints**: Container Apps use public ingress (VNet integration in post-MVP)
5. **Bot Authentication**: Bot Framework JWT validation enforced in application code

## Performance Targets

- **Deployment Time**: Complete `azd up` in <15 minutes
- **Resource Provisioning**: Most resources provision in parallel
- **Container App Cold Start**: <10 seconds with Azure Container Apps
- **OpenAI Response Time**: <2 seconds for typical queries

## Cost Optimization

Estimated monthly costs (USD, as of 2024):

| Resource | SKU | Est. Cost |
|----------|-----|-----------|
| Container Apps | Consumption | ~$10-50 |
| Azure OpenAI | Pay-per-token | ~$50-200 |
| Container Registry | Basic | ~$5 |
| Key Vault | Standard | ~$1 |
| Application Insights | Pay-as-you-go | ~$10-30 |
| Log Analytics | Pay-per-GB | ~$5-20 |

**Total Estimated**: $81-306/month (varies with usage)

Cost optimization strategies:
- Use consumption-based Container Apps (no idle costs)
- Monitor OpenAI token usage closely
- Set retention policies on Log Analytics
- Use Basic tier Container Registry for development

## References

- [Azure Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Azure Developer CLI Documentation](https://learn.microsoft.com/azure/developer/azure-developer-cli/)
- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Azure OpenAI Service Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [Azure Bot Service Documentation](https://learn.microsoft.com/azure/bot-service/)
- [Azure Naming Conventions](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/azure-best-practices/resource-naming)

## Next Steps

After completing Task 1.2, proceed to:
1. **Task 1.3**: Implement Networking & Environment module
2. **Task 1.4**: Implement Container Infrastructure module
3. **Task 1.5**: Implement AI Services module
4. **Task 1.6**: Implement Bot Service & Security module
5. **Task 1.7**: Implement Monitoring & Validation

Each module will uncomment its corresponding section in `main.bicep` and provide real outputs to replace placeholders.
