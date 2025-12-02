"""Registry for managing custom agent configurations.

This module provides thread-safe registry functionality for loading,
storing, and retrieving custom agent definitions.
"""
import threading
import logging
from pathlib import Path
from typing import Dict, List, Optional

from app.agent.agent_config import AgentDefinition, AgentTarget
from app.agent.agent_parser import parse_agent_file, AgentParseError

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Thread-safe registry for custom agent configurations.

    Manages agent lifecycle including loading from files, registration,
    validation, and retrieval. Supports filtering by target environment.

    Example:
        >>> registry = AgentRegistry()
        >>> registry.load_agents_from_folder(Path(".github/agents"))
        2
        >>> agent = registry.get_agent("my-agent")
        >>> teams_agents = registry.get_agents_by_target(AgentTarget.TEAMS)
    """

    def __init__(self, agents_folder: Optional[Path] = None):
        """Initialize agent registry.

        Args:
            agents_folder: Optional path to .github/agents or custom folder
        """
        self._agents: Dict[str, AgentDefinition] = {}
        self._lock = threading.Lock()
        self._agents_folder = agents_folder

    def register_agent(self, agent: AgentDefinition) -> None:
        """Register an agent in the registry.

        Thread-safe registration that prevents duplicate agent names.

        Args:
            agent: Agent definition to register

        Raises:
            ValueError: If agent with same name already exists
        """
        with self._lock:
            if agent.name in self._agents:
                raise ValueError(f"Agent '{agent.name}' already registered")

            self._agents[agent.name] = agent
            logger.info(f"Registered agent '{agent.name}' with {len(agent.tools)} tools")

    def get_agent(self, name: str) -> Optional[AgentDefinition]:
        """Retrieve agent by name.

        Thread-safe retrieval of agent configuration.

        Args:
            name: Agent identifier

        Returns:
            Agent definition if found, None otherwise
        """
        with self._lock:
            return self._agents.get(name)

    def list_agents(self) -> List[AgentDefinition]:
        """Get all registered agents.

        Thread-safe retrieval of all agents.

        Returns:
            List of all registered agent definitions
        """
        with self._lock:
            return list(self._agents.values())

    def get_agents_by_target(self, target: AgentTarget) -> List[AgentDefinition]:
        """Get agents filtered by target environment.

        Args:
            target: Target environment to filter by

        Returns:
            List of agents matching the target environment
        """
        with self._lock:
            return [
                agent for agent in self._agents.values()
                if agent.target == target
            ]

    def load_agents_from_folder(self, folder_path: Path) -> int:
        """Load all .agent.md files from a folder.

        Scans folder for .agent.md files and registers all valid agents.
        Invalid files are logged but don't stop the loading process.

        Args:
            folder_path: Path to folder containing .agent.md files

        Returns:
            Number of successfully loaded agents

        Raises:
            FileNotFoundError: If folder doesn't exist
        """
        if not folder_path.exists():
            raise FileNotFoundError(f"Agents folder not found: {folder_path}")

        if not folder_path.is_dir():
            raise ValueError(f"Path is not a directory: {folder_path}")

        loaded_count = 0
        agent_files = list(folder_path.glob("*.agent.md"))

        logger.info(f"Scanning folder for agent files: {folder_path}")
        logger.info(f"Found {len(agent_files)} .agent.md files")

        for agent_file in agent_files:
            try:
                agent = parse_agent_file(agent_file)
                self.register_agent(agent)
                loaded_count += 1
                logger.info(f"Loaded agent from {agent_file.name}")
            except (AgentParseError, ValueError) as e:
                logger.warning(
                    f"Failed to load agent from {agent_file.name}: {e}"
                )
                continue

        logger.info(f"Successfully loaded {loaded_count} agents from {folder_path}")
        return loaded_count
