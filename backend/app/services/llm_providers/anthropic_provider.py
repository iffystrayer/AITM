"""
Anthropic Provider Implementation
Supports Claude 3.5 Sonnet, Claude 3 Haiku and other Anthropic models
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


class AnthropicProvider(BaseLLMProvider):
    """Anthropic API provider implementation"""
    
    BASE_URL = "https://api.anthropic.com/v1"
    API_VERSION = "2023-06-01"
    
    # Cost per 1K tokens (as of 2024)
    MODEL_COSTS = {
        LLMModel.CLAUDE_3_5_SONNET: {"input": 0.003, "output": 0.015},  # $3/$15 per 1M tokens
        LLMModel.CLAUDE_3_HAIKU: {"input": 0.00025, "output": 0.00125},  # $0.25/$1.25 per 1M tokens
    }
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        if not api_key:
            raise ValueError("Anthropic API key is required")
        super().__init__(api_key, **kwargs)
    
    def _setup_client(self) -> None:
        """Initialize the Anthropic HTTP client"""
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION,
            "Content-Type": "application/json",
            "User-Agent": "AITM/1.0"
        }
        
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, read=60.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    def _get_supported_models(self) -> List[LLMModel]:
        """Return Anthropic models supported by this provider"""
        return [
            LLMModel.CLAUDE_3_5_SONNET,
            LLMModel.CLAUDE_3_HAIKU
        ]
    
    def _estimate_cost(self, model: LLMModel, token_usage: TokenUsage) -> float:
        """Estimate cost for Anthropic model usage"""
        if model not in self.MODEL_COSTS:
            return 0.0
        
        costs = self.MODEL_COSTS[model]
        input_cost = (token_usage.prompt_tokens / 1000) * costs["input"]
        output_cost = (token_usage.completion_tokens / 1000) * costs["output"]
        
        return input_cost + output_cost
    
    def _format_messages(self, messages: List[LLMMessage]) -> tuple[str, List[Dict[str, Any]]]:
        """
        Convert internal message format to Anthropic format
        Anthropic expects system message separate from conversation messages
        """
        system_message = ""
        conversation_messages = []
        
        for msg in messages:
            if msg.role == "system":
                # Combine all system messages
                if system_message:
                    system_message += "\n\n" + msg.content
                else:
                    system_message = msg.content
            else:
                conversation_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        return system_message, conversation_messages
    
    async def _make_request(self, request: LLMRequest) -> LLMResponse:
        """Make request to Anthropic API"""
        self.validate_request(request)
        
        # Format messages for Anthropic API
        system_message, messages = self._format_messages(request.messages)
        
        # Build request payload
        payload = {
            "model": request.model.value,
            "messages": messages,
            "temperature": request.temperature,
            "top_p": request.top_p,
        }
        
        # Add system message if present
        if system_message:
            payload["system"] = system_message
        
        # Add optional parameters
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        else:
            # Anthropic requires max_tokens
            payload["max_tokens"] = 4096
        
        if request.stop:
            payload["stop_sequences"] = request.stop if isinstance(request.stop, list) else [request.stop]
        
        try:
            response = await self.client.post(
                f"{self.BASE_URL}/messages",
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
                raise APIError(f"Anthropic API error: {error_msg}")
            
            response.raise_for_status()
            data = response.json()
            
            # Parse response - Anthropic has different response format
            content_blocks = data.get("content", [])
            content = ""
            
            # Combine all text content blocks
            for block in content_blocks:
                if block.get("type") == "text":
                    content += block.get("text", "")
            
            finish_reason = data.get("stop_reason")
            
            # Parse usage information
            usage_data = data.get("usage", {})
            token_usage = TokenUsage(
                prompt_tokens=usage_data.get("input_tokens", 0),
                completion_tokens=usage_data.get("output_tokens", 0),
                total_tokens=usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0)
            )
            
            return LLMResponse(
                content=content,
                model=data.get("model", request.model.value),
                finish_reason=finish_reason,
                token_usage=token_usage,
                metadata={
                    "id": data.get("id"),
                    "type": data.get("type"),
                    "role": data.get("role"),
                    "stop_sequence": data.get("stop_sequence")
                }
            )
            
        except httpx.RequestError as e:
            raise APIError(f"Anthropic request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise APIError(f"Invalid JSON response from Anthropic: {str(e)}")
        except KeyError as e:
            raise APIError(f"Unexpected response format from Anthropic: {str(e)}")
    
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
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.client.aclose())
            except RuntimeError:
                pass
        except:
            pass
