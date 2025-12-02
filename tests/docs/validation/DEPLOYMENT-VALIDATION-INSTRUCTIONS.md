# Deployment Validation Instructions
## Full Deployment Validation from Scratch

This document provides step-by-step instructions for executing a complete deployment validation of the MS Teams AI Agent.

---

## Overview

The deployment validation consists of:
1. **Automated Validation Script** - Runs complete end-to-end tests
2. **Manual Validation Report** - Comprehensive checklist for manual verification
3. **Performance Testing** - Response time and scalability validation

**Expected Time:** 20-30 minutes (including deployment)
**Target:** <15 minute deployment, <2 second response time

---

## Prerequisites

Before starting validation, ensure you have:

### Required Tools
- [ ] Azure CLI installed - `az version`
- [ ] Azure Developer CLI (azd) installed - `azd version`
- [ ] Docker installed and running - `docker --version`
- [ ] Git for repository access
- [ ] bash shell (macOS/Linux/WSL)

### Azure Access
- [ ] Active Azure subscription
- [ ] Contributor role or higher on subscription
- [ ] Logged in to Azure: `az login`
- [ ] Default subscription set: `az account set --subscription <subscription-id>`

### Project Setup
- [ ] Repository cloned
- [ ] On correct branch/commit
- [ ] `.env` file configured (if required)
- [ ] All Bicep files validated

---

## Quick Start

### Option 1: Automated Validation (Recommended)

Run the automated validation script:

```bash
# Full deployment + validation
./scripts/validate-full-deployment.sh --environment dev --location eastus

# Validate existing deployment
./scripts/validate-full-deployment.sh --environment dev --skip-deploy

# With automatic cleanup after
./scripts/validate-full-deployment.sh --environment dev --clean
```

**Output:**
- Console output with real-time test results
- Generated report: `deployment-validation-report-<timestamp>.md`

### Option 2: Manual Validation

Follow the manual checklist in `DEPLOYMENT-VALIDATION-REPORT.md`:

```bash
# 1. Deploy infrastructure
azd up --environment dev --location eastus

# 2. Run deployment tests
./scripts/test-teams-deployment.sh \
  --resource-group <rg-name> \
  --bot-name <bot-name> \
  --endpoint <endpoint-url>

# 3. Manual testing in Teams
# (Follow report checklist)
```

---

## Detailed Validation Steps

### Step 1: Pre-Deployment Checks

Verify all prerequisites are met:

```bash
# Check Azure CLI
az version

# Check authentication
az account show

# Check azd
azd version

# Check Docker
docker ps

# Validate Bicep files
az bicep build --file ./infra/main.bicep
```

**Expected Result:** All tools installed, Azure authenticated, Bicep valid

---

### Step 2: Run Full Deployment

Deploy infrastructure from scratch:

```bash
# Option A: Using automated script
./scripts/validate-full-deployment.sh --environment dev --location eastus

# Option B: Manual deployment
azd up --environment dev --location eastus
```

**Monitor:**
- Watch deployment progress
- Note any warnings or errors
- **Record total deployment time**

**Success Criteria:**
- ✅ Deployment completes without errors
- ✅ Total time <15 minutes
- ✅ All 10+ Azure resources created

---

### Step 3: Resource Validation

Verify all Azure resources are created:

```bash
# Get resource group name
RG_NAME=$(azd env get-values --environment dev | grep AZURE_RESOURCE_GROUP | cut -d= -f2 | tr -d '"')

# List all resources
az resource list --resource-group $RG_NAME --output table

# Count resources
az resource list --resource-group $RG_NAME --query "length(@)"
```

**Expected Resources:**
1. Resource Group
2. Container Apps Environment
3. Container Registry
4. Container App (API)
5. Azure OpenAI Service
6. GPT-4o Deployment
7. Bot Service
8. Key Vault
9. Log Analytics Workspace
10. Application Insights

**Verify each resource:**

```bash
# Container App
az containerapp list --resource-group $RG_NAME --output table

# Get Container App URL
CA_NAME=$(az containerapp list --resource-group $RG_NAME --query "[0].name" -o tsv)
CA_URL=$(az containerapp show --name $CA_NAME --resource-group $RG_NAME --query "properties.configuration.ingress.fqdn" -o tsv)
echo "Container App URL: https://$CA_URL"

# Key Vault
az keyvault list --resource-group $RG_NAME --output table

# Azure OpenAI
az cognitiveservices account list --resource-group $RG_NAME --output table

# Bot Service
az bot list --resource-group $RG_NAME --output table
```

---

### Step 4: Endpoint Testing

Test all endpoints are accessible:

```bash
# Get Container App URL (from Step 3)
BASE_URL="https://$CA_URL"

# Test health endpoint
curl -i $BASE_URL/health

# Test root endpoint
curl -i $BASE_URL/

# Test bot messages endpoint (should require auth)
curl -i $BASE_URL/api/messages

# Measure response time
time curl -s $BASE_URL/health > /dev/null
```

**Success Criteria:**
- ✅ Health endpoint returns 200 OK
- ✅ Root endpoint accessible
- ✅ Messages endpoint requires auth (401/403/405)
- ✅ Response time <2 seconds
- ✅ HTTPS enforced

---

### Step 5: Run Deployment Test Script

Execute the comprehensive deployment test:

```bash
# Get deployment details
RG_NAME=$(azd env get-values --environment dev | grep AZURE_RESOURCE_GROUP | cut -d= -f2 | tr -d '"')
BOT_NAME=$(az bot list --resource-group $RG_NAME --query "[0].name" -o tsv)
BOT_ENDPOINT="$BASE_URL/api/messages"

# Run tests
./scripts/test-teams-deployment.sh \
  --resource-group $RG_NAME \
  --bot-name $BOT_NAME \
  --endpoint $BOT_ENDPOINT
```

**Test Coverage:**
- ✅ Bot registration verification
- ✅ Bot endpoint configuration
- ✅ Teams channel enabled
- ✅ Endpoint accessibility
- ✅ Health checks
- ✅ Authentication validation
- ✅ Manifest validation
- ✅ Icon files present
- ✅ HTTPS enforcement

---

### Step 6: Teams App Testing

**Manual Testing Required:**

#### 6.1 Generate Teams App Package

```bash
# If not already generated by post-deploy hook
./scripts/create-teams-package.sh \
  --input ./teams \
  --output teams-app-dev.zip \
  --version 1.0.0 \
  --environment dev
```

#### 6.2 Upload to Teams

1. Open **Teams Admin Center**: https://admin.teams.microsoft.com/
2. Navigate to **Teams apps** > **Manage apps**
3. Click **Upload** > Upload custom app
4. Select `teams-app-dev.zip`
5. Wait for approval/publication

#### 6.3 Install Bot in Teams Client

1. Open Microsoft Teams desktop or web client
2. Go to **Apps** in left sidebar
3. Search for your bot name
4. Click **Add**
5. Start a chat with the bot

#### 6.4 Functional Testing

**Test 1: Basic Response**
```
User: Hello
Bot: (Should respond within 2 seconds)
```
- [ ] Response received
- [ ] Response time <2 seconds
- [ ] Response is appropriate

**Test 2: MCP Integration (if configured)**
```
User: Search Microsoft docs for Azure Container Apps
Bot: (Should call MCP tool and return results)
```
- [ ] MCP tool invoked
- [ ] Results returned
- [ ] Response time <2 seconds

**Test 3: Error Handling**
```
User: [Send gibberish or invalid command]
Bot: (Should handle gracefully)
```
- [ ] Error handled gracefully
- [ ] User-friendly error message
- [ ] No application crash

**Test 4: Multi-turn Conversation**
```
User: What can you do?
Bot: [Lists capabilities]
User: Tell me more about [capability]
Bot: [Provides details]
```
- [ ] Context maintained
- [ ] Responses coherent
- [ ] Performance consistent

---

### Step 7: Monitoring Validation

#### 7.1 Application Insights

```bash
# Get Application Insights name
AI_NAME=$(az monitor app-insights component list --resource-group $RG_NAME --query "[0].name" -o tsv)

# Open in portal
az monitor app-insights component show --app $AI_NAME --resource-group $RG_NAME
```

**Navigate to Azure Portal:**
1. Open Application Insights resource
2. Go to **Logs**
3. Run queries:

```kusto
// Recent requests
requests
| where timestamp > ago(1h)
| project timestamp, name, resultCode, duration
| order by timestamp desc
| take 20

// Errors
exceptions
| where timestamp > ago(1h)
| project timestamp, type, outerMessage
| order by timestamp desc

// Performance
requests
| where timestamp > ago(1h)
| summarize avg(duration), max(duration), count() by bin(timestamp, 5m)
| render timechart
```

**Verify:**
- [ ] Bot requests appearing in logs
- [ ] No critical errors
- [ ] Response times <2000ms
- [ ] Custom events tracked

#### 7.2 Container App Logs

```bash
# Stream container logs
az containerapp logs show --name $CA_NAME --resource-group $RG_NAME --follow

# View recent logs
az containerapp logs show --name $CA_NAME --resource-group $RG_NAME --tail 100
```

**Verify:**
- [ ] Application starting successfully
- [ ] No startup errors
- [ ] Bot messages logged
- [ ] Proper log levels

---

### Step 8: Performance Validation

#### 8.1 Response Time Testing

```bash
# Test health endpoint 10 times
for i in {1..10}; do
  time curl -s $BASE_URL/health > /dev/null
done

# Average response time calculation
echo "Testing response times..."
TOTAL=0
for i in {1..10}; do
  TIME=$(curl -s -o /dev/null -w "%{time_total}" $BASE_URL/health)
  echo "Request $i: ${TIME}s"
  TOTAL=$(echo "$TOTAL + $TIME" | bc)
done
AVG=$(echo "scale=3; $TOTAL / 10" | bc)
echo "Average response time: ${AVG}s"
```

**Success Criteria:**
- Average <2 seconds
- Max <3 seconds
- No timeouts

#### 8.2 Load Testing (Optional)

```bash
# Using Apache Bench (if installed)
ab -n 100 -c 10 $BASE_URL/health

# Or using curl in loop
for i in {1..100}; do
  curl -s $BASE_URL/health > /dev/null &
done
wait
```

**Monitor:**
- Container App CPU/Memory
- Response times
- Error rates

---

### Step 9: Security Validation

#### 9.1 HTTPS Enforcement

```bash
# All endpoints should redirect to HTTPS
curl -I http://${CA_URL}/health
```

**Verify:**
- [ ] Redirects to HTTPS
- [ ] TLS 1.2+ used

#### 9.2 Authentication

```bash
# Messages endpoint should require auth
curl -i $BASE_URL/api/messages

# Expected: 401 Unauthorized or 403 Forbidden
```

**Verify:**
- [ ] Unauthenticated requests blocked
- [ ] JWT validation active

#### 9.3 Key Vault Integration

```bash
# Check secrets are in Key Vault
KV_NAME=$(az keyvault list --resource-group $RG_NAME --query "[0].name" -o tsv)

# List secrets (names only)
az keyvault secret list --vault-name $KV_NAME --query "[].name" -o table
```

**Verify:**
- [ ] bot-id secret exists
- [ ] bot-password secret exists
- [ ] Other secrets as expected

#### 9.4 Managed Identity

```bash
# Check Container App managed identity
az containerapp show --name $CA_NAME --resource-group $RG_NAME --query "identity"
```

**Verify:**
- [ ] System-assigned identity enabled
- [ ] Identity has Key Vault access

---

### Step 10: Documentation and Reporting

#### 10.1 Complete Validation Report

Fill out `DEPLOYMENT-VALIDATION-REPORT.md` with:
- [ ] All test results
- [ ] Actual deployment time
- [ ] Performance metrics
- [ ] Any issues encountered
- [ ] Screenshots from Teams testing

---

## Troubleshooting

### Common Issues

#### Issue: Deployment takes >15 minutes

**Possible Causes:**
- Large container image
- Slow network
- Azure region capacity

**Solutions:**
- Optimize Dockerfile (multi-stage builds)
- Use Azure Container Registry closer to deployment region
- Try different Azure region

#### Issue: Container App not starting

**Check:**
```bash
# View container logs
az containerapp logs show --name $CA_NAME --resource-group $RG_NAME --tail 100

# Check revision status
az containerapp revision list --name $CA_NAME --resource-group $RG_NAME --output table
```

**Common Causes:**
- Environment variables missing
- Port configuration incorrect
- Application startup failures

#### Issue: Bot not responding in Teams

**Check:**
1. Bot registration completed
2. Teams channel enabled: `az bot msteams show --name $BOT_NAME --resource-group $RG_NAME`
3. Endpoint accessible from Teams servers
4. Bot credentials in Key Vault correct

#### Issue: High response times (>2 seconds)

**Investigate:**
- Container App scaling settings
- Azure OpenAI throttling
- Network latency
- Cold start times

**Optimize:**
- Adjust min/max replicas
- Enable always-on (if available)
- Optimize application startup

---

## Cleanup

### After Validation (Test Environment)

```bash
# Option 1: Using automated script
./scripts/validate-full-deployment.sh --environment dev --clean

# Option 2: Manual cleanup
azd down --purge --force --environment dev

# Verify all resources deleted
az resource list --resource-group $RG_NAME
```

### Keeping Environment (Dev/Production)

If keeping the environment:
- [ ] Document resource names and IDs
- [ ] Save deployment outputs
- [ ] Update documentation with actual values
- [ ] Schedule regular monitoring reviews

---

## Success Criteria Summary

### Must-Have ✅

- [X] Deployment completes in <15 minutes
- [X] All 10 Azure resources provisioned
- [X] Bot endpoint accessible via HTTPS
- [X] Health endpoint returns 200 OK
- [X] Bot responds in Teams client
- [X] Response time <2 seconds
- [X] No critical errors in logs
- [X] Security controls active (HTTPS, Auth, Key Vault)
- [X] Monitoring operational (Application Insights, logs)

### Nice-to-Have ⭐

- [ ] Deployment time <10 minutes
- [ ] Response time <1 second
- [ ] WAF configured (optional)
- [ ] Custom domain
- [ ] CI/CD pipeline integrated

---

## Next Steps After Validation

1. **Document Results**
   - Complete validation report
   - Note any issues or improvements needed
   - Update project documentation

2. **Address Issues**
   - Fix any failed tests
   - Optimize performance bottlenecks
   - Enhance security configurations

3. **Production Readiness**
   - Review production deployment plan
   - Set up monitoring alerts
   - Configure backup and disaster recovery
   - Document operational procedures

4. **Continuous Improvement**
   - Automate validation in CI/CD
   - Set up scheduled health checks
   - Monitor costs and optimize resources

---

## Resources

- **Scripts:**
  - `./scripts/validate-full-deployment.sh` - Automated validation
  - `./scripts/test-teams-deployment.sh` - Deployment tests
  - `./scripts/deploy-teams-bot.sh` - Bot deployment orchestrator

- **Documentation:**
  - `DEPLOYMENT-VALIDATION-REPORT.md` - Comprehensive checklist
  - `README.md` - Project overview
  - `infra/README.md` - Infrastructure documentation

- **Azure Documentation:**
  - [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)
  - [Azure Bot Service](https://learn.microsoft.com/azure/bot-service/)
  - [Teams App Development](https://learn.microsoft.com/microsoftteams/platform/)

---

**Validation Checklist Complete! 🚀**

For questions or issues, review troubleshooting section or consult project documentation.
