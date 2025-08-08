"""
OpenAI Provider Implementation
Supports GPT-4, GPT-4o, and other OpenAI models
"""

import json
import logging
from typing import List, Optional, Dict, Any
import httpx

from .base import (
    BaseLLMProvider, LLMRequest, LLMResponse, LLMMessage, LLMModel, 
    TokenUsage, APIError, RateLimitError, ModelNotFoundError
)

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider implementation"""
    
    BASE_URL = "https://api.openai.com/v1"
    
    # Cost per 1K tokens (as of 2024) - Update these regularly
    MODEL_COSTS = {
        LLMModel.GPT_4O: {"input": 0.005, "output": 0.015},  # $5/$15 per 1M tokens
        LLMModel.GPT_4O_MINI: {"input": 0.00015, "output": 0.0006},  # $0.15/$0.6 per 1M tokens
        LLMModel.GPT_4_TURBO: {"input": 0.01, "output": 0.03},  # $10/$30 per 1M tokens
    }
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        if not api_key:
            raise ValueError("OpenAI API key is required")
        super().__init__(api_key, **kwargs)
    
    def _setup_client(self) -> None:
        """Initialize the OpenAI HTTP client"""
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AITM/1.0"
        }
        
        # Configure HTTP client with timeouts and retries
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, read=60.0),  # 30s connect, 60s read
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    def _get_supported_models(self) -> List[LLMModel]:
        """Return OpenAI models supported by this provider"""
        return [
            LLMModel.GPT_4O,
            LLMModel.GPT_4O_MINI, 
            LLMModel.GPT_4_TURBO
        ]
    
    def _estimate_cost(self, model: LLMModel, token_usage: TokenUsage) -> float:
        """Estimate cost for OpenAI model usage"""
        if model not in self.MODEL_COSTS:
            return 0.0
        
        costs = self.MODEL_COSTS[model]
        input_cost = (token_usage.prompt_tokens / 1000) * costs["input"]
        output_cost = (token_usage.completion_tokens / 1000) * costs["output"]
        
        return input_cost + output_cost
    
    def _format_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """Convert internal message format to OpenAI format"""
        formatted = []
        for msg in messages:
            formatted_msg = {
                "role": msg.role,
                "content": msg.content
            }
            if msg.name:
                formatted_msg["name"] = msg.name
            formatted.append(formatted_msg)
        return formatted
    
    async def _make_request(self, request: LLMRequest) -> LLMResponse:
        """Make request to OpenAI API"""
        self.validate_request(request)
        
        # Build request payload
        payload = {
            "model": request.model.value,
            "messages": self._format_messages(request.messages),
            "temperature": request.temperature,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
        }
        
        # Add optional parameters
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        if request.stop:
            payload["stop"] = request.stop
        if request.response_format:
            payload["response_format"] = request.response_format
        if request.tools:
            payload["tools"] = request.tools
        if request.tool_choice:
            payload["tool_choice"] = request.tool_choice
        
        try:
            response = await self.client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60.0
            )
            
            # Handle different response status codes
            if response.status_code == 429:
                retry_after = response.headers.get("retry-after")
                retry_after = int(retry_after) if retry_after else None
                raise RateLimitError(retry_after)
            
            if response.status_code == 404:
                raise ModelNotFoundError(f"Model {request.model.value} not found")
            
            if response.status_code >= 400:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                raise APIError(f"OpenAI API error: {error_msg}")
            
            response.raise_for_status()
            data = response.json()
            
            # Parse response
            choice = data["choices"][0]
            content = choice["message"]["content"] or ""
            finish_reason = choice.get("finish_reason")
            
            # Parse usage information
            usage_data = data.get("usage", {})
            token_usage = TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0)
            )
            
            # Handle tool calls if present
            tool_calls = None
            message = choice.get("message", {})
            if message.get("tool_calls"):
                tool_calls = message["tool_calls"]
            
            return LLMResponse(
                content=content,
                model=data.get("model", request.model.value),
                finish_reason=finish_reason,
                token_usage=token_usage,
                tool_calls=tool_calls,
                metadata={
                    "id": data.get("id"),
                    "created": data.get("created"),
                    "system_fingerprint": data.get("system_fingerprint")
                }
            )
            
        except httpx.RequestError as e:
            raise APIError(f"OpenAI request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise APIError(f"Invalid JSON response from OpenAI: {str(e)}")
        except KeyError as e:
            raise APIError(f"Unexpected response format from OpenAI: {str(e)}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.client.aclose()
    
    def __del__(self):
        """Cleanup when provider is destroyed"""
        try:
            import asyncio
            # Try to close the client if event loop is running
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.client.aclose())
            except RuntimeError:
                # No event loop running, can't close gracefully
                pass
        except:
            # Ignore cleanup errors
            pass
