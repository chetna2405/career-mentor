# Frontend

Plain HTML, CSS and JavaScript (no build step). Bootstrap (CSS only) and Chart.js are included in `vendor/`,
so the site works without internet. The backend serves these files, so there is nothing separate to run:

```
cd backend
uvicorn app.main:app --reload
```
Then open http://127.0.0.1:8000/

## Screens
| Screen | Route | What it does |
|---|---|---|
| Profile | `#/profile` | Goal, level, hours per day, target date, skills you know |
| Review | `#/review` | Confirm the career and skills ("did you mean...?"), see the skill gap, generate the roadmap |
| Roadmap | `#/roadmap` | Week-by-week plan with resource links; the current week is open |
| Today | `#/today` | Today's tasks (done / skip / undo), overdue tasks, take a break, "why did my plan change?" |
| Dashboard | `#/dashboard` | Progress, time studied, streak, schedule, two charts |

## Demo date (top right: "Today is")
The plan adapts over days, so for demos you can pretend it is another day: change the date, or press **+1 day**.
A "demo date" badge shows while it is active; **Reset** returns to the real date.
Typical demo: mark today's task done, press +1 day, skip a task, read the message, add a break, open the dashboard.

## Files
```
index.html        page shell (navigation, demo-date control)
css/app.css       styles
js/api.js         API calls, date helpers, the demo date
js/views.js       the five screens
js/app.js         routing and navigation
vendor/           Bootstrap CSS 5.3.3 and Chart.js 4.4.3 (MIT licence, see vendor/README.md)
```
All text that comes from users or the database is escaped before it is shown.
