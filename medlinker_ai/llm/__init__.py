"""LLM provider abstraction for MedLinker AI."""

from medlinker_ai.llm.base import LLMClient
from medlinker_ai.llm.factory import get_llm_client

__all__ = ["LLMClient", "get_llm_client"]
