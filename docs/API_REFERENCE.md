# MS Teams AI Agent - API Reference

This document describes the HTTP endpoints and webhook handlers exposed by the MS Teams AI Agent.

## Base URL

- **Local Development**: `http://localhost:8000`
- **Production**: `https://<container-app-name>.<region>.azurecontainerapps.io`

## Endpoints

### Health Check

Check application health status.

```
GET /health
```

#### Response

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-25T12:00:00.000Z",
  "components": {
    "openai": "connected",
    "mcp": "operational"
  }
}
```

#### Status Codes

| Code | Description |
|------|-------------|
| 200 | Application is healthy |
| 503 | Application is unhealthy |

---

### Bot Messages Webhook

Receives messages from Azure Bot Service (Bot Framework Protocol).

```
POST /api/messages
```

#### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | Bot Framework JWT token |
| `Content-Type` | Yes | `application/json` |

#### Request Body

Bot Framework Activity object:

```json
{
  "type": "message",
  "id": "activity-id",
  "timestamp": "2025-11-25T12:00:00.000Z",
  "localTimestamp": "2025-11-25T12:00:00.000Z",
  "channelId": "msteams",
  "from": {
    "id": "user-id",
    "name": "User Name",
    "aadObjectId": "azure-ad-object-id"
  },
  "conversation": {
    "id": "conversation-id",
    "conversationType": "personal",
    "tenantId": "tenant-id"
  },
  "recipient": {
    "id": "bot-id",
    "name": "Bot Name"
  },
  "text": "Hello, bot!",
  "textFormat": "plain",
  "locale": "en-US",
  "channelData": {
    "tenant": {
      "id": "tenant-id"
    }
  },
  "serviceUrl": "https://smba.trafficmanager.net/amer/"
}
```

#### Response

Empty response with status 200 (Bot Framework protocol).

```
HTTP/1.1 200 OK
```

#### Status Codes

| Code | Description |
|------|-------------|
| 200 | Activity processed successfully |
| 401 | Invalid or missing authorization token |
| 400 | Malformed activity payload |
| 500 | Internal server error |

---

### Root Endpoint

Basic application information.

```
GET /
```

#### Response

```json
{
  "name": "MS Teams AI Agent",
  "version": "1.0.0",
  "description": "AI agent for Microsoft Teams with MCP integration",
  "docs": "/docs",
  "health": "/health"
}
```

---

### OpenAPI Documentation

Interactive API documentation (Swagger UI).

```
GET /docs
```

Returns Swagger UI interface for testing endpoints.

---

### OpenAPI Schema

OpenAPI 3.0 specification.

```
GET /openapi.json
```

Returns JSON schema for API endpoints.

---

## Activity Types

The bot handles the following Bot Framework activity types:

### Message Activity

Standard text message from user.

```json
{
  "type": "message",
  "text": "User message content"
}
```

**Bot Response**: AI-generated response based on conversation context.

### Conversation Update

User added/removed from conversation.

```json
{
  "type": "conversationUpdate",
  "membersAdded": [{"id": "user-id", "name": "User"}],
  "membersRemoved": []
}
```

**Bot Response**: Welcome message when bot is added.

### Message Reaction

User reacted to a message.

```json
{
  "type": "messageReaction",
  "reactionsAdded": [{"type": "like"}]
}
```

**Bot Response**: None (logged only).

### Typing Activity

User is typing.

```json
{
  "type": "typing"
}
```

**Bot Response**: None.

---

## Teams-Specific Features

### @Mentions

When the bot is @mentioned in a channel:

```json
{
  "type": "message",
  "text": "<at>BotName</at> What is the weather?",
  "entities": [
    {
      "type": "mention",
      "mentioned": {
        "id": "bot-id",
        "name": "BotName"
      },
      "text": "<at>BotName</at>"
    }
  ]
}
```

The bot processes the message after removing the @mention.

### Adaptive Cards

The bot can send rich Adaptive Cards:

```json
{
  "type": "message",
  "attachments": [
    {
      "contentType": "application/vnd.microsoft.card.adaptive",
      "content": {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
          {
            "type": "TextBlock",
            "text": "Hello from the bot!",
            "weight": "bolder",
            "size": "medium"
          }
        ]
      }
    }
  ]
}
```

---

## Error Responses

### Standard Error Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": {
      "field": "Additional context"
    }
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or expired token |
| `INVALID_ACTIVITY` | 400 | Malformed activity payload |
| `RATE_LIMITED` | 429 | Too many requests |
| `OPENAI_ERROR` | 502 | Azure OpenAI service error |
| `MCP_ERROR` | 502 | MCP server error |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## Rate Limiting

The API implements rate limiting to prevent abuse:

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/messages` | 100 requests | per minute per user |
| `/health` | 1000 requests | per minute |

Rate limit headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1732536000
```

---

## Authentication

### Bot Framework Authentication

The `/api/messages` endpoint validates Bot Framework JWT tokens:

1. Token is extracted from `Authorization` header
2. Token signature is validated against Microsoft's public keys
3. Claims are verified (audience, issuer, expiry)
4. Activity is processed if valid

### Token Validation

```python
# Token structure
{
  "iss": "https://api.botframework.com",
  "aud": "<bot-app-id>",
  "exp": 1732536000,
  "nbf": 1732532400,
  "serviceurl": "https://smba.trafficmanager.net/amer/"
}
```

---

## WebSocket Support (Future)

Reserved for future WebSocket-based real-time communication:

```
WS /ws
```

Not currently implemented.

---

## SDK Examples

### Python (httpx)

```python
import httpx

async def check_health():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://your-bot.azurecontainerapps.io/health")
        return response.json()
```

### JavaScript (fetch)

```javascript
async function checkHealth() {
  const response = await fetch('https://your-bot.azurecontainerapps.io/health');
  return await response.json();
}
```

### cURL

```bash
# Health check
curl -X GET https://your-bot.azurecontainerapps.io/health

# With verbose output
curl -v -X GET https://your-bot.azurecontainerapps.io/health
```

---

## Testing Endpoints

### Local Testing

```bash
# Start server
uvicorn src.app.main:app --port 8000

# Test health
curl http://localhost:8000/health

# View docs
open http://localhost:8000/docs
```

### Production Testing

```bash
# Get Container App FQDN
FQDN=$(az containerapp show --name <app-name> --resource-group <rg-name> \
  --query "properties.configuration.ingress.fqdn" -o tsv)

# Test health
curl https://$FQDN/health
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-25 | Initial API release |

---
*Last Updated: 2025-11-25*
*Version: 1.0*
