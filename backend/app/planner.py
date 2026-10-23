"""Skill gap, ordering and day-wise scheduling.

Pure functions (no database, no web framework), so they are easy to test and explain:
  compute_gap   -> which skills the user still has to learn
  order_skills  -> put them in a valid learning order (prerequisites first)
  build_segments-> split one skill's study time across its recommended resources
  schedule      -> spread everything over calendar days, respecting minutes per day
"""
import heapq
from collections import defaultdict
from datetime import date, timedelta


def ancestors(skill_ids, prereqs):
    """All direct and indirect prerequisites of the given skills."""
    seen, stack = set(), list(skill_ids)
    while stack:
        s = stack.pop()
        for p in prereqs.get(s, ()):
            if p not in seen:
                seen.add(p)
                stack.append(p)
    return seen


def compute_gap(career_skills, known, prereqs):
    """
    career_skills: {skill_id: priority} required for the career
    known:         set of skill ids the user already has
    prereqs:       {skill_id: set(prerequisite ids)}

    Returns (gap, implied_known)
      gap:           {skill_id: {"priority": int, "reason": str, "prereq_of": id | None}}
      implied_known: skills assumed known because they are prerequisites of something the user knows
                     (someone who knows Pandas already knows NumPy and Python)
    """
    implied = ancestors(known, prereqs) - known
    known_all = known | implied

    gap = {}
    for sid, pr in career_skills.items():
        if sid not in known_all:
            gap[sid] = {"priority": pr, "reason": "required for this career", "prereq_of": None}

    # a missing prerequisite of a gap skill must be learned too, even if the career list does not name it
    stack = list(gap)
    while stack:
        s = stack.pop()
        for p in prereqs.get(s, ()):
            if p not in known_all and p not in gap:
                gap[p] = {"priority": gap[s]["priority"], "reason": "prerequisite", "prereq_of": s}
                stack.append(p)
    return gap, implied


def order_skills(gap, prereqs, difficulty):
    """
    Topological order: a skill never comes before its prerequisites.
    Among skills that are ready at the same time we pick:
      1. higher priority first (1 before 2 before 3)
      2. easier first
      3. the one that unlocks more other skills
      4. skill id (so the order is always the same)
    """
    deps = {s: {p for p in prereqs.get(s, ()) if p in gap} for s in gap}
    children = defaultdict(set)
    for s, ps in deps.items():
        for p in ps:
            children[p].add(s)

    memo = {}

    def n_unlocked(s):
        if s not in memo:
            seen, stack = set(), list(children[s])
            while stack:
                c = stack.pop()
                if c not in seen:
                    seen.add(c)
                    stack.extend(children[c])
            memo[s] = len(seen)
        return memo[s]

    def key(s):
        return (gap[s]["priority"], difficulty[s], -n_unlocked(s), s)

    ready = [(key(s), s) for s in gap if not deps[s]]
    heapq.heapify(ready)
    order = []
    while ready:
        _, s = heapq.heappop(ready)
        order.append(s)
        for c in children[s]:
            deps[c].discard(s)
            if not deps[c]:
                heapq.heappush(ready, (key(c), c))
    if len(order) != len(gap):
        raise ValueError("Prerequisite cycle detected in the skill data")
    return order


def build_segments(total_minutes, resources):
    """
    Split a skill's study time: first the recommended resources (up to their own duration),
    and whatever time is left becomes hands-on practice (resource_id None).
    The minutes always add up to total_minutes.
    """
    segments, remaining = [], total_minutes
    for r in resources:
        if remaining <= 0:
            break
        m = min(r["duration_min"], remaining)
        segments.append((r["resource_id"], m))
        remaining -= m
    if remaining > 0:
        segments.append((None, remaining))
    return segments


def schedule(plan, minutes_per_day, start, blocked=frozenset()):
    """
    plan: [(skill_id, [(resource_id | None, minutes), ...]), ...] in learning order
    Fills each day up to minutes_per_day, then moves to the next day. Days in `blocked` (study breaks) stay empty.
    Returns a list of task dicts.
    """
    def open_day(d):
        while d in blocked:
            d += timedelta(days=1)
        return d

    day = open_day(start)
    free, tasks = minutes_per_day, []
    for skill_id, segments in plan:
        for resource_id, minutes in segments:
            while minutes > 0:
                if free == 0:
                    day = open_day(day + timedelta(days=1))
                    free = minutes_per_day
                take = min(minutes, free)
                tasks.append({"skill_id": skill_id, "resource_id": resource_id, "date": day, "minutes": take})
                minutes -= take
                free -= take
    return tasks
