from datetime import date, timedelta

from test_tasks import START, all_tasks, day, patch, setup, today


def dash(client, d=START):
    return client.get("/api/dashboard/1", params={"on_date": d.isoformat()})


def test_dashboard_needs_a_roadmap(client):
    assert client.get("/api/dashboard/9999").status_code == 404


def test_fresh_roadmap_dashboard(client):
    r = setup(client)
    d = dash(client).json()
    assert d["career"] == "Web Developer" and d["roadmap_version"] == r["version"]
    assert d["progress"]["percent"] == 0 and d["progress"]["tasks_done"] == 0
    assert d["progress"]["tasks_total"] == r["task_count"]
    assert d["time"]["planned_minutes"] == r["total_hours"] * 60 and d["time"]["done_minutes"] == 0
    assert d["skills"]["total"] == r["skills"] and d["skills"]["completed"] == 0
    assert d["skills"]["current"]["skill_id"] == d["skills"]["list"][0]["skill_id"]
    assert [s["status"] for s in d["skills"]["list"]][:2] == ["in_progress", "upcoming"]
    assert sum(w["planned_minutes"] for w in d["weekly"]) == d["time"]["planned_minutes"]
    assert d["streak"]["current_days"] == 0
    assert d["schedule"]["days_behind_original_plan"] == 0
    assert d["adaptation"] == {"tasks_skipped": 0, "tasks_rescheduled": 0, "breaks": 0, "workload_changes": 0}


def test_progress_after_completing_tasks(client):
    setup(client)
    for t in today(client, day(0))["tasks"]:
        patch(client, t["task_id"], "done", day(0))
    d = dash(client).json()
    assert d["time"]["done_minutes"] > 0 and d["progress"]["percent"] > 0
    assert d["time"]["remaining_minutes"] == d["time"]["planned_minutes"] - d["time"]["done_minutes"]
    assert d["streak"]["current_days"] == 1
    assert d["weekly"][0]["done_minutes"] == d["time"]["done_minutes"]


def test_a_finished_skill_moves_the_current_skill_on(client):
    setup(client)
    first = dash(client).json()["skills"]["list"][0]["skill_id"]
    for t in all_tasks(client):
        if t["skill_id"] == first:
            patch(client, t["task_id"], "done", START)
    s = dash(client).json()["skills"]
    assert s["completed"] == 1 and s["list"][0]["status"] == "completed" and s["list"][0]["percent"] == 100
    assert s["current"]["skill_id"] == s["list"][1]["skill_id"] and s["list"][1]["status"] == "in_progress"


def test_skip_and_break_show_up_in_the_dashboard(client):
    setup(client)
    patch(client, today(client, day(0))["tasks"][0]["task_id"], "skipped", day(0))
    d = dash(client).json()
    assert d["progress"]["tasks_skipped"] == 1 and d["adaptation"]["tasks_skipped"] == 1
    assert d["schedule"]["days_behind_original_plan"] == 1 and d["adaptation"]["tasks_rescheduled"] > 0
    client.post("/api/breaks", json={"user_id": 1, "start_date": day(3).isoformat(),
                                     "end_date": day(5).isoformat(), "on_date": day(0).isoformat()})
    d = dash(client).json()
    assert d["adaptation"]["breaks"] >= 1 and d["schedule"]["days_behind_original_plan"] > 1


def test_streak_and_workload_change(client):
    setup(client)
    for k in range(5):
        for t in today(client, day(k))["tasks"]:
            patch(client, t["task_id"], "done", day(k))
    d = dash(client, day(4)).json()
    assert d["streak"]["current_days"] == 5 and d["adaptation"]["workload_changes"] == 1
    assert d["time"]["hours_per_day"] > 2
    assert d["schedule"]["days_behind_original_plan"] < 0                      # a longer day means finishing earlier


def test_dashboard_total_minutes_never_change_when_adapting(client):
    r = setup(client)
    patch(client, today(client, day(0))["tasks"][0]["task_id"], "skipped", day(0))
    d = dash(client).json()
    assert d["time"]["planned_minutes"] == r["total_hours"] * 60               # skipped work is re-added, not lost
