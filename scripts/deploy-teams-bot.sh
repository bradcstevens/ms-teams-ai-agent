#!/bin/bash
# Teams Bot Deployment Orchestrator
# End-to-end deployment orchestration for Teams AI Agent

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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

End-to-end Teams bot deployment orchestration.

OPTIONS:
    -e, --environment ENV      Environment (dev/staging/prod) [required]
    -g, --resource-group RG    Azure resource group name [required]
    -n, --bot-name NAME       Bot service name [required]
    -u, --endpoint URL        Bot endpoint URL [required]
    -k, --key-vault NAME      Key Vault name [required]
    -v, --version VERSION     App version (default: 1.0.0)
    -s, --skip-tests          Skip deployment testing
    -h, --help                Show this help message

EXAMPLE:
    $0 --environment dev \\
       --resource-group rg-teams-bot-dev \\
       --bot-name bot-teams-ai-agent-dev \\
       --endpoint https://ca-dev-abc123.azurecontainerapps.io/api/messages \\
       --key-vault kv-dev-abc123 \\
       --version 1.0.0

DESCRIPTION:
    This script orchestrates the complete Teams bot deployment:
    1. Bot registration in Azure
    2. Teams manifest generation
    3. Teams app package creation
    4. Deployment validation and testing

PREREQUISITES:
    - Azure infrastructure deployed (Task 1)
    - Container app running (Task 2)
    - Azure CLI authenticated
EOF
    exit 1
}

# Parse arguments
ENVIRONMENT=""
RESOURCE_GROUP=""
BOT_NAME=""
BOT_ENDPOINT=""
KEY_VAULT_NAME=""
APP_VERSION="1.0.0"
SKIP_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
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
        -k|--key-vault)
            KEY_VAULT_NAME="$2"
            shift 2
            ;;
        -v|--version)
            APP_VERSION="$2"
            shift 2
            ;;
        -s|--skip-tests)
            SKIP_TESTS=true
            shift
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
if [[ -z "$ENVIRONMENT" || -z "$RESOURCE_GROUP" || -z "$BOT_NAME" || -z "$BOT_ENDPOINT" || -z "$KEY_VAULT_NAME" ]]; then
    log_error "Missing required parameters"
    usage
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log_info "================================================"
log_info "Teams Bot Deployment Orchestrator"
log_info "================================================"
log_info "Environment: $ENVIRONMENT"
log_info "Bot Name: $BOT_NAME"
log_info "Version: $APP_VERSION"
log_info ""

# Step 1: Bot Registration
log_step "Step 1: Creating bot registration..."
log_info "Running: create-bot-registration.sh"

if [[ -f "$SCRIPT_DIR/create-bot-registration.sh" ]]; then
    if bash "$SCRIPT_DIR/create-bot-registration.sh" \
        --environment "$ENVIRONMENT" \
        --resource-group "$RESOURCE_GROUP" \
        --bot-name "$BOT_NAME" \
        --endpoint "$BOT_ENDPOINT" \
        --key-vault "$KEY_VAULT_NAME"; then
        log_info "✓ Bot registration completed"
    else
        log_error "✗ Bot registration failed"
        exit 1
    fi
else
    log_error "create-bot-registration.sh not found"
    exit 1
fi

# Get bot ID from Key Vault
log_info "Retrieving bot ID from Key Vault..."
BOT_ID=$(az keyvault secret show \
    --vault-name "$KEY_VAULT_NAME" \
    --name "bot-id" \
    --query "value" -o tsv 2>/dev/null || echo "")

if [[ -z "$BOT_ID" ]]; then
    log_error "Failed to retrieve bot ID from Key Vault"
    exit 1
fi

log_info "Bot ID: $BOT_ID"

# Step 2: Generate Teams Manifest
log_step "Step 2: Generating Teams manifest..."
log_info "Running: generate-teams-manifest.sh"

# Strip protocol from endpoint
ENDPOINT_DOMAIN="${BOT_ENDPOINT#https://}"
ENDPOINT_DOMAIN="${BOT_ENDPOINT#http://}"

if [[ -f "$SCRIPT_DIR/generate-teams-manifest.sh" ]]; then
    if bash "$SCRIPT_DIR/generate-teams-manifest.sh" \
        --bot-id "$BOT_ID" \
        --endpoint "$ENDPOINT_DOMAIN" \
        --version "$APP_VERSION" \
        --environment "$ENVIRONMENT"; then
        log_info "✓ Manifest generation completed"
    else
        log_error "✗ Manifest generation failed"
        exit 1
    fi
else
    log_error "generate-teams-manifest.sh not found"
    exit 1
fi

# Step 3: Create Teams Package
log_step "Step 3: Creating Teams app package..."
log_info "Running: create-teams-package.sh"

PACKAGE_OUTPUT="./teams-app-${ENVIRONMENT}-${APP_VERSION}.zip"

if [[ -f "$SCRIPT_DIR/create-teams-package.sh" ]]; then
    if bash "$SCRIPT_DIR/create-teams-package.sh" \
        --input "./teams" \
        --output "$PACKAGE_OUTPUT" \
        --version "$APP_VERSION" \
        --environment "$ENVIRONMENT"; then
        log_info "✓ Teams package created: $PACKAGE_OUTPUT"
    else
        log_error "✗ Teams package creation failed"
        exit 1
    fi
else
    log_error "create-teams-package.sh not found"
    exit 1
fi

# Step 4: Deployment Testing
if [[ "$SKIP_TESTS" == false ]]; then
    log_step "Step 4: Running deployment tests..."
    log_info "Running: test-teams-deployment.sh"

    if [[ -f "$SCRIPT_DIR/test-teams-deployment.sh" ]]; then
        if bash "$SCRIPT_DIR/test-teams-deployment.sh" \
            --resource-group "$RESOURCE_GROUP" \
            --bot-name "$BOT_NAME" \
            --endpoint "$BOT_ENDPOINT"; then
            log_info "✓ Deployment tests passed"
        else
            log_warning "✗ Some deployment tests failed"
            log_warning "Review test output above for details"
        fi
    else
        log_warning "test-teams-deployment.sh not found, skipping tests"
    fi
else
    log_warning "Skipping deployment tests (--skip-tests flag)"
fi

# Final Summary
log_info ""
log_info "================================================"
log_info "Deployment Summary"
log_info "================================================"
log_info "✓ Bot registered: $BOT_NAME"
log_info "✓ Bot ID: $BOT_ID"
log_info "✓ Manifest generated and validated"
log_info "✓ Teams package created: $PACKAGE_OUTPUT"
log_info ""
log_info "Next Steps:"
log_info "  1. Upload Teams app package to Teams Admin Center:"
log_info "     https://admin.teams.microsoft.com/policies/manage-apps"
log_info ""
log_info "  2. Or sideload the app for testing:"
log_info "     - Open Microsoft Teams"
log_info "     - Go to Apps > Upload a custom app"
log_info "     - Select: $PACKAGE_OUTPUT"
log_info ""
log_info "  3. Test the bot in Teams:"
log_info "     - Search for '$BOT_NAME' in Teams"
log_info "     - Start a chat and send a message"
log_info ""
log_info "  4. Monitor the bot:"
log_info "     - Check Application Insights for logs"
log_info "     - Monitor Container App metrics"
log_info ""
log_info "Deployment completed successfully!"
log_info "================================================"

exit 0
