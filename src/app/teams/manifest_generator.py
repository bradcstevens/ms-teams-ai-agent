"""
Teams App Manifest Generator
Generates Teams app manifest with environment-specific values
"""
import os
import json
from typing import Dict, Any


def generate_manifest() -> Dict[str, Any]:
    """
    Generate Teams app manifest with environment variables.

    Returns:
        Dictionary with complete manifest

    Environment Variables Required:
    - BOT_ID: Azure Bot Service app ID
    - BOT_ENDPOINT: Bot messaging endpoint URL
    - APP_VERSION: Application version (default: 1.0.0)
    - ENVIRONMENT: Deployment environment (dev/staging/prod)
    """
    bot_id = os.getenv('BOT_ID', '{{BOT_ID}}')
    bot_endpoint = os.getenv('BOT_ENDPOINT', '{{BOT_ENDPOINT}}')
    app_version = os.getenv('APP_VERSION', '1.0.0')
    environment = os.getenv('ENVIRONMENT', 'dev')

    manifest = {
        "$schema": "https://developer.microsoft.com/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
        "manifestVersion": "1.16",
        "version": app_version,
        "id": bot_id,
        "packageName": f"com.microsoft.teams.aiagent.{environment}",
        "developer": {
            "name": "AI Agent Development Team",
            "websiteUrl": "https://example.com",
            "privacyUrl": "https://example.com/privacy",
            "termsOfUseUrl": "https://example.com/terms"
        },
        "name": {
            "short": "AI Agent",
            "full": f"AI Agent for Teams ({environment})"
        },
        "description": {
            "short": "AI-powered assistant for Microsoft Teams",
            "full": "An intelligent AI agent powered by Azure OpenAI that helps users with various tasks in Microsoft Teams. Built using the Microsoft Agent Framework."
        },
        "icons": {
            "color": "color.png",
            "outline": "outline.png"
        },
        "accentColor": "#0078D4",
        "bots": [
            {
                "botId": bot_id,
                "scopes": [
                    "personal",
                    "team",
                    "groupchat"
                ],
                "supportsFiles": False,
                "isNotificationOnly": False,
                "commandLists": [
                    {
                        "scopes": [
                            "personal"
                        ],
                        "commands": [
                            {
                                "title": "Help",
                                "description": "Get help and learn what I can do"
                            },
                            {
                                "title": "Status",
                                "description": "Check my current status and capabilities"
                            }
                        ]
                    },
                    {
                        "scopes": [
                            "team",
                            "groupchat"
                        ],
                        "commands": [
                            {
                                "title": "Help",
                                "description": "Get help and learn what I can do"
                            }
                        ]
                    }
                ]
            }
        ],
        "permissions": [
            "identity",
            "messageTeamMembers"
        ],
        "validDomains": [
            "*.azurecontainerapps.io",
            "*.azure.com",
            "api.botframework.com"
        ],
        "webApplicationInfo": {
            "id": bot_id,
            "resource": f"api://{bot_endpoint.replace('https://', '')}"
        }
    }

    return manifest


def save_manifest(manifest: Dict[str, Any], output_path: str) -> None:
    """
    Save manifest to file.

    Args:
        manifest: Manifest dictionary
        output_path: Output file path
    """
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)


def substitute_placeholders(manifest_template: str, values: Dict[str, str]) -> str:
    """
    Substitute placeholders in manifest template.

    Args:
        manifest_template: Manifest JSON string with placeholders
        values: Dictionary of placeholder values

    Returns:
        Manifest string with substituted values
    """
    for key, value in values.items():
        placeholder = f"{{{{{key}}}}}"
        manifest_template = manifest_template.replace(placeholder, value)

    return manifest_template
