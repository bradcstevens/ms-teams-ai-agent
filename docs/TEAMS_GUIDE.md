# Microsoft Teams Bot - Complete Guide

Comprehensive guide for deploying, testing, and troubleshooting the MS Teams AI Agent.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment](#deployment)
3. [Testing & Validation](#testing--validation)
4. [Troubleshooting](#troubleshooting)
5. [Security Configuration](#security-configuration)
6. [Multi-Environment Deployment](#multi-environment-deployment)
7. [Programmatic Upload Options](#programmatic-upload-options)

---

## Prerequisites

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Azure CLI | 2.50+ | Azure resource management |
| Python | 3.9+ | Validation scripts |
| bash | - | Unix shell (Linux, macOS, WSL2) |
| zip | - | Package creation |

### Required Azure Resources

Ensure these resources are deployed (via `azd up`):

- Azure Resource Group
- Azure Container Apps Environment
- Azure Container App (bot service running)
- Azure Bot Service registration
- Azure Key Vault
- Azure OpenAI Service

### Authentication

```bash
az login
az account set --subscription "Your Subscription Name"
az account show
```

---

## Deployment

### Quick Start (Automated)

```bash
./scripts/deploy-teams-bot.sh \
  --environment dev \
  --resource-group rg-teams-bot-dev \
  --bot-name bot-teams-ai-agent-dev \
  --endpoint https://ca-dev-abc123.azurecontainerapps.io/api/messages \
  --key-vault kv-dev-abc123 \
  --version 1.0.0
```

### Step-by-Step Deployment

#### Step 1: Bot Registration

```bash
./scripts/create-bot-registration.sh \
  --environment dev \
  --resource-group rg-teams-bot-dev \
  --bot-name bot-teams-ai-agent-dev \
  --endpoint https://ca-dev-abc123.azurecontainerapps.io/api/messages \
  --key-vault kv-dev-abc123
```

**Outputs stored in Key Vault:**
- `bot-id` - Bot application ID (GUID)
- `bot-password` - Bot application secret

**Retrieve Bot ID:**
```bash
BOT_ID=$(az keyvault secret show \
  --vault-name kv-dev-abc123 \
  --name "bot-id" \
  --query "value" -o tsv)
echo "Bot ID: $BOT_ID"
```

#### Step 2: Generate Teams Manifest

```bash
./scripts/generate-teams-manifest.sh \
  --bot-id "$BOT_ID" \
  --endpoint "ca-dev-abc123.azurecontainerapps.io/api/messages" \
  --version "1.0.0" \
  --environment dev
```

#### Step 3: Prepare Icons

Teams requires two icons in `teams/` directory:
- `color.png` - 192x192 PNG (solid background)
- `outline.png` - 32x32 PNG (transparent background)

#### Step 4: Create Teams Package

```bash
./scripts/create-teams-package.sh \
  --input ./teams \
  --output ./teams-app-dev-1.0.0.zip \
  --version 1.0.0 \
  --environment dev
```

#### Step 5: Upload to Teams

**Option A: Teams Admin Center (Organization-wide)**
1. Navigate to [Teams Admin Center](https://admin.teams.microsoft.com/policies/manage-apps)
2. Click **Upload** → **Upload an app to your organization's app catalog**
3. Select `teams-app-dev-1.0.0.zip`
4. Configure app policies and publish

**Option B: Sideloading (Testing)**
1. Open Microsoft Teams
2. Go to **Apps** → **Upload a custom app**
3. Select your package file
4. Click **Add**

---

## Testing & Validation

### Automated Validation

```bash
./scripts/test-teams-deployment.sh \
  --resource-group rg-teams-bot-dev \
  --bot-name bot-teams-ai-agent-dev \
  --endpoint https://ca-dev-abc123.azurecontainerapps.io/api/messages
```

### Run Unit Tests

```bash
# Bot authentication tests
pytest src/tests/test_bot_authentication.py -v

# Teams manifest tests
pytest src/tests/test_teams_manifest.py -v

# Integration tests
pytest tests/integration/test_teams_deployment.py -v
```

### Manual Verification

#### Verify Bot Registration
```bash
az bot show --name bot-teams-ai-agent-dev --resource-group rg-teams-bot-dev
az bot msteams show --name bot-teams-ai-agent-dev --resource-group rg-teams-bot-dev
```

#### Test Endpoints
```bash
# Health check (should return 200)
curl https://ca-dev-abc123.azurecontainerapps.io/health

# Messages endpoint (should return 401 - auth required)
curl -X POST https://ca-dev-abc123.azurecontainerapps.io/api/messages \
  -H "Content-Type: application/json" \
  -d '{"type":"message","text":"test"}'
```

#### Validate Manifest
```bash
# Check JSON syntax
python3 -m json.tool teams/manifest.json

# Verify no unsubstituted placeholders
grep -E "{{BOT_ID}}|{{BOT_ENDPOINT}}" teams/manifest.json
# Expected: no output
```

#### Verify Package Contents
```bash
unzip -l teams-app-dev-1.0.0.zip
# Expected: manifest.json, color.png, outline.png (3 files)
```

### Testing Checklist

- [ ] Bot Service created in Azure
- [ ] Bot credentials in Key Vault
- [ ] Teams channel enabled
- [ ] Health endpoint returns 200
- [ ] Messages endpoint requires auth
- [ ] Manifest JSON is valid
- [ ] Icons are correct sizes
- [ ] App installs in Teams
- [ ] Bot responds to messages

---

## Troubleshooting

### Bot Registration Issues

| Error | Cause | Solution |
|-------|-------|----------|
| "Bot already exists" | Duplicate registration | Script updates existing bots |
| "Insufficient permissions" | Missing Azure role | Ensure Contributor role on resource group |
| "Key Vault access denied" | Missing access policy | Add user with Secret Get/Set permissions |

### Manifest Issues

| Error | Cause | Solution |
|-------|-------|----------|
| "Unsubstituted placeholders" | Missing generation step | Run `generate-teams-manifest.sh` |
| "Invalid JSON syntax" | Malformed JSON | Use `python -m json.tool` to debug |
| "Missing required fields" | Incomplete manifest | Compare with template |

### Endpoint Issues

| Error | Cause | Solution |
|-------|-------|----------|
| "Health endpoint not accessible" | Container not running | Check `az containerapp show` |
| "503 Service Unavailable" | Container starting | Wait 30s, check logs |
| "401 Unauthorized" | Invalid credentials | Verify bot credentials in Key Vault |

### Teams Upload Issues

| Error | Cause | Solution |
|-------|-------|----------|
| "App validation failed" | Invalid manifest | Check schema version (1.16+) |
| "Bot ID not found" | Bot not registered | Verify Bot Service exists |
| "Package too large" | Size > 10MB | Compress icons |

### View Logs

```bash
# Container App logs
az containerapp logs show \
  --name ca-dev-abc123 \
  --resource-group rg-teams-bot-dev \
  --follow

# Application Insights
# Azure Portal → Application Insights → Logs
# Query: traces | where message contains "bot"
```

---

## Security Configuration

### Authentication

The bot validates JWT tokens from Bot Framework:
- Bearer token required
- Audience validation (bot ID)
- Issuer validation (Microsoft)
- Expiration validation

### Security Headers

All responses include:
```
Strict-Transport-Security: max-age=31536000
Content-Security-Policy: default-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
```

### CORS Configuration

Allowed origins:
- `https://teams.microsoft.com`
- `https://api.botframework.com`
- Bot Framework infrastructure domains

### Rate Limiting

Default limits (configurable in `src/app/bot/security.py`):
- 10 messages per minute per user
- 100 messages per hour per user
- 5 message burst size

### Credential Management

- Use Azure Key Vault for production
- Use environment variables for development
- Rotate secrets every 90 days
- Never commit credentials to git

---

## Multi-Environment Deployment

### Deploy to Different Environments

```bash
# Development
./scripts/deploy-teams-bot.sh --environment dev ...

# Staging
./scripts/deploy-teams-bot.sh --environment staging ...

# Production
./scripts/deploy-teams-bot.sh --environment prod ...
```

### Environment Isolation

Each environment should have separate:
- Resource group
- Bot registration
- Key Vault
- Container App
- Teams app package

### Package Naming

Packages are auto-tagged: `teams-app-{env}-{version}.zip`

---

## Programmatic Upload Options

> **Note**: Programmatic upload to Teams org catalog requires **delegated user authentication** - service principals cannot upload apps.

### Microsoft Graph API

```bash
# Requires user access token (not service principal)
curl -X POST "https://graph.microsoft.com/v1.0/appCatalogs/teamsApps" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -H "Content-Type: application/zip" \
  --data-binary @teams-app-dev-1.0.0.zip
```

**Permissions**: `AppCatalog.Submit` or `AppCatalog.ReadWrite.All` (delegated only)

### Teams Toolkit CLI

```bash
npm install -g @microsoft/teamsapp-cli
teamsfx publish --env dev  # Requires interactive auth
```

### Recommended Approach

1. **Automated**: Package creation via `azd up` postdeploy hook
2. **Manual Once**: First upload via Teams Admin Center
3. **Subsequent Updates**: Graph API with cached user token

---

## References

- [Bot Framework Documentation](https://docs.microsoft.com/azure/bot-service/)
- [Teams App Manifest Schema](https://docs.microsoft.com/microsoftteams/platform/resources/schema/manifest-schema)
- [Microsoft Graph teamsApp API](https://learn.microsoft.com/en-us/graph/api/teamsapp-publish)
- [Azure Container Apps](https://docs.microsoft.com/azure/container-apps/)
