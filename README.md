# Azure AI Agent Framework for Microsoft Teams

An AI agent for Microsoft Teams, built with Azure Container Apps, Azure OpenAI, and the Microsoft Agent Framework. Deploy to Azure with a single command using Azure Developer CLI.

## Features

- One-command deployment with `azd up` (target: <15 minutes)
- Azure OpenAI integration with GPT-4
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
- [Teams Deployment Guide](docs/TEAMS_DEPLOYMENT.md)
- [Testing & Troubleshooting](docs/TEAMS_TESTING.md)

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
# Run application locally (after Phase 2 implementation)
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
| `AZURE_OPENAI_DEPLOYMENT_NAME` | GPT-4 model deployment name | Bicep output |
| `BOT_ID` | Azure Bot Service application ID | Bot registration |
| `BOT_PASSWORD` | Bot application password | Key Vault |
| `BOT_TENANT_ID` | Azure AD tenant ID | Bicep output |
| `KEY_VAULT_NAME` | Key Vault name | Bicep output |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Application Insights connection | Bicep output |

## Architecture

### Azure Resources

- **Azure Container Apps**: Serverless container hosting
- **Azure OpenAI Service**: GPT-4 model deployment
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

- [Scripts Documentation](scripts/README.md) - Automation scripts and hooks
- [Infrastructure Guide](infra/README.md) - Bicep templates and Azure resources (Task 1.2+)
- [Application Guide](src/README.md) - Python application architecture (Phase 2+)
- [MCP Integration](docs/mcp-integration.md) - Model Context Protocol setup (Phase 3+)
- [Teams Deployment](docs/teams-deployment.md) - Teams configuration guide (Phase 4+)

## Project Status

**Last Updated**: 2025-11-13

### Project Completion: 60% (3/5 Phases Complete)

This project is under active development following a phased approach with multi-agent collective workflow:

#### Phase 1: Infrastructure Foundation - COMPLETE
**Status**: Production-ready | **All 7 subtasks completed**

- Azure Bicep infrastructure deployed
- Core modules: Container Apps, OpenAI, Bot Service, Key Vault, Monitoring
- All validation tests passing
- Infrastructure fully documented and validated

**Key Deliverables**:
- `infra/main.bicep` - Main orchestration template
- `infra/ai/openai.bicep` - Azure OpenAI configuration
- `infra/bot/bot-service.bicep` - Teams bot setup
- `infra/core/host/*.bicep` - Container Apps infrastructure
- `infra/security/key-vault.bicep` - Secrets management

#### Phase 2: Agent Implementation - COMPLETE
**Status**: Production-ready | **All 8 subtasks completed**

- Teams AI agent with FastAPI implementation
- Microsoft Agent Framework integration
- Bot Framework SDK implementation
- All core functionality implemented

**Key Deliverables**:
- `src/app/` - Python application with FastAPI
- `src/requirements.txt` - Production dependencies
- `src/Dockerfile` - Container image definition

#### Phase 3: MCP Integration - COMPLETE
**Status**: Production-ready | **All 7 subtasks completed**

- Model Context Protocol integration
- **98/98 tests passing (100% pass rate)**
- Quality gates: mypy 0 errors, ruff 0 warnings
- 2,009 lines of production code

**Key Deliverables**:
- Configuration management system
- Client/Manager implementation
- Discovery/Registry system
- Server integrations (OpenAI, Perplexity, Anthropic)
- Bridge layer for agent communication
- Comprehensive error handling
- Full test coverage

#### Phase 4: Teams Deployment - UNDER VALIDATION
**Status**: Requires verification | **6 subtasks pending validation**

- TaskMaster shows "done" but subtasks show "pending"
- Requires validation before confirming completion
- Deployment automation being verified

**Planned Deliverables**:
- Teams app manifest generation
- Bot registration automation
- End-to-end deployment scripts

#### Phase 5: Validation & Documentation - PENDING
**Status**: Blocked | **Awaiting Phase 4 completion**

- Status: pending
- Not yet started
- Comprehensive testing and documentation phase

### Quality Metrics

- **Test Coverage**: 98/98 passing for MCP integration (Phase 3)
- **Type Safety**: 100% (mypy strict mode)
- **Code Quality**: 100% (ruff compliance)
- **Total Implementation**: 2,000+ lines of production code
- **Infrastructure**: 100% Bicep validation passing

### Development Approach

This project uses a **multi-agent collective workflow** with TaskMaster AI:
- Research agents for technical investigation
- Implementation agents for code development
- Validation agents for quality assurance
- See `.taskmaster/tasks/` for detailed task tracking

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
# Validate Bicep templates (Task 1.2+)
az bicep build --file infra/main.bicep
```

### Application Testing
```bash
# Run unit tests (Phase 2+)
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
