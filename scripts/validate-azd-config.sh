#!/bin/bash
# Azure Developer CLI (azd) Configuration Validation Script
# This script validates the azure.yaml configuration and project structure
# following azd best practices for 2025

set -e

echo "=== Azure Developer CLI Configuration Validation ==="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

VALIDATION_ERRORS=0

# Test 1: Verify azure.yaml exists
echo -n "Test 1: Checking azure.yaml exists... "
if [ -f "azure.yaml" ]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
    echo "  azure.yaml not found in project root"
    VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
fi

# Test 2: Verify azure.yaml has required top-level keys
echo -n "Test 2: Checking azure.yaml schema (name, services)... "
if [ -f "azure.yaml" ]; then
    if grep -q "^name:" azure.yaml && grep -q "^services:" azure.yaml; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${RED}FAIL${NC}"
        echo "  azure.yaml missing required keys: name and/or services"
        VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
    fi
else
    echo -e "${YELLOW}SKIP${NC} (azure.yaml not found)"
fi

# Test 3: Verify service definition exists for container app
echo -n "Test 3: Checking service definition (api)... "
if [ -f "azure.yaml" ]; then
    if grep -q "api:" azure.yaml; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${RED}FAIL${NC}"
        echo "  azure.yaml missing 'api' service definition"
        VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
    fi
else
    echo -e "${YELLOW}SKIP${NC} (azure.yaml not found)"
fi

# Test 4: Verify deployment hooks are configured
echo -n "Test 4: Checking deployment hooks (prepackage, postprovision, postdeploy)... "
if [ -f "azure.yaml" ]; then
    HOOKS_FOUND=0
    if grep -q "prepackage:" azure.yaml; then
        HOOKS_FOUND=$((HOOKS_FOUND + 1))
    fi
    if grep -q "postprovision:" azure.yaml; then
        HOOKS_FOUND=$((HOOKS_FOUND + 1))
    fi
    if grep -q "postdeploy:" azure.yaml; then
        HOOKS_FOUND=$((HOOKS_FOUND + 1))
    fi

    if [ $HOOKS_FOUND -ge 2 ]; then
        echo -e "${GREEN}PASS${NC} ($HOOKS_FOUND hooks configured)"
    else
        echo -e "${RED}FAIL${NC}"
        echo "  Expected at least 2 deployment hooks, found $HOOKS_FOUND"
        VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
    fi
else
    echo -e "${YELLOW}SKIP${NC} (azure.yaml not found)"
fi

# Test 5: Verify required directory structure
echo -n "Test 5: Checking directory structure (infra/, src/, scripts/)... "
DIRS_MISSING=""
if [ ! -d "infra" ]; then
    DIRS_MISSING="${DIRS_MISSING}infra/ "
fi
if [ ! -d "src" ]; then
    DIRS_MISSING="${DIRS_MISSING}src/ "
fi
if [ ! -d "scripts" ]; then
    DIRS_MISSING="${DIRS_MISSING}scripts/ "
fi

if [ -z "$DIRS_MISSING" ]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
    echo "  Missing directories: $DIRS_MISSING"
    VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
fi

# Test 6: Verify environment variable mappings are defined
echo -n "Test 6: Checking environment variable configuration... "
if [ -f "azure.yaml" ]; then
    # Look for env section or environment variable references
    if grep -q "AZURE_OPENAI_ENDPOINT" azure.yaml || grep -q "env:" azure.yaml; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${RED}FAIL${NC}"
        echo "  No environment variable configuration found in azure.yaml"
        VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
    fi
else
    echo -e "${YELLOW}SKIP${NC} (azure.yaml not found)"
fi

# Test 7: Verify hook scripts exist (if referenced in azure.yaml)
echo -n "Test 7: Checking hook script placeholders... "
MISSING_SCRIPTS=""
if [ -f "azure.yaml" ]; then
    # Check for common hook script references
    if grep -q "scripts/validate-config.sh" azure.yaml && [ ! -f "scripts/validate-config.sh" ]; then
        MISSING_SCRIPTS="${MISSING_SCRIPTS}validate-config.sh "
    fi
    if grep -q "scripts/setup-bot.sh" azure.yaml && [ ! -f "scripts/setup-bot.sh" ]; then
        MISSING_SCRIPTS="${MISSING_SCRIPTS}setup-bot.sh "
    fi
    if grep -q "scripts/generate-teams-manifest.sh" azure.yaml && [ ! -f "scripts/generate-teams-manifest.sh" ]; then
        MISSING_SCRIPTS="${MISSING_SCRIPTS}generate-teams-manifest.sh "
    fi

    if [ -z "$MISSING_SCRIPTS" ]; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${YELLOW}WARNING${NC}"
        echo "  Referenced scripts not yet created: $MISSING_SCRIPTS"
        # Not counting as error since scripts can be placeholders
    fi
else
    echo -e "${YELLOW}SKIP${NC} (azure.yaml not found)"
fi

# Summary
echo ""
echo "=== Validation Summary ==="
if [ $VALIDATION_ERRORS -eq 0 ]; then
    echo -e "${GREEN}All validations passed!${NC}"
    echo "azure.yaml configuration is ready for azd deployment"
    exit 0
else
    echo -e "${RED}Validation failed with $VALIDATION_ERRORS error(s)${NC}"
    echo "Please fix the issues above before deploying"
    exit 1
fi
