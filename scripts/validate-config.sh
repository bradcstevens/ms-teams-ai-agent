#!/bin/bash
# Pre-package Configuration Validation
# This script validates the application configuration before packaging

set -e

echo "=== Pre-Package Configuration Validation ==="

# Validate source directory exists
if [ ! -d "src" ]; then
    echo "ERROR: src directory not found"
    exit 1
fi

# Validate requirements.txt exists
if [ ! -f "src/requirements.txt" ]; then
    echo "ERROR: src/requirements.txt not found"
    exit 1
fi

# TODO: Add more validation as application develops
# - Validate Python syntax
# - Check for required environment variables
# - Verify dependencies are compatible

echo "Configuration validation passed"
exit 0
