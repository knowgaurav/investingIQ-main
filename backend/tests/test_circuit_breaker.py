"""Tests for circuit breaker."""
import pytest
import time
from unittest.mock import MagicMock

from app.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitOpenError,
    get_circuit,
    circuit_protected,
)


class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""
    
    def test_circuit_starts_closed(self):
        """Test that circuit starts in closed state."""
        circuit = CircuitBreaker("test", failure_threshold=3)
        assert circuit.state == CircuitState.CLOSED
    
    def test_circuit_opens_after_threshold_failures(self):
        """Test that circuit opens after reaching failure threshold."""
        circuit = CircuitBreaker("test", failure_threshold=3)
        
        def failing_func():
            raise Exception("Service unavailable")
        
        # Fail 3 times
        for _ in range(3):
            with pytest.raises(Exception):
                circuit.call(failing_func)
        
        assert circuit.state == CircuitState.OPEN
    
    def test_open_circuit_blocks_calls(self):
        """Test that open circuit blocks calls."""
        circuit = CircuitBreaker("test", failure_threshold=1)
        
        def failing_func():
            raise Exception("Service unavailable")
        
        # Open the circuit
        with pytest.raises(Exception):
            circuit.call(failing_func)
        
        assert circuit.state == CircuitState.OPEN
        
        # Further calls should raise CircuitOpenError
        with pytest.raises(CircuitOpenError):
            circuit.call(lambda: "success")
    
    def test_open_circuit_uses_fallback(self):
        """Test that open circuit uses fallback if provided."""
        circuit = CircuitBreaker("test", failure_threshold=1)
        
        def failing_func():
            raise Exception("Service unavailable")
        
        def fallback():
            return "fallback_result"
        
        # Open the circuit
        with pytest.raises(Exception):
            circuit.call(failing_func)
        
        assert circuit.state == CircuitState.OPEN
        
        # Call with fallback should return fallback result
        result = circuit.call(failing_func, fallback=fallback)
        assert result == "fallback_result"
    
    def test_circuit_transitions_to_half_open(self):
        """Test that circuit transitions to half-open after recovery timeout."""
        circuit = CircuitBreaker("test_half_open", failure_threshold=1, recovery_timeout=0)
        
        def failing_func():
            raise Exception("Service unavailable")
        
        # Open the circuit
        with pytest.raises(Exception):
            circuit.call(failing_func)
        
        # Access internal state directly (bypassing the property that checks recovery)
        assert circuit._state == CircuitState.OPEN
        
        # Wait for recovery timeout (0 seconds in this case)
        time.sleep(0.01)
        
        # Force state check which should transition to half-open
        _ = circuit.state
        
        # Now should be half-open
        assert circuit._state == CircuitState.HALF_OPEN
    
    def test_half_open_closes_on_success(self):
        """Test that half-open circuit closes on successful call."""
        circuit = CircuitBreaker(
            "test",
            failure_threshold=1,
            recovery_timeout=0,
            success_threshold=1,
        )
        
        call_count = 0
        
        def sometimes_failing_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First call fails")
            return "success"
        
        # Open the circuit
        with pytest.raises(Exception):
            circuit.call(sometimes_failing_func)
        
        time.sleep(0.1)  # Wait for half-open
        
        # Successful call in half-open should close circuit
        result = circuit.call(sometimes_failing_func)
        assert result == "success"
        assert circuit.state == CircuitState.CLOSED
    
    def test_half_open_reopens_on_failure(self):
        """Test that half-open circuit reopens on failure."""
        circuit = CircuitBreaker("test_reopen", failure_threshold=1, recovery_timeout=0)
        
        call_count = 0
        def always_failing_func():
            nonlocal call_count
            call_count += 1
            raise Exception(f"Always fails (call {call_count})")
        
        # Open the circuit
        with pytest.raises(Exception):
            circuit.call(always_failing_func)
        
        # Verify it's open
        assert circuit._state == CircuitState.OPEN
        
        # Wait for recovery timeout and trigger transition to half-open
        time.sleep(0.01)
        _ = circuit.state  # This triggers the transition check
        
        # Now it should be half-open
        assert circuit._state == CircuitState.HALF_OPEN
        
        # Failed call in half-open should reopen circuit
        with pytest.raises(Exception):
            circuit.call(always_failing_func)
        
        # Should be back to open
        assert circuit._state == CircuitState.OPEN
    
    def test_circuit_stats(self):
        """Test that circuit stats are tracked correctly."""
        circuit = CircuitBreaker("test_stats", failure_threshold=5)
        
        def success_func():
            return "ok"
        
        def fail_func():
            raise Exception("fail")
        
        # Make some calls
        circuit.call(success_func)
        circuit.call(success_func)
        
        with pytest.raises(Exception):
            circuit.call(fail_func)
        
        stats = circuit.get_stats()
        
        assert stats.name == "test_stats"
        assert stats.total_calls == 3
        assert stats.total_failures == 1
    
    def test_reset_circuit(self):
        """Test that circuit can be manually reset."""
        circuit = CircuitBreaker("test", failure_threshold=1)
        
        def failing_func():
            raise Exception("fail")
        
        # Open the circuit
        with pytest.raises(Exception):
            circuit.call(failing_func)
        
        assert circuit.state == CircuitState.OPEN
        
        # Reset the circuit
        circuit.reset()
        
        assert circuit.state == CircuitState.CLOSED


class TestCircuitProtectedDecorator:
    """Tests for circuit_protected decorator."""
    
    def test_decorator_creates_circuit(self):
        """Test that decorator creates a named circuit."""
        @circuit_protected("decorated_test", failure_threshold=3)
        def protected_function():
            return "result"
        
        result = protected_function()
        assert result == "result"
        
        # Check circuit was created
        circuit = get_circuit("decorated_test")
        assert circuit is not None


class TestGetCircuit:
    """Tests for get_circuit function."""
    
    def test_get_circuit_returns_same_instance(self):
        """Test that get_circuit returns the same instance for same name."""
        circuit1 = get_circuit("singleton_test")
        circuit2 = get_circuit("singleton_test")
        
        assert circuit1 is circuit2
    
    def test_get_circuit_creates_different_instances_for_different_names(self):
        """Test that get_circuit creates different instances for different names."""
        circuit1 = get_circuit("test_a")
        circuit2 = get_circuit("test_b")
        
        assert circuit1 is not circuit2
