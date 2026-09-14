"""
services/resilient_gateway.py - Enterprise Resilient API Gateway & Multi-Provider Token Manager.

Implements token-bucket rate limiting, exponential backoff with full jitter for HTTP 429/5xx,
and circuit-breaker failover across all cloud LLM providers (Gemini, DeepSeek, Claude, ChatGPT, etc.).
"""

import time
import random
import asyncio
import threading
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Tuple


class CircuitState(Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Outage detected - fast-fail & trigger fallback
    HALF_OPEN = "half_open"  # Probing provider recovery


class CircuitBreakerOpenException(Exception):
    """Raised when an API call is made to a provider whose circuit is OPEN."""
    pass


class TokenBucketLimiter:
    """
    Thread-safe Token Bucket Rate Limiter per provider.
    Enforces maximum requests-per-minute (RPM) and tokens-per-minute (TPM).
    """
    def __init__(self, rpm: int = 60, burst_capacity: int = 10):
        self.capacity = float(burst_capacity)
        self.tokens = float(burst_capacity)
        self.fill_rate = float(rpm) / 60.0  # tokens per second
        self.last_update = time.time()
        self._lock = threading.Lock()

    def acquire(self, tokens: float = 1.0, wait: bool = True, max_wait_sec: float = 10.0) -> bool:
        start_wait = time.time()
        while True:
            with self._lock:
                now = time.time()
                elapsed = now - self.last_update
                self.last_update = now
                self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                if not wait:
                    return False

                # Calculate required sleep duration
                missing = tokens - self.tokens
                sleep_time = missing / self.fill_rate

            if (time.time() - start_wait) + sleep_time > max_wait_sec:
                return False

            time.sleep(min(sleep_time, 0.5))


class CircuitBreaker:
    """
    Protects multi-agent pipeline from cascading outages.
    Trips to OPEN state after consecutive failures and routes to fallback models.
    """
    def __init__(self, failure_threshold: int = 4, recovery_timeout_sec: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_sec
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self._lock = threading.Lock()

    def record_success(self):
        with self._lock:
            self.failure_count = 0
            self.state = CircuitState.CLOSED

    def record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN

    def allow_request(self) -> bool:
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    return True
                return False
            if self.state == CircuitState.HALF_OPEN:
                return True
        return True


class ResilientGateway:
    """
    Central API Gateway managing resilience, rate limits, and failover across providers.
    """
    def __init__(self):
        self._limiters: Dict[str, TokenBucketLimiter] = {
            "gemini": TokenBucketLimiter(rpm=60, burst_capacity=10),
            "deepseek": TokenBucketLimiter(rpm=30, burst_capacity=5),
            "claude": TokenBucketLimiter(rpm=50, burst_capacity=8),
            "openai": TokenBucketLimiter(rpm=60, burst_capacity=10),
            "openrouter": TokenBucketLimiter(rpm=120, burst_capacity=20),
            "perplexity": TokenBucketLimiter(rpm=40, burst_capacity=5),
            "huggingface": TokenBucketLimiter(rpm=60, burst_capacity=10),
        }
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()

    def _get_breaker(self, provider: str) -> CircuitBreaker:
        p = provider.lower()
        with self._lock:
            if p not in self._breakers:
                self._breakers[p] = CircuitBreaker()
            return self._breakers[p]

    def _get_limiter(self, provider: str) -> TokenBucketLimiter:
        p = provider.lower()
        with self._lock:
            if p not in self._limiters:
                self._limiters[p] = TokenBucketLimiter(rpm=60, burst_capacity=10)
            return self._limiters[p]

    def execute_with_resilience(
        self,
        provider: str,
        api_callable: Callable[..., Any],
        *args,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 12.0,
        fallback_callable: Optional[Callable[..., Any]] = None,
        **kwargs
    ) -> Any:
        """
        Executes an API call with token bucket gating, exponential backoff,
        full jitter retry for 429/5xx, and circuit-breaker failover.
        """
        breaker = self._get_breaker(provider)
        limiter = self._get_limiter(provider)

        # 1. Check Circuit Breaker
        if not breaker.allow_request():
            if fallback_callable:
                print(f"[ResilientGateway] Provider '{provider}' circuit is OPEN -> Dispatching Fallback...")
                return fallback_callable(*args, **kwargs)
            raise CircuitBreakerOpenException(f"Provider '{provider}' circuit is currently OPEN due to repeated errors.")

        # 2. Acquire Token from Rate Limiter Bucket
        limiter.acquire(tokens=1.0, wait=True, max_wait_sec=10.0)

        # 3. Retry loop with Exponential Backoff & Full Jitter
        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                result = api_callable(*args, **kwargs)
                breaker.record_success()

                # Auto-record token telemetry into TokenManager
                try:
                    from services.token_manager import get_token_manager
                    # Estimate tokens from result length if not explicit
                    prompt_len = sum(len(str(a)) for a in args) // 4 + 100
                    res_len = len(str(result)) // 4 + 50
                    get_token_manager().record_usage(
                        provider=provider,
                        model=provider.lower(),
                        prompt_tokens=prompt_len,
                        completion_tokens=res_len
                    )
                except Exception:
                    pass

                return result
            except Exception as e:
                last_exception = e
                err_str = str(e).lower()
                is_rate_limit = "429" in err_str or "rate limit" in err_str or "quota" in err_str
                is_server_error = any(code in err_str for code in ["500", "502", "503", "504", "overloaded", "timeout", "connection", "network", "reset"])

                if attempt < max_retries and (is_rate_limit or is_server_error or isinstance(e, (ConnectionError, TimeoutError, OSError))):
                    # Full Jitter Exponential Backoff: delay = uniform(0, min(max_delay, base * 2^attempt))
                    min_jitter = min(base_delay, max_delay)
                    max_jitter = min(max_delay, base_delay * (2 ** attempt))
                    jitter_delay = random.uniform(min_jitter, max(min_jitter, max_jitter))
                    time.sleep(jitter_delay)
                    continue
                else:
                    breaker.record_failure()
                    break

        # 4. Trigger Fallback if available
        if fallback_callable:
            print(f"[ResilientGateway] Provider '{provider}' failed ({last_exception}) -> Executing Fallback...")
            return fallback_callable(*args, **kwargs)

        raise last_exception or RuntimeError(f"Execution failed for provider '{provider}'.")


# Global Gateway Singleton
_global_resilient_gateway: Optional[ResilientGateway] = None

def get_resilient_gateway() -> ResilientGateway:
    global _global_resilient_gateway
    if _global_resilient_gateway is None:
        _global_resilient_gateway = ResilientGateway()
    return _global_resilient_gateway
