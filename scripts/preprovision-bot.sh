#!/bin/bash
# Pre-provision Bot Registration Script
# Creates Azure AD app registration before Bicep deployment
# Sets azd environment variables for use in infrastructure provisioning

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Get environment name from azd
AZURE_ENV_NAME="${AZURE_ENV_NAME:-}"
if [[ -z "$AZURE_ENV_NAME" ]]; then
    log_error "AZURE_ENV_NAME not set. Are you running this via 'azd up'?"
    exit 1
fi

log_info "================================================"
log_info "Pre-provision: Bot App Registration"
log_info "Environment: $AZURE_ENV_NAME"
log_info "================================================"

# Check if Azure CLI is available
if ! command -v az &> /dev/null; then
    log_error "Azure CLI is not installed"
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    log_error "Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

# Check if BOT_APP_ID is already set
EXISTING_BOT_APP_ID="${BOT_APP_ID:-}"
if [[ -n "$EXISTING_BOT_APP_ID" ]]; then
    log_info "BOT_APP_ID already set: $EXISTING_BOT_APP_ID"
    log_info "Skipping app registration creation"
    exit 0
fi

# App registration display name
APP_DISPLAY_NAME="teams-ai-agent-${AZURE_ENV_NAME}"

log_info "Checking for existing app registration: $APP_DISPLAY_NAME"

# Check if app already exists
EXISTING_APP=$(az ad app list --display-name "$APP_DISPLAY_NAME" --query "[0].appId" -o tsv 2>/dev/null || true)

if [[ -n "$EXISTING_APP" && "$EXISTING_APP" != "None" ]]; then
    log_info "Found existing app registration: $EXISTING_APP"
    BOT_APP_ID="$EXISTING_APP"
else
    log_info "Creating new Azure AD app registration..."

    # Create the app registration
    # Note: Using --sign-in-audience for single tenant (AzureADMyOrg)
    BOT_APP_ID=$(az ad app create \
        --display-name "$APP_DISPLAY_NAME" \
        --sign-in-audience "AzureADMyOrg" \
        --query appId -o tsv)

    if [[ -z "$BOT_APP_ID" ]]; then
        log_error "Failed to create app registration"
        exit 1
    fi

    log_info "Created app registration: $BOT_APP_ID"

    # Wait for propagation
    log_info "Waiting for Azure AD propagation..."
    sleep 5
fi

# Get tenant ID
TENANT_ID=$(az account show --query tenantId -o tsv)
log_info "Tenant ID: $TENANT_ID"

# Generate client secret
log_info "Generating client secret..."

# Check for existing credentials and create new one
BOT_PASSWORD=$(az ad app credential reset \
    --id "$BOT_APP_ID" \
    --display-name "azd-generated-$(date +%Y%m%d)" \
    --years 2 \
    --query password -o tsv 2>/dev/null || true)

if [[ -z "$BOT_PASSWORD" ]]; then
    log_warning "Could not generate new credential, trying to create one..."
    BOT_PASSWORD=$(az ad app credential reset \
        --id "$BOT_APP_ID" \
        --years 2 \
        --query password -o tsv)
fi

if [[ -z "$BOT_PASSWORD" ]]; then
    log_error "Failed to generate client secret"
    exit 1
fi

log_info "Client secret generated successfully"

# Set azd environment variables
log_info "Setting azd environment variables..."

azd env set BOT_APP_ID "$BOT_APP_ID"
azd env set BOT_TENANT_ID "$TENANT_ID"
azd env set BOT_PASSWORD "$BOT_PASSWORD"

log_info "================================================"
log_info "Pre-provision complete!"
log_info "================================================"
log_info "Bot App ID: $BOT_APP_ID"
log_info "Tenant ID: $TENANT_ID"
log_info "Password: [STORED IN AZD ENV]"
log_info ""
log_info "These values will be used by the Bicep deployment"
log_info "================================================"

exit 0
