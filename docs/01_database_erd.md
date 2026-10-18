# 🗄️ Database Design — ERD & Schema Reference
**Project:** Career Mentor  
**Version:** v1.0 | Phase 3

---

## 📐 Entity Relationship Diagram (Mermaid)

`mermaid
erDiagram
    USERS {
        uuid        user_id       PK
        string      name
        string      email         UK
        string      password_hash
        string      preferred_lang  "en | hi | hinglish"
        string      current_level   "beginner | intermediate | advanced"
        timestamp   created_at
        timestamp   updated_at
    }

    CAREERS {
        string      career_id     PK  "e.g. data_scientist"
        string      career_name
        string      description
        string      avg_salary_range
        string      job_demand    "high | medium | low"
    }

    SKILLS {
        string      skill_id      PK  "S01..S50"
        string      skill_name
        int         difficulty    "1=easy 2=med 3=hard"
        int         est_hours
        text        aliases       "pipe-separated"
        string      category      "programming | math | tools | soft"
    }

    CAREER_SKILLS {
        string      career_id     FK
        string      skill_id      FK
        int         priority      "1=must 2=important 3=optional"
    }

    PREREQUISITES {
        string      skill_id       FK
        string      prereq_skill_id FK
    }

    RESOURCES {
        string      resource_id    PK  "R001..R109"
        string      skill_id       FK
        string      title
        string      type           "video | course | book | docs | article | tool"
        string      url
        string      level          "beginner | intermediate | advanced"
        int         duration_min
        boolean     is_free
        float       quality_score  "0-1, computed from user ratings"
    }

    USER_GOALS {
        uuid        goal_id        PK
        uuid        user_id        FK
        string      raw_text
        string      detected_career FK
        float       confidence_score
        timestamp   created_at
    }

    USER_SKILLS {
        uuid        user_skill_id  PK
        uuid        user_id        FK
        string      skill_id       FK
        string      status         "not_started | in_progress | completed"
        int         self_rating    "1-5"
        timestamp   started_at
        timestamp   completed_at
    }

    ROADMAPS {
        uuid        roadmap_id     PK
        uuid        user_id        FK
        string      career_id      FK
        string      status         "active | paused | completed"
        int         total_weeks
        int         hours_per_week
        date        start_date
        date        target_date
        timestamp   last_rescheduled_at
        timestamp   created_at
    }

    ROADMAP_ITEMS {
        uuid        item_id        PK
        uuid        roadmap_id     FK
        string      skill_id       FK
        int         week_number
        date        planned_date
        date        actual_date
        string      status         "pending | in_progress | done | skipped"
        int         order_in_week
    }

    RESOURCE_LOGS {
        uuid        log_id         PK
        uuid        user_id        FK
        string      resource_id    FK
        int         progress_pct   "0-100"
        int         rating         "1-5"
        text        notes
        timestamp   started_at
        timestamp   completed_at
    }

    SESSIONS {
        uuid        session_id     PK
        uuid        user_id        FK
        timestamp   login_at
        timestamp   logout_at
        int         study_minutes
    }

    USERS           ||--o{ USER_GOALS      : "creates"
    USERS           ||--o{ USER_SKILLS     : "tracks"
    USERS           ||--o{ ROADMAPS        : "has"
    USERS           ||--o{ RESOURCE_LOGS   : "logs"
    USERS           ||--o{ SESSIONS        : "opens"
    CAREERS         ||--o{ CAREER_SKILLS   : "requires"
    CAREERS         ||--o{ ROADMAPS        : "guides"
    SKILLS          ||--o{ CAREER_SKILLS   : "used_in"
    SKILLS          ||--o{ PREREQUISITES   : "depends_on"
    SKILLS          ||--o{ RESOURCES       : "taught_by"
    SKILLS          ||--o{ USER_SKILLS     : "learned_by"
    SKILLS          ||--o{ ROADMAP_ITEMS   : "scheduled_in"
    RESOURCES       ||--o{ RESOURCE_LOGS   : "tracked_in"
    ROADMAPS        ||--o{ ROADMAP_ITEMS   : "contains"
    USER_GOALS      }o--|| CAREERS         : "maps_to"
`

---

## 📋 Table Definitions (SQL)

### users
`sql
CREATE TABLE users (
    user_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name             VARCHAR(100) NOT NULL,
    email            VARCHAR(255) UNIQUE NOT NULL,
    password_hash    VARCHAR(255) NOT NULL,
    preferred_lang   VARCHAR(20)  DEFAULT 'hinglish'
                     CHECK (preferred_lang IN ('en','hi','hinglish')),
    current_level    VARCHAR(20)  DEFAULT 'beginner'
                     CHECK (current_level IN ('beginner','intermediate','advanced')),
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW()
);
`

### skills (reference table, pre-seeded from skills.csv)
`sql
CREATE TABLE skills (
    skill_id    VARCHAR(10) PRIMARY KEY,   -- S01, S02 ...
    skill_name  VARCHAR(100) NOT NULL,
    difficulty  SMALLINT CHECK (difficulty BETWEEN 1 AND 3),
    est_hours   SMALLINT,
    aliases     TEXT,                       -- "py|python3|python programming"
    category    VARCHAR(50)
);
`

### career_skills
`sql
CREATE TABLE career_skills (
    career_id   VARCHAR(50) REFERENCES careers(career_id),
    skill_id    VARCHAR(10) REFERENCES skills(skill_id),
    priority    SMALLINT CHECK (priority BETWEEN 1 AND 3),
    PRIMARY KEY (career_id, skill_id)
);
`

### prerequisites (DAG edges)
`sql
CREATE TABLE prerequisites (
    skill_id        VARCHAR(10) REFERENCES skills(skill_id),
    prereq_skill_id VARCHAR(10) REFERENCES skills(skill_id),
    PRIMARY KEY (skill_id, prereq_skill_id),
    CHECK (skill_id != prereq_skill_id)
);
`

### user_goals
`sql
CREATE TABLE user_goals (
    goal_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES users(user_id),
    raw_text         TEXT NOT NULL,
    detected_career  VARCHAR(50) REFERENCES careers(career_id),
    confidence_score NUMERIC(5,4) CHECK (confidence_score BETWEEN 0 AND 1),
    created_at       TIMESTAMP DEFAULT NOW()
);
`

### roadmaps
`sql
CREATE TABLE roadmaps (
    roadmap_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID NOT NULL REFERENCES users(user_id),
    career_id            VARCHAR(50) REFERENCES careers(career_id),
    status               VARCHAR(20) DEFAULT 'active'
                         CHECK (status IN ('active','paused','completed','archived')),
    total_weeks          SMALLINT NOT NULL,
    hours_per_week       SMALLINT NOT NULL,
    start_date           DATE NOT NULL,
    target_date          DATE NOT NULL,
    last_rescheduled_at  TIMESTAMP,
    created_at           TIMESTAMP DEFAULT NOW()
);
`

### roadmap_items
`sql
CREATE TABLE roadmap_items (
    item_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    roadmap_id    UUID NOT NULL REFERENCES roadmaps(roadmap_id) ON DELETE CASCADE,
    skill_id      VARCHAR(10) REFERENCES skills(skill_id),
    week_number   SMALLINT NOT NULL,
    planned_date  DATE,
    actual_date   DATE,
    status        VARCHAR(20) DEFAULT 'pending'
                  CHECK (status IN ('pending','in_progress','done','skipped')),
    order_in_week SMALLINT DEFAULT 1
);
`

### resource_logs
`sql
CREATE TABLE resource_logs (
    log_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(user_id),
    resource_id   VARCHAR(10) REFERENCES resources(resource_id),
    progress_pct  SMALLINT DEFAULT 0 CHECK (progress_pct BETWEEN 0 AND 100),
    rating        SMALLINT CHECK (rating BETWEEN 1 AND 5),
    notes         TEXT,
    started_at    TIMESTAMP DEFAULT NOW(),
    completed_at  TIMESTAMP
);
`

---

## 🔑 Indexes (Performance)

`sql
-- Fast user lookups
CREATE INDEX idx_user_goals_user    ON user_goals(user_id);
CREATE INDEX idx_user_skills_user   ON user_skills(user_id);
CREATE INDEX idx_roadmap_user       ON roadmaps(user_id);
CREATE INDEX idx_roadmap_items_rm   ON roadmap_items(roadmap_id);
CREATE INDEX idx_resource_logs_user ON resource_logs(user_id);

-- Fast skill-based queries
CREATE INDEX idx_career_skills_sid  ON career_skills(skill_id);
CREATE INDEX idx_prereq_skill       ON prerequisites(skill_id);
CREATE INDEX idx_resources_skill    ON resources(skill_id);
`

---

## 🔗 Key Relationships Summary

| Relation              | Type     | Notes                                    |
|-----------------------|----------|------------------------------------------|
| users → roadmaps      | 1 → many | Ek user ke multiple roadmaps ho sakte    |
| roadmaps → items      | 1 → many | Har roadmap mein ordered skill items     |
| skills → prerequisites| many → many | DAG structure, topological sort possible |
| careers → skills      | many → many | priority (1/2/3) ke saath               |
| resources → resource_logs | 1 → many | User progress tracking               |
| user_goals → careers  | many → 1 | ML classifier output yahan store hota   |

