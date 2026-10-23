def test_health(client):
    r = client.get("/api/health").json()
    assert r["status"] == "ok" and r["embeddings"] is False


def test_careers(client):
    r = client.get("/api/careers").json()
    assert {c["career"] for c in r} == {"Web Developer", "Data Scientist", "Software Engineer"}
    assert all(c["skill_count"] > 10 for c in r)


def _form(**kw):
    body = {"user_id": 1, "goal_text": "mujhe websites banane hain", "level": "beginner",
            "hours_per_day": 2, "skills_text": ["py", "html5"]}
    body.update(kw)
    return body


def test_profile_prediction_and_skill_matching(client):
    r = client.post("/api/profile", json=_form(skills_text=["py, pyhton", "html and css", "photoshop"])).json()
    assert r["predicted_career"] == "Web Developer"
    assert r["confidence"] > 0.6 and r["needs_confirmation"] is False
    by_raw = {m["raw_text"]: m for m in r["matched_skills"]}
    assert by_raw["py"]["skill_id"] == "S01" and by_raw["py"]["method"] == "alias"
    assert by_raw["pyhton"]["skill_id"] == "S01" and by_raw["pyhton"]["method"] == "fuzzy"
    assert by_raw["html"]["skill_id"] == "S04" and by_raw["css"]["skill_id"] == "S05"
    assert by_raw["photoshop"]["skill_id"] is None and by_raw["photoshop"]["method"] == "none"


def test_other_careers(client):
    r = client.post("/api/profile", json=_form(goal_text="I want to build machine learning models")).json()
    assert r["predicted_career"] == "Data Scientist"
    r = client.post("/api/profile", json=_form(goal_text="mujhe DSA seekhna hai placement ke liye")).json()
    assert r["predicted_career"] == "Software Engineer"


def test_vague_goal_asks_for_confirmation(client):
    r = client.post("/api/profile", json=_form(goal_text="mujhe kuch samajh nahi aa raha career ke baare mein")).json()
    assert r["needs_confirmation"] is True
    assert len(r["alternatives"]) == 1


def test_resubmit_replaces_old_data(client):
    client.post("/api/profile", json=_form(skills_text=["py", "git"]))
    client.post("/api/profile", json=_form(skills_text=["numpy"]))
    p = client.get("/api/profile/1").json()
    assert [s["raw_text"] for s in p["skills"]] == ["numpy"]


def test_confirm_flow(client):
    client.post("/api/profile", json=_form(skills_text=["py", "excel"]))
    r = client.post("/api/profile/confirm", json={
        "user_id": 1, "career": "Data Scientist", "skills": [{"raw_text": "excel", "skill_id": "S20"}]})
    assert r.status_code == 200
    p = client.get("/api/profile/1").json()
    assert p["confirmed_career"] == "Data Scientist"
    ex = next(s for s in p["skills"] if s["raw_text"] == "excel")
    assert ex["skill_id"] == "S20" and ex["needs_confirmation"] is False


def test_confirm_validation(client):
    client.post("/api/profile", json=_form())
    assert client.post("/api/profile/confirm", json={"career": "Astronaut"}).status_code == 422
    assert client.post("/api/profile/confirm", json={
        "career": "Web Developer", "skills": [{"raw_text": "nope", "skill_id": None}]}).status_code == 422
    assert client.post("/api/profile/confirm", json={
        "career": "Web Developer", "skills": [{"raw_text": "py", "skill_id": "S999"}]}).status_code == 422
    assert client.post("/api/profile/confirm", json={"user_id": 99, "career": "Web Developer"}).status_code == 404


def test_form_validation(client):
    assert client.post("/api/profile", json=_form(goal_text="")).status_code == 422
    assert client.post("/api/profile", json=_form(level="expert")).status_code == 422
    assert client.post("/api/profile", json=_form(hours_per_day=0)).status_code == 422
    assert client.get("/api/profile/12345").status_code == 404


def test_skills_list(client):
    r = client.get("/api/skills").json()
    assert len(r) == 42 and r == sorted(r, key=lambda s: s["skill_name"])
    assert {"skill_id", "skill_name", "difficulty", "est_hours"} <= set(r[0])


def test_website_is_served_and_api_still_works(client):
    page = client.get("/")
    assert page.status_code == 200 and "Career Mentor" in page.text
    assert client.get("/js/app.js").status_code == 200 and client.get("/css/app.css").status_code == 200
    assert client.get("/api/health").json()["status"] == "ok"          # the static mount must not hide the API


def test_state_endpoint(client):
    assert client.get("/api/state/31337").json() == {"has_profile": False, "has_roadmap": False, "career": None}
    client.post("/api/profile", json={"user_id": 31337, "goal_text": "I want to become a data scientist"})
    st = client.get("/api/state/31337").json()
    assert st["has_profile"] is True and st["has_roadmap"] is False and st["career"] == "Data Scientist"
    client.post("/api/roadmap/generate", json={"user_id": 31337})
    assert client.get("/api/state/31337").json()["has_roadmap"] is True
