#!/bin/bash
# Teams App Package Upload Script
# Uploads Teams app package to organization catalog via Microsoft Graph API
#
# IMPORTANT: This script requires delegated (user) authentication.
# Application/service principal authentication is NOT supported by Microsoft
# for Teams app catalog uploads. See docs/TEAMS-APP-UPLOAD-RESEARCH.md
#
# Prerequisites:
#   - Azure CLI installed and configured
#   - User with AppCatalog.Submit or AppCatalog.ReadWrite.All permissions
#   - Valid Teams app package (.zip) with manifest.json, color.png, outline.png

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

Upload a Teams app package to the organization's app catalog via Microsoft Graph API.

OPTIONS:
    -p, --package FILE         Path to the Teams app package (.zip) [REQUIRED]
    -t, --tenant-id ID         Azure AD tenant ID (uses default if not specified)
    -u, --update APP_ID        Update existing app instead of creating new
    -r, --require-review       Submit for admin review (default: publish directly)
    -f, --force                Skip confirmation prompts
    -h, --help                 Show this help message

AUTHENTICATION:
    This script uses Azure CLI for authentication. If not already logged in,
    it will prompt for device code authentication.

    Application/service principal authentication is NOT supported by Microsoft
    for Teams app catalog operations. A user must authenticate interactively.

REQUIRED PERMISSIONS:
    - AppCatalog.Submit (minimum for submitting apps for review)
    - AppCatalog.ReadWrite.All (for direct publishing without review)

EXAMPLES:
    # Upload new app to catalog (requires admin approval)
    $0 --package ./teams-app-dev-1.0.0.zip --require-review

    # Upload and publish directly (requires ReadWrite.All permission)
    $0 --package ./teams-app-dev-1.0.0.zip

    # Update existing app
    $0 --package ./teams-app-dev-1.0.1.zip --update <teams-app-id>

    # Non-interactive mode (assumes already authenticated)
    $0 --package ./teams-app-dev-1.0.0.zip --force

DOCUMENTATION:
    See docs/TEAMS-APP-UPLOAD-RESEARCH.md for detailed information about
    programmatic Teams app upload methods and limitations.

EOF
    exit 1
}

# Default values
PACKAGE_PATH=""
TENANT_ID=""
UPDATE_APP_ID=""
REQUIRE_REVIEW=false
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--package)
            PACKAGE_PATH="$2"
            shift 2
            ;;
        -t|--tenant-id)
            TENANT_ID="$2"
            shift 2
            ;;
        -u|--update)
            UPDATE_APP_ID="$2"
            shift 2
            ;;
        -r|--require-review)
            REQUIRE_REVIEW=true
            shift
            ;;
        -f|--force)
            FORCE=true
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

# Validate required arguments
if [[ -z "$PACKAGE_PATH" ]]; then
    log_error "Package path is required. Use --package <path>"
    usage
fi

if [[ ! -f "$PACKAGE_PATH" ]]; then
    log_error "Package file not found: $PACKAGE_PATH"
    exit 1
fi

# Check Azure CLI is installed
if ! command -v az &> /dev/null; then
    log_error "Azure CLI not found. Please install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

echo ""
echo "=============================================="
echo "Teams App Package Upload"
echo "=============================================="
echo ""
log_info "Package: $PACKAGE_PATH"
log_info "Mode: $([ -n "$UPDATE_APP_ID" ] && echo "Update ($UPDATE_APP_ID)" || echo "New upload")"
log_info "Require Review: $REQUIRE_REVIEW"
echo ""

# Step 1: Check Azure CLI authentication
log_step "Step 1: Checking Azure CLI authentication..."

# Check if already logged in
if ! az account show &> /dev/null; then
    log_warning "Not logged in to Azure CLI"

    if [[ "$FORCE" == "true" ]]; then
        log_error "Force mode enabled but not authenticated. Please run 'az login' first."
        exit 1
    fi

    echo ""
    log_info "Starting device code authentication..."
    log_info "A browser window will open for you to sign in."
    echo ""

    if [[ -n "$TENANT_ID" ]]; then
        az login --tenant "$TENANT_ID" --use-device-code
    else
        az login --use-device-code
    fi

    if [[ $? -ne 0 ]]; then
        log_error "Authentication failed"
        exit 1
    fi
fi

# Get current account info
ACCOUNT_INFO=$(az account show --output json)
CURRENT_USER=$(echo "$ACCOUNT_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin).get('user', {}).get('name', 'Unknown'))")
CURRENT_TENANT=$(echo "$ACCOUNT_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin).get('tenantId', 'Unknown'))")

log_info "Authenticated as: $CURRENT_USER"
log_info "Tenant ID: $CURRENT_TENANT"

# Step 2: Get access token for Microsoft Graph
log_step "Step 2: Acquiring Microsoft Graph access token..."

# Get token for Graph API
ACCESS_TOKEN=$(az account get-access-token --resource "https://graph.microsoft.com" --query accessToken --output tsv 2>/dev/null)

if [[ -z "$ACCESS_TOKEN" ]]; then
    log_error "Failed to acquire access token for Microsoft Graph"
    log_error "Ensure your account has the required permissions:"
    log_error "  - AppCatalog.Submit (for review submission)"
    log_error "  - AppCatalog.ReadWrite.All (for direct publishing)"
    exit 1
fi

log_info "Access token acquired successfully"

# Step 3: Validate package
log_step "Step 3: Validating Teams app package..."

# Check package is a valid zip
if ! unzip -t "$PACKAGE_PATH" &> /dev/null; then
    log_error "Invalid zip file: $PACKAGE_PATH"
    exit 1
fi

# Check required files exist in package
REQUIRED_FILES=("manifest.json" "color.png" "outline.png")
for FILE in "${REQUIRED_FILES[@]}"; do
    if ! unzip -l "$PACKAGE_PATH" | grep -q "$FILE"; then
        log_error "Package missing required file: $FILE"
        exit 1
    fi
done

log_info "Package validation passed"

# Extract app info from manifest for display
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

unzip -q "$PACKAGE_PATH" manifest.json -d "$TEMP_DIR"
APP_NAME=$(python3 -c "import json; m=json.load(open('$TEMP_DIR/manifest.json')); print(m.get('name', {}).get('short', 'Unknown'))")
APP_VERSION=$(python3 -c "import json; m=json.load(open('$TEMP_DIR/manifest.json')); print(m.get('version', 'Unknown'))")
APP_ID=$(python3 -c "import json; m=json.load(open('$TEMP_DIR/manifest.json')); print(m.get('id', 'Unknown'))")

log_info "App Name: $APP_NAME"
log_info "App Version: $APP_VERSION"
log_info "Manifest ID: $APP_ID"

# Step 4: Confirmation
if [[ "$FORCE" != "true" ]]; then
    echo ""
    log_warning "You are about to upload this app to your organization's Teams app catalog."
    echo ""
    read -p "Continue? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Upload cancelled"
        exit 0
    fi
fi

# Step 5: Upload to Teams App Catalog
log_step "Step 4: Uploading to Teams App Catalog..."

# Determine API endpoint and method
if [[ -n "$UPDATE_APP_ID" ]]; then
    # Update existing app
    GRAPH_URL="https://graph.microsoft.com/v1.0/appCatalogs/teamsApps/$UPDATE_APP_ID/appDefinitions"
    log_info "Updating existing app: $UPDATE_APP_ID"
else
    # Create new app
    GRAPH_URL="https://graph.microsoft.com/v1.0/appCatalogs/teamsApps"
    if [[ "$REQUIRE_REVIEW" == "true" ]]; then
        GRAPH_URL="${GRAPH_URL}?requiresReview=true"
        log_info "Submitting for admin review"
    fi
fi

# Upload the package
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "$GRAPH_URL" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/zip" \
    --data-binary @"$PACKAGE_PATH")

# Parse response
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')

echo ""

if [[ "$HTTP_CODE" == "201" ]] || [[ "$HTTP_CODE" == "200" ]]; then
    log_info "Upload successful!"
    echo ""

    # Extract app ID from response
    TEAMS_APP_ID=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 'Unknown'))" 2>/dev/null || echo "")

    if [[ -n "$TEAMS_APP_ID" && "$TEAMS_APP_ID" != "Unknown" ]]; then
        log_info "Teams App ID: $TEAMS_APP_ID"

        # Save app ID for future updates
        echo "$TEAMS_APP_ID" > ".teams-app-id"
        log_info "App ID saved to .teams-app-id for future updates"
    fi

    echo ""
    echo "=============================================="
    echo "Upload Complete!"
    echo "=============================================="
    echo ""

    if [[ "$REQUIRE_REVIEW" == "true" ]]; then
        log_info "Your app has been submitted for admin review."
        log_info "An admin must approve it before users can install it."
        echo ""
        log_info "Admin Center: https://admin.teams.microsoft.com/policies/manage-apps"
    else
        log_info "Your app is now available in your organization's app catalog."
        echo ""
        log_info "Users can find it in Teams:"
        log_info "  1. Open Microsoft Teams"
        log_info "  2. Go to Apps"
        log_info "  3. Search for '$APP_NAME'"
        log_info "  4. Click 'Add' to install"
    fi

    echo ""
    log_info "To update this app in the future, run:"
    log_info "  $0 --package <new-package.zip> --update $TEAMS_APP_ID"
    echo ""

    exit 0
else
    log_error "Upload failed with HTTP status: $HTTP_CODE"
    echo ""
    log_error "Response:"
    echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"
    echo ""

    # Provide helpful error messages
    case "$HTTP_CODE" in
        401)
            log_error "Authentication failed. Your session may have expired."
            log_error "Try: az logout && az login"
            ;;
        403)
            log_error "Permission denied. You need one of these permissions:"
            log_error "  - AppCatalog.Submit (for review submission)"
            log_error "  - AppCatalog.ReadWrite.All (for direct publishing)"
            log_error ""
            log_error "Contact your Azure AD admin to grant these permissions."
            ;;
        409)
            log_error "Conflict: An app with this ID may already exist."
            log_error "Use --update <app-id> to update an existing app."
            ;;
        *)
            log_error "See Microsoft Graph API documentation for error details:"
            log_error "https://learn.microsoft.com/en-us/graph/api/teamsapp-publish"
            ;;
    esac

    exit 1
fi
