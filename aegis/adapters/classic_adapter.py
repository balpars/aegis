"""Classic ML adapter for scikit-learn/ONNX models."""
import json
import time
import hashlib
from typing import Any, Dict, Optional
from pathlib import Path
from aegis.adapters.base import AbstractAdapter
from aegis.models import ModelRequest, ModelResponse, HealthResponse, Finding


class ClassicAdapter(AbstractAdapter):
    """Adapter for classic ML models (scikit-learn, ONNX, etc.)."""

    def __init__(
        self,
        model_path: str,
        model_type: str = "sklearn",
        display_name: Optional[str] = None,
    ):
        model_name = Path(model_path).stem
        adapter_id = f"classic:{model_name}"
        super().__init__(
            adapter_id=adapter_id,
            display_name=display_name or f"Classic {model_name}",
            provider="classic",
            supports_stream=False,
            supports_json=False,
        )
        self.model_path = model_path
        self.model_type = model_type
        self._model = None

    def _load_model(self):
        """Lazy load the model."""
        if self._model is None:
            if self.model_type == "sklearn":
                import pickle
                with open(self.model_path, "rb") as f:
                    self._model = pickle.load(f)
            elif self.model_type == "onnx":
                import onnxruntime as ort
                self._model = ort.InferenceSession(self.model_path)
            else:
                raise ValueError(f"Unsupported model type: {self.model_type}")

    def _extract_features(self, code: str) -> list[float]:
        """Extract features from code for ML model."""
        # Simple feature extraction: token n-grams, length, etc.
        # This is a placeholder - real implementation would use proper tokenization
        features = [
            len(code),
            code.count("eval("),
            code.count("exec("),
            code.count("input("),
            code.count("sql"),
            code.count("password"),
            code.count("secret"),
            code.count("token"),
            code.count("api_key"),
            code.count("http://"),
            code.count("https://"),
        ]
        return features

    def predict(self, request: ModelRequest) -> ModelResponse:
        """Run prediction using classic ML model."""
        start_time = time.time()
        
        try:
            self._load_model()
            
            # Extract features
            features = self._extract_features(request.code_context)
            
            # Run prediction
            if self.model_type == "sklearn":
                # Assume model outputs probabilities or labels
                prediction = self._model.predict_proba([features])[0]
                # Map to findings (simplified)
                findings = self._map_prediction_to_findings(
                    prediction, request.file_path, request.code_context
                )
            elif self.model_type == "onnx":
                # ONNX inference
                input_name = self._model.get_inputs()[0].name
                output = self._model.run(None, {input_name: [features]})
                findings = self._map_prediction_to_findings(
                    output[0][0], request.file_path, request.code_context
                )
            else:
                findings = []
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return ModelResponse(
                model_id=self.id,
                findings=findings,
                raw={"features": features},
                latency_ms=latency_ms,
            )

        except Exception as e:
            return ModelResponse(
                model_id=self.id,
                findings=[],
                error=f"Classic ML prediction failed: {str(e)}",
                latency_ms=int((time.time() - start_time) * 1000),
            )

    def _map_prediction_to_findings(
        self, prediction: Any, file_path: str, code: str
    ) -> list[Finding]:
        """Map ML model prediction to Findings."""
        findings = []
        
        # Simple mapping: if prediction indicates vulnerability, create finding
        # This is a placeholder - real implementation would be more sophisticated
        if isinstance(prediction, (list, tuple)) and len(prediction) > 0:
            # Assume first element is vulnerability probability
            prob = float(prediction[0]) if isinstance(prediction[0], (int, float)) else 0.5
            
            if prob > 0.5:
                # Generate fingerprint
                fingerprint = hashlib.sha1(
                    f"{file_path}:{code[:100]}".encode()
                ).hexdigest()[:16]
                
                finding = Finding(
                    name="Potential Security Issue",
                    severity="medium" if prob < 0.7 else "high",
                    cwe="CWE-20",  # Generic
                    file=file_path,
                    start_line=1,
                    end_line=len(code.split("\n")),
                    message=f"ML model detected potential vulnerability (confidence: {prob:.2f})",
                    confidence=prob,
                    fingerprint=fingerprint,
                )
                findings.append(finding)
        
        return findings

    def health(self) -> HealthResponse:
        """Check classic adapter health."""
        try:
            if not Path(self.model_path).exists():
                return HealthResponse(
                    healthy=False,
                    message=f"Model file not found: {self.model_path}",
                )
            
            self._load_model()
            return HealthResponse(
                healthy=True,
                message="Classic adapter is healthy",
                details={"model_path": self.model_path, "model_type": self.model_type},
            )
        except Exception as e:
            return HealthResponse(
                healthy=False,
                message=f"Classic adapter health check failed: {str(e)}",
            )

