"""
LLM Service with dynamic provider selection
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

import openai
import google.generativeai as genai
import ollama
import litellm
from langsmith import traceable

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Configure LLM providers
if settings.langsmith_api_key and settings.langsmith_tracing:
    import langsmith
    langsmith.init(api_key=settings.langsmith_api_key, project=settings.langsmith_project)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self):
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
            self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            self.client = None
    
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens or 2000
        )
        
        return response.choices[0].message.content
    
    def is_available(self) -> bool:
        return settings.openai_api_key is not None


class GoogleProvider(LLMProvider):
    """Google Gemini provider"""
    
    def __init__(self):
        if settings.google_api_key:
            genai.configure(api_key=settings.google_api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
    
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        if not self.model:
            raise ValueError("Google API key not configured")
        
        # Combine system prompt and user prompt for Gemini
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = await asyncio.to_thread(
            self.model.generate_content,
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens or 2000
            )
        )
        
        return response.text
    
    def is_available(self) -> bool:
        return settings.google_api_key is not None


class OllamaProvider(LLMProvider):
    """Ollama local model provider"""
    
    def __init__(self):
        self.client = ollama.AsyncClient(host=settings.ollama_base_url)
    
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat(
                model="llama2",  # Default model, can be configured
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_ctx": max_tokens or 2000
                }
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise ValueError(f"Ollama service unavailable: {e}")
    
    def is_available(self) -> bool:
        try:
            # Test if Ollama service is running
            import requests
            response = requests.get(f"{settings.ollama_base_url}/api/version", timeout=5)
            return response.status_code == 200
        except:
            return False


class LiteLLMProvider(LLMProvider):
    """LiteLLM provider for unified API access"""
    
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await litellm.acompletion(
            model="gpt-3.5-turbo",  # Can be configured
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens or 2000
        )
        
        return response.choices[0].message.content
    
    def is_available(self) -> bool:
        return True  # LiteLLM handles availability internally


class LLMService:
    """Main LLM service with provider selection and fallback"""
    
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "google": GoogleProvider(),
            "ollama": OllamaProvider(),
            "litellm": LiteLLMProvider()
        }
        self.default_provider = settings.default_llm_provider
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return [name for name, provider in self.providers.items() if provider.is_available()]
    
    def select_provider(self, preferred_provider: Optional[str] = None) -> str:
        """Select the best available provider"""
        available = self.get_available_providers()
        
        if not available:
            raise ValueError("No LLM providers available")
        
        # Try preferred provider first
        if preferred_provider and preferred_provider in available:
            return preferred_provider
        
        # Try default provider
        if self.default_provider in available:
            return self.default_provider
        
        # Return first available
        return available[0]
    
    @traceable
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        preferred_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate response using the best available provider"""
        
        provider_name = self.select_provider(preferred_provider)
        provider = self.providers[provider_name]
        
        logger.info(f"Using {provider_name} provider for LLM request")
        
        try:
            response = await provider.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "response": response,
                "provider": provider_name,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error with {provider_name} provider: {e}")
            
            # Try fallback providers
            available = self.get_available_providers()
            for fallback_provider in available:
                if fallback_provider != provider_name:
                    try:
                        logger.info(f"Trying fallback provider: {fallback_provider}")
                        fallback = self.providers[fallback_provider]
                        response = await fallback.generate_response(
                            prompt=prompt,
                            system_prompt=system_prompt,
                            temperature=temperature,
                            max_tokens=max_tokens
                        )
                        
                        return {
                            "response": response,
                            "provider": fallback_provider,
                            "success": True,
                            "fallback_used": True
                        }
                    except Exception as fallback_error:
                        logger.error(f"Fallback {fallback_provider} failed: {fallback_error}")
                        continue
            
            # All providers failed
            raise ValueError(f"All LLM providers failed. Last error: {e}")


# Global LLM service instance
llm_service = LLMService()
