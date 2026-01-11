#!/usr/bin/env python3
"""Database initialization script for Aegis.

This script initializes the Aegis SQLite database with default providers and models.

Note: As of the latest version, the database is auto-initialized on first run.
You only need to run this script manually if you want to reset the database.
"""
import sys
from pathlib import Path

# Add parent directory to path to import aegis modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from aegis.database.init import initialize_database


def migrate():
    """Initialize database and create default configuration."""
    print("=" * 60)
    print("Aegis Database Initialization")
    print("=" * 60)
    print()

    success = initialize_database(silent=False)

    print()
    if success:
        print("Database initialization complete!")
        print()
        print("Next steps:")
        print("  1. (Optional) Edit config/models.yaml to customize models")
        print("  2. (Optional) Set API keys: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY")
        print("  3. Start Aegis: python app.py")
    else:
        print("Database initialization failed!")
        print("Please check the error messages above.")

    print()
    print("=" * 60)

if __name__ == "__main__":
    try:
        migrate()
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
