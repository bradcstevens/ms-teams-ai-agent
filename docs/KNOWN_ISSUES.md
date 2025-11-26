# MS Teams AI Agent - Known Issues & Technical Debt

This document tracks known issues, limitations, and technical debt in the MS Teams AI Agent project.

## Known Issues

### Critical

No critical issues identified at this time.

### High Priority

#### KI-001: Bicep Name Length Warnings
**Status:** Open
**Component:** Infrastructure (Bicep)
**Description:** Bicep templates generate warnings about potential resource name length violations (BCP335).

**Details:**
```
Warning BCP335: The provided value can have a length as large as 82
and may be too long to assign to a target with a configured maximum length of 63.
```

**Impact:** Resource creation may fail if environment names are too long.

**Workaround:** Use short environment names (< 10 characters).

**Resolution:** Add explicit name length validation in Bicep templates.

---

#### KI-002: MCP Server Configuration Hot Reload
**Status:** Open
**Component:** MCP Integration
**Description:** Changes to `mcp_servers.json` require container restart to take effect.

**Impact:** No dynamic MCP server reconfiguration.

**Workaround:** Restart container app after configuration changes.

**Resolution:** Implement configuration file watcher with automatic reconnection.

---

### Medium Priority

#### KI-003: Dockerfile Not Using Multi-Stage Build
**Status:** Open
**Component:** Container
**Description:** Dockerfile uses single-stage build, resulting in larger image size.

**Impact:** Larger container image size, slower deployment.

**Workaround:** None required - works correctly.

**Resolution:** Implement multi-stage build to reduce image size.

---

#### KI-004: No Explicit Telemetry SDK in Requirements
**Status:** Open
**Component:** Monitoring
**Description:** Application Insights integration relies on environment, no explicit SDK dependency.

**Impact:** May miss some telemetry in certain configurations.

**Workaround:** Azure Container Apps automatically injects Application Insights agent.

**Resolution:** Add `azure-monitor-opentelemetry` to requirements.txt for explicit control.

---

#### KI-005: In-Memory Conversation State
**Status:** Acknowledged
**Component:** Bot Framework
**Description:** Conversation state is stored in-memory, lost on container restart.

**Impact:** Multi-turn conversations lost on deployment or scaling events.

**Workaround:** Users may need to restart conversation after deployments.

**Resolution:** Implement Redis or Cosmos DB state store.

---

### Low Priority

#### KI-006: Missing .env.example in Original Template
**Status:** Resolved (2025-11-25)
**Component:** Documentation
**Description:** No environment template file existed for developer onboarding.

**Resolution:** Created `.env.example` with all required variables.

---

#### KI-007: Unnecessary dependsOn in Bicep
**Status:** Open
**Component:** Infrastructure
**Description:** Bicep linter warns about unnecessary `dependsOn` entries.

**Impact:** No functional impact, cleaner code possible.

**Resolution:** Remove redundant `dependsOn` entries where implicit dependencies exist.

---

## Technical Debt

### Architecture

| ID | Description | Priority | Effort |
|----|-------------|----------|--------|
| TD-001 | Implement proper dependency injection container | Medium | High |
| TD-002 | Extract common utilities to shared package | Low | Medium |
| TD-003 | Add request/response caching layer | Medium | Medium |
| TD-004 | Implement proper message queue for async processing | High | High |

### Code Quality

| ID | Description | Priority | Effort |
|----|-------------|----------|--------|
| TD-005 | Increase test coverage to 80%+ | High | Medium |
| TD-006 | Add integration tests for Azure services | Medium | High |
| TD-007 | Implement proper error codes and messages | Medium | Low |
| TD-008 | Add request validation middleware | Medium | Low |

### Infrastructure

| ID | Description | Priority | Effort |
|----|-------------|----------|--------|
| TD-009 | Implement blue-green deployment strategy | Medium | Medium |
| TD-010 | Add proper health check with dependency status | High | Low |
| TD-011 | Implement proper secret rotation | High | Medium |
| TD-012 | Add proper network segmentation | Medium | High |

### Security

| ID | Description | Priority | Effort |
|----|-------------|----------|--------|
| TD-013 | Implement rate limiting per user | High | Medium |
| TD-014 | Add request signing validation | Medium | Medium |
| TD-015 | Implement proper audit logging | High | Medium |
| TD-016 | Add security headers middleware | Medium | Low |

### Documentation

| ID | Description | Priority | Effort |
|----|-------------|----------|--------|
| TD-017 | Add inline code documentation | Medium | Medium |
| TD-018 | Create video walkthrough for deployment | Low | Medium |
| TD-019 | Add troubleshooting decision tree | Medium | Low |
| TD-020 | Create architecture decision records (ADRs) | Low | Medium |

---

## Resolution Tracking

### Recently Resolved

| Date | Issue | Resolution |
|------|-------|------------|
| 2025-11-25 | Bicep compilation error (BCP053) | Fixed output reference from `containerAppsEnvironmentId` to `id` |
| 2025-11-25 | Missing .env.example | Created comprehensive environment template |
| 2025-11-25 | Missing architecture documentation | Created ARCHITECTURE.md |
| 2025-11-25 | Missing operations guide | Created OPERATIONS.md |
| 2025-11-25 | Missing developer guide | Created DEVELOPER_GUIDE.md |
| 2025-11-25 | Missing API documentation | Created API_REFERENCE.md |

### Scheduled for Next Release

| Issue | Target Date | Owner |
|-------|-------------|-------|
| TD-005 | TBD | Development Team |
| TD-010 | TBD | Development Team |
| KI-002 | TBD | Development Team |

---

## Reporting New Issues

When reporting new issues, include:

1. **Description**: Clear description of the issue
2. **Component**: Which component is affected
3. **Steps to Reproduce**: How to trigger the issue
4. **Expected Behavior**: What should happen
5. **Actual Behavior**: What actually happens
6. **Impact**: Severity and user impact
7. **Workaround**: Any temporary fixes

---

## Issue Categories

| Priority | Definition |
|----------|------------|
| **Critical** | System unusable, no workaround |
| **High** | Major functionality impacted |
| **Medium** | Functionality impaired but usable |
| **Low** | Minor issues, cosmetic |

| Technical Debt Priority | Definition |
|-------------------------|------------|
| **High** | Blocking future development |
| **Medium** | Should address soon |
| **Low** | Nice to have |

---
*Last Updated: 2025-11-25*
*Version: 1.0*
