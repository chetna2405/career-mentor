import csv, sys
from collections import defaultdict

def load(name):
    with open(name, encoding="utf-8") as f:
        return list(csv.DictReader(f))

skills = load("skills.csv"); cs = load("career_skills.csv")
pre = load("prerequisites.csv"); goals = load("goal_texts.csv"); res = load("resources.csv")
ids = {s["skill_id"] for s in skills}
errors = []

if len(ids) != len(skills): errors.append("duplicate skill_id in skills.csv")
for r in cs:
    if r["skill_id"] not in ids: errors.append(f"career_skills: unknown {r['skill_id']}")
for r in pre:
    for k in ("skill_id", "prereq_skill_id"):
        if r[k] not in ids: errors.append(f"prerequisites: unknown {r[k]}")
for r in res:
    if r["skill_id"] not in ids: errors.append(f"resources: unknown {r['skill_id']}")
for s in ids:
    if sum(1 for r in res if r["skill_id"] == s) < 2: errors.append(f"{s} has fewer than 2 resources")

graph = defaultdict(list)
for r in pre: graph[r["skill_id"]].append(r["prereq_skill_id"])
state = {}
def dfs(n):
    if state.get(n) == 1: errors.append(f"cycle at {n}"); return
    if state.get(n) == 2: return
    state[n] = 1
    for m in graph[n]: dfs(m)
    state[n] = 2
for n in ids: dfs(n)

aliases = defaultdict(list)
for s in skills:
    for a in s["aliases"].split("|"): aliases[a.lower()].append(s["skill_id"])
for a, v in aliases.items():
    if len(set(v)) > 1: errors.append(f"alias '{a}' used by {sorted(set(v))}")

print("skills:", len(skills), "| career_skills:", len(cs), "| prerequisites:", len(pre),
      "| goal_texts:", len(goals), "| resources:", len(res))
for c in sorted({r["career"] for r in goals}):
    print(f"  {c}: {sum(1 for r in goals if r['career']==c)} goal texts, "
          f"{sum(1 for r in cs if r['career']==c)} skills")
print("ERRORS:" if errors else "All checks passed.")
for e in errors: print(" -", e)
sys.exit(1 if errors else 0)
