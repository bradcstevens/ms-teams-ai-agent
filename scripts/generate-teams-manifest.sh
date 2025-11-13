#!/bin/bash
# Teams App Manifest Generation Script (Task 4.2)
# Generates Teams app manifest with dynamic environment-specific values

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

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Generate Teams app manifest with environment-specific values.

OPTIONS:
    -b, --bot-id ID            Bot application ID (GUID) [required]
    -e, --endpoint URL         Bot messaging endpoint URL [required]
    -v, --version VERSION      App version (default: 1.0.0)
    -n, --environment ENV      Environment (dev/staging/prod, default: dev)
    -o, --output DIR           Output directory (default: ./teams)
    -h, --help                 Show this help message

EXAMPLE:
    $0 --bot-id "12345678-1234-1234-1234-123456789012" \\
       --endpoint "ca-dev-abc123.azurecontainerapps.io/api/messages" \\
       --version "1.0.0" \\
       --environment dev

DESCRIPTION:
    This script generates a Teams app manifest.json file by substituting
    placeholder values with actual bot configuration.
EOF
    exit 1
}

# Parse arguments
BOT_ID=""
BOT_ENDPOINT=""
APP_VERSION="1.0.0"
ENVIRONMENT="dev"
OUTPUT_DIR="./teams"

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--bot-id)
            BOT_ID="$2"
            shift 2
            ;;
        -e|--endpoint)
            BOT_ENDPOINT="$2"
            shift 2
            ;;
        -v|--version)
            APP_VERSION="$2"
            shift 2
            ;;
        -n|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
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
if [[ -z "$BOT_ID" || -z "$BOT_ENDPOINT" ]]; then
    log_error "Missing required parameters: --bot-id and --endpoint are required"
    usage
fi

# Validate bot ID format (GUID)
if ! [[ "$BOT_ID" =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]]; then
    log_error "Invalid bot ID format. Must be a valid GUID."
    exit 1
fi

# Validate version format (semantic versioning)
if ! [[ "$APP_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    log_error "Invalid version format. Must be semantic version (e.g., 1.0.0)"
    exit 1
fi

# Strip https:// from endpoint if present
BOT_ENDPOINT="${BOT_ENDPOINT#https://}"
BOT_ENDPOINT="${BOT_ENDPOINT#http://}"

log_info "Generating Teams manifest..."
log_info "Bot ID: $BOT_ID"
log_info "Endpoint: $BOT_ENDPOINT"
log_info "Version: $APP_VERSION"
log_info "Environment: $ENVIRONMENT"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Check if template exists
TEMPLATE_FILE="$OUTPUT_DIR/manifest.template.json"
MANIFEST_FILE="$OUTPUT_DIR/manifest.json"

if [[ ! -f "$MANIFEST_FILE" ]]; then
    log_error "Manifest file not found: $MANIFEST_FILE"
    log_error "Please ensure the manifest template exists"
    exit 1
fi

# Create a temporary file for substitution
TEMP_MANIFEST=$(mktemp)

# Read the manifest template and substitute placeholders
sed -e "s|{{BOT_ID}}|$BOT_ID|g" \
    -e "s|{{BOT_ENDPOINT}}|$BOT_ENDPOINT|g" \
    -e "s|\"version\": \".*\"|\"version\": \"$APP_VERSION\"|" \
    "$MANIFEST_FILE" > "$TEMP_MANIFEST"

# Validate JSON syntax
if ! python3 -m json.tool "$TEMP_MANIFEST" > /dev/null 2>&1; then
    log_error "Generated manifest has invalid JSON syntax"
    rm "$TEMP_MANIFEST"
    exit 1
fi

# Move temp file to final location
mv "$TEMP_MANIFEST" "$MANIFEST_FILE"

log_info "Manifest generated successfully: $MANIFEST_FILE"

# Validate manifest using Python validator if available
if command -v python3 &> /dev/null; then
    VALIDATOR_SCRIPT="./src/app/teams/manifest_validator.py"
    if [[ -f "$VALIDATOR_SCRIPT" ]]; then
        log_info "Validating manifest..."
        if python3 -c "
import sys
sys.path.insert(0, './src')
from app.teams.manifest_validator import validate_manifest
is_valid, errors = validate_manifest('$MANIFEST_FILE')
if not is_valid:
    print('Validation errors:')
    for error in errors:
        print(f'  - {error}')
    sys.exit(1)
print('Manifest validation passed')
" 2>&1; then
            log_info "Manifest validation passed"
        else
            log_warning "Manifest validation failed (see errors above)"
        fi
    fi
fi

# Check if icons exist
if [[ ! -f "$OUTPUT_DIR/color.png" ]]; then
    log_warning "Color icon not found: $OUTPUT_DIR/color.png"
    log_warning "Please add a 192x192 color icon before packaging"
fi

if [[ ! -f "$OUTPUT_DIR/outline.png" ]]; then
    log_warning "Outline icon not found: $OUTPUT_DIR/outline.png"
    log_warning "Please add a 32x32 outline icon before packaging"
fi

log_info "================================================"
log_info "Manifest generation completed!"
log_info "================================================"
log_info ""
log_info "Next steps:"
log_info "  1. Review the generated manifest: $MANIFEST_FILE"
log_info "  2. Ensure icons are present:"
log_info "     - $OUTPUT_DIR/color.png (192x192)"
log_info "     - $OUTPUT_DIR/outline.png (32x32)"
log_info "  3. Create Teams package: ./scripts/create-teams-package.sh"
log_info ""

exit 0
