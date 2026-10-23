"""Request and response shapes (see docs/api_design.md)."""
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

Level = Literal["beginner", "intermediate", "advanced"]


class ProfileIn(BaseModel):
    user_id: int = 1
    goal_text: str = Field(min_length=3, max_length=500)
    level: Level = "beginner"
    hours_per_day: float = Field(default=2, ge=0.25, le=12)
    target_date: date | None = None
    skills_text: list[str] = Field(default_factory=list, max_length=50)


class CareerGuess(BaseModel):
    career: str
    confidence: float


class MatchedSkill(BaseModel):
    raw_text: str
    skill_id: str | None = None
    skill_name: str | None = None
    score: float = 0.0
    method: str = "none"
    needs_confirmation: bool = False


class ProfileOut(BaseModel):
    predicted_career: str
    confidence: float
    alternatives: list[CareerGuess]
    needs_confirmation: bool
    matched_skills: list[MatchedSkill]


class SkillConfirm(BaseModel):
    raw_text: str
    skill_id: str | None = None      # None = the user rejected the suggestion


class ConfirmIn(BaseModel):
    user_id: int = 1
    career: str
    skills: list[SkillConfirm] = Field(default_factory=list)


class ProfileDetail(BaseModel):
    user_id: int
    goal_text: str
    predicted_career: str
    confidence: float
    confirmed_career: str | None
    level: str
    hours_per_day: float
    target_date: date | None
    skills: list[MatchedSkill]


class RoadmapIn(BaseModel):
    user_id: int = 1
    start_date: date | None = None       # defaults to today


class TaskUpdate(BaseModel):
    status: Literal["pending", "done", "skipped"]
    on_date: date | None = None          # "today" for demos and tests; defaults to the real date


class BreakIn(BaseModel):
    user_id: int = 1
    start_date: date
    end_date: date
    on_date: date | None = None


class FeedbackIn(BaseModel):
    user_id: int = 1
    helpful: bool
