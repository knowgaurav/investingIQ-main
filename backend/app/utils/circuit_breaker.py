"""Circuit breaker pattern implementation for external API calls.

Prevents cascading failures by temporarily blocking calls to failing services.
"""
import logging
import time
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from threading import Lock
from typing import Callable, Optional, TypeVar, Dict, List

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation, requests flow through
    OPEN = "open"  # Failure threshold exceeded, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitStats:
    """Statistics for a circuit breaker."""
    name: str
    state: str
    failure_count: int
    success_count: int
    last_failure_time: Optional[float]
    last_success_time: Optional[float]
    total_calls: int
    total_failures: int


class CircuitBreaker:
    """
    Circuit breaker for external service calls.
    
    States:
    - CLOSED: Normal operation, failures are counted
    - OPEN: Service is failing, all calls return fallback immediately
    - HALF_OPEN: After recovery timeout, allow one test call
    
    Usage:
        breaker = CircuitBreaker("yfinance", failure_threshold=5, recovery_timeout=60)
        
        result = breaker.call(fetch_stock_data, "AAPL")
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Identifier for this circuit
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            success_threshold: Successes needed in half-open to close circuit
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._last_success_time: Optional[float] = None
        self._total_calls = 0
        self._total_failures = 0
        self._lock = Lock()
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for recovery timeout."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_recovery():
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    logger.info(f"Circuit '{self.name}' entering HALF_OPEN state")
            return self._state
    
    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to try recovery."""
        if self._last_failure_time is None:
            return True
        return time.time() - self._last_failure_time >= self.recovery_timeout
    
    def _record_success(self):
        """Record a successful call."""
        with self._lock:
            self._success_count += 1
            self._last_success_time = time.time()
            self._total_calls += 1
            
            if self._state == CircuitState.HALF_OPEN:
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    logger.info(f"Circuit '{self.name}' recovered, now CLOSED")
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = max(0, self._failure_count - 1)
    
    def _record_failure(self, error: Exception):
        """Record a failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            self._total_calls += 1
            self._total_failures += 1
            
            if self._state == CircuitState.HALF_OPEN:
                # Back to open on any failure in half-open
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit '{self.name}' back to OPEN after failure in HALF_OPEN: {error}")
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.warning(f"Circuit '{self.name}' OPENED after {self._failure_count} failures")
    
    def call(
        self,
        func: Callable,
        *args,
        fallback: Optional[Callable] = None,
        **kwargs,
    ):
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args: Positional arguments for func
            fallback: Optional fallback function if circuit is open
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from func or fallback
            
        Raises:
            CircuitOpenError: If circuit is open and no fallback provided
        """
        current_state = self.state
        
        if current_state == CircuitState.OPEN:
            if fallback:
                logger.debug(f"Circuit '{self.name}' is OPEN, using fallback")
                return fallback()
            raise CircuitOpenError(f"Circuit '{self.name}' is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure(e)
            if fallback and self.state == CircuitState.OPEN:
                return fallback()
            raise
    
    async def call_async(
        self,
        func: Callable,
        *args,
        fallback: Optional[Callable] = None,
        **kwargs,
    ):
        """Async version of call()."""
        current_state = self.state
        
        if current_state == CircuitState.OPEN:
            if fallback:
                logger.debug(f"Circuit '{self.name}' is OPEN, using fallback")
                return fallback()
            raise CircuitOpenError(f"Circuit '{self.name}' is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure(e)
            if fallback and self.state == CircuitState.OPEN:
                return fallback()
            raise
    
    def get_stats(self) -> CircuitStats:
        """Get current circuit statistics."""
        with self._lock:
            return CircuitStats(
                name=self.name,
                state=self._state.value,
                failure_count=self._failure_count,
                success_count=self._success_count,
                last_failure_time=self._last_failure_time,
                last_success_time=self._last_success_time,
                total_calls=self._total_calls,
                total_failures=self._total_failures,
            )
    
    def reset(self):
        """Manually reset the circuit to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            logger.info(f"Circuit '{self.name}' manually reset to CLOSED")


class CircuitOpenError(Exception):
    """Raised when circuit is open and no fallback provided."""
    pass


# Global circuit breakers for external services
_circuits: Dict[str, CircuitBreaker] = {}
_circuits_lock = Lock()


def get_circuit(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
) -> CircuitBreaker:
    """Get or create a named circuit breaker."""
    with _circuits_lock:
        if name not in _circuits:
            _circuits[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
            )
        return _circuits[name]


def circuit_protected(
    circuit_name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    fallback: Optional[Callable] = None,
):
    """
    Decorator to protect a function with a circuit breaker.
    
    Usage:
        @circuit_protected("yfinance", failure_threshold=5, recovery_timeout=60)
        def fetch_stock_data(ticker: str) -> dict:
            ...
    """
    def decorator(func: Callable) -> Callable:
        circuit = get_circuit(circuit_name, failure_threshold, recovery_timeout)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return circuit.call(func, *args, fallback=fallback, **kwargs)
        
        return wrapper
    return decorator


def get_all_circuit_stats() -> List[CircuitStats]:
    """Get statistics for all circuit breakers."""
    with _circuits_lock:
        return [circuit.get_stats() for circuit in _circuits.values()]
