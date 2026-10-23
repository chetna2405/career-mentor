def test_resources_are_ranked_for_the_learner(client):
    r = client.get("/api/resources/S31", params={"level": "beginner", "minutes_per_day": 60}).json()
    assert r["skill_name"] == "Algorithms" and 1 <= len(r["resources"]) <= 3
    scores = [x["score"] for x in r["resources"]]
    assert scores == sorted(scores, reverse=True)
    assert r["resources"][0]["level"] == "beginner" and r["resources"][0]["reasons"]
    r2 = client.get("/api/resources/S31", params={"level": "intermediate", "minutes_per_day": 240}).json()
    assert r2["resources"][0]["level"] == "intermediate"                      # different learner, different pick


def test_top_k_and_validation(client):
    assert len(client.get("/api/resources/S01", params={"top_k": 1}).json()["resources"]) == 1
    assert client.get("/api/resources/S999").status_code == 404
    assert client.get("/api/resources/S01", params={"level": "expert"}).status_code == 422
    assert client.get("/api/resources/S01", params={"minutes_per_day": 5}).status_code == 422
    assert client.get("/api/resources/S01", params={"top_k": 0}).status_code == 422


def test_feedback_counts_and_one_vote_per_user(client):
    rid = client.get("/api/resources/S02").json()["resources"][0]["resource_id"]
    a = client.post(f"/api/resources/{rid}/feedback", json={"user_id": 41, "helpful": True}).json()
    assert a["helpful"] == 1 and a["not_helpful"] == 0
    b = client.post(f"/api/resources/{rid}/feedback", json={"user_id": 41, "helpful": False}).json()   # changed mind
    assert b["total"] == 1 and b["helpful"] == 0 and b["not_helpful"] == 1
    c = client.post(f"/api/resources/{rid}/feedback", json={"user_id": 42, "helpful": True}).json()
    assert c["total"] == 2 and c["helpful"] == 1


def test_feedback_validation(client):
    assert client.post("/api/resources/R999/feedback", json={"helpful": True}).status_code == 404
    assert client.post("/api/resources/R01/feedback", json={}).status_code == 422


def test_feedback_changes_future_recommendations(client):
    first = client.get("/api/resources/S03", params={"level": "beginner"}).json()["resources"][0]["resource_id"]
    for u in range(100, 110):
        client.post(f"/api/resources/{first}/feedback", json={"user_id": u, "helpful": False})
    after = client.get("/api/resources/S03", params={"level": "beginner"}).json()["resources"]
    assert after[0]["resource_id"] != first
    assert any("found it helpful" in reason for r in after for reason in r["reasons"])
