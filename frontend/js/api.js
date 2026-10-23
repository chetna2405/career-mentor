"use strict";

const USER_ID = 1;                       // the prototype uses one demo user

/* ---------- small helpers ---------- */
function esc(s) {                        // always escape text that came from a user or the database
  return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function safeUrl(u) { return /^https?:\/\//i.test(u || "") ? u : "#"; }

function isoDate(d) {
  const p = n => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}
function parseIso(s) { const [y, m, d] = s.split("-").map(Number); return new Date(y, m - 1, d); }
function addDays(s, n) { const d = parseIso(s); d.setDate(d.getDate() + n); return isoDate(d); }
function fmtDate(s, short = false) {
  return parseIso(s).toLocaleDateString("en-GB", short
    ? { day: "numeric", month: "short" }
    : { weekday: "short", day: "numeric", month: "short", year: "numeric" });
}
function fmtMinutes(m) {
  m = Math.round(m);
  const h = Math.floor(m / 60), r = m % 60;
  return h ? (r ? `${h}h ${r}m` : `${h}h`) : `${r}m`;
}
function fmtHours(minutes) { return `${Math.round(minutes / 6) / 10} h`; }

/* ---------- "today" (can be changed for demos) ---------- */
const Demo = {
  key: "careerMentorDemoDate",
  real() { return isoDate(new Date()); },
  get() {
    try { const v = localStorage.getItem(this.key); return v && /^\d{4}-\d{2}-\d{2}$/.test(v) ? v : null; }
    catch (e) { return null; }
  },
  today() { return this.get() || this.real(); },
  set(v) {
    try { if (!v || v === this.real()) localStorage.removeItem(this.key); else localStorage.setItem(this.key, v); }
    catch (e) { /* storage not available: demo date just resets */ }
  },
  active() { return this.get() !== null; },
};

/* ---------- API ---------- */
function errorMessage(data) {
  if (!data) return null;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map(d => `${(d.loc || []).slice(1).join(".")}: ${d.msg}`).join("; ");
  }
  return null;
}

const Api = {
  async request(method, path, body) {
    let res;
    try {
      res = await fetch(path, {
        method,
        headers: body !== undefined ? { "Content-Type": "application/json" } : {},
        body: body !== undefined ? JSON.stringify(body) : undefined,
      });
    } catch (e) {
      const err = new Error("Cannot reach the server. Is it running?");
      err.status = 0;
      throw err;
    }
    let data = null;
    try { data = await res.json(); } catch (e) { /* empty body */ }
    if (!res.ok) {
      const err = new Error(errorMessage(data) || `Request failed (${res.status})`);
      err.status = res.status;
      throw err;
    }
    return data;
  },
  get(path) { return this.request("GET", path); },
  post(path, body) { return this.request("POST", path, body ?? {}); },
  patch(path, body) { return this.request("PATCH", path, body); },
};
