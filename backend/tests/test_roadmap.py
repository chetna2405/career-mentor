import csv
from collections import defaultdict
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent.parent / "data"
START = "2026-11-02"


def _form(**kw):
    body = {"user_id": 1, "goal_text": "mujhe websites banane hain", "level": "beginner",
            "hours_per_day": 2, "skills_text": ["html", "css", "js"]}
    body.update(kw)
    return body


def test_gap_for_web_developer(client):
    client.post("/api/profile", json=_form())
    g = client.get("/api/gap/1").json()
    assert g["career"] == "Web Developer"
    assert {s["skill_id"] for s in g["known_skills"]} == {"S04", "S05", "S06"}
    ids = [s["skill_id"] for s in g["gap"]]
    assert "S09" in ids and "S04" not in ids and "S06" not in ids
    assert [s["order"] for s in g["gap"]] == list(range(1, len(ids) + 1))
    assert g["total_hours"] == sum(s["est_hours"] for s in g["gap"])
    assert g["estimated_days"] == round(g["total_hours"] / 2 + 0.499)   # 2 h/day, rounded up


def test_gap_lists_known_skills_and_pending_confirmations(client):
    client.post("/api/profile", json=_form(skills_text=["python"]))
    g = client.get("/api/gap/1").json()
    assert {s["skill_id"] for s in g["known_skills"]} == {"S01"}
    assert isinstance(g["pending_skill_confirmations"], list)


def test_roadmap_generate_and_read(client):
    client.post("/api/profile", json=_form())
    r = client.post("/api/roadmap/generate", json={"user_id": 1, "start_date": START}).json()
    assert r["version"] >= 1 and r["task_count"] > 0 and r["start_date"] == START
    assert r["total_days"] == (date.fromisoformat(r["end_date"]) - date.fromisoformat(START)).days + 1

    rm = client.get("/api/roadmap/1").json()
    assert rm["roadmap_id"] == r["roadmap_id"] and rm["progress"]["tasks_done"] == 0
    assert rm["progress"]["tasks_total"] == r["task_count"]
    days = [d for w in rm["weeks"] for d in w["days"]]
    assert all(d["total_minutes"] <= 120 for d in days)                 # 2 h/day
    assert sum(d["total_minutes"] for d in days) == r["total_hours"] * 60
    assert days[0]["date"] == START
    first = days[0]["tasks"][0]
    assert first["resource"] is not None and first["resource"]["url"].startswith("http")


def test_prerequisites_are_scheduled_before_dependents(client):
    client.post("/api/profile", json=_form(skills_text=[]))
    client.post("/api/roadmap/generate", json={"user_id": 1, "start_date": START})
    rm = client.get("/api/roadmap/1").json()
    first, last = {}, {}
    for w in rm["weeks"]:
        for d in w["days"]:
            for t in d["tasks"]:
                first.setdefault(t["skill_id"], d["date"])
                last[t["skill_id"]] = d["date"]
    with open(DATA / "prerequisites.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["skill_id"] in first and r["prereq_skill_id"] in last:
                assert last[r["prereq_skill_id"]] <= first[r["skill_id"]], r


def test_regenerating_keeps_old_version_and_bumps_version(client):
    client.post("/api/profile", json=_form())
    v1 = client.post("/api/roadmap/generate", json={"user_id": 1, "start_date": START}).json()
    v2 = client.post("/api/roadmap/generate", json={"user_id": 1, "start_date": START}).json()
    assert v2["version"] == v1["version"] + 1
    assert client.get("/api/roadmap/1").json()["roadmap_id"] == v2["roadmap_id"]


def test_target_date_warning(client):
    client.post("/api/profile", json=_form(skills_text=[], hours_per_day=1, target_date="2026-12-01"))
    g = client.get("/api/gap/1").json()
    assert g["fits_target_date"] is False and g["suggested_hours_per_day"] > 1
    r = client.post("/api/roadmap/generate", json={"user_id": 1, "start_date": START}).json()
    assert r["warnings"] and "target date" in r["warnings"][0]


def test_roadmap_with_everything_known(client):
    with open(DATA / "career_skills.csv", encoding="utf-8", newline="") as f:
        web = [r["skill_id"] for r in csv.DictReader(f) if r["career"] == "Web Developer"]
    with open(DATA / "skills.csv", encoding="utf-8", newline="") as f:
        names = {r["skill_id"]: r["skill_name"] for r in csv.DictReader(f)}
    client.post("/api/profile", json=_form(skills_text=[names[s] for s in web]))
    r = client.post("/api/roadmap/generate", json={"user_id": 1}).json()
    assert r["roadmap_id"] is None and "already know" in r["message"]


def test_vague_goal_must_be_confirmed_first(client):
    client.post("/api/profile", json=_form(goal_text="mujhe kuch samajh nahi aa raha career ke baare mein"))
    assert client.get("/api/gap/1").status_code == 409
    assert client.post("/api/roadmap/generate", json={"user_id": 1}).status_code == 409
    client.post("/api/profile/confirm", json={"user_id": 1, "career": "Data Scientist"})
    assert client.get("/api/gap/1").json()["career"] == "Data Scientist"


def test_no_profile_or_roadmap(client):
    assert client.get("/api/gap/777").status_code == 404
    assert client.post("/api/roadmap/generate", json={"user_id": 777}).status_code == 404
    assert client.get("/api/roadmap/777").status_code == 404


def test_gap_and_generate_agree_about_the_target_date(client):
    client.post("/api/profile", json=_form(skills_text=[], hours_per_day=2, target_date="2027-03-01"))
    g = client.get("/api/gap/1", params={"start_date": START}).json()
    r = client.post("/api/roadmap/generate", json={"user_id": 1, "start_date": START}).json()
    assert g["fits_target_date"] is (not r["warnings"])


def test_new_roadmap_respects_existing_breaks(client):
    client.post("/api/profile", json=_form(skills_text=[]))
    client.post("/api/roadmap/generate", json={"user_id": 1, "start_date": START})
    client.post("/api/breaks", json={"user_id": 1, "start_date": "2026-11-04", "end_date": "2026-11-06",
                                     "on_date": START})
    r = client.post("/api/roadmap/generate", json={"user_id": 1, "start_date": START}).json()
    rm = client.get("/api/roadmap/1").json()
    dates = {d["date"] for w in rm["weeks"] for d in w["days"]}
    assert not dates & {"2026-11-04", "2026-11-05", "2026-11-06"} and "2026-11-07" in dates
    assert r["total_days"] == (date.fromisoformat(r["end_date"]) - date.fromisoformat(r["start_date"])).days + 1


def test_start_date_inside_a_break_moves_to_the_first_open_day(client):
    client.post("/api/profile", json=_form(skills_text=[]))
    client.post("/api/roadmap/generate", json={"user_id": 1, "start_date": START})
    client.post("/api/breaks", json={"user_id": 1, "start_date": START, "end_date": "2026-11-03", "on_date": START})
    r = client.post("/api/roadmap/generate", json={"user_id": 1, "start_date": START}).json()
    assert r["start_date"] == "2026-11-04"
