from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..recommend import build_recommender

router = APIRouter(prefix="/api", tags=["resources"])


@router.get("/resources/{skill_id}")
def resources_for_skill(skill_id: str,
                        level: Literal["beginner", "intermediate", "advanced"] = "beginner",
                        minutes_per_day: int = Query(120, ge=15, le=720),
                        top_k: int = Query(3, ge=1, le=10),
                        db: Session = Depends(get_db)):
    """Best resources for one skill, ranked for this level and daily study time, with reasons."""
    skill = db.get(models.Skill, skill_id)
    if skill is None:
        raise HTTPException(404, f"Unknown skill '{skill_id}'.")
    recs = build_recommender(db).recommend(skill_id, level, minutes_per_day, top_k)
    return {"skill_id": skill_id, "skill_name": skill.skill_name, "level": level,
            "minutes_per_day": minutes_per_day, "resources": recs}


@router.post("/resources/{resource_id}/feedback")
def resource_feedback(resource_id: str, body: schemas.FeedbackIn, db: Session = Depends(get_db)):
    """'Helpful / not helpful' vote. One vote per user and resource: voting again replaces the old vote."""
    if db.get(models.Resource, resource_id) is None:
        raise HTTPException(404, f"Unknown resource '{resource_id}'.")
    if db.get(models.User, body.user_id) is None:
        db.add(models.User(user_id=body.user_id, name=f"User {body.user_id}"))
        db.flush()
    vote = db.query(models.ResourceFeedback).filter_by(user_id=body.user_id, resource_id=resource_id).first()
    if vote is None:
        db.add(models.ResourceFeedback(user_id=body.user_id, resource_id=resource_id, helpful=body.helpful))
    else:
        vote.helpful = body.helpful
    db.commit()
    total, up = db.query(func.count(models.ResourceFeedback.id),
                         func.sum(models.ResourceFeedback.helpful)).filter_by(resource_id=resource_id).one()
    up = int(up or 0)
    return {"resource_id": resource_id, "helpful": up, "not_helpful": total - up, "total": total,
            "note": "Your vote improves the ranking of this resource for future roadmaps."}
