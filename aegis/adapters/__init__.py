"""Model adapters for Aegis."""
from typing import Protocol, Literal
from aegis.models import ModelRequest, ModelResponse, HealthResponse


class BaseAdapter(Protocol):
    """Protocol for all model adapters."""
    id: str
    display_name: str
    provider: Literal["openai", "anthropic", "azure", "ollama", "hf", "classic", "rest"]
    supports_stream: bool
    supports_json: bool

    def predict(self, request: ModelRequest) -> ModelResponse:
        """Run prediction on the model."""
        ...

    def health(self) -> HealthResponse:
        """Check adapter health."""
        ...

