#!/bin/bash
# Teams App Package Creation Script
# Bundles manifest.json and icons into a deployment-ready .zip package

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

Create a Teams app package (.zip) from manifest and icons.

OPTIONS:
    -i, --input DIR            Input directory with manifest and icons (default: ./teams)
    -o, --output FILE          Output zip file path (default: ./teams-app-package.zip)
    -v, --version VERSION      App version for package naming (default: from manifest)
    -n, --environment ENV      Environment tag (dev/staging/prod, default: none)
    -h, --help                 Show this help message

EXAMPLE:
    $0 --input ./teams \\
       --output ./dist/teams-app-dev-1.0.0.zip \\
       --version 1.0.0 \\
       --environment dev

DESCRIPTION:
    Creates a Teams app package containing:
    - manifest.json (validated)
    - color.png (192x192 icon)
    - outline.png (32x32 icon)

REQUIREMENTS:
    - manifest.json must exist and be valid
    - Both icon files must exist
    - zip command must be available
EOF
    exit 1
}

# Parse arguments
INPUT_DIR="./teams"
OUTPUT_FILE=""
APP_VERSION=""
ENVIRONMENT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input)
            INPUT_DIR="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
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
        -h|--help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Check if zip is available
if ! command -v zip &> /dev/null; then
    log_error "zip command not found. Please install zip."
    exit 1
fi

# Validate input directory exists
if [[ ! -d "$INPUT_DIR" ]]; then
    log_error "Input directory not found: $INPUT_DIR"
    exit 1
fi

log_info "Creating Teams app package..."
log_info "Input directory: $INPUT_DIR"

# Check required files
MANIFEST_FILE="$INPUT_DIR/manifest.json"
COLOR_ICON="$INPUT_DIR/color.png"
OUTLINE_ICON="$INPUT_DIR/outline.png"

if [[ ! -f "$MANIFEST_FILE" ]]; then
    log_error "Manifest file not found: $MANIFEST_FILE"
    exit 1
fi

if [[ ! -f "$COLOR_ICON" ]]; then
    log_error "Color icon not found: $COLOR_ICON"
    log_error "Please add a 192x192 PNG icon at $COLOR_ICON"
    exit 1
fi

if [[ ! -f "$OUTLINE_ICON" ]]; then
    log_error "Outline icon not found: $OUTLINE_ICON"
    log_error "Please add a 32x32 PNG icon at $OUTLINE_ICON"
    exit 1
fi

log_info "All required files found"

# Validate manifest JSON syntax
log_info "Validating manifest..."

if ! python3 -m json.tool "$MANIFEST_FILE" > /dev/null 2>&1; then
    log_error "Manifest has invalid JSON syntax"
    exit 1
fi

log_info "Manifest JSON syntax valid"

# Extract version from manifest if not provided
if [[ -z "$APP_VERSION" ]]; then
    APP_VERSION=$(python3 -c "
import json
with open('$MANIFEST_FILE', 'r') as f:
    manifest = json.load(f)
    print(manifest.get('version', '1.0.0'))
" 2>/dev/null || echo "1.0.0")
    log_info "Extracted version from manifest: $APP_VERSION"
fi

# Determine output file name if not provided
if [[ -z "$OUTPUT_FILE" ]]; then
    if [[ -n "$ENVIRONMENT" ]]; then
        OUTPUT_FILE="./teams-app-${ENVIRONMENT}-${APP_VERSION}.zip"
    else
        OUTPUT_FILE="./teams-app-${APP_VERSION}.zip"
    fi
    log_info "Output file: $OUTPUT_FILE"
fi

# Convert to absolute path to ensure it works after cd
OUTPUT_FILE=$(cd "$(dirname "$OUTPUT_FILE")" && pwd)/$(basename "$OUTPUT_FILE")

# Create output directory if needed
OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
mkdir -p "$OUTPUT_DIR"

# Remove existing package if it exists
if [[ -f "$OUTPUT_FILE" ]]; then
    log_warning "Removing existing package: $OUTPUT_FILE"
    rm "$OUTPUT_FILE"
fi

# Create temporary directory for packaging
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

log_info "Preparing package contents..."

# Copy files to temp directory
cp "$MANIFEST_FILE" "$TEMP_DIR/"
cp "$COLOR_ICON" "$TEMP_DIR/"
cp "$OUTLINE_ICON" "$TEMP_DIR/"

# Validate manifest placeholders are substituted
if grep -q "{{BOT_ID}}" "$TEMP_DIR/manifest.json" || grep -q "{{BOT_ENDPOINT}}" "$TEMP_DIR/manifest.json"; then
    log_error "Manifest contains unsubstituted placeholders!"
    log_error "Please run generate-teams-manifest.sh first to substitute values."
    exit 1
fi

# Create zip package
log_info "Creating zip package..."

cd "$TEMP_DIR"
zip -q "$OUTPUT_FILE" manifest.json color.png outline.png
cd - > /dev/null

# Verify package was created
if [[ ! -f "$OUTPUT_FILE" ]]; then
    log_error "Failed to create package"
    exit 1
fi

# Get package size
PACKAGE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)

log_info "Package created successfully: $OUTPUT_FILE"
log_info "Package size: $PACKAGE_SIZE"

# Verify package contents
log_info "Verifying package contents..."

if ! unzip -l "$OUTPUT_FILE" | grep -q "manifest.json"; then
    log_error "Package verification failed: manifest.json missing"
    exit 1
fi

if ! unzip -l "$OUTPUT_FILE" | grep -q "color.png"; then
    log_error "Package verification failed: color.png missing"
    exit 1
fi

if ! unzip -l "$OUTPUT_FILE" | grep -q "outline.png"; then
    log_error "Package verification failed: outline.png missing"
    exit 1
fi

log_info "Package contents verified"

# Display package contents
log_info ""
log_info "Package contents:"
unzip -l "$OUTPUT_FILE"

log_info ""
log_info "================================================"
log_info "Teams app package created successfully!"
log_info "================================================"
log_info ""
log_info "Package Details:"
log_info "  Location: $OUTPUT_FILE"
log_info "  Size: $PACKAGE_SIZE"
log_info "  Version: $APP_VERSION"
if [[ -n "$ENVIRONMENT" ]]; then
    log_info "  Environment: $ENVIRONMENT"
fi
log_info ""
log_info "Next Steps:"
log_info "  1. Upload to Teams Admin Center:"
log_info "     https://admin.teams.microsoft.com/policies/manage-apps"
log_info "  2. Or sideload for testing:"
log_info "     Teams > Apps > Upload a custom app > Upload for [your org]"
log_info "  3. Test the deployment:"
log_info "     ./scripts/test-teams-deployment.sh"
log_info ""

exit 0
