"""Hybrid skill matcher: normalize -> alias lookup -> fuzzy match -> embedding similarity.

Output format of SkillMatcher.match() follows docs/api_design.md.
The embedding layer is optional: pass an `encoder` (list[str] -> normalized np.ndarray)
or leave it None to use only alias + fuzzy matching.
"""
import re
import numpy as np
from rapidfuzz import process, fuzz


def normalize(text):
    """Lowercase, unify separators, drop odd characters, collapse spaces."""
    t = str(text).lower().strip()
    t = re.sub(r"[-_/]", " ", t)
    t = re.sub(r"[^a-z0-9+#. ]", " ", t)
    return re.sub(r"\s+", " ", t).strip(" .")


def split_skills(text):
    """Split one free-text field ("python, html and css") into separate skill strings."""
    parts = re.split(r"[,;\n&|]| and | aur ", str(text), flags=re.I)
    return [p.strip() for p in parts if p.strip()]


def load_sentence_encoder(model_name="all-MiniLM-L6-v2"):
    """Needs `pip install sentence-transformers`; downloads the model on first use."""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    return lambda texts: model.encode(list(texts), normalize_embeddings=True)


class SkillMatcher:
    def __init__(self, skills, encoder=None, fuzzy_threshold=80, emb_high=0.70, emb_low=0.50):
        """skills: DataFrame with columns skill_id, skill_name, aliases (pipe separated)."""
        self.names = dict(zip(skills["skill_id"], skills["skill_name"]))
        self.exact = {}
        for sid, name, aliases in zip(skills["skill_id"], skills["skill_name"], skills["aliases"]):
            for key in [name] + str(aliases).split("|"):
                k = normalize(key)
                if k:
                    self.exact.setdefault(k, sid)
        self.keys = list(self.exact)
        self.fuzzy_threshold = fuzzy_threshold      # None disables the fuzzy layer
        self.emb_high, self.emb_low = emb_high, emb_low
        self.encoder = encoder
        if encoder is not None:
            self.doc_sid = [self.exact[k] for k in self.keys]
            self.doc_vecs = np.asarray(encoder(self.keys))

    def _fill(self, out, sid, score, method, confirm):
        out.update(skill_id=sid, skill_name=self.names[sid], score=round(float(score), 3),
                   method=method, needs_confirmation=confirm)
        return out

    def embedding_best(self, q):
        v = np.asarray(self.encoder([q]))[0]
        sims = self.doc_vecs @ v
        i = int(np.argmax(sims))
        return self.doc_sid[i], float(sims[i])

    def match(self, raw_text):
        out = {"raw_text": raw_text, "skill_id": None, "skill_name": None,
               "score": 0.0, "method": "none", "needs_confirmation": False}
        q = normalize(raw_text)
        if not q:
            return out
        if q in self.exact:                                           # layer 1: alias / exact name
            return self._fill(out, self.exact[q], 1.0, "alias", False)
        if self.fuzzy_threshold is not None and len(q) >= 4:          # layer 2: typos
            hit = process.extractOne(q, self.keys, scorer=fuzz.ratio, score_cutoff=self.fuzzy_threshold)
            if hit:
                return self._fill(out, self.exact[hit[0]], hit[1] / 100, "fuzzy", False)
        if self.encoder is not None:                                  # layer 3: meaning
            sid, score = self.embedding_best(q)
            if score >= self.emb_high:
                return self._fill(out, sid, score, "embedding", False)
            if score >= self.emb_low:
                return self._fill(out, sid, score, "embedding", True)  # ask the user
            out["score"] = round(score, 3)
        return out

    def match_many(self, texts):
        return [self.match(t) for t in texts]
