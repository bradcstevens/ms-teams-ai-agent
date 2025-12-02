# MS Teams AI Agent - Architecture Documentation

## System Overview

The MS Teams AI Agent is a cloud-native AI assistant that integrates with Microsoft Teams, leveraging Azure OpenAI for intelligent responses and the Model Context Protocol (MCP) for extensible tool capabilities.

```mermaid
flowchart TB
    subgraph Teams["Microsoft Teams (User UI)"]
        User[User]
    end

    subgraph BotService["Azure Bot Service (Message Router)"]
        Router[Message Router]
    end

    subgraph ACA["Azure Container Apps"]
        subgraph Container["Python Application Container"]
            FastAPI[FastAPI Web Framework]
            TeamsBot[Teams Bot Handler]
            Agent[AI Agent Orchestrator]
            MCP[MCP Manager<br/>Tool Bridge]
            OpenAI[Azure OpenAI Client]
        end
    end

    subgraph MCPServers["MCP Servers"]
        FS[Filesystem<br/>MCP Server]
        WS[Web Search<br/>MCP Server]
        Custom[Custom<br/>MCP Server]
    end

    User -->|Bot Framework Protocol| Router
    Router -->|HTTPS Webhook| FastAPI
    FastAPI --> TeamsBot
    TeamsBot --> Agent
    Agent --> MCP
    Agent --> OpenAI
    MCP --> FS
    MCP --> WS
    MCP --> Custom
```

## Component Architecture

### 1. Web Layer (`src/app/`)

**FastAPI Application** - Main entry point handling HTTP requests

```text
src/app/
├── main.py              # FastAPI application entrypoint
├── __init__.py          # Package initialization
└── config/
    ├── __init__.py
    └── settings.py      # Pydantic settings management
```

Key responsibilities:

- HTTP request routing
- Health check endpoints (`/health`)
- Bot Framework webhook (`/api/messages`)
- CORS and security middleware

### 2. Bot Layer (`src/app/bot/`)

**Teams Bot Handler** - Processes Bot Framework activities

```text
src/app/bot/
├── __init__.py
├── auth.py              # Bot authentication handling
├── security.py          # Security utilities and validation
├── conversation_state.py # Conversation state management
└── teams_bot.py         # Main bot activity handler
```

Key responsibilities:

- Bot Framework authentication
- Activity type routing (message, typing, etc.)
- Conversation state persistence
- Teams-specific message formatting

### 3. Agent Layer (`src/app/agent/`)

**AI Agent Orchestrator** - Coordinates AI responses

```text
src/app/agent/
├── __init__.py
└── ai_agent.py          # Agent logic and orchestration
```

Key responsibilities:

- Azure OpenAI integration
- Prompt engineering
- Tool call routing to MCP
- Response formatting

### 4. MCP Layer (`src/app/mcp/`)

**Model Context Protocol Integration** - Extensible tool framework

```text
src/app/mcp/
├── __init__.py
├── config.py            # MCP configuration management
├── discovery.py         # Server discovery mechanisms
├── registry.py          # Tool registry
├── tool_schema.py       # Tool schema definitions
├── client.py            # MCP client implementation
├── bridge.py            # Agent-MCP bridge layer
├── factory.py           # Server factory pattern
├── circuit_breaker.py   # Fault tolerance
├── loader.py            # Dynamic server loading
├── exceptions.py        # Custom exception types
├── manager.py           # Server lifecycle management
└── servers/
    ├── __init__.py
    ├── filesystem.py    # Filesystem server adapter
    └── web_search.py    # Web search server adapter
```

Key responsibilities:

- MCP server lifecycle management
- Tool discovery and registration
- Request/response bridging
- Circuit breaker pattern for fault tolerance
- Dynamic server configuration

### 5. Teams Layer (`src/app/teams/`)

**Teams Integration Utilities**

```text
src/app/teams/
├── __init__.py
├── manifest_generator.py  # Teams manifest generation
└── manifest_validator.py  # Manifest validation
```

Key responsibilities:

- Teams app manifest generation
- Manifest schema validation
- Bot capability configuration

### 6. Utilities (`src/app/utils/`)

**Shared Utilities**

```text
src/app/utils/
├── __init__.py
└── teams_helper.py      # Teams-specific helpers
```

## Infrastructure Architecture

### Azure Resources (Bicep)

```text
infra/
├── main.bicep           # Main orchestration template
├── main.parameters.json # Parameter file
├── abbreviations.json   # Resource naming conventions
├── ai/
│   └── openai.bicep     # Azure OpenAI configuration
├── bot/
│   └── bot-service.bicep # Bot Service setup
├── core/
│   └── host/
│       ├── container-app.bicep
│       ├── container-registry.bicep
│       └── container-apps-environment.bicep
└── security/
    └── key-vault.bicep   # Secret management
```

### Resource Topology

```mermaid
flowchart TB
    subgraph RG["Resource Group"]
        subgraph CAE["Container Apps Environment"]
            CA[Container App<br/>Python Agent]
        end
        CR[Container Registry]
        subgraph AOAI["Azure OpenAI Service"]
            GPT[GPT-5 Deployment]
        end
        subgraph Bot["Bot Service"]
            Teams[Teams Channel]
        end
        subgraph KV["Key Vault"]
            Creds[Bot Credentials]
        end
        AI[Application Insights]
        LA[Log Analytics Workspace]
    end
```

## Data Flow

### Message Processing Flow

```mermaid
sequenceDiagram
    participant U as User
    participant T as Teams
    participant B as Bot Service
    participant F as FastAPI
    participant H as Bot Handler
    participant A as AI Agent
    participant O as Azure OpenAI
    participant M as MCP Manager

    U->>T: 1. Send message
    T->>B: 2. Bot Framework Protocol
    B->>F: 3. HTTPS Webhook /api/messages
    F->>H: 4. Route to Bot Handler
    H->>H: 5. Validate auth, extract message
    H->>A: 6. Pass message context
    A->>O: 7. Query with conversation history
    O-->>A: Response

    alt Tool call needed
        A->>M: 8a. Route to MCP
        M->>M: 8b. Execute tool
        M-->>A: 8c. Return result
    end

    A-->>H: 9. Format response
    H-->>B: Send via Bot Framework
    B-->>T: Deliver message
    T-->>U: 10. Display response
```

### MCP Tool Flow

```mermaid
sequenceDiagram
    participant A as AI Agent
    participant B as MCP Bridge
    participant R as Registry
    participant CB as Circuit Breaker
    participant C as MCP Client
    participant S as MCP Server

    A->>B: 1. Tool request
    B->>R: 2. Lookup tool → server mapping
    R-->>B: Server info
    B->>CB: 3. Check server health
    CB-->>B: Health OK
    B->>C: 4. Send request
    C->>S: 5. Execute tool
    S-->>C: 6. Return result
    C-->>B: Result
    B->>B: 7. Format for Agent
    B-->>A: 8. Formatted response
```

## Security Architecture

### Authentication Layers

1. **Bot Framework Auth**: Microsoft App ID/Password validation
2. **Azure AD**: Managed identity for Azure resources
3. **Key Vault**: Secure secret storage
4. **HTTPS**: TLS encryption for all traffic

### Secret Management

```mermaid
flowchart LR
    subgraph KV["Key Vault"]
        S1[BOT_APP_ID]
        S2[BOT_APP_PASSWORD]
        S3[AZURE_OPENAI_API_KEY<br/>if not using managed identity]
        S4[MCP_SERVER_CREDENTIALS<br/>optional]
    end
```

### Network Security

- Container App ingress limited to HTTPS
- Bot Service validates token signatures
- MCP servers run in isolated processes

## Scalability Design

### Container Apps Auto-scaling

```yaml
# Scaling configuration
minReplicas: 1
maxReplicas: 10
rules:
  - name: http-scaling
    http:
      metadata:
        concurrentRequests: 50
```

### Performance Targets

| Metric | Target |
|--------|--------|
| Bot response time | < 2 seconds |
| Health endpoint | < 100ms |
| Concurrent users | 50+ per replica |
| Deployment time | < 15 minutes |

## Monitoring & Observability

### Telemetry Collection

```mermaid
flowchart TB
    subgraph AI["Application Insights"]
        RT[Request traces]
        DC[Dependency calls<br/>OpenAI, MCP]
        CM[Custom metrics]
        EL[Exception logging]
        PC[Performance counters]
    end

    subgraph LA["Log Analytics"]
        CL[Container logs]
        IL[Infrastructure logs]
        SL[Security logs]
    end
```

### Key Metrics

- Request duration percentiles (p50, p95, p99)
- Error rates by endpoint
- OpenAI token usage
- MCP server health status
- Container resource utilization

## Deployment Architecture

### azd Workflow

```mermaid
flowchart TB
    AZD[azd up] --> Pre[prepackage hook<br/>validate-config.sh]
    Pre --> Prov[provision<br/>Bicep deployment]
    Prov --> Resources[Creates all Azure resources]
    Prov --> Post[postprovision hook<br/>setup-bot.sh]
    Post --> BotReg[Registers bot with Bot Service]
    Post --> Deploy[deploy<br/>Container build & push]
    Deploy --> Image[Builds image, deploys to Container Apps]
    Deploy --> PostDeploy[postdeploy hook<br/>generate-teams-manifest.sh]
    PostDeploy --> Package[Creates Teams app package]
```

### Environment Promotion

```mermaid
flowchart LR
    Dev[Development] --> Staging[Staging] --> Prod[Production]

    subgraph AZD["azd environment management"]
        Dev
        Staging
        Prod
    end
```

## Extension Points

### Adding New MCP Servers

1. Create server adapter in `src/app/mcp/servers/`
2. Register in `mcp_servers.json`
3. Restart container (auto-discovery)

### Adding New Bot Capabilities

1. Extend `TeamsBot` class in `src/app/bot/teams_bot.py`
2. Add activity handlers for new message types
3. Update Teams manifest with new capabilities

### Adding New AI Models

1. Configure deployment in `infra/ai/openai.bicep`
2. Update agent configuration
3. Redeploy with `azd up`

## Technology Stack

| Component | Technology |
|-----------|------------|
| Runtime | Python 3.11+ |
| Web Framework | FastAPI |
| Bot SDK | botbuilder-python |
| AI | Azure OpenAI (GPT-5) |
| Hosting | Azure Container Apps |
| IaC | Bicep |
| Deployment | Azure Developer CLI (azd) |
| Monitoring | Application Insights |
| Secrets | Azure Key Vault |

---

*Last Updated: 2025-12-01*
*Version: 1.1*
