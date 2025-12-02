# Deployment Validation Instructions

This document describes how to validate the MS Teams AI Agent deployment against all PRD success criteria.

## Quick Start

Run the comprehensive acceptance criteria validation:

```bash
./scripts/validate-acceptance-criteria.sh
```

This generates a detailed report in `validation-report-TIMESTAMP.md`.

## Validation Categories

The validation script checks 33+ criteria across 5 categories:

### 1. Deployment Automation (8 tests)
- azure.yaml configuration
- Bicep infrastructure modules
- Container image configuration
- Bicep outputs completeness
- azd hooks configuration
- Resource tagging strategy
- Deployment scripts availability

### 2. Teams Integration (7 tests)
- Teams manifest template
- Bot icons (color/outline)
- Bot Framework SDK dependencies
- Bot messages endpoint implementation
- Bot Service Bicep module
- Teams channel configuration
- Typing indicator support

### 3. MCP Integration (7 tests)
- MCP configuration file
- At least 2 MCP servers configured
- MCP SDK dependencies
- MCP client implementation
- MCP tool discovery
- MCP error handling
- MCP integration tests

### 4. Monitoring & Observability (5 tests)
- Application Insights Bicep module
- Log Analytics Workspace
- Telemetry SDK configuration
- Structured logging
- Health check endpoint

### 5. Documentation (7 tests)
- README comprehensiveness
- Setup instructions
- Environment template file
- Environment variables in README
- Architecture documentation
- Troubleshooting section
- Scripts documentation

## Command Options

```bash
# Full validation (default)
./scripts/validate-acceptance-criteria.sh

# Validate specific Azure environment
./scripts/validate-acceptance-criteria.sh --environment dev

# Skip deployment-specific tests (pre-deployment)
./scripts/validate-acceptance-criteria.sh --skip-deployment

# Quick validation (skip slow tests)
./scripts/validate-acceptance-criteria.sh --quick

# Custom output file
./scripts/validate-acceptance-criteria.sh --output my-report.md
```

## Full Deployment Validation

For complete end-to-end deployment validation including Azure resources:

```bash
./scripts/validate-full-deployment.sh \
  --environment dev \
  --location eastus
```

This will:
1. Validate pre-deployment requirements
2. Run `azd up` deployment
3. Verify Azure resources creation
4. Test endpoints and response times
5. Run deployment test scripts
6. Generate comprehensive report

## PRD Success Criteria Reference

The validation covers all success criteria from PRD Appendix C:

### Deployment Automation
- [ ] `azd up` completes without errors in <15 minutes
- [ ] All Azure resources created with correct names and tags
- [ ] Container image built and pushed to ACR successfully
- [ ] Container App running with green health status
- [ ] Bot Service registered and configured for Teams channel
- [ ] Key Vault populated with all required secrets
- [ ] Application Insights receiving telemetry

### Teams Integration
- [ ] Bot appears in Teams app catalog after manifest upload
- [ ] Bot can be added to a Teams channel
- [ ] Bot responds to @mentions in channel within 2 seconds
- [ ] Bot responds to direct messages within 2 seconds
- [ ] Bot maintains conversation context across messages
- [ ] Bot displays typing indicator while processing

### MCP Integration
- [ ] At least 2 MCP servers configured in mcp_servers.json
- [ ] MCP servers successfully discovered on agent startup
- [ ] Agent can list available tools from MCP servers
- [ ] Agent successfully invokes tools from MCP servers
- [ ] Tool results properly integrated into responses
- [ ] Adding new MCP server to config works after restart

### Monitoring and Observability
- [ ] Application Insights shows request telemetry
- [ ] Azure OpenAI API calls logged correctly
- [ ] Error conditions logged with stack traces
- [ ] Bot Framework protocol messages captured
- [ ] MCP server interactions traced

### Documentation
- [ ] README provides clear setup instructions
- [ ] All environment variables documented
- [ ] Troubleshooting section covers common issues
- [ ] Architecture diagrams included and accurate
- [ ] New developer can deploy successfully in <30 minutes

## Interpreting Results

### Pass Rates
- **100%**: All criteria met - ready for production
- **90%+**: Minor issues only - review warnings
- **80%+**: Some issues need attention before deployment
- **<80%**: Significant gaps - address failures first

### Result Types
- **PASS**: Criterion fully met
- **FAIL**: Critical issue - must fix before deployment
- **WARN**: Minor issue - should address but not blocking
- **SKIP**: Test skipped (dependencies not available)

## Troubleshooting Common Failures

### Bicep Compilation Failure
```bash
# Check for specific errors
az bicep build --file infra/main.bicep 2>&1

# Common fixes:
# - Check output property names match module exports
# - Verify parameter references are correct
# - Update Bicep CLI: az bicep upgrade
```

### Missing Dependencies
```bash
# Verify Python dependencies
pip install -r src/requirements.txt

# Verify Node.js dependencies (for MCP servers)
npm install

# Verify Azure CLI
az version
azd version
```

### Teams Integration Issues
```bash
# Validate Teams manifest
./scripts/generate-teams-manifest.sh

# Check bot registration
./scripts/create-bot-registration.sh --check
```

## Related Documentation

- [README.md](../../README.md) - Project overview and quick start
- [TEAMS_GUIDE.md](../TEAMS_GUIDE.md) - Teams deployment and testing
- [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md) - Development setup and workflow
- [OPERATIONS.md](../OPERATIONS.md) - Monitoring and troubleshooting
- [MCP_INTEGRATION.md](../MCP_INTEGRATION.md) - MCP server configuration

---
*Last Updated: 2025-12-01*
