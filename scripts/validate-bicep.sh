#!/bin/bash
# Bicep Infrastructure Validation Test Script
# Tests for Task 1.2: Core Bicep Infrastructure Module

set -e

echo "================================"
echo "Bicep Infrastructure Validation"
echo "Task 1.2: Core Bicep Infrastructure Module"
echo "================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_BICEP="$SCRIPT_DIR/main.bicep"
PARAMS_FILE="$SCRIPT_DIR/main.parameters.json"

PASSED=0
FAILED=0

# Helper functions
pass_test() {
    echo "✅ PASS: $1"
    ((PASSED++))
}

fail_test() {
    echo "❌ FAIL: $1"
    ((FAILED++))
}

# Test 1: Bicep file exists
echo "Test 1: Checking if main.bicep exists..."
if [ -f "$MAIN_BICEP" ]; then
    pass_test "main.bicep file exists"
else
    fail_test "main.bicep file not found"
    exit 1
fi

# Test 2: Bicep compilation without errors
echo ""
echo "Test 2: Compiling main.bicep..."
if az bicep build --file "$MAIN_BICEP" --outfile /tmp/main.json 2>&1 > /tmp/bicep-build.log; then
    # Check if compilation succeeded (exit code 0) - warnings are OK
    if [ -f /tmp/main.json ]; then
        pass_test "Bicep compilation successful"
        # Show warnings if any
        if grep -q "Warning" /tmp/bicep-build.log; then
            echo "   ℹ️  Note: Compilation succeeded with warnings (expected for modules pending implementation)"
        fi
    else
        fail_test "Bicep compilation failed - no output generated"
        cat /tmp/bicep-build.log
    fi
else
    fail_test "Bicep compilation failed"
    cat /tmp/bicep-build.log
fi

# Test 3: Required parameters are defined
echo ""
echo "Test 3: Validating required parameters..."
REQUIRED_PARAMS=(
    "environmentName"
    "location"
    "principalId"
    "openAiLocation"
    "openAiModelName"
    "openAiModelVersion"
    "botDisplayName"
)

for param in "${REQUIRED_PARAMS[@]}"; do
    if grep -q "param $param" "$MAIN_BICEP"; then
        pass_test "Parameter '$param' is defined"
    else
        fail_test "Parameter '$param' is missing"
    fi
done

# Test 4: Required outputs are defined
echo ""
echo "Test 4: Validating required outputs..."
REQUIRED_OUTPUTS=(
    "AZURE_OPENAI_ENDPOINT"
    "AZURE_OPENAI_DEPLOYMENT_NAME"
    "BOT_ID"
    "KEY_VAULT_NAME"
    "APPLICATIONINSIGHTS_CONNECTION_STRING"
    "CONTAINER_REGISTRY_ENDPOINT"
    "CONTAINER_APP_NAME"
    "CONTAINER_APP_ENVIRONMENT_NAME"
)

for output in "${REQUIRED_OUTPUTS[@]}"; do
    if grep -q "output $output" "$MAIN_BICEP"; then
        pass_test "Output '$output' is defined"
    else
        fail_test "Output '$output' is missing"
    fi
done

# Test 5: Tagging strategy is implemented
echo ""
echo "Test 5: Validating tagging strategy..."
if grep -q "azd-env-name" "$MAIN_BICEP"; then
    pass_test "Tag 'azd-env-name' is defined"
else
    fail_test "Tag 'azd-env-name' is missing"
fi

# Test 6: Resource naming with uniqueString
echo ""
echo "Test 6: Validating resource naming convention..."
if grep -q "uniqueString" "$MAIN_BICEP"; then
    pass_test "uniqueString used for resource naming"
else
    fail_test "uniqueString not found in resource naming"
fi

# Test 7: Parameter file template exists
echo ""
echo "Test 7: Checking parameter file template..."
if [ -f "$PARAMS_FILE" ]; then
    pass_test "main.parameters.json exists"
else
    fail_test "main.parameters.json not found"
fi

# Test 8: No hardcoded values (basic check)
echo ""
echo "Test 8: Checking for hardcoded values..."
if grep -E "'[a-z0-9]{20,}'" "$MAIN_BICEP" | grep -v "uniqueString\|resourceToken" > /dev/null; then
    fail_test "Potential hardcoded values found"
else
    pass_test "No obvious hardcoded values detected"
fi

# Summary
echo ""
echo "================================"
echo "Test Summary"
echo "================================"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✅ All tests passed! Bicep infrastructure is valid."
    exit 0
else
    echo "❌ Some tests failed. Please review the errors above."
    exit 1
fi
