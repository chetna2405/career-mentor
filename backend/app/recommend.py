"""Builds the resource recommender (ml/recommender.py) from the database, including user feedback."""
import pandas as pd

from . import models
from recommender import ResourceRecommender  # ml/ is on sys.path


def build_recommender(db):
    resources = pd.DataFrame([{"resource_id": r.resource_id, "skill_id": r.skill_id, "title": r.title,
                               "type": r.type, "url": r.url, "level": r.level,
                               "duration_min": r.duration_min, "is_free": r.is_free}
                              for r in db.query(models.Resource).all()])
    votes = db.query(models.ResourceFeedback).all()
    feedback = (pd.DataFrame([{"resource_id": v.resource_id, "helpful": int(v.helpful)} for v in votes])
                if votes else None)
    return ResourceRecommender(resources, feedback)
