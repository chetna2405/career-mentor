"""Database tables. See docs/database_design.md and the ERD."""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


# ---------- static tables (loaded from data/*.csv) ----------
class Skill(Base):
    __tablename__ = "skills"
    skill_id: Mapped[str] = mapped_column(String, primary_key=True)
    skill_name: Mapped[str] = mapped_column(String)
    difficulty: Mapped[int] = mapped_column(Integer)
    est_hours: Mapped[int] = mapped_column(Integer)
    aliases: Mapped[str] = mapped_column(String, default="")


class CareerSkill(Base):
    __tablename__ = "career_skills"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    career: Mapped[str] = mapped_column(String, index=True)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.skill_id"))
    priority: Mapped[int] = mapped_column(Integer)


class Prerequisite(Base):
    __tablename__ = "prerequisites"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.skill_id"))
    prereq_skill_id: Mapped[str] = mapped_column(ForeignKey("skills.skill_id"))


class Resource(Base):
    __tablename__ = "resources"
    resource_id: Mapped[str] = mapped_column(String, primary_key=True)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.skill_id"), index=True)
    title: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    level: Mapped[str] = mapped_column(String)
    duration_min: Mapped[int] = mapped_column(Integer)
    is_free: Mapped[str] = mapped_column(String, default="yes")


# ---------- dynamic tables ----------
class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, default="")
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Profile(Base):
    __tablename__ = "profiles"
    profile_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), unique=True)
    goal_text: Mapped[str] = mapped_column(String)
    predicted_career: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    confirmed_career: Mapped[str | None] = mapped_column(String, nullable=True)
    level: Mapped[str] = mapped_column(String)
    hours_per_day: Mapped[float] = mapped_column(Float)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class UserSkill(Base):
    __tablename__ = "user_skills"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)
    raw_text: Mapped[str] = mapped_column(String)
    matched_skill_id: Mapped[str | None] = mapped_column(ForeignKey("skills.skill_id"), nullable=True)
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    match_method: Mapped[str] = mapped_column(String, default="none")   # alias / fuzzy / embedding / none
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)


class Roadmap(Base):
    __tablename__ = "roadmaps"
    roadmap_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)
    career: Mapped[str] = mapped_column(String)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, default="active")      # active / old
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    original_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)   # end date when first generated


class Task(Base):
    __tablename__ = "tasks"
    task_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    roadmap_id: Mapped[int] = mapped_column(ForeignKey("roadmaps.roadmap_id"), index=True)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.skill_id"))
    resource_id: Mapped[str | None] = mapped_column(ForeignKey("resources.resource_id"), nullable=True)
    scheduled_date: Mapped[date] = mapped_column(Date)
    original_date: Mapped[date] = mapped_column(Date)
    planned_minutes: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String, default="pending")     # pending / done / skipped
    reschedule_count: Mapped[int] = mapped_column(Integer, default=0)
    seq: Mapped[int] = mapped_column(Integer, default=0)               # position in the learning order


class StudyBreak(Base):
    __tablename__ = "study_breaks"
    break_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)


class ResourceFeedback(Base):
    __tablename__ = "resource_feedback"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    resource_id: Mapped[str] = mapped_column(ForeignKey("resources.resource_id"))
    helpful: Mapped[bool] = mapped_column(Boolean)


class AdaptationLog(Base):
    __tablename__ = "adaptation_log"
    log_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    roadmap_id: Mapped[int] = mapped_column(ForeignKey("roadmaps.roadmap_id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    event: Mapped[str] = mapped_column(String)
    detail: Mapped[str] = mapped_column(String, default="")
