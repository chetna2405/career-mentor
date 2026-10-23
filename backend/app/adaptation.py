"""Adaptation rules. Pure functions (no database), easy to test and to explain in the viva.

Rules:
  * a skipped task is re-added and everything after it shifts            -> pack()
  * 3 skipped days in a row  -> daily study time goes down by 20%        -> trailing_streaks(), reduce()
  * 5 fully completed days in a row -> daily study time goes up by 10%   -> trailing_streaks(), increase()
  * after a break the first 2 study days are half as long                -> pack(ease_days=2)
"""
from collections import defaultdict
from datetime import timedelta

SKIP_STREAK = 3          # skipped days in a row that trigger a reduction
DONE_STREAK = 5          # completed days in a row that trigger an increase
REDUCE_FACTOR = 0.8
INCREASE_FACTOR = 1.1
MIN_MINUTES = 30
MAX_MINUTES = 360
EASE_DAYS = 2            # days of reduced load after a break
EASE_FACTOR = 0.5


def _round5(x):
    return int(round(x / 5.0)) * 5


def reduce_minutes(minutes):
    return max(MIN_MINUTES, _round5(minutes * REDUCE_FACTOR))


def increase_minutes(minutes):
    return min(MAX_MINUTES, _round5(minutes * INCREASE_FACTOR))


def pack(minutes_list, start, minutes_per_day, ease_days=0, blocked=frozenset(), ease_factor=EASE_FACTOR):
    """
    Spread tasks over days, in order, starting on `start`.
    Days in `blocked` (study breaks) are skipped. The first `ease_days` open days get a reduced capacity.
    A task that does not fit in the rest of a day is split.
    Returns [(task_index, date, minutes), ...].
    """
    minutes_per_day = max(15, int(minutes_per_day))

    def open_day(d):
        while d in blocked:
            d += timedelta(days=1)
        return d

    def capacity(i):
        return max(15, int(minutes_per_day * ease_factor)) if i < ease_days else minutes_per_day

    day, open_index = open_day(start), 0
    free = capacity(0)
    out = []
    for i, m in enumerate(minutes_list):
        while m > 0:
            if free == 0:
                day = open_day(day + timedelta(days=1))
                open_index += 1
                free = capacity(open_index)
            take = min(m, free)
            out.append((i, day, take))
            m -= take
            free -= take
    return out


def trailing_streaks(rows, upto):
    """
    rows: iterable of (date, minutes, status) for one roadmap.
    Looks at the most recent study days up to `upto` and returns (kind, length, last_day) where kind is
      "skipped": days where at least as much was skipped as done
      "done":    days where everything was completed
    A day that still has pending tasks ends the streak (except `upto` itself, which may still be in progress).
    Days without tasks (breaks, gaps) are ignored.
    """
    per = defaultdict(lambda: {"done": 0, "skipped": 0, "pending": 0})
    for d, m, s in rows:
        if d <= upto:
            per[d][s] += m

    kind, n, last = None, 0, None
    for d in sorted(per, reverse=True):
        v = per[d]
        if v["pending"] > 0:
            if d == upto:
                continue
            break
        if v["skipped"] and v["skipped"] >= v["done"]:
            k = "skipped"
        elif v["done"] and not v["skipped"]:
            k = "done"
        else:
            break
        if kind is None:
            kind, last = k, d
        if k != kind:
            break
        n += 1
    return kind, n, last
