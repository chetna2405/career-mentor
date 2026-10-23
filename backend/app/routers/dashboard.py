from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import adaptation, models
from ..database import get_db

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard/{user_id}")
def dashboard(user_id: int, on_date: date | None = None, db: Session = Depends(get_db)):
    """Everything the dashboard screen needs, in one call. `on_date` pretends it is another day (demos, tests)."""
    today = on_date or date.today()
    roadmap = db.query(models.Roadmap).filter_by(user_id=user_id, status="active").first()
    if roadmap is None:
        raise HTTPException(404, "No active roadmap. Generate one first (POST /api/roadmap/generate).")
    profile = db.query(models.Profile).filter_by(user_id=user_id).first()
    names = {s.skill_id: s.skill_name for s in db.query(models.Skill).all()}
    tasks = db.query(models.Task).filter_by(roadmap_id=roadmap.roadmap_id).all()

    # a skipped task was re-added as a new task, so only non-skipped tasks make up the plan
    plan = [t for t in tasks if t.status != "skipped"]
    done = [t for t in plan if t.status == "done"]
    pending = sorted((t for t in plan if t.status == "pending"), key=lambda t: (t.seq, t.task_id))
    planned_min = sum(t.planned_minutes for t in plan)
    done_min = sum(t.planned_minutes for t in done)

    # ----- skills -----
    by_skill = defaultdict(lambda: {"planned": 0, "done": 0, "seq": 10 ** 9})
    for t in plan:
        s = by_skill[t.skill_id]
        s["planned"] += t.planned_minutes
        s["done"] += t.planned_minutes if t.status == "done" else 0
        s["seq"] = min(s["seq"], t.seq)
    current = pending[0].skill_id if pending else None
    skill_list = []
    for sid, s in sorted(by_skill.items(), key=lambda kv: kv[1]["seq"]):
        complete = s["done"] == s["planned"]
        skill_list.append({"skill_id": sid, "skill_name": names[sid], "planned_minutes": s["planned"],
                           "done_minutes": s["done"], "percent": round(100 * s["done"] / s["planned"], 1),
                           "status": "completed" if complete else "in_progress" if sid == current else "upcoming"})

    # ----- weekly chart -----
    start = min(t.original_date for t in tasks)
    weeks = defaultdict(lambda: {"planned": 0, "done": 0})
    for t in plan:
        w = weeks[(t.scheduled_date - start).days // 7 + 1]
        w["planned"] += t.planned_minutes
        w["done"] += t.planned_minutes if t.status == "done" else 0
    weekly = [{"week": w, "planned_minutes": v["planned"], "done_minutes": v["done"]}
              for w, v in sorted(weeks.items())]

    # ----- streak, schedule, adaptation -----
    kind, n, _ = adaptation.trailing_streaks([(t.scheduled_date, t.planned_minutes, t.status) for t in tasks], today)
    original_end = roadmap.original_end_date or max(t.original_date for t in tasks)
    current_end = max(t.scheduled_date for t in plan)
    events = [e.event for e in db.query(models.AdaptationLog).filter_by(roadmap_id=roadmap.roadmap_id).all()]

    return {
        "career": roadmap.career, "roadmap_version": roadmap.version, "today": today,
        "start_date": start, "end_date": current_end,
        "progress": {"percent": round(100 * done_min / planned_min, 1) if planned_min else 0.0,
                     "tasks_total": len(plan), "tasks_done": len(done), "tasks_pending": len(pending),
                     "tasks_skipped": len(tasks) - len(plan)},
        "time": {"planned_minutes": planned_min, "done_minutes": done_min,
                 "remaining_minutes": planned_min - done_min, "hours_per_day": profile.hours_per_day},
        "streak": {"current_days": n if kind == "done" else 0},
        "skills": {"total": len(skill_list), "completed": sum(1 for s in skill_list if s["status"] == "completed"),
                   "current": {"skill_id": current, "skill_name": names[current]} if current else None,
                   "list": skill_list},
        "weekly": weekly,
        "schedule": {"original_end_date": original_end, "current_end_date": current_end,
                     "days_behind_original_plan": (current_end - original_end).days},   # negative = ahead
        "adaptation": {"tasks_skipped": len(tasks) - len(plan),
                       "tasks_rescheduled": sum(1 for t in plan if t.reschedule_count > 0),
                       "breaks": db.query(models.StudyBreak).filter_by(user_id=user_id).count(),
                       "workload_changes": sum(e in ("workload_reduced", "workload_increased") for e in events)},
    }
