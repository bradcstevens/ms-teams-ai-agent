# Automation Scripts

This directory contains automation scripts for Azure deployment and configuration management.

## Available Scripts

### `validate-azd-config.sh`
**Purpose:** Validates the Azure Developer CLI (azd) project structure and configuration.

**Usage:**
```bash
./scripts/validate-azd-config.sh
```

**Validation Checks:**
- ✅ azure.yaml exists and has required schema
- ✅ Service definitions are properly configured
- ✅ Deployment hooks are configured
- ✅ Required directory structure exists
- ✅ Environment variable mappings are defined
- ✅ Referenced hook scripts exist

**Exit Codes:**
- `0` - All validations passed
- `1` - One or more validations failed

---

### `validate-config.sh`
**Purpose:** Pre-package validation hook for azd deployment.

**Trigger:** Automatically called by azd during `prepackage` phase.

**Validation Checks:**
- Source directory exists
- requirements.txt is present
- (More checks will be added as application develops)

**Status:** ✅ Implemented

---

### `setup-bot.sh`
**Purpose:** Post-provision hook to register Azure Bot Service and configure credentials.

**Trigger:** Automatically called by azd during `postprovision` phase.

**Tasks:**
- Register Azure Bot Service
- Enable Microsoft Teams channel
- Store Bot ID and Password in Key Vault
- Configure messaging endpoint

**Status:** 🚧 Placeholder - To be implemented in Task 4.1

---

### `generate-teams-manifest.sh`
**Purpose:** Post-deploy hook to generate Teams app manifest with dynamic values.

**Trigger:** Automatically called by azd during `postdeploy` phase.

**Tasks:**
- Generate manifest.json from template
- Substitute Bot ID and messaging endpoint
- Package with app icons
- Output instructions for Teams upload

**Status:** 🚧 Placeholder - To be implemented in Task 4.2

---

### `setup-local.sh`
**Purpose:** Local development environment setup script.

**Usage:**
```bash
./scripts/setup-local.sh
```

**Tasks:**
- Install Python dependencies
- Configure local environment variables
- Set up development tools
- Verify Azure CLI and azd installation

**Status:** ✅ Implemented

---

## azd Workflow Hooks

The following hooks are configured in `azure.yaml`:

### Pre-package Hook
**Trigger:** Before packaging the application for deployment
**Script:** `validate-config.sh`
**Purpose:** Validate configuration and dependencies

### Post-provision Hook
**Trigger:** After Azure infrastructure is provisioned
**Script:** `setup-bot.sh`
**Purpose:** Register and configure Azure Bot Service

### Post-deploy Hook
**Trigger:** After application is deployed to Azure
**Script:** `generate-teams-manifest.sh`
**Purpose:** Generate Teams app manifest for upload

---

## Development Workflow

### Initial Setup
```bash
# 1. Validate project structure
./scripts/validate-azd-config.sh

# 2. Set up local development environment
./scripts/setup-local.sh

# 3. Deploy to Azure
azd up
```

### Deployment Process
```bash
# The following happens automatically during 'azd up':

# 1. Prepackage: Validation
#    → validate-config.sh runs

# 2. Provision: Infrastructure deployment
#    → Bicep templates create Azure resources

# 3. Postprovision: Bot registration
#    → setup-bot.sh runs (when implemented)

# 4. Deploy: Container deployment
#    → Docker image built and pushed
#    → Container App updated

# 5. Postdeploy: Teams manifest generation
#    → generate-teams-manifest.sh runs (when implemented)
```

### Cleanup
```bash
# Remove all Azure resources
azd down
```

---

## Environment Variables

Scripts may use the following environment variables from azd:

- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI service endpoint
- `AZURE_OPENAI_DEPLOYMENT_NAME` - Model deployment name
- `BOT_ID` - Azure Bot Service application ID
- `BOT_PASSWORD` - Bot application password
- `BOT_TENANT_ID` - Azure AD tenant ID
- `KEY_VAULT_NAME` - Key Vault name for secrets
- `APPLICATIONINSIGHTS_CONNECTION_STRING` - Application Insights connection

These are automatically populated by the Bicep templates and available to hooks.

---

## Cross-Platform Support

All scripts are available in both POSIX (sh) and Windows (PowerShell) versions:
- `*.sh` - POSIX/Linux/macOS/WSL2
- `*.ps1` - Windows PowerShell

The azure.yaml configuration automatically selects the appropriate version based on the platform.

---

## Testing

To test hooks without full deployment:
```bash
# Test validation hook
./scripts/validate-config.sh

# Test azd configuration validation
./scripts/validate-azd-config.sh
```

---

## Future Enhancements

Planned improvements for post-MVP:
- Automated Bot Service registration (Task 4.1)
- Dynamic Teams manifest generation (Task 4.2)
- Certificate management automation
- Monitoring dashboard setup
- Rollback automation
- Multi-environment support (dev/staging/prod)

---

**Last Updated:** 2025-11-12 (Task 1.1)
