# Teams Deployment Testing & Troubleshooting Guide

Comprehensive testing procedures and troubleshooting for Microsoft Teams bot deployment.

## Testing Checklist

Use this checklist to validate your deployment:

### Pre-Deployment Tests

- [ ] Azure CLI installed and authenticated
- [ ] All infrastructure resources deployed (Tasks 1-3)
- [ ] Container App running and healthy
- [ ] Bot application code deployed
- [ ] Environment variables configured
- [ ] Key Vault accessible

### Bot Registration Tests

- [ ] Bot Service created in Azure
- [ ] Bot ID stored in Key Vault
- [ ] Bot Password stored in Key Vault
- [ ] Teams channel enabled
- [ ] Messaging endpoint configured
- [ ] Bot shows as "Running" in Azure Portal

### Manifest Tests

- [ ] manifest.json file exists
- [ ] Valid JSON syntax
- [ ] Bot ID placeholder substituted
- [ ] Endpoint placeholder substituted
- [ ] All required fields present
- [ ] Schema version 1.16+
- [ ] Bot scopes include personal, team, groupchat

### Package Tests

- [ ] color.png exists (192x192)
- [ ] outline.png exists (32x32)
- [ ] Package created as .zip
- [ ] Package size < 10MB
- [ ] Package contains exactly 3 files

### Endpoint Tests

- [ ] Health endpoint returns 200
- [ ] Root endpoint returns 200
- [ ] Messages endpoint requires authentication
- [ ] HTTPS enforced
- [ ] Security headers present

### Teams Integration Tests

- [ ] App uploads successfully
- [ ] App installs without errors
- [ ] Bot appears in Teams search
- [ ] Bot accepts chat messages
- [ ] Bot responds to messages
- [ ] Bot works in teams/channels

## Automated Testing

### Run All Tests

```bash
# Run deployment validation
./scripts/test-teams-deployment.sh \
  --resource-group rg-teams-bot-dev \
  --bot-name bot-teams-ai-agent-dev \
  --endpoint https://ca-dev-abc123.azurecontainerapps.io/api/messages
```

### Run Unit Tests

```bash
# Install test dependencies
pip install -r src/requirements.txt

# Run authentication tests
pytest src/tests/test_bot_authentication.py -v

# Run manifest tests
pytest src/tests/test_teams_manifest.py -v

# Run integration tests
pytest tests/integration/test_teams_deployment.py -v

# Run all tests
pytest src/tests/ tests/integration/ -v
```

### Test Coverage

```bash
# Generate coverage report
pytest --cov=src/app --cov-report=html src/tests/

# View report
open htmlcov/index.html
```

## Manual Testing Procedures

### Test 1: Bot Registration Verification

**Verify bot exists:**
```bash
az bot show \
  --name bot-teams-ai-agent-dev \
  --resource-group rg-teams-bot-dev
```

**Expected:** JSON output with bot details

**Verify Teams channel:**
```bash
az bot msteams show \
  --name bot-teams-ai-agent-dev \
  --resource-group rg-teams-bot-dev
```

**Expected:** JSON output with channel configuration

### Test 2: Credential Verification

**Check bot credentials in Key Vault:**
```bash
# Get bot ID
az keyvault secret show \
  --vault-name kv-dev-abc123 \
  --name "bot-id" \
  --query "value" -o tsv

# Get bot password (masked)
az keyvault secret show \
  --vault-name kv-dev-abc123 \
  --name "bot-password" \
  --query "value" -o tsv | head -c 10
```

**Expected:** Bot ID (GUID) and password prefix

### Test 3: Endpoint Accessibility

**Test health endpoint:**
```bash
curl -v https://ca-dev-abc123.azurecontainerapps.io/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "teams-ai-agent",
  "agent_initialized": true,
  "conversations": {
    "active": 0,
    "total": 0
  }
}
```

**Test root endpoint:**
```bash
curl https://ca-dev-abc123.azurecontainerapps.io/
```

**Expected response:**
```json
{
  "service": "Teams AI Agent",
  "version": "1.0.0",
  "status": "running"
}
```

**Test messages endpoint (should require auth):**
```bash
curl -X POST https://ca-dev-abc123.azurecontainerapps.io/api/messages \
  -H "Content-Type: application/json" \
  -d '{"type":"message","text":"test"}'
```

**Expected:** `401 Unauthorized` or `403 Forbidden`

### Test 4: Security Headers

**Verify security headers:**
```bash
curl -I https://ca-dev-abc123.azurecontainerapps.io/health
```

**Expected headers:**
```
Strict-Transport-Security: max-age=31536000
Content-Security-Policy: default-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
```

### Test 5: Manifest Validation

**Validate JSON syntax:**
```bash
python3 -m json.tool teams/manifest.json
```

**Expected:** Pretty-printed JSON (no errors)

**Check for placeholders:**
```bash
grep -E "{{BOT_ID}}|{{BOT_ENDPOINT}}" teams/manifest.json
```

**Expected:** No output (placeholders substituted)

**Validate with Python:**
```bash
python3 << EOF
import sys
sys.path.insert(0, './src')
from app.teams.manifest_validator import validate_manifest

is_valid, errors = validate_manifest('teams/manifest.json')
if not is_valid:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
print("✓ Manifest validation passed")
EOF
```

### Test 6: Package Validation

**Verify package contents:**
```bash
unzip -l teams-app-dev-1.0.0.zip
```

**Expected output:**
```
Archive:  teams-app-dev-1.0.0.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
     1234  01-01-2025 12:00   manifest.json
    12345  01-01-2025 12:00   color.png
     4321  01-01-2025 12:00   outline.png
---------                     -------
    17900                     3 files
```

**Validate package integrity:**
```bash
unzip -t teams-app-dev-1.0.0.zip
```

**Expected:** "No errors detected"

### Test 7: Teams Sideloading

**Steps:**
1. Open Microsoft Teams
2. Click Apps (left sidebar)
3. Click "Upload a custom app"
4. Select package file
5. Click "Add"

**Expected:** App installs without errors

**Common errors:**
- "App validation failed" → Check manifest schema
- "Bot not found" → Verify bot registration
- "Invalid bot ID" → Check bot ID substitution

### Test 8: Bot Conversation

**Test in Teams:**
1. Search for bot: "AI Agent"
2. Click bot to open chat
3. Send message: "hello"

**Expected:** Bot responds within 5 seconds

**Test commands:**
```
User: hello
Bot: Hello! I'm your AI assistant...

User: help
Bot: Here's what I can help you with...

User: status
Bot: System status: Running
      Agent: Initialized
      Version: 1.0.0
```

### Test 9: Application Insights

**View bot telemetry:**
```bash
# Get connection string
CONN_STRING=$(az monitor app-insights component show \
  --resource-group rg-teams-bot-dev \
  --app appi-dev-abc123 \
  --query connectionString -o tsv)

echo "Connection String: $CONN_STRING"
```

**Query logs in Azure Portal:**
1. Go to Application Insights resource
2. Navigate to Logs
3. Run query:

```kusto
traces
| where timestamp > ago(1h)
| where message contains "bot"
| order by timestamp desc
| limit 100
```

**Expected:** Bot activity logs

### Test 10: Container App Logs

**View real-time logs:**
```bash
az containerapp logs show \
  --name ca-dev-abc123 \
  --resource-group rg-teams-bot-dev \
  --follow
```

**Expected:** Application logs streaming

**Search for errors:**
```bash
az containerapp logs show \
  --name ca-dev-abc123 \
  --resource-group rg-teams-bot-dev \
  | grep -i error
```

## Troubleshooting Guide

### Issue: Bot Not Responding in Teams

**Symptoms:**
- Messages sent but no response
- Bot appears offline

**Diagnosis:**
```bash
# 1. Check Container App status
az containerapp show \
  --name ca-dev-abc123 \
  --resource-group rg-teams-bot-dev \
  --query "properties.runningStatus"

# 2. Check logs for errors
az containerapp logs show \
  --name ca-dev-abc123 \
  --resource-group rg-teams-bot-dev \
  --tail 50

# 3. Test health endpoint
curl https://ca-dev-abc123.azurecontainerapps.io/health
```

**Solutions:**
1. **Container App stopped:** Restart with `az containerapp restart`
2. **Application error:** Check logs for Python exceptions
3. **Environment variable missing:** Verify BOT_ID, BOT_PASSWORD set
4. **Key Vault access denied:** Add Container App managed identity to Key Vault

### Issue: 401 Unauthorized Errors

**Symptoms:**
- Bot Framework sends messages but gets 401 response

**Diagnosis:**
```bash
# 1. Verify bot credentials
az keyvault secret show \
  --vault-name kv-dev-abc123 \
  --name "bot-id"

# 2. Check Container App environment variables
az containerapp show \
  --name ca-dev-abc123 \
  --resource-group rg-teams-bot-dev \
  --query "properties.template.containers[0].env"

# 3. Test authentication
curl -X POST https://ca-dev-abc123.azurecontainerapps.io/api/messages \
  -H "Content-Type: application/json" \
  -d '{"type":"message"}' \
  -v
```

**Solutions:**
1. **Bot credentials mismatch:** Regenerate credentials and update Key Vault
2. **Environment variables not set:** Update Container App configuration
3. **Bot Service endpoint wrong:** Update Bot Service messaging endpoint

### Issue: Manifest Validation Fails

**Symptoms:**
- Teams rejects app package
- "App validation failed" error

**Diagnosis:**
```bash
# 1. Validate JSON
python3 -m json.tool teams/manifest.json

# 2. Check placeholders
grep "{{" teams/manifest.json

# 3. Validate schema
python3 -c "
import sys
sys.path.insert(0, './src')
from app.teams.manifest_validator import validate_manifest
is_valid, errors = validate_manifest('teams/manifest.json')
for error in errors:
    print(error)
"
```

**Solutions:**
1. **Invalid JSON:** Fix syntax errors
2. **Placeholders not substituted:** Run generate-teams-manifest.sh
3. **Missing required fields:** Add missing fields to manifest
4. **Wrong schema version:** Update manifestVersion to 1.16

### Issue: Icons Not Displaying

**Symptoms:**
- App installs but shows default icon
- Icon appears pixelated

**Diagnosis:**
```bash
# Check icon files exist
ls -lh teams/*.png

# Check icon dimensions (requires ImageMagick)
identify teams/color.png
identify teams/outline.png
```

**Expected dimensions:**
- color.png: 192x192 pixels
- outline.png: 32x32 pixels

**Solutions:**
1. **Icons missing:** Add PNG files to teams/ directory
2. **Wrong dimensions:** Resize icons to correct size
3. **Wrong format:** Convert to PNG format
4. **File too large:** Compress PNG files

### Issue: Bot Service Not Found

**Symptoms:**
- Bot registration doesn't exist in Azure
- Teams can't find bot ID

**Diagnosis:**
```bash
# Check if bot exists
az bot show \
  --name bot-teams-ai-agent-dev \
  --resource-group rg-teams-bot-dev

# Check bot list
az bot list \
  --resource-group rg-teams-bot-dev
```

**Solutions:**
1. **Bot not created:** Run create-bot-registration.sh
2. **Wrong resource group:** Check correct resource group name
3. **Wrong subscription:** Set correct subscription with `az account set`

### Issue: Endpoint Not Accessible

**Symptoms:**
- Health endpoint returns timeout or error
- curl fails to connect

**Diagnosis:**
```bash
# 1. Check Container App status
az containerapp show \
  --name ca-dev-abc123 \
  --resource-group rg-teams-bot-dev \
  --query "properties.{running:runningStatus,url:configuration.ingress.fqdn}"

# 2. Test DNS resolution
nslookup ca-dev-abc123.azurecontainerapps.io

# 3. Test connectivity
curl -v https://ca-dev-abc123.azurecontainerapps.io/health
```

**Solutions:**
1. **Container App stopped:** Start/restart app
2. **Ingress not enabled:** Enable ingress in Container App config
3. **Firewall blocking:** Check network security rules
4. **DNS not propagated:** Wait 5-10 minutes for DNS propagation

## Performance Testing

### Load Testing with Apache Bench

```bash
# Install ab (Apache Bench)
brew install apache2  # macOS
apt-get install apache2-utils  # Linux

# Test health endpoint (100 requests, 10 concurrent)
ab -n 100 -c 10 https://ca-dev-abc123.azurecontainerapps.io/health

# Analyze results
# - Requests per second
# - Time per request
# - Failed requests
```

**Expected performance:**
- Requests per second: > 50
- Mean time per request: < 200ms
- Failed requests: 0

### Rate Limiting Test

```bash
# Test rate limiting (send 20 requests rapidly)
for i in {1..20}; do
  curl -X POST https://ca-dev-abc123.azurecontainerapps.io/api/messages \
    -H "Content-Type: application/json" \
    -d '{"type":"message","text":"test"}' &
done
wait
```

**Expected:** Some requests return 429 (rate limit exceeded)

## Monitoring Setup

### Application Insights Alerts

Create alerts for:
- Failed requests > 10 in 5 minutes
- Response time > 2 seconds
- Exceptions > 5 in 10 minutes

```bash
# Create alert rule
az monitor metrics alert create \
  --name "High Error Rate" \
  --resource-group rg-teams-bot-dev \
  --scopes /subscriptions/.../resourceGroups/.../providers/Microsoft.ContainerApps/containerApps/ca-dev-abc123 \
  --condition "count requests > 10" \
  --window-size 5m \
  --evaluation-frequency 1m
```

### Container App Metrics

Monitor:
- CPU usage
- Memory usage
- Request count
- Response time
- Active revisions

```bash
# View metrics
az monitor metrics list \
  --resource ca-dev-abc123 \
  --resource-group rg-teams-bot-dev \
  --resource-type Microsoft.ContainerApps/containerApps \
  --metric Requests
```

## CI/CD Testing

Integrate tests into CI/CD pipeline:

```yaml
# Azure DevOps pipeline example
- task: Bash@3
  displayName: 'Run Deployment Tests'
  inputs:
    targetType: 'inline'
    script: |
      ./scripts/test-teams-deployment.sh \
        --resource-group $(RESOURCE_GROUP) \
        --bot-name $(BOT_NAME) \
        --endpoint $(BOT_ENDPOINT)

- task: PublishTestResults@2
  inputs:
    testResultsFormat: 'JUnit'
    testResultsFiles: '**/test-results.xml'
```

## Security Testing

### Vulnerability Scanning

```bash
# Scan Python dependencies
pip install safety
safety check -r src/requirements.txt

# Scan container image
trivy image <your-container-registry>/bot-app:latest
```

### Penetration Testing

Test security:
- SQL injection attempts
- XSS attempts
- CSRF attempts
- Authentication bypass
- Rate limiting bypass

**Note:** Only test against your own deployments with permission.

## Support Resources

- [Bot Framework Troubleshooting](https://docs.microsoft.com/azure/bot-service/bot-service-troubleshoot-general-problems)
- [Teams App Validation](https://docs.microsoft.com/microsoftteams/platform/concepts/deploy-and-publish/appsource/prepare/submission-checklist)
- [Container Apps Troubleshooting](https://docs.microsoft.com/azure/container-apps/troubleshooting)
- [Azure Support](https://azure.microsoft.com/support/)
