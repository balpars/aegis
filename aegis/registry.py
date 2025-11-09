"""Model registry for managing adapters."""
import json
import requests
from typing import Dict, List, Optional, Any
from pathlib import Path
from aegis.adapters.base import AbstractAdapter
from aegis.adapters.ollama_adapter import OllamaAdapter
from aegis.adapters.llm_adapter import LLMAdapter
from aegis.adapters.hf_adapter import HFAdapter
from aegis.adapters.classic_adapter import ClassicAdapter


class ModelRegistry:
    """Registry for managing model adapters."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize model registry."""
        if config_path is None:
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "models.yaml"
        
        self.config_path = Path(config_path)
        self._adapters: Dict[str, AbstractAdapter] = {}
        self._load_config()

    def _load_config(self):
        """Load model configuration."""
        # For now, just initialize with defaults
        # In production, load from YAML
        pass

    def register(self, adapter: AbstractAdapter):
        """Register an adapter."""
        self._adapters[adapter.id] = adapter

    def get(self, adapter_id: str) -> Optional[AbstractAdapter]:
        """Get adapter by ID."""
        return self._adapters.get(adapter_id)

    def list_all(self) -> List[Dict[str, Any]]:
        """List all registered adapters."""
        return [adapter.to_dict() for adapter in self._adapters.values()]

    def list_by_provider(self, provider: str) -> List[Dict[str, Any]]:
        """List adapters by provider."""
        return [
            adapter.to_dict()
            for adapter in self._adapters.values()
            if adapter.provider == provider
        ]

    def discover_ollama_models(self, base_url: str = "http://localhost:11434") -> List[Dict[str, Any]]:
        """Discover installed Ollama models."""
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            models = []
            for model_info in data.get("models", []):
                model_name = model_info.get("name", "")
                models.append({
                    "name": model_name,
                    "id": f"ollama:{model_name}",
                    "size": model_info.get("size", 0),
                    "modified": model_info.get("modified_at", ""),
                })
            return models
        except Exception:
            return []

    def pull_ollama_model(
        self, model_name: str, base_url: str = "http://localhost:11434"
    ) -> Dict[str, Any]:
        """Pull an Ollama model."""
        try:
            response = requests.post(
                f"{base_url}/api/pull",
                json={"name": model_name},
                timeout=300,  # Long timeout for model downloads
                stream=True,
            )
            response.raise_for_status()
            
            # Stream progress
            progress_data = []
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        progress_data.append(data)
                    except json.JSONDecodeError:
                        continue
            
            return {
                "success": True,
                "model_name": model_name,
                "progress": progress_data,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def create_ollama_adapter(
        self, model_name: str, base_url: str = "http://localhost:11434"
    ) -> OllamaAdapter:
        """Create and register an Ollama adapter."""
        adapter = OllamaAdapter(model_name=model_name, base_url=base_url)
        self.register(adapter)
        return adapter

    def create_llm_adapter(
        self,
        provider: str,
        model_name: str,
        api_key: str,
        api_base: Optional[str] = None,
    ) -> LLMAdapter:
        """Create and register an LLM adapter."""
        adapter = LLMAdapter(
            provider=provider,
            model_name=model_name,
            api_key=api_key,
            api_base=api_base,
        )
        self.register(adapter)
        return adapter

    def create_hf_adapter(
        self,
        model_id: str,
        task: str = "text-generation",
        cache_dir: Optional[str] = None,
    ) -> HFAdapter:
        """Create and register a HuggingFace adapter."""
        adapter = HFAdapter(
            model_id=model_id,
            task=task,
            cache_dir=cache_dir,
        )
        self.register(adapter)
        return adapter

    def create_classic_adapter(
        self,
        model_path: str,
        model_type: str = "sklearn",
    ) -> ClassicAdapter:
        """Create and register a classic ML adapter."""
        adapter = ClassicAdapter(
            model_path=model_path,
            model_type=model_type,
        )
        self.register(adapter)
        return adapter

    def remove(self, adapter_id: str) -> bool:
        """Remove an adapter."""
        if adapter_id in self._adapters:
            del self._adapters[adapter_id]
            return True
        return False

