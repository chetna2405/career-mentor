import os
import sys
import tempfile
from pathlib import Path

# use a throw-away database and skip the embedding model so tests are fast and repeatable
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmp) / 'test.db'}"
os.environ["USE_EMBEDDINGS"] = "0"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_breaks(client):
    """Study breaks would otherwise leak from one test into the next (they are stored per user)."""
    from app.database import SessionLocal
    from app.models import StudyBreak
    with SessionLocal() as db:
        db.query(StudyBreak).delete()
        db.commit()
