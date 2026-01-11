"""Database initialization and seeding for Aegis."""
import os
from pathlib import Path
from typing import Optional

from aegis.database import init_db
from aegis.database.repositories import ProviderRepository, ModelRepository


def initialize_database(silent: bool = False) -> bool:
    """
    Initialize Aegis database with default providers and models.

    Args:
        silent: If True, suppress output messages

    Returns:
        True if initialization successful, False otherwise
    """
    def log(message: str):
        if not silent:
            print(message)

    try:
        # Initialize database
        log("Initializing database...")
        db = init_db()
        log(f"  Database: {db.db_path}")

        # Create default providers
        provider_repo = ProviderRepository()

        providers_config = [
            {
                "name": "ollama",
                "type": "llm",
                "base_url": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
                "rate_limit_per_second": 10.0,
                "timeout_seconds": 600,
                "retry_max_attempts": 3,
                "retry_backoff_factor": 2.0,
            },
            {
                "name": "openai",
                "type": "llm",
                "base_url": "https://api.openai.com/v1",
                "rate_limit_per_second": 5.0,
                "timeout_seconds": 60,
                "retry_max_attempts": 3,
                "retry_backoff_factor": 2.0,
            },
            {
                "name": "anthropic",
                "type": "llm",
                "base_url": "https://api.anthropic.com/v1",
                "rate_limit_per_second": 5.0,
                "timeout_seconds": 60,
                "retry_max_attempts": 3,
                "retry_backoff_factor": 2.0,
            },
            {
                "name": "google",
                "type": "llm",
                "base_url": "https://generativelanguage.googleapis.com/v1beta",
                "rate_limit_per_second": 5.0,
                "timeout_seconds": 60,
                "retry_max_attempts": 3,
                "retry_backoff_factor": 2.0,
            },
            {
                "name": "huggingface",
                "type": "llm",
                "base_url": "https://huggingface.co",
                "rate_limit_per_second": 10.0,
                "timeout_seconds": 600,
                "retry_max_attempts": 3,
                "retry_backoff_factor": 2.0,
            },
        ]

        created_providers = {}
        for prov_config in providers_config:
            existing = provider_repo.get_by_name(prov_config["name"])
            if existing:
                created_providers[prov_config["name"]] = existing['id']
            else:
                provider_id = provider_repo.create(
                    name=prov_config["name"],
                    type=prov_config["type"],
                    config=prov_config
                )
                created_providers[prov_config["name"]] = provider_id

        log(f"  Providers: {len(created_providers)}")

        # Load models from YAML config if available
        try:
            from aegis.config_loader import ConfigLoader

            # Try to find config/models.yaml
            config_paths = [
                Path.cwd() / "config" / "models.yaml",
                Path(__file__).parent.parent.parent / "config" / "models.yaml",
            ]

            yaml_path = None
            for path in config_paths:
                if path.exists():
                    yaml_path = path
                    break

            if yaml_path:
                log(f"  Loading models from: {yaml_path}")
                ConfigLoader.bootstrap_from_yaml(yaml_path)

                # Count loaded models
                model_repo = ModelRepository()
                models = model_repo.list_all()
                log(f"  Models: {len(models)}")
            else:
                log("  No models.yaml found, using defaults")

        except Exception as e:
            log(f"  Warning: Could not load YAML config: {e}")

        log("Database initialization complete!")
        return True

    except Exception as e:
        log(f"Error during database initialization: {e}")
        import traceback
        traceback.print_exc()
        return False


def ensure_database_initialized(silent: bool = True) -> bool:
    """
    Ensure database is initialized. Auto-initialize if needed.

    Args:
        silent: If True, suppress output messages

    Returns:
        True if database is ready, False otherwise
    """
    try:
        from aegis.database import get_db

        db = get_db()

        # Check if database has providers (indicates it's been initialized)
        provider_repo = ProviderRepository()
        providers = provider_repo.list_enabled()

        if not providers:
            # Database exists but empty - initialize it
            if not silent:
                print("Database is empty. Initializing...")
            return initialize_database(silent=silent)

        return True

    except Exception:
        # Database doesn't exist or is corrupted - initialize it
        if not silent:
            print("Database not found. Initializing...")
        return initialize_database(silent=silent)
