import math
from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, planner, schemas
from ..config import CONFIDENCE_THRESHOLD
from ..database import get_db
from ..recommend import build_recommender
from ..serializers import task_item

router = APIRouter(prefix="/api", tags=["roadmap"])


def _context(db: Session, user_id: int):
    """Everything the planner needs about this user, read from the database."""
    profile = db.query(models.Profile).filter_by(user_id=user_id).first()
    if profile is None:
        raise HTTPException(404, "Profile not found. Submit the form first (POST /api/profile).")
    if profile.confirmed_career is None and profile.confidence < CONFIDENCE_THRESHOLD:
        raise HTTPException(409, "The predicted career is not certain. Confirm it first (POST /api/profile/confirm).")
    career = profile.confirmed_career or profile.predicted_career

    skills = {s.skill_id: s for s in db.query(models.Skill).all()}
    career_skills = {c.skill_id: c.priority for c in db.query(models.CareerSkill).filter_by(career=career)}
    prereqs = defaultdict(set)
    for p in db.query(models.Prerequisite).all():
        prereqs[p.skill_id].add(p.prereq_skill_id)

    rows = db.query(models.UserSkill).filter_by(user_id=user_id).all()
    known = {r.matched_skill_id for r in rows if r.matched_skill_id and r.confirmed}
    pending = [r.raw_text for r in rows if r.matched_skill_id and not r.confirmed]

    gap, implied = planner.compute_gap(career_skills, known, prereqs)
    order = planner.order_skills(gap, prereqs, {s: skills[s].difficulty for s in gap})
    return {"profile": profile, "career": career, "skills": skills, "known": known, "implied": implied,
            "gap": gap, "order": order, "pending": pending,
            "minutes_per_day": max(15, int(round(profile.hours_per_day * 60)))}


def _hours(ctx, ids):
    return sum(ctx["skills"][s].est_hours for s in ids)


def _skill_ref(ctx, sid):
    return {"skill_id": sid, "skill_name": ctx["skills"][sid].skill_name}


def _target_info(ctx, start, total_hours):
    """Does the plan fit before the user's target date?"""
    target = ctx["profile"].target_date
    days_needed = math.ceil(total_hours * 60 / ctx["minutes_per_day"]) if total_hours else 0
    if target is None:
        return {"target_date": None, "fits_target_date": None, "suggested_hours_per_day": None}
    days_available = max((target - start).days + 1, 1)
    fits = days_needed <= days_available
    suggested = None if fits else math.ceil(total_hours / days_available * 2) / 2   # round up to 0.5 h
    return {"target_date": target, "fits_target_date": fits, "suggested_hours_per_day": suggested}


@router.get("/gap/{user_id}")
def get_gap(user_id: int, start_date: date | None = None, db: Session = Depends(get_db)):
    """start_date (optional) is the day the user plans to begin; defaults to today."""
    ctx = _context(db, user_id)
    total_hours = _hours(ctx, ctx["order"])
    days = math.ceil(total_hours * 60 / ctx["minutes_per_day"]) if total_hours else 0
    gap_list = []
    for i, sid in enumerate(ctx["order"], 1):
        g = ctx["gap"][sid]
        gap_list.append({"order": i, **_skill_ref(ctx, sid), "priority": g["priority"],
                         "est_hours": ctx["skills"][sid].est_hours, "reason": g["reason"],
                         "prerequisite_of": ctx["skills"][g["prereq_of"]].skill_name if g["prereq_of"] else None})
    return {
        "career": ctx["career"],
        "known_skills": [_skill_ref(ctx, s) for s in sorted(ctx["known"])],
        "implied_known": [_skill_ref(ctx, s) for s in sorted(ctx["implied"])],
        "gap": gap_list,
        "total_hours": total_hours,
        "hours_per_day": ctx["minutes_per_day"] / 60,
        "estimated_days": days,
        "pending_skill_confirmations": ctx["pending"],
        **_target_info(ctx, start_date or date.today(), total_hours),
    }


@router.post("/roadmap/generate")
def generate_roadmap(body: schemas.RoadmapIn, db: Session = Depends(get_db)):
    ctx = _context(db, body.user_id)
    if not ctx["order"]:
        return {"roadmap_id": None, "message": "You already know every skill for this career.", "warnings": []}
    start = body.start_date or date.today()

    recommender = build_recommender(db)

    level, mpd = ctx["profile"].level, ctx["minutes_per_day"]
    plan = []
    for sid in ctx["order"]:
        recs = recommender.recommend(sid, level, mpd, top_k=2)
        plan.append((sid, planner.build_segments(ctx["skills"][sid].est_hours * 60, recs)))
    blocked = set()
    for b in db.query(models.StudyBreak).filter_by(user_id=body.user_id).all():
        d = b.start_date
        while d <= b.end_date:
            blocked.add(d)
            d += timedelta(days=1)
    tasks = planner.schedule(plan, mpd, start, blocked)
    start = tasks[0]["date"]                      # first real study day (a break may cover the requested start)
    end = tasks[-1]["date"]

    # the previous active roadmap is kept, but marked "old"
    previous = db.query(models.Roadmap).filter_by(user_id=body.user_id).all()
    for r in previous:
        if r.status == "active":
            r.status = "old"
    version = max([r.version for r in previous], default=0) + 1
    roadmap = models.Roadmap(user_id=body.user_id, career=ctx["career"], version=version, status="active",
                             original_end_date=end)
    db.add(roadmap)
    db.flush()
    db.add_all([models.Task(roadmap_id=roadmap.roadmap_id, skill_id=t["skill_id"], resource_id=t["resource_id"],
                            scheduled_date=t["date"], original_date=t["date"], planned_minutes=t["minutes"], seq=i)
                for i, t in enumerate(tasks)])
    total_hours = _hours(ctx, ctx["order"])
    db.add(models.AdaptationLog(roadmap_id=roadmap.roadmap_id, date=date.today(), event="roadmap_generated",
                                detail=f"version {version}: {len(ctx['order'])} skills, {len(tasks)} tasks, "
                                       f"{(end - start).days + 1} days"))
    db.commit()

    warnings = []
    info = _target_info(ctx, start, total_hours)
    if info["fits_target_date"] is False:
        optional = _hours(ctx, [s for s in ctx["order"] if ctx["gap"][s]["priority"] == 3])
        warnings.append(f"The plan ends on {end}, after your target date {info['target_date']}. "
                        f"Study about {info['suggested_hours_per_day']} h/day to finish in time"
                        + (f", or skip the optional skills ({optional} h)." if optional else "."))
    return {"roadmap_id": roadmap.roadmap_id, "version": version, "career": ctx["career"],
            "start_date": start, "end_date": end, "total_days": (end - start).days + 1,
            "skills": len(ctx["order"]), "total_hours": total_hours, "task_count": len(tasks),
            "warnings": warnings}


@router.get("/roadmap/{user_id}")
def get_roadmap(user_id: int, db: Session = Depends(get_db)):
    roadmap = db.query(models.Roadmap).filter_by(user_id=user_id, status="active").first()
    if roadmap is None:
        raise HTTPException(404, "No active roadmap. Generate one first (POST /api/roadmap/generate).")
    tasks = (db.query(models.Task).filter_by(roadmap_id=roadmap.roadmap_id)
             .order_by(models.Task.scheduled_date, models.Task.seq, models.Task.task_id).all())
    skills = {s.skill_id: s.skill_name for s in db.query(models.Skill).all()}
    resources = {r.resource_id: r for r in db.query(models.Resource).all()}

    start = tasks[0].scheduled_date
    weeks = defaultdict(lambda: defaultdict(list))
    for t in tasks:
        item = task_item(t, skills, resources)
        weeks[(t.scheduled_date - start).days // 7 + 1][t.scheduled_date].append(item)

    out_weeks = []
    for w in sorted(weeks):
        days = [{"date": d, "total_minutes": sum(i["planned_minutes"] for i in items), "tasks": items}
                for d, items in sorted(weeks[w].items())]
        seen = []
        for d in days:
            for i in d["tasks"]:
                if i["skill_name"] not in seen:
                    seen.append(i["skill_name"])
        out_weeks.append({"week": w, "start_date": days[0]["date"], "end_date": days[-1]["date"],
                          "skills": seen, "days": days})
    # skipped tasks were re-added as new tasks, so they do not count towards the total
    counted = [t for t in tasks if t.status != "skipped"]
    done = sum(1 for t in counted if t.status == "done")
    return {"roadmap_id": roadmap.roadmap_id, "version": roadmap.version, "career": roadmap.career,
            "start_date": tasks[0].scheduled_date, "end_date": tasks[-1].scheduled_date,
            "progress": {"tasks_total": len(counted), "tasks_done": done,
                         "tasks_skipped": len(tasks) - len(counted),
                         "percent": round(100 * done / max(len(counted), 1), 1)},
            "weeks": out_weeks}
