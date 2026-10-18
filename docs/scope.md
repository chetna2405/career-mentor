# Project scope: Personalized Career Guidance and Adaptive Learning Roadmap

## Careers (prototype)
1. Web Developer
2. Data Scientist
3. Software Engineer (DSA + backend + core CS)

## Features
**Must (prototype):** profile form, goal classifier, skill matcher, skill gap analysis,
roadmap generator, daily tasks, done/skip, break + rescheduling, resource recommendation,
progress dashboard.

**Should:** basic login, helpful / not helpful feedback on resources, weekly view.

**Nice:** skip-risk predictor, LLM mentor feedback, deployment.

## ML components
1. Goal classifier: TF-IDF + Logistic Regression (baseline), embeddings (comparison)
2. Skill matcher: normalize + alias/fuzzy match + embedding similarity
3. Resource recommender: similarity + filters

## Stack
FastAPI, SQLite (SQLAlchemy), scikit-learn, sentence-transformers (optional),
HTML/CSS/JS + Bootstrap + Chart.js.

## Roles
- A: data + ML
- B: backend
- C: frontend

## Rules
- Every person works on their own branch; merge to `main` through pull requests.
- Skill names use full standard names (e.g. "JavaScript"); short forms go in the aliases column.
