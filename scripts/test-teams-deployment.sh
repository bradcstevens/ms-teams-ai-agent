#!/bin/bash
# End-to-End Teams Deployment Testing Script (Task 4.6)
# Validates bot registration, endpoint accessibility, and Teams app configuration

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Test Teams bot deployment end-to-end.

OPTIONS:
    -g, --resource-group RG    Azure resource group name [required]
    -n, --bot-name NAME       Bot service name [required]
    -u, --endpoint URL        Bot endpoint URL [required]
    -h, --help                Show this help message

EXAMPLE:
    $0 --resource-group rg-teams-bot-dev \\
       --bot-name bot-teams-ai-agent-dev \\
       --endpoint https://ca-dev-abc123.azurecontainerapps.io/api/messages

DESCRIPTION:
    This script performs comprehensive testing:
    1. Bot registration verification
    2. Endpoint accessibility test
    3. Health check validation
    4. Manifest validation
    5. Authentication flow test
    6. Teams channel verification
EOF
    exit 1
}

# Parse arguments
RESOURCE_GROUP=""
BOT_NAME=""
BOT_ENDPOINT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -n|--bot-name)
            BOT_NAME="$2"
            shift 2
            ;;
        -u|--endpoint)
            BOT_ENDPOINT="$2"
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
if [[ -z "$RESOURCE_GROUP" || -z "$BOT_NAME" || -z "$BOT_ENDPOINT" ]]; then
    log_error "Missing required parameters"
    usage
fi

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNING=0

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

log_info "================================================"
log_info "Teams Bot Deployment Testing"
log_info "================================================"
log_info "Resource Group: $RESOURCE_GROUP"
log_info "Bot Name: $BOT_NAME"
log_info "Endpoint: $BOT_ENDPOINT"
log_info ""

# Test 1: Azure CLI availability
log_test "Testing Azure CLI availability..."
if command -v az &> /dev/null; then
    test_result "Azure CLI Check" "PASS" ""
else
    test_result "Azure CLI Check" "FAIL" "Azure CLI not installed"
    exit 1
fi

# Test 2: Azure authentication
log_test "Testing Azure authentication..."
if az account show &> /dev/null; then
    test_result "Azure Auth Check" "PASS" ""
else
    test_result "Azure Auth Check" "FAIL" "Not logged in to Azure"
    exit 1
fi

# Test 3: Bot registration exists
log_test "Testing bot registration..."
if az bot show --name "$BOT_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    test_result "Bot Registration" "PASS" ""

    # Get bot details
    BOT_ID=$(az bot show --name "$BOT_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.appId" -o tsv 2>/dev/null || echo "")
    CONFIGURED_ENDPOINT=$(az bot show --name "$BOT_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.endpoint" -o tsv 2>/dev/null || echo "")

    log_info "  Bot ID: $BOT_ID"
    log_info "  Configured Endpoint: $CONFIGURED_ENDPOINT"

    # Verify endpoint matches
    if [[ "$CONFIGURED_ENDPOINT" == "$BOT_ENDPOINT" ]]; then
        test_result "Bot Endpoint Config" "PASS" ""
    else
        test_result "Bot Endpoint Config" "WARN" "Endpoint mismatch: configured=$CONFIGURED_ENDPOINT, expected=$BOT_ENDPOINT"
    fi
else
    test_result "Bot Registration" "FAIL" "Bot not found in Azure"
fi

# Test 4: Teams channel enabled
log_test "Testing Teams channel..."
if az bot msteams show --name "$BOT_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    test_result "Teams Channel" "PASS" ""
else
    test_result "Teams Channel" "FAIL" "Teams channel not enabled"
fi

# Test 5: Endpoint accessibility
log_test "Testing endpoint accessibility..."

# Strip protocol for base URL test
BASE_URL="${BOT_ENDPOINT#https://}"
BASE_URL="${BASE_URL#http://}"
BASE_URL="https://${BASE_URL%/api/messages*}"

# Test health endpoint
HEALTH_ENDPOINT="${BASE_URL}/health"
log_info "  Testing health endpoint: $HEALTH_ENDPOINT"

if HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_ENDPOINT" --max-time 10); then
    if [[ "$HTTP_CODE" == "200" ]]; then
        test_result "Health Endpoint" "PASS" ""

        # Get health response
        HEALTH_RESPONSE=$(curl -s "$HEALTH_ENDPOINT" 2>/dev/null || echo "{}")
        log_info "  Health response: $HEALTH_RESPONSE"
    else
        test_result "Health Endpoint" "WARN" "HTTP $HTTP_CODE"
    fi
else
    test_result "Health Endpoint" "FAIL" "Endpoint not accessible"
fi

# Test 6: Root endpoint
log_test "Testing root endpoint..."
if HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/" --max-time 10); then
    if [[ "$HTTP_CODE" == "200" ]]; then
        test_result "Root Endpoint" "PASS" ""
    else
        test_result "Root Endpoint" "WARN" "HTTP $HTTP_CODE"
    fi
else
    test_result "Root Endpoint" "FAIL" "Endpoint not accessible"
fi

# Test 7: Messages endpoint (should require auth)
log_test "Testing messages endpoint authentication..."
if HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BOT_ENDPOINT" --max-time 10); then
    if [[ "$HTTP_CODE" == "401" || "$HTTP_CODE" == "403" ]]; then
        test_result "Bot Auth Endpoint" "PASS" ""
        log_info "  Correctly returns $HTTP_CODE without authentication"
    elif [[ "$HTTP_CODE" == "405" ]]; then
        test_result "Bot Auth Endpoint" "PASS" ""
        log_info "  Method not allowed (expected for GET on POST endpoint)"
    else
        test_result "Bot Auth Endpoint" "WARN" "Unexpected HTTP $HTTP_CODE"
    fi
else
    test_result "Bot Auth Endpoint" "FAIL" "Endpoint not accessible"
fi

# Test 8: Manifest validation
log_test "Testing Teams manifest..."
MANIFEST_FILE="./teams/manifest.json"

if [[ -f "$MANIFEST_FILE" ]]; then
    # Validate JSON syntax
    if python3 -m json.tool "$MANIFEST_FILE" > /dev/null 2>&1; then
        test_result "Manifest JSON" "PASS" ""

        # Check for placeholders
        if grep -q "{{BOT_ID}}" "$MANIFEST_FILE" || grep -q "{{BOT_ENDPOINT}}" "$MANIFEST_FILE"; then
            test_result "Manifest Placeholders" "FAIL" "Unsubstituted placeholders found"
        else
            test_result "Manifest Placeholders" "PASS" ""
        fi

        # Validate with Python validator if available
        if [[ -f "./src/app/teams/manifest_validator.py" ]]; then
            if python3 -c "
import sys
sys.path.insert(0, './src')
from app.teams.manifest_validator import validate_manifest
is_valid, errors = validate_manifest('$MANIFEST_FILE')
sys.exit(0 if is_valid else 1)
" 2>/dev/null; then
                test_result "Manifest Validation" "PASS" ""
            else
                test_result "Manifest Validation" "FAIL" "Schema validation failed"
            fi
        fi
    else
        test_result "Manifest JSON" "FAIL" "Invalid JSON syntax"
    fi
else
    test_result "Manifest File" "FAIL" "Manifest file not found"
fi

# Test 9: Icon files
log_test "Testing icon files..."
if [[ -f "./teams/color.png" ]]; then
    test_result "Color Icon" "PASS" ""
else
    test_result "Color Icon" "FAIL" "color.png not found"
fi

if [[ -f "./teams/outline.png" ]]; then
    test_result "Outline Icon" "PASS" ""
else
    test_result "Outline Icon" "FAIL" "outline.png not found"
fi

# Test 10: HTTPS enforcement
log_test "Testing HTTPS enforcement..."
if [[ "$BOT_ENDPOINT" =~ ^https:// ]]; then
    test_result "HTTPS Enforcement" "PASS" ""
else
    test_result "HTTPS Enforcement" "FAIL" "Endpoint not using HTTPS"
fi

# Test Summary
log_info ""
log_info "================================================"
log_info "Test Summary"
log_info "================================================"
log_info "${GREEN}Passed:${NC}  $TESTS_PASSED"
log_info "${YELLOW}Warnings:${NC} $TESTS_WARNING"
log_info "${RED}Failed:${NC}  $TESTS_FAILED"
log_info ""

if [[ $TESTS_FAILED -eq 0 ]]; then
    log_info "${GREEN}✓ All critical tests passed!${NC}"
    if [[ $TESTS_WARNING -gt 0 ]]; then
        log_warning "Some warnings detected. Review above for details."
    fi
    log_info ""
    log_info "Deployment appears healthy. Next steps:"
    log_info "  1. Upload Teams app package to Teams Admin Center"
    log_info "  2. Test bot in Teams client"
    log_info "  3. Monitor Application Insights for errors"
    exit 0
else
    log_error "${RED}✗ Some tests failed!${NC}"
    log_error "Please review the failed tests above and fix issues before deploying."
    exit 1
fi
