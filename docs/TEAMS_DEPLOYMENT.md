# Microsoft Teams Bot Deployment Guide

This guide provides comprehensive instructions for deploying the AI Agent to Microsoft Teams.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Overview](#deployment-overview)
3. [Step-by-Step Deployment](#step-by-step-deployment)
4. [Testing & Validation](#testing--validation)
5. [Troubleshooting](#troubleshooting)
6. [Security Configuration](#security-configuration)

## Prerequisites

### Required Tools

- **Azure CLI**: Version 2.50.0 or later
- **Azure Subscription**: With permissions to create resources
- **bash**: Unix shell (Linux, macOS, WSL2)
- **zip**: Package creation utility
- **Python 3.9+**: For validation scripts

### Required Azure Resources

Ensure the following resources are deployed (from Task 1-3):

- Azure Resource Group
- Azure Container Apps Environment
- Azure Container App (bot service running)
- Azure Bot Service registration
- Azure Key Vault
- Azure OpenAI Service

### Authentication

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "Your Subscription Name"

# Verify authentication
az account show
```

## Deployment Overview

The deployment process consists of four main steps:

```
1. Bot Registration    → Register bot in Azure & store credentials
2. Manifest Generation → Create Teams app manifest with bot ID
3. Package Creation    → Bundle manifest + icons into .zip
4. Validation         → Test deployment end-to-end
```

### Automated Deployment

Use the orchestrator script for complete deployment:

```bash
./scripts/deploy-teams-bot.sh \
  --environment dev \
  --resource-group rg-teams-bot-dev \
  --bot-name bot-teams-ai-agent-dev \
  --endpoint https://ca-dev-abc123.azurecontainerapps.io/api/messages \
  --key-vault kv-dev-abc123 \
  --version 1.0.0
```

### Manual Deployment

Follow individual steps for more control.

## Step-by-Step Deployment

### Step 1: Bot Registration

Register the Azure Bot Service and generate credentials.

```bash
./scripts/create-bot-registration.sh \
  --environment dev \
  --resource-group rg-teams-bot-dev \
  --bot-name bot-teams-ai-agent-dev \
  --endpoint https://ca-dev-abc123.azurecontainerapps.io/api/messages \
  --key-vault kv-dev-abc123
```

**What this does:**
- Creates Azure AD app registration
- Generates client secret (app password)
- Creates Azure Bot Service resource
- Enables Microsoft Teams channel
- Stores credentials in Key Vault

**Outputs:**
- Bot ID (GUID) stored in Key Vault as `bot-id`
- Bot Password stored in Key Vault as `bot-password`

**Retrieve Bot ID:**
```bash
BOT_ID=$(az keyvault secret show \
  --vault-name kv-dev-abc123 \
  --name "bot-id" \
  --query "value" -o tsv)

echo "Bot ID: $BOT_ID"
```

### Step 2: Teams Manifest Generation

Generate the Teams app manifest with bot ID and endpoint.

```bash
./scripts/generate-teams-manifest.sh \
  --bot-id "$BOT_ID" \
  --endpoint "ca-dev-abc123.azurecontainerapps.io/api/messages" \
  --version "1.0.0" \
  --environment dev
```

**What this does:**
- Substitutes `{{BOT_ID}}` and `{{BOT_ENDPOINT}}` placeholders
- Validates JSON syntax
- Checks manifest schema compliance
- Warns if icons are missing

**Output:**
- Updated `teams/manifest.json` with actual values

**Manifest Structure:**
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
  "manifestVersion": "1.16",
  "version": "1.0.0",
  "id": "actual-bot-id-here",
  "bots": [{
    "botId": "actual-bot-id-here",
    "scopes": ["personal", "team", "groupchat"]
  }]
}
```

### Step 3: Icon Preparation

Teams requires two icons:
- **Color icon**: 192x192 PNG (solid background)
- **Outline icon**: 32x32 PNG (transparent background)

**Create icons manually** or use design tools:
- Adobe Photoshop
- GIMP (free)
- Figma (free)
- Canva (free)

Place icons in `teams/` directory:
```
teams/
├── manifest.json
├── color.png      (192x192)
└── outline.png    (32x32)
```

### Step 4: Teams Package Creation

Bundle manifest and icons into a deployable .zip package.

```bash
./scripts/create-teams-package.sh \
  --input ./teams \
  --output ./teams-app-dev-1.0.0.zip \
  --version 1.0.0 \
  --environment dev
```

**What this does:**
- Validates manifest JSON
- Checks all required files present
- Verifies placeholders are substituted
- Creates .zip package

**Output:**
- `teams-app-dev-1.0.0.zip` ready for upload

**Package Contents:**
```
teams-app-dev-1.0.0.zip
├── manifest.json
├── color.png
└── outline.png
```

### Step 5: Deployment Validation

Test the deployment end-to-end.

```bash
./scripts/test-teams-deployment.sh \
  --resource-group rg-teams-bot-dev \
  --bot-name bot-teams-ai-agent-dev \
  --endpoint https://ca-dev-abc123.azurecontainerapps.io/api/messages
```

**Tests performed:**
1. Azure CLI availability
2. Azure authentication
3. Bot registration exists
4. Teams channel enabled
5. Endpoint accessibility (health check)
6. Authentication enforcement
7. Manifest validation
8. Icon files present
9. HTTPS enforcement

**Expected output:**
```
[TEST] ✓ Azure CLI Check: PASSED
[TEST] ✓ Bot Registration: PASSED
[TEST] ✓ Teams Channel: PASSED
[TEST] ✓ Health Endpoint: PASSED
[TEST] ✓ Manifest Validation: PASSED
...
Passed:  10
Warnings: 0
Failed:   0
```

### Step 6: Upload to Teams

#### Option A: Teams Admin Center (Organization-wide)

1. Navigate to [Teams Admin Center](https://admin.teams.microsoft.com/policies/manage-apps)
2. Click **Upload** → **Upload an app to your organization's app catalog**
3. Select `teams-app-dev-1.0.0.zip`
4. Review app details and click **Add**
5. Configure app policies and permissions
6. Publish to users

#### Option B: Sideloading (Testing)

1. Open Microsoft Teams desktop/web client
2. Go to **Apps** in left sidebar
3. Click **Upload a custom app** (bottom-left)
4. Select **Upload for [your org]** or **Upload for me**
5. Choose `teams-app-dev-1.0.0.zip`
6. Click **Add** to install

#### Option C: AppSource (Public Distribution)

For public distribution, submit to [Microsoft AppSource](https://appsource.microsoft.com).

## Testing & Validation

### Test Bot in Teams

1. Search for bot in Teams: "AI Agent"
2. Start a personal chat
3. Send a test message: "hello"
4. Verify bot responds

### Monitor Bot Activity

**Application Insights:**
```bash
# Get connection string
az monitor app-insights component show \
  --resource-group rg-teams-bot-dev \
  --app appi-dev-abc123 \
  --query connectionString -o tsv
```

**View logs:**
- Azure Portal → Application Insights → Logs
- Query: `traces | where message contains "bot"`

**Container App Logs:**
```bash
az containerapp logs show \
  --name ca-dev-abc123 \
  --resource-group rg-teams-bot-dev \
  --follow
```

### Test Bot Endpoints Manually

**Health check:**
```bash
curl https://ca-dev-abc123.azurecontainerapps.io/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "teams-ai-agent",
  "agent_initialized": true
}
```

**Bot messages endpoint (should require auth):**
```bash
curl -X POST https://ca-dev-abc123.azurecontainerapps.io/api/messages \
  -H "Content-Type: application/json" \
  -d '{"type":"message","text":"test"}'
```

Expected: `401 Unauthorized` (authentication required)

## Troubleshooting

### Bot Registration Issues

**Error: "Bot already exists"**
- The script updates existing bots
- Check bot configuration in Azure Portal

**Error: "Insufficient permissions"**
- Ensure you have `Contributor` role on resource group
- Check Azure AD permissions for app registration

**Error: "Key Vault access denied"**
- Add your user to Key Vault access policies
- Requires `Secret Get` and `Secret Set` permissions

### Manifest Validation Errors

**Error: "Unsubstituted placeholders"**
- Run `generate-teams-manifest.sh` before packaging
- Verify bot ID was retrieved from Key Vault

**Error: "Invalid JSON syntax"**
- Check `teams/manifest.json` for syntax errors
- Use `python -m json.tool teams/manifest.json` to validate

**Error: "Missing required fields"**
- Ensure manifest includes all required fields
- Compare with template at `teams/manifest.json`

### Endpoint Accessibility Issues

**Error: "Health endpoint not accessible"**
- Verify Container App is running: `az containerapp show ...`
- Check Container App ingress is enabled
- Verify no firewall rules blocking access

**Error: "HTTP 503 Service Unavailable"**
- Container App may be starting up (wait 30s)
- Check Container App logs for errors
- Verify all environment variables are set

### Teams Upload Issues

**Error: "App validation failed"**
- Ensure manifest version is 1.16+
- Check all required fields are present
- Verify icons are correct size (192x192, 32x32)

**Error: "Bot ID not found"**
- Verify bot is registered in Azure Bot Service
- Check bot ID matches manifest
- Ensure Teams channel is enabled

**Error: "Package too large"**
- Maximum package size: 10MB
- Compress icons if needed
- Remove unnecessary files from package

### Authentication Issues

**Error: "401 Unauthorized" in bot conversations**
- Verify bot credentials in Key Vault
- Check Container App environment variables:
  - `BOT_ID`
  - `BOT_PASSWORD`
- Restart Container App after updating credentials

**Error: "Bot not responding"**
- Check Application Insights for errors
- Verify messaging endpoint in Bot Service matches Container App URL
- Test health endpoint accessibility

## Security Configuration

### Bot Authentication

The bot implements JWT token validation:

```python
# Validates Bot Framework tokens
- Bearer token required
- Audience validation (bot ID)
- Issuer validation (Microsoft)
- Expiration validation
```

### Security Headers

All responses include security headers:

```
Strict-Transport-Security: max-age=31536000
Content-Security-Policy: default-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
```

### CORS Configuration

Bot endpoint allows requests from:
- `https://teams.microsoft.com`
- `https://api.botframework.com`
- Bot Framework infrastructure domains

### HTTPS Enforcement

- All endpoints enforce HTTPS
- Container Apps provides TLS termination
- HTTP requests redirected to HTTPS

### Credential Management

**Never commit credentials to git:**
- Use Azure Key Vault for production
- Use environment variables for local development
- Rotate secrets regularly (every 90 days)

**Retrieve credentials securely:**
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://kv-name.vault.azure.net", credential=credential)
bot_password = client.get_secret("bot-password").value
```

### Optional: Azure Front Door (WAF)

For production deployments, consider adding Azure Front Door with WAF:

**Benefits:**
- DDoS protection
- Rate limiting
- SQL injection prevention
- XSS protection
- Geographic filtering

**Configuration:** See `infra/security/front-door.bicep` (optional module)

### Rate Limiting

Default rate limits:
- 10 messages per minute per user
- 100 messages per hour per user
- 5 message burst size

**Configure in:** `src/app/bot/security.py`

## Multi-Environment Deployment

### Environment-Specific Configuration

Deploy to multiple environments (dev, staging, prod):

```bash
# Development
./scripts/deploy-teams-bot.sh --environment dev ...

# Staging
./scripts/deploy-teams-bot.sh --environment staging ...

# Production
./scripts/deploy-teams-bot.sh --environment prod ...
```

### Environment Variables

Each environment should have:
- Separate resource group
- Separate bot registration
- Separate Key Vault
- Separate Container App
- Environment-tagged manifest

### Package Naming Convention

Packages are automatically tagged with environment:
- `teams-app-dev-1.0.0.zip`
- `teams-app-staging-1.0.0.zip`
- `teams-app-prod-1.0.0.zip`

## References

- [Bot Framework Documentation](https://docs.microsoft.com/azure/bot-service/)
- [Teams App Manifest Schema](https://docs.microsoft.com/microsoftteams/platform/resources/schema/manifest-schema)
- [Azure Container Apps](https://docs.microsoft.com/azure/container-apps/)
- [Azure Key Vault](https://docs.microsoft.com/azure/key-vault/)

## Support

For issues or questions:
1. Check Application Insights logs
2. Review Container App logs
3. Run `test-teams-deployment.sh` for diagnostics
4. Check [Troubleshooting](#troubleshooting) section above
