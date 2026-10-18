# 📱 Wireframes — 6 App Screens
**Project:** Career Mentor | **Platform:** Mobile-first Web App

> ASCII wireframes reference ke liye hain. Actual implementation mein Figma/React components use honge.

---

## Screen 1: Onboarding / Goal Input

```
┌─────────────────────────────┐
│  🎯 Career Mentor            │
│  ─────────────────────────  │
│                              │
│  Apna career goal batao      │
│  (Hindi, English, dono ✓)   │
│                              │
│  ┌──────────────────────┐   │
│  │ "mujhe data science  │   │
│  │  seekhna hai..."     │   │
│  │                    🎤│   │
│  └──────────────────────┘   │
│                              │
│  Suggestions:                │
│  [Data Science] [Web Dev]   │
│  [Full Stack]  [ML/AI]      │
│                              │
│  ┌──────────────────────┐   │
│  │   🚀 Goal Analyze Karo  │   │
│  └──────────────────────┘   │
│                              │
│  Ya seedha choose karo:      │
│  > Data Scientist            │
│  > Web Developer             │
│  > Full Stack Developer      │
└─────────────────────────────┘
```

**Key UI Elements:**
- Multiline textarea (Hinglish + English support)
- 🎤 Voice input button (future feature)
- Quick-pick suggestion chips
- Primary CTA: "Analyze"
- Secondary: Direct career selection

---

## Screen 2: Career Detected Result

```
┌─────────────────────────────┐
│  ← Goal Analysis Result      │
│  ─────────────────────────  │
│                              │
│  "mujhe data science..."    │
│                              │
│  ┌──────────────────────┐   │
│  │  🏆 Data Scientist    │   │
│  │                      │   │
│  │  Match: ████████░  92%│   │
│  │                      │   │
│  │  Detected Skills:    │   │
│  │  🐍Python  📊Stats   │   │
│  │  🤖ML      🗃️SQL    │   │
│  └──────────────────────┘   │
│                              │
│  Other options:              │
│  Full Stack Dev   45%  >    │
│  Web Developer    38%  >    │
│                              │
│  ┌──────────────────────┐   │
│  │  📍 Roadmap Banao    │   │
│  └──────────────────────┘   │
│  [← Dobara Type Karo]       │
└─────────────────────────────┘
```

**Key UI Elements:**
- Detected career card (highlighted)
- Confidence bar (color coded: green>80%, yellow 60-80%, red<60%)
- Detected skill chips
- Alternative careers (tappable)
- Primary CTA: Create Roadmap
- Low confidence → shows clarification question instead

---

## Screen 3: Roadmap Setup / Configuration

```
┌─────────────────────────────┐
│  ← Roadmap Setup             │
│  Data Scientist 🏆           │
│  ─────────────────────────  │
│                              │
│  Hafte mein kitne ghante?    │
│  ┌──────────────────────┐   │
│  │  ●────────────  10h  │   │
│  │  5h           20h    │   │
│  └──────────────────────┘   │
│  Est. completion: ~18 weeks  │
│                              │
│  Kya pehle se kuch aata hai? │
│  ☑ Python    ☐ SQL          │
│  ☐ Statistics ☐ NumPy       │
│                              │
│  Kya include karna hai?      │
│  ● Must-have skills (P1)    │
│  ● Important skills  (P2)   │
│  ○ Optional skills   (P3)   │
│                              │
│  Start date: 15 Oct 2026    │
│                              │
│  ┌──────────────────────┐   │
│  │  🗺️ Roadmap Generate  │   │
│  └──────────────────────┘   │
└─────────────────────────────┘
```

**Key UI Elements:**
- Hours/week slider (5-20h range)
- Dynamic completion estimate (recalculates on slide)
- Known skills multi-select
- Priority level toggles
- Date picker

---

## Screen 4: Roadmap View (Main Screen)

```
┌─────────────────────────────┐
│  Data Scientist Roadmap  ⚙️  │
│  Progress: ████░░░░░  28%   │
│  Week 4 of 18 | On Track ✅  │
│  ─────────────────────────  │
│                              │
│  THIS WEEK ──────────────── │
│  ✅ NumPy        [Done]      │
│  🔄 Data Viz     [Active]   │
│     ████████░░  80% →       │
│                              │
│  NEXT WEEK ─────────────── │
│  ○ Machine Learning          │
│  ○ Scikit-Learn              │
│                              │
│  WEEK 6 ───────────────── │
│  ○ Feature Engineering       │
│  ○ Model Evaluation          │
│                              │
│  ─────────────────────────  │
│  🕐 Reschedule  📊 Stats    │
│  [─────────────────────────]│
│  🏠 Home  🗺️ Roadmap  👤 Me │
└─────────────────────────────┘
```

**Key UI Elements:**
- Global progress bar
- "On Track / Behind" status badge
- Collapsible week sections
- Per-item status (✅ done, 🔄 active, ○ pending)
- Resource progress mini-bar on active items
- Bottom: Reschedule + Stats buttons
- Tab bar navigation

---

## Screen 5: Skill Detail View

```
┌─────────────────────────────┐
│  ← Machine Learning    S10  │
│  ─────────────────────────  │
│  ⭐⭐⭐ Difficulty: Medium    │
│  ⏱ Est: 50 hours            │
│                              │
│  Prerequisites Chain:        │
│  ✅ Python (S01)             │
│      └──→ ✅ NumPy (S06)    │
│  ❌ Statistics (S02)  [Learn]│
│  ❌ Linear Algebra (S03) [!] │
│                              │
│  ⚠️ 2 prerequisites pending  │
│                              │
│  Recommended Resources:      │
│  ┌──────────────────────┐   │
│  │▶ ML Course - Andrew Ng    │
│  │  Coursera | 60h | FREE ✓ │
│  │  ⭐⭐⭐⭐⭐              │
│  └──────────────────────┘   │
│  ┌──────────────────────┐   │
│  │📖 Hands-On ML Book    │   │
│  │  O'Reilly | 800min   │   │
│  └──────────────────────┘   │
│                              │
│  ┌──────────────────────┐   │
│  │  📌 Roadmap mein Add  │   │
│  └──────────────────────┘   │
└─────────────────────────────┘
```

**Key UI Elements:**
- Difficulty stars
- Prerequisites visual chain (✅/❌ status)
- Warning if prereqs not done
- Resource cards (type icon, duration, free/paid badge)
- "Add to Roadmap" button (if not already there)

---

## Screen 6: Dashboard / Progress Summary

```
┌─────────────────────────────┐
│  👋 Namaste, Rahul!          │
│  🔥 5 day streak!            │
│  ─────────────────────────  │
│                              │
│       ╭───────╮             │
│      ╭│  28%  │╮            │
│      │╰───────╯│            │
│      │Data Sci │            │
│       ╰───────╯             │
│                              │
│  THIS WEEK                   │
│  ┌──────┬──────┬──────┐    │
│  │  6.5h│  2   │  5   │    │
│  │Studied│Done │Left  │    │
│  └──────┴──────┴──────┘    │
│                              │
│  UPCOMING (This Week):       │
│  🔄 Data Visualization       │
│  ○  Machine Learning (Week 5)│
│                              │
│  RECENT ACTIVITY:            │
│  ✅ NumPy — 2 days ago       │
│  ✅ Pandas — 5 days ago      │
│                              │
│  🏆 Badges: 🥇 🔥 📚        │
│  [─────────────────────────]│
│  🏠 Home  🗺️ Roadmap  👤 Me │
└─────────────────────────────┘
```

**Key UI Elements:**
- Streak counter (gamification)
- Circular progress donut (career progress)
- This week stats: hours, skills done/left
- Upcoming skills preview
- Recent activity feed
- Badges earned row
- Tab bar (Home / Roadmap / Profile)

---

## 🔄 Screen Flow Diagram

```
┌──────────────┐
│  Onboarding  │
│  (Screen 1)  │
└──────┬───────┘
       │ user types goal
       ▼
┌──────────────┐    low confidence    ┌─────────────────┐
│ Career Match │ ──────────────────→  │ Clarify Question│
│  (Screen 2)  │ ←────────────────── │ (inline modal)  │
└──────┬───────┘    user selects      └─────────────────┘
       │ "Roadmap Banao"
       ▼
┌──────────────┐
│ Roadmap Setup│
│  (Screen 3)  │
└──────┬───────┘
       │ "Generate"
       ▼
┌──────────────┐    tap skill    ┌─────────────┐
│ Roadmap View │ ──────────────→ │Skill Detail │
│  (Screen 4)  │ ←───────────── │  (Screen 5) │
└──────┬───────┘    back         └─────────────┘
       │
       ├──→ "Reschedule" → Modal (inline)
       │
       ▼
┌──────────────┐
│  Dashboard   │
│  (Screen 6)  │
└──────────────┘
```

---

## 📐 Design System Notes

| Element        | Spec                                    |
|----------------|-----------------------------------------|
| Primary Color  | Indigo `#4f46e5`                        |
| Accent Color   | Purple `#7c3aed`                        |
| Success        | Emerald `#10b981`                       |
| Warning        | Amber `#f59e0b`                         |
| Font           | Inter (system fallback: sans-serif)     |
| Border Radius  | 12px cards, 8px buttons                 |
| Base Spacing   | 8px grid                                |
| Mobile Width   | 375px (iPhone SE base)                  |
| Breakpoint     | 768px tablet, 1024px desktop            |
