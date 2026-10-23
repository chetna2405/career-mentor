def task_item(t, skills, resources):
    """One task as the API shows it. skills: {id: name}, resources: {id: Resource row}."""
    res = resources.get(t.resource_id)
    name = skills[t.skill_id]
    return {
        "task_id": t.task_id, "skill_id": t.skill_id, "skill_name": name,
        "title": f"{name}: {res.title}" if res else f"Practice {name}: build something small",
        "resource": {"resource_id": res.resource_id, "title": res.title, "type": res.type,
                     "url": res.url, "level": res.level} if res else None,
        "planned_minutes": t.planned_minutes, "status": t.status,
        "scheduled_date": t.scheduled_date, "original_date": t.original_date,
        "reschedule_count": t.reschedule_count,
    }
