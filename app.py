#!/usr/bin/env python3

import os
import sys
from aegis import create_app

if __name__ == "__main__":
    upload_dir = os.path.join(os.getcwd(), "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    # Initialize database (V2)
    use_v2 = os.environ.get("AEGIS_USE_V2", "true").lower() == "true"
    if use_v2:
        print("Starting Aegis with SQLite database...")
        from aegis.database.init import ensure_database_initialized
        from aegis.database import get_db
        from aegis.database.repositories import ProviderRepository, ModelRepository

        # Auto-initialize database if needed
        if ensure_database_initialized(silent=False):
            db = get_db()
            provider_repo = ProviderRepository()
            model_repo = ModelRepository()

            providers = provider_repo.list_enabled()
            models = model_repo.list_all()

            print(f"  Database: {db.db_path}")
            print(f"  Providers: {len(providers)}, Models: {len(models)}")
        else:
            print("  Failed to initialize database. Continuing with V1 (in-memory) mode...")
            use_v2 = False
    else:
        print("Using Aegis V1 (in-memory mode)")

    app = create_app()

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"

    print(f"Starting aegis on http://{host}:{port}")
    print("Upload your source code ZIP files for security analysis")
    print("Press CTRL+C to stop the server")

    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\nShutting down aegis...")
        sys.exit(0)
