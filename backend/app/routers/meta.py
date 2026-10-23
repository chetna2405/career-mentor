from fastapi import APIRouter, Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CareerSkill, Profile, Roadmap, Skill

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/health")
def health(request: Request):
    ml = request.app.state.ml
    return {"status": "ok", "classifier": ml.classifier_source, "embeddings": ml.embeddings_on}


@router.get("/careers")
def careers(db: Session = Depends(get_db)):
    rows = db.query(CareerSkill.career, func.count(CareerSkill.id)).group_by(CareerSkill.career).all()
    return [{"career": c, "skill_count": n} for c, n in sorted(rows)]


@router.get("/skills")
def skills(db: Session = Depends(get_db)):
    """All standard skills (used for the 'did you mean...?' dropdowns)."""
    rows = db.query(Skill).order_by(Skill.skill_name).all()
    return [{"skill_id": s.skill_id, "skill_name": s.skill_name, "difficulty": s.difficulty,
             "est_hours": s.est_hours} for s in rows]


@router.get("/state/{user_id}")
def state(user_id: int, db: Session = Depends(get_db)):
    """Where is this user in the journey? Lets the website choose the first screen without trial and error."""
    profile = db.query(Profile).filter_by(user_id=user_id).first()
    roadmap = db.query(Roadmap).filter_by(user_id=user_id, status="active").first()
    return {"has_profile": profile is not None, "has_roadmap": roadmap is not None,
            "career": roadmap.career if roadmap else (profile.confirmed_career or profile.predicted_career if profile else None)}
