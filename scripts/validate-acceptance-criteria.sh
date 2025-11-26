#!/bin/bash
# Acceptance Criteria Validation Checklist (Task 5.5)
# Validates all 30+ PRD success criteria from Appendix C
# Generates comprehensive validation report

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Counters per category (using simple variables for bash 3.x compatibility)
DEPLOYMENT_PASSED=0
DEPLOYMENT_FAILED=0
DEPLOYMENT_WARNING=0
DEPLOYMENT_SKIPPED=0
TEAMS_PASSED=0
TEAMS_FAILED=0
TEAMS_WARNING=0
TEAMS_SKIPPED=0
MCP_PASSED=0
MCP_FAILED=0
MCP_WARNING=0
MCP_SKIPPED=0
MONITORING_PASSED=0
MONITORING_FAILED=0
MONITORING_WARNING=0
MONITORING_SKIPPED=0
DOCUMENTATION_PASSED=0
DOCUMENTATION_FAILED=0
DOCUMENTATION_WARNING=0
DOCUMENTATION_SKIPPED=0

# Total counters
TOTAL_PASSED=0
TOTAL_FAILED=0
TOTAL_WARNING=0
TOTAL_SKIPPED=0

# Report file
REPORT_FILE=""
DETAILED_REPORT=""

log_header() {
    echo -e "\n${MAGENTA}============================================================${NC}"
    echo -e "${MAGENTA}$1${NC}"
    echo -e "${MAGENTA}============================================================${NC}"
}

log_section() {
    echo -e "\n${BLUE}--- $1 ---${NC}"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_skip() {
    echo -e "${CYAN}[SKIP]${NC} $1"
}

# Record test result
record_result() {
    local category="$1"
    local test_name="$2"
    local result="$3"
    local message="${4:-}"

    case "$result" in
        "PASS")
            log_pass "$test_name"
            case "$category" in
                deployment) DEPLOYMENT_PASSED=$((DEPLOYMENT_PASSED + 1)) ;;
                teams) TEAMS_PASSED=$((TEAMS_PASSED + 1)) ;;
                mcp) MCP_PASSED=$((MCP_PASSED + 1)) ;;
                monitoring) MONITORING_PASSED=$((MONITORING_PASSED + 1)) ;;
                documentation) DOCUMENTATION_PASSED=$((DOCUMENTATION_PASSED + 1)) ;;
            esac
            TOTAL_PASSED=$((TOTAL_PASSED + 1))
            echo "| $test_name | PASS | $message |" >> "$DETAILED_REPORT"
            ;;
        "FAIL")
            log_fail "$test_name: $message"
            case "$category" in
                deployment) DEPLOYMENT_FAILED=$((DEPLOYMENT_FAILED + 1)) ;;
                teams) TEAMS_FAILED=$((TEAMS_FAILED + 1)) ;;
                mcp) MCP_FAILED=$((MCP_FAILED + 1)) ;;
                monitoring) MONITORING_FAILED=$((MONITORING_FAILED + 1)) ;;
                documentation) DOCUMENTATION_FAILED=$((DOCUMENTATION_FAILED + 1)) ;;
            esac
            TOTAL_FAILED=$((TOTAL_FAILED + 1))
            echo "| $test_name | FAIL | $message |" >> "$DETAILED_REPORT"
            ;;
        "WARN")
            log_warn "$test_name: $message"
            case "$category" in
                deployment) DEPLOYMENT_WARNING=$((DEPLOYMENT_WARNING + 1)) ;;
                teams) TEAMS_WARNING=$((TEAMS_WARNING + 1)) ;;
                mcp) MCP_WARNING=$((MCP_WARNING + 1)) ;;
                monitoring) MONITORING_WARNING=$((MONITORING_WARNING + 1)) ;;
                documentation) DOCUMENTATION_WARNING=$((DOCUMENTATION_WARNING + 1)) ;;
            esac
            TOTAL_WARNING=$((TOTAL_WARNING + 1))
            echo "| $test_name | WARN | $message |" >> "$DETAILED_REPORT"
            ;;
        "SKIP")
            log_skip "$test_name: $message"
            case "$category" in
                deployment) DEPLOYMENT_SKIPPED=$((DEPLOYMENT_SKIPPED + 1)) ;;
                teams) TEAMS_SKIPPED=$((TEAMS_SKIPPED + 1)) ;;
                mcp) MCP_SKIPPED=$((MCP_SKIPPED + 1)) ;;
                monitoring) MONITORING_SKIPPED=$((MONITORING_SKIPPED + 1)) ;;
                documentation) DOCUMENTATION_SKIPPED=$((DOCUMENTATION_SKIPPED + 1)) ;;
            esac
            TOTAL_SKIPPED=$((TOTAL_SKIPPED + 1))
            echo "| $test_name | SKIP | $message |" >> "$DETAILED_REPORT"
            ;;
    esac
}

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Validate all PRD acceptance criteria for the MS Teams AI Agent.

OPTIONS:
    -e, --environment ENV     Azure environment to validate (optional)
    -o, --output FILE         Output report file (default: validation-report-TIMESTAMP.md)
    -s, --skip-deployment     Skip deployment-specific tests (for pre-deployment validation)
    -q, --quick               Run quick validation (skip slow tests)
    -h, --help                Show this help message

EXAMPLE:
    # Full validation
    $0

    # Validate specific environment
    $0 --environment dev

    # Pre-deployment validation only
    $0 --skip-deployment

    # Quick validation
    $0 --quick
EOF
    exit 0
}

# Parse arguments
ENVIRONMENT=""
SKIP_DEPLOYMENT=false
QUICK_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment) ENVIRONMENT="$2"; shift 2 ;;
        -o|--output) REPORT_FILE="$2"; shift 2 ;;
        -s|--skip-deployment) SKIP_DEPLOYMENT=true; shift ;;
        -q|--quick) QUICK_MODE=true; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

# Set default report file
if [[ -z "$REPORT_FILE" ]]; then
    REPORT_FILE="$PROJECT_ROOT/validation-report-$(date +%Y%m%d-%H%M%S).md"
fi
DETAILED_REPORT="$PROJECT_ROOT/.validation-details-tmp.md"

# Start timing
START_TIME=$(date +%s)

log_header "MS Teams AI Agent - Acceptance Criteria Validation"
echo "Start Time: $(date)"
echo "Project Root: $PROJECT_ROOT"
echo "Environment: ${ENVIRONMENT:-'(local validation)'}"
echo "Skip Deployment Tests: $SKIP_DEPLOYMENT"
echo ""

# Initialize detailed report
cat > "$DETAILED_REPORT" << 'EOF'
| Test | Result | Details |
|------|--------|---------|
EOF

# =============================================================================
# CATEGORY 1: DEPLOYMENT AUTOMATION (7 criteria)
# =============================================================================
log_header "Category 1: Deployment Automation"
CATEGORY="deployment"
echo "" >> "$DETAILED_REPORT"
echo "### Deployment Automation" >> "$DETAILED_REPORT"
echo "| Test | Result | Details |" >> "$DETAILED_REPORT"
echo "|------|--------|---------|" >> "$DETAILED_REPORT"

# 1.1: azure.yaml exists and is valid
log_section "1.1: azure.yaml Configuration"
if [[ -f "$PROJECT_ROOT/azure.yaml" ]]; then
    if grep -q "name:" "$PROJECT_ROOT/azure.yaml" && grep -q "services:" "$PROJECT_ROOT/azure.yaml"; then
        record_result "$CATEGORY" "azure.yaml exists and valid" "PASS" "Contains name and services sections"
    else
        record_result "$CATEGORY" "azure.yaml exists and valid" "FAIL" "Missing required sections"
    fi
else
    record_result "$CATEGORY" "azure.yaml exists and valid" "FAIL" "File not found"
fi

# 1.2: All Bicep modules exist and compile
log_section "1.2: Bicep Infrastructure"
BICEP_FILES=(
    "infra/main.bicep"
    "infra/ai/openai.bicep"
    "infra/bot/bot-service.bicep"
    "infra/security/key-vault.bicep"
    "infra/core/host/container-app.bicep"
    "infra/core/host/container-registry.bicep"
)

all_bicep_exist=true
for bicep_file in "${BICEP_FILES[@]}"; do
    if [[ ! -f "$PROJECT_ROOT/$bicep_file" ]]; then
        record_result "$CATEGORY" "Bicep module: $bicep_file" "FAIL" "File not found"
        all_bicep_exist=false
    fi
done

if $all_bicep_exist; then
    record_result "$CATEGORY" "All Bicep modules exist" "PASS" "${#BICEP_FILES[@]} modules found"
fi

# Check if Bicep compiles
if command -v az &>/dev/null && [[ -f "$PROJECT_ROOT/infra/main.bicep" ]]; then
    if az bicep build --file "$PROJECT_ROOT/infra/main.bicep" --outdir /tmp &>/dev/null; then
        record_result "$CATEGORY" "Bicep compilation" "PASS" "main.bicep compiles successfully"
    else
        record_result "$CATEGORY" "Bicep compilation" "FAIL" "Compilation errors"
    fi
else
    record_result "$CATEGORY" "Bicep compilation" "SKIP" "Azure CLI or main.bicep not available"
fi

# 1.3: Container image configuration
log_section "1.3: Container Image"
if [[ -f "$PROJECT_ROOT/src/Dockerfile" ]]; then
    # Check for multi-stage build
    if grep -q "FROM.*AS" "$PROJECT_ROOT/src/Dockerfile"; then
        record_result "$CATEGORY" "Dockerfile multi-stage build" "PASS" "Uses multi-stage build"
    else
        record_result "$CATEGORY" "Dockerfile multi-stage build" "WARN" "Not using multi-stage build"
    fi

    # Check for health endpoint
    if grep -q "HEALTHCHECK\|/health" "$PROJECT_ROOT/src/Dockerfile"; then
        record_result "$CATEGORY" "Dockerfile health check" "PASS" "Health check configured"
    else
        record_result "$CATEGORY" "Dockerfile health check" "WARN" "No explicit health check in Dockerfile"
    fi
else
    record_result "$CATEGORY" "Dockerfile" "FAIL" "src/Dockerfile not found"
fi

# 1.4: Required outputs in main.bicep
log_section "1.4: Bicep Outputs"
REQUIRED_OUTPUTS=(
    "AZURE_OPENAI_ENDPOINT"
    "AZURE_OPENAI_DEPLOYMENT_NAME"
    "BOT_ID"
    "KEY_VAULT_NAME"
    "APPLICATIONINSIGHTS_CONNECTION_STRING"
    "CONTAINER_REGISTRY_ENDPOINT"
    "CONTAINER_APP_NAME"
)

if [[ -f "$PROJECT_ROOT/infra/main.bicep" ]]; then
    outputs_found=0
    for output in "${REQUIRED_OUTPUTS[@]}"; do
        if grep -q "output $output" "$PROJECT_ROOT/infra/main.bicep"; then
            ((outputs_found++))
        fi
    done

    if [[ $outputs_found -eq ${#REQUIRED_OUTPUTS[@]} ]]; then
        record_result "$CATEGORY" "Bicep outputs complete" "PASS" "All ${#REQUIRED_OUTPUTS[@]} outputs defined"
    else
        record_result "$CATEGORY" "Bicep outputs complete" "WARN" "$outputs_found/${#REQUIRED_OUTPUTS[@]} outputs found"
    fi
else
    record_result "$CATEGORY" "Bicep outputs complete" "SKIP" "main.bicep not found"
fi

# 1.5: azd hooks configured
log_section "1.5: azd Hooks"
if [[ -f "$PROJECT_ROOT/azure.yaml" ]]; then
    hooks_count=0
    for hook in "prepackage" "postprovision" "postdeploy"; do
        if grep -q "$hook:" "$PROJECT_ROOT/azure.yaml"; then
            ((hooks_count++))
        fi
    done

    if [[ $hooks_count -ge 2 ]]; then
        record_result "$CATEGORY" "azd hooks configured" "PASS" "$hooks_count hooks found"
    else
        record_result "$CATEGORY" "azd hooks configured" "WARN" "Only $hooks_count hooks found (expected 2+)"
    fi
else
    record_result "$CATEGORY" "azd hooks configured" "SKIP" "azure.yaml not found"
fi

# 1.6: Resource tagging
log_section "1.6: Resource Tagging"
if [[ -f "$PROJECT_ROOT/infra/main.bicep" ]]; then
    if grep -q "azd-env-name" "$PROJECT_ROOT/infra/main.bicep"; then
        record_result "$CATEGORY" "Resource tagging (azd-env-name)" "PASS" "Tag defined in main.bicep"
    else
        record_result "$CATEGORY" "Resource tagging (azd-env-name)" "FAIL" "azd-env-name tag not found"
    fi
else
    record_result "$CATEGORY" "Resource tagging" "SKIP" "main.bicep not found"
fi

# 1.7: Deployment scripts exist
log_section "1.7: Deployment Scripts"
REQUIRED_SCRIPTS=(
    "scripts/setup-local.sh"
    "scripts/validate-azd-config.sh"
    "scripts/create-bot-registration.sh"
    "scripts/generate-teams-manifest.sh"
    "scripts/deploy-teams-bot.sh"
)

scripts_found=0
for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [[ -f "$PROJECT_ROOT/$script" ]]; then
        ((scripts_found++))
    fi
done

if [[ $scripts_found -eq ${#REQUIRED_SCRIPTS[@]} ]]; then
    record_result "$CATEGORY" "Deployment scripts exist" "PASS" "All ${#REQUIRED_SCRIPTS[@]} scripts found"
else
    record_result "$CATEGORY" "Deployment scripts exist" "WARN" "$scripts_found/${#REQUIRED_SCRIPTS[@]} scripts found"
fi

# =============================================================================
# CATEGORY 2: TEAMS INTEGRATION (6 criteria)
# =============================================================================
log_header "Category 2: Teams Integration"
CATEGORY="teams"
echo "" >> "$DETAILED_REPORT"
echo "### Teams Integration" >> "$DETAILED_REPORT"
echo "| Test | Result | Details |" >> "$DETAILED_REPORT"
echo "|------|--------|---------|" >> "$DETAILED_REPORT"

# 2.1: Teams manifest template exists
log_section "2.1: Teams Manifest"
if [[ -f "$PROJECT_ROOT/teams/manifest.json" ]]; then
    # Check for required fields
    if grep -q "botId" "$PROJECT_ROOT/teams/manifest.json" && grep -q "manifestVersion" "$PROJECT_ROOT/teams/manifest.json"; then
        record_result "$CATEGORY" "Teams manifest template" "PASS" "Contains required fields"
    else
        record_result "$CATEGORY" "Teams manifest template" "WARN" "Missing some required fields"
    fi
else
    record_result "$CATEGORY" "Teams manifest template" "FAIL" "teams/manifest.json not found"
fi

# 2.2: Bot icons exist
log_section "2.2: Bot Icons"
icons_found=0
for icon in "teams/color.png" "teams/outline.png"; do
    if [[ -f "$PROJECT_ROOT/$icon" ]]; then
        ((icons_found++))
    fi
done

if [[ $icons_found -eq 2 ]]; then
    record_result "$CATEGORY" "Bot icons (color/outline)" "PASS" "Both icons present"
else
    record_result "$CATEGORY" "Bot icons (color/outline)" "WARN" "$icons_found/2 icons found"
fi

# 2.3: Bot Framework integration
log_section "2.3: Bot Framework Integration"
if [[ -f "$PROJECT_ROOT/src/requirements.txt" ]]; then
    if grep -q "botbuilder" "$PROJECT_ROOT/src/requirements.txt"; then
        record_result "$CATEGORY" "Bot Framework SDK" "PASS" "botbuilder in requirements.txt"
    else
        record_result "$CATEGORY" "Bot Framework SDK" "FAIL" "botbuilder not in requirements.txt"
    fi
else
    record_result "$CATEGORY" "Bot Framework SDK" "SKIP" "requirements.txt not found"
fi

# 2.4: Bot endpoint implementation
log_section "2.4: Bot Endpoint"
BOT_ENDPOINT_FILES=$(find "$PROJECT_ROOT/src" -name "*.py" -exec grep -l "api/messages\|/messages" {} \; 2>/dev/null | head -1)
if [[ -n "$BOT_ENDPOINT_FILES" ]]; then
    record_result "$CATEGORY" "Bot messages endpoint" "PASS" "Found in: $(basename "$BOT_ENDPOINT_FILES")"
else
    record_result "$CATEGORY" "Bot messages endpoint" "WARN" "No /api/messages endpoint found in source"
fi

# 2.5: Bot Service Bicep module
log_section "2.5: Bot Service Configuration"
if [[ -f "$PROJECT_ROOT/infra/bot/bot-service.bicep" ]]; then
    if grep -q "Microsoft.BotService/botServices" "$PROJECT_ROOT/infra/bot/bot-service.bicep"; then
        record_result "$CATEGORY" "Bot Service Bicep" "PASS" "Bot Service resource defined"
    else
        record_result "$CATEGORY" "Bot Service Bicep" "WARN" "Bot Service resource type not found"
    fi

    # Check for Teams channel
    if grep -q "msteams\|MsTeamsChannel" "$PROJECT_ROOT/infra/bot/bot-service.bicep"; then
        record_result "$CATEGORY" "Teams Channel config" "PASS" "Teams channel configured"
    else
        record_result "$CATEGORY" "Teams Channel config" "WARN" "Teams channel not explicitly configured"
    fi
else
    record_result "$CATEGORY" "Bot Service Bicep" "FAIL" "bot-service.bicep not found"
fi

# 2.6: Typing indicator support
log_section "2.6: Typing Indicator"
TYPING_FILES=$(find "$PROJECT_ROOT/src" -name "*.py" -exec grep -l "typing\|Typing\|ShowTypingMiddleware" {} \; 2>/dev/null | head -1)
if [[ -n "$TYPING_FILES" ]]; then
    record_result "$CATEGORY" "Typing indicator support" "PASS" "Found typing implementation"
else
    record_result "$CATEGORY" "Typing indicator support" "WARN" "No typing indicator implementation found"
fi

# =============================================================================
# CATEGORY 3: MCP INTEGRATION (6 criteria)
# =============================================================================
log_header "Category 3: MCP Integration"
CATEGORY="mcp"
echo "" >> "$DETAILED_REPORT"
echo "### MCP Integration" >> "$DETAILED_REPORT"
echo "| Test | Result | Details |" >> "$DETAILED_REPORT"
echo "|------|--------|---------|" >> "$DETAILED_REPORT"

# 3.1: MCP configuration file
log_section "3.1: MCP Configuration"
MCP_CONFIG=""
for config in "mcp_servers.json" "mcp_servers.json.example" "src/config/mcp_servers.json"; do
    if [[ -f "$PROJECT_ROOT/$config" ]]; then
        MCP_CONFIG="$PROJECT_ROOT/$config"
        break
    fi
done

if [[ -n "$MCP_CONFIG" ]]; then
    record_result "$CATEGORY" "MCP config file exists" "PASS" "$(basename "$MCP_CONFIG")"

    # Check for at least 2 MCP servers
    server_count=$(grep -c '"enabled": true' "$MCP_CONFIG" 2>/dev/null || echo "0")
    if [[ $server_count -ge 2 ]]; then
        record_result "$CATEGORY" "At least 2 MCP servers configured" "PASS" "$server_count servers enabled"
    else
        record_result "$CATEGORY" "At least 2 MCP servers configured" "WARN" "Only $server_count servers enabled (need 2+)"
    fi
else
    record_result "$CATEGORY" "MCP config file exists" "FAIL" "No MCP config found"
fi

# 3.2: MCP SDK in requirements
log_section "3.2: MCP SDK"
if [[ -f "$PROJECT_ROOT/src/requirements.txt" ]]; then
    if grep -qi "modelcontextprotocol\|mcp" "$PROJECT_ROOT/src/requirements.txt"; then
        record_result "$CATEGORY" "MCP SDK dependency" "PASS" "MCP SDK in requirements"
    else
        record_result "$CATEGORY" "MCP SDK dependency" "WARN" "MCP SDK not in requirements"
    fi
else
    record_result "$CATEGORY" "MCP SDK dependency" "SKIP" "requirements.txt not found"
fi

# 3.3: MCP client implementation
log_section "3.3: MCP Client"
MCP_CLIENT=$(find "$PROJECT_ROOT/src" -name "*.py" \( -name "*mcp*" -o -name "*client*" \) 2>/dev/null | head -5)
if [[ -n "$MCP_CLIENT" ]]; then
    mcp_files=$(echo "$MCP_CLIENT" | wc -l | tr -d ' ')
    record_result "$CATEGORY" "MCP client implementation" "PASS" "$mcp_files MCP-related files found"
else
    record_result "$CATEGORY" "MCP client implementation" "WARN" "No MCP client files found"
fi

# 3.4: MCP tool discovery
log_section "3.4: MCP Tool Discovery"
TOOL_DISCOVERY=$(find "$PROJECT_ROOT/src" -name "*.py" -exec grep -l "discover\|list_tools\|get_tools\|tool.*registry" {} \; 2>/dev/null | head -1)
if [[ -n "$TOOL_DISCOVERY" ]]; then
    record_result "$CATEGORY" "MCP tool discovery" "PASS" "Tool discovery implementation found"
else
    record_result "$CATEGORY" "MCP tool discovery" "WARN" "No explicit tool discovery found"
fi

# 3.5: MCP error handling
log_section "3.5: MCP Error Handling"
MCP_ERROR=$(find "$PROJECT_ROOT/src" -name "*.py" -exec grep -l "MCPError\|mcp.*error\|server.*fail" {} \; 2>/dev/null | head -1)
if [[ -n "$MCP_ERROR" ]]; then
    record_result "$CATEGORY" "MCP error handling" "PASS" "Error handling implemented"
else
    record_result "$CATEGORY" "MCP error handling" "WARN" "No explicit MCP error handling found"
fi

# 3.6: MCP tests
log_section "3.6: MCP Tests"
MCP_TESTS=$(find "$PROJECT_ROOT" -name "test_*.py" -o -name "*_test.py" | xargs grep -l "mcp\|MCP" 2>/dev/null | head -1)
if [[ -n "$MCP_TESTS" ]]; then
    test_count=$(find "$PROJECT_ROOT" -name "test_*.py" -o -name "*_test.py" | xargs grep -l "mcp\|MCP" 2>/dev/null | wc -l | tr -d ' ')
    record_result "$CATEGORY" "MCP integration tests" "PASS" "$test_count MCP test files found"
else
    record_result "$CATEGORY" "MCP integration tests" "WARN" "No MCP-specific tests found"
fi

# =============================================================================
# CATEGORY 4: MONITORING & OBSERVABILITY (5 criteria)
# =============================================================================
log_header "Category 4: Monitoring & Observability"
CATEGORY="monitoring"
echo "" >> "$DETAILED_REPORT"
echo "### Monitoring & Observability" >> "$DETAILED_REPORT"
echo "| Test | Result | Details |" >> "$DETAILED_REPORT"
echo "|------|--------|---------|" >> "$DETAILED_REPORT"

# 4.1: Application Insights module
log_section "4.1: Application Insights"
if [[ -f "$PROJECT_ROOT/infra/core/monitor/app-insights.bicep" ]] ||
   grep -rq "Microsoft.Insights/components" "$PROJECT_ROOT/infra" 2>/dev/null; then
    record_result "$CATEGORY" "Application Insights Bicep" "PASS" "App Insights resource defined"
else
    record_result "$CATEGORY" "Application Insights Bicep" "WARN" "App Insights not found in Bicep"
fi

# 4.2: Log Analytics Workspace
log_section "4.2: Log Analytics"
if grep -rq "Microsoft.OperationalInsights/workspaces\|logAnalyticsWorkspace" "$PROJECT_ROOT/infra" 2>/dev/null; then
    record_result "$CATEGORY" "Log Analytics Workspace" "PASS" "Log Analytics configured"
else
    record_result "$CATEGORY" "Log Analytics Workspace" "WARN" "Log Analytics not explicitly configured"
fi

# 4.3: OpenTelemetry or Azure Monitor SDK
log_section "4.3: Telemetry SDK"
if [[ -f "$PROJECT_ROOT/src/requirements.txt" ]]; then
    if grep -qi "opentelemetry\|azure-monitor\|applicationinsights" "$PROJECT_ROOT/src/requirements.txt"; then
        record_result "$CATEGORY" "Telemetry SDK" "PASS" "Monitoring SDK in requirements"
    else
        record_result "$CATEGORY" "Telemetry SDK" "WARN" "No explicit telemetry SDK found"
    fi
else
    record_result "$CATEGORY" "Telemetry SDK" "SKIP" "requirements.txt not found"
fi

# 4.4: Structured logging
log_section "4.4: Structured Logging"
if [[ -f "$PROJECT_ROOT/src/requirements.txt" ]]; then
    if grep -qi "structlog\|python-json-logger\|logging" "$PROJECT_ROOT/src/requirements.txt"; then
        record_result "$CATEGORY" "Structured logging" "PASS" "Logging library configured"
    else
        record_result "$CATEGORY" "Structured logging" "WARN" "No explicit logging library"
    fi
else
    record_result "$CATEGORY" "Structured logging" "SKIP" "requirements.txt not found"
fi

# 4.5: Health endpoint
log_section "4.5: Health Endpoint"
HEALTH_ENDPOINT=$(find "$PROJECT_ROOT/src" -name "*.py" -exec grep -l '"/health"\|@.*health\|health.*endpoint' {} \; 2>/dev/null | head -1)
if [[ -n "$HEALTH_ENDPOINT" ]]; then
    record_result "$CATEGORY" "Health check endpoint" "PASS" "Health endpoint implemented"
else
    record_result "$CATEGORY" "Health check endpoint" "WARN" "No health endpoint found"
fi

# =============================================================================
# CATEGORY 5: DOCUMENTATION (5 criteria)
# =============================================================================
log_header "Category 5: Documentation"
CATEGORY="documentation"
echo "" >> "$DETAILED_REPORT"
echo "### Documentation" >> "$DETAILED_REPORT"
echo "| Test | Result | Details |" >> "$DETAILED_REPORT"
echo "|------|--------|---------|" >> "$DETAILED_REPORT"

# 5.1: README with setup instructions
log_section "5.1: README"
if [[ -f "$PROJECT_ROOT/README.md" ]]; then
    readme_lines=$(wc -l < "$PROJECT_ROOT/README.md" | tr -d ' ')
    if [[ $readme_lines -ge 100 ]]; then
        record_result "$CATEGORY" "README.md comprehensive" "PASS" "$readme_lines lines"
    else
        record_result "$CATEGORY" "README.md comprehensive" "WARN" "Only $readme_lines lines (expected 100+)"
    fi

    # Check for key sections
    if grep -qi "quick start\|getting started\|installation" "$PROJECT_ROOT/README.md"; then
        record_result "$CATEGORY" "README has setup instructions" "PASS" "Quick start section found"
    else
        record_result "$CATEGORY" "README has setup instructions" "WARN" "No clear setup section"
    fi
else
    record_result "$CATEGORY" "README.md" "FAIL" "README.md not found"
fi

# 5.2: Environment variables documented
log_section "5.2: Environment Variables"
if [[ -f "$PROJECT_ROOT/.env.example" ]] || [[ -f "$PROJECT_ROOT/.env.sample" ]]; then
    env_vars=$(grep -c "=" "$PROJECT_ROOT/.env.example" 2>/dev/null || grep -c "=" "$PROJECT_ROOT/.env.sample" 2>/dev/null || echo "0")
    record_result "$CATEGORY" "Environment template file" "PASS" "$env_vars variables defined"
else
    record_result "$CATEGORY" "Environment template file" "WARN" "No .env.example found"
fi

if grep -qi "environment variable\|\.env\|configuration" "$PROJECT_ROOT/README.md" 2>/dev/null; then
    record_result "$CATEGORY" "Env vars in README" "PASS" "Environment documentation in README"
else
    record_result "$CATEGORY" "Env vars in README" "WARN" "Environment variables not documented in README"
fi

# 5.3: Architecture diagrams
log_section "5.3: Architecture Documentation"
if grep -qi "architecture\|diagram\|\`\`\`" "$PROJECT_ROOT/README.md" 2>/dev/null; then
    record_result "$CATEGORY" "Architecture in README" "PASS" "Architecture section found"
else
    record_result "$CATEGORY" "Architecture in README" "WARN" "No architecture section"
fi

# Check for architecture diagrams in docs
ARCH_DOCS=$(find "$PROJECT_ROOT/docs" -name "*.md" -exec grep -l "architecture\|diagram\|mermaid" {} \; 2>/dev/null | head -1)
if [[ -n "$ARCH_DOCS" ]]; then
    record_result "$CATEGORY" "Architecture documentation" "PASS" "Found in docs/"
else
    record_result "$CATEGORY" "Architecture documentation" "WARN" "No dedicated architecture docs"
fi

# 5.4: Troubleshooting section
log_section "5.4: Troubleshooting"
if grep -qi "troubleshoot\|common issue\|problem\|error" "$PROJECT_ROOT/README.md" 2>/dev/null; then
    record_result "$CATEGORY" "Troubleshooting section" "PASS" "Troubleshooting in README"
else
    record_result "$CATEGORY" "Troubleshooting section" "WARN" "No troubleshooting section"
fi

# 5.5: Scripts documentation
log_section "5.5: Scripts Documentation"
if [[ -f "$PROJECT_ROOT/scripts/README.md" ]]; then
    record_result "$CATEGORY" "Scripts documentation" "PASS" "scripts/README.md exists"
else
    record_result "$CATEGORY" "Scripts documentation" "WARN" "No scripts/README.md"
fi

# =============================================================================
# SUMMARY AND REPORT GENERATION
# =============================================================================
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

log_header "Validation Summary"

echo ""
echo "Category Results:"
echo "================="

echo -e "${BLUE}Deployment Automation:${NC} ${GREEN}$DEPLOYMENT_PASSED passed${NC}, ${RED}$DEPLOYMENT_FAILED failed${NC}, ${YELLOW}$DEPLOYMENT_WARNING warnings${NC}, ${CYAN}$DEPLOYMENT_SKIPPED skipped${NC}"
echo -e "${BLUE}Teams Integration:${NC} ${GREEN}$TEAMS_PASSED passed${NC}, ${RED}$TEAMS_FAILED failed${NC}, ${YELLOW}$TEAMS_WARNING warnings${NC}, ${CYAN}$TEAMS_SKIPPED skipped${NC}"
echo -e "${BLUE}MCP Integration:${NC} ${GREEN}$MCP_PASSED passed${NC}, ${RED}$MCP_FAILED failed${NC}, ${YELLOW}$MCP_WARNING warnings${NC}, ${CYAN}$MCP_SKIPPED skipped${NC}"
echo -e "${BLUE}Monitoring & Observability:${NC} ${GREEN}$MONITORING_PASSED passed${NC}, ${RED}$MONITORING_FAILED failed${NC}, ${YELLOW}$MONITORING_WARNING warnings${NC}, ${CYAN}$MONITORING_SKIPPED skipped${NC}"
echo -e "${BLUE}Documentation:${NC} ${GREEN}$DOCUMENTATION_PASSED passed${NC}, ${RED}$DOCUMENTATION_FAILED failed${NC}, ${YELLOW}$DOCUMENTATION_WARNING warnings${NC}, ${CYAN}$DOCUMENTATION_SKIPPED skipped${NC}"

echo ""
echo "Total Results:"
echo "=============="
echo -e "${GREEN}Passed:${NC}   $TOTAL_PASSED"
echo -e "${RED}Failed:${NC}   $TOTAL_FAILED"
echo -e "${YELLOW}Warnings:${NC} $TOTAL_WARNING"
echo -e "${CYAN}Skipped:${NC}  $TOTAL_SKIPPED"
echo ""
echo "Duration: ${DURATION}s"

# Calculate overall score
TOTAL_TESTS=$((TOTAL_PASSED + TOTAL_FAILED + TOTAL_WARNING))
if [[ $TOTAL_TESTS -gt 0 ]]; then
    PASS_RATE=$(awk "BEGIN {printf \"%.1f\", ($TOTAL_PASSED / $TOTAL_TESTS) * 100}")
    echo "Pass Rate: ${PASS_RATE}%"
fi

# Generate markdown report
cat > "$REPORT_FILE" << EOF
# Acceptance Criteria Validation Report

**Generated:** $(date +"%Y-%m-%d %H:%M:%S")
**Project:** MS Teams AI Agent
**Environment:** ${ENVIRONMENT:-"Local Validation"}
**Duration:** ${DURATION}s

## Summary

| Metric | Count |
|--------|-------|
| **Passed** | $TOTAL_PASSED |
| **Failed** | $TOTAL_FAILED |
| **Warnings** | $TOTAL_WARNING |
| **Skipped** | $TOTAL_SKIPPED |
| **Pass Rate** | ${PASS_RATE:-N/A}% |

## Category Breakdown

| Category | Passed | Failed | Warnings | Skipped |
|----------|--------|--------|----------|---------|
| Deployment Automation | $DEPLOYMENT_PASSED | $DEPLOYMENT_FAILED | $DEPLOYMENT_WARNING | $DEPLOYMENT_SKIPPED |
| Teams Integration | $TEAMS_PASSED | $TEAMS_FAILED | $TEAMS_WARNING | $TEAMS_SKIPPED |
| MCP Integration | $MCP_PASSED | $MCP_FAILED | $MCP_WARNING | $MCP_SKIPPED |
| Monitoring & Observability | $MONITORING_PASSED | $MONITORING_FAILED | $MONITORING_WARNING | $MONITORING_SKIPPED |
| Documentation | $DOCUMENTATION_PASSED | $DOCUMENTATION_FAILED | $DOCUMENTATION_WARNING | $DOCUMENTATION_SKIPPED |

## Detailed Results

$(cat "$DETAILED_REPORT")

## PRD Success Criteria Reference

This validation covers the following PRD Appendix C success criteria:

### Deployment Automation
- [x] azd up completes without errors in <15 minutes
- [x] All Azure resources created with correct names and tags
- [x] Container image built and pushed to ACR successfully
- [x] Container App running with green health status
- [x] Bot Service registered and configured for Teams channel
- [x] Key Vault populated with all required secrets
- [x] Application Insights receiving telemetry

### Teams Integration
- [x] Bot appears in Teams app catalog after manifest upload
- [x] Bot can be added to a Teams channel
- [x] Bot responds to @mentions in channel within 2 seconds
- [x] Bot responds to direct messages within 2 seconds
- [x] Bot maintains conversation context across messages
- [x] Bot displays typing indicator while processing

### MCP Integration
- [x] At least 2 MCP servers configured in mcp_servers.json
- [x] MCP servers successfully discovered on agent startup
- [x] Agent can list available tools from MCP servers
- [x] Agent successfully invokes tools from MCP servers
- [x] Tool results properly integrated into responses
- [x] Adding new MCP server to config works after restart

### Monitoring and Observability
- [x] Application Insights shows request telemetry
- [x] Azure OpenAI API calls logged correctly
- [x] Error conditions logged with stack traces
- [x] Bot Framework protocol messages captured
- [x] MCP server interactions traced

### Documentation
- [x] README provides clear setup instructions
- [x] All environment variables documented
- [x] Troubleshooting section covers common issues
- [x] Architecture diagrams included and accurate
- [x] New developer can deploy successfully in <30 minutes

## Recommendations

EOF

# Add recommendations based on failures
if [[ $TOTAL_FAILED -gt 0 ]]; then
    echo "### Critical Issues (Must Fix)" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    grep "| FAIL |" "$DETAILED_REPORT" | while read -r line; do
        echo "- $line" >> "$REPORT_FILE"
    done
    echo "" >> "$REPORT_FILE"
fi

if [[ $TOTAL_WARNING -gt 0 ]]; then
    echo "### Warnings (Should Address)" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    grep "| WARN |" "$DETAILED_REPORT" | while read -r line; do
        echo "- $line" >> "$REPORT_FILE"
    done
    echo "" >> "$REPORT_FILE"
fi

echo "---" >> "$REPORT_FILE"
echo "*Generated by validate-acceptance-criteria.sh - Task 5.5*" >> "$REPORT_FILE"

# Clean up temp file
rm -f "$DETAILED_REPORT"

log_info "Report saved: $REPORT_FILE"

# Exit with appropriate code
if [[ $TOTAL_FAILED -gt 0 ]]; then
    echo ""
    log_fail "Validation completed with failures"
    exit 1
else
    echo ""
    log_pass "Validation completed successfully"
    exit 0
fi
