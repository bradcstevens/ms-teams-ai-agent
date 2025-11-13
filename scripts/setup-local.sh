#!/bin/bash
# Local Development Environment Setup Script
# This script sets up the development environment for the Azure AI Agent Framework

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Azure AI Agent Framework - Local Development Setup ===${NC}"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed${NC}"
    echo "Please install Python 3.11 or later"
    exit 1
else
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
fi

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo -e "${YELLOW}WARNING: Azure CLI is not installed${NC}"
    echo "Install from: https://docs.microsoft.com/cli/azure/install-azure-cli"
else
    AZ_VERSION=$(az version --query '["azure-cli"]' -o tsv)
    echo -e "${GREEN}✓ Azure CLI $AZ_VERSION found${NC}"
fi

# Check Azure Developer CLI
if ! command -v azd &> /dev/null; then
    echo -e "${YELLOW}WARNING: Azure Developer CLI (azd) is not installed${NC}"
    echo "Install from: https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd"
else
    AZD_VERSION=$(azd version)
    echo -e "${GREEN}✓ Azure Developer CLI $AZD_VERSION found${NC}"
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}WARNING: Docker is not installed${NC}"
    echo "Install from: https://docs.docker.com/get-docker/"
else
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    echo -e "${GREEN}✓ Docker $DOCKER_VERSION found${NC}"
fi

echo ""

# Create Python virtual environment
echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Install Python dependencies (when requirements.txt is populated)
if [ -f "src/requirements.txt" ]; then
    echo "Installing Python dependencies..."
    # Check if requirements.txt has actual dependencies (not just comments/TODO)
    if grep -q '^[^#]' src/requirements.txt; then
        pip install --upgrade pip
        pip install -r src/requirements.txt
        echo -e "${GREEN}✓ Dependencies installed${NC}"
    else
        echo -e "${YELLOW}No dependencies to install yet (placeholder file)${NC}"
    fi
else
    echo -e "${YELLOW}requirements.txt not found, skipping dependency installation${NC}"
fi

# Create .env file template if it doesn't exist
echo ""
echo "Setting up environment variables..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Azure AI Agent Framework - Local Environment Configuration
# Copy this file to .env and fill in your values

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Azure Bot Service Configuration
BOT_ID=your-bot-app-id
BOT_PASSWORD=your-bot-app-password
BOT_TENANT_ID=your-azure-tenant-id

# Azure Resources
KEY_VAULT_NAME=your-keyvault-name
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=your-key-here

# Application Configuration
PYTHON_ENV=development
LOG_LEVEL=DEBUG

# Local Development
LOCAL_PORT=8000
EOF
    echo -e "${GREEN}✓ .env template created${NC}"
    echo -e "${YELLOW}  Please edit .env with your Azure resource values${NC}"
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi

# Create .gitignore entries
echo ""
echo "Updating .gitignore..."
if [ -f ".gitignore" ]; then
    # Add common Python and Azure entries if not present
    grep -q "^venv/" .gitignore || echo "venv/" >> .gitignore
    grep -q "^.env$" .gitignore || echo ".env" >> .gitignore
    grep -q "^__pycache__/" .gitignore || echo "__pycache__/" >> .gitignore
    grep -q "^*.pyc$" .gitignore || echo "*.pyc" >> .gitignore
    grep -q "^.azure/" .gitignore || echo ".azure/" >> .gitignore
    echo -e "${GREEN}✓ .gitignore updated${NC}"
else
    echo -e "${YELLOW}.gitignore not found, creating...${NC}"
    cat > .gitignore << 'EOF'
# Python
venv/
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Environment
.env
.env.local

# Azure
.azure/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
EOF
    echo -e "${GREEN}✓ .gitignore created${NC}"
fi

echo ""
echo -e "${BLUE}=== Setup Complete! ===${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env with your Azure resource values"
echo "2. Activate the virtual environment: ${YELLOW}source venv/bin/activate${NC}"
echo "3. Start development or deploy to Azure: ${YELLOW}azd up${NC}"
echo ""
echo "For Windows PowerShell, use: ${YELLOW}venv\\Scripts\\Activate.ps1${NC}"
echo ""
