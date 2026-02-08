"""OpenAI LLM provider implementation."""

import os
import json
from typing import Optional

from medlinker_ai.llm.base import LLMClient


class OpenAIClient(LLMClient):
    """OpenAI API client for capability extraction."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var).
            model: Model name (defaults to OPENAI_MODEL env var or "gpt-4o-mini").
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable or api_key parameter required")
        
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # Import OpenAI SDK
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "openai package required for OpenAI provider. "
                "Install with: pip install openai"
            )
    
    def extract(self, prompt: str) -> str:
        """Extract structured data using OpenAI API.
        
        Args:
            prompt: The extraction prompt.
            
        Returns:
            JSON string response from OpenAI.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a healthcare data extraction assistant. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            # If JSON parsing fails, try one retry with clarification
            if "json" in str(e).lower() or "parse" in str(e).lower():
                retry_prompt = (
                    f"{prompt}\n\n"
                    "IMPORTANT: Your previous response had JSON formatting issues. "
                    "Please return ONLY valid JSON with no markdown formatting, "
                    "no code blocks, and no extra text."
                )
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a healthcare data extraction assistant. Return only valid JSON."
                        },
                        {
                            "role": "user",
                            "content": retry_prompt
                        }
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content
            raise
