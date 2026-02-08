"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract interface for LLM providers."""
    
    @abstractmethod
    def extract(self, prompt: str) -> str:
        """Extract structured data from prompt.
        
        Args:
            prompt: The extraction prompt containing source text and instructions.
            
        Returns:
            JSON string response from the LLM.
            
        Raises:
            Exception: If the LLM call fails.
        """
        pass
