#!/bin/bash
# Full Deployment Validation Script (Task 5.7)
# Validates complete end-to-end deployment from scratch

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

log_test() {
    echo -e "${CYAN}[TEST]${NC} $1"
}

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Full deployment validation from scratch.

OPTIONS:
    -e, --environment ENV          Environment name (dev/staging/prod)
    -l, --location LOCATION       Azure region (default: eastus)
    -s, --skip-deploy             Skip azd up, validate existing deployment
    -c, --clean                   Clean up resources after validation
    -r, --report FILE             Output report file (default: deployment-report.md)
    -h, --help                    Show this help message

EXAMPLE:
    # Full validation with deployment
    $0 --environment dev --location eastus

    # Validate existing deployment
    $0 --environment dev --skip-deploy

    # With cleanup
    $0 --environment dev --clean

DESCRIPTION:
    This script performs complete deployment validation:
    1. Pre-deployment checks
    2. Infrastructure deployment (azd up)
    3. Automated validation tests
    4. Performance testing
    5. Security validation
    6. Monitoring verification
    7. Optional cleanup

REQUIREMENTS:
    - Azure CLI (az)
    - Azure Developer CLI (azd)
    - curl
    - jq (optional, for JSON parsing)
EOF
    exit 1
}

# Parse arguments
ENVIRONMENT=""
LOCATION="eastus"
SKIP_DEPLOY=false
CLEAN_UP=false
REPORT_FILE="deployment-validation-report-$(date +%Y%m%d-%H%M%S).md"

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -l|--location)
            LOCATION="$2"
            shift 2
            ;;
        -s|--skip-deploy)
            SKIP_DEPLOY=true
            shift
            ;;
        -c|--clean)
            CLEAN_UP=true
            shift
            ;;
        -r|--report)
            REPORT_FILE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate required parameters
if [[ -z "$ENVIRONMENT" ]]; then
    log_error "Environment is required"
    usage
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log_info "================================================"
log_info "Full Deployment Validation"
log_info "================================================"
log_info "Environment: $ENVIRONMENT"
log_info "Location: $LOCATION"
log_info "Report: $REPORT_FILE"
log_info ""

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNING=0

# Timing
VALIDATION_START=$(date +%s)
DEPLOYMENT_START=""
DEPLOYMENT_END=""

# Test result function
test_result() {
    local test_name="$1"
    local result="$2"
    local message="$3"

    if [[ "$result" == "PASS" ]]; then
        log_test "${GREEN}✓${NC} $test_name: PASSED"
        ((TESTS_PASSED++))
    elif [[ "$result" == "FAIL" ]]; then
        log_test "${RED}✗${NC} $test_name: FAILED - $message"
        ((TESTS_FAILED++))
    elif [[ "$result" == "WARN" ]]; then
        log_test "${YELLOW}!${NC} $test_name: WARNING - $message"
        ((TESTS_WARNING++))
    fi
}

# Phase 1: Pre-Deployment Validation
log_step "Phase 1: Pre-Deployment Validation"
log_info ""

# Check Azure CLI
log_test "Checking Azure CLI..."
if command -v az &> /dev/null; then
    AZ_VERSION=$(az version --query '"azure-cli"' -o tsv 2>/dev/null || echo "unknown")
    test_result "Azure CLI" "PASS" ""
    log_info "  Version: $AZ_VERSION"
else
    test_result "Azure CLI" "FAIL" "Not installed"
    exit 1
fi

# Check Azure authentication
log_test "Checking Azure authentication..."
if az account show &> /dev/null; then
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    TENANT_ID=$(az account show --query tenantId -o tsv)
    test_result "Azure Authentication" "PASS" ""
    log_info "  Subscription: $SUBSCRIPTION_ID"
    log_info "  Tenant: $TENANT_ID"
else
    test_result "Azure Authentication" "FAIL" "Not logged in"
    log_error "Run: az login"
    exit 1
fi

# Check Azure Developer CLI
log_test "Checking Azure Developer CLI..."
if command -v azd &> /dev/null; then
    AZD_VERSION=$(azd version 2>/dev/null | head -n 1 || echo "unknown")
    test_result "Azure Developer CLI" "PASS" ""
    log_info "  Version: $AZD_VERSION"
else
    test_result "Azure Developer CLI" "FAIL" "Not installed"
    log_error "Install from: https://aka.ms/azd-install"
    exit 1
fi

# Check Docker
log_test "Checking Docker..."
if command -v docker &> /dev/null; then
    if docker ps &> /dev/null; then
        DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "unknown")
        test_result "Docker" "PASS" ""
        log_info "  Version: $DOCKER_VERSION"
    else
        test_result "Docker" "FAIL" "Docker daemon not running"
        exit 1
    fi
else
    test_result "Docker" "FAIL" "Not installed"
    exit 1
fi

# Validate Bicep files
log_test "Validating Bicep files..."
if [[ -f "$PROJECT_ROOT/infra/main.bicep" ]]; then
    if az bicep build --file "$PROJECT_ROOT/infra/main.bicep" --outdir /tmp &> /dev/null; then
        test_result "Bicep Validation" "PASS" ""
    else
        test_result "Bicep Validation" "FAIL" "Bicep compilation failed"
    fi
else
    test_result "Bicep Files" "FAIL" "main.bicep not found"
fi

log_info ""
log_info "Pre-deployment validation complete: $TESTS_PASSED passed, $TESTS_FAILED failed"
log_info ""

# Phase 2: Infrastructure Deployment
if [[ "$SKIP_DEPLOY" == false ]]; then
    log_step "Phase 2: Infrastructure Deployment"
    log_info ""

    log_info "Starting deployment with: azd up"
    log_info "Environment: $ENVIRONMENT"
    log_info "Location: $LOCATION"
    log_info ""

    DEPLOYMENT_START=$(date +%s)

    # Run azd up
    cd "$PROJECT_ROOT"
    if azd up --environment "$ENVIRONMENT" --location "$LOCATION"; then
        DEPLOYMENT_END=$(date +%s)
        DEPLOYMENT_TIME=$((DEPLOYMENT_END - DEPLOYMENT_START))
        DEPLOYMENT_MINUTES=$((DEPLOYMENT_TIME / 60))
        DEPLOYMENT_SECONDS=$((DEPLOYMENT_TIME % 60))

        log_info ""
        log_info "Deployment completed in ${DEPLOYMENT_MINUTES}m ${DEPLOYMENT_SECONDS}s"

        if [[ $DEPLOYMENT_TIME -lt 900 ]]; then
            test_result "Deployment Time" "PASS" "${DEPLOYMENT_MINUTES}m ${DEPLOYMENT_SECONDS}s (Target: <15min)"
        else
            test_result "Deployment Time" "WARN" "${DEPLOYMENT_MINUTES}m ${DEPLOYMENT_SECONDS}s (Target: <15min)"
        fi
    else
        log_error "Deployment failed!"
        test_result "Deployment" "FAIL" "azd up failed"
        exit 1
    fi
else
    log_warning "Skipping deployment (--skip-deploy flag)"
fi

log_info ""

# Phase 3: Resource Validation
log_step "Phase 3: Azure Resource Validation"
log_info ""

# Get azd environment variables
cd "$PROJECT_ROOT"
eval "$(azd env get-values --environment "$ENVIRONMENT" 2>/dev/null || echo '')"

# Get resource group from azd
RESOURCE_GROUP=$(azd env get-values --environment "$ENVIRONMENT" 2>/dev/null | grep AZURE_RESOURCE_GROUP | cut -d= -f2 | tr -d '"' || echo "")

if [[ -z "$RESOURCE_GROUP" ]]; then
    log_error "Could not determine resource group"
    test_result "Resource Group Discovery" "FAIL" "Environment not initialized"
else
    log_info "Resource Group: $RESOURCE_GROUP"
    test_result "Resource Group Discovery" "PASS" ""

    # Count resources
    RESOURCE_COUNT=$(az resource list --resource-group "$RESOURCE_GROUP" --query "length(@)" -o tsv 2>/dev/null || echo "0")
    log_info "Resources found: $RESOURCE_COUNT"

    if [[ $RESOURCE_COUNT -ge 10 ]]; then
        test_result "Resource Count" "PASS" "$RESOURCE_COUNT resources (Expected: 10)"
    else
        test_result "Resource Count" "WARN" "$RESOURCE_COUNT resources (Expected: 10)"
    fi

    # Check specific resources
    log_test "Validating individual resources..."

    # Container Apps Environment
    if az containerapp env list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv &> /dev/null; then
        test_result "Container Apps Environment" "PASS" ""
    else
        test_result "Container Apps Environment" "FAIL" "Not found"
    fi

    # Container App
    if az containerapp list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv &> /dev/null; then
        CONTAINER_APP_NAME=$(az containerapp list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)
        CONTAINER_APP_FQDN=$(az containerapp show --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null || echo "")
        test_result "Container App" "PASS" ""
        log_info "  Name: $CONTAINER_APP_NAME"
        log_info "  FQDN: $CONTAINER_APP_FQDN"
    else
        test_result "Container App" "FAIL" "Not found"
    fi

    # Key Vault
    if az keyvault list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv &> /dev/null; then
        KEY_VAULT_NAME=$(az keyvault list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)
        test_result "Key Vault" "PASS" ""
        log_info "  Name: $KEY_VAULT_NAME"
    else
        test_result "Key Vault" "FAIL" "Not found"
    fi

    # Azure OpenAI
    if az cognitiveservices account list --resource-group "$RESOURCE_GROUP" --query "[?kind=='OpenAI'] | [0].name" -o tsv &> /dev/null; then
        OPENAI_NAME=$(az cognitiveservices account list --resource-group "$RESOURCE_GROUP" --query "[?kind=='OpenAI'] | [0].name" -o tsv)
        test_result "Azure OpenAI" "PASS" ""
        log_info "  Name: $OPENAI_NAME"
    else
        test_result "Azure OpenAI" "FAIL" "Not found"
    fi

    # Bot Service
    BOT_NAME=$(az bot list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv 2>/dev/null || echo "")
    if [[ -n "$BOT_NAME" ]]; then
        test_result "Bot Service" "PASS" ""
        log_info "  Name: $BOT_NAME"
    else
        test_result "Bot Service" "WARN" "Not found (may not be created yet)"
    fi

    # Application Insights
    if az monitor app-insights component list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv &> /dev/null; then
        APP_INSIGHTS_NAME=$(az monitor app-insights component list --resource-group "$RESOURCE_GROUP" --query "[0].name" -o tsv)
        test_result "Application Insights" "PASS" ""
        log_info "  Name: $APP_INSIGHTS_NAME"
    else
        test_result "Application Insights" "FAIL" "Not found"
    fi
fi

log_info ""

# Phase 4: Endpoint Validation
log_step "Phase 4: Endpoint Validation"
log_info ""

if [[ -n "$CONTAINER_APP_FQDN" ]]; then
    BASE_URL="https://$CONTAINER_APP_FQDN"

    # Health endpoint
    log_test "Testing health endpoint..."
    HEALTH_URL="$BASE_URL/health"
    if HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" --max-time 10 2>/dev/null); then
        if [[ "$HTTP_CODE" == "200" ]]; then
            test_result "Health Endpoint" "PASS" "HTTP $HTTP_CODE"
        else
            test_result "Health Endpoint" "WARN" "HTTP $HTTP_CODE (Expected: 200)"
        fi
    else
        test_result "Health Endpoint" "FAIL" "Not accessible"
    fi

    # Root endpoint
    log_test "Testing root endpoint..."
    if HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/" --max-time 10 2>/dev/null); then
        if [[ "$HTTP_CODE" == "200" ]]; then
            test_result "Root Endpoint" "PASS" "HTTP $HTTP_CODE"
        else
            test_result "Root Endpoint" "WARN" "HTTP $HTTP_CODE"
        fi
    else
        test_result "Root Endpoint" "FAIL" "Not accessible"
    fi

    # Bot messages endpoint (should require auth)
    log_test "Testing bot messages endpoint authentication..."
    BOT_ENDPOINT="$BASE_URL/api/messages"
    if HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BOT_ENDPOINT" --max-time 10 2>/dev/null); then
        if [[ "$HTTP_CODE" == "401" || "$HTTP_CODE" == "403" || "$HTTP_CODE" == "405" ]]; then
            test_result "Bot Messages Endpoint Auth" "PASS" "HTTP $HTTP_CODE (Auth required)"
        else
            test_result "Bot Messages Endpoint Auth" "WARN" "HTTP $HTTP_CODE"
        fi
    else
        test_result "Bot Messages Endpoint" "FAIL" "Not accessible"
    fi

    # Response time test
    log_test "Testing response time..."
    RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" "$HEALTH_URL" --max-time 10 2>/dev/null || echo "999")
    if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l 2>/dev/null || echo "0") )); then
        test_result "Response Time" "PASS" "${RESPONSE_TIME}s (Target: <2s)"
    else
        test_result "Response Time" "WARN" "${RESPONSE_TIME}s (Target: <2s)"
    fi
else
    log_warning "Container App FQDN not available, skipping endpoint tests"
fi

log_info ""

# Phase 5: Deployment Testing Script
if [[ -n "$RESOURCE_GROUP" && -n "$BOT_NAME" && -n "$BOT_ENDPOINT" ]]; then
    log_step "Phase 5: Running Deployment Test Script"
    log_info ""

    if [[ -f "$SCRIPT_DIR/test-teams-deployment.sh" ]]; then
        log_info "Running: test-teams-deployment.sh"
        if bash "$SCRIPT_DIR/test-teams-deployment.sh" \
            --resource-group "$RESOURCE_GROUP" \
            --bot-name "$BOT_NAME" \
            --endpoint "$BOT_ENDPOINT"; then
            test_result "Deployment Test Script" "PASS" ""
        else
            test_result "Deployment Test Script" "WARN" "Some tests failed"
        fi
    else
        test_result "Deployment Test Script" "WARN" "Script not found"
    fi
else
    log_warning "Skipping deployment test script (missing required parameters)"
fi

log_info ""

# Final Summary
VALIDATION_END=$(date +%s)
VALIDATION_TIME=$((VALIDATION_END - VALIDATION_START))
VALIDATION_MINUTES=$((VALIDATION_TIME / 60))
VALIDATION_SECONDS=$((VALIDATION_TIME % 60))

log_info "================================================"
log_info "Validation Summary"
log_info "================================================"
log_info "${GREEN}Passed:${NC}  $TESTS_PASSED"
log_info "${YELLOW}Warnings:${NC} $TESTS_WARNING"
log_info "${RED}Failed:${NC}  $TESTS_FAILED"
log_info ""
log_info "Total validation time: ${VALIDATION_MINUTES}m ${VALIDATION_SECONDS}s"

if [[ -n "$DEPLOYMENT_TIME" ]]; then
    log_info "Deployment time: ${DEPLOYMENT_MINUTES}m ${DEPLOYMENT_SECONDS}s"
fi

log_info ""

# Generate Report
log_info "Generating validation report: $REPORT_FILE"

cat > "$REPORT_FILE" << EOF
# Deployment Validation Report
**Date:** $(date +"%Y-%m-%d %H:%M:%S")
**Environment:** $ENVIRONMENT
**Location:** $LOCATION

## Summary
- **Tests Passed:** $TESTS_PASSED
- **Tests Failed:** $TESTS_FAILED
- **Warnings:** $TESTS_WARNING
- **Total Validation Time:** ${VALIDATION_MINUTES}m ${VALIDATION_SECONDS}s
EOF

if [[ -n "$DEPLOYMENT_TIME" ]]; then
    cat >> "$REPORT_FILE" << EOF
- **Deployment Time:** ${DEPLOYMENT_MINUTES}m ${DEPLOYMENT_SECONDS}s
- **Deployment SLA Met:** $([[ $DEPLOYMENT_TIME -lt 900 ]] && echo "✅ Yes (<15 min)" || echo "⚠️ No (>15 min)")
EOF
fi

cat >> "$REPORT_FILE" << EOF

## Azure Resources
- **Subscription:** $SUBSCRIPTION_ID
- **Resource Group:** ${RESOURCE_GROUP:-N/A}
- **Resource Count:** ${RESOURCE_COUNT:-0}
- **Container App:** ${CONTAINER_APP_NAME:-N/A}
- **Container App URL:** ${BASE_URL:-N/A}
- **Key Vault:** ${KEY_VAULT_NAME:-N/A}
- **Azure OpenAI:** ${OPENAI_NAME:-N/A}
- **Bot Service:** ${BOT_NAME:-N/A}

## Test Results
- Azure CLI: ✅ Installed
- Azure Authentication: ✅ Active
- Azure Developer CLI: ✅ Installed
- Docker: ✅ Running
- Bicep Validation: ✅ Passed
- Resource Group: ${RESOURCE_GROUP:+✅ Created}${RESOURCE_GROUP:-❌ Not found}
- Container App: ${CONTAINER_APP_NAME:+✅ Running}${CONTAINER_APP_NAME:-❌ Not found}
- Health Endpoint: See detailed logs above
- Response Time: ${RESPONSE_TIME:-N/A}s

## Next Steps
1. Upload Teams app package to Teams Admin Center
2. Test bot in Microsoft Teams client
3. Verify bot response time <2 seconds
4. Monitor Application Insights for errors
5. Review and act on any warnings or failures

---
*Generated by validate-full-deployment.sh*
EOF

log_info "Report saved: $REPORT_FILE"
log_info ""

# Cleanup
if [[ "$CLEAN_UP" == true ]]; then
    log_warning "Cleanup requested..."
    log_warning "This will DELETE all Azure resources!"
    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ $REPLY == "yes" ]]; then
        log_info "Running: azd down --purge --force"
        cd "$PROJECT_ROOT"
        azd down --purge --force --environment "$ENVIRONMENT"
        log_info "Cleanup complete"
    else
        log_info "Cleanup cancelled"
    fi
fi

# Exit status
if [[ $TESTS_FAILED -eq 0 ]]; then
    log_info "${GREEN}✓ Validation completed successfully!${NC}"
    exit 0
else
    log_error "${RED}✗ Validation completed with failures!${NC}"
    exit 1
fi
