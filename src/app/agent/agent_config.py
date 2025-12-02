"""Agent configuration models for .agent.md files.

This module defines Pydantic models for custom agent configurations
following VS Code/GitHub Copilot specification.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from enum import Enum


class AgentTarget(str, Enum):
    """Agent target environments.

    Defines where the agent can be deployed or used.
    """
    VSCODE = "vscode"
    GITHUB_COPILOT = "github-copilot"
    TEAMS = "teams"  # Custom target for Microsoft Teams integration


class AgentHandoff(BaseModel):
    """Agent workflow transition configuration.

    Defines how to hand off conversation to another agent.

    Attributes:
        label: Button display text for the handoff action
        agent: Target agent identifier to hand off to
        prompt: Optional pre-filled message text
        send: Whether to auto-submit the handoff (default: False)
    """
    label: str = Field(..., description="Button display text")
    agent: str = Field(..., description="Target agent identifier")
    prompt: Optional[str] = Field(None, description="Pre-filled message text")
    send: bool = Field(False, description="Auto-submit flag")


class AgentDefinition(BaseModel):
    """Complete agent configuration from .agent.md file.

    Represents a parsed agent definition with YAML frontmatter fields
    and markdown body instructions.

    Attributes:
        name: Agent identifier (alphanumeric, hyphens, underscores)
        description: Brief agent purpose shown in UI
        tools: List of available tool names (built-in, MCP, custom)
        model: AI model specification
        argument_hint: Optional guidance text for user interaction
        target: Optional environment scope (vscode, github-copilot, teams)
        mcp_servers: Optional MCP server configuration
        handoffs: Optional workflow transitions to other agents
        instructions: Markdown body as system prompt
        file_path: Optional source file path
    """
    # Required fields
    name: str = Field(..., description="Agent identifier", min_length=1)
    description: str = Field(..., description="Brief agent purpose", min_length=1)
    tools: List[str] = Field(..., description="Available tool names")
    model: str = Field(..., description="AI model specification")

    # Optional fields
    argument_hint: Optional[str] = Field(None, alias="argument-hint")
    target: Optional[AgentTarget] = Field(None, description="Environment scope")
    mcp_servers: Optional[Dict[str, dict]] = Field(None, alias="mcp-servers")
    handoffs: Optional[List[AgentHandoff]] = Field(None, description="Workflow transitions")

    # Parsed from body
    instructions: str = Field(..., description="Markdown body as system prompt")
    file_path: Optional[str] = Field(None, description="Source file path")

    model_config = ConfigDict(
        populate_by_name=True  # Allow both alias and field name
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate agent name is valid identifier.

        Args:
            v: Agent name to validate

        Returns:
            Validated and stripped agent name

        Raises:
            ValueError: If name is empty or contains invalid characters
        """
        if not v or not v.strip():
            raise ValueError("Agent name cannot be empty")

        # Allow alphanumeric, hyphens, underscores
        v = v.strip()
        if not all(c.isalnum() or c in ("-", "_") for c in v):
            raise ValueError(
                f"Invalid agent name '{v}': use alphanumeric, hyphens, underscores only"
            )
        return v

    @field_validator("tools")
    @classmethod
    def validate_tools(cls, v: List[str]) -> List[str]:
        """Validate tools list is not empty.

        Args:
            v: Tools list to validate

        Returns:
            Validated tools list

        Raises:
            ValueError: If tools list is empty
        """
        if not v:
            raise ValueError("Agent must specify at least one tool")
        return v
