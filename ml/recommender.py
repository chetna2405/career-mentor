"""Resource recommender: content-based scoring + feedback re-ranking.

For a skill the user needs to learn, rank the available resources by how well they fit:
the user's level, daily study time, preferred resource type, and what earlier learners
found helpful. Every score is explained with human-readable reasons.
"""
import pandas as pd

LEVELS = {"beginner": 0, "intermediate": 1, "advanced": 2}

# How suitable each resource type is for a learner at a given level (0..1)
TYPE_FIT = {
    "beginner":     {"course": 1.0, "video": 1.0, "practice": 0.8, "tool": 0.8, "docs": 0.6, "book": 0.4},
    "intermediate": {"docs": 1.0, "practice": 1.0, "course": 0.8, "tool": 0.7, "video": 0.7, "book": 0.6},
    "advanced":     {"docs": 1.0, "book": 1.0, "practice": 1.0, "tool": 0.6, "course": 0.6, "video": 0.4},
}
# resource level minus user level -> how good a fit (0 = exact, +1 = a stretch, -1 = a bit easy)
LEVEL_FIT = {0: 1.0, 1: 0.4, -1: 0.6, 2: 0.0, -2: 0.2}

DEFAULT_WEIGHTS = {"level": 0.40, "time": 0.20, "type": 0.15, "feedback": 0.20, "free": 0.05}


class ResourceRecommender:
    def __init__(self, resources, feedback=None, weights=None, prior_a=2, prior_b=2):
        """resources: DataFrame (resources.csv). feedback: DataFrame with resource_id, helpful (0/1)."""
        self.resources = resources.copy()
        self.weights = {**DEFAULT_WEIGHTS, **(weights or {})}
        self.prior_a, self.prior_b = prior_a, prior_b     # Beta prior: neutral start (0.5)
        self.set_feedback(feedback)

    def set_feedback(self, feedback):
        self.fb = {}
        if feedback is not None and len(feedback):
            g = feedback.groupby("resource_id")["helpful"].agg(["sum", "count"])
            self.fb = {rid: (int(r["sum"]), int(r["count"])) for rid, r in g.iterrows()}

    def feedback_score(self, resource_id):
        up, n = self.fb.get(resource_id, (0, 0))
        return (up + self.prior_a) / (n + self.prior_a + self.prior_b), n

    def recommend(self, skill_id, level="beginner", minutes_per_day=120, top_k=3):
        rows = self.resources[self.resources["skill_id"] == skill_id]
        if rows.empty:
            return []
        ul = LEVELS[level]
        out = []
        for r in rows.itertuples(index=False):
            gap = LEVELS[r.level] - ul
            level_fit = LEVEL_FIT.get(gap, 0.0)
            days = r.duration_min / max(minutes_per_day, 1)
            time_fit = 1 / (1 + days / 7)
            type_fit = TYPE_FIT[level].get(r.type, 0.5)
            fb, n = self.feedback_score(r.resource_id)
            free = 1.0 if str(r.is_free).lower() == "yes" else 0.0
            w = self.weights
            score = (w["level"] * level_fit + w["time"] * time_fit + w["type"] * type_fit
                     + w["feedback"] * fb + w["free"] * free)

            reasons = []
            reasons.append("matches your level" if gap == 0 else
                           "a slight stretch above your level" if gap == 1 else
                           "a bit easier than your level" if gap == -1 else "far from your level")
            reasons.append(f"about {max(days, 0.1):.1f} days at {minutes_per_day} min/day")
            if n >= 3:
                reasons.append(f"{round(100 * fb)}% of {n} learners found it helpful")
            out.append({"resource_id": r.resource_id, "title": r.title, "type": r.type, "url": r.url,
                        "level": r.level, "duration_min": r.duration_min,
                        "score": round(score, 3), "estimated_days": round(days, 1), "reasons": reasons})
        out.sort(key=lambda x: x["score"], reverse=True)
        return out[:top_k]
