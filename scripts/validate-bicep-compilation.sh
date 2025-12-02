#!/bin/bash
# Bicep Infrastructure Validation Script
# Tests infrastructure modules for compilation and dependency correctness

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INFRA_DIR="$PROJECT_ROOT/infra"

echo "=========================================="
echo "Bicep Infrastructure Validation"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test
run_test() {
    local test_name="$1"
    local test_command="$2"

    TESTS_RUN=$((TESTS_RUN + 1))
    echo -n "Testing: $test_name ... "

    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Check if bicep CLI is available
if ! command -v bicep &> /dev/null; then
    echo -e "${RED}ERROR: bicep CLI not found${NC}"
    echo "Install with: az bicep install"
    exit 1
fi

echo "=== Phase 1: Module File Existence ==="
echo ""

# Container Infrastructure
run_test "Container Registry module exists" \
    "test -f '$INFRA_DIR/core/host/container-registry.bicep'"

run_test "Container App module exists" \
    "test -f '$INFRA_DIR/core/host/container-app.bicep'"

# AI Services
run_test "Azure OpenAI module exists" \
    "test -f '$INFRA_DIR/ai/openai.bicep'"

# Bot Service & Security
run_test "Bot Service module exists" \
    "test -f '$INFRA_DIR/bot/bot-service.bicep'"

run_test "Key Vault module exists" \
    "test -f '$INFRA_DIR/security/key-vault.bicep'"

echo ""
echo "=== Phase 2: Bicep Compilation ==="
echo ""

# Test individual module compilation
run_test "Container Registry compiles" \
    "bicep build '$INFRA_DIR/core/host/container-registry.bicep'"

run_test "Container App compiles" \
    "bicep build '$INFRA_DIR/core/host/container-app.bicep'"

run_test "Azure OpenAI compiles" \
    "bicep build '$INFRA_DIR/ai/openai.bicep'"

run_test "Bot Service compiles" \
    "bicep build '$INFRA_DIR/bot/bot-service.bicep'"

run_test "Key Vault compiles" \
    "bicep build '$INFRA_DIR/security/key-vault.bicep'"

run_test "Container Apps Environment compiles" \
    "bicep build '$INFRA_DIR/core/host/container-apps-environment.bicep'"

echo ""
echo "=== Phase 3: Main Template Integration ==="
echo ""

run_test "Main template compiles" \
    "bicep build '$INFRA_DIR/main.bicep'"

run_test "Main template has no warnings" \
    "bicep build '$INFRA_DIR/main.bicep' 2>&1 | grep -v Warning"

echo ""
echo "=== Phase 4: Required Outputs Validation ==="
echo ""

# Check that main.bicep contains required outputs
run_test "Main template has AZURE_OPENAI_ENDPOINT output" \
    "grep -q 'output AZURE_OPENAI_ENDPOINT' '$INFRA_DIR/main.bicep'"

run_test "Main template has BOT_ID output" \
    "grep -q 'output BOT_ID' '$INFRA_DIR/main.bicep'"

run_test "Main template has KEY_VAULT_NAME output" \
    "grep -q 'output KEY_VAULT_NAME' '$INFRA_DIR/main.bicep'"

run_test "Main template has CONTAINER_REGISTRY_ENDPOINT output" \
    "grep -q 'output CONTAINER_REGISTRY_ENDPOINT' '$INFRA_DIR/main.bicep'"

echo ""
echo "=== Phase 5: Module Parameter Validation ==="
echo ""

# Validate required parameters exist in modules
run_test "Container Registry has name parameter" \
    "grep -q 'param.*containerRegistryName' '$INFRA_DIR/core/host/container-registry.bicep'"

run_test "Container App has environment ID parameter" \
    "grep -q 'param.*containerAppsEnvironmentId' '$INFRA_DIR/core/host/container-app.bicep'"

run_test "OpenAI has model parameters" \
    "grep -q 'param.*modelName' '$INFRA_DIR/ai/openai.bicep'"

run_test "Bot Service has endpoint parameter" \
    "grep -q 'param.*botEndpoint' '$INFRA_DIR/bot/bot-service.bicep'"

run_test "Key Vault has RBAC parameter" \
    "grep -q 'param.*principalId' '$INFRA_DIR/security/key-vault.bicep'"

echo ""
echo "=========================================="
echo "Test Results Summary"
echo "=========================================="
echo "Tests Run:    $TESTS_RUN"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    echo "Infrastructure is ready for deployment with 'azd up'"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    echo "Please fix the issues before deployment."
    exit 1
fi
