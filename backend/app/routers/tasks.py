from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import adaptation, models, schemas
from ..database import get_db
from ..serializers import task_item

router = APIRouter(prefix="/api", tags=["tasks"])

ALLOWED = {("pending", "done"), ("pending", "skipped"), ("done", "pending")}


# ---------- helpers ----------
def _active_roadmap(db, user_id):
    roadmap = db.query(models.Roadmap).filter_by(user_id=user_id, status="active").first()
    if roadmap is None:
        raise HTTPException(404, "No active roadmap. Generate one first (POST /api/roadmap/generate).")
    return roadmap


def _profile(db, user_id):
    profile = db.query(models.Profile).filter_by(user_id=user_id).first()
    if profile is None:
        raise HTTPException(404, "Profile not found.")
    return profile


def _lookups(db):
    return ({s.skill_id: s.skill_name for s in db.query(models.Skill).all()},
            {r.resource_id: r for r in db.query(models.Resource).all()})


def _minutes_per_day(profile):
    return max(15, int(round(profile.hours_per_day * 60)))


def _blocked_days(db, user_id):
    days = set()
    for b in db.query(models.StudyBreak).filter_by(user_id=user_id).all():
        d = b.start_date
        while d <= b.end_date:
            days.add(d)
            d += timedelta(days=1)
    return days


def _pending_ordered(db, roadmap_id, extra=(), after=None, from_date=None):
    """Pending tasks in learning order. `after`: only tasks scheduled after this date; `from_date`: on/after."""
    q = db.query(models.Task).filter_by(roadmap_id=roadmap_id, status="pending")
    tasks = [t for t in q.all()
             if (after is None or t.scheduled_date > after) and (from_date is None or t.scheduled_date >= from_date)]
    tasks += [t for t in extra if t not in tasks]
    return sorted(tasks, key=lambda t: (t.seq, t.task_id))


def _repack(db, tasks, start, minutes_per_day, blocked, ease_days=0):
    """Re-schedule the given tasks from `start`. Returns the tasks that changed their day."""
    chunks = adaptation.pack([t.planned_minutes for t in tasks], start, minutes_per_day, ease_days, blocked)
    seen, moved = set(), []
    for i, day, minutes in chunks:
        t = tasks[i]
        if i not in seen:                       # the first piece keeps the original row
            seen.add(i)
            if t.scheduled_date != day:
                t.reschedule_count += 1
                moved.append(t)
            t.scheduled_date, t.planned_minutes = day, minutes
        else:                                   # a task that no longer fits in one day is split
            db.add(models.Task(roadmap_id=t.roadmap_id, skill_id=t.skill_id, resource_id=t.resource_id,
                               scheduled_date=day, original_date=t.original_date, planned_minutes=minutes,
                               status="pending", reschedule_count=t.reschedule_count, seq=t.seq))
    return moved


def _merge_adjacent(db, tasks):
    """
    Join neighbouring pending pieces of the same skill and resource back into one block before re-packing.
    Without this, shifting the plan by an odd number of minutes (for example after a break) would cut
    every task into two pieces. Returns (merged tasks, {removed task_id: the task it was merged into}).
    """
    merged, owner = [], {}
    for t in tasks:
        prev = merged[-1] if merged else None
        if prev is not None and prev.skill_id == t.skill_id and prev.resource_id == t.resource_id:
            prev.planned_minutes += t.planned_minutes
            prev.original_date = min(prev.original_date, t.original_date)
            prev.reschedule_count = max(prev.reschedule_count, t.reschedule_count)
            owner[t.task_id] = prev
            db.delete(t)
        else:
            merged.append(t)
    return merged, owner


def _end_date(db, roadmap_id):
    db.flush()                                   # the session does not autoflush: make pending changes visible
    last = (db.query(models.Task).filter_by(roadmap_id=roadmap_id)
            .order_by(models.Task.scheduled_date.desc()).first())
    return last.scheduled_date if last else None


def _logged(db, roadmap_id, event, marker):
    return any(marker in l.detail for l in
               db.query(models.AdaptationLog).filter_by(roadmap_id=roadmap_id, event=event).all())


def _streak_rules(db, roadmap, profile, today, mpd):
    """Apply the 3-skipped-days and 5-done-days rules. Returns (new minutes per day, messages)."""
    rows = [(t.scheduled_date, t.planned_minutes, t.status)
            for t in db.query(models.Task).filter_by(roadmap_id=roadmap.roadmap_id).all()]
    kind, n, last = adaptation.trailing_streaks(rows, today)
    marker = f"streak_end={last}"
    new, msgs = mpd, []
    if kind == "skipped" and n % adaptation.SKIP_STREAK == 0 and not _logged(db, roadmap.roadmap_id, "workload_reduced", marker):
        new = adaptation.reduce_minutes(mpd)
        if new != mpd:
            msgs.append(f"You skipped {n} study days in a row, so your daily study time was reduced "
                        f"from {mpd} to {new} minutes.")
            db.add(models.AdaptationLog(roadmap_id=roadmap.roadmap_id, date=today, event="workload_reduced",
                                        detail=f"{mpd} -> {new} min/day after {n} skipped days; {marker}"))
    elif kind == "done" and n % adaptation.DONE_STREAK == 0 and not _logged(db, roadmap.roadmap_id, "workload_increased", marker):
        new = adaptation.increase_minutes(mpd)
        if new != mpd:
            msgs.append(f"{n} days in a row completed. Your daily study time was increased "
                        f"from {mpd} to {new} minutes.")
            db.add(models.AdaptationLog(roadmap_id=roadmap.roadmap_id, date=today, event="workload_increased",
                                        detail=f"{mpd} -> {new} min/day after {n} completed days; {marker}"))
    if new != mpd:
        profile.hours_per_day = round(new / 60, 2)
    return new, msgs


# ---------- endpoints ----------
@router.get("/tasks/today/{user_id}")
def tasks_today(user_id: int, on_date: date | None = None, db: Session = Depends(get_db)):
    """Tasks for today (`on_date` lets demos and tests pretend it is another day) plus overdue ones."""
    today = on_date or date.today()
    roadmap = _active_roadmap(db, user_id)
    skills, resources = _lookups(db)
    q = db.query(models.Task).filter_by(roadmap_id=roadmap.roadmap_id)
    todays = q.filter(models.Task.scheduled_date == today).order_by(models.Task.seq, models.Task.task_id).all()
    overdue = (q.filter(models.Task.scheduled_date < today, models.Task.status == "pending")
               .order_by(models.Task.scheduled_date, models.Task.seq, models.Task.task_id).all())
    on_break = today in _blocked_days(db, user_id)
    total = sum(t.planned_minutes for t in todays)
    done = sum(t.planned_minutes for t in todays if t.status == "done")
    message = ("You are on a study break today. Enjoy the rest!" if on_break and not todays else
               "No tasks scheduled for today." if not todays else None)
    return {"date": today, "on_break": on_break, "message": message,
            "total_minutes": total, "done_minutes": done,
            "tasks": [task_item(t, skills, resources) for t in todays],
            "overdue": [task_item(t, skills, resources) for t in overdue]}


@router.patch("/tasks/{task_id}")
def update_task(task_id: int, body: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(models.Task, task_id)
    if task is None:
        raise HTTPException(404, "Task not found.")
    roadmap = db.get(models.Roadmap, task.roadmap_id)
    if roadmap.status != "active":
        raise HTTPException(409, "This task belongs to an old roadmap version.")
    profile = _profile(db, roadmap.user_id)
    today = body.on_date or date.today()
    skills, resources = _lookups(db)

    if body.status == task.status:
        return {"task": task_item(task, skills, resources),
                "adaptation": {"changed": False, "messages": [], "daily_minutes": _minutes_per_day(profile),
                               "roadmap_end_date": _end_date(db, roadmap.roadmap_id)}}
    if (task.status, body.status) not in ALLOWED:
        raise HTTPException(409, f"A {task.status} task cannot be changed to {body.status}.")
    if body.status == "skipped" and task.scheduled_date > today:
        raise HTTPException(409, "You can only skip tasks scheduled for today or earlier.")

    mpd = _minutes_per_day(profile)
    end_before = _end_date(db, roadmap.roadmap_id)
    task.status = body.status
    messages, copy = [], None
    if body.status == "skipped":
        # keep the skipped task as history and re-add the same work as a new pending task
        copy = models.Task(roadmap_id=task.roadmap_id, skill_id=task.skill_id, resource_id=task.resource_id,
                           scheduled_date=today + timedelta(days=1), original_date=task.original_date,
                           planned_minutes=task.planned_minutes, status="pending",
                           reschedule_count=task.reschedule_count + 1, seq=task.seq)
        db.add(copy)
    db.flush()

    new_mpd, rule_msgs = _streak_rules(db, roadmap, profile, today, mpd)
    messages += rule_msgs

    if copy is not None or new_mpd != mpd:
        pending = _pending_ordered(db, roadmap.roadmap_id, after=today)     # includes the copy (dated tomorrow)
        n_replanned = len(pending) - (1 if copy is not None else 0)      # later tasks affected (before merging)
        pending, owner = _merge_adjacent(db, pending)
        landing = owner.get(copy.task_id, copy) if copy is not None else None   # where the skipped work now sits
        moved = [t for t in _repack(db, pending, today + timedelta(days=1), new_mpd,
                                    _blocked_days(db, roadmap.user_id)) if t is not landing]
        if copy is not None:
            end_after = _end_date(db, roadmap.roadmap_id)
            delay = (end_after - end_before).days
            tail = (f"Your plan now ends on {end_after} ({delay} day{'s' if delay != 1 else ''} later)."
                    if delay > 0 else f"Your plan still ends on {end_after}.")
            messages.insert(0, f"Skipped task moved to {landing.scheduled_date}. {tail}")
            db.add(models.AdaptationLog(roadmap_id=roadmap.roadmap_id, date=today, event="task_skipped",
                                        detail=f"'{skills[task.skill_id]}' task moved from {task.scheduled_date} "
                                               f"to {landing.scheduled_date}; {n_replanned} later tasks re-planned; "
                                               f"plan ends {end_after}"))
        elif moved:
            messages.append(f"{n_replanned} upcoming tasks were re-planned.")
    db.commit()
    return {"task": task_item(task, skills, resources),
            "adaptation": {"changed": bool(messages), "messages": messages, "daily_minutes": new_mpd,
                           "roadmap_end_date": _end_date(db, roadmap.roadmap_id)}}


@router.post("/breaks")
def add_break(body: schemas.BreakIn, db: Session = Depends(get_db)):
    if body.end_date < body.start_date:
        raise HTTPException(422, "end_date must not be before start_date.")
    length = (body.end_date - body.start_date).days + 1
    if length > 60:
        raise HTTPException(422, "A break can be at most 60 days.")
    profile = _profile(db, body.user_id)
    roadmap = _active_roadmap(db, body.user_id)
    today = body.on_date or date.today()

    brk = models.StudyBreak(user_id=body.user_id, start_date=body.start_date, end_date=body.end_date)
    db.add(brk)
    db.flush()

    affected = _pending_ordered(db, roadmap.roadmap_id, from_date=body.start_date)
    moved = len(affected)                                    # tasks the break pushes back
    affected, _ = _merge_adjacent(db, affected)
    if affected:
        restart = max(body.end_date + timedelta(days=1), today)
        _repack(db, affected, restart, _minutes_per_day(profile), _blocked_days(db, body.user_id),
                ease_days=adaptation.EASE_DAYS)
    new_end = _end_date(db, roadmap.roadmap_id)
    msg = (f"Break of {length} day(s) added. Your upcoming tasks move to after the break, the first "
           f"{adaptation.EASE_DAYS} days back are lighter, and the plan now ends on {new_end}." if moved else
           f"Break of {length} day(s) added. No tasks were affected.")
    db.add(models.AdaptationLog(roadmap_id=roadmap.roadmap_id, date=today, event="break_added",
                                detail=f"{body.start_date} to {body.end_date}: {moved} tasks moved; plan ends {new_end}"))
    db.commit()
    return {"break_id": brk.break_id, "tasks_moved": moved, "new_end_date": new_end, "message": msg}


@router.get("/adaptation-log/{user_id}")
def adaptation_log(user_id: int, db: Session = Depends(get_db)):
    rows = (db.query(models.AdaptationLog, models.Roadmap.version)
            .join(models.Roadmap, models.Roadmap.roadmap_id == models.AdaptationLog.roadmap_id)
            .filter(models.Roadmap.user_id == user_id)
            .order_by(models.AdaptationLog.log_id.desc()).all())
    return [{"date": l.date, "event": l.event, "detail": l.detail, "roadmap_version": v} for l, v in rows]
