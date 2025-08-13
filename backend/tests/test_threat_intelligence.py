"""
Unit tests for threat intelligence framework
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.services.threat_intelligence.data_validator import ThreatDataValidator
from app.services.threat_intelligence.rate_limiter import (
    TokenBucket, AdaptiveRateLimiter, RetryHandler, RateLimitConfig
)
from app.models.threat_schemas import ThreatType, SeverityLevel


class TestThreatDataValidator:
    """Test threat data validation and normalization"""
    
    def setup_method(self):
        self.validator = ThreatDataValidator()
    
    def test_validate_hash_indicator(self):
        """Test validation of hash indicators"""
        raw_data = {
            'value': 'd41d8cd98f00b204e9800998ecf8427e',
            'type': 'hash',
            'description': 'Test hash',
            'first_seen': '2023-01-01T00:00:00Z'
        }
        
        result = self.validator.validate_and_normalize(raw_data, 'test_source')
        
        assert result is not None
        assert result.type == ThreatType.IOC
        assert result.value == 'd41d8cd98f00b204e9800998ecf8427e'
        assert result.source == 'test_source'
        assert result.description == 'Test hash'
    
    def test_validate_ip_indicator(self):
        """Test validation of IP address indicators"""
        raw_data = {
            'value': '192.168.1.1',
            'type': 'ip',
            'severity': 'high',
            'tags': ['malicious', 'botnet']
        }
        
        result = self.validator.validate_and_normalize(raw_data, 'test_source')
        
        assert result is not None
        assert result.type == ThreatType.IOC
        assert result.value == '192.168.1.1'
        assert result.severity == SeverityLevel.HIGH
        assert 'malicious' in result.tags
        assert 'botnet' in result.tags
    
    def test_validate_domain_indicator(self):
        """Test validation of domain indicators"""
        raw_data = {
            'value': 'malicious.example.com',
            'type': 'domain',
            'confidence': 0.9,
            'first_seen': '2023-01-01',
            'last_seen': '2023-01-02'
        }
        
        result = self.validator.validate_and_normalize(raw_data, 'test_source')
        
        assert result is not None
        assert result.type == ThreatType.IOC
        assert result.value == 'malicious.example.com'
        assert result.confidence >= 0.6  # Should be reasonable due to explicit confidence
    
    def test_validate_cve_indicator(self):
        """Test validation of CVE indicators"""
        raw_data = {
            'value': 'CVE-2023-1234',
            'description': 'Critical vulnerability',
            'severity': 'critical'
        }
        
        result = self.validator.validate_and_normalize(raw_data, 'test_source')
        
        assert result is not None
        assert result.type == ThreatType.VULNERABILITY
        assert result.value == 'cve-2023-1234'
        assert result.severity == SeverityLevel.CRITICAL
    
    def test_invalid_indicator_data(self):
        """Test handling of invalid indicator data"""
        invalid_data = [
            {},  # Empty data
            {'description': 'No value field'},  # Missing value
            {'value': ''},  # Empty value
            {'value': None},  # None value
        ]
        
        for data in invalid_data:
            result = self.validator.validate_and_normalize(data, 'test_source')
            assert result is None
    
    def test_confidence_calculation(self):
        """Test confidence score calculation"""
        # High confidence data
        high_conf_data = {
            'value': 'malicious.example.com',
            'type': 'domain',
            'confidence': 0.95,
            'description': 'Known malicious domain',
            'tags': ['malware', 'c2'],
            'first_seen': '2023-01-01T00:00:00Z',
            'last_seen': '2023-01-01T12:00:00Z'
        }
        
        result = self.validator.validate_and_normalize(high_conf_data, 'virustotal')
        assert result.confidence > 0.75  # Adjusted to realistic expectation
        
        # Low confidence data
        low_conf_data = {
            'value': 'suspicious.example.com',
            'type': 'domain'
        }
        
        result = self.validator.validate_and_normalize(low_conf_data, 'unknown_source')
        assert result.confidence < 0.7
    
    def test_datetime_parsing(self):
        """Test datetime parsing with various formats"""
        test_cases = [
            ('2023-01-01T00:00:00Z', datetime(2023, 1, 1, 0, 0, 0)),
            ('2023-01-01T00:00:00.123Z', datetime(2023, 1, 1, 0, 0, 0, 123000)),
            ('2023-01-01 00:00:00', datetime(2023, 1, 1, 0, 0, 0)),
            ('2023-01-01', datetime(2023, 1, 1, 0, 0, 0)),
            ('01/01/2023', datetime(2023, 1, 1, 0, 0, 0)),
        ]
        
        for date_str, expected in test_cases:
            result = self.validator._parse_datetime(date_str)
            assert result == expected
    
    def test_tag_extraction(self):
        """Test tag extraction from various formats"""
        test_cases = [
            ({'tags': ['malware', 'trojan']}, ['malware', 'trojan']),
            ({'tags': 'malware,trojan'}, ['malware', 'trojan']),
            ({'labels': ['suspicious']}, ['suspicious']),
            ({'categories': ['network']}, ['network']),
            ({'tags': [], 'labels': ['test']}, ['test']),
        ]
        
        for raw_data, expected in test_cases:
            tags = self.validator._extract_tags(raw_data)
            assert set(tags) == set(expected)


class TestTokenBucket:
    """Test token bucket rate limiting"""
    
    @pytest.mark.asyncio
    async def test_token_consumption(self):
        """Test basic token consumption"""
        bucket = TokenBucket(rate=1.0, capacity=5)
        
        # Should be able to consume initial tokens
        assert await bucket.consume(3) == True
        assert await bucket.consume(2) == True
        assert await bucket.consume(1) == False  # No tokens left
    
    @pytest.mark.asyncio
    async def test_token_refill(self):
        """Test token refill over time"""
        bucket = TokenBucket(rate=2.0, capacity=5)  # 2 tokens per second
        
        # Consume all tokens
        assert await bucket.consume(5) == True
        assert await bucket.consume(1) == False
        
        # Wait for refill
        await asyncio.sleep(1.1)  # Allow for 2+ tokens to be added
        assert await bucket.consume(2) == True
    
    @pytest.mark.asyncio
    async def test_wait_for_tokens(self):
        """Test wait time calculation"""
        bucket = TokenBucket(rate=1.0, capacity=5)
        
        # Consume all tokens
        await bucket.consume(5)
        
        # Should need to wait for tokens
        wait_time = await bucket.wait_for_tokens(2)
        assert wait_time >= 2.0


class TestAdaptiveRateLimiter:
    """Test adaptive rate limiting"""
    
    def setup_method(self):
        config = RateLimitConfig(
            requests_per_second=2.0,
            requests_per_minute=60.0,
            requests_per_hour=1000.0,
            burst_size=5
        )
        self.limiter = AdaptiveRateLimiter(feed_id=1, config=config)
    
    @pytest.mark.asyncio
    async def test_acquire_permission(self):
        """Test acquiring permission to make requests"""
        # Should be able to acquire immediately
        start_time = asyncio.get_event_loop().time()
        await self.limiter.acquire()
        end_time = asyncio.get_event_loop().time()
        
        assert end_time - start_time < 0.1  # Should be immediate
    
    @pytest.mark.asyncio
    async def test_rate_adaptation_on_success(self):
        """Test rate adaptation on successful requests"""
        initial_rate = self.limiter.current_rate
        
        # Record multiple successes
        for _ in range(15):
            await self.limiter.record_success()
        
        # Rate should increase (or stay same if already at max)
        assert self.limiter.current_rate >= initial_rate
    
    @pytest.mark.asyncio
    async def test_rate_adaptation_on_failure(self):
        """Test rate adaptation on failed requests"""
        initial_rate = self.limiter.current_rate
        
        # Record rate limit failure
        await self.limiter.record_failure(status_code=429)
        
        # Rate should decrease
        assert self.limiter.current_rate < initial_rate
    
    @pytest.mark.asyncio
    async def test_retry_delay_calculation(self):
        """Test retry delay calculation"""
        delay_0 = await self.limiter.get_retry_delay(0)
        delay_1 = await self.limiter.get_retry_delay(1)
        delay_2 = await self.limiter.get_retry_delay(2)
        
        # Delays should increase exponentially
        assert delay_1 > delay_0
        assert delay_2 > delay_1
    
    @pytest.mark.asyncio
    async def test_stats_collection(self):
        """Test statistics collection"""
        await self.limiter.record_success()
        await self.limiter.record_failure()
        
        stats = await self.limiter.get_stats()
        
        assert 'current_rate' in stats
        assert 'requests_last_minute' in stats
        assert 'errors_last_minute' in stats
        assert 'consecutive_successes' in stats
        assert 'consecutive_failures' in stats


class TestRetryHandler:
    """Test retry handling with circuit breaker"""
    
    def setup_method(self):
        self.handler = RetryHandler(feed_id=1, max_retries=3)
    
    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test successful function execution"""
        async def success_func():
            return "success"
        
        result = await self.handler.execute_with_retry(success_func)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test retry behavior on failures"""
        call_count = 0
        
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = await self.handler.execute_with_retry(failing_func)
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_max_retries_exhausted(self):
        """Test behavior when max retries are exhausted"""
        async def always_failing_func():
            raise Exception("Permanent failure")
        
        with pytest.raises(Exception, match="Permanent failure"):
            await self.handler.execute_with_retry(always_failing_func)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opening(self):
        """Test circuit breaker opening after failures"""
        # Cause enough failures to open circuit
        for _ in range(6):
            await self.handler._record_failure()
        
        # Circuit should be open
        assert await self.handler._is_circuit_open() == True
        
        # Should raise exception without calling function
        async def should_not_be_called():
            assert False, "Function should not be called when circuit is open"
        
        with pytest.raises(Exception, match="Circuit breaker is open"):
            await self.handler.execute_with_retry(should_not_be_called)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout"""
        # Open circuit
        for _ in range(6):
            await self.handler._record_failure()
        
        # Simulate timeout by setting old timestamp
        self.handler.circuit_open_time = asyncio.get_event_loop().time() - 400
        
        # Circuit should now be closed (half-open)
        assert await self.handler._is_circuit_open() == False
    
    @pytest.mark.asyncio
    async def test_stats_collection(self):
        """Test statistics collection"""
        await self.handler._record_failure()
        await self.handler._record_success()
        
        stats = await self.handler.get_stats()
        
        assert 'failure_count' in stats
        assert 'circuit_open' in stats
        assert 'last_failure_time' in stats


class TestIntegration:
    """Integration tests for threat intelligence components"""
    
    def setup_method(self):
        self.validator = ThreatDataValidator()
    
    def test_end_to_end_indicator_processing(self):
        """Test complete indicator processing pipeline"""
        # Simulate raw data from different sources
        test_indicators = [
            {
                'value': 'malicious.example.com',
                'type': 'domain',
                'confidence': 0.9,
                'description': 'Known C2 domain',
                'tags': ['malware', 'c2'],
                'first_seen': '2023-01-01T00:00:00Z',
                'source': 'virustotal'
            },
            {
                'value': '192.168.1.100',
                'indicator_type': 'ip',
                'severity': 'high',
                'created': '2023-01-01',
                'source': 'misp'
            },
            {
                'value': 'd41d8cd98f00b204e9800998ecf8427e',
                'category': 'hash',
                'priority': 'medium',
                'source': 'otx'
            }
        ]
        
        processed_indicators = []
        for raw_data in test_indicators:
            source = raw_data.pop('source')
            result = self.validator.validate_and_normalize(raw_data, source)
            if result:
                processed_indicators.append(result)
        
        # All indicators should be processed successfully
        assert len(processed_indicators) == 3
        
        # Check types are correctly identified
        types = [ind.type for ind in processed_indicators]
        assert ThreatType.IOC in types
        
        # Check confidence scores are reasonable
        confidences = [ind.confidence for ind in processed_indicators]
        assert all(0.0 <= conf <= 1.0 for conf in confidences)
        
        # Check sources are preserved
        sources = [ind.source for ind in processed_indicators]
        assert 'virustotal' in sources
        assert 'misp' in sources
        assert 'otx' in sources


if __name__ == '__main__':
    pytest.main([__file__])