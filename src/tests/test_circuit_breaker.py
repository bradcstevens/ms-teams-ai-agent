"""Tests for circuit breaker pattern implementation.

This test suite validates the circuit breaker functionality for MCP server resilience.
"""
import asyncio

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

        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_func)

        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker._failure_count == 1

    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold_failures(self, circuit_breaker):
        """Test circuit opens after reaching failure threshold."""
        async def failing_func():
            raise ValueError("Simulated failure")

        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        assert circuit_breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_open_fails_fast(self, circuit_breaker):
        """Test circuit in OPEN state fails immediately without calling function."""
        async def should_not_be_called():
            pytest.fail("Function should not be called when circuit is OPEN")

        async def failing_func():
            raise ValueError("Failure")

        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        with pytest.raises(MCPConnectionError, match="Circuit breaker.*is OPEN"):
            await circuit_breaker.call(should_not_be_called)

    @pytest.mark.asyncio
    async def test_circuit_transitions_to_half_open_after_timeout(self, circuit_breaker):
        """Test circuit transitions from OPEN to HALF_OPEN after recovery timeout."""
        async def failing_func():
            raise ValueError("Failure")

        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        assert circuit_breaker.state == CircuitState.OPEN
        await asyncio.sleep(1.1)
        assert circuit_breaker.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_circuit_closes_after_successful_half_open_calls(self, circuit_breaker):
        """Test circuit closes after success threshold in HALF_OPEN state."""
        async def failing_func():
            raise ValueError("Failure")

        async def success_func():
            return "success"

        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        await asyncio.sleep(1.1)
        assert circuit_breaker.state == CircuitState.HALF_OPEN

        await circuit_breaker.call(success_func)
        assert circuit_breaker.state == CircuitState.HALF_OPEN

        await circuit_breaker.call(success_func)
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_manual_reset(self, circuit_breaker):
        """Test manual circuit breaker reset."""
        async def failing_func():
            raise ValueError("Failure")

        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        assert circuit_breaker.state == CircuitState.OPEN

        circuit_breaker.reset()

        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker._failure_count == 0

    @pytest.mark.asyncio
    async def test_get_metrics(self, circuit_breaker):
        """Test circuit breaker metrics retrieval."""
        metrics = circuit_breaker.get_metrics()

        assert metrics["name"] == "test-server"
        assert metrics["state"] == CircuitState.CLOSED.value
        assert metrics["failure_count"] == 0
