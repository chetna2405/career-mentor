"use strict";

const ROUTES = {
  "#/profile": viewProfile, "#/review": viewReview, "#/roadmap": viewRoadmap,
  "#/today": viewToday, "#/dashboard": viewDashboard,
};
const NAV_FOR = { "#/review": "#/profile" };          // the review screen belongs to the Profile step

async function render() {
  destroyCharts();
  const root = $("#app");
  root.onclick = null;
  let route = location.hash;

  if (!ROUTES[route]) {                               // first visit: go to Today if a roadmap exists, else to the form
    let target = "#/profile";
    try { if ((await Api.get(`/api/state/${USER_ID}`)).has_roadmap) target = "#/today"; } catch (e) { /* server problem: show the form */ }
    if (location.hash === target) return render();
    location.hash = target;
    return;
  }
  if (route !== "#/today") todayNotice = [];

  $$("#nav a").forEach(a => a.classList.toggle("active", a.dataset.route === (NAV_FOR[route] || route)));
  syncDemoControl();
  try {
    await ROUTES[route](root);
  } catch (e) {
    root.innerHTML = `<div class="alert alert-danger"><strong>Something went wrong.</strong> ${esc(e.message)}
      <div class="mt-2"><button class="btn btn-sm btn-outline-danger" id="retry">Try again</button></div></div>`;
    $("#retry").addEventListener("click", render);
  }
  window.scrollTo(0, 0);
}

/* ---------- demo date control ---------- */
function syncDemoControl() {
  $("#demoDate").value = Demo.today();
  $("#demoBadge").classList.toggle("d-none", !Demo.active());
}
function setDemo(value) { Demo.set(value); render(); }

$("#demoDate").addEventListener("change", e => { if (e.target.value) setDemo(e.target.value); });
$("#demoNext").addEventListener("click", () => setDemo(addDays(Demo.today(), 1)));
$("#demoReset").addEventListener("click", () => setDemo(null));

window.addEventListener("hashchange", render);
render();
