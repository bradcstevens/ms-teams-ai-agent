# MS Teams AI Agent - Operations Guide

This document covers operational procedures for monitoring, maintaining, and troubleshooting the MS Teams AI Agent in production.

## Monitoring

### Application Insights Dashboard

Access Application Insights through the Azure Portal:

```bash
# Get Application Insights connection info
az monitor app-insights component show \
  --resource-group <rg-name> \
  --app <app-insights-name>
```

#### Key Metrics to Monitor

| Metric | Alert Threshold | Description |
|--------|-----------------|-------------|
| Request Duration (p95) | > 2000ms | Bot response time |
| Failed Requests | > 5% | Error rate |
| Dependency Duration | > 1000ms | OpenAI/MCP latency |
| Exceptions | Any | Application errors |
| Server Response Time | > 500ms | Health endpoint |

#### Recommended Alerts

```bash
# Create response time alert
az monitor metrics alert create \
  --name "BotResponseTime" \
  --resource-group <rg-name> \
  --scopes <app-insights-resource-id> \
  --condition "avg requests/duration > 2000" \
  --window-size 5m \
  --evaluation-frequency 1m
```

### Log Analytics Queries

#### Recent Errors
```kusto
traces
| where severityLevel >= 3
| where timestamp > ago(1h)
| order by timestamp desc
| project timestamp, message, operation_Name
| take 50
```

#### Bot Response Times
```kusto
requests
| where name contains "api/messages"
| where timestamp > ago(24h)
| summarize
    avg(duration),
    percentile(duration, 95),
    percentile(duration, 99)
  by bin(timestamp, 1h)
| render timechart
```

#### OpenAI API Calls
```kusto
dependencies
| where type == "HTTP" and target contains "openai"
| where timestamp > ago(1h)
| summarize count(), avg(duration) by bin(timestamp, 5m)
| render timechart
```

#### MCP Server Health
```kusto
customEvents
| where name == "MCPServerCall"
| where timestamp > ago(1h)
| summarize
    successCount = countif(customDimensions.success == "true"),
    failureCount = countif(customDimensions.success == "false")
  by bin(timestamp, 5m), tostring(customDimensions.serverName)
```

### Container Logs

```bash
# Stream live logs
az containerapp logs show \
  --name <container-app-name> \
  --resource-group <rg-name> \
  --follow

# Get recent logs
az containerapp logs show \
  --name <container-app-name> \
  --resource-group <rg-name> \
  --tail 100
```

## Health Checks

### Endpoint Health

```bash
# Check health endpoint
curl -s https://<container-app-fqdn>/health | jq .

# Expected response
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-25T12:00:00Z"
}
```

### Azure Resource Health

```bash
# Check Container App status
az containerapp show \
  --name <container-app-name> \
  --resource-group <rg-name> \
  --query "properties.runningStatus"

# Check Bot Service status
az bot show \
  --name <bot-name> \
  --resource-group <rg-name> \
  --query "properties.provisioningState"
```

### MCP Server Health Check

```bash
# Via health endpoint (if implemented)
curl -s https://<container-app-fqdn>/health/mcp | jq .

# Expected response
{
  "servers": {
    "filesystem": {"status": "healthy", "tools": 5},
    "web-search": {"status": "healthy", "tools": 2}
  }
}
```

## Common Operations

### Restart Container App

```bash
# Restart all replicas
az containerapp revision restart \
  --name <container-app-name> \
  --resource-group <rg-name> \
  --revision <revision-name>

# Force new revision deployment
az containerapp update \
  --name <container-app-name> \
  --resource-group <rg-name> \
  --set-env-vars "RESTART_TRIGGER=$(date +%s)"
```

### Scale Container App

```bash
# Manual scaling
az containerapp update \
  --name <container-app-name> \
  --resource-group <rg-name> \
  --min-replicas 2 \
  --max-replicas 10

# Check current replicas
az containerapp replica list \
  --name <container-app-name> \
  --resource-group <rg-name> \
  --query "[].name"
```

### Update Configuration

```bash
# Update environment variable
az containerapp update \
  --name <container-app-name> \
  --resource-group <rg-name> \
  --set-env-vars "LOG_LEVEL=DEBUG"

# Update from Key Vault
az containerapp update \
  --name <container-app-name> \
  --resource-group <rg-name> \
  --set-env-vars "BOT_PASSWORD=secretref:bot-password"
```

### Rotate Secrets

```bash
# 1. Update secret in Key Vault
az keyvault secret set \
  --vault-name <vault-name> \
  --name "bot-password" \
  --value "<new-password>"

# 2. Restart container to pick up new secret
az containerapp revision restart \
  --name <container-app-name> \
  --resource-group <rg-name> \
  --revision <current-revision>

# 3. Update Bot Service (if needed)
az bot update \
  --name <bot-name> \
  --resource-group <rg-name> \
  --endpoint "https://<container-app-fqdn>/api/messages"
```

## Troubleshooting

### Bot Not Responding in Teams

1. **Check Container App Health**
   ```bash
   curl -s https://<container-app-fqdn>/health
   ```

2. **Verify Bot Service Endpoint**
   ```bash
   az bot show --name <bot-name> --resource-group <rg-name> \
     --query "properties.endpoint"
   ```

3. **Check Application Insights for Errors**
   ```kusto
   exceptions
   | where timestamp > ago(1h)
   | where operation_Name contains "messages"
   | project timestamp, problemId, outerMessage
   ```

4. **Validate Bot Credentials**
   ```bash
   # Ensure secrets match
   az keyvault secret show --vault-name <vault-name> --name bot-app-id
   az keyvault secret show --vault-name <vault-name> --name bot-password
   ```

### Slow Response Times

1. **Check OpenAI Latency**
   ```kusto
   dependencies
   | where target contains "openai"
   | summarize avg(duration), percentile(duration, 95) by bin(timestamp, 5m)
   ```

2. **Check MCP Server Performance**
   ```kusto
   customEvents
   | where name == "MCPServerCall"
   | summarize avg(todouble(customDimensions.duration)) by serverName
   ```

3. **Review Container Resources**
   ```bash
   az containerapp show --name <app-name> --resource-group <rg-name> \
     --query "properties.template.containers[0].resources"
   ```

### MCP Server Failures

1. **Check Circuit Breaker Status**
   ```kusto
   customEvents
   | where name == "CircuitBreakerTripped"
   | where timestamp > ago(1h)
   ```

2. **Review Server Logs**
   ```kusto
   traces
   | where message contains "MCP"
   | where severityLevel >= 2
   | order by timestamp desc
   ```

3. **Restart Specific Server**
   - Update `mcp_servers.json` to disable/enable server
   - Restart container to reload configuration

### Deployment Failures

1. **Check Provisioning Logs**
   ```bash
   az deployment group show \
     --resource-group <rg-name> \
     --name <deployment-name> \
     --query "properties.error"
   ```

2. **Validate Bicep Templates**
   ```bash
   az bicep build --file infra/main.bicep
   ```

3. **Check Container Build Logs**
   ```bash
   az acr task logs --registry <acr-name> --run-id <run-id>
   ```

## Backup & Recovery

### Configuration Backup

```bash
# Export environment variables
azd env get-values > env-backup-$(date +%Y%m%d).txt

# Backup Key Vault secrets list
az keyvault secret list --vault-name <vault-name> \
  --query "[].name" -o tsv > secrets-list-backup.txt
```

### Disaster Recovery

1. **Full Redeployment**
   ```bash
   # In case of complete failure, redeploy from scratch
   azd down --force --purge
   azd up
   ```

2. **Restore from Previous Revision**
   ```bash
   # List revisions
   az containerapp revision list \
     --name <container-app-name> \
     --resource-group <rg-name>

   # Activate previous revision
   az containerapp revision activate \
     --name <container-app-name> \
     --resource-group <rg-name> \
     --revision <previous-revision-name>
   ```

## Maintenance Windows

### Recommended Practices

1. **Schedule deployments during low-usage periods**
2. **Use blue-green deployment with revision management**
3. **Monitor for 15 minutes after any change**
4. **Keep previous revision active as fallback**

### Pre-Maintenance Checklist

- [ ] Notify stakeholders of maintenance window
- [ ] Verify backup of current configuration
- [ ] Test rollback procedure
- [ ] Have support contacts ready
- [ ] Monitor dashboards during change

### Post-Maintenance Checklist

- [ ] Verify health endpoints responding
- [ ] Check Application Insights for new errors
- [ ] Validate bot responding in Teams
- [ ] Monitor for 15 minutes minimum
- [ ] Update change log

## Performance Tuning

### Container Resources

```yaml
# Recommended starting configuration
resources:
  cpu: 0.5
  memory: 1Gi

# For higher load
resources:
  cpu: 1.0
  memory: 2Gi
```

### Scaling Configuration

```yaml
# Conservative scaling
minReplicas: 1
maxReplicas: 5
scale:
  rules:
    - name: http-rule
      http:
        metadata:
          concurrentRequests: 50

# Aggressive scaling for high traffic
minReplicas: 2
maxReplicas: 20
scale:
  rules:
    - name: http-rule
      http:
        metadata:
          concurrentRequests: 25
```

### OpenAI Optimization

- Use streaming responses for long outputs
- Implement response caching for common queries
- Set appropriate max_tokens limits
- Monitor token usage and adjust as needed

---

## Known Issues & Limitations

### Infrastructure

| Issue | Impact | Workaround |
|-------|--------|------------|
| Bicep name length warnings (BCP335) | Resource creation may fail with long environment names | Use short environment names (< 10 chars) |
| MCP server config requires restart | No hot reload for `mcp_servers.json` changes | Restart container after config changes |

### Application

| Issue | Impact | Workaround |
|-------|--------|------------|
| In-memory conversation state | Multi-turn conversations lost on restart | Users restart conversation after deployments |
| Single-stage Dockerfile | Larger image size, slower deploys | None required - works correctly |

### Technical Debt Priorities

**High Priority:**
- Implement proper message queue for async processing
- Increase test coverage to 80%+
- Add proper health check with dependency status
- Implement rate limiting per user
- Add proper audit logging

**Medium Priority:**
- Implement dependency injection container
- Add request/response caching layer
- Implement blue-green deployment strategy
- Add security headers middleware

For detailed issue tracking, see the project issue tracker.

---

## Related Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
- [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) - Development setup and workflow
- [MCP_INTEGRATION.md](./MCP_INTEGRATION.md) - MCP server configuration
- [TEAMS_GUIDE.md](./TEAMS_GUIDE.md) - Teams deployment and testing

---
*Last Updated: 2025-12-01*
