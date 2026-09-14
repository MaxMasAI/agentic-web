"""
tests/test_resilient_gateway.py - Test suite for Token Bucket, Backoff, and Circuit Breaker Gateway.
"""

import sys
import os
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.resilient_gateway import (
    TokenBucketLimiter,
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenException,
    ResilientGateway,
    get_resilient_gateway
)


class TestResilientGateway(unittest.TestCase):

    def test_token_bucket_rate_limiter(self):
        """Verify token bucket respects rate and capacity."""
        limiter = TokenBucketLimiter(rpm=300, burst_capacity=2)
        # First 2 should acquire immediately
        self.assertTrue(limiter.acquire(tokens=1.0, wait=False))
        self.assertTrue(limiter.acquire(tokens=1.0, wait=False))
        # Third without waiting should fail
        self.assertFalse(limiter.acquire(tokens=1.0, wait=False))

    def test_circuit_breaker_tripping_and_fallback(self):
        """Verify circuit breaker opens after failure threshold."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout_sec=0.2)

        self.assertTrue(cb.allow_request())
        self.assertEqual(cb.state, CircuitState.CLOSED)

        # First failure
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.CLOSED)

        # Second failure -> trips to OPEN
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.OPEN)
        self.assertFalse(cb.allow_request())

        # After recovery_timeout, state becomes HALF_OPEN
        time.sleep(0.25)
        self.assertTrue(cb.allow_request())
        self.assertEqual(cb.state, CircuitState.HALF_OPEN)

        # Recording success resets to CLOSED
        cb.record_success()
        self.assertEqual(cb.state, CircuitState.CLOSED)

    def test_resilient_gateway_execute_with_retry(self):
        """Verify gateway executes with retries and handles fallback."""
        gw = ResilientGateway()
        attempts = 0

        def flaky_api_call():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise ConnectionResetError("Temporary network hiccup")
            return {"status": "ok", "provider": "gemini"}

        result = gw.execute_with_resilience(
            provider="gemini_test",
            api_callable=flaky_api_call,
            max_retries=3,
            base_delay=0.01,
            max_delay=0.05
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(attempts, 2)


if __name__ == "__main__":
    unittest.main()
