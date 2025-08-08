"""
Enhanced LLM Integration Service
Handles integration with various LLM providers for threat modeling analysis
"""

import logging
import os
from typing import Dict, Any, Optional, List, Union
from contextlib import asynccontextmanager

from .llm_providers import (
    OpenAIProvider, AnthropicProvider, BaseLLMProvider,
    LLMRequest, LLMResponse, LLMMessage, LLMModel,
    LLMError, RateLimitError, APIError, ModelNotFoundError
)

logger = logging.getLogger(__name__)


class EnhancedLLMService:
    """Enhanced service for managing LLM interactions across multiple providers"""
    
    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.default_models = {
            "openai": LLMModel.GPT_4O_MINI,
            "anthropic": LLMModel.CLAUDE_3_HAIKU,
        }
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available LLM providers"""
        
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                self.providers["openai"] = OpenAIProvider(api_key=openai_key)
                logger.info("✅ OpenAI provider initialized")
            except Exception as e:
                logger.warning(f"❌ Failed to initialize OpenAI provider: {e}")
        
        # Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                self.providers["anthropic"] = AnthropicProvider(api_key=anthropic_key)
                logger.info("✅ Anthropic provider initialized")
            except Exception as e:
                logger.warning(f"❌ Failed to initialize Anthropic provider: {e}")
        
        if not self.providers:
            logger.warning("⚠️ No LLM providers initialized. Set API keys in environment variables.")
        else:
            provider_names = ", ".join(self.providers.keys())
            logger.info(f"🚀 Initialized {len(self.providers)} LLM providers: {provider_names}")
    
    async def generate_completion(
        self,
        prompt: str,
        model: Optional[Union[str, LLMModel]] = None,
        provider: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using specified or best available provider"""
        
        if not self.providers:
            raise ValueError("No LLM providers available. Please configure API keys.")
        
        # Convert string model to enum if needed
        if isinstance(model, str):
            model = self._string_to_model(model)
        
        # Auto-select provider if not specified
        if not provider:
            provider = self._select_best_provider(model)
        
        if provider not in self.providers:
            available = ", ".join(self.providers.keys())
            raise ValueError(f"Provider '{provider}' not available. Available: {available}")
        
        # Auto-select model if not specified
        if not model:
            model = self.default_models.get(provider, LLMModel.GPT_4O_MINI)
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))
        messages.append(LLMMessage(role="user", content=prompt))
        
        # Create request
        request = LLMRequest(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        try:
            provider_instance = self.providers[provider]
            logger.info(f"🤖 Generating completion: {provider}/{model.value}")
            
            response = await provider_instance.generate(request)
            
            logger.info(
                f"✅ Completion generated: {response.token_usage.total if response.token_usage else 'unknown'} tokens, "
                f"${response.token_usage.estimated_cost:.4f} cost, {response.response_time:.2f}s"
            )
            
            return response
            
        except (RateLimitError, APIError, ModelNotFoundError) as e:
            logger.error(f"❌ LLM request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"💥 Unexpected error in LLM service: {e}", exc_info=True)
            raise LLMError(f"LLM service error: {str(e)}")
    
    async def generate_structured_completion(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        model: Optional[Union[str, LLMModel]] = None,
        provider: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate structured completion with JSON schema validation"""
        
        # Add JSON format instruction to system prompt
        schema_instruction = f"""
You must respond with valid JSON that matches this schema:
{response_schema}

Ensure your response is properly formatted JSON only, no additional text."""
        
        if system_prompt:
            system_prompt = system_prompt + "\n\n" + schema_instruction
        else:
            system_prompt = schema_instruction
        
        # Use JSON response format if provider supports it
        if "response_format" not in kwargs:
            kwargs["response_format"] = {"type": "json_object"}
        
        return await self.generate_completion(
            prompt=prompt,
            model=model,
            provider=provider,
            system_prompt=system_prompt,
            **kwargs
        )
    
    def _string_to_model(self, model_string: str) -> LLMModel:
        """Convert string model name to LLMModel enum"""
        # Try direct match first
        for model in LLMModel:
            if model.value == model_string:
                return model
        
        # Try partial matches
        model_lower = model_string.lower()
        if "gpt-4o-mini" in model_lower:
            return LLMModel.GPT_4O_MINI
        elif "gpt-4o" in model_lower:
            return LLMModel.GPT_4O
        elif "gpt-4" in model_lower:
            return LLMModel.GPT_4_TURBO
        elif "claude-3-5" in model_lower or "claude-3.5" in model_lower:
            return LLMModel.CLAUDE_3_5_SONNET
        elif "claude" in model_lower:
            return LLMModel.CLAUDE_3_HAIKU
        elif "gemini-1.5-pro" in model_lower:
            return LLMModel.GEMINI_1_5_PRO
        elif "gemini" in model_lower:
            return LLMModel.GEMINI_1_5_FLASH
        
        # Default fallback
        logger.warning(f"Unknown model '{model_string}', using GPT-4o-mini as fallback")
        return LLMModel.GPT_4O_MINI
    
    def _select_best_provider(self, model: Optional[LLMModel] = None) -> str:
        """Select the best available provider for the given model"""
        if not model:
            # Return first available provider
            return list(self.providers.keys())[0]
        
        # Find provider that supports the model
        for provider_name, provider in self.providers.items():
            if provider.is_model_supported(model):
                return provider_name
        
        # No provider supports this model, return first available
        available_providers = list(self.providers.keys())
        logger.warning(
            f"Model {model.value} not supported by any provider. Using {available_providers[0]}"
        )
        return available_providers[0]
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self.providers.keys())
    
    def get_available_models(self, provider: Optional[str] = None) -> List[str]:
        """Get list of available models for a provider or all providers"""
        if provider:
            if provider not in self.providers:
                return []
            provider_instance = self.providers[provider]
            return [model.value for model in provider_instance._get_supported_models()]
        
        # Return all models from all providers
        all_models = set()
        for provider_instance in self.providers.values():
            for model in provider_instance._get_supported_models():
                all_models.add(model.value)
        return sorted(list(all_models))
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about all providers"""
        info = {
            "total_providers": len(self.providers),
            "providers": {}
        }
        
        for name, provider in self.providers.items():
            info["providers"][name] = provider.get_provider_info()
        
        return info
    
    @asynccontextmanager
    async def get_provider(self, provider_name: str):
        """Get provider instance as async context manager"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not available")
        
        provider = self.providers[provider_name]
        try:
            yield provider
        finally:
            # Any cleanup if needed
            pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all providers"""
        health_status = {
            "healthy": True,
            "total_providers": len(self.providers),
            "providers": {}
        }
        
        if not self.providers:
            health_status["healthy"] = False
            health_status["error"] = "No providers available"
            return health_status
        
        # Test each provider with a simple request
        for name, provider in self.providers.items():
            try:
                # Use the cheapest/fastest model for health check
                test_model = (
                    LLMModel.GPT_4O_MINI if name == "openai" 
                    else LLMModel.CLAUDE_3_HAIKU if name == "anthropic"
                    else provider._get_supported_models()[0]
                )
                
                test_request = LLMRequest(
                    messages=[LLMMessage(role="user", content="Hi")],
                    model=test_model,
                    max_tokens=5
                )
                
                response = await provider.generate(test_request)
                health_status["providers"][name] = {
                    "healthy": True,
                    "response_time": response.response_time,
                    "model": response.model
                }
                
            except Exception as e:
                health_status["healthy"] = False
                health_status["providers"][name] = {
                    "healthy": False,
                    "error": str(e)
                }
        
        return health_status


# Global service instance
_llm_service: Optional[EnhancedLLMService] = None


def get_enhanced_llm_service() -> EnhancedLLMService:
    """Get or create global LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = EnhancedLLMService()
    return _llm_service
