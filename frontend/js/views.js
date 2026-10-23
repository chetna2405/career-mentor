"use strict";

/* ---------- shared UI pieces ---------- */
let charts = [];
let todayNotice = [];                    // messages from the last adaptation, shown on the Today screen

function destroyCharts() { charts.forEach(c => c.destroy()); charts = []; }
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

function toast(message, type = "success", ms = 6000) {
  const el = document.createElement("div");
  el.className = `alert alert-${type} py-2 px-3`;
  el.textContent = message;
  $("#toasts").appendChild(el);
  setTimeout(() => el.remove(), ms);
}

function loading(root, text = "Loading…") {
  root.innerHTML = `<div class="text-center py-5 text-muted">
    <div class="spinner-border" role="status"></div><div class="mt-3">${esc(text)}</div></div>`;
}

function emptyState(root, title, text, href, button) {
  root.innerHTML = `<div class="card-soft p-5 text-center mx-auto" style="max-width:34rem">
    <h2 class="h4">${esc(title)}</h2><p class="text-muted">${esc(text)}</p>
    <a class="btn btn-primary" href="${href}">${esc(button)}</a></div>`;
}

const PRIORITY = { 1: ["Core", "text-bg-primary"], 2: ["Important", "text-bg-info"], 3: ["Optional", "text-bg-secondary"] };
const priorityBadge = p => { const [t, c] = PRIORITY[p] || ["", "text-bg-light"]; return `<span class="badge ${c}">${t}</span>`; };

/* ======================================================================
   1. PROFILE FORM
   ====================================================================== */
async function viewProfile(root) {
  loading(root);
  const st = await Api.get(`/api/state/${USER_ID}`);
  const p = st.has_profile ? await Api.get(`/api/profile/${USER_ID}`) : null;      // prefill when the user comes back
  const examples = ["mujhe websites banane hain", "I want to become a data scientist", "mujhe DSA seekhna hai placement ke liye"];

  root.innerHTML = `
  <div class="row justify-content-center"><div class="col-lg-8">
    <div class="card-soft p-4 p-md-5">
      <h1 class="h3 mb-1">Tell us about your goal</h1>
      <p class="text-muted mb-4">We find your career path, check what you already know, and plan your days around your time.</p>
      <form id="profileForm" novalidate>
        <div class="mb-3">
          <label class="form-label fw-semibold" for="goal">What do you want to become or learn?</label>
          <textarea id="goal" class="form-control" rows="2" maxlength="500" required
                    placeholder="e.g. mujhe websites banane hain"></textarea>
          <div class="chips mt-2">${examples.map(e => `<button type="button" class="chip example-chip" data-example="${esc(e)}">${esc(e)}</button>`).join("")}</div>
        </div>
        <div class="row g-3 mb-3">
          <div class="col-md-4">
            <label class="form-label fw-semibold" for="level">Your level</label>
            <select id="level" class="form-select">
              <option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label fw-semibold" for="hours">Hours per day</label>
            <input id="hours" type="number" class="form-control" min="0.25" max="12" step="0.25" value="2" required>
          </div>
          <div class="col-md-4">
            <label class="form-label fw-semibold" for="target">Target date <span class="text-muted fw-normal">(optional)</span></label>
            <input id="target" type="date" class="form-control">
          </div>
        </div>
        <div class="mb-4">
          <label class="form-label fw-semibold" for="skills">Skills you already know <span class="text-muted fw-normal">(optional)</span></label>
          <textarea id="skills" class="form-control" rows="2" placeholder="e.g. python, html and css, pandas"></textarea>
          <div class="form-text">Separate with commas. Short forms and small typos are fine ("py", "javscript").</div>
        </div>
        <button id="profileSubmit" class="btn btn-primary btn-lg" type="submit">Continue →</button>
      </form>
    </div>
  </div></div>`;

  if (p) {
    $("#goal").value = p.goal_text;
    $("#level").value = p.level;
    $("#hours").value = p.hours_per_day;
    $("#target").value = p.target_date || "";
    $("#skills").value = p.skills.map(s => s.raw_text).join(", ");
  }
  $$("[data-example]", root).forEach(b => b.addEventListener("click", () => { $("#goal").value = b.dataset.example; $("#goal").focus(); }));

  $("#profileForm").addEventListener("submit", async ev => {
    ev.preventDefault();
    const goal = $("#goal").value.trim();
    const hours = parseFloat($("#hours").value);
    if (goal.length < 3) return toast("Please describe your goal in a few words.", "warning");
    if (!(hours >= 0.25 && hours <= 12)) return toast("Hours per day must be between 0.25 and 12.", "warning");
    const skills = $("#skills").value.trim();
    const btn = $("#profileSubmit");
    btn.disabled = true; btn.textContent = "Analysing…";
    try {
      await Api.post("/api/profile", {
        user_id: USER_ID, goal_text: goal, level: $("#level").value, hours_per_day: hours,
        target_date: $("#target").value || null, skills_text: skills ? [skills] : [],
      });
      location.hash = "#/review";
    } catch (e) {
      toast(e.message, "danger");
      btn.disabled = false; btn.textContent = "Continue →";
    }
  });
}

/* ======================================================================
   2. REVIEW: confirm career and skills, then see the skill gap
   ====================================================================== */
const CONFIDENCE_LIMIT = 0.6;            // same value as CONFIDENCE_THRESHOLD in the backend

async function viewReview(root) {
  loading(root);
  let profile;
  try { profile = await Api.get(`/api/profile/${USER_ID}`); }
  catch (e) { if (e.status === 404) { location.hash = "#/profile"; return; } throw e; }
  const [careers, allSkills] = await Promise.all([Api.get("/api/careers"), Api.get("/api/skills")]);

  const unsure = profile.confirmed_career === null && profile.confidence < CONFIDENCE_LIMIT;
  const chosen = profile.confirmed_career || profile.predicted_career;
  const pct = Math.round(profile.confidence * 100);
  const options = `<option value="">— not a skill we track —</option>` +
    allSkills.map(s => `<option value="${esc(s.skill_id)}">${esc(s.skill_name)}</option>`).join("");

  root.innerHTML = `
  <div class="row g-4">
    <div class="col-lg-5">
      <div class="card-soft p-4 h-100">
        <div class="section-title">1. Your career path</div>
        <p class="text-muted small mb-2">Your goal: “${esc(profile.goal_text)}”</p>
        <div class="conf-bar mb-1"><div class="progress"><div class="progress-bar" style="width:${pct}%"></div></div></div>
        <div class="small text-muted mb-3">Our best guess: <strong>${esc(profile.predicted_career)}</strong> (${pct}% sure)</div>
        ${unsure ? `<div class="alert alert-warning py-2 small">We are not fully sure. Please pick the career that fits you best.</div>` : ""}
        <div id="careerOptions">
          ${careers.map(c => `<label class="d-flex align-items-center gap-2 p-2 border rounded mb-2" style="cursor:pointer">
              <input type="radio" name="career" value="${esc(c.career)}" ${c.career === chosen ? "checked" : ""}>
              <span class="fw-semibold">${esc(c.career)}</span>
              ${c.career === profile.predicted_career ? `<span class="badge text-bg-primary">Our guess</span>` : ""}
              <span class="text-muted small ms-auto">${c.skill_count} skills</span></label>`).join("")}
        </div>
      </div>
    </div>
    <div class="col-lg-7">
      <div class="card-soft p-4 h-100">
        <div class="section-title">2. Skills you already know</div>
        ${profile.skills.length === 0
          ? `<p class="text-muted mb-0">You did not add any skills, so we will plan from the basics.</p>`
          : `<div class="table-responsive"><table class="table table-sm align-middle mb-0">
              <thead><tr><th>You wrote</th><th>We understood</th><th></th></tr></thead><tbody>
              ${profile.skills.map((s, i) => `<tr class="skill-row ${s.needs_confirmation ? "check" : ""}">
                <td>${esc(s.raw_text)}</td>
                <td><select class="form-select form-select-sm" data-i="${i}" aria-label="Skill for ${esc(s.raw_text)}">${options}</select></td>
                <td class="small">${skillNote(s)}</td></tr>`).join("")}
              </tbody></table></div>
              <div class="form-text mt-2">Wrong match? Choose the right skill from the list.</div>`}
      </div>
    </div>
  </div>
  <div class="text-end mt-4"><button id="confirmBtn" class="btn btn-primary btn-lg">Confirm and see my skill gap →</button></div>
  <div id="gapArea" class="mt-4"></div>`;

  // preselect what we matched
  $$("select[data-i]", root).forEach(sel => { sel.value = profile.skills[+sel.dataset.i].skill_id || ""; });

  $("#confirmBtn").addEventListener("click", async () => {
    const career = ($("input[name=career]:checked", root) || {}).value;
    if (!career) return toast("Please choose a career.", "warning");
    const btn = $("#confirmBtn");
    btn.disabled = true;
    try {
      await Api.post("/api/profile/confirm", {
        user_id: USER_ID, career,
        skills: profile.skills.map((s, i) => ({ raw_text: s.raw_text, skill_id: $(`select[data-i="${i}"]`, root).value || null })),
      });
      await renderGap($("#gapArea"));
      $("#gapArea").scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (e) { toast(e.message, "danger"); }
    btn.disabled = false;
  });
}

function skillNote(s) {
  if (s.needs_confirmation) return `<span class="badge text-bg-warning">Please check</span> <span class="text-muted">Did you mean ${esc(s.skill_name)}?</span>`;
  if (s.method === "none") return `<span class="badge text-bg-secondary">Not recognised</span>`;
  return `<span class="badge text-bg-success">Matched</span> <span class="text-muted">${esc(s.method)} · ${Math.round(s.score * 100)}%</span>`;
}

async function renderGap(box) {
  loading(box, "Working out your skill gap…");
  const g = await Api.get(`/api/gap/${USER_ID}?start_date=${Demo.today()}`);
  if (g.gap.length === 0) {
    box.innerHTML = `<div class="alert alert-success">You already know every skill for ${esc(g.career)}. Nothing left to plan. Great job!</div>`;
    return;
  }
  const finish = addDays(Demo.today(), g.estimated_days - 1);
  let targetMsg = "";
  if (g.fits_target_date === false) {
    targetMsg = `<div class="alert alert-warning">At ${g.hours_per_day} h/day you will not reach your target date (${fmtDate(g.target_date, true)}).
      Study about <strong>${g.suggested_hours_per_day} h/day</strong>, or skip the optional skills.</div>`;
  } else if (g.fits_target_date === true) {
    targetMsg = `<div class="alert alert-success">This plan fits before your target date (${fmtDate(g.target_date, true)}).</div>`;
  }
  box.innerHTML = `
    <div class="card-soft p-4">
      <div class="section-title">3. Your skill gap for ${esc(g.career)}</div>
      <div class="row g-3 mb-3">
        <div class="col-6 col-md-3"><div class="stat"><div class="label">Skills to learn</div><div class="value">${g.gap.length}</div></div></div>
        <div class="col-6 col-md-3"><div class="stat"><div class="label">Total effort</div><div class="value">${g.total_hours} h</div></div></div>
        <div class="col-6 col-md-3"><div class="stat"><div class="label">At ${g.hours_per_day} h/day</div><div class="value">${g.estimated_days} days</div></div></div>
        <div class="col-6 col-md-3"><div class="stat"><div class="label">Done around</div><div class="value fs-5">${fmtDate(finish, true)}</div><div class="sub">${finish.slice(0, 4)}</div></div></div>
      </div>
      ${targetMsg}
      ${g.known_skills.length ? `<div class="mb-2"><span class="small text-muted me-2">You know:</span><span class="chips d-inline-flex">${g.known_skills.map(s => `<span class="chip ok">${esc(s.skill_name)}</span>`).join("")}</span></div>` : ""}
      ${g.implied_known.length ? `<div class="mb-3"><span class="small text-muted me-2">Assumed known (needed for what you know):</span><span class="chips d-inline-flex">${g.implied_known.map(s => `<span class="chip gray">${esc(s.skill_name)}</span>`).join("")}</span></div>` : ""}
      <ol class="gap-list mt-3">
        ${g.gap.map(s => `<li><span class="gap-num">${s.order}</span><span class="fw-semibold">${esc(s.skill_name)}</span>
            ${priorityBadge(s.priority)}
            ${s.prerequisite_of ? `<span class="small text-muted">needed for ${esc(s.prerequisite_of)}</span>` : ""}
            <span class="ms-auto text-muted small">${s.est_hours} h</span></li>`).join("")}
      </ol>
      <div class="d-flex align-items-center gap-3 mt-3 flex-wrap">
        <button id="genBtn" class="btn btn-success btn-lg">Generate my roadmap →</button>
        <span class="small text-muted">Starting ${fmtDate(Demo.today(), true)}. A new roadmap replaces the current one; the old one is kept as history.</span>
      </div>
    </div>`;

  $("#genBtn").addEventListener("click", async ev => {
    ev.target.disabled = true; ev.target.textContent = "Building your plan…";
    try {
      const r = await Api.post("/api/roadmap/generate", { user_id: USER_ID, start_date: Demo.today() });
      (r.warnings || []).forEach(w => toast(w, "warning", 12000));
      toast(r.roadmap_id ? `Roadmap ready: ${r.skills} skills, ${r.total_days} days.` : r.message, "success");
      location.hash = "#/roadmap";
    } catch (e) { toast(e.message, "danger"); ev.target.disabled = false; ev.target.textContent = "Generate my roadmap →"; }
  });
}

/* ======================================================================
   3. ROADMAP
   ====================================================================== */
const STATUS_ICON = { done: "✅", skipped: "⏭", pending: "⬜" };

async function viewRoadmap(root) {
  loading(root);
  let rm;
  try { rm = await Api.get(`/api/roadmap/${USER_ID}`); }
  catch (e) { if (e.status === 404) return emptyState(root, "No roadmap yet", "Tell us your goal and we will build your day-wise plan.", "#/profile", "Start"); throw e; }

  const today = Demo.today();
  let current = rm.weeks.findIndex(w => w.start_date <= today && today <= w.end_date);
  if (current < 0) current = today < rm.start_date ? 0 : rm.weeks.length - 1;

  root.innerHTML = `
    <div class="card-soft p-4 mb-3">
      <div class="d-flex flex-wrap gap-2 align-items-baseline">
        <h1 class="h4 mb-0">${esc(rm.career)} roadmap</h1>
        <span class="badge text-bg-light border">version ${rm.version}</span>
        <span class="text-muted ms-auto small">${fmtDate(rm.start_date, true)} → ${fmtDate(rm.end_date, true)} · ${rm.weeks.length} weeks</span>
      </div>
      <div class="progress mt-3"><div class="progress-bar" style="width:${rm.progress.percent}%"></div></div>
      <div class="small text-muted mt-1">${rm.progress.tasks_done} of ${rm.progress.tasks_total} tasks done (${rm.progress.percent}%)
        ${rm.progress.tasks_skipped ? ` · ${rm.progress.tasks_skipped} skipped and re-planned` : ""}</div>
    </div>
    <div class="d-flex justify-content-between align-items-center mb-2">
      <div class="section-title mb-0">Week by week</div>
      <a class="btn btn-sm btn-outline-secondary" href="#/profile">Update profile and re-plan</a>
    </div>
    <div id="weeks">${rm.weeks.map((w, i) => weekHtml(w, i === current)).join("")}</div>`;
}

function weekHtml(w, open) {
  const tasks = w.days.flatMap(d => d.tasks).filter(t => t.status !== "skipped");
  const done = tasks.filter(t => t.status === "done").length;
  return `<details class="week ${open ? "current" : ""}" ${open ? "open" : ""}>
    <summary>
      <span class="fw-semibold">Week ${w.week}</span>
      <span class="text-muted small">${fmtDate(w.start_date, true)} – ${fmtDate(w.end_date, true)}</span>
      <span class="chips">${w.skills.map(s => `<span class="chip">${esc(s)}</span>`).join("")}</span>
      <span class="ms-auto small text-muted">${done}/${tasks.length} done</span>
    </summary>
    <div class="week-body">${w.days.map(d => `
      <div class="day-row">
        <div class="day-head"><span>${fmtDate(d.date)}</span><span class="text-muted fw-normal">${fmtMinutes(d.total_minutes)}</span></div>
        ${d.tasks.map(taskLine).join("")}
      </div>`).join("")}</div>
  </details>`;
}

function taskLine(t) {
  const r = t.resource;
  const title = r
    ? `<strong>${esc(t.skill_name)}</strong>: <a href="${esc(safeUrl(r.url))}" target="_blank" rel="noopener">${esc(r.title)}</a>`
    : `<strong>${esc(t.skill_name)}</strong>: practice, build something small`;
  return `<div class="rm-task ${t.status}"><span>${STATUS_ICON[t.status]}</span><span>${title}
    ${t.reschedule_count > 0 && t.status !== "skipped" ? `<span class="badge text-bg-light border" title="Moved from ${esc(t.original_date)}">↻ moved</span>` : ""}</span>
    <span class="mins">${fmtMinutes(t.planned_minutes)}</span></div>`;
}

/* ======================================================================
   4. TODAY
   ====================================================================== */
const EVENT_LABEL = {
  roadmap_generated: "🗺 Roadmap created", task_skipped: "⏭ Task skipped", workload_reduced: "📉 Daily time reduced",
  workload_increased: "📈 Daily time increased", break_added: "🌴 Break added",
};

async function viewToday(root) {
  loading(root);
  const today = Demo.today();
  let data, log;
  try {
    [data, log] = await Promise.all([Api.get(`/api/tasks/today/${USER_ID}?on_date=${today}`), Api.get(`/api/adaptation-log/${USER_ID}`)]);
  } catch (e) {
    if (e.status === 404) return emptyState(root, "No roadmap yet", "Create your roadmap first, then your daily tasks will show up here.", "#/profile", "Start");
    throw e;
  }
  const pct = data.total_minutes ? Math.round(100 * data.done_minutes / data.total_minutes) : 0;

  root.innerHTML = `
    ${todayNotice.map(m => `<div class="alert alert-info d-flex gap-2 align-items-start"><span>🔔</span><span>${esc(m)}</span></div>`).join("")}
    <div class="card-soft p-4 mb-3">
      <div class="d-flex flex-wrap gap-2 align-items-baseline">
        <h1 class="h4 mb-0">${fmtDate(today)}</h1>
        ${Demo.active() ? `<span class="badge text-bg-warning">demo date</span>` : ""}
        <span class="ms-auto text-muted">${fmtMinutes(data.done_minutes)} of ${fmtMinutes(data.total_minutes)} done</span>
      </div>
      <div class="progress mt-3"><div class="progress-bar" style="width:${pct}%"></div></div>
    </div>
    ${data.overdue.length ? `<div class="section-title text-warning-emphasis">⚠ Overdue (${data.overdue.length})</div>
      ${data.overdue.map(t => taskCard(t, true)).join("")}` : ""}
    <div class="section-title">Today's tasks</div>
    ${data.tasks.length ? data.tasks.map(t => taskCard(t, false)).join("")
      : `<div class="card-soft p-4 text-center text-muted mb-3">${esc(data.message || "No tasks scheduled for today.")}</div>`}

    <details class="card-soft p-3 mt-4"><summary class="fw-semibold" style="cursor:pointer">🌴 Need a break?</summary>
      <div class="row g-2 align-items-end mt-2">
        <div class="col-sm-4"><label class="form-label small mb-1" for="brkStart">From</label><input id="brkStart" type="date" class="form-control form-control-sm" value="${addDays(today, 1)}"></div>
        <div class="col-sm-4"><label class="form-label small mb-1" for="brkEnd">To</label><input id="brkEnd" type="date" class="form-control form-control-sm" value="${addDays(today, 2)}"></div>
        <div class="col-sm-4"><button id="brkBtn" class="btn btn-outline-primary btn-sm w-100">Add break</button></div>
      </div>
      <div class="form-text">Your tasks move to after the break, and the first two days back are lighter.</div>
    </details>

    <details class="card-soft p-3 mt-3"><summary class="fw-semibold" style="cursor:pointer">🧭 Why did my plan change? (${log.length})</summary>
      <ul class="list-unstyled mt-2 mb-0 small">
        ${log.map(e => `<li class="py-1 border-top"><span class="text-muted">${fmtDate(e.date, true)}</span> · <strong>${esc(EVENT_LABEL[e.event] || e.event)}</strong><br><span class="text-muted">${esc(e.detail)}</span></li>`).join("")}
      </ul></details>`;

  // task buttons
  root.onclick = async ev => {
    const act = ev.target.closest("[data-act]"), fb = ev.target.closest("[data-fb]");
    if (act) {
      act.disabled = true;
      try {
        const res = await Api.patch(`/api/tasks/${act.dataset.id}`, { status: act.dataset.act, on_date: today });
        todayNotice = res.adaptation.messages;
        await viewToday(root);
      } catch (e) { toast(e.message, "danger"); act.disabled = false; }
    } else if (fb) {
      try {
        await Api.post(`/api/resources/${fb.dataset.res}/feedback`, { user_id: USER_ID, helpful: fb.dataset.fb === "1" });
        toast(fb.dataset.fb === "1" ? "Thanks! Glad it helped." : "Thanks! We will rank it lower for others.", "success", 3000);
      } catch (e) { toast(e.message, "danger"); }
    }
  };
  $("#brkBtn").addEventListener("click", async () => {
    try {
      const res = await Api.post("/api/breaks", { user_id: USER_ID, start_date: $("#brkStart").value, end_date: $("#brkEnd").value, on_date: today });
      todayNotice = [res.message];
      await viewToday(root);
    } catch (e) { toast(e.message, "danger"); }
  });
}

function taskCard(t, overdue) {
  const r = t.resource;
  const actions = t.status === "pending"
    ? `<button class="btn btn-success btn-sm" data-act="done" data-id="${t.task_id}">✓ Done</button>
       <button class="btn btn-outline-secondary btn-sm" data-act="skipped" data-id="${t.task_id}">⏭ Skip</button>`
    : t.status === "done"
      ? `<button class="btn btn-outline-secondary btn-sm" data-act="pending" data-id="${t.task_id}">↩ Undo</button>`
      : `<span class="small text-muted">Skipped, moved to a later day</span>`;
  const feedback = r ? `<span class="fb ms-auto" title="Was this resource helpful?"><span class="small text-muted me-1">Helpful?</span>
      <button type="button" data-fb="1" data-res="${esc(r.resource_id)}" aria-label="Helpful">👍</button>
      <button type="button" data-fb="0" data-res="${esc(r.resource_id)}" aria-label="Not helpful">👎</button></span>` : "";
  return `<div class="task-card ${t.status} ${overdue ? "overdue" : ""}">
    <div class="d-flex flex-wrap gap-2 align-items-start">
      <div>
        <div class="task-title">${r ? `${esc(t.skill_name)}: <a href="${esc(safeUrl(r.url))}" target="_blank" rel="noopener">${esc(r.title)}</a>`
                                    : `${esc(t.skill_name)}: practice, build something small`}</div>
        <div class="task-meta">
          <span>⏱ ${fmtMinutes(t.planned_minutes)}</span>
          ${r ? `<span class="badge text-bg-light border">${esc(r.type)}</span><span class="badge text-bg-light border">${esc(r.level)}</span>` : `<span class="badge text-bg-light border">hands-on</span>`}
          ${overdue ? `<span>from ${fmtDate(t.scheduled_date, true)}</span>` : ""}
          ${t.reschedule_count > 0 && !overdue ? `<span title="Originally planned for ${esc(t.original_date)}">↻ moved from ${fmtDate(t.original_date, true)}</span>` : ""}
        </div>
      </div>${feedback}
    </div>
    <div class="mt-2 d-flex gap-2 align-items-center">${actions}</div>
  </div>`;
}

/* ======================================================================
   5. DASHBOARD
   ====================================================================== */
async function viewDashboard(root) {
  loading(root);
  let d;
  try { d = await Api.get(`/api/dashboard/${USER_ID}?on_date=${Demo.today()}`); }
  catch (e) { if (e.status === 404) return emptyState(root, "No roadmap yet", "Your progress will show up here once you have a roadmap.", "#/profile", "Start"); throw e; }

  const shift = d.schedule.days_behind_original_plan;
  const sched = shift > 0 ? { v: `${shift} day${shift === 1 ? "" : "s"} behind`, c: "text-warning" }
              : shift < 0 ? { v: `${-shift} day${shift === -1 ? "" : "s"} ahead`, c: "text-success" }
              : { v: "On track", c: "text-success" };
  const a = d.adaptation;

  root.innerHTML = `
    <div class="d-flex flex-wrap align-items-baseline gap-2 mb-3">
      <h1 class="h4 mb-0">${esc(d.career)} progress</h1>
      ${Demo.active() ? `<span class="badge text-bg-warning">demo date ${fmtDate(d.today, true)}</span>` : ""}
    </div>
    <div class="row g-3 mb-3">
      <div class="col-6 col-lg-3"><div class="stat"><div class="label">Overall progress</div><div class="value">${d.progress.percent}%</div>
        <div class="progress mt-2"><div class="progress-bar" style="width:${d.progress.percent}%"></div></div></div></div>
      <div class="col-6 col-lg-3"><div class="stat"><div class="label">Time studied</div><div class="value">${fmtHours(d.time.done_minutes)}</div>
        <div class="sub">${fmtHours(d.time.remaining_minutes)} to go</div></div></div>
      <div class="col-6 col-lg-3"><div class="stat"><div class="label">Streak</div><div class="value">🔥 ${d.streak.current_days}</div>
        <div class="sub">day${d.streak.current_days === 1 ? "" : "s"} fully completed in a row</div></div></div>
      <div class="col-6 col-lg-3"><div class="stat"><div class="label">Schedule</div><div class="value fs-4 ${sched.c}">${sched.v}</div>
        <div class="sub">Ends ${fmtDate(d.schedule.current_end_date, true)}</div></div></div>
    </div>
    <div class="card-soft p-3 mb-3 d-flex flex-wrap gap-3 align-items-center">
      <div><span class="text-muted small">Skills completed</span> <strong>${d.skills.completed} / ${d.skills.total}</strong></div>
      <div><span class="text-muted small">Studying now</span> <strong>${d.skills.current ? esc(d.skills.current.skill_name) : "All done 🎉"}</strong></div>
      <div class="ms-auto small text-muted">Adaptation: ${a.tasks_skipped} skipped · ${a.tasks_rescheduled} re-planned · ${a.breaks} break${a.breaks === 1 ? "" : "s"} · ${a.workload_changes} workload change${a.workload_changes === 1 ? "" : "s"}</div>
    </div>
    <div class="row g-3">
      <div class="col-lg-6"><div class="card-soft p-3"><div class="section-title">Study time per week</div>
        <div class="scroll-x"><div class="chart-box" style="min-width:${Math.max(320, d.weekly.length * 34)}px"><canvas id="weeklyChart"></canvas></div></div></div></div>
      <div class="col-lg-6"><div class="card-soft p-3"><div class="section-title">Progress per skill</div>
        <div class="chart-box" style="height:${Math.max(260, d.skills.list.length * 26 + 50)}px"><canvas id="skillChart"></canvas></div></div></div>
    </div>`;

  charts.push(new Chart($("#weeklyChart"), {
    type: "bar",
    data: { labels: d.weekly.map(w => `W${w.week}`),
            datasets: [{ label: "Planned (h)", data: d.weekly.map(w => +(w.planned_minutes / 60).toFixed(1)), backgroundColor: "#c7d2fe" },
                       { label: "Done (h)", data: d.weekly.map(w => +(w.done_minutes / 60).toFixed(1)), backgroundColor: "#1f9d6b" }] },
    options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, title: { display: true, text: "hours" } } } },
  }));
  charts.push(new Chart($("#skillChart"), {
    type: "bar",
    data: { labels: d.skills.list.map(s => s.skill_name),
            datasets: [{ label: "% done", data: d.skills.list.map(s => s.percent),
                         backgroundColor: d.skills.list.map(s => s.status === "completed" ? "#1f9d6b" : s.status === "in_progress" ? "#4f46e5" : "#d1d5db") }] },
    options: { indexAxis: "y", responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
               scales: { x: { min: 0, max: 100, title: { display: true, text: "% done" } } } },
  }));
}
