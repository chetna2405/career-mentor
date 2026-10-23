"""Wraps the ML pieces built in notebooks 01-02 so the API can use them."""
import logging

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline, make_union

from .config import DATA_DIR, MODEL_DIR, USE_EMBEDDINGS
from skill_matcher import SkillMatcher, load_sentence_encoder, normalize, split_skills  # noqa: E402  (ml/ is on sys.path)

log = logging.getLogger("ml_service")


def _build_classifier():
    """Same model that won in notebook 01: word + char TF-IDF with Logistic Regression."""
    word = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), sublinear_tf=True)
    char = TfidfVectorizer(lowercase=True, analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True)
    return make_pipeline(make_union(word, char), LogisticRegression(C=10, max_iter=1000))


class MLService:
    def __init__(self):
        goals = pd.read_csv(DATA_DIR / "goal_texts.csv")
        skills = pd.read_csv(DATA_DIR / "skills.csv")

        # Goal classifier: use the saved model from notebook 01 if it loads, otherwise train from the CSV.
        self.classifier, self.classifier_source = None, "trained"
        path = MODEL_DIR / "goal_classifier.joblib"
        if path.exists():
            try:
                self.classifier = joblib.load(path)
                self.classifier_source = "loaded"
            except Exception as e:                      # e.g. scikit-learn version mismatch
                log.warning("could not load %s (%s); training instead", path, e)
        if self.classifier is None:
            self.classifier = _build_classifier().fit(goals["text"], goals["career"])

        # Skill matcher: embeddings are optional.
        encoder = None
        if USE_EMBEDDINGS:
            try:
                encoder = load_sentence_encoder()
            except Exception as e:
                log.warning("embedding layer disabled (%s: %s)", type(e).__name__, e)
        self.embeddings_on = encoder is not None
        self.matcher = SkillMatcher(skills, encoder=encoder)

    def predict_career(self, text, top_k=2):
        proba = self.classifier.predict_proba([text])[0]
        order = proba.argsort()[::-1][:top_k]
        return [{"career": str(self.classifier.classes_[i]), "confidence": round(float(proba[i]), 3)} for i in order]

    def match_skills(self, skill_texts):
        """skill_texts: list of strings already split with split_skills."""
        return self.matcher.match_many(skill_texts)
