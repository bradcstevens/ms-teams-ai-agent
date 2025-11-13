"""Application configuration and settings."""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Azure OpenAI Configuration
    azure_openai_endpoint: str
    azure_openai_deployment_name: str
    azure_openai_api_version: str = "2024-10-21"

    # Bot Service Configuration
    bot_id: str
    bot_password: Optional[str] = None  # Optional for managed identity

    # Key Vault Configuration (optional for local dev)
    key_vault_name: Optional[str] = None
    key_vault_uri: Optional[str] = None

    # Application Insights Configuration
    applicationinsights_connection_string: Optional[str] = None

    # Application Configuration
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # Conversation Configuration
    max_conversation_history: int = 10
    conversation_timeout_minutes: int = 30

    # Agent Configuration
    agent_name: str = "Teams AI Agent"
    agent_instructions: str = (
        "You are a helpful AI assistant for Microsoft Teams. "
        "Provide clear, concise, and professional responses to user questions."
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"

    @property
    def use_managed_identity(self) -> bool:
        """Check if using managed identity for authentication."""
        return self.bot_password is None or self.bot_password == ""


# Global settings instance
settings = Settings()
