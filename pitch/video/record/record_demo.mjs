// Records the end-to-end 4site demo with Playwright: a visible cursor clicks through the real app (light
// theme), while a CDP screencast saves every frame with its timestamp. Step markers go to markers.json so
// the Remotion edit can cut, zoom and caption each step.
//
//   node record/record_demo.mjs            # record into public/demo/
//   DRY=1 node record/record_demo.mjs      # screenshot each step into /tmp/demo_dry instead
//
// Needs the API on :8000 (with ANTHROPIC_API_KEY for live chat) and the web app on APP_URL.
import { spawnSync } from "node:child_process";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const BASE = process.env.APP_URL ?? "http://localhost:5180";
const DRY = process.env.DRY === "1";
const OUT = DRY ? "/tmp/demo_dry" : path.join(HERE, "../public/demo");
const FRAMES = path.join(HERE, "../.frames");
const VIEW = { width: 1600, height: 900 };
const SCALE = 1.2; // 1920 x 1080 frames

const CURSOR = `
(() => {
  const install = () => {
    if (document.getElementById("__demo_cursor")) return;
    const style = document.createElement("style");
    style.textContent = \`
      #__demo_cursor { position: fixed; left: 0; top: 0; width: 26px; height: 26px; z-index: 2147483647;
        pointer-events: none; transform: translate(-100px, -100px); transition: transform 16ms linear;
        filter: drop-shadow(0 2px 3px rgba(0,0,0,.35)); }
      .__demo_ripple { position: fixed; z-index: 2147483646; pointer-events: none; width: 44px; height: 44px;
        margin: -22px 0 0 -22px; border-radius: 50%; border: 3px solid rgba(74,108,247,.9);
        background: rgba(74,108,247,.18); animation: __demo_ripple 600ms ease-out forwards; }
      @keyframes __demo_ripple { from { transform: scale(.3); opacity: 1 } to { transform: scale(1.5); opacity: 0 } }
    \`;
    document.head.appendChild(style);
    const c = document.createElement("div");
    c.id = "__demo_cursor";
    c.innerHTML = '<svg viewBox="0 0 24 24" width="26" height="26"><path d="M4 2l15 11.2-6.6.9 3.9 7.4-2.9 1.5-3.9-7.5L4 20z" fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    document.body.appendChild(c);
    window.addEventListener("mousemove", (e) => { c.style.transform = \`translate(\${e.clientX - 3}px, \${e.clientY - 2}px)\`; }, true);
    window.addEventListener("mousedown", (e) => {
      const r = document.createElement("div");
      r.className = "__demo_ripple";
      r.style.left = e.clientX + "px";
      r.style.top = e.clientY + "px";
      document.body.appendChild(r);
      setTimeout(() => r.remove(), 700);
    }, true);
  };
  if (document.body) install(); else document.addEventListener("DOMContentLoaded", install);
})();
`;

const browser = await chromium.launch({
  headless: true,
  args: ["--use-angle=metal", "--ignore-gpu-blocklist", "--enable-gpu", "--hide-scrollbars"],
});
const context = await browser.newContext({ viewport: VIEW, deviceScaleFactor: SCALE });
await context.addInitScript(() => {
  window.sessionStorage.setItem("foresite.intro.seen", "1");
  window.localStorage.setItem("foresite.theme.v2", "light");
});
await context.addInitScript(CURSOR);
const page = await context.newPage();
page.on("console", (m) => m.type() === "error" && console.log("  console:", m.text().slice(0, 160)));

mkdirSync(OUT, { recursive: true });
const frames = [];
let cdp = null;
if (!DRY) {
  rmSync(FRAMES, { recursive: true, force: true });
  mkdirSync(FRAMES, { recursive: true });
  cdp = await context.newCDPSession(page);
  cdp.on("Page.screencastFrame", async ({ data, metadata, sessionId }) => {
    const file = path.join(FRAMES, `f${String(frames.length).padStart(6, "0")}.jpg`);
    frames.push({ file, t: metadata.timestamp });
    writeFileSync(file, Buffer.from(data, "base64"));
    await cdp.send("Page.screencastFrameAck", { sessionId }).catch(() => undefined);
  });
}

const markers = [];
let t0 = null;
const now = () => Date.now() / 1000;
let step = 0;
async function mark(name) {
  markers.push({ name, t: now() - t0 });
  console.log(`${(now() - t0).toFixed(1).padStart(6)}s  ${name}`);
  if (DRY) await page.screenshot({ path: `${OUT}/${String(++step).padStart(2, "0")}_${name}.png` });
}
const wait = (ms) => page.waitForTimeout(ms);

let mouse = { x: VIEW.width / 2, y: VIEW.height / 2 };
async function moveTo(x, y, ms = 650) {
  const steps = Math.max(8, Math.round(ms / 16));
  const from = { ...mouse };
  for (let i = 1; i <= steps; i++) {
    const k = i / steps;
    const e = k < 0.5 ? 2 * k * k : 1 - (-2 * k + 2) ** 2 / 2;
    await page.mouse.move(from.x + (x - from.x) * e, from.y + (y - from.y) * e);
  }
  mouse = { x, y };
}
async function point(locator, { ms = 650, dx = 0.5, dy = 0.5 } = {}) {
  await locator.scrollIntoViewIfNeeded({ timeout: 15000 }).catch(() => undefined);
  const box = await locator.boundingBox({ timeout: 15000 });
  if (!box) throw new Error(`no box for ${locator}`);
  await moveTo(box.x + box.width * dx, box.y + box.height * dy, ms);
  return box;
}
async function click(locator, opts = {}) {
  await point(locator, opts);
  await wait(opts.hover ?? 250);
  await page.mouse.down();
  await wait(70);
  await page.mouse.up();
  await wait(opts.after ?? 600);
}
async function scrollIn(locator, dy, times = 6) {
  await point(locator, { ms: 400 });
  for (let i = 0; i < times; i++) {
    await page.mouse.wheel(0, dy / times);
    await wait(60);
  }
}

const panel = page.locator(".fs-shell__right .fs-site, .fs-shell__right [class*='fs-site']").first();
const tab = (name) => page.getByRole("tab", { name }).or(page.locator(".fs-site__bar button", { hasText: name })).first();

// ---- The flow ----------------------------------------------------------------------------------------
await page.goto(BASE);
await page.waitForSelector(".fs-topbar", { state: "visible" });
await wait(6000); // city layers and tiles settle before the take starts
if (cdp) await cdp.send("Page.startScreencast", { format: "jpeg", quality: 90, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 });
t0 = now();
await moveTo(820, 520, 10);
await wait(1500);
await mark("city");

// Inputs: every public source is a layer
await click(page.locator(".fs-layers-btn"), { after: 1200 });
await mark("layers");
for (const name of [/Unsafe facades/i, /Sandy/i]) {
  const toggle = page.locator(".fs-shell__left").getByRole("switch", { name }).first();
  if (await toggle.count()) await click(toggle, { after: 1600, dx: 0.1 });
}
await mark("layers_toggled");
await moveTo(900, 560, 900);
await wait(2200);
for (const name of [/Unsafe facades/i, /Sandy/i]) {
  const toggle = page.locator(".fs-shell__left").getByRole("switch", { name }).first();
  if (await toggle.count()) await click(toggle, { after: 500, dx: 0.1, ms: 400 });
}
await click(page.locator(".fs-layers-btn"), { after: 900 });

// Search: the command bar
await click(page.locator(".fs-search"), { after: 500 });
await mark("search_open");
await page.keyboard.type("861 Park Ave Brooklyn", { delay: 75 });
const result = page.locator(".fs-cmd__item", { hasText: /861 Park Ave.*Brooklyn/i }).first();
await result.waitFor({ timeout: 30000 });
await wait(800);
await mark("search_results");
await click(result, { after: 200 });
await mark("fly_to");
await page.locator(".fs-shell__right").getByText("What stands out", { exact: false }).first().waitFor({ timeout: 60000 });
await wait(5500);
await mark("site_overview");
await moveTo(1300, 470, 900);
await wait(1500);

// Overview: top signals, then why
const firstSignal = page.locator(".fs-shell__right .fs-signals .fs-card").first();
await point(firstSignal, { ms: 600 });
await wait(800);
await click(firstSignal.locator(".fs-explain summary"), { after: 1500 });
await mark("signal_why");
await wait(2000);
await click(firstSignal.locator(".fs-explain summary"), { after: 500 });

// Touching lots
const fold = (re) => page.locator(".fs-shell__right details.fs-site__fold summary", { hasText: re }).first();
await click(fold(/Touching lots/i), { after: 900 });
await mark("touching_lots");
await scrollIn(fold(/Touching lots/i), 380);
await wait(3000);
await click(fold(/Touching lots/i), { after: 500 });

// Similar cases
await click(tab(/Similar/), { after: 1200 });
await mark("similar");
await wait(2200);
const heroCase = page.locator(".fs-shell__right .fs-case", { hasText: /211 E 34th/i }).first();
const firstCase = heroCase.locator(".fs-case__main").first();
await point(heroCase, { ms: 700 });
await wait(900);
await click(firstCase, { after: 600 });
await mark("case_strand");
await wait(4500);
const happened = heroCase.getByText(/What happened/i).first();
if (await happened.count()) {
  await click(happened, { after: 1200 });
  await mark("case_what_happened");
  await scrollIn(happened, 260);
  await wait(4500);
}
await click(firstCase, { after: 3500 });
await mark("case_unfocused");

// Actions by discipline
await click(tab(/Actions/), { after: 1200 });
await mark("actions");
await wait(1500);
const firstAction = page.locator(".fs-shell__right .fs-card").first();
await click(firstAction.locator(".fs-explain summary").first(), { after: 1500 });
await mark("action_why");
await wait(2500);

// Project: shared checklist for the team
await click(page.getByRole("button", { name: /Continue to project/i }), { after: 1500 });
await mark("project_setup");
await click(page.locator(".fs-ps-card", { hasText: "New construction" }), { after: 800 });
await click(page.locator(".fs-ps-card", { hasText: "Masonry" }), { after: 800 });
const scopeChips = page.locator(".fs-ps-chips[aria-label='Scope'] .fs-chip");
if (await scopeChips.count()) {
  await point(scopeChips.first(), { ms: 500 });
  await wait(600);
  await point(scopeChips.nth(2), { ms: 500 });
  await wait(900);
}
const seRole = page.locator(".fs-ps-card", { hasText: "Structural engineer" }).first();
if (await seRole.count()) {
  await point(seRole, { ms: 600 });
  await wait(900);
}
await mark("project_filled");
await click(page.getByRole("button", { name: /Draft checklist/i }), { after: 2500 });
await page.locator(".fs-ps-item__title").first().waitFor({ timeout: 30000 }).catch(() => console.log("  no checklist items"));
await mark("checklist");
await wait(2000);
const lifeSafety = page.locator(".fs-ps-chips .fs-chip", { hasText: "Life safety" }).first();
if (await lifeSafety.count()) {
  await click(lifeSafety, { after: 1500 });
  await mark("checklist_life_safety");
}
const seItem = page.locator(".fs-ps-item", { hasText: "Examine the adjoining building" }).first();
const item = (await seItem.count()) ? seItem.locator(".fs-ps-item__title") : page.locator(".fs-ps-item__title").first();
if (await item.count()) {
  await click(item, { after: 1800 });
  await mark("checklist_item");
  const status = (await seItem.count()) ? seItem.locator(".fs-ps-status") : page.locator(".fs-ps-status").first();
  if (await status.count()) {
    await click(status, { after: 1500 });
    await mark("checklist_status");
  }
}
const docs = page.locator(".fs-ps__step", { hasText: /Documents/i }).first();
if (await docs.count()) {
  await click(docs, { after: 1800 });
  await mark("documents");
  await wait(2200);
}
await click(page.getByRole("button", { name: /← Map/ }), { after: 2500 });
await mark("back_to_map");

// Early warnings, later in the job
await click(tab(/Overview/), { after: 900 });
const warnings = page.locator(".fs-shell__right .fs-site__section", { hasText: "Early warnings" }).first();
await warnings.scrollIntoViewIfNeeded();
await wait(800);
await point(warnings, { ms: 600, dy: 0.2 });
await mark("early_warnings");
await wait(2000);
const rainCard = warnings.locator(".fs-card", { hasText: /rain/i }).first();
const warnCard = (await rainCard.count()) ? rainCard : warnings.locator(".fs-card").first();
await click(warnCard.locator(".fs-explain summary"), { after: 1200 });
await mark("warning_why");
await scrollIn(warnCard, 200);
await wait(4000);
await click(warnCard.locator(".fs-explain summary"), { after: 500 });

// Chat: ask in plain English, answer with sources, pin to the project
await click(page.locator(".fs-chat-fab"), { after: 1400 });
await mark("chat_open");
const input = page.getByPlaceholder(/Ask in plain English/i).first();
await click(input, { after: 300 });
await page.keyboard.type("What should the structural engineer check before excavation continues?", { delay: 40 });
await wait(600);
await mark("chat_typed");
await page.keyboard.press("Enter");
await wait(800);
await mark("chat_waiting");
await page.waitForFunction(() => {
  const l = document.querySelector("[role='log'][aria-label='Questions and answers']");
  return l && l.querySelector("article") && !/Looking this up/.test(l.textContent ?? "");
}, null, { timeout: 180000 }).catch(() => console.log("  chat: still waiting"));
await mark("chat_answer");
const log = page.locator("[role='log'][aria-label='Questions and answers']");
await log.evaluate((el) => {
  const q = el.querySelector("article");
  el.scrollTo({ top: q ? q.offsetTop - el.offsetTop - 8 : 0, behavior: "instant" });
});
await wait(2500);
await mark("chat_answer_top");
for (let i = 0; i < 6; i++) {
  await scrollIn(log, 160, 8);
  await wait(1300);
}
await mark("chat_answer_scrolled");
const pinBtn = log.getByRole("button", { name: /pin/i }).last();
if (await pinBtn.count()) {
  await click(pinBtn, { after: 1800 });
  await mark("chat_pinned");
  const projectTab = page.locator(".fs-shell__right [role='tab'], .fs-shell__right button", { hasText: /^Project$/ }).first();
  if (await projectTab.count()) {
    await click(projectTab, { after: 2500 });
    await mark("chat_project_tab");
    await wait(2000);
  }
}

// Limitations, always visible
await click(page.locator(".fs-limits__head"), { after: 1500 });
await mark("limitations");
await wait(3500);
await mark("end");

if (cdp) {
  await cdp.send("Page.stopScreencast");
  await wait(500);
}
await browser.close();

writeFileSync(path.join(OUT, "markers.json"), JSON.stringify(markers, null, 2));
if (!DRY && frames.length) {
  // Variable-rate screencast frames into a constant 30 fps video.
  const start = frames[0].t;
  const lines = ["ffconcat version 1.0"];
  frames.forEach((f, i) => {
    const next = frames[i + 1]?.t ?? f.t + 0.5;
    lines.push(`file '${f.file}'`, `duration ${Math.max(0.001, next - f.t).toFixed(4)}`);
  });
  lines.push(`file '${frames.at(-1).file}'`);
  writeFileSync(path.join(FRAMES, "list.ffconcat"), lines.join("\n"));
  const offset = start - (t0 ?? start);
  writeFileSync(path.join(OUT, "markers.json"), JSON.stringify(markers.map((m) => ({ ...m, t: +(m.t - offset).toFixed(3) })), null, 2));
  const r = spawnSync("ffmpeg", ["-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", path.join(FRAMES, "list.ffconcat"),
    "-vf", "fps=30,scale=1920:1080:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
    path.join(OUT, "demo.mp4")], { stdio: "inherit" });
  console.log("frames", frames.length, "ffmpeg", r.status);
}
