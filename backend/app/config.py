"""Paths and settings. Also makes the ml/ folder importable (skill_matcher.py, recommender.py)."""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent      # backend/
ROOT_DIR = BASE_DIR.parent                             # repo root
DATA_DIR = ROOT_DIR / "data"
ML_DIR = ROOT_DIR / "ml"
MODEL_DIR = ML_DIR / "models"
FRONTEND_DIR = ROOT_DIR / "frontend"

DB_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'career_mentor.db'}")

# Set USE_EMBEDDINGS=0 to skip loading the sentence-transformers model (faster startup).
USE_EMBEDDINGS = os.getenv("USE_EMBEDDINGS", "1") == "1"

# Below this confidence the website asks the user to confirm the predicted career (from notebook 01).
CONFIDENCE_THRESHOLD = 0.6

if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))
