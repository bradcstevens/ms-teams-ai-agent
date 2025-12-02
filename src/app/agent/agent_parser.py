"""Parser for .agent.md files with YAML frontmatter.

This module provides functionality to parse custom agent definition files
following the VS Code/GitHub Copilot .agent.md specification.
"""
import re
import logging
from pathlib import Path
from typing import Tuple
import yaml
from pydantic import ValidationError

from app.agent.agent_config import AgentDefinition

logger = logging.getLogger(__name__)

# Regex pattern for YAML frontmatter (--- delimited)
FRONTMATTER_PATTERN = re.compile(
    r'^---\s*\n(.*?)\n---\s*\n(.*)$',
    re.DOTALL | re.MULTILINE
)


class AgentParseError(Exception):
    """Raised when agent file parsing fails.

    This exception is raised for:
    - Missing or malformed YAML frontmatter
    - Invalid YAML syntax
    - Failed Pydantic validation
    """
    pass


def parse_agent_file(file_path: Path) -> AgentDefinition:
    """Parse .agent.md file into AgentDefinition.

    Extracts YAML frontmatter configuration and markdown body instructions
    from a .agent.md file and validates the configuration.

    Args:
        file_path: Path to .agent.md file

    Returns:
        Parsed and validated AgentDefinition

    Raises:
        FileNotFoundError: If file doesn't exist
        AgentParseError: If file is malformed or validation fails

    Example:
        >>> agent = parse_agent_file(Path(".github/agents/my-agent.agent.md"))
        >>> print(agent.name)
        'my-agent'
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Agent file not found: {file_path}")

    try:
        content = file_path.read_text(encoding='utf-8')

        # Extract frontmatter and body
        frontmatter, body = _extract_frontmatter(content)

        # Parse YAML frontmatter
        try:
            config = yaml.safe_load(frontmatter)
            if not isinstance(config, dict):
                raise AgentParseError("Frontmatter must be a YAML dictionary")
        except yaml.YAMLError as e:
            raise AgentParseError(f"Invalid YAML frontmatter: {e}")

        # Add parsed body as instructions
        config['instructions'] = body.strip()
        config['file_path'] = str(file_path)

        # Validate with Pydantic model
        try:
            return AgentDefinition(**config)
        except ValidationError as e:
            raise AgentParseError(f"Agent configuration validation failed: {e}")

    except AgentParseError:
        # Re-raise AgentParseError as-is
        raise
    except FileNotFoundError:
        # Re-raise FileNotFoundError as-is
        raise
    except Exception as e:
        logger.error(f"Failed to parse agent file {file_path}: {e}")
        raise AgentParseError(f"Unexpected error parsing agent file: {e}")


def _extract_frontmatter(content: str) -> Tuple[str, str]:
    """Extract YAML frontmatter and Markdown body.

    Parses content with YAML frontmatter delimited by --- markers.

    Args:
        content: File content with frontmatter

    Returns:
        Tuple of (frontmatter, body)

    Raises:
        AgentParseError: If frontmatter not found or malformed

    Example:
        >>> content = '''---
        ... name: test
        ... ---
        ... Instructions'''
        >>> fm, body = _extract_frontmatter(content)
        >>> 'name: test' in fm
        True
    """
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        raise AgentParseError(
            "No YAML frontmatter found. Expected format:\n"
            "---\n"
            "YAML content\n"
            "---\n"
            "Markdown body"
        )

    return match.group(1), match.group(2)
