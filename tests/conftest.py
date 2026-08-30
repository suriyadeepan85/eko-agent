"""
Pytest configuration for eko-agent tests.

Tests assume the corpus has been ingested into chroma_db/.
Run ingestion before testing:
    python -c "from src.ingestion import ingest; ingest('documents/')"
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """Pytest hook called before tests run."""
    # Verify chroma_db exists
    chroma_db_path = project_root / "chroma_db"
    if not chroma_db_path.exists():
        pytest.exit(
            "Error: chroma_db/ not found. Run ingestion before testing:\n"
            "  python -c \"from src.ingestion import ingest; ingest('documents/')\""
        )
