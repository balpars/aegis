"""Base adapter implementation."""
from abc import ABC, abstractmethod
from typing import Literal
from aegis.models import ModelRequest, ModelResponse, HealthResponse


class AbstractAdapter(ABC):
    """Abstract base class for model adapters."""
    
    def __init__(
        self,
        adapter_id: str,
        display_name: str,
        provider: Literal["openai", "anthropic", "azure", "ollama", "hf", "classic", "rest"],
        supports_stream: bool = False,
        supports_json: bool = True,
    ):
        self.id = adapter_id
        self.display_name = display_name
        self.provider = provider
        self.supports_stream = supports_stream
        self.supports_json = supports_json

    @abstractmethod
    def predict(self, request: ModelRequest) -> ModelResponse:
        """Run prediction on the model."""
        pass

    @abstractmethod
    def health(self) -> HealthResponse:
        """Check adapter health."""
        pass

    def to_dict(self) -> dict:
        """Convert adapter to dictionary."""
        return {
            "id": self.id,
            "display_name": self.display_name,
            "provider": self.provider,
            "supports_stream": self.supports_stream,
            "supports_json": self.supports_json,
        }

