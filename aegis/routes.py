"""Routes for Aegis application."""
import os
import json
import uuid
from typing import Any, Dict, List
from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    current_app,
    flash,
    redirect,
    url_for,
    Response,
    stream_with_context,
)
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from aegis.utils import allowed_file, extract_source_files
from aegis.registry import ModelRegistry
from aegis.runner import MultiModelRunner
from aegis.exports import export_sarif, export_csv
from aegis.models import ScanResult

main_bp = Blueprint("main", __name__)

# Global registry and scan storage
_registry = ModelRegistry()
_scan_results: Dict[str, ScanResult] = {}


@main_bp.route("/")
def index() -> str:
    """Main index page."""
    return render_template("index.html")


@main_bp.route("/models")
def models_page() -> str:
    """Models management page."""
    return render_template("models.html")


@main_bp.route("/scan/<scan_id>")
def scan_detail(scan_id: str) -> str:
    """Scan detail page."""
    return render_template("scan_detail.html", scan_id=scan_id)


# API Routes

@main_bp.route("/api/models", methods=["GET"])
def list_models() -> Any:
    """List all registered models."""
    return jsonify({"models": _registry.list_all()})


@main_bp.route("/api/models/<provider>", methods=["GET"])
def list_models_by_provider(provider: str) -> Any:
    """List models by provider."""
    return jsonify({"models": _registry.list_by_provider(provider)})


@main_bp.route("/api/models/ollama", methods=["GET"])
def list_ollama_models() -> Any:
    """List installed Ollama models."""
    base_url = current_app.config.get("OLLAMA_BASE_URL", "http://localhost:11434")
    models = _registry.discover_ollama_models(base_url)
    return jsonify({"models": models})


@main_bp.route("/api/models/ollama/pull", methods=["POST"])
def pull_ollama_model() -> Any:
    """Pull an Ollama model."""
    data = request.get_json()
    model_name = data.get("name")
    
    if not model_name:
        return jsonify({"error": "Model name required"}), 400
    
    base_url = current_app.config.get("OLLAMA_BASE_URL", "http://localhost:11434")
    result = _registry.pull_ollama_model(model_name, base_url)
    
    if result.get("success"):
        return jsonify(result)
    else:
        return jsonify({"error": result.get("error")}), 500


@main_bp.route("/api/models/ollama/register", methods=["POST"])
def register_ollama_model() -> Any:
    """Register an Ollama model as an adapter."""
    data = request.get_json()
    model_name = data.get("name")
    
    if not model_name:
        return jsonify({"error": "Model name required"}), 400
    
    base_url = current_app.config.get("OLLAMA_BASE_URL", "http://localhost:11434")
    adapter = _registry.create_ollama_adapter(model_name, base_url)
    
    return jsonify({"adapter": adapter.to_dict()})


@main_bp.route("/api/models/llm/register", methods=["POST"])
def register_llm_model() -> Any:
    """Register a cloud LLM model."""
    data = request.get_json()
    provider = data.get("provider")
    model_name = data.get("model_name")
    api_key = data.get("api_key")
    api_base = data.get("api_base")
    
    if not all([provider, model_name, api_key]):
        return jsonify({"error": "provider, model_name, and api_key required"}), 400
    
    adapter = _registry.create_llm_adapter(provider, model_name, api_key, api_base)
    return jsonify({"adapter": adapter.to_dict()})


@main_bp.route("/api/models/hf/register", methods=["POST"])
def register_hf_model() -> Any:
    """Register a HuggingFace model."""
    data = request.get_json()
    model_id = data.get("model_id")
    task = data.get("task", "text-generation")
    cache_dir = data.get("cache_dir")
    
    if not model_id:
        return jsonify({"error": "model_id required"}), 400
    
    adapter = _registry.create_hf_adapter(model_id, task, cache_dir)
    return jsonify({"adapter": adapter.to_dict()})


@main_bp.route("/api/models/classic/register", methods=["POST"])
def register_classic_model() -> Any:
    """Register a classic ML model."""
    data = request.get_json()
    model_path = data.get("model_path")
    model_type = data.get("model_type", "sklearn")
    
    if not model_path:
        return jsonify({"error": "model_path required"}), 400
    
    adapter = _registry.create_classic_adapter(model_path, model_type)
    return jsonify({"adapter": adapter.to_dict()})


@main_bp.route("/api/models/<adapter_id>", methods=["DELETE"])
def remove_model(adapter_id: str) -> Any:
    """Remove a model adapter."""
    success = _registry.remove(adapter_id)
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Model not found"}), 404


@main_bp.route("/api/scan", methods=["POST"])
def create_scan() -> Any:
    """Create a new scan."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file: FileStorage = request.files["file"]
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400
    
    data = request.form.to_dict()
    model_ids = data.get("models", "").split(",") if data.get("models") else []
    # CWE IDs are auto-selected by language, no need for user input
    consensus_strategy = data.get("consensus_strategy", "union")
    judge_model_id = data.get("judge_model_id")
    
    filepath = None
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        
        # Extract source files
        source_files = extract_source_files(filepath)
        
        # Get selected models
        models = []
        for model_id in model_ids:
            adapter = _registry.get(model_id)
            if adapter:
                models.append(adapter)
        
        if not models:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({"error": "No valid models selected"}), 400
        
        # Get judge model if specified
        judge_model = None
        if judge_model_id:
            judge_model = _registry.get(judge_model_id)
        
        # Run scan
        runner = MultiModelRunner()
        scan_result = runner.run_scan(
            source_files=source_files,
            models=models,
            cwe_ids=None,  # Auto-select by language
            consensus_strategy=consensus_strategy,
            judge_model=judge_model,
        )
        
        # Store result with source files for code snippet display
        scan_result.source_files = source_files
        _scan_results[scan_result.scan_id] = scan_result
        
        # Clean up
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify(scan_result.to_dict())
    
    except Exception as e:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": str(e)}), 500


@main_bp.route("/api/scan/<scan_id>", methods=["GET"])
def get_scan(scan_id: str) -> Any:
    """Get scan results."""
    if scan_id not in _scan_results:
        return jsonify({"error": "Scan not found"}), 404
    
    return jsonify(_scan_results[scan_id].to_dict())


@main_bp.route("/api/scan/<scan_id>/file/<path:file_path>", methods=["GET"])
def get_scan_file(scan_id: str, file_path: str) -> Any:
    """Get source code content for a file in a scan."""
    if scan_id not in _scan_results:
        return jsonify({"error": "Scan not found"}), 404
    
    scan_result = _scan_results[scan_id]
    if not scan_result.source_files:
        return jsonify({"error": "Source files not available"}), 404
    
    # Normalize file path (handle URL encoding)
    if file_path not in scan_result.source_files:
        # Try to find by matching end of path
        for stored_path, content in scan_result.source_files.items():
            if stored_path.endswith(file_path) or file_path.endswith(stored_path):
                return jsonify({"content": content, "file_path": stored_path})
        return jsonify({"error": "File not found"}), 404
    
    return jsonify({"content": scan_result.source_files[file_path], "file_path": file_path})


@main_bp.route("/api/scan/<scan_id>/sarif", methods=["GET"])
def get_scan_sarif(scan_id: str) -> Any:
    """Get scan results as SARIF."""
    if scan_id not in _scan_results:
        return jsonify({"error": "Scan not found"}), 404
    
    scan_result = _scan_results[scan_id]
    sarif = export_sarif(scan_result)
    
    return Response(
        json.dumps(sarif, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename=scan_{scan_id}.sarif.json"},
    )


@main_bp.route("/api/scan/<scan_id>/csv", methods=["GET"])
def get_scan_csv(scan_id: str) -> Any:
    """Get scan results as CSV."""
    if scan_id not in _scan_results:
        return jsonify({"error": "Scan not found"}), 404
    
    scan_result = _scan_results[scan_id]
    
    # Create temporary CSV
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        export_csv(scan_result.consensus_findings, f.name)
        csv_content = open(f.name, "r").read()
        os.unlink(f.name)
    
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=scan_{scan_id}.csv"},
    )


# Legacy routes for backward compatibility

@main_bp.route("/upload", methods=["POST"])
def upload_file() -> Any:
    """Legacy upload route."""
    if "file" not in request.files:
        flash("No file selected")
        return redirect(request.url)
    
    file: FileStorage = request.files["file"]
    
    if file.filename == "":
        flash("No file selected")
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        
        try:
            # Use new scan API
            source_files = extract_source_files(filepath)
            
            # Get default Ollama model
            base_url = current_app.config.get("OLLAMA_BASE_URL", "http://localhost:11434")
            model_name = current_app.config.get("OLLAMA_MODEL", "gpt-oss:120b-cloud")
            adapter = _registry.create_ollama_adapter(model_name, base_url)
            
            runner = MultiModelRunner()
            scan_result = runner.run_scan(
                source_files=source_files,
                models=[adapter],
            )
            
            _scan_results[scan_result.scan_id] = scan_result
            
            os.remove(filepath)
            
            # Convert to legacy format for template
            legacy_results = []
            for finding in scan_result.consensus_findings:
                legacy_results.append({
                    "file_path": finding.file,
                    "line_number": finding.start_line,
                    "severity": finding.severity,
                    "score": finding.confidence * 10.0,
                    "category": finding.cwe,
                    "description": finding.message,
                    "recommendation": f"Address {finding.cwe} vulnerability",
                    "code_snippet": "",
                })
            
            return render_template("results.html", results=legacy_results)
        
        except Exception as e:
            flash(f"Error analyzing file: {str(e)}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return redirect(url_for("main.index"))
    
    flash("Invalid file type. Please upload a ZIP file.")
    return redirect(url_for("main.index"))


@main_bp.route("/api/analyze", methods=["POST"])
def api_analyze() -> Any:
    """Legacy API analyze route."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file: FileStorage = request.files["file"]
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        
        source_files = extract_source_files(filepath)
        
        base_url = current_app.config.get("OLLAMA_BASE_URL", "http://localhost:11434")
        model_name = current_app.config.get("OLLAMA_MODEL", "gpt-oss:120b-cloud")
        adapter = _registry.create_ollama_adapter(model_name, base_url)
        
        runner = MultiModelRunner()
        scan_result = runner.run_scan(
            source_files=source_files,
            models=[adapter],
        )
        
        os.remove(filepath)
        
        # Convert to legacy format
        legacy_results = []
        for finding in scan_result.consensus_findings:
            legacy_results.append({
                "file_path": finding.file,
                "line_number": finding.start_line,
                "severity": finding.severity,
                "score": finding.confidence * 10.0,
                "category": finding.cwe,
                "description": finding.message,
                "recommendation": f"Address {finding.cwe} vulnerability",
                "code_snippet": "",
            })
        
        return jsonify({"results": legacy_results})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/health")
def health_check() -> Any:
    """Health check endpoint."""
    return "OK", 200
