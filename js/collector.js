// collector.html: shows the task, records the mouse and saves each session as json

// center of each element as [x, y] (0-1 of the window size)
// NOTE: robot.py has the same values, update both if anything moves
const LAYOUT = {
  brand: [0.1, 0.06],
  work: [0.62, 0.06],
  about: [0.7, 0.06],
  resume: [0.79, 0.06],
  contact: [0.89, 0.06],
  pet: [0.29, 0.34],
  cakery: [0.71, 0.34],
  permit: [0.29, 0.62],
  canvas: [0.71, 0.62],
  footerH: [0.5, 0.865],
  styleguide: [0.32, 0.945],
  citation: [0.5, 0.945],
  github: [0.68, 0.945],
  start: [0.5, 0.62],
  ok: [0.5, 0.55],
};
// clickable items + the text shown in the instructions
const NAMES = {
  brand: '"GROUP 2" in the menu',
  work: '"WORK" in the menu',
  about: '"ABOUT" in the menu',
  resume: '"RESUME" in the menu',
  contact: '"CONTACT" in the menu',
  pet: 'the "IAT201 Broker 1" card',
  cakery: 'the "IAT238 MVRDV" card',
  permit: 'the "IAT 334 Feature Design" card',
  canvas: 'the "IAT 167 Character Design" card',
  styleguide: '"I believe" in the footer',
  citation: '"I trust" in the footer',
  github: '"I can" in the footer',
};
const N_CLICKS = 6;

const $ = (id) => document.getElementById(id);
const place = (el, [fx, fy]) => {
  el.style.left = fx * 100 + "%";
  el.style.top = fy * 100 + "%";
};
document
  .querySelectorAll("[data-k]")
  .forEach((el) => place(el, LAYOUT[el.dataset.k]));
place(document.querySelector(".footer-h"), LAYOUT.footerH);
place($("startBtn"), LAYOUT.start);
place($("okBtn"), LAYOUT.ok);

// label comes from the url. no params = human,
// robot.py opens it with ?label=bot&level=...
const params = new URLSearchParams(location.search);
const LABEL = params.get("label") || "human";
const LEVEL = params.get("level") || null;
const DEVICE = params.get("device") || null;
if (DEVICE) $("device").style.display = "none";
if (LABEL === "bot")
  document
    .querySelectorAll(".mark")
    .forEach((m) => (m.style.display = "block"));

// pick 6 random items (out of 12) for each session.
// the bot picks its order the same way in python and sends it with ?order=
// so both humans and bots get random targets
function randomOrder() {
  const keys = Object.keys(NAMES);
  for (let i = keys.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [keys[i], keys[j]] = [keys[j], keys[i]];
  }
  return keys.slice(0, N_CLICKS);
}
const urlOrder = (params.get("order") || "")
  .split(",")
  .filter((k) => k in NAMES);
const CLICK_ORDER = urlOrder.length ? urlOrder : randomOrder();

// recording
let events = [],
  t0 = 0,
  recording = false,
  startedAt = null;
const now = () => Math.round((performance.now() - t0) * 10) / 10; // time in ms since start
const log = (e) => {
  if (recording) events.push({ t: now(), ...e });
};
const task = (name) => log({ type: "task", name });

document.addEventListener(
  "mousemove",
  (e) => log({ type: "move", x: e.clientX, y: e.clientY }),
  { passive: true },
);
document.addEventListener("mousedown", (e) =>
  log({ type: "down", x: e.clientX, y: e.clientY, button: e.button }),
);
document.addEventListener("mouseup", (e) =>
  log({ type: "up", x: e.clientX, y: e.clientY, button: e.button }),
);
document.addEventListener(
  "wheel",
  (e) =>
    log({
      type: "wheel",
      x: e.clientX,
      y: e.clientY,
      dy: e.deltaY,
      mode: e.deltaMode,
    }),
  { passive: true },
);
window.addEventListener("resize", () =>
  log({ type: "resize", w: innerWidth, h: innerHeight }),
);
document.addEventListener("click", (e) => {
  if (e.target.closest("a[data-k]")) e.preventDefault();
}); // stop links from opening other pages

const overlay = (id) => {
  document
    .querySelectorAll(".overlay")
    .forEach((o) => o.classList.remove("on"));
  if (id) $(id).classList.add("on");
};

$("startBtn").addEventListener("click", () => {
  document.querySelectorAll(".mark").forEach((m) => (m.style.display = "none"));
  t0 = performance.now();
  startedAt = new Date();
  recording = true;
  events = [];
  task("start");
  overlay(null);
  nextClick();
});

// highlight the next item and check clicks
let ci = 0;
function nextClick() {
  document.querySelectorAll(".glow").forEach((g) => g.classList.remove("glow"));
  const k = CLICK_ORDER[ci];
  document.querySelector(`[data-k="${k}"]`).classList.add("glow");
  $("instr").textContent =
    `Click ${NAMES[k]} (${ci + 1}/${CLICK_ORDER.length})`;
  task("click_" + (ci + 1) + "_" + k + "_shown");
}
document.querySelectorAll("[data-k]").forEach((el) =>
  el.addEventListener("click", () => {
    if (
      !recording ||
      ci >= CLICK_ORDER.length ||
      el.dataset.k !== CLICK_ORDER[ci]
    ) {
      if (recording) task("wrong_click_" + el.dataset.k);
      return;
    }
    task("click_" + (ci + 1) + "_" + el.dataset.k + "_hit");
    ci++;
    if (ci < CLICK_ORDER.length) nextClick();
    else {
      el.classList.remove("glow");
      $("instr").textContent = "";
      task("ok_shown");
      overlay("ovDone");
    }
  }),
);

// OK button saves the session
$("okBtn").addEventListener("click", () => {
  task("ok");
  finish();
});

// save everything as a json file (downloads)
function finish() {
  recording = false;
  const pad = (n) => String(n).padStart(2, "0"),
    d = startedAt;
  const stamp = `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
  const data = {
    label: LABEL,
    level: LEVEL,
    click_order: CLICK_ORDER,
    device: DEVICE || document.querySelector("input[name=dev]:checked").value,
    session_id: stamp + "-" + Math.random().toString(36).slice(2, 6),
    started_at: d.toISOString(),
    duration_ms: events.length ? events[events.length - 1].t : 0,
    viewport: { w: innerWidth, h: innerHeight },
    screen: { w: screen.width, h: screen.height },
    device_pixel_ratio: devicePixelRatio,
    fullscreen:
      Math.abs(innerWidth - screen.width) < 5 &&
      Math.abs(innerHeight - screen.height) < 5,
    user_agent: navigator.userAgent,
    events,
  };
  const fname = `${LABEL}${LEVEL ? "_" + LEVEL : ""}_${stamp}.json`;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(
    new Blob([JSON.stringify(data)], { type: "application/json" }),
  );
  a.download = fname;
  document.body.appendChild(a);
  a.click();
  a.remove();
  $("fname").textContent = fname + " (" + events.length + " events)";
  overlay("ovSaved");
}
