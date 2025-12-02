#!/usr/bin/env bash
# Networking Validation Script
# Tests for Networking & Environment Bicep Modules

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

echo "=========================================="
echo "Networking & Environment Validation"
echo "=========================================="
echo ""

# Test function
test() {
    local name="$1"
    local command="$2"

    echo -n "Testing: $name ... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

# ============================================
# Module File Existence Tests
# ============================================
echo "==> Module File Tests"
test "Log Analytics module exists" "[ -f core/monitor/loganalytics.bicep ]"
test "Application Insights module exists" "[ -f core/monitor/applicationinsights.bicep ]"
test "Container Apps Environment module exists" "[ -f core/host/container-apps-environment.bicep ]"

# ============================================
# Bicep Compilation Tests
# ============================================
echo ""
echo "==> Bicep Compilation Tests"
test "Log Analytics compiles" "az bicep build --file core/monitor/loganalytics.bicep --stdout"
test "Application Insights compiles" "az bicep build --file core/monitor/applicationinsights.bicep --stdout"
test "Container Apps Environment compiles" "az bicep build --file core/host/container-apps-environment.bicep --stdout"
test "Main template compiles" "az bicep build --file main.bicep --stdout"

# ============================================
# Module Parameter Tests
# ============================================
echo ""
echo "==> Module Parameter Tests"

# Log Analytics parameters
test "Log Analytics has name parameter" "grep -q 'param name string' core/monitor/loganalytics.bicep"
test "Log Analytics has location parameter" "grep -q 'param location string' core/monitor/loganalytics.bicep"
test "Log Analytics has tags parameter" "grep -q 'param tags object' core/monitor/loganalytics.bicep"

# Application Insights parameters
test "App Insights has name parameter" "grep -q 'param name string' core/monitor/applicationinsights.bicep"
test "App Insights has location parameter" "grep -q 'param location string' core/monitor/applicationinsights.bicep"
test "App Insights has workspaceId parameter" "grep -q 'param workspaceId string' core/monitor/applicationinsights.bicep"

# Container Apps Environment parameters
test "CAE has name parameter" "grep -q 'param name string' core/host/container-apps-environment.bicep"
test "CAE has location parameter" "grep -q 'param location string' core/host/container-apps-environment.bicep"
test "CAE has Customer ID parameter" "grep -q 'param logAnalyticsCustomerId string' core/host/container-apps-environment.bicep"

# ============================================
# Module Output Tests
# ============================================
echo ""
echo "==> Module Output Tests"

test "Log Analytics outputs workspace ID" "grep -q 'output.*workspaceId' core/monitor/loganalytics.bicep"
test "Log Analytics outputs customer ID" "grep -q 'output.*customerId' core/monitor/loganalytics.bicep"
test "App Insights outputs connection string" "grep -q 'output.*connectionString' core/monitor/applicationinsights.bicep"
test "App Insights outputs instrumentation key" "grep -q 'output.*instrumentationKey' core/monitor/applicationinsights.bicep"
test "CAE outputs environment ID" "grep -q 'output.*id' core/host/container-apps-environment.bicep || grep -q 'output.*environmentId' core/host/container-apps-environment.bicep"
test "CAE outputs default domain" "grep -q 'output.*defaultDomain' core/host/container-apps-environment.bicep || grep -q 'output.*domain' core/host/container-apps-environment.bicep"

# ============================================
# Main Template Integration Tests
# ============================================
echo ""
echo "==> Main Template Integration Tests"

test "Main template calls Log Analytics module" "grep -q 'module.*loganalytics' main.bicep || grep -q 'module.*log' main.bicep"
test "Main template calls App Insights module" "grep -q 'module.*applicationinsights' main.bicep || grep -q 'module.*appinsights' main.bicep"
test "Main template calls CAE module" "grep -q 'module.*container.*environment' main.bicep || grep -q 'module.*containerAppsEnvironment' main.bicep"
test "Main outputs App Insights connection string" "grep -q 'output APPLICATIONINSIGHTS_CONNECTION_STRING' main.bicep && ! grep -q 'InstrumentationKey=placeholder' main.bicep"

# ============================================
# API Version Tests
# ============================================
echo ""
echo "==> API Version Tests"

test "Log Analytics uses 2023+ API" "grep -q \"Microsoft.OperationalInsights/workspaces@202[3-9]\" core/monitor/loganalytics.bicep"
test "App Insights uses 2020+ API" "grep -q \"Microsoft.Insights/components@202[0-9]\" core/monitor/applicationinsights.bicep"
test "CAE uses 2024 API" "grep -q \"Microsoft.App/managedEnvironments@202[4-9]\" core/host/container-apps-environment.bicep"

# ============================================
# Results Summary
# ============================================
echo ""
echo "=========================================="
echo "Test Results:"
echo "  Passed: ${GREEN}$PASSED${NC}"
echo "  Failed: ${RED}$FAILED${NC}"
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
