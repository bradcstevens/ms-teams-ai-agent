# Azure AI Agent Framework for Microsoft Teams

An AI agent for Microsoft Teams, built with Azure Container Apps, Azure OpenAI, and the Microsoft Agent Framework. Deploy to Azure with a single command using Azure Developer CLI.

## Features

- One-command deployment with `azd up` (target: <15 minutes)
- Azure OpenAI integration with GPT-5
- Microsoft Teams bot integration
- Model Context Protocol (MCP) server support
- Application Insights monitoring
- Secure secret management with Azure Key Vault
- Container-based deployment on Azure Container Apps

## Prerequisites

- **Azure Subscription** with access to:
  - Azure OpenAI Service
  - Azure Container Apps
  - Azure Bot Service
- **Azure CLI** (`az`) - [Install](https://docs.microsoft.com/cli/azure/install-azure-cli)
- **Azure Developer CLI** (`azd`) - [Install](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- **Python 3.11+** - [Install](https://www.python.org/downloads/)
- **Docker** - [Install](https://docs.docker.com/get-docker/)

## Quick Start

### 1. Local Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd ms-teams-ai-agent

# Set up local development environment
./scripts/setup-local.sh

# Activate Python virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\Activate.ps1

# Edit .env with your Azure resource values
nano .env
```

### 2. Deploy to Azure

```bash
# Login to Azure
azd auth login

# Provision infrastructure and deploy application
azd up
```

This single command will:
1. Validate configuration (prepackage hook)
2. Provision Azure infrastructure (Bicep templates)
3. Register Azure Bot Service (postprovision hook)
4. Build and deploy container image
5. Generate Teams app manifest (postdeploy hook)

### 3. Deploy to Microsoft Teams

After infrastructure deployment completes, deploy the bot to Teams:

```bash
# Deploy bot to Teams (automated)
./scripts/deploy-teams-bot.sh \
  --environment <dev|staging|prod> \
  --resource-group <rg-name> \
  --bot-name <bot-name> \
  --endpoint <container-app-url>/api/messages \
  --key-vault <key-vault-name> \
  --version 1.0.0
```

This will:
1. Register the bot in Azure Bot Service
2. Generate Teams app manifest
3. Create Teams app package (.zip)
4. Validate deployment end-to-end

Then upload the generated `teams-app-<env>-1.0.0.zip` to Teams Admin Center.

**Detailed documentation:**
- [Teams Guide](docs/TEAMS_GUIDE.md) - Complete deployment, testing, and troubleshooting

## Project Structure

```
/
├── azure.yaml              # Azure Developer CLI configuration
├── infra/                  # Bicep infrastructure templates
│   ├── main.bicep         # Main orchestration template
│   └── modules/           # Modular Bicep components
├── src/                    # Python application source
│   ├── requirements.txt   # Python dependencies
│   ├── Dockerfile         # Container image definition
│   └── app/               # Application code
├── scripts/                # Automation scripts
│   ├── validate-azd-config.sh      # Configuration validation
│   ├── setup-local.sh              # Local development setup
│   ├── validate-config.sh          # Pre-package validation hook
│   ├── setup-bot.sh                # Post-provision bot registration
│   └── generate-teams-manifest.sh  # Post-deploy manifest generation
└── .azure/                 # azd environment files (auto-generated)
```

## Development Workflow

### Validate Configuration
```bash
# Validate azd project structure
./scripts/validate-azd-config.sh
```

### Local Testing
```bash
# Run application locally
python src/app/main.py

# Test with Bot Framework Emulator
# See docs/testing.md for details
```

### Deploy Changes
```bash
# Deploy application updates
azd deploy

# Deploy infrastructure changes
azd provision

# Full redeploy
azd up
```

### View Logs
```bash
# Stream container logs
azd logs --service api

# View in Azure Portal
az container logs --resource-group <rg-name> --name <container-name>
```

## Environment Variables

The following environment variables are automatically configured during deployment:

| Variable | Description | Source |
|----------|-------------|--------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI service endpoint | Bicep output |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | gpt-5 model deployment name | Bicep output |
| `BOT_ID` | Azure Bot Service application ID | Bot registration |
| `BOT_PASSWORD` | Bot application password | Key Vault |
| `BOT_TENANT_ID` | Azure AD tenant ID | Bicep output |
| `KEY_VAULT_NAME` | Key Vault name | Bicep output |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Application Insights connection | Bicep output |

## Architecture

### Azure Resources

- **Azure Container Apps**: Serverless container hosting
- **Azure OpenAI Service**: gpt-5 model deployment
- **Azure Bot Service**: Teams integration
- **Azure Container Registry**: Container image storage
- **Azure Key Vault**: Secrets management
- **Application Insights**: Monitoring and telemetry
- **Log Analytics Workspace**: Centralized logging

### Application Stack

- **Python 3.11+**: Core application runtime
- **FastAPI**: Web framework for bot endpoints
- **Microsoft Agent Framework**: AI agent orchestration
- **Bot Framework SDK**: Teams messaging integration
- **Azure SDK for Python**: Azure service integration

## Deployment Hooks

The `azure.yaml` configuration defines three deployment hooks:

1. **prepackage**: Validates configuration before packaging
2. **postprovision**: Registers bot and configures Azure resources
3. **postdeploy**: Generates Teams app manifest

See [scripts/README.md](scripts/README.md) for detailed hook documentation.

## Documentation

- [Developer Guide](docs/DEVELOPER_GUIDE.md) - Local setup, workflow, and API reference
- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [Operations Guide](docs/OPERATIONS.md) - Monitoring, maintenance, and troubleshooting
- [MCP Integration](docs/MCP_INTEGRATION.md) - Model Context Protocol setup
- [Teams Guide](docs/TEAMS_GUIDE.md) - Teams deployment and testing
- [Infrastructure Guide](infra/README.md) - Bicep templates and Azure resources

## Testing

### Configuration Validation
```bash
# Validate azd configuration
./scripts/validate-azd-config.sh

# Validate application configuration
./scripts/validate-config.sh
```

### Infrastructure Testing
```bash
# Validate Bicep templates
az bicep build --file infra/main.bicep
```

### Application Testing
```bash
# Run unit tests
pytest tests/

# Run integration tests with Bot Framework Emulator
# See docs/testing.md
```

## Troubleshooting

### Common Issues

**azd command not found**
- Install Azure Developer CLI: https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd

**Deployment timeout**
- Check Azure subscription quotas for Container Apps and OpenAI
- Verify region availability for all required services

**Bot not responding in Teams**
- Verify Bot Service messaging endpoint matches Container App URL
- Check Application Insights logs for errors
- Validate Bot ID and Password in Key Vault

For more troubleshooting guidance, see [docs/troubleshooting.md](docs/troubleshooting.md).

## License

License information will be added here.

## Support

For issues and questions:
- Review existing documentation in `/docs`
- Check Application Insights logs for runtime issues
- Review Bicep deployment logs in Azure Portal

---

**Built with Azure Developer CLI** | **Powered by Azure OpenAI** | **Integrated with Microsoft Teams**
