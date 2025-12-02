"""Tests for custom agent configuration system (.agent.md files).

This module tests the agent configuration models, parser, and registry
for custom agent definitions following VS Code/GitHub Copilot specification.
"""
import pytest
from pathlib import Path
from typing import Dict, Any
from pydantic import ValidationError

from app.agent.agent_config import (
    AgentTarget,
    AgentHandoff,
    AgentDefinition,
)
from app.agent.agent_parser import (
    parse_agent_file,
    AgentParseError,
    _extract_frontmatter,
)
from app.agent.agent_registry import AgentRegistry


class TestAgentDefinitionValidation:
    """Test AgentDefinition model validation."""

    def test_minimal_valid_definition(self):
        """Test creating agent with minimal required fields."""
        agent = AgentDefinition(
            name="test-agent",
            description="Test agent for validation",
            tools=["tool1", "tool2"],
            model="Claude Sonnet 4",
            instructions="Test instructions"
        )

        assert agent.name == "test-agent"
        assert agent.description == "Test agent for validation"
        assert agent.tools == ["tool1", "tool2"]
        assert agent.model == "Claude Sonnet 4"
        assert agent.instructions == "Test instructions"
        assert agent.target is None
        assert agent.handoffs is None

    def test_full_agent_definition(self):
        """Test creating agent with all optional fields."""
        agent = AgentDefinition(
            name="full-agent",
            description="Complete agent configuration",
            tools=["tool1", "server/*"],
            model="Claude Sonnet 4",
            instructions="Full instructions",
            **{
                "argument-hint": "Ask me about...",
                "target": "teams",
                "mcp-servers": {
                    "test-server": {
                        "command": "npx",
                        "args": ["-y", "test-package"],
                        "env": {"API_KEY": "secret"}
                    }
                },
                "handoffs": [
                    {
                        "label": "Next Agent",
                        "agent": "target-agent",
                        "prompt": "Continue with...",
                        "send": False
                    }
                ]
            }
        )

        assert agent.name == "full-agent"
        assert agent.argument_hint == "Ask me about..."
        assert agent.target == AgentTarget.TEAMS
        assert "test-server" in agent.mcp_servers
        assert len(agent.handoffs) == 1
        assert agent.handoffs[0].label == "Next Agent"

    def test_empty_name_validation(self):
        """Test that empty agent name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AgentDefinition(
                name="",
                description="Test",
                tools=["tool1"],
                model="Claude Sonnet 4",
                instructions="Test"
            )
        assert "name" in str(exc_info.value).lower()

    def test_invalid_name_characters(self):
        """Test that invalid characters in name raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AgentDefinition(
                name="agent@test!",
                description="Test",
                tools=["tool1"],
                model="Claude Sonnet 4",
                instructions="Test"
            )
        assert "invalid" in str(exc_info.value).lower()

    def test_empty_tools_list_validation(self):
        """Test that empty tools list raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AgentDefinition(
                name="test-agent",
                description="Test",
                tools=[],
                model="Claude Sonnet 4",
                instructions="Test"
            )
        assert "tools" in str(exc_info.value).lower()


class TestAgentParser:
    """Test .agent.md file parsing functionality."""

    @pytest.fixture
    def temp_agent_file(self, tmp_path: Path) -> Path:
        """Create a temporary .agent.md file."""
        agent_file = tmp_path / "test-agent.agent.md"
        content = """---
name: test-agent
description: Test agent for parsing
tools:
  - tool1
  - tool2
model: Claude Sonnet 4
target: teams
---

# Test Agent Instructions

This is the agent's system prompt.
It can contain multiple lines.
"""
        agent_file.write_text(content, encoding='utf-8')
        return agent_file

    def test_parse_valid_agent_file(self, temp_agent_file: Path):
        """Test parsing a valid .agent.md file."""
        agent = parse_agent_file(temp_agent_file)

        assert agent.name == "test-agent"
        assert agent.description == "Test agent for parsing"
        assert agent.tools == ["tool1", "tool2"]
        assert agent.model == "Claude Sonnet 4"
        assert agent.target == AgentTarget.TEAMS
        assert "Test Agent Instructions" in agent.instructions
        assert str(temp_agent_file) == agent.file_path

    def test_parse_file_not_found(self, tmp_path: Path):
        """Test parsing non-existent file raises FileNotFoundError."""
        non_existent = tmp_path / "missing.agent.md"
        with pytest.raises(FileNotFoundError):
            parse_agent_file(non_existent)

    def test_parse_missing_frontmatter(self, tmp_path: Path):
        """Test parsing file without frontmatter raises AgentParseError."""
        bad_file = tmp_path / "bad.agent.md"
        bad_file.write_text("Just markdown content without frontmatter")

        with pytest.raises(AgentParseError) as exc_info:
            parse_agent_file(bad_file)
        assert "frontmatter" in str(exc_info.value).lower()

    def test_parse_invalid_yaml(self, tmp_path: Path):
        """Test parsing file with invalid YAML raises AgentParseError."""
        bad_yaml = tmp_path / "bad-yaml.agent.md"
        bad_yaml.write_text("""---
name: test
invalid: [unclosed list
---
Instructions""")

        with pytest.raises(AgentParseError) as exc_info:
            parse_agent_file(bad_yaml)
        assert "yaml" in str(exc_info.value).lower()

    def test_extract_frontmatter_valid(self):
        """Test extracting valid YAML frontmatter."""
        content = """---
name: test
description: Test
---
Body content"""

        frontmatter, body = _extract_frontmatter(content)
        assert "name: test" in frontmatter
        assert "Body content" in body

    def test_extract_frontmatter_missing(self):
        """Test extracting from content without frontmatter."""
        content = "Just markdown content"

        with pytest.raises(AgentParseError):
            _extract_frontmatter(content)


class TestAgentRegistry:
    """Test agent registry functionality."""

    @pytest.fixture
    def sample_agent(self) -> AgentDefinition:
        """Create a sample agent definition."""
        return AgentDefinition(
            name="sample-agent",
            description="Sample agent",
            tools=["tool1"],
            model="Claude Sonnet 4",
            instructions="Sample instructions"
        )

    def test_register_agent(self, sample_agent: AgentDefinition):
        """Test registering an agent."""
        registry = AgentRegistry()
        registry.register_agent(sample_agent)

        retrieved = registry.get_agent("sample-agent")
        assert retrieved is not None
        assert retrieved.name == "sample-agent"

    def test_register_duplicate_agent(self, sample_agent: AgentDefinition):
        """Test that registering duplicate agent raises ValueError."""
        registry = AgentRegistry()
        registry.register_agent(sample_agent)

        with pytest.raises(ValueError) as exc_info:
            registry.register_agent(sample_agent)
        assert "already registered" in str(exc_info.value).lower()

    def test_get_nonexistent_agent(self):
        """Test retrieving non-existent agent returns None."""
        registry = AgentRegistry()
        result = registry.get_agent("nonexistent")
        assert result is None

    def test_list_agents(self, sample_agent: AgentDefinition):
        """Test listing all registered agents."""
        registry = AgentRegistry()
        registry.register_agent(sample_agent)

        agents = registry.list_agents()
        assert len(agents) == 1
        assert agents[0].name == "sample-agent"

    def test_load_agents_from_folder(self, tmp_path: Path):
        """Test loading multiple agents from folder."""
        agents_folder = tmp_path / "agents"
        agents_folder.mkdir()

        # Create two agent files
        agent1 = agents_folder / "agent1.agent.md"
        agent1.write_text("""---
name: agent1
description: First agent
tools: [tool1]
model: Claude Sonnet 4
---
Instructions 1""")

        agent2 = agents_folder / "agent2.agent.md"
        agent2.write_text("""---
name: agent2
description: Second agent
tools: [tool2]
model: Claude Sonnet 4
---
Instructions 2""")

        registry = AgentRegistry()
        count = registry.load_agents_from_folder(agents_folder)

        assert count == 2
        assert registry.get_agent("agent1") is not None
        assert registry.get_agent("agent2") is not None

    def test_get_agents_by_target(self):
        """Test filtering agents by target."""
        registry = AgentRegistry()

        teams_agent = AgentDefinition(
            name="teams-agent",
            description="Teams agent",
            tools=["tool1"],
            model="Claude Sonnet 4",
            instructions="Teams instructions",
            target=AgentTarget.TEAMS
        )

        vscode_agent = AgentDefinition(
            name="vscode-agent",
            description="VS Code agent",
            tools=["tool2"],
            model="Claude Sonnet 4",
            instructions="VS Code instructions",
            target=AgentTarget.VSCODE
        )

        registry.register_agent(teams_agent)
        registry.register_agent(vscode_agent)

        teams_agents = registry.get_agents_by_target(AgentTarget.TEAMS)
        assert len(teams_agents) == 1
        assert teams_agents[0].name == "teams-agent"
