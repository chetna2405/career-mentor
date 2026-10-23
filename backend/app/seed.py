"""Load the static CSV data into the database (only when the tables are empty)."""
import csv

from sqlalchemy.orm import Session

from . import models
from .config import DATA_DIR


def _read(name):
    with open(DATA_DIR / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def seed(db: Session):
    if db.query(models.Skill).count() == 0:
        db.add_all([models.Skill(skill_id=r["skill_id"], skill_name=r["skill_name"],
                                 difficulty=int(r["difficulty"]), est_hours=int(r["est_hours"]),
                                 aliases=r["aliases"]) for r in _read("skills.csv")])
        db.flush()
        db.add_all([models.CareerSkill(career=r["career"], skill_id=r["skill_id"], priority=int(r["priority"]))
                    for r in _read("career_skills.csv")])
        db.add_all([models.Prerequisite(skill_id=r["skill_id"], prereq_skill_id=r["prereq_skill_id"])
                    for r in _read("prerequisites.csv")])
        db.add_all([models.Resource(resource_id=r["resource_id"], skill_id=r["skill_id"], title=r["title"],
                                    type=r["type"], url=r["url"], level=r["level"],
                                    duration_min=int(r["duration_min"]), is_free=r["is_free"])
                    for r in _read("resources.csv")])
    if db.get(models.User, 1) is None:      # prototype uses one demo user
        db.add(models.User(user_id=1, name="Demo User", email="demo@example.com"))
    db.commit()
