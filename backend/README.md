# Backend (FastAPI)

## Run
```
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/ for the website, or http://127.0.0.1:8000/docs to try the API.

## Settings
- `USE_EMBEDDINGS=0` skips loading the sentence-transformers model (faster startup, alias + fuzzy matching only).
  On Windows PowerShell: `$env:USE_EMBEDDINGS="0"` before running uvicorn.
- The database file `career_mentor.db` is created on first start. If you change the CSV files in `data/`,
  delete `career_mentor.db` and restart so the tables are loaded again.

## Tests
```
cd backend
python -m pytest -q
```

## API at a glance (details in docs/api_design.md)
| Area | Endpoints |
|---|---|
| Onboarding | `GET /api/careers`, `POST /api/profile`, `POST /api/profile/confirm`, `GET /api/profile/{user_id}` |
| Plan | `GET /api/gap/{user_id}`, `POST /api/roadmap/generate`, `GET /api/roadmap/{user_id}` |
| Daily use | `GET /api/tasks/today/{user_id}`, `PATCH /api/tasks/{task_id}`, `POST /api/breaks`, `GET /api/adaptation-log/{user_id}` |
| Resources | `GET /api/resources/{skill_id}`, `POST /api/resources/{resource_id}/feedback` |
| Dashboard | `GET /api/dashboard/{user_id}` |
| Misc | `GET /api/health` |
