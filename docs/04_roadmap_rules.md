# 🗺️ Roadmap Generator & Rescheduling Rules
**Project:** Career Mentor | **Version:** v1.0 | Phase 3

---

## PART 1: Roadmap Generator Algorithm

### 1.1 Input Parameters

| Parameter         | Type    | Default  | Description                              |
|-------------------|---------|----------|------------------------------------------|
| career_id         | string  | required | e.g. "data_scientist"                    |
| hours_per_week    | int     | 10       | User ki available time (5–20h)           |
| start_date        | date    | today    | Roadmap start kab se                     |
| include_priority  | list    | [1, 2]   | Kaunsi priority skills include karni     |
| skip_skill_ids    | list    | []       | Already known skills (skip karo)         |
| user_level        | string  | beginner | beginner / intermediate / advanced       |

---

### 1.2 Step-by-Step Generation Algorithm

```
FUNCTION generate_roadmap(career_id, hours_per_week, start_date,
                           include_priority, skip_skill_ids, user_level):

  STEP 1: SKILLS FETCH
  ─────────────────────
  skills = career_skills
           WHERE career = career_id
           AND priority IN include_priority
           AND skill_id NOT IN skip_skill_ids
           ORDER BY priority ASC

  STEP 2: TOPOLOGICAL SORT (Prerequisites DAG)
  ─────────────────────────────────────────────
  graph = build_prerequisite_graph(skills)

  # Kahn's Algorithm for topological ordering
  in_degree = {skill: count of prerequisites for skill in skills}
  queue = [skills where in_degree == 0]  # no prerequisites
  ordered_skills = []

  WHILE queue not empty:
    skill = queue.pop_front()  # FIFO for stable ordering
    ordered_skills.append(skill)
    FOR each dependent_skill of skill:
      in_degree[dependent_skill] -= 1
      IF in_degree[dependent_skill] == 0:
        queue.push(dependent_skill)

  # If cycle detected (shouldn't happen with clean data):
  IF len(ordered_skills) != len(skills):
    RAISE CycleDetectedError

  STEP 3: WITHIN SAME LEVEL — SORT BY PRIORITY THEN DIFFICULTY
  ─────────────────────────────────────────────────────────────
  # Topologically equal skills sort karo
  ordered_skills = stable_sort(ordered_skills,
    key = (priority ASC, difficulty ASC, est_hours ASC))

  STEP 4: PACK INTO WEEKS (BIN PACKING)
  ──────────────────────────────────────
  week_capacity = hours_per_week
  current_week = 1
  current_week_hours = 0
  roadmap_items = []

  FOR each skill in ordered_skills:
    skill_hours = skill.est_hours

    # Ek skill ko multiple weeks mein split kar sakte hain
    remaining_hours = skill_hours
    order_in_week = 1

    WHILE remaining_hours > 0:
      space_this_week = week_capacity - current_week_hours

      IF space_this_week <= 0:
        current_week += 1
        current_week_hours = 0
        space_this_week = week_capacity

      hours_this_week = MIN(remaining_hours, space_this_week)
      roadmap_items.append({
        skill_id: skill.id,
        week_number: current_week,
        planned_hours: hours_this_week,
        order_in_week: order_in_week,
        status: 'pending'
      })

      current_week_hours += hours_this_week
      remaining_hours -= hours_this_week
      order_in_week += 1

      # Week overflow → next week
      IF current_week_hours >= week_capacity:
        current_week += 1
        current_week_hours = 0

  STEP 5: CALCULATE DATES
  ──────────────────────
  total_weeks = current_week
  target_date = start_date + (total_weeks * 7 days)

  FOR each item in roadmap_items:
    item.planned_date = start_date + ((item.week_number - 1) * 7 days)

  STEP 6: SAVE & RETURN
  ──────────────────────
  roadmap = save_to_db(roadmap_items, total_weeks, target_date)
  RETURN roadmap
```

---

### 1.3 Example: Data Scientist (10h/week, skip Python)

```
Input skills (after skip): Statistics(40h), NumPy(15h), Pandas(20h),
             Data Viz(20h), ML(50h), Scikit(25h), EDA(20h), Feature Eng(30h)

After topological sort:
  Week 1: Statistics(40h) → splits into 4 weeks of 10h
  Week 5: NumPy(15h) + Pandas starts (10-15= -5 overflow → next week)
  ...

Output:
  Week 1-4: Statistics & Probability    (40h total)
  Week 5:   NumPy (15h) + Pandas (part) (10h)
  Week 6:   Pandas finish (10h)         (10h)
  Week 7:   Data Visualization          (10h+10h = split)
  Week 8:   Data Viz finish + EDA start
  ...
  Total: ~18 weeks | Target: 18 Feb 2027
```

---

## PART 2: Rescheduling Rules

### 2.1 Triggers for Rescheduling

| Trigger              | Condition                                     | Auto or Manual |
|----------------------|-----------------------------------------------|----------------|
| Week missed          | Current week ends with >50% items pending     | Auto (suggest) |
| Hours reduced        | User manually changes hours_per_week          | Manual         |
| Skill skipped        | User marks skill as "skip"                    | Auto           |
| Ahead of schedule    | User finishes >1 week early                  | Auto (compress)|
| Extended break       | User pauses roadmap for 7+ days              | Auto on resume |
| Target date changed  | User manually sets new deadline               | Manual         |

---

### 2.2 Rescheduling Algorithm (Core Rules)

```
FUNCTION reschedule_roadmap(roadmap_id, reason, new_hours_per_week,
                             extend_deadline, skip_item_ids):

  RULE R1: NEVER MOVE COMPLETED ITEMS
  ─────────────────────────────────────
  completed_items = items WHERE status = 'done'
  # Yeh items lock hain — touch mat karo

  RULE R2: IN_PROGRESS ITEM STAYS IN CURRENT WEEK
  ─────────────────────────────────────────────────
  in_progress_item = items WHERE status = 'in_progress'
  # Isko current week mein rakhna hai — shift mat karo

  RULE R3: RECALCULATE FROM CURRENT WEEK ONWARDS
  ─────────────────────────────────────────────────
  pending_items = items WHERE status IN ('pending', 'skipped')
  pending_items = SORT pending_items by (week_number, order_in_week)

  remaining_skills = [item.skill_id for item in pending_items]

  # Re-run bin packing with new hours_per_week
  new_items = bin_pack(remaining_skills,
                       hours_per_week = new_hours_per_week,
                       start_week = current_week + 1)

  RULE R4: PRESERVE PREREQUISITE ORDER
  ──────────────────────────────────────
  # Topological order kabhi nahi todna
  ASSERT topological_order_valid(new_items)

  RULE R5: DEADLINE EXTENSION
  ────────────────────────────
  IF extend_deadline = True:
    new_target_date = today + (new_total_weeks * 7 days)
  ELSE:
    # Compress into existing deadline — increase density
    available_weeks = (original_target - today).weeks
    new_hours_needed = sum(pending_skill.est_hours)
    required_weekly_hours = CEIL(new_hours_needed / available_weeks)

    IF required_weekly_hours > 25:
      WARN "Deadline achieve karna bahut mushkil hai. Extend karo?"
    ELSE:
      new_hours_per_week = required_weekly_hours

  RULE R6: MINIMUM WEEK GAP BETWEEN SKILLS
  ──────────────────────────────────────────
  # Ek skill ke beech mein 0 mandatory gap (continuous learning ok)
  # Lekin ek hi week mein maximum 3 different skills (cognitive load)
  IF skills_in_week > 3:
    overflow to next week

  RULE R7: SKIP LOGIC
  ─────────────────────
  FOR each skip_item_id in skip_item_ids:
    item = get_item(skip_item_id)
    item.status = 'skipped'
    # Check: kya is skill ke dependents hain?
    dependents = get_dependents(item.skill_id)
    IF dependents exist AND they are pending:
      WARN "Ye skill skip karne se {dependent} seekhna mushkil ho sakta hai"

  SAVE rescheduled items
  UPDATE roadmap.last_rescheduled_at = NOW()
  RETURN { old_target, new_target, weeks_changed, items_moved }
```

---

### 2.3 On-Track Detection Rules

```
FUNCTION is_on_track(roadmap):

  elapsed_weeks = (today - start_date).weeks
  expected_done = ROUND(total_skills * (elapsed_weeks / total_weeks))
  actual_done   = COUNT(items WHERE status = 'done')

  gap = expected_done - actual_done

  IF gap <= 0:   RETURN "on_track"   # Aage hain ya sahi time par
  IF gap == 1:   RETURN "slightly_behind"   # 1 skill peeche
  IF gap == 2:   RETURN "behind"            # 2 skills peeche
  IF gap >= 3:   RETURN "significantly_behind"  # Reschedule suggest karo
```

---

### 2.4 Rescheduling Reasons & Responses

| Reason Code      | User Display           | System Action                          |
|------------------|------------------------|----------------------------------------|
| `busy_week`      | Yeh hafte busy tha     | Push pending items by 1 week           |
| `skill_hard`     | Skill zyada mushkil thi| Add 1.5x buffer for remaining skills   |
| `reduce_hours`   | Time kam hai ab        | Recalculate with new hours_per_week    |
| `took_break`     | Break li thi           | Push all pending by break_duration     |
| `ahead_schedule` | Jaldi seekh liya       | Compress upcoming weeks                |
| `change_career`  | Career change karna hai| Archive old, generate new roadmap      |
| `skip_skill`     | Yeh skill nahi chahiye | Remove from roadmap, warn if prereq    |

---

### 2.5 Notification Rules (Trigger Conditions)

```
Daily Check (run at 9 AM):

IF today = planned_date of any item AND item.status = 'pending':
  NOTIFY "Aaj {skill_name} start karo! 📚"

IF current_week.skills_done == 0 AND current_week.day >= 4 (Thursday):
  NOTIFY "Abhi tak kuch nahi seekha is hafte. Chalo shuru karte hain! 🔥"

IF consecutive_missed_days >= 3:
  NOTIFY "3 din se nahi pada. Roadmap reschedule karein? 🕐"

IF roadmap.progress_pct crosses [25, 50, 75, 100]:
  NOTIFY "{pct}% complete! 🎉 {milestone_message}"

IF streak_days == [3, 7, 14, 30]:
  NOTIFY "🔥 {days} day streak! Badge earned: {badge_name}"
```

---

### 2.6 Edge Cases & Guard Rules

| Edge Case                                     | Rule                                                  |
|-----------------------------------------------|-------------------------------------------------------|
| Circular prerequisites in data               | Detect cycle → raise error, log to admin              |
| All skills already known (skip_all)          | No items to schedule → suggest advanced roadmap       |
| hours_per_week < 5                           | Warn: "Minimum 5h/week recommended"                   |
| Skill has no resource in DB                  | Still add to roadmap, flag for content team           |
| Two roadmaps for same career                 | Allow (mark old as 'archived'), warn user             |
| Reschedule when 0 pending items remain       | Roadmap already complete → redirect to dashboard      |
| Prerequisite skill not in user's roadmap     | Auto-add with priority=2 before dependent skill       |
| User level = advanced, all diff=1 skills     | Skip difficulty=1, start from difficulty=2 directly   |

---

## PART 3: Learning Path Order — Visual Reference

```
DATA SCIENTIST PATH (Priority 1+2 only, beginner user, 10h/week):

Week  1-4: ┌─ Statistics & Probability (S02) ──────────────── 40h
Week  5:   ├─ NumPy (S06) ──────────── 15h
Week  5-6: ├─ Pandas (S05) ─────────────────── 20h
Week  7-8: ├─ Data Wrangling (S04) ───────────────── 25h (dep: S05)
Week  8-9: ├─ Data Visualization (S07) ────── 20h
Week 9-10: ├─ Matplotlib (S08) ──────── 15h (dep: S06)
Week 11:   ├─ EDA (S49) ─────── 20h (dep: S05, S07)
Week 11-16:├─ Machine Learning (S10) ─────────────────────── 50h (dep: S02,S03)
Week 17-18:└─ Scikit-Learn (S11) ──────────── 25h (dep: S10)

Total: ~18 weeks | 180 estimated hours at 10h/week

WEB DEVELOPER PATH (Priority 1+2, beginner, 10h/week):

Week 1-2:  ┌─ HTML (S21) ── 20h
Week 3-4:  ├─ CSS (S22) ───────── 25h
Week 5-8:  ├─ JavaScript (S23) ──────────────────── 40h
Week 8-9:  ├─ Responsive Design (S24) ─── 20h (dep: S22,S23)
Week 9-10: ├─ Git & GitHub (S26) ── 15h
Week 10-13:├─ React (S25) ──────────────────── 40h (dep: S23,S21)
Week 13:   ├─ Tailwind CSS (S38) ─ 15h (dep: S22)
Week 14-15:├─ Redux (S44) ────── 20h (dep: S25)
Week 16-17:└─ Testing (S45) ───── 20h (dep: S23)

Total: ~17 weeks
```
