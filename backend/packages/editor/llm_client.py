"""
LLM client abstraction for brief synthesis
Supports multiple providers: Claude, Ollama, OpenAI, etc.
"""
import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """
    Abstract base class for LLM clients.
    All LLM providers must implement this interface.
    """
    
    def __init__(self, model: Optional[str] = None, **kwargs):
        """
        Initialize LLM client.
        
        Args:
            model: Model name/identifier
            **kwargs: Provider-specific configuration
        """
        self.model = model
        self.config = kwargs
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            **kwargs: Provider-specific parameters
            
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this LLM client is available/configured"""
        pass


class ClaudeClient(LLMClient):
    """Claude API client via Anthropic SDK"""
    
    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize Claude client.
        
        Args:
            model: Claude model (default: claude-3-sonnet-20240229)
            api_key: Anthropic API key (default: from ANTHROPIC_API_KEY env)
        """
        super().__init__(model or "claude-3-sonnet-20240229")
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._client = None
    
    def is_available(self) -> bool:
        """Check if Claude API key is configured"""
        return bool(self.api_key)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text using Claude API"""
        if not self.is_available():
            raise RuntimeError("Claude API key not configured")
        
        try:
            from anthropic import Anthropic
            
            if not self._client:
                self._client = Anthropic(api_key=self.api_key)
            
            messages = [{"role": "user", "content": prompt}]
            
            response = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt if system_prompt else "",
                messages=messages,
                **kwargs
            )
            
            return response.content[0].text
            
        except Exception as e:
            raise RuntimeError(f"Claude API error: {e}")


class OllamaClient(LLMClient):
    """Ollama local LLM client"""
    
    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize Ollama client.
        
        Args:
            model: Ollama model (default: llama3.2)
            base_url: Ollama API URL (default: http://localhost:11434)
        """
        super().__init__(model or "llama3.2")
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    def is_available(self) -> bool:
        """Check if Ollama is accessible"""
        try:
            import httpx
            response = httpx.get(f"{self.base_url}/api/tags", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text using Ollama API"""
        if not self.is_available():
            raise RuntimeError("Ollama not available at " + self.base_url)
        
        try:
            import httpx
            
            # Combine system and user prompts
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
                
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}")


class OpenAIClient(LLMClient):
    """OpenAI API client"""
    
    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize OpenAI client.
        
        Args:
            model: OpenAI model (default: gpt-4)
            api_key: OpenAI API key (default: from OPENAI_API_KEY env)
        """
        super().__init__(model or "gpt-4")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None
    
    def is_available(self) -> bool:
        """Check if OpenAI API key is configured"""
        return bool(self.api_key)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text using OpenAI API"""
        if not self.is_available():
            raise RuntimeError("OpenAI API key not configured")
        
        try:
            from openai import AsyncOpenAI
            
            if not self._client:
                self._client = AsyncOpenAI(api_key=self.api_key)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")


def get_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> LLMClient:
    """
    Get an LLM client based on provider preference.
    
    Args:
        provider: Provider name (claude, ollama, openai) or None for auto-detect
        model: Model name (provider-specific)
        **kwargs: Provider-specific configuration
        
    Returns:
        Configured LLM client
        
    Raises:
        RuntimeError: If no available LLM provider found
    """
    provider = provider or os.getenv("LLM_PROVIDER", "").lower()
    
    # Try specified provider first
    if provider == "claude":
        client = ClaudeClient(model=model, **kwargs)
        if client.is_available():
            return client
    elif provider == "ollama":
        client = OllamaClient(model=model, **kwargs)
        if client.is_available():
            return client
    elif provider == "openai":
        client = OpenAIClient(model=model, **kwargs)
        if client.is_available():
            return client
    
    # Auto-detect available provider
    logger.info(f"Provider '{provider}' not available or not specified, trying auto-detect...")
    
    # Try Ollama (local, no API key needed)
    try:
        client = OllamaClient(model=model)
        if client.is_available():
            logger.info("✅ Using Ollama (local)")
            return client
    except Exception:
        pass
    
    # Try Claude
    try:
        client = ClaudeClient(model=model)
        if client.is_available():
            logger.info("✅ Using Claude API")
            return client
    except Exception:
        pass
    
    # Try OpenAI
    try:
        client = OpenAIClient(model=model)
        if client.is_available():
            logger.info("✅ Using OpenAI API")
            return client
    except Exception:
        pass
    
    raise RuntimeError(
        "No LLM provider available. Please configure:\n"
        "  - Ollama (local): Install and run `ollama serve`\n"
        "  - Claude: Set ANTHROPIC_API_KEY environment variable\n"
        "  - OpenAI: Set OPENAI_API_KEY environment variable"
    )
