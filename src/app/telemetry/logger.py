"""Structured logging and Application Insights telemetry."""
import logging
import sys
from typing import Any, Dict, Optional
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace import config_integration
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

from app.config.settings import settings


class StructuredLogger:
    """Structured logger with Application Insights integration."""

    def __init__(self, name: str):
        """Initialize structured logger.

        Args:
            name: Logger name (typically __name__ of the module)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, settings.log_level.upper()))

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Application Insights handler (if configured)
        if settings.applicationinsights_connection_string:
            try:
                azure_handler = AzureLogHandler(
                    connection_string=settings.applicationinsights_connection_string
                )
                self.logger.addHandler(azure_handler)
            except Exception as e:
                self.logger.warning(f"Failed to configure Application Insights: {e}")

    def _enrich_properties(
        self,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Enrich log properties with standard fields.

        Args:
            properties: Additional properties to include

        Returns:
            Enriched properties dictionary
        """
        base_properties = {
            "service": "teams-ai-agent",
            "environment": "production" if settings.is_production else "development"
        }
        if properties:
            base_properties.update(properties)
        return base_properties

    def info(self, message: str, properties: Optional[Dict[str, Any]] = None):
        """Log info message with optional properties."""
        self.logger.info(message, extra={"custom_dimensions": self._enrich_properties(properties)})

    def warning(self, message: str, properties: Optional[Dict[str, Any]] = None):
        """Log warning message with optional properties."""
        self.logger.warning(message, extra={"custom_dimensions": self._enrich_properties(properties)})

    def error(self, message: str, properties: Optional[Dict[str, Any]] = None, exc_info: bool = True):
        """Log error message with optional properties."""
        self.logger.error(
            message,
            extra={"custom_dimensions": self._enrich_properties(properties)},
            exc_info=exc_info
        )

    def debug(self, message: str, properties: Optional[Dict[str, Any]] = None):
        """Log debug message with optional properties."""
        self.logger.debug(message, extra={"custom_dimensions": self._enrich_properties(properties)})


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)


def configure_tracing() -> Optional[Tracer]:
    """Configure distributed tracing with Application Insights.

    Returns:
        Tracer instance if Application Insights is configured, None otherwise
    """
    if not settings.applicationinsights_connection_string:
        return None

    try:
        # Enable tracing for common integrations
        config_integration.trace_integrations(['requests', 'httplib'])

        # Create tracer with Azure exporter
        exporter = AzureExporter(
            connection_string=settings.applicationinsights_connection_string
        )
        tracer = Tracer(
            exporter=exporter,
            sampler=ProbabilitySampler(1.0)  # Sample 100% in MVP
        )
        return tracer
    except Exception as e:
        logging.warning(f"Failed to configure distributed tracing: {e}")
        return None
