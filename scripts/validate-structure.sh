#!/bin/bash
# Infrastructure Structure Validation Script
# Basic validation without requiring Azure CLI
# Tests file existence and content requirements

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INFRA_DIR="$PROJECT_ROOT/infra"

echo "=========================================="
echo "Infrastructure Structure Validation"
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
echo "=== Phase 2: Main Template Integration ==="
echo ""

run_test "Main template exists" \
    "test -f '$INFRA_DIR/main.bicep'"

echo ""
echo "=== Phase 3: Required Outputs Validation ==="
echo ""

# Check that main.bicep contains required outputs
run_test "Main has AZURE_OPENAI_ENDPOINT output" \
    "grep -q 'output AZURE_OPENAI_ENDPOINT' '$INFRA_DIR/main.bicep'"

run_test "Main has BOT_ID output" \
    "grep -q 'output BOT_ID' '$INFRA_DIR/main.bicep'"

run_test "Main has KEY_VAULT_NAME output" \
    "grep -q 'output KEY_VAULT_NAME' '$INFRA_DIR/main.bicep'"

run_test "Main has CONTAINER_REGISTRY_ENDPOINT output" \
    "grep -q 'output CONTAINER_REGISTRY_ENDPOINT' '$INFRA_DIR/main.bicep'"

echo ""
echo "=== Phase 4: Module Parameter Validation ==="
echo ""

# Validate required parameters exist in modules
run_test "Container Registry has name parameter" \
    "test -f '$INFRA_DIR/core/host/container-registry.bicep' && grep -q 'param.*containerRegistryName' '$INFRA_DIR/core/host/container-registry.bicep'"

run_test "Container App has environment ID parameter" \
    "test -f '$INFRA_DIR/core/host/container-app.bicep' && grep -q 'param.*containerAppsEnvironmentId' '$INFRA_DIR/core/host/container-app.bicep'"

run_test "OpenAI has model parameters" \
    "test -f '$INFRA_DIR/ai/openai.bicep' && grep -q 'param.*modelName' '$INFRA_DIR/ai/openai.bicep'"

run_test "Bot Service has endpoint parameter" \
    "test -f '$INFRA_DIR/bot/bot-service.bicep' && grep -q 'param.*botEndpoint' '$INFRA_DIR/bot/bot-service.bicep'"

run_test "Key Vault has RBAC parameter" \
    "test -f '$INFRA_DIR/security/key-vault.bicep' && grep -q 'param.*principalId' '$INFRA_DIR/security/key-vault.bicep'"

echo ""
echo "=== Phase 5: Module Outputs Validation ==="
echo ""

run_test "Container Registry has loginServer output" \
    "test -f '$INFRA_DIR/core/host/container-registry.bicep' && grep -q 'output.*loginServer' '$INFRA_DIR/core/host/container-registry.bicep'"

run_test "Container App has FQDN output" \
    "test -f '$INFRA_DIR/core/host/container-app.bicep' && grep -q 'output.*fqdn' '$INFRA_DIR/core/host/container-app.bicep'"

run_test "OpenAI has endpoint output" \
    "test -f '$INFRA_DIR/ai/openai.bicep' && grep -q 'output.*endpoint' '$INFRA_DIR/ai/openai.bicep'"

run_test "Bot Service has botId output" \
    "test -f '$INFRA_DIR/bot/bot-service.bicep' && grep -q 'output.*botId' '$INFRA_DIR/bot/bot-service.bicep'"

run_test "Key Vault has name output" \
    "test -f '$INFRA_DIR/security/key-vault.bicep' && grep -q 'output.*keyVaultName' '$INFRA_DIR/security/key-vault.bicep'"

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
    echo "Infrastructure structure is complete."
    echo ""
    echo "Next steps:"
    echo "  1. Install Azure CLI: brew install azure-cli"
    echo "  2. Install Bicep: az bicep install"
    echo "  3. Run full validation: ./scripts/validate-bicep.sh"
    echo "  4. Deploy infrastructure: azd up"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    echo "Please implement missing modules."
    exit 1
fi
