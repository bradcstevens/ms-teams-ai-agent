"""Circuit breaker pattern implementation for MCP server resilience.

This module provides a circuit breaker to protect against cascading failures
when MCP servers become unresponsive or fail repeatedly.

Circuit states:
- CLOSED: Normal operation, requests pass through
- OPEN: Too many failures, requests immediately fail
- HALF_OPEN: Testing if service has recovered
"""
import logging
import time
from enum import Enum
from typing import Any, Callable, Optional

from app.mcp.exceptions import MCPConnectionError

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Circuit tripped, failing fast
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """Circuit breaker for protecting MCP server calls.

    Implements the circuit breaker pattern with configurable thresholds
    and recovery mechanisms.

    Attributes:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        success_threshold: Successes needed in half-open state to close circuit
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
    ):
        """Initialize circuit breaker.

        Args:
            name: Name of the circuit (typically server name)
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before trying half-open state
            success_threshold: Successes to close from half-open
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None

    @property
    def state(self) -> CircuitState:
        """Get current circuit state.

        Automatically transitions OPEN -> HALF_OPEN if recovery timeout elapsed.

        Returns:
            Current circuit state
        """
        # Auto-transition from OPEN to HALF_OPEN after timeout
        if self._state == CircuitState.OPEN and self._should_attempt_reset():
            logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN (recovery attempt)")
            self._state = CircuitState.HALF_OPEN
            self._success_count = 0

        return self._state

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery.

        Returns:
            True if recovery timeout has elapsed since last failure
        """
        if self._last_failure_time is None:
            return False
        return time.time() - self._last_failure_time >= self.recovery_timeout

    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute a function through the circuit breaker.

        Args:
            func: Async function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Result from function execution

        Raises:
            MCPConnectionError: If circuit is OPEN
            Exception: Any exception raised by the function
        """
        current_state = self.state

        # Fail fast if circuit is open
        if current_state == CircuitState.OPEN:
            raise MCPConnectionError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Service unavailable (recovery in {self._time_until_reset():.1f}s)"
            )

        try:
            # Execute the function
            result = await func(*args, **kwargs)

            # Record success
            self._on_success()

            return result

        except Exception:
            # Record failure
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Handle successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            logger.debug(
                f"Circuit breaker '{self.name}' success in HALF_OPEN "
                f"({self._success_count}/{self.success_threshold})"
            )

            # Close circuit if enough successes
            if self._success_count >= self.success_threshold:
                logger.info(f"Circuit breaker '{self.name}' closing (recovery successful)")
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
                self._last_failure_time = None

        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success in CLOSED state
            self._failure_count = 0

    def _on_failure(self) -> None:
        """Handle failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            # Immediately open if failure in half-open state
            logger.warning(
                f"Circuit breaker '{self.name}' opening (failure during recovery attempt)"
            )
            self._state = CircuitState.OPEN
            self._success_count = 0

        elif self._state == CircuitState.CLOSED:
            # Open if threshold exceeded
            if self._failure_count >= self.failure_threshold:
                logger.warning(
                    f"Circuit breaker '{self.name}' opening "
                    f"(threshold {self.failure_threshold} failures exceeded)"
                )
                self._state = CircuitState.OPEN

    def _time_until_reset(self) -> float:
        """Calculate time remaining until reset attempt.

        Returns:
            Seconds until reset, or 0 if ready
        """
        if self._last_failure_time is None:
            return 0.0

        elapsed = time.time() - self._last_failure_time
        remaining = max(0.0, self.recovery_timeout - elapsed)
        return remaining

    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state.

        Use this for administrative reset or testing.
        """
        logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED")
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None

    def get_metrics(self) -> dict[str, Any]:
        """Get current circuit breaker metrics.

        Returns:
            Dictionary with state, failure count, and time until reset
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "time_until_reset": self._time_until_reset() if self._state == CircuitState.OPEN else None,
        }
