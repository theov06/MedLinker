"""Factory for creating LLM clients based on configuration."""

import os
from typing import Optional

from medlinker_ai.llm.base import LLMClient
from medlinker_ai.llm.fallback import FallbackClient


def get_llm_client(provider: Optional[str] = None) -> LLMClient:
    """Get LLM client based on provider configuration.
    
    Args:
        provider: LLM provider name ("gemini", "openai", "none").
                 Defaults to LLM_PROVIDER env var or "gemini".
    
    Returns:
        Configured LLM client instance.
        
    Raises:
        ValueError: If provider is unknown or required credentials are missing.
    """
    provider = provider or os.getenv("LLM_PROVIDER", "gemini")
    provider = provider.lower()
    
    if provider == "none":
        return FallbackClient()
    
    elif provider == "gemini":
        # Check if API key is available
        if not os.getenv("GEMINI_API_KEY"):
            # Fall back to offline mode
            return FallbackClient()
        
        try:
            from medlinker_ai.llm.gemini import GeminiClient
            return GeminiClient()
        except (ImportError, ValueError):
            # Fall back if SDK not installed or key missing
            return FallbackClient()
    
    elif provider == "openai":
        # Check if API key is available
        if not os.getenv("OPENAI_API_KEY"):
            # Fall back to offline mode
            return FallbackClient()
        
        try:
            from medlinker_ai.llm.openai import OpenAIClient
            return OpenAIClient()
        except (ImportError, ValueError):
            # Fall back if SDK not installed or key missing
            return FallbackClient()
    
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            f"Valid options: 'gemini', 'openai', 'none'"
        )
