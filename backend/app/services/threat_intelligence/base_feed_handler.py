"""
Base threat feed handler with common functionality
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, AsyncGenerator
import aiohttp
from asyncio_throttle import Throttler

from app.models.threat_intelligence import ThreatFeed, ThreatIndicator
from app.models.threat_schemas import ThreatIndicatorCreate
from app.core.redis_config import threat_cache


logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Raised when API rate limit is exceeded"""
    pass


class FeedConnectionError(Exception):
    """Raised when feed connection fails"""
    pass


class FeedAuthenticationError(Exception):
    """Raised when feed authentication fails"""
    pass


class BaseThreatFeedHandler(ABC):
    """
    Abstract base class for threat intelligence feed handlers
    """
    
    def __init__(self, feed: ThreatFeed):
        self.feed = feed
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Rate limiting
        self.throttler = Throttler(rate_limit=feed.rate_limit, period=3600)  # per hour
        
        # HTTP session configuration
        self.session_timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        # Processing configuration
        self.batch_size = 100
        self.max_indicators_per_run = getattr(feed, 'max_indicators_per_run', 10000)
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=self.session_timeout,
            headers=self._get_default_headers()
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if hasattr(self, 'session'):
            await self.session.close()
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default HTTP headers for requests"""
        return {
            'User-Agent': 'AITM-ThreatIntelligence/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the threat feed API
        Returns True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def fetch_indicators(self, since: Optional[datetime] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Fetch threat indicators from the feed
        
        Args:
            since: Only fetch indicators updated since this timestamp
            
        Yields:
            Raw indicator data from the feed
        """
        pass
    
    @abstractmethod
    def normalize_indicator(self, raw_data: Dict[str, Any]) -> Optional[ThreatIndicatorCreate]:
        """
        Normalize raw indicator data to standard format
        
        Args:
            raw_data: Raw indicator data from feed
            
        Returns:
            Normalized threat indicator or None if invalid
        """
        pass
    
    async def test_connection(self) -> bool:
        """
        Test connection to the threat feed
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            async with self:
                auth_result = await self.authenticate()
                if not auth_result:
                    self.logger.error(f"Authentication failed for feed {self.feed.name}")
                    return False
                
                # Try to fetch a small sample
                indicator_count = 0
                async for _ in self.fetch_indicators():
                    indicator_count += 1
                    if indicator_count >= 1:  # Just test with one indicator
                        break
                
                self.logger.info(f"Connection test successful for feed {self.feed.name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Connection test failed for feed {self.feed.name}: {e}")
            return False
    
    async def ingest_indicators(self, since: Optional[datetime] = None) -> Dict[str, int]:
        """
        Main ingestion method - fetch and process indicators
        
        Args:
            since: Only fetch indicators updated since this timestamp
            
        Returns:
            Dictionary with processing statistics
        """
        stats = {
            'fetched': 0,
            'processed': 0,
            'skipped': 0,
            'errors': 0
        }
        
        try:
            async with self:
                # Authenticate
                if not await self.authenticate():
                    raise FeedAuthenticationError(f"Authentication failed for feed {self.feed.name}")
                
                # Track processing status
                await threat_cache.track_feed_processing(self.feed.id, "processing")
                
                # Process indicators in batches
                batch = []
                async for raw_indicator in self.fetch_indicators(since):
                    stats['fetched'] += 1
                    
                    # Apply rate limiting
                    async with self.throttler:
                        try:
                            normalized = self.normalize_indicator(raw_indicator)
                            if normalized:
                                batch.append(normalized)
                                stats['processed'] += 1
                            else:
                                stats['skipped'] += 1
                                
                            # Process batch when full
                            if len(batch) >= self.batch_size:
                                await self._process_batch(batch)
                                batch = []
                                
                            # Check limits
                            if stats['fetched'] >= self.max_indicators_per_run:
                                self.logger.info(f"Reached max indicators limit for feed {self.feed.name}")
                                break
                                
                        except Exception as e:
                            self.logger.error(f"Error processing indicator: {e}")
                            stats['errors'] += 1
                
                # Process remaining batch
                if batch:
                    await self._process_batch(batch)
                
                # Update feed status
                await self._update_feed_status(stats)
                await threat_cache.track_feed_processing(self.feed.id, "completed")
                
        except Exception as e:
            self.logger.error(f"Ingestion failed for feed {self.feed.name}: {e}")
            await threat_cache.track_feed_processing(self.feed.id, "error")
            stats['errors'] += 1
            raise
        
        return stats
    
    async def _process_batch(self, batch: List[ThreatIndicatorCreate]) -> None:
        """
        Process a batch of normalized indicators
        
        Args:
            batch: List of normalized threat indicators
        """
        # This will be implemented when we create the threat intelligence service
        # For now, just log the batch size
        self.logger.info(f"Processing batch of {len(batch)} indicators for feed {self.feed.name}")
        
        # TODO: Implement actual database insertion and deduplication
        # This would involve:
        # 1. Check for existing indicators (deduplication)
        # 2. Insert new indicators
        # 3. Update existing indicators if newer
        # 4. Create relationships
        # 5. Trigger correlation analysis
    
    async def _update_feed_status(self, stats: Dict[str, int]) -> None:
        """
        Update feed status after processing
        
        Args:
            stats: Processing statistics
        """
        try:
            # Cache the feed status
            status_data = {
                'last_run': datetime.utcnow().isoformat(),
                'stats': stats,
                'status': 'completed' if stats['errors'] == 0 else 'error'
            }
            
            await threat_cache.cache_feed_status(self.feed.id, status_data)
            
            self.logger.info(f"Updated status for feed {self.feed.name}: {stats}")
            
        except Exception as e:
            self.logger.error(f"Failed to update feed status: {e}")
    
    async def _make_request(self, url: str, method: str = 'GET', **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and error handling
        
        Args:
            url: Request URL
            method: HTTP method
            **kwargs: Additional request parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            FeedConnectionError: If request fails after retries
            RateLimitExceeded: If rate limit is exceeded
        """
        for attempt in range(self.max_retries):
            try:
                async with self.session.request(method, url, **kwargs) as response:
                    # Handle rate limiting
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    # Handle authentication errors
                    if response.status == 401:
                        raise FeedAuthenticationError(f"Authentication failed: {response.status}")
                    
                    # Handle other client errors
                    if response.status >= 400:
                        error_text = await response.text()
                        raise FeedConnectionError(f"HTTP {response.status}: {error_text}")
                    
                    # Parse response
                    if response.content_type == 'application/json':
                        return await response.json()
                    else:
                        text = await response.text()
                        return {'data': text}
                        
            except aiohttp.ClientError as e:
                self.logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    raise FeedConnectionError(f"Request failed after {self.max_retries} attempts: {e}")
        
        raise FeedConnectionError("Unexpected error in request handling")
    
    def _validate_indicator_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate raw indicator data
        
        Args:
            data: Raw indicator data
            
        Returns:
            True if data is valid, False otherwise
        """
        required_fields = ['value', 'type']
        
        for field in required_fields:
            if field not in data or not data[field]:
                self.logger.debug(f"Missing required field '{field}' in indicator data")
                return False
        
        return True
    
    def _extract_tags(self, raw_data: Dict[str, Any]) -> List[str]:
        """
        Extract tags from raw indicator data
        
        Args:
            raw_data: Raw indicator data
            
        Returns:
            List of tags
        """
        tags = []
        
        # Common tag field names
        tag_fields = ['tags', 'labels', 'categories', 'malware_families']
        
        for field in tag_fields:
            if field in raw_data:
                field_data = raw_data[field]
                if isinstance(field_data, list):
                    tags.extend([str(tag) for tag in field_data])
                elif isinstance(field_data, str):
                    tags.append(field_data)
        
        # Remove duplicates and empty tags
        return list(set(tag for tag in tags if tag and tag.strip()))
    
    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """
        Parse datetime string with multiple format support
        
        Args:
            date_str: Date string to parse
            
        Returns:
            Parsed datetime or None if parsing fails
        """
        if not date_str:
            return None
        
        # Common datetime formats
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO format with microseconds
            '%Y-%m-%dT%H:%M:%SZ',     # ISO format
            '%Y-%m-%d %H:%M:%S',      # Standard format
            '%Y-%m-%d',               # Date only
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        self.logger.warning(f"Could not parse datetime: {date_str}")
        return None