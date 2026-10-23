import csv
from datetime import date, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent.parent / "data"
START = date(2026, 11, 2)


def day(n):
    return START + timedelta(days=n)


def setup(client, hours=2):
    client.post("/api/profile", json={"user_id": 1, "goal_text": "mujhe websites banane hain", "level": "beginner",
                                      "hours_per_day": hours, "skills_text": []})
    return client.post("/api/roadmap/generate", json={"user_id": 1, "start_date": START.isoformat()}).json()


def today(client, d):
    return client.get("/api/tasks/today/1", params={"on_date": d.isoformat()}).json()


def patch(client, task_id, status, d):
    return client.patch(f"/api/tasks/{task_id}", json={"status": status, "on_date": d.isoformat()})


def all_tasks(client):
    rm = client.get("/api/roadmap/1").json()
    return [t for w in rm["weeks"] for dd in w["days"] for t in dd["tasks"]]


def per_day(tasks, statuses=("pending", "done")):
    out = {}
    for t in tasks:
        if t["status"] in statuses:
            out[t["scheduled_date"]] = out.get(t["scheduled_date"], 0) + t["planned_minutes"]
    return out


def hours(client):
    return client.get("/api/profile/1").json()["hours_per_day"]


# ---------- today ----------
def test_today_lists_tasks_and_overdue(client):
    setup(client)
    t = today(client, day(0))
    assert t["tasks"] and 0 < t["total_minutes"] <= 120 and t["overdue"] == [] and t["on_break"] is False
    later = today(client, day(5))
    assert later["overdue"] and all(o["status"] == "pending" and o["scheduled_date"] < day(5).isoformat()
                                    for o in later["overdue"])


# ---------- done / undo ----------
def test_mark_done_and_undo(client):
    setup(client)
    tid = today(client, day(0))["tasks"][0]["task_id"]
    r = patch(client, tid, "done", day(0)).json()
    assert r["task"]["status"] == "done" and r["adaptation"]["changed"] is False
    assert client.get("/api/roadmap/1").json()["progress"]["tasks_done"] == 1
    assert today(client, day(0))["done_minutes"] > 0
    assert patch(client, tid, "pending", day(0)).json()["task"]["status"] == "pending"
    assert client.get("/api/roadmap/1").json()["progress"]["tasks_done"] == 0


# ---------- skip ----------
def test_skip_moves_the_task_and_shifts_the_plan(client):
    r = setup(client)
    before = all_tasks(client)
    total_before = sum(t["planned_minutes"] for t in before)
    first = today(client, day(0))["tasks"][0]

    resp = patch(client, first["task_id"], "skipped", day(0)).json()
    assert resp["task"]["status"] == "skipped"
    assert resp["adaptation"]["changed"] and "Skipped task moved" in resp["adaptation"]["messages"][0]
    assert resp["adaptation"]["roadmap_end_date"] >= r["end_date"]

    after = all_tasks(client)
    skipped = [t for t in after if t["status"] == "skipped"]
    assert [t["task_id"] for t in skipped] == [first["task_id"]]
    assert sum(t["planned_minutes"] for t in after if t["status"] != "skipped") == total_before   # no work lost
    copies = [t for t in after if t["status"] == "pending" and t["original_date"] == day(0).isoformat()
              and t["skill_id"] == first["skill_id"] and t["reschedule_count"] >= 1]
    assert copies and min(c["scheduled_date"] for c in copies) > day(0).isoformat()
    assert max(per_day(after).values()) <= 120
    assert client.get("/api/roadmap/1").json()["progress"]["tasks_skipped"] == 1


def test_prerequisite_order_survives_a_skip(client):
    setup(client)
    patch(client, today(client, day(0))["tasks"][0]["task_id"], "skipped", day(0))
    first, last = {}, {}
    for t in sorted(all_tasks(client), key=lambda t: t["scheduled_date"]):
        if t["status"] == "skipped":
            continue
        first.setdefault(t["skill_id"], t["scheduled_date"])
        last[t["skill_id"]] = t["scheduled_date"]
    with open(DATA / "prerequisites.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["skill_id"] in first and r["prereq_skill_id"] in last:
                assert last[r["prereq_skill_id"]] <= first[r["skill_id"]], r


def test_task_update_validation(client):
    setup(client)
    tasks = today(client, day(0))["tasks"]
    future = today(client, day(3))["tasks"][0]["task_id"]
    assert patch(client, future, "skipped", day(0)).status_code == 409           # cannot skip a future task
    assert patch(client, 999999, "done", day(0)).status_code == 404
    tid = tasks[0]["task_id"]
    patch(client, tid, "skipped", day(0))
    assert patch(client, tid, "done", day(0)).status_code == 409                 # skipped is final
    assert client.patch(f"/api/tasks/{tid}", json={"status": "later"}).status_code == 422
    old_id = today(client, day(0))["tasks"][-1]["task_id"]
    setup(client)                                                                 # new roadmap version
    assert patch(client, old_id, "done", day(0)).status_code == 409              # old roadmap is read-only


# ---------- streak rules ----------
def test_three_skipped_days_reduce_the_daily_time(client):
    setup(client, hours=2)
    last = None
    for k in range(3):
        for t in today(client, day(k))["tasks"]:
            last = patch(client, t["task_id"], "skipped", day(k)).json()
    assert any("reduced" in m for m in last["adaptation"]["messages"])
    assert last["adaptation"]["daily_minutes"] == 95
    assert abs(hours(client) - 95 / 60) < 0.01
    log = client.get("/api/adaptation-log/1").json()
    assert "workload_reduced" in [e["event"] for e in log]
    assert max(per_day(all_tasks(client), ("pending",)).values()) <= 95           # the new plan uses 95 min/day


def test_five_done_days_increase_the_daily_time(client):
    setup(client, hours=2)
    for k in range(5):
        for t in today(client, day(k))["tasks"]:
            patch(client, t["task_id"], "done", day(k))
    assert abs(hours(client) - 130 / 60) < 0.01
    assert "workload_increased" in [e["event"] for e in client.get("/api/adaptation-log/1").json()]
    assert max(per_day(all_tasks(client), ("pending",)).values()) <= 130


def test_two_skipped_days_do_not_change_the_workload(client):
    setup(client, hours=2)
    for k in range(2):
        for t in today(client, day(k))["tasks"]:
            patch(client, t["task_id"], "skipped", day(k))
    assert hours(client) == 2


# ---------- breaks ----------
def test_break_moves_tasks_and_eases_the_return(client):
    r = setup(client)
    before = {t["task_id"]: t["scheduled_date"] for t in all_tasks(client)}
    res = client.post("/api/breaks", json={"user_id": 1, "start_date": day(2).isoformat(),
                                           "end_date": day(4).isoformat(), "on_date": day(0).isoformat()}).json()
    assert res["tasks_moved"] > 0 and res["new_end_date"] > r["end_date"]
    after = all_tasks(client)
    dates = {t["scheduled_date"] for t in after}
    assert not dates & {day(2).isoformat(), day(3).isoformat(), day(4).isoformat()}   # nothing during the break
    for t in after:                                                                    # earlier tasks untouched
        if t["task_id"] in before and before[t["task_id"]] < day(2).isoformat():
            assert t["scheduled_date"] == before[t["task_id"]]
    totals = per_day(after)
    assert totals[day(5).isoformat()] <= 60 and totals[day(6).isoformat()] <= 60       # lighter first two days
    assert max(totals.values()) <= 120


def test_break_validation(client):
    setup(client)
    assert client.post("/api/breaks", json={"start_date": "2026-11-05", "end_date": "2026-11-04"}).status_code == 422
    assert client.post("/api/breaks", json={"start_date": "2026-11-05", "end_date": "2027-02-01"}).status_code == 422
    assert client.post("/api/breaks", json={"user_id": 777, "start_date": "2026-11-05",
                                            "end_date": "2026-11-06"}).status_code == 404


def test_today_on_a_break_day_and_skips_avoid_breaks(client):
    setup(client)
    client.post("/api/breaks", json={"user_id": 1, "start_date": day(1).isoformat(),
                                     "end_date": day(2).isoformat(), "on_date": day(0).isoformat()})
    t = today(client, day(1))
    assert t["on_break"] is True and t["tasks"] == [] and "break" in t["message"]
    patch(client, today(client, day(0))["tasks"][0]["task_id"], "skipped", day(0))
    dates = {t["scheduled_date"] for t in all_tasks(client)}
    assert day(1).isoformat() not in dates and day(2).isoformat() not in dates


# ---------- log ----------
def test_adaptation_log_is_newest_first(client):
    setup(client)
    patch(client, today(client, day(0))["tasks"][0]["task_id"], "skipped", day(0))
    log = client.get("/api/adaptation-log/1").json()
    assert [e["event"] for e in log][:2] == ["task_skipped", "roadmap_generated"]
    assert all({"date", "event", "detail", "roadmap_version"} <= set(e) for e in log)


def test_a_break_does_not_cut_tasks_into_pieces(client):
    setup(client)
    before = len(all_tasks(client))
    client.post("/api/breaks", json={"user_id": 1, "start_date": day(2).isoformat(),
                                     "end_date": day(4).isoformat(), "on_date": day(0).isoformat()})
    after = [t for t in all_tasks(client) if t["status"] != "skipped"]
    assert len(after) <= before + 3                         # before the fix every task was split in two
    assert sum(t["planned_minutes"] for t in after) == sum(t["planned_minutes"] for t in all_tasks(client))


def test_repeated_skips_and_breaks_keep_the_task_count_stable(client):
    setup(client)
    before = len(all_tasks(client))
    for k in range(2):                                      # two skipped days: below the 3-day workload rule
        for t in today(client, day(k))["tasks"][:1]:
            patch(client, t["task_id"], "skipped", day(k))
    assert hours(client) == 2
    client.post("/api/breaks", json={"user_id": 1, "start_date": day(6).isoformat(),
                                     "end_date": day(7).isoformat(), "on_date": day(3).isoformat()})
    live = [t for t in all_tasks(client) if t["status"] != "skipped"]
    assert len(live) <= before + 6
