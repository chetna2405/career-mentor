# 🔌 API Design — Endpoints & JSON Formats
**Project:** Career Mentor | **Base URL:** `/api/v1` | **Auth:** Bearer JWT

---

## 📋 Endpoint Index

| Method | Endpoint                          | Description                        | Auth |
|--------|-----------------------------------|------------------------------------|------|
| POST   | /auth/register                    | Naya user register karo            | ❌   |
| POST   | /auth/login                       | Login + JWT token lo               | ❌   |
| GET    | /auth/me                          | Apni profile dekho                 | ✅   |
| POST   | /goals/analyze                    | Goal text → career detect karo     | ✅   |
| GET    | /goals/history                    | Past goals ki list                 | ✅   |
| GET    | /careers                          | Saare careers list karo            | ❌   |
| GET    | /careers/{career_id}              | Ek career ki detail                | ❌   |
| GET    | /careers/{career_id}/skills       | Career ki skills (priority order)  | ✅   |
| GET    | /skills/{skill_id}                | Ek skill ki detail                 | ✅   |
| GET    | /skills/{skill_id}/resources      | Skill ke resources (filtered)      | ✅   |
| GET    | /skills/{skill_id}/prerequisites  | Skill ki prerequisites chain       | ✅   |
| GET    | /roadmaps                         | User ke saare roadmaps             | ✅   |
| POST   | /roadmaps                         | Naya roadmap banao                 | ✅   |
| GET    | /roadmaps/{roadmap_id}            | Roadmap detail + items             | ✅   |
| PATCH  | /roadmaps/{roadmap_id}            | Roadmap update (pause/resume)      | ✅   |
| POST   | /roadmaps/{roadmap_id}/reschedule | Roadmap reschedule karo            | ✅   |
| PATCH  | /roadmaps/{roadmap_id}/items/{item_id} | Item status update karo       | ✅   |
| GET    | /progress/summary                 | Overall progress dashboard data    | ✅   |
| POST   | /resources/{resource_id}/log      | Resource progress log karo         | ✅   |
| GET    | /resources/{resource_id}/log      | Resource ka progress dekho         | ✅   |

---

## 🔐 Auth Endpoints

### POST /auth/register
**Request:**
```json
{
  "name": "Rahul Sharma",
  "email": "rahul@example.com",
  "password": "SecurePass123",
  "preferred_lang": "hinglish",
  "current_level": "beginner"
}
```
**Response 201:**
```json
{
  "success": true,
  "data": {
    "user_id": "uuid-xxxx",
    "name": "Rahul Sharma",
    "email": "rahul@example.com",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_expires_in": 86400
  }
}
```
**Error 400:**
```json
{
  "success": false,
  "error": { "code": "EMAIL_EXISTS", "message": "Email already registered" }
}
```

---

### POST /auth/login
**Request:**
```json
{ "email": "rahul@example.com", "password": "SecurePass123" }
```
**Response 200:**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGci...",
    "token_expires_in": 86400,
    "user": { "user_id": "uuid-xxxx", "name": "Rahul Sharma", "current_level": "beginner" }
  }
}
```

---

## 🎯 Goal Analysis Endpoint

### POST /goals/analyze
Yeh endpoint ML classifier call karta hai.

**Request:**
```json
{
  "text": "mujhe data science seekhna hai aur python bhi",
  "save": true
}
```
**Response 200:**
```json
{
  "success": true,
  "data": {
    "goal_id": "uuid-yyyy",
    "raw_text": "mujhe data science seekhna hai aur python bhi",
    "detected_career": "data_scientist",
    "career_name": "Data Scientist",
    "confidence": 0.9231,
    "all_probabilities": {
      "data_scientist": 0.9231,
      "web_developer": 0.0412,
      "full_stack_developer": 0.0357
    },
    "detected_skills": [
      { "skill_id": "S01", "skill_name": "Python", "match_method": "alias", "score": 1.0 },
      { "skill_id": "S10", "skill_name": "Machine Learning", "match_method": "semantic", "score": 0.82 }
    ],
    "suggested_next": "roadmap_create"
  }
}
```
**Low confidence response (confidence < 0.6):**
```json
{
  "success": true,
  "data": {
    "detected_career": null,
    "confidence": 0.42,
    "clarification_needed": true,
    "clarification_question": "Aap development mein zyada interested hain ya data analysis mein?",
    "options": ["Data Scientist", "Web Developer", "Full Stack Developer"]
  }
}
```

---

## 🗺️ Roadmap Endpoints

### POST /roadmaps
**Request:**
```json
{
  "career_id": "data_scientist",
  "hours_per_week": 10,
  "start_date": "2026-10-15",
  "include_priority": [1, 2],
  "skip_known_skills": ["S01", "S12"]
}
```
**Response 201:**
```json
{
  "success": true,
  "data": {
    "roadmap_id": "uuid-rmap",
    "career_id": "data_scientist",
    "career_name": "Data Scientist",
    "total_weeks": 18,
    "hours_per_week": 10,
    "start_date": "2026-10-15",
    "target_date": "2027-02-18",
    "total_skills": 14,
    "status": "active",
    "items": [
      {
        "item_id": "uuid-i1",
        "week_number": 1,
        "skill_id": "S06",
        "skill_name": "NumPy",
        "est_hours": 15,
        "planned_date": "2026-10-15",
        "status": "pending",
        "order_in_week": 1
      },
      {
        "item_id": "uuid-i2",
        "week_number": 1,
        "skill_id": "S05",
        "skill_name": "Pandas",
        "est_hours": 20,
        "planned_date": "2026-10-15",
        "status": "pending",
        "order_in_week": 2
      }
    ]
  }
}
```

---

### GET /roadmaps/{roadmap_id}
**Response 200:**
```json
{
  "success": true,
  "data": {
    "roadmap_id": "uuid-rmap",
    "career_name": "Data Scientist",
    "status": "active",
    "progress_pct": 23.5,
    "total_weeks": 18,
    "current_week": 4,
    "weeks_remaining": 14,
    "start_date": "2026-10-15",
    "target_date": "2027-02-18",
    "skills_done": 3,
    "skills_total": 14,
    "current_week_items": [
      {
        "item_id": "uuid-i5",
        "skill_id": "S07",
        "skill_name": "Data Visualization",
        "status": "in_progress",
        "resources": [
          {
            "resource_id": "R018",
            "title": "Data Visualization with Python - IBM Coursera",
            "type": "course",
            "url": "https://coursera.org/...",
            "level": "beginner",
            "is_free": true,
            "progress_pct": 40
          }
        ]
      }
    ],
    "upcoming_weeks": [
      { "week": 5, "skills": ["Machine Learning", "Scikit-Learn"] }
    ]
  }
}
```

---

### POST /roadmaps/{roadmap_id}/reschedule
**Request:**
```json
{
  "reason": "busy_week",
  "new_hours_per_week": 7,
  "extend_deadline": true,
  "skip_item_ids": []
}
```
**Response 200:**
```json
{
  "success": true,
  "data": {
    "roadmap_id": "uuid-rmap",
    "old_target_date": "2027-02-18",
    "new_target_date": "2027-03-15",
    "old_total_weeks": 18,
    "new_total_weeks": 22,
    "rescheduled_items": 11,
    "message": "Roadmap successfully rescheduled. Naya target: 15 March 2027"
  }
}
```

---

### PATCH /roadmaps/{roadmap_id}/items/{item_id}
**Request:**
```json
{
  "status": "done",
  "actual_date": "2026-11-02"
}
```
**Response 200:**
```json
{
  "success": true,
  "data": {
    "item_id": "uuid-i5",
    "skill_id": "S07",
    "status": "done",
    "actual_date": "2026-11-02",
    "streak_days": 5,
    "roadmap_progress_pct": 28.5,
    "next_item": {
      "skill_id": "S10",
      "skill_name": "Machine Learning",
      "week_number": 5
    },
    "achievement": null
  }
}
```

---

## 🔍 Skills & Resources Endpoints

### GET /skills/{skill_id}/resources
**Query params:** `?level=beginner&free_only=true&type=video,course&max_duration=120`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "skill_id": "S01",
    "skill_name": "Python",
    "total_resources": 5,
    "filters_applied": { "level": "beginner", "free_only": true },
    "resources": [
      {
        "resource_id": "R003",
        "title": "Python Crash Course - YouTube freeCodeCamp",
        "type": "video",
        "url": "https://youtube.com/watch?v=rfscVS0vtbw",
        "level": "beginner",
        "duration_min": 240,
        "is_free": true,
        "hybrid_score": 0.891
      },
      {
        "resource_id": "R001",
        "title": "Python for Everybody - Coursera",
        "type": "course",
        "url": "https://coursera.org/...",
        "level": "beginner",
        "duration_min": 1200,
        "is_free": true,
        "hybrid_score": 0.874
      }
    ]
  }
}
```

---

### GET /skills/{skill_id}/prerequisites
**Response 200:**
```json
{
  "success": true,
  "data": {
    "skill_id": "S10",
    "skill_name": "Machine Learning",
    "prereq_chain": [
      { "skill_id": "S01", "skill_name": "Python",  "level": 1, "user_status": "completed" },
      { "skill_id": "S02", "skill_name": "Statistics & Probability", "level": 1, "user_status": "not_started" },
      { "skill_id": "S03", "skill_name": "Linear Algebra", "level": 1, "user_status": "not_started" }
    ],
    "can_start": false,
    "blocking_skills": ["S02", "S03"]
  }
}
```

---

## 📊 Progress Dashboard Endpoint

### GET /progress/summary
**Response 200:**
```json
{
  "success": true,
  "data": {
    "user": { "name": "Rahul Sharma", "current_level": "beginner" },
    "active_roadmap": {
      "roadmap_id": "uuid-rmap",
      "career_name": "Data Scientist",
      "progress_pct": 28.5,
      "streak_days": 5,
      "target_date": "2027-02-18",
      "weeks_remaining": 14,
      "on_track": true
    },
    "skills_summary": {
      "total": 14,
      "completed": 4,
      "in_progress": 1,
      "pending": 9
    },
    "this_week": {
      "hours_studied": 6.5,
      "hours_planned": 10,
      "skills_touched": ["Data Visualization"],
      "resources_completed": 2
    },
    "total_hours_studied": 42,
    "badges_earned": ["first_skill", "5_day_streak"]
  }
}
```

---

## ⚠️ Standard Error Format

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Roadmap not found",
    "details": null
  }
}
```

**Common Error Codes:**

| Code                  | HTTP | Meaning                           |
|-----------------------|------|-----------------------------------|
| INVALID_INPUT         | 400  | Request body validation fail      |
| UNAUTHORIZED          | 401  | Token missing ya expired          |
| FORBIDDEN             | 403  | Resource kisi aur ka hai          |
| RESOURCE_NOT_FOUND    | 404  | ID se kuch nahi mila              |
| LOW_CONFIDENCE        | 200  | Goal samajh nahi aaya, clarify lo |
| DUPLICATE_ROADMAP     | 409  | Same career ka roadmap already hai|
| INTERNAL_ERROR        | 500  | Server crash                      |
