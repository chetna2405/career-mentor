from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import CONFIDENCE_THRESHOLD
from ..database import get_db
from skill_matcher import normalize, split_skills  # ml/ is on sys.path

router = APIRouter(prefix="/api", tags=["profile"])


def _careers(db):
    return {c for (c,) in db.query(models.CareerSkill.career).distinct().all()}


@router.post("/profile", response_model=schemas.ProfileOut)
def create_profile(body: schemas.ProfileIn, request: Request, db: Session = Depends(get_db)):
    """Save the form, predict the career, and match the typed skills to standard skills."""
    ml = request.app.state.ml

    user = db.get(models.User, body.user_id)
    if user is None:
        user = models.User(user_id=body.user_id, name=f"User {body.user_id}")
        db.add(user)
        db.flush()

    guesses = ml.predict_career(body.goal_text, top_k=2)
    top = guesses[0]
    needs_confirmation = top["confidence"] < CONFIDENCE_THRESHOLD

    # split "python, html and css" into separate skills, drop duplicates
    texts, seen = [], set()
    for field in body.skills_text:
        for t in split_skills(field):
            k = normalize(t)
            if k and k not in seen:
                seen.add(k)
                texts.append(t)
    matches = ml.match_skills(texts)

    # re-submitting the form replaces the old profile and skills
    db.query(models.UserSkill).filter_by(user_id=body.user_id).delete()
    profile = db.query(models.Profile).filter_by(user_id=body.user_id).first()
    if profile is None:
        profile = models.Profile(user_id=body.user_id)
        db.add(profile)
    profile.goal_text = body.goal_text
    profile.predicted_career = top["career"]
    profile.confidence = top["confidence"]
    profile.confirmed_career = None
    profile.level = body.level
    profile.hours_per_day = body.hours_per_day
    profile.target_date = body.target_date

    for m in matches:
        db.add(models.UserSkill(user_id=body.user_id, raw_text=m["raw_text"], matched_skill_id=m["skill_id"],
                                match_score=m["score"], match_method=m["method"],
                                confirmed=not m["needs_confirmation"]))
    db.commit()

    return schemas.ProfileOut(
        predicted_career=top["career"], confidence=top["confidence"],
        alternatives=[schemas.CareerGuess(**g) for g in guesses[1:]],
        needs_confirmation=needs_confirmation,
        matched_skills=[schemas.MatchedSkill(**m) for m in matches])


@router.post("/profile/confirm")
def confirm_profile(body: schemas.ConfirmIn, db: Session = Depends(get_db)):
    """The user confirms the career and answers the 'did you mean...?' skill questions."""
    profile = db.query(models.Profile).filter_by(user_id=body.user_id).first()
    if profile is None:
        raise HTTPException(404, "Profile not found. Submit the form first (POST /api/profile).")
    if body.career not in _careers(db):
        raise HTTPException(422, f"Unknown career '{body.career}'.")

    for s in body.skills:
        row = db.query(models.UserSkill).filter_by(user_id=body.user_id, raw_text=s.raw_text).first()
        if row is None:
            raise HTTPException(422, f"Skill text '{s.raw_text}' was not in the submitted profile.")
        if s.skill_id is not None and db.get(models.Skill, s.skill_id) is None:
            raise HTTPException(422, f"Unknown skill_id '{s.skill_id}'.")
        row.matched_skill_id = s.skill_id
        row.confirmed = True

    profile.confirmed_career = body.career
    db.commit()
    return {"status": "ok", "career": body.career, "skills_confirmed": len(body.skills)}


@router.get("/profile/{user_id}", response_model=schemas.ProfileDetail)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    profile = db.query(models.Profile).filter_by(user_id=user_id).first()
    if profile is None:
        raise HTTPException(404, "Profile not found.")
    names = {s.skill_id: s.skill_name for s in db.query(models.Skill).all()}
    rows = db.query(models.UserSkill).filter_by(user_id=user_id).all()
    return schemas.ProfileDetail(
        user_id=user_id, goal_text=profile.goal_text, predicted_career=profile.predicted_career,
        confidence=profile.confidence, confirmed_career=profile.confirmed_career, level=profile.level,
        hours_per_day=profile.hours_per_day, target_date=profile.target_date,
        skills=[schemas.MatchedSkill(raw_text=r.raw_text, skill_id=r.matched_skill_id,
                                     skill_name=names.get(r.matched_skill_id), score=r.match_score,
                                     method=r.match_method, needs_confirmation=not r.confirmed)
                for r in rows])
