"""
Advanced rate limiting and retry logic for threat intelligence feeds
"""

import asyncio
import time
import logging
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque

from app.core.redis_config import redis_manager


logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_second: float = 1.0
    requests_per_minute: float = 60.0
    requests_per_hour: float = 3600.0
    burst_size: int = 10
    backoff_factor: float = 2.0
    max_backoff: float = 300.0  # 5 minutes


class TokenBucket:
    """Token bucket algorithm for rate limiting"""
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False otherwise
        """
        async with self._lock:
            now = time.time()
            
            # Add tokens based on elapsed time
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    async def wait_for_tokens(self, tokens: int = 1) -> float:
        """
        Calculate wait time for tokens to be available
        
        Args:
            tokens: Number of tokens needed
            
        Returns:
            Wait time in seconds
        """
        async with self._lock:
            if self.tokens >= tokens:
                return 0.0
            
            needed_tokens = tokens - self.tokens
            wait_time = needed_tokens / self.rate
            return wait_time


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter that adjusts based on API responses
    """
    
    def __init__(self, feed_id: int, config: RateLimitConfig):
        self.feed_id = feed_id
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Token buckets for different time windows
        self.second_bucket = TokenBucket(config.requests_per_second, config.burst_size)
        self.minute_bucket = TokenBucket(config.requests_per_minute / 60, int(config.requests_per_minute))
        self.hour_bucket = TokenBucket(config.requests_per_hour / 3600, int(config.requests_per_hour))
        
        # Adaptive parameters
        self.current_rate = config.requests_per_second
        self.consecutive_successes = 0
        self.consecutive_failures = 0
        self.last_rate_limit_time = None
        
        # Request tracking
        self.request_times = deque(maxlen=1000)
        self.error_times = deque(maxlen=100)
    
    async def acquire(self) -> None:
        """
        Acquire permission to make a request
        Blocks until permission is granted
        """
        # Check all token buckets
        buckets = [
            ("second", self.second_bucket),
            ("minute", self.minute_bucket),
            ("hour", self.hour_bucket)
        ]
        
        max_wait = 0.0
        for name, bucket in buckets:
            if not await bucket.consume():
                wait_time = await bucket.wait_for_tokens()
                max_wait = max(max_wait, wait_time)
                self.logger.debug(f"Rate limit hit for {name} bucket, waiting {wait_time:.2f}s")
        
        if max_wait > 0:
            await asyncio.sleep(max_wait)
            # Try again after waiting
            await self.acquire()
        
        # Track request time
        self.request_times.append(time.time())
    
    async def record_success(self) -> None:
        """Record a successful request"""
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        
        # Gradually increase rate if we're consistently successful
        if self.consecutive_successes >= 10:
            self.current_rate = min(
                self.config.requests_per_second * 1.1,
                self.config.requests_per_second
            )
            self.consecutive_successes = 0
    
    async def record_failure(self, status_code: Optional[int] = None) -> None:
        """Record a failed request"""
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        self.error_times.append(time.time())
        
        # Handle rate limiting
        if status_code == 429:
            self.last_rate_limit_time = time.time()
            # Reduce rate significantly
            self.current_rate = max(
                self.current_rate * 0.5,
                0.1  # Minimum rate
            )
            self.logger.warning(f"Rate limited, reducing rate to {self.current_rate}")
        
        # Handle other errors
        elif self.consecutive_failures >= 3:
            self.current_rate = max(
                self.current_rate * 0.8,
                0.1
            )
    
    async def get_retry_delay(self, attempt: int) -> float:
        """
        Calculate retry delay with exponential backoff
        
        Args:
            attempt: Retry attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        base_delay = 1.0
        
        # Exponential backoff
        delay = base_delay * (self.config.backoff_factor ** attempt)
        
        # Add jitter to prevent thundering herd
        jitter = delay * 0.1 * (time.time() % 1)  # 0-10% jitter
        delay += jitter
        
        # Cap at maximum backoff
        delay = min(delay, self.config.max_backoff)
        
        # Additional delay if we were recently rate limited
        if self.last_rate_limit_time:
            time_since_limit = time.time() - self.last_rate_limit_time
            if time_since_limit < 300:  # 5 minutes
                delay *= 2
        
        return delay
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        now = time.time()
        
        # Calculate recent request rate
        recent_requests = [t for t in self.request_times if now - t < 60]  # Last minute
        recent_errors = [t for t in self.error_times if now - t < 60]
        
        return {
            'current_rate': self.current_rate,
            'requests_last_minute': len(recent_requests),
            'errors_last_minute': len(recent_errors),
            'consecutive_successes': self.consecutive_successes,
            'consecutive_failures': self.consecutive_failures,
            'last_rate_limit': self.last_rate_limit_time,
            'tokens_available': {
                'second': self.second_bucket.tokens,
                'minute': self.minute_bucket.tokens,
                'hour': self.hour_bucket.tokens
            }
        }


class RetryHandler:
    """
    Handles retry logic with exponential backoff and circuit breaker pattern
    """
    
    def __init__(self, feed_id: int, max_retries: int = 3):
        self.feed_id = feed_id
        self.max_retries = max_retries
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Circuit breaker state
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_open = False
        self.circuit_open_time = None
        
        # Circuit breaker thresholds
        self.failure_threshold = 5
        self.recovery_timeout = 300  # 5 minutes
        self.half_open_max_calls = 3
        self.half_open_calls = 0
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries are exhausted
        """
        # Check circuit breaker
        if await self._is_circuit_open():
            raise Exception("Circuit breaker is open, skipping request")
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                
                # Success - reset circuit breaker
                await self._record_success()
                return result
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                # Record failure
                await self._record_failure()
                
                # Don't retry on final attempt
                if attempt == self.max_retries:
                    break
                
                # Calculate retry delay
                delay = await self._calculate_retry_delay(attempt)
                self.logger.info(f"Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
        
        # All retries exhausted
        raise last_exception
    
    async def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open"""
        if not self.circuit_open:
            return False
        
        # Check if recovery timeout has passed
        if self.circuit_open_time:
            time_since_open = time.time() - self.circuit_open_time
            if time_since_open >= self.recovery_timeout:
                # Move to half-open state
                self.circuit_open = False
                self.half_open_calls = 0
                self.logger.info("Circuit breaker moving to half-open state")
                return False
        
        return True
    
    async def _record_success(self) -> None:
        """Record successful execution"""
        if self.half_open_calls > 0:
            # We're in half-open state
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                # Enough successful calls, close circuit
                self.failure_count = 0
                self.circuit_open = False
                self.circuit_open_time = None
                self.half_open_calls = 0
                self.logger.info("Circuit breaker closed after successful recovery")
        else:
            # Normal operation
            self.failure_count = max(0, self.failure_count - 1)
    
    async def _record_failure(self) -> None:
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        # Check if we should open circuit
        if self.failure_count >= self.failure_threshold:
            self.circuit_open = True
            self.circuit_open_time = time.time()
            self.logger.error(f"Circuit breaker opened after {self.failure_count} failures")
    
    async def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate delay before retry"""
        base_delay = 1.0
        max_delay = 60.0
        
        # Exponential backoff with jitter
        delay = base_delay * (2 ** attempt)
        jitter = delay * 0.1 * (time.time() % 1)
        delay = min(delay + jitter, max_delay)
        
        return delay
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get retry handler statistics"""
        return {
            'failure_count': self.failure_count,
            'circuit_open': self.circuit_open,
            'circuit_open_time': self.circuit_open_time,
            'last_failure_time': self.last_failure_time,
            'half_open_calls': self.half_open_calls
        }


class FeedRateLimitManager:
    """
    Manages rate limiting for multiple threat feeds
    """
    
    def __init__(self):
        self.limiters: Dict[int, AdaptiveRateLimiter] = {}
        self.retry_handlers: Dict[int, RetryHandler] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def get_rate_limiter(self, feed_id: int, config: Optional[RateLimitConfig] = None) -> AdaptiveRateLimiter:
        """Get or create rate limiter for feed"""
        if feed_id not in self.limiters:
            if not config:
                config = RateLimitConfig()  # Use defaults
            self.limiters[feed_id] = AdaptiveRateLimiter(feed_id, config)
        
        return self.limiters[feed_id]
    
    def get_retry_handler(self, feed_id: int, max_retries: int = 3) -> RetryHandler:
        """Get or create retry handler for feed"""
        if feed_id not in self.retry_handlers:
            self.retry_handlers[feed_id] = RetryHandler(feed_id, max_retries)
        
        return self.retry_handlers[feed_id]
    
    async def execute_with_limits(self, feed_id: int, func: Callable, 
                                config: Optional[RateLimitConfig] = None,
                                max_retries: int = 3, *args, **kwargs) -> Any:
        """
        Execute function with rate limiting and retry logic
        
        Args:
            feed_id: Feed identifier
            func: Function to execute
            config: Rate limit configuration
            max_retries: Maximum retry attempts
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        rate_limiter = self.get_rate_limiter(feed_id, config)
        retry_handler = self.get_retry_handler(feed_id, max_retries)
        
        async def rate_limited_func(*args, **kwargs):
            await rate_limiter.acquire()
            try:
                result = await func(*args, **kwargs)
                await rate_limiter.record_success()
                return result
            except Exception as e:
                # Extract status code if available
                status_code = getattr(e, 'status_code', None)
                await rate_limiter.record_failure(status_code)
                raise
        
        return await retry_handler.execute_with_retry(rate_limited_func, *args, **kwargs)
    
    async def get_all_stats(self) -> Dict[int, Dict[str, Any]]:
        """Get statistics for all feeds"""
        stats = {}
        
        for feed_id in set(self.limiters.keys()) | set(self.retry_handlers.keys()):
            feed_stats = {}
            
            if feed_id in self.limiters:
                feed_stats['rate_limiter'] = await self.limiters[feed_id].get_stats()
            
            if feed_id in self.retry_handlers:
                feed_stats['retry_handler'] = await self.retry_handlers[feed_id].get_stats()
            
            stats[feed_id] = feed_stats
        
        return stats
    
    async def reset_feed_limits(self, feed_id: int) -> None:
        """Reset rate limits and circuit breaker for a feed"""
        if feed_id in self.limiters:
            limiter = self.limiters[feed_id]
            limiter.consecutive_failures = 0
            limiter.consecutive_successes = 0
            limiter.current_rate = limiter.config.requests_per_second
            limiter.last_rate_limit_time = None
        
        if feed_id in self.retry_handlers:
            handler = self.retry_handlers[feed_id]
            handler.failure_count = 0
            handler.circuit_open = False
            handler.circuit_open_time = None
            handler.half_open_calls = 0
        
        self.logger.info(f"Reset rate limits for feed {feed_id}")


# Global rate limit manager instance
rate_limit_manager = FeedRateLimitManager()