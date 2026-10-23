from datetime import date, timedelta

from app import adaptation as ad

D0 = date(2026, 11, 2)


def d(n):
    return D0 + timedelta(days=n)


# ---------- pack ----------
def test_pack_respects_capacity_and_keeps_totals():
    chunks = ad.pack([100, 100, 100], D0, 120)
    per_day = {}
    for _, day, m in chunks:
        per_day[day] = per_day.get(day, 0) + m
    assert max(per_day.values()) <= 120 and sum(per_day.values()) == 300
    assert [c[0] for c in chunks] == sorted(c[0] for c in chunks)        # task order kept
    assert [c[1] for c in chunks] == sorted(c[1] for c in chunks)        # dates never go backwards


def test_pack_splits_a_task_across_days():
    chunks = ad.pack([100, 100], D0, 120)
    assert [(i, m) for i, _, m in chunks] == [(0, 100), (1, 20), (1, 80)]


def test_pack_ease_in_after_a_break():
    chunks = ad.pack([300], D0, 120, ease_days=2)
    assert [(day, m) for _, day, m in chunks] == [(d(0), 60), (d(1), 60), (d(2), 120), (d(3), 60)]


def test_pack_skips_blocked_days():
    chunks = ad.pack([240], D0, 120, blocked={d(1)})
    assert [day for _, day, _ in chunks] == [d(0), d(2)]
    assert [day for _, day, _ in ad.pack([60], D0, 120, blocked={d(0), d(1)})] == [d(2)]


def test_pack_never_uses_a_capacity_below_15():
    assert ad.pack([30], D0, 5)[0][2] == 15


# ---------- streaks ----------
def rows(*days):
    """days: (day_number, status) with 60 minutes each."""
    return [(d(n), 60, s) for n, s in days]


def test_three_skipped_days_in_a_row():
    assert ad.trailing_streaks(rows((0, "skipped"), (1, "skipped"), (2, "skipped")), d(2)) == ("skipped", 3, d(2))


def test_five_done_days_and_gaps_are_ignored():
    r = rows((0, "done"), (1, "done"), (3, "done"), (4, "done"), (6, "done"))      # days 2 and 5 had no tasks
    assert ad.trailing_streaks(r, d(6)) == ("done", 5, d(6))


def test_pending_day_breaks_the_streak_but_today_in_progress_is_ignored():
    r = rows((0, "skipped"), (1, "pending"), (2, "skipped"))
    assert ad.trailing_streaks(r, d(2)) == ("skipped", 1, d(2))
    r = rows((0, "skipped"), (1, "skipped"), (2, "pending"))                        # today still in progress
    assert ad.trailing_streaks(r, d(2)) == ("skipped", 2, d(1))


def test_mixed_day_and_mixed_kinds_end_the_streak():
    assert ad.trailing_streaks(rows((0, "done"), (1, "skipped")), d(1)) == ("skipped", 1, d(1))
    r = [(d(0), 60, "done"), (d(0), 60, "skipped")]
    assert ad.trailing_streaks(r, d(0)) == ("skipped", 1, d(0))                      # equal amounts count as skipped
    assert ad.trailing_streaks(rows((0, "done")), d(0)) == ("done", 1, d(0))


def test_future_days_are_ignored():
    assert ad.trailing_streaks(rows((0, "done"), (5, "skipped")), d(1)) == ("done", 1, d(0))


def test_no_rows():
    assert ad.trailing_streaks([], d(0)) == (None, 0, None)


# ---------- workload changes ----------
def test_reduce_and_increase_minutes():
    assert ad.reduce_minutes(120) == 95 and ad.increase_minutes(120) == 130
    assert ad.reduce_minutes(30) == 30 and ad.increase_minutes(360) == 360
