from __future__ import annotations

import pytest

from app.agents.retry.policy import RetryPolicyExecutor, RetryReason
from app.agents.retry.strategy import (
    ExponentialBackoff, FullJitterBackoff, EqualJitterBackoff,
)
from app.agents.contracts import RetryPolicy


def test_exponential_backoff_delays() -> None:
    backoff = ExponentialBackoff(base_delay_ms=1000.0, max_delay_ms=30000.0)
    assert backoff.delay(1) == 1000.0
    assert backoff.delay(2) == 2000.0
    assert backoff.delay(3) == 4000.0
    assert backoff.delay(10) == 30000.0  # Max reached


def test_full_jitter_backoff_includes_jitter() -> None:
    backoff = FullJitterBackoff(base_delay_ms=1000.0, max_delay_ms=30000.0)
    delays = [backoff.delay(3) for _ in range(10)]
    base_delay = 4000.0  # 1000 * 2^(3-1)
    # All should be >= base and <= max
    for delay in delays:
        assert delay >= base_delay
        assert delay <= 30000.0


def test_retry_policy_executor_should_retry_logic() -> None:
    policy = RetryPolicy(max_retries=3, retryable_errors=["timeout", "rate_limit"])
    executor = RetryPolicyExecutor(policy)
    
    # Should retry timeout errors
    assert executor.should_retry("Request timeout") is True
    
    # Should retry rate limit errors
    assert executor.should_retry("Rate limit exceeded (429)") is True
    
    # Should NOT retry non-retryable errors
    assert executor.should_retry("Invalid JSON schema") is False


def test_retry_policy_executor_classify_error() -> None:
    policy = RetryPolicy()
    executor = RetryPolicyExecutor(policy)
    
    assert executor._classify_error("timeout occurred") == RetryReason.TIMEOUT
    assert executor._classify_error("429 rate limit") == RetryReason.RATE_LIMIT
    assert executor._classify_error("500 server error") == RetryReason.SERVER_ERROR
    assert executor._classify_error("malformed json") == RetryReason.MALFORMED_RESPONSE
    assert executor._classify_error("validation failed") == RetryReason.VALIDATION_FAILED


async def test_retry_policy_executor_execute_with_retry_success() -> None:
    policy = RetryPolicy(max_retries=2)
    executor = RetryPolicyExecutor(policy)
    
    async def successful_func():
        return True, {"result": "success"}, None
    
    success, result, error = await executor.execute_with_retry(successful_func)
    assert success is True
    assert result == {"result": "success"}
    assert error is None
    assert executor.attempt == 1  # No retries needed


async def test_retry_policy_executor_execute_with_retry_failure_then_success() -> None:
    policy = RetryPolicy(max_retries=3)
    executor = RetryPolicyExecutor(policy)
    
    attempt_count = 0
    
    async def fail_then_succeed():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            return False, None, "Server timeout error"
        return True, {"result": "finally worked"}, None
    
    success, result, error = await executor.execute_with_retry(fail_then_succeed)
    assert success is True
    assert result == {"result": "finally worked"}
    assert error is None
    assert executor.attempt == 3  # Two failures, then success
    assert len(executor.retry_history) == 3


async def test_retry_policy_executor_execute_with_retry_all_failures() -> None:
    policy = RetryPolicy(max_retries=3)
    executor = RetryPolicyExecutor(policy)
    
    async def always_fail():
        return False, None, "Server timeout error"
    
    success, result, error = await executor.execute_with_retry(always_fail)
    assert success is False
    assert result is None
    assert error == "Server timeout error"
    assert executor.attempt == 3
    assert len(executor.retry_history) == 3
