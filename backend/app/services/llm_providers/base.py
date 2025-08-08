"""
Base LLM Provider Interface
Abstract base class for all LLM providers in AITM system
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
import time
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class LLMModel(Enum):
    """Supported LLM models"""
    # OpenAI Models
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"
    
    # Anthropic Models
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    
    # Google Models
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    
    # Ollama Models (Local)
    LLAMA_3_1 = "llama3.1"
    MISTRAL = "mistral"


@dataclass
class TokenUsage:
    """Token usage statistics"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    
    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class LLMMessage:
    """Standard message format for all providers"""
    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None


@dataclass
class LLMRequest:
    """Standard request format for all providers"""
    messages: List[LLMMessage]
    model: LLMModel
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[Union[str, List[str]]] = None
    response_format: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None


@dataclass 
class LLMResponse:
    """Standard response format from all providers"""
    content: str
    model: str
    finish_reason: Optional[str] = None
    token_usage: Optional[TokenUsage] = None
    response_time: float = 0.0
    provider: str = ""
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMError(Exception):
    """Base exception for LLM provider errors"""
    pass


class RateLimitError(LLMError):
    """Rate limit exceeded"""
    def __init__(self, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after: {retry_after}s")


class APIError(LLMError):
    """API related errors"""
    pass


class ModelNotFoundError(LLMError):
    """Model not available or not found"""
    pass


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers"""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.provider_name = self.__class__.__name__.replace('Provider', '').lower()
        self.config = kwargs
        self._setup_client()
    
    @abstractmethod
    def _setup_client(self) -> None:
        """Initialize the provider-specific client"""
        pass
    
    @abstractmethod
    async def _make_request(self, request: LLMRequest) -> LLMResponse:
        """Make the actual API request to the provider"""
        pass
    
    @abstractmethod
    def _get_supported_models(self) -> List[LLMModel]:
        """Return list of models supported by this provider"""
        pass
    
    @abstractmethod
    def _estimate_cost(self, model: LLMModel, token_usage: TokenUsage) -> float:
        """Estimate the cost for the given model and token usage"""
        pass
    
    def is_model_supported(self, model: LLMModel) -> bool:
        """Check if the model is supported by this provider"""
        return model in self._get_supported_models()
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Main entry point for generating completions
        Includes retry logic and error handling
        """
        if not self.is_model_supported(request.model):
            raise ModelNotFoundError(f"Model {request.model.value} not supported by {self.provider_name}")
        
        # Track timing
        start_time = time.time()
        
        try:
            # Make the request with retry logic
            response = await self._make_request_with_retry(request)
            response.response_time = time.time() - start_time
            response.provider = self.provider_name
            
            # Estimate cost if token usage is available
            if response.token_usage:
                response.token_usage.estimated_cost = self._estimate_cost(
                    request.model, response.token_usage
                )
            
            logger.info(
                f"LLM request completed: {self.provider_name}, "
                f"model={request.model.value}, "
                f"tokens={response.token_usage.total if response.token_usage else 'unknown'}, "
                f"time={response.response_time:.2f}s"
            )
            
            return response
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"LLM request failed: {self.provider_name}, "
                f"model={request.model.value}, "
                f"error={str(e)}, "
                f"time={elapsed:.2f}s"
            )
            raise
    
    async def _make_request_with_retry(
        self, 
        request: LLMRequest, 
        max_retries: int = 3,
        base_delay: float = 1.0
    ) -> LLMResponse:
        """Make request with exponential backoff retry logic"""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await self._make_request(request)
                
            except RateLimitError as e:
                if attempt == max_retries:
                    raise
                    
                # Use the retry_after from the error, or exponential backoff
                delay = e.retry_after if e.retry_after else base_delay * (2 ** attempt)
                logger.warning(
                    f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{max_retries + 1})"
                )
                await self._sleep(delay)
                last_exception = e
                
            except (APIError, Exception) as e:
                if attempt == max_retries:
                    raise
                    
                # Exponential backoff for other errors
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"Request failed, retrying in {delay}s (attempt {attempt + 1}/{max_retries + 1}): {e}"
                )
                await self._sleep(delay)
                last_exception = e
        
        # This shouldn't be reached, but just in case
        if last_exception:
            raise last_exception
    
    async def _sleep(self, seconds: float) -> None:
        """Async sleep utility"""
        import asyncio
        await asyncio.sleep(seconds)
    
    def validate_request(self, request: LLMRequest) -> None:
        """Validate the request parameters"""
        if not request.messages:
            raise ValueError("Messages cannot be empty")
        
        if not 0.0 <= request.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        if request.max_tokens and request.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        
        if not 0.0 <= request.top_p <= 1.0:
            raise ValueError("top_p must be between 0.0 and 1.0")
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about this provider"""
        return {
            "name": self.provider_name,
            "supported_models": [model.value for model in self._get_supported_models()],
            "config": {k: v for k, v in self.config.items() if k != 'api_key'}
        }
