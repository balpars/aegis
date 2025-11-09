"""HuggingFace adapter for Transformers models."""
import json
import time
from typing import Any, Dict, Optional
from aegis.adapters.base import AbstractAdapter
from aegis.models import ModelRequest, ModelResponse, HealthResponse, Finding


class HFAdapter(AbstractAdapter):
    """Adapter for HuggingFace Transformers models."""

    def __init__(
        self,
        model_id: str,
        task: str = "text-generation",
        cache_dir: Optional[str] = None,
        display_name: Optional[str] = None,
    ):
        adapter_id = f"hf:{model_id}"
        super().__init__(
            adapter_id=adapter_id,
            display_name=display_name or f"HF {model_id}",
            provider="hf",
            supports_stream=False,
            supports_json=True,
        )
        self.model_id = model_id
        self.task = task
        self.cache_dir = cache_dir
        self._model = None
        self._tokenizer = None

    def _load_model(self):
        """Lazy load the model and tokenizer."""
        if self._model is None:
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
                
                if self.task == "text-generation":
                    self._tokenizer = AutoTokenizer.from_pretrained(
                        self.model_id, cache_dir=self.cache_dir
                    )
                    self._model = AutoModelForCausalLM.from_pretrained(
                        self.model_id, cache_dir=self.cache_dir
                    )
                    self._pipeline = pipeline(
                        "text-generation",
                        model=self._model,
                        tokenizer=self._tokenizer,
                        device_map="auto",
                    )
                else:
                    # For other tasks, use pipeline directly
                    self._pipeline = pipeline(
                        self.task,
                        model=self.model_id,
                        cache_dir=self.cache_dir,
                    )
            except ImportError:
                raise ImportError(
                    "transformers library not installed. Install with: pip install transformers torch"
                )

    def predict(self, request: ModelRequest) -> ModelResponse:
        """Run prediction using HuggingFace model."""
        start_time = time.time()
        
        try:
            self._load_model()
            
            if self.task == "text-generation":
                # Generate text response
                prompt = request.code_context
                result = self._pipeline(
                    prompt,
                    max_new_tokens=512,
                    temperature=0.1,
                    do_sample=True,
                    return_full_text=False,
                )
                raw_response = result[0]["generated_text"]
            else:
                # For sequence classification, map labels to findings
                result = self._pipeline(request.code_context)
                raw_response = json.dumps(result)
            
            findings = self._parse_response(raw_response, request.file_path)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return ModelResponse(
                model_id=self.id,
                findings=findings,
                raw=raw_response,
                latency_ms=latency_ms,
            )

        except Exception as e:
            return ModelResponse(
                model_id=self.id,
                findings=[],
                error=f"HF prediction failed: {str(e)}",
                latency_ms=int((time.time() - start_time) * 1000),
            )

    def _parse_response(self, response_text: str, file_path: str) -> list[Finding]:
        """Parse response into Findings."""
        findings = []
        
        try:
            # Try to extract JSON
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start != -1 and json_end > 0:
                json_str = response_text[json_start:json_end]
                parsed = json.loads(json_str)
                
                if "findings" in parsed:
                    for finding_data in parsed["findings"]:
                        try:
                            finding = Finding(
                                name=finding_data.get("name", "Security Issue"),
                                severity=finding_data.get("severity", "medium"),
                                cwe=finding_data.get("cwe", "CWE-20"),
                                file=finding_data.get("file", file_path),
                                start_line=finding_data.get("start_line", 0),
                                end_line=finding_data.get("end_line", 0),
                                message=finding_data.get("message", ""),
                                confidence=finding_data.get("confidence", 0.5),
                                fingerprint=finding_data.get("fingerprint", ""),
                            )
                            findings.append(finding)
                        except Exception:
                            continue
        except Exception:
            pass
        
        return findings

    def health(self) -> HealthResponse:
        """Check HF adapter health."""
        try:
            self._load_model()
            return HealthResponse(
                healthy=True,
                message="HF adapter is healthy",
                details={"model_id": self.model_id, "task": self.task},
            )
        except Exception as e:
            return HealthResponse(
                healthy=False,
                message=f"HF adapter health check failed: {str(e)}",
            )

