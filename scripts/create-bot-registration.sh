#!/bin/bash
# Bot Registration Automation Script
# Automates Azure Bot Service registration via Azure CLI
# Generates bot credentials and stores them securely in Key Vault

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Automate Azure Bot Service registration and credential management.

OPTIONS:
    -e, --environment ENV       Environment name (dev/staging/prod) [required]
    -g, --resource-group RG     Azure resource group name [required]
    -n, --bot-name NAME        Bot service name [required]
    -u, --endpoint URL         Bot messaging endpoint URL [required]
    -k, --key-vault NAME       Key Vault name for credential storage [required]
    -l, --location LOC         Azure region (default: global)
    -h, --help                 Show this help message

EXAMPLE:
    $0 --environment dev \\
       --resource-group rg-teams-bot-dev \\
       --bot-name bot-teams-ai-agent-dev \\
       --endpoint https://ca-dev-abc123.azurecontainerapps.io/api/messages \\
       --key-vault kv-dev-abc123

DESCRIPTION:
    This script performs the following operations:
    1. Creates an Azure AD app registration for the bot
    2. Generates a client secret for the bot
    3. Creates Azure Bot Service resource
    4. Enables Microsoft Teams channel
    5. Stores bot credentials in Azure Key Vault
    6. Configures messaging endpoint

PREREQUISITES:
    - Azure CLI installed and authenticated (az login)
    - Sufficient permissions to create resources
    - Key Vault already exists with appropriate access policies
EOF
    exit 1
}

# Parse command line arguments
ENVIRONMENT=""
RESOURCE_GROUP=""
BOT_NAME=""
BOT_ENDPOINT=""
KEY_VAULT_NAME=""
LOCATION="global"

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
        -l|--location)
            LOCATION="$2"
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
if [[ -z "$ENVIRONMENT" || -z "$RESOURCE_GROUP" || -z "$BOT_NAME" || -z "$BOT_ENDPOINT" || -z "$KEY_VAULT_NAME" ]]; then
    log_error "Missing required parameters"
    usage
fi

# Validate environment value
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    log_error "Environment must be one of: dev, staging, prod"
    exit 1
fi

log_info "Starting bot registration process..."
log_info "Environment: $ENVIRONMENT"
log_info "Resource Group: $RESOURCE_GROUP"
log_info "Bot Name: $BOT_NAME"
log_info "Endpoint: $BOT_ENDPOINT"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    log_error "Azure CLI is not installed. Please install it first."
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    log_error "Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

# Step 1: Create Azure AD app registration
log_info "Creating Azure AD app registration..."

APP_DISPLAY_NAME="${BOT_NAME}-${ENVIRONMENT}"

# Check if app already exists
EXISTING_APP=$(az ad app list --display-name "$APP_DISPLAY_NAME" --query "[0].appId" -o tsv 2>/dev/null || true)

if [[ -n "$EXISTING_APP" ]]; then
    log_warning "App registration already exists: $EXISTING_APP"
    BOT_APP_ID="$EXISTING_APP"
else
    # Create new app registration
    BOT_APP_ID=$(az ad app create \
        --display-name "$APP_DISPLAY_NAME" \
        --available-to-other-tenants true \
        --query appId -o tsv)

    if [[ -z "$BOT_APP_ID" ]]; then
        log_error "Failed to create app registration"
        exit 1
    fi

    log_info "Created app registration: $BOT_APP_ID"
fi

# Step 2: Generate client secret
log_info "Generating client secret..."

BOT_APP_PASSWORD=$(az ad app credential reset \
    --id "$BOT_APP_ID" \
    --append \
    --years 2 \
    --query password -o tsv)

if [[ -z "$BOT_APP_PASSWORD" ]]; then
    log_error "Failed to generate client secret"
    exit 1
fi

log_info "Client secret generated successfully"

# Step 3: Store credentials in Key Vault
log_info "Storing credentials in Key Vault: $KEY_VAULT_NAME"

az keyvault secret set \
    --vault-name "$KEY_VAULT_NAME" \
    --name "bot-id" \
    --value "$BOT_APP_ID" \
    --output none

az keyvault secret set \
    --vault-name "$KEY_VAULT_NAME" \
    --name "bot-password" \
    --value "$BOT_APP_PASSWORD" \
    --output none

log_info "Credentials stored in Key Vault"

# Step 4: Create Azure Bot Service
log_info "Creating Azure Bot Service..."

# Check if bot already exists
if az bot show --name "$BOT_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
    log_warning "Bot Service already exists. Updating configuration..."

    # Update existing bot
    az bot update \
        --name "$BOT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --endpoint "$BOT_ENDPOINT" \
        --output none
else
    # Create new bot service
    az bot create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$BOT_NAME" \
        --kind registration \
        --app-type MultiTenant \
        --appid "$BOT_APP_ID" \
        --password "$BOT_APP_PASSWORD" \
        --endpoint "$BOT_ENDPOINT" \
        --location "$LOCATION" \
        --tags environment="$ENVIRONMENT" \
        --output none

    log_info "Bot Service created successfully"
fi

# Step 5: Enable Microsoft Teams channel
log_info "Enabling Microsoft Teams channel..."

# Check if Teams channel is already enabled
TEAMS_ENABLED=$(az bot msteams show \
    --name "$BOT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "properties.channelName" -o tsv 2>/dev/null || echo "")

if [[ "$TEAMS_ENABLED" == "MsTeamsChannel" ]]; then
    log_warning "Microsoft Teams channel already enabled"
else
    az bot msteams create \
        --name "$BOT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --enable-calling false \
        --calling-web-hook "" \
        --output none

    log_info "Microsoft Teams channel enabled"
fi

# Step 6: Configure bot properties
log_info "Configuring bot properties..."

az bot update \
    --name "$BOT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --icon-url "https://example.com/icon.png" \
    --output none

# Output summary
log_info "================================================"
log_info "Bot registration completed successfully!"
log_info "================================================"
log_info ""
log_info "Bot Details:"
log_info "  App ID: $BOT_APP_ID"
log_info "  Bot Name: $BOT_NAME"
log_info "  Endpoint: $BOT_ENDPOINT"
log_info "  Environment: $ENVIRONMENT"
log_info ""
log_info "Next Steps:"
log_info "  1. Generate Teams manifest with: ./scripts/generate-teams-manifest.sh"
log_info "  2. Create Teams package with: ./scripts/create-teams-package.sh"
log_info "  3. Test deployment with: ./scripts/test-teams-deployment.sh"
log_info ""
log_info "Credentials stored in Key Vault: $KEY_VAULT_NAME"
log_info "  - bot-id"
log_info "  - bot-password"
log_info ""

exit 0
