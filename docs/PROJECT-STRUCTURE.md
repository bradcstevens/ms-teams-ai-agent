# MS Teams AI Agent - Project Structure

**Last Updated:** 2025-11-24
**Status:** Phase 5 - Validation & Documentation Complete

---

## Directory Structure

```
ms-teams-ai-agent/
├── .azure/                          # Azure Developer CLI environments
├── .claude/                         # Claude Code configuration (gitignored)
│   ├── commands/                    # Custom slash commands
│   ├── docs/                        # Claude-specific documentation
│   └── hooks/                       # Git hooks for development
├── .claude-collective/              # Claude Code sub-agent collective (gitignored)
│   ├── agents.md                    # Agent definitions
│   ├── CLAUDE.md                    # Collective behavioral rules
│   ├── DECISION.md                  # Routing decision engine
│   ├── hooks.md                     # Hook integration docs
│   ├── quality.md                   # Quality assurance standards
│   └── research.md                  # Research framework
├── .github/                         # GitHub configuration
│   ├── copilot-instructions.md      # GitHub Copilot instructions
│   └── workflows/                   # CI/CD workflows (future)
├── .taskmaster/                     # TaskMaster AI configuration (gitignored)
│   ├── config.json                  # AI model configuration
│   ├── docs/                        # TaskMaster documentation
│   └── tasks/                       # Task database and tracking
├── docs/                            # Project documentation
│   ├── PROJECT-STRUCTURE.md         # Complete project structure (this file)
│   ├── MCP_INTEGRATION.md           # MCP integration guide
│   ├── TEAMS_DEPLOYMENT.md          # Teams deployment documentation
│   └── TEAMS_TESTING.md             # Teams testing procedures
├── infra/                           # Azure infrastructure as code
│   ├── core/                        # Reusable Bicep modules
│   │   ├── host/                    # Container Apps, Registry
│   │   ├── monitor/                 # Application Insights, Log Analytics
│   │   └── security/                # Key Vault
│   ├── ai/                          # AI service modules
│   │   └── openai.bicep             # Azure OpenAI Service
│   ├── bot/                         # Bot service modules
│   │   └── bot-service.bicep        # Azure Bot Service
│   └── main.bicep                   # Main infrastructure orchestration
├── reports/                         # Test and validation reports (gitignored)
│   └── test-results/                # Test execution outputs
│       ├── htmlcov/                 # HTML coverage report
│       ├── coverage.json            # Coverage data
│       ├── test-results.log         # pytest output
│       ├── mypy-results.log         # Type checking results
│       └── ruff-results.log         # Linting results
├── scripts/                         # Automation scripts
│   ├── create-bot-registration.sh   # Bot registration automation
│   ├── create-teams-package.sh      # Teams package creation
│   ├── deploy-teams-bot.sh          # End-to-end deployment orchestrator
│   ├── generate-teams-manifest.sh   # Manifest generation
│   ├── test-teams-deployment.sh     # Deployment validation tests
│   └── validate-full-deployment.sh  # Comprehensive deployment validator
├── src/                             # Application source code
│   ├── app/                         # Main application package
│   │   ├── agent/                   # AI agent implementation
│   │   │   └── ai_agent.py          # TeamsAIAgent with Azure OpenAI
│   │   ├── bot/                     # Teams bot implementation
│   │   │   ├── auth.py              # JWT authentication
│   │   │   ├── conversation_state.py # State management
│   │   │   ├── security.py          # Security headers and CORS
│   │   │   └── teams_bot.py         # TeamsBot handler
│   │   ├── config/                  # Configuration management
│   │   │   └── settings.py          # Pydantic settings
│   │   ├── mcp/                     # MCP integration
│   │   │   ├── client.py            # MCP client implementations
│   │   │   ├── config.py            # MCP configuration models
│   │   │   ├── manager.py           # Connection manager
│   │   │   ├── circuit_breaker.py   # Resilience patterns
│   │   │   ├── servers/             # MCP server helpers
│   │   │   └── ...                  # Other MCP modules
│   │   ├── teams/                   # Teams integration
│   │   │   ├── manifest_generator.py # Manifest generation
│   │   │   └── manifest_validator.py # Manifest validation
│   │   ├── telemetry/               # Observability
│   │   │   └── logger.py            # Application Insights logging
│   │   ├── utils/                   # Utility functions
│   │   │   └── teams_helper.py      # Teams helper functions
│   │   └── main.py                  # FastAPI application entry point
│   ├── tests/                       # Unit tests
│   │   ├── test_bot_authentication.py
│   │   ├── test_circuit_breaker.py
│   │   ├── test_mcp_*.py            # MCP tests (7 files)
│   │   ├── test_server_helpers.py
│   │   └── test_teams_manifest.py
│   ├── Dockerfile                   # Container image definition
│   └── requirements.txt             # Python dependencies
├── teams/                           # Teams app manifest
│   ├── manifest.json                # Teams app manifest
│   ├── color.png                    # App icon (color)
│   └── outline.png                  # App icon (outline)
├── tests/                           # Tests and test documentation
│   ├── docs/                        # Test documentation
│   │   ├── README.md                # Test docs overview
│   │   ├── validation/              # Deployment validation docs
│   │   │   ├── DEPLOYMENT-VALIDATION-REPORT.md
│   │   │   ├── DEPLOYMENT-VALIDATION-INSTRUCTIONS.md
│   │   │   └── VALIDATION-README.md
│   │   ├── reports/                 # Test results documentation
│   │   │   └── TEST-RESULTS-REPORT.md
│   │   └── ORGANIZATION-SUMMARY.md  # File organization summary
│   ├── integration/                 # Integration tests
│   │   └── test_teams_deployment.py # Deployment integration tests
│   └── test_*.py                    # Additional integration tests
├── .env.template                    # Environment variables template
├── .gitignore                       # Git ignore patterns
├── azure.yaml                       # Azure Developer CLI configuration
├── CLAUDE.md                        # Claude Code instructions (gitignored)
├── pytest.ini                       # pytest configuration
├── README.md                        # Project README
└── requirements.txt                 # Root Python dependencies
```

---

## Key Directories

### `/docs` - Project Documentation
General project documentation for integration guides and deployment procedures.

**Contents:**
- **PROJECT-STRUCTURE.md** - Complete project structure overview (this file)
- **MCP_INTEGRATION.md** - MCP server integration guide
- **TEAMS_DEPLOYMENT.md** - Teams deployment procedures
- **TEAMS_TESTING.md** - Teams app testing guide

**Audience:** All team members, new developers, architects

**Note:** Test-specific documentation moved to `/tests/docs/`

---

### `/infra` - Infrastructure as Code
Bicep modules for Azure infrastructure deployment.

**Key Files:**
- **main.bicep** - Main orchestration template
- **core/** - Reusable infrastructure modules
  - Container Apps environment and apps
  - Container Registry
  - Key Vault for secrets
  - Log Analytics and Application Insights
- **ai/openai.bicep** - Azure OpenAI Service (GPT-4o)
- **bot/bot-service.bicep** - Azure Bot Service

**Deployment:** Via `azd up` command

---

### `/scripts` - Automation Scripts
Bash scripts for deployment automation and validation.

**Key Scripts:**
- **validate-full-deployment.sh** - Complete deployment validation (executable)
- **deploy-teams-bot.sh** - End-to-end deployment orchestrator
- **test-teams-deployment.sh** - Deployment testing and validation
- **create-bot-registration.sh** - Automated bot registration
- **generate-teams-manifest.sh** - Teams manifest generation
- **create-teams-package.sh** - Teams app package creation

**Usage:** See docs/validation/DEPLOYMENT-VALIDATION-INSTRUCTIONS.md

---

### `/src/app` - Application Source
Python FastAPI application with Teams bot and MCP integration.

**Architecture:**
- **main.py** - FastAPI application, health endpoints, bot endpoint
- **bot/** - Teams bot implementation (TeamsBot, authentication, state)
- **agent/** - AI agent with Azure OpenAI integration
- **mcp/** - MCP server integration (client, manager, config)
- **teams/** - Teams manifest generation and validation
- **telemetry/** - Application Insights logging
- **config/** - Pydantic settings management

**Testing:** 136 unit tests, 98.5% pass rate
**Coverage:** 49% (MCP: 80-97%, Core: needs improvement)

---

### `/src/tests` - Unit Tests
Comprehensive unit test suite for all application components.

**Test Files:**
- **test_bot_authentication.py** - JWT auth, security headers, CORS
- **test_circuit_breaker.py** - Circuit breaker resilience
- **test_mcp_*.py** - MCP integration (7 test files, 80+ tests)
- **test_server_helpers.py** - MCP server helper utilities
- **test_teams_manifest.py** - Teams manifest validation

**Execution:** `pytest src/tests/`

---

### `/tests` - Tests and Test Documentation
Comprehensive test suite and testing documentation.

**Structure:**
```
tests/
├── docs/                           # Test documentation
│   ├── README.md                   # Test docs overview
│   ├── validation/                 # Deployment validation docs
│   ├── reports/                    # Test results reports
│   └── ORGANIZATION-SUMMARY.md
├── integration/                    # Integration tests
│   └── test_teams_deployment.py
└── test_*.py                       # Additional integration tests
```

**Test Documentation:**
- **Deployment Validation:** Complete validation procedures and checklists
- **Test Results:** Comprehensive test suite analysis and quality metrics
- **Organization:** File structure and maintenance guidelines

**Test Execution:**
- Unit tests: `pytest src/tests/` (136 tests)
- Integration tests: `pytest tests/integration/` (27 tests)
- All tests: `pytest -v`

---

### `/reports` - Test Reports (Gitignored)
Generated test outputs and coverage reports.

**Contents:**
- **test-results/** - Test execution outputs
  - htmlcov/ - HTML coverage report
  - coverage.json - Coverage data
  - test-results.log - pytest output
  - mypy-results.log - Type checking
  - ruff-results.log - Linting

**Regeneration:** Run test suite to recreate

---

### `/teams` - Teams App Manifest
Microsoft Teams app package files.

**Contents:**
- **manifest.json** - Teams app manifest with bot configuration
- **color.png** - App icon (192x192, color)
- **outline.png** - App icon (32x32, outline)

**Package Creation:** Use `scripts/create-teams-package.sh`

---

## Configuration Files

### Root Level

| File | Purpose |
|------|---------|
| `azure.yaml` | Azure Developer CLI configuration for deployment |
| `pytest.ini` | pytest test configuration |
| `.env.template` | Environment variables template |
| `.gitignore` | Git ignore patterns (includes reports/, test outputs) |
| `requirements.txt` | Python dependencies |
| `CLAUDE.md` | Claude Code instructions (gitignored) |
| `README.md` | Project overview and quick start |

### Application Level

| File | Purpose |
|------|---------|
| `src/Dockerfile` | Container image definition |
| `src/requirements.txt` | Application-specific Python dependencies |

---

## Hidden Directories (Gitignored)

### `.azure/`
Azure Developer CLI environments and secrets.
- **Do not commit** - Contains sensitive environment data

### `.claude/` & `.claude-collective/`
Claude Code configuration and sub-agent collective.
- **Do not commit** - Development tooling configuration

### `.taskmaster/`
TaskMaster AI configuration and task database.
- **Do not commit** - Project management data

### `.venv/`
Python virtual environment.
- **Do not commit** - Local Python environment

---

## File Naming Conventions

### Documentation
- **UPPERCASE-WITH-DASHES.md** - Major documentation files
- **lowercase-with-dashes.md** - Supporting documentation

### Scripts
- **kebab-case.sh** - Bash scripts
- All scripts in `/scripts` are executable

### Source Code
- **snake_case.py** - Python modules
- **PascalCase** for class names
- **snake_case** for functions and variables

### Tests
- **test_*.py** - Test files (pytest convention)
- Mirror source structure when possible

---

## Quick Reference

### Key Entry Points

| Purpose | File/Command |
|---------|-------------|
| **Application Entry** | `src/app/main.py` |
| **Deployment** | `azd up` or `scripts/deploy-teams-bot.sh` |
| **Validation** | `scripts/validate-full-deployment.sh` |
| **Testing** | `pytest src/tests/` |
| **Documentation** | `docs/` directory |

### Important Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| **Project Overview** | `README.md` | Quick start and overview |
| **Deployment Guide** | `docs/validation/DEPLOYMENT-VALIDATION-INSTRUCTIONS.md` | Deploy and validate |
| **Test Results** | `docs/validation/TEST-RESULTS-REPORT.md` | Quality assessment |
| **MCP Integration** | `docs/MCP_INTEGRATION.md` | MCP server setup |
| **Teams Deployment** | `docs/TEAMS_DEPLOYMENT.md` | Teams app deployment |

---

## Maintenance Notes

### Adding New Features
1. Create feature branch
2. Add unit tests in `src/tests/`
3. Implement in `src/app/`
4. Update relevant documentation in `docs/`
5. Run full test suite
6. Update this structure doc if needed

### Adding New Documentation
1. Place in appropriate `docs/` subdirectory
2. Update section README if applicable
3. Link from main `README.md` if major doc
4. Update this structure doc

### Adding New Scripts
1. Place in `scripts/` directory
2. Make executable: `chmod +x scripts/your-script.sh`
3. Add usage documentation
4. Update this structure doc

---

## Development Workflow

### Local Development
```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r src/requirements.txt

# Testing
pytest src/tests/
pytest tests/integration/

# Type checking
mypy src/app --strict

# Linting
ruff check src/app
```

### Deployment
```bash
# Full deployment
azd up --environment dev --location eastus

# Validation
./scripts/validate-full-deployment.sh --environment dev

# Cleanup
azd down --purge --force
```

---

## Resources

- **Azure DevOps:** (Configure if using)
- **GitHub Repository:** (Configure if using)
- **Documentation Portal:** `docs/` directory
- **Issue Tracking:** TaskMaster (`.taskmaster/`)

---

**Project Structure Maintained By:** Development Team
**Last Major Update:** 2025-11-24 (Phase 5 Completion)
**Next Review:** After Phase 6 or major feature additions
