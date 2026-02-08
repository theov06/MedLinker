"""Gemini LLM provider implementation."""

import os
from typing import Optional

from medlinker_ai.llm.base import LLMClient


class GeminiClient(LLMClient):
    """Gemini API client for capability extraction with strict JSON enforcement."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var).
            model: Model name (defaults to GEMINI_MODEL env var or "gemini-1.5-flash").
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable or api_key parameter required")
        
        # Try different model names (API has changed)
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-pro")
        
        # Import Gemini SDK
        try:
            import google.generativeai as genai
            self.genai = genai
            self.genai.configure(api_key=self.api_key)
            self.client = self.genai.GenerativeModel(self.model)
        except ImportError:
            raise ImportError(
                "google-generativeai package required for Gemini provider. "
                "Install with: pip install google-generativeai"
            )
    
    def extract(self, prompt: str) -> str:
        """Extract structured data using Gemini API with strict JSON output.
        
        Args:
            prompt: The extraction prompt with strict JSON requirements.
            
        Returns:
            Raw JSON string response from Gemini (not parsed).
            
        Raises:
            Exception: If the API call fails.
        """
        response = self.client.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,
                "response_mime_type": "application/json"
            }
        )
        return response.text
