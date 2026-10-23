# API Design (draft v1)

Base path: `/api`. All responses are JSON. Prototype uses `user_id = 1`.

## Onboarding
| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/careers | List the 3 careers |
| POST | /api/profile | Save the form, run goal classifier and skill matcher |
| POST | /api/profile/confirm | User confirms career and uncertain skill matches |

POST /api/profile request:
```json
{
  "user_id": 1,
  "goal_text": "mujhe websites banane hain",
  "level": "beginner",
  "hours_per_day": 2,
  "target_date": "2026-12-31",
  "skills_text": ["py", "html5", "excel"]
}
```
Response:
```json
{
  "predicted_career": "Web Developer",
  "confidence": 0.86,
  "alternatives": [{"career": "Software Engineer", "confidence": 0.09}],
  "needs_confirmation": false,
  "matched_skills": [
    {"raw_text": "py", "skill_id": "S01", "skill_name": "Python", "score": 1.0, "method": "alias", "needs_confirmation": false},
    {"raw_text": "excel", "skill_id": null, "skill_name": null, "score": 0.31, "method": "embedding", "needs_confirmation": true}
  ]
}
```

## Gap and roadmap
| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/gap/{user_id} | Required skills minus known skills |
| POST | /api/roadmap/generate | Build day-wise roadmap from the gap |
| GET | /api/roadmap/{user_id} | Active roadmap, tasks grouped by week |

## Tasks and adaptation
| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/tasks/today/{user_id} | Today's tasks with resources |
| PATCH | /api/tasks/{task_id} | Mark done or skipped; triggers adaptation |
| POST | /api/breaks | Add a study break; triggers rescheduling |
| GET | /api/adaptation-log/{user_id} | Why the plan changed |

PATCH /api/tasks/{task_id} request: `{"status": "skipped"}`
Response: `{"task_id": 12, "status": "skipped", "adaptation": {"changed": true, "message": "Task moved to 2026-11-05", "roadmap_version": 2}}`

## Resources and dashboard
| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/resources/{skill_id}?level=beginner | Ranked resources for a skill |
| POST | /api/resources/{resource_id}/feedback | Helpful / not helpful |
| GET | /api/dashboard/{user_id} | Progress %, tasks done / skipped, streak, hours studied |

## Notes
- Frontend and backend both follow these JSON shapes. Any change is agreed first, then this file is updated.
- Skill matches with low score return needs_confirmation = true so the UI can ask the user.
- FastAPI generates live docs at /docs (Swagger), used for testing before the frontend exists.

---

# Implemented in backend v0.2 (real responses)

## GET /api/gap/{user_id}?start_date=2026-11-02
`start_date` is optional (defaults to today). Returns 409 if the career is uncertain and not confirmed yet,
404 if there is no profile.
```json
{
  "career": "Web Developer",
  "known_skills": [{"skill_id": "S04", "skill_name": "HTML"}, {"skill_id": "S05", "skill_name": "CSS"}],
  "implied_known": [],
  "gap": [
    {"order": 1, "skill_id": "S02", "skill_name": "Git and GitHub", "priority": 1, "est_hours": 8,
     "reason": "required for this career", "prerequisite_of": null}
  ],
  "total_hours": 270,
  "hours_per_day": 2.0,
  "estimated_days": 135,
  "pending_skill_confirmations": [],
  "target_date": null,
  "fits_target_date": null,
  "suggested_hours_per_day": null
}
```
- `implied_known`: skills assumed known because they are prerequisites of something the user knows (Pandas implies NumPy).
- `reason` is `"required for this career"` or `"prerequisite"` (then `prerequisite_of` names the skill that needs it).
- `pending_skill_confirmations`: typed skills with an unanswered "did you mean...?". They are not counted as known.

## POST /api/roadmap/generate
Request: `{"user_id": 1, "start_date": "2026-11-02"}` (start_date optional). Response:
```json
{
  "roadmap_id": 1, "version": 1, "career": "Web Developer",
  "start_date": "2026-11-02", "end_date": "2027-03-16", "total_days": 135,
  "skills": 14, "total_hours": 270, "task_count": 161,
  "warnings": []
}
```
If the user already knows everything: `{"roadmap_id": null, "message": "...", "warnings": []}`.
Generating again keeps the earlier roadmap with status "old" and increases `version`.

## GET /api/roadmap/{user_id}
```json
{
  "roadmap_id": 1, "version": 1, "career": "Web Developer",
  "start_date": "2026-11-02", "end_date": "2027-03-16",
  "progress": {"tasks_total": 161, "tasks_done": 0, "percent": 0.0},
  "weeks": [
    {"week": 1, "start_date": "2026-11-02", "end_date": "2026-11-08",
     "skills": ["Git and GitHub", "JavaScript"],
     "days": [
       {"date": "2026-11-02", "total_minutes": 120,
        "tasks": [
          {"task_id": 1, "skill_id": "S02", "skill_name": "Git and GitHub",
           "title": "Git and GitHub: GitHub Skills",
           "resource": {"resource_id": "R04", "title": "GitHub Skills", "type": "course",
                        "url": "https://skills.github.com/", "level": "beginner"},
           "planned_minutes": 120, "status": "pending"}
        ]}
     ]}
  ]
}
```
A task with `"resource": null` is a hands-on practice task ("Practice <skill>: build something small").

---

# Implemented in backend v0.3 (tasks, breaks, adaptation)

Every task object (in `/api/roadmap`, `/api/tasks/today`, and the PATCH response) now also has
`scheduled_date`, `original_date` and `reschedule_count`.
`/api/roadmap` progress is now `{"tasks_total", "tasks_done", "tasks_skipped", "percent"}`
(skipped tasks are not counted in `tasks_total`, because their work is re-added as a new task).

**"Today" for demos and tests:** `GET /api/tasks/today`, `PATCH /api/tasks/{id}` and `POST /api/breaks`
accept an optional `on_date` (`2026-11-02`) to pretend it is another day. The frontend normally leaves it out.

## GET /api/tasks/today/{user_id}?on_date=2026-11-02
```json
{
  "date": "2026-11-02", "on_break": false, "message": null,
  "total_minutes": 120, "done_minutes": 0,
  "tasks": [ { "task_id": 1, "skill_name": "HTML", "title": "HTML: freeCodeCamp Curriculum",
               "planned_minutes": 120, "status": "pending", "scheduled_date": "2026-11-02",
               "original_date": "2026-11-02", "reschedule_count": 0, "resource": { "...": "..." } } ],
  "overdue": []
}
```
`overdue` = pending tasks from earlier days. On a break day: `on_break: true`, empty `tasks`, and a `message`.

## PATCH /api/tasks/{task_id}
Request: `{"status": "done" | "skipped" | "pending", "on_date": "2026-11-02"}`
```json
{
  "task": { "task_id": 1, "status": "skipped", "...": "..." },
  "adaptation": {
    "changed": true,
    "messages": ["Skipped task moved to 2026-11-03. Your plan now ends on 2027-04-04 (1 day later)."],
    "daily_minutes": 120,
    "roadmap_end_date": "2027-04-04"
  }
}
```
Show `adaptation.messages` to the user. Allowed changes: pending to done, pending to skipped, done to pending.
A skipped task is final (its work is re-added as a new pending task). Errors (409): skipping a task scheduled in the
future, changing a skipped task, editing a task of an old roadmap version.

Adaptation rules:
| Situation | What happens |
|---|---|
| Task skipped | Same work is re-added from tomorrow; everything after it shifts |
| 3 skipped days in a row | Daily study time goes down by 20% (min 30 min) |
| 5 completed days in a row | Daily study time goes up by 10% (max 6 h) |
| Break | Break days stay empty, later tasks move after it, first 2 days back are half as long |

## POST /api/breaks
Request: `{"user_id": 1, "start_date": "2026-11-05", "end_date": "2026-11-07"}` (max 60 days; `on_date` optional)
```json
{ "break_id": 1, "tasks_moved": 175, "new_end_date": "2027-04-08",
  "message": "Break of 3 day(s) added. Your upcoming tasks move to after the break, the first 2 days back are lighter, and the plan now ends on 2027-04-08." }
```
A break in the past (the user was away) restarts the plan from today.

## GET /api/adaptation-log/{user_id}
Newest first: `[{"date": "2026-11-02", "event": "task_skipped", "detail": "...", "roadmap_version": 1}]`
Events: `roadmap_generated`, `task_skipped`, `workload_reduced`, `workload_increased`, `break_added`.

---

# Implemented in backend v0.4 (resources, feedback, dashboard)

## GET /api/resources/{skill_id}?level=beginner&minutes_per_day=120&top_k=3
`level`: beginner | intermediate | advanced. `minutes_per_day`: 15 to 720. `top_k`: 1 to 10. 404 for an unknown skill.
```json
{
  "skill_id": "S06", "skill_name": "JavaScript", "level": "beginner", "minutes_per_day": 120,
  "resources": [
    {"resource_id": "R11", "title": "JavaScript.info", "type": "docs", "url": "https://javascript.info/",
     "level": "beginner", "duration_min": 900, "score": 0.737, "estimated_days": 7.5,
     "reasons": ["matches your level", "about 7.5 days at 120 min/day"]},
    {"resource_id": "R12", "title": "MDN: JavaScript Guide", "level": "intermediate", "score": 0.517,
     "reasons": ["a slight stretch above your level", "about 5.0 days at 120 min/day"]}
  ]
}
```
Show `reasons` to the user ("why this resource"). Once 3 or more people voted, a reason like
"83% of 8 learners found it helpful" appears.

## POST /api/resources/{resource_id}/feedback
Request: `{"user_id": 1, "helpful": true}`. One vote per user and resource: voting again replaces the old vote.
```json
{"resource_id": "R11", "helpful": 1, "not_helpful": 0, "total": 1,
 "note": "Your vote improves the ranking of this resource for future roadmaps."}
```
Votes change the ranking when a roadmap is generated or `GET /api/resources` is called; an existing roadmap keeps its resources.

## GET /api/dashboard/{user_id}?on_date=2026-11-02
One call with everything the dashboard needs (`on_date` is optional and only for demos and tests).
```json
{
  "career": "Web Developer", "roadmap_version": 1, "today": "2026-11-02",
  "start_date": "2026-11-02", "end_date": "2027-04-03",
  "progress": {"percent": 0.7, "tasks_total": 177, "tasks_done": 1, "tasks_pending": 176, "tasks_skipped": 0},
  "time": {"planned_minutes": 18300, "done_minutes": 120, "remaining_minutes": 18180, "hours_per_day": 2.0},
  "streak": {"current_days": 1},
  "skills": {
    "total": 16, "completed": 0, "current": {"skill_id": "S04", "skill_name": "HTML"},
    "list": [{"skill_id": "S04", "skill_name": "HTML", "planned_minutes": 900, "done_minutes": 120,
              "percent": 13.3, "status": "in_progress"}]
  },
  "weekly": [{"week": 1, "planned_minutes": 840, "done_minutes": 120}],
  "schedule": {"original_end_date": "2027-04-03", "current_end_date": "2027-04-03", "days_behind_original_plan": 0},
  "adaptation": {"tasks_skipped": 0, "tasks_rescheduled": 0, "breaks": 0, "workload_changes": 0}
}
```
- `progress.percent` is by study minutes (a 2-hour task weighs more than a 10-minute one). Skipped tasks are not part of the plan, because their work is re-added.
- `skills.list[].status`: completed | in_progress (the skill being studied now) | upcoming.
- `streak.current_days`: study days in a row with every task done, up to today.
- `days_behind_original_plan`: positive means the plan now ends later than first planned (skips, breaks); negative means earlier (workload was increased).
- Suggested charts: `skills.list[].percent` as bars, `weekly` as planned vs done bars.

## Change in v0.4
A roadmap generated again now respects breaks the user already added (those days stay empty).

---

# Implemented in backend v0.5 (website, skills list, state)

## The website
The backend also serves the website: open `http://127.0.0.1:8000/` after starting the server. The files are in `frontend/`.
Every API path starts with `/api`, so the website and the API do not clash.

## GET /api/skills
All 42 standard skills, sorted by name (used for the "did you mean...?" dropdowns).
```json
[{"skill_id": "S06", "skill_name": "JavaScript", "difficulty": 2, "est_hours": 40}]
```

## GET /api/state/{user_id}
Where the user is in the journey; the website uses it to pick the first screen.
```json
{"has_profile": true, "has_roadmap": true, "career": "Web Developer"}
```

## Changes to earlier endpoints
- `GET /api/dashboard`: `schedule.original_end_date` is now the end date saved when the roadmap was generated, so
  `days_behind_original_plan` stays correct however often the plan is re-packed.
- Adaptation messages: "N later tasks re-planned" and the break's `tasks_moved` count the tasks that were pushed back.
- After a skip or a break, neighbouring pieces of the same resource are joined back together before re-packing,
  so tasks do not get cut into smaller and smaller pieces.
