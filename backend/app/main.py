from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import models  # noqa: F401  (registers the tables)
from sqlalchemy import inspect, text

from .config import FRONTEND_DIR
from .database import Base, SessionLocal, engine
from .ml_service import MLService
from .routers import dashboard, meta, profile, resources, roadmap, tasks
from .seed import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    # small migration: databases created before v0.3 have no tasks.seq column
    if "seq" not in {c["name"] for c in inspect(engine).get_columns("tasks")}:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN seq INTEGER NOT NULL DEFAULT 0"))
        with SessionLocal() as db:                      # old roadmaps: learning order = date order
            for (rid,) in db.query(models.Roadmap.roadmap_id).all():
                rows = (db.query(models.Task).filter_by(roadmap_id=rid)
                        .order_by(models.Task.scheduled_date, models.Task.task_id).all())
                for i, t in enumerate(rows):
                    t.seq = i
            db.commit()
    if "original_end_date" not in {c["name"] for c in inspect(engine).get_columns("roadmaps")}:
        with engine.begin() as conn:                    # databases created before v0.5
            conn.execute(text("ALTER TABLE roadmaps ADD COLUMN original_end_date DATE"))
            conn.execute(text("UPDATE roadmaps SET original_end_date = "
                              "(SELECT MAX(original_date) FROM tasks WHERE tasks.roadmap_id = roadmaps.roadmap_id)"))
    with SessionLocal() as db:
        seed(db)
    app.state.ml = MLService()
    yield


app = FastAPI(title="Career Mentor API", version="0.5", lifespan=lifespan)

# the frontend (opened from a file or another port) must be allowed to call the API
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(meta.router)
app.include_router(profile.router)
app.include_router(roadmap.router)
app.include_router(tasks.router)
app.include_router(resources.router)
app.include_router(dashboard.router)

# the website: served from the same address as the API (http://127.0.0.1:8000). Must be mounted last.
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
