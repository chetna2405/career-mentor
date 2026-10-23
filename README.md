# Career Mentor

**Personalized career guidance and adaptive learning roadmap using machine learning.**

A student describes a goal and the skills they already have. The website finds the career path, works out the skill
gap, builds a day-wise roadmap with learning resources, and re-plans when the student skips tasks, takes a break,
or studies consistently.

## How it works
1. **Goal classifier** (ML): goal text in Hinglish or English to one of 3 careers, with a confidence score.
   Low confidence means the website asks the user to confirm.
2. **Skill matcher** (ML): typed skills ("py", "javscript", "writing unit tests") to standard skills using aliases,
   fuzzy matching and sentence embeddings. Uncertain matches are shown as "did you mean...?".
3. **Skill gap and roadmap**: required skills minus known skills, ordered so prerequisites come first, spread over
   days according to the hours per day and the target date.
4. **Resource recommender** (content-based scoring + feedback): ranks resources for the learner's level and daily
   time, and learns from "helpful / not helpful" votes.
5. **Adaptation** (rules): skipped tasks are re-planned; 3 skipped days in a row lower the daily time by 20%;
   5 completed days raise it by 10%; breaks are honoured and the return is eased.

## Run it
```
pip install -r ml/requirements.txt
pip install -r backend/requirements.txt
cd ml                        # open and run the notebooks once (01 creates ml/models/goal_classifier.joblib)
cd ../backend
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/ . Details: `backend/README.md`, `frontend/README.md`.
Tests: `cd backend && python -m pytest -q`

## Project structure
```
data/       skills, prerequisites, goal sentences, resources (CSV) and test / rating sheets
ml/         notebooks 01 to 03, skill_matcher.py, recommender.py
backend/    FastAPI app, planner, adaptation rules, tests
frontend/   the website (HTML, CSS, JavaScript)
docs/       scope, database design, API design
```

## Results so far
| Component | Result | How it was measured |
|---|---|---|
| Goal classifier | 91% accuracy, 0.91 macro-F1 | 5-fold cross-validation on 122 sentences |
| Skill matcher | 58.9% (aliases only), 72.2% (+ fuzzy), 93.3% (+ embeddings) | 90 test inputs; the thresholds were chosen on the same set |
| Resource recommender | 4.29 / 5 average rating | 3 team members rated 32 recommendations (96 ratings) |
| Backend | 74 automated tests pass | `pytest` |
| Website | full flow checked in a real browser (Chromium) | 32 checks, no console errors |

## Known limitations
- One demo user; there is no login yet.
- Small data: 3 careers, 42 skills, 84 resources (two per skill), 122 goal sentences.
- Skill-matcher thresholds were tuned on the same test set, so its score is optimistic; a held-out set is still to do.
- The recommender was rated by the team itself; ratings from outside classmates are still to be collected.
- Adaptation rules are designed by hand (not learned); every day, including weekends, is a study day.
