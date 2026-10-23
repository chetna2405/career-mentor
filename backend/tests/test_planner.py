"""Tests for the pure planning functions, using the real CSV data."""
import csv
from collections import defaultdict
from datetime import date
from pathlib import Path

import pytest

from app import planner

DATA = Path(__file__).resolve().parent.parent.parent / "data"


def _rows(name):
    with open(DATA / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


PREREQS = defaultdict(set)
for r in _rows("prerequisites.csv"):
    PREREQS[r["skill_id"]].add(r["prereq_skill_id"])
DIFF = {r["skill_id"]: int(r["difficulty"]) for r in _rows("skills.csv")}
HOURS = {r["skill_id"]: int(r["est_hours"]) for r in _rows("skills.csv")}
CAREERS = defaultdict(dict)
for r in _rows("career_skills.csv"):
    CAREERS[r["career"]][r["skill_id"]] = int(r["priority"])


@pytest.mark.parametrize("career", sorted(CAREERS))
def test_order_respects_prerequisites_for_every_career(career):
    gap, _ = planner.compute_gap(CAREERS[career], set(), PREREQS)
    order = planner.order_skills(gap, PREREQS, DIFF)
    assert sorted(order) == sorted(gap)                       # nothing lost, nothing repeated
    pos = {s: i for i, s in enumerate(order)}
    for s in order:
        for p in PREREQS.get(s, ()):
            assert pos[p] < pos[s], f"{p} must come before {s}"


def test_order_is_deterministic():
    gap, _ = planner.compute_gap(CAREERS["Web Developer"], set(), PREREQS)
    assert planner.order_skills(gap, PREREQS, DIFF) == planner.order_skills(gap, PREREQS, DIFF)


def test_web_roadmap_starts_with_html():
    gap, _ = planner.compute_gap(CAREERS["Web Developer"], set(), PREREQS)
    assert planner.order_skills(gap, PREREQS, DIFF)[0] == "S04"


def test_known_skills_leave_the_gap():
    gap, implied = planner.compute_gap(CAREERS["Data Scientist"], {"S01", "S20"}, PREREQS)
    assert "S01" not in gap and "S20" not in gap
    assert "S19" in implied and "S19" not in gap             # knowing Pandas implies NumPy


def test_missing_prerequisite_is_added():
    # a career list that names Pandas but not its prerequisites
    gap, _ = planner.compute_gap({"S20": 1}, set(), PREREQS)
    assert set(gap) == {"S20", "S19", "S01"}
    assert gap["S19"]["reason"] == "prerequisite" and gap["S19"]["prereq_of"] == "S20"


def test_knowing_everything_gives_empty_gap():
    gap, _ = planner.compute_gap(CAREERS["Web Developer"], set(CAREERS["Web Developer"]), PREREQS)
    assert gap == {}


def test_cycle_is_detected():
    with pytest.raises(ValueError):
        planner.order_skills({"A": {"priority": 1}, "B": {"priority": 1}}, {"A": {"B"}, "B": {"A"}}, {"A": 1, "B": 1})


def test_segments_always_add_up():
    res = [{"resource_id": "R1", "duration_min": 300}, {"resource_id": "R2", "duration_min": 200}]
    for total in (100, 300, 450, 500, 900):
        assert sum(m for _, m in planner.build_segments(total, res)) == total
    assert planner.build_segments(900, res)[-1] == (None, 400)       # leftover = practice
    assert planner.build_segments(100, res) == [("R1", 100)]


def test_schedule_respects_daily_limit_and_total():
    gap, _ = planner.compute_gap(CAREERS["Software Engineer"], set(), PREREQS)
    order = planner.order_skills(gap, PREREQS, DIFF)
    plan = [(s, [(None, HOURS[s] * 60)]) for s in order]
    tasks = planner.schedule(plan, 90, date(2026, 1, 1))
    per_day = defaultdict(int)
    for t in tasks:
        per_day[t["date"]] += t["minutes"]
    assert max(per_day.values()) <= 90
    assert sum(per_day.values()) == sum(HOURS[s] * 60 for s in order)
    days = sorted(per_day)
    assert (days[-1] - days[0]).days + 1 == len(days)               # no empty days in between
    assert [t["date"] for t in tasks] == sorted(t["date"] for t in tasks)


def test_schedule_leaves_blocked_days_empty():
    plan = [("S01", [(None, 240)])]
    tasks = planner.schedule(plan, 120, date(2026, 1, 1), blocked={date(2026, 1, 1), date(2026, 1, 3)})
    assert [t["date"] for t in tasks] == [date(2026, 1, 2), date(2026, 1, 4)]
