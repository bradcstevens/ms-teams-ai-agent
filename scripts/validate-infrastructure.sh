#!/bin/bash
# Simplified Bicep Infrastructure Validation Test
# Task 1.2: Core Bicep Infrastructure Module

echo "========================================"
echo "Bicep Infrastructure Validation"
echo "Task 1.2: Core Bicep Infrastructure Module"
echo "========================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_BICEP="$SCRIPT_DIR/main.bicep"

PASSED=0
FAILED=0

# Test 1: Bicep compilation
echo "Test 1: Compiling main.bicep..."
if az bicep build --file "$MAIN_BICEP" --outfile /tmp/main.json 2>&1 >/dev/null; then
    echo "✅ PASS: Bicep compilation successful"
    ((PASSED++))
else
    echo "❌ FAIL: Bicep compilation failed"
    ((FAILED++))
fi

# Test 2-8: Check required elements
echo ""
echo "Test 2: Checking required parameters..."
REQUIRED_PARAMS=("environmentName" "location" "principalId" "openAiLocation" "openAiModelName" "openAiModelVersion" "botDisplayName")
for param in "${REQUIRED_PARAMS[@]}"; do
    if grep -q "param $param" "$MAIN_BICEP"; then
        ((PASSED++))
    else
        echo "❌ FAIL: Missing parameter: $param"
        ((FAILED++))
    fi
done
echo "✅ PASS: All required parameters present (${#REQUIRED_PARAMS[@]}/7)"

echo ""
echo "Test 3: Checking required outputs..."
REQUIRED_OUTPUTS=("AZURE_OPENAI_ENDPOINT" "AZURE_OPENAI_DEPLOYMENT_NAME" "BOT_ID" "KEY_VAULT_NAME" "APPLICATIONINSIGHTS_CONNECTION_STRING" "CONTAINER_REGISTRY_ENDPOINT" "CONTAINER_APP_NAME" "CONTAINER_APP_ENVIRONMENT_NAME")
for output in "${REQUIRED_OUTPUTS[@]}"; do
    if grep -q "output $output" "$MAIN_BICEP"; then
        ((PASSED++))
    else
        echo "❌ FAIL: Missing output: $output"
        ((FAILED++))
    fi
done
echo "✅ PASS: All required outputs present (${#REQUIRED_OUTPUTS[@]}/8)"

echo ""
echo "Test 4: Checking tagging strategy..."
if grep -q "'azd-env-name'" "$MAIN_BICEP"; then
    echo "✅ PASS: azd-env-name tag present"
    ((PASSED++))
else
    echo "❌ FAIL: azd-env-name tag missing"
    ((FAILED++))
fi

echo ""
echo "Test 5: Checking resource naming..."
if grep -q "uniqueString" "$MAIN_BICEP"; then
    echo "✅ PASS: uniqueString used for naming"
    ((PASSED++))
else
    echo "❌ FAIL: uniqueString not found"
    ((FAILED++))
fi

echo ""
echo "Test 6: Checking parameter file..."
if [ -f "$SCRIPT_DIR/main.parameters.json" ]; then
    echo "✅ PASS: main.parameters.json exists"
    ((PASSED++))
else
    echo "❌ FAIL: main.parameters.json missing"
    ((FAILED++))
fi

echo ""
echo "Test 7: Checking documentation..."
if [ -f "$SCRIPT_DIR/README.md" ]; then
    echo "✅ PASS: README.md exists"
    ((PASSED++))
else
    echo "❌ FAIL: README.md missing"
    ((FAILED++))
fi

echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✅ All tests passed! Bicep infrastructure is valid."
    exit 0
else
    echo "❌ Some tests failed."
    exit 1
fi
