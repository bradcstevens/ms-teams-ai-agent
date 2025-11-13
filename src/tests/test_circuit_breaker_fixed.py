"""Tests for circuit breaker pattern implementation.

This test suite validates the circuit breaker functionality for MCP server resilience.
"""
import asyncio
import time

import pytest

from app.mcp.circuit_breaker import CircuitBreaker, CircuitState
from app.mcp.exceptions import MCPConnectionError


class TestCircuitBreaker:
    """Test cases for CircuitBreaker pattern."""

    @pytest.fixture
    def circuit_breaker(self):
        """Create a circuit breaker with low thresholds for testing."""
        return CircuitBreaker(
            name="test-server",
            failure_threshold=3,
            recovery_timeout=1.0,
            success_threshold=2,
        )

    @pytest.mark.asyncio
    async def test_circuit_breaker_initial_state(self, circuit_breaker):
        """Test circuit breaker starts in CLOSED state."""
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.name == "test-server"

    @pytest.mark.asyncio
    async def test_successful_call_in_closed_state(self, circuit_breaker):
        """Test successful function call passes through."""
        async def success_func():
            return "success"

        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failed_call_increments_failure_count(self, circuit_breaker):
        """Test failed calls increment failure counter."""
        async def failing_func():
            raise ValueError("Simulated failure")

        # First failure
        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_func)

        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker._failure_count == 1

    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold_failures(self, circuit_breaker):
        """Test circuit opens after reaching failure threshold."""
        async def failing_func():
            raise ValueError("Simulated failure")

        # Trigger failures up to threshold (3)
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        # Circuit should now be OPEN
        assert circuit_breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_open_fails_fast(self, circuit_breaker):
        """Test circuit in OPEN state fails immediately without calling function."""
        async def should_not_be_called():
            pytest.fail("Function should not be called when circuit is OPEN")

        # Trigger failures to open circuit
        async def failing_func():
            raise ValueError("Failure")

        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        # Circuit is OPEN, should fail fast
        with pytest.raises(MCPConnectionError, match="Circuit breaker.*is OPEN"):
            await circuit_breaker.call(should_not_be_called)

    @pytest.mark.asyncio
    async def test_circuit_transitions_to_half_open_after_timeout(self, circuit_breaker):
        """Test circuit transitions from OPEN to HALF_OPEN after recovery timeout."""
        async def failing_func():
            raise ValueError("Failure")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        assert circuit_breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Check state should transition to HALF_OPEN
        assert circuit_breaker.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_circuit_closes_after_successful_half_open_calls(self, circuit_breaker):
        """Test circuit closes after success threshold in HALF_OPEN state."""
        async def failing_func():
            raise ValueError("Failure")

        async def success_func():
            return "success"

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        # Wait for HALF_OPEN
        await asyncio.sleep(1.1)
        assert circuit_breaker.state == CircuitState.HALF_OPEN

        # Successful calls to close circuit (need 2)
        await circuit_breaker.call(success_func)
        assert circuit_breaker.state == CircuitState.HALF_OPEN

        await circuit_breaker.call(success_func)
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_reopens_on_half_open_failure(self, circuit_breaker):
        """Test circuit reopens immediately if call fails in HALF_OPEN state."""
        async def failing_func():
            raise ValueError("Failure")

        async def success_func():
            return "success"

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        # Wait for HALF_OPEN
        await asyncio.sleep(1.1)
        assert circuit_breaker.state == CircuitState.HALF_OPEN

        # Failure in HALF_OPEN should reopen circuit
        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_func)

        assert circuit_breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_manual_reset(self, circuit_breaker):
        """Test manual circuit breaker reset."""
        async def failing_func():
            raise ValueError("Failure")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        assert circuit_breaker.state == CircuitState.OPEN

        # Manual reset
        circuit_breaker.reset()

        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker._failure_count == 0
        assert circuit_breaker._success_count == 0

    @pytest.mark.asyncio
    async def test_get_metrics(self, circuit_breaker):
        """Test circuit breaker metrics retrieval."""
        metrics = circuit_breaker.get_metrics()

        assert metrics["name"] == "test-server"
        assert metrics["state"] == CircuitState.CLOSED.value
        assert metrics["failure_count"] == 0
        assert metrics["success_count"] == 0
        assert metrics["time_until_reset"] is None

    @pytest.mark.asyncio
    async def test_metrics_in_open_state(self, circuit_breaker):
        """Test metrics include time_until_reset in OPEN state."""
        async def failing_func():
            raise ValueError("Failure")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        metrics = circuit_breaker.get_metrics()

        assert metrics["state"] == CircuitState.OPEN.value
        assert metrics["failure_count"] == 3
        assert metrics["time_until_reset"] is not None
        assert metrics["time_until_reset"] > 0

    @pytest.mark.asyncio
    async def test_success_resets_failure_count_in_closed_state(self, circuit_breaker):
        """Test successful call resets failure count in CLOSED state."""
        async def failing_func():
            raise ValueError("Failure")

        async def success_func():
            return "success"

        # Accumulate some failures (but not enough to open)
        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_func)

        assert circuit_breaker._failure_count == 1

        # Success should reset failure count
        await circuit_breaker.call(success_func)
        assert circuit_breaker._failure_count == 0
        assert circuit_breaker.state == CircuitState.CLOSED
