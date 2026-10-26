// Page navigation (progress bar, contents, Back/Next, arrow keys) and the looping diagram animations
// for index.html. Pages are the .lesson sections; data-part groups them into Part 1 and Part 2.
const pages = [...document.querySelectorAll(".lesson")];
const partNames = { 1: "Part 1 · The big picture", 2: "Part 2 · Contributing" };
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
let current = 0;

const partsEl = document.getElementById("parts");
const contentsEl = document.getElementById("contents");
const contentsBtn = document.getElementById("contentsBtn");
const prevBtn = document.getElementById("prev");
const nextBtn = document.getElementById("next");
const countEl = document.getElementById("count");

// Group pages by part for the progress bar and the contents list.
const groups = [];
pages.forEach((page, index) => {
  let last = groups[groups.length - 1];
  if (!last || last.part !== page.dataset.part) {
    last = { part: page.dataset.part, pages: [] };
    groups.push(last);
  }
  last.pages.push(index);
});

const segs = [];
const contentItems = [];
const partEls = [];
for (const group of groups) {
  const partEl = document.createElement("div");
  partEl.className = "part";
  partEl.style.flex = String(group.pages.length);
  const label = document.createElement("div");
  label.className = "part-label";
  label.textContent = partNames[group.part];
  const row = document.createElement("div");
  row.className = "segs";
  partEl.append(label, row);
  partsEl.append(partEl);
  partEls.push({ el: partEl, part: group.part });

  const block = document.createElement("div");
  const heading = document.createElement("h3");
  heading.textContent = partNames[group.part];
  const list = document.createElement("ol");
  block.append(heading, list);
  contentsEl.append(block);

  group.pages.forEach((index, n) => {
    const title = pages[index].dataset.title;
    const seg = document.createElement("button");
    seg.type = "button";
    seg.className = "seg";
    seg.setAttribute("aria-label", `Go to ${title}`);
    seg.title = title;
    seg.addEventListener("click", () => show(index, true));
    row.append(seg);
    segs[index] = seg;

    const item = document.createElement("li");
    const go = document.createElement("button");
    go.type = "button";
    const num = document.createElement("span");
    num.textContent = String(n + 1);
    go.append(num, title);
    go.addEventListener("click", () => {
      setContents(false);
      show(index, true);
    });
    item.append(go);
    list.append(item);
    contentItems[index] = go;
  });
}

function setContents(open) {
  contentsEl.hidden = !open;
  contentsBtn.setAttribute("aria-expanded", open ? "true" : "false");
}
contentsBtn.addEventListener("click", () => setContents(contentsEl.hidden));

function positionInPart(index) {
  const group = groups.find((g) => g.pages.includes(index));
  return { part: group.part, n: group.pages.indexOf(index) + 1, of: group.pages.length };
}

function show(index, scroll) {
  const previous = pages[current];
  current = Math.max(0, Math.min(pages.length - 1, index));
  pages.forEach((page, i) => { page.hidden = i !== current; });
  segs.forEach((seg, i) => {
    seg.classList.toggle("done", i < current);
    seg.classList.toggle("now", i === current);
    seg.setAttribute("aria-current", i === current ? "step" : "false");
  });
  contentItems.forEach((item, i) => item.setAttribute("aria-current", i === current ? "true" : "false"));
  const pos = positionInPart(current);
  partEls.forEach((p) => p.el.classList.toggle("on", p.part === pos.part));
  countEl.innerHTML = `<b>Part ${pos.part}</b> · ${pos.n} of ${pos.of}`;
  prevBtn.disabled = current === 0;
  nextBtn.disabled = current === pages.length - 1;

  const previousFig = previous !== pages[current] ? previous.querySelector(".anim") : null;
  if (previousFig) { stopFig(previousFig); }
  const fig = pages[current].querySelector(".anim");
  if (fig) {
    if (reduceMotion) { stopFig(fig); } else { play(fig); }
  }
  if (scroll) { partsEl.scrollIntoView({ block: "nearest" }); }
}

prevBtn.addEventListener("click", () => show(current - 1, true));
nextBtn.addEventListener("click", () => show(current + 1, true));
document.querySelectorAll("[data-go]").forEach((button) => {
  button.addEventListener("click", () => {
    const target = button.dataset.go === "next" ? current + 1 : Number(button.dataset.go);
    show(target, true);
  });
});
document.addEventListener("keydown", (event) => {
  if (event.altKey || event.ctrlKey || event.metaKey) { return; }
  // Leave arrow keys alone inside code blocks, which scroll sideways.
  if (event.target.closest?.("pre")) { return; }
  if (event.key === "Escape") { setContents(false); }
  if (event.key === "ArrowRight") { show(current + 1, false); }
  if (event.key === "ArrowLeft") { show(current - 1, false); }
});

// Animation: each input item travels into the machine, then its output appears.
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
function centre(el, base) {
  const r = el.getBoundingClientRect();
  return { x: r.left - base.left + r.width / 2, y: r.top - base.top + r.height / 2 };
}
const items = (fig, attr) => [...fig.querySelectorAll(`[${attr}]`)];
function restState(fig) {
  items(fig, "data-src").forEach((el) => { el.style.opacity = "0.4"; });
  items(fig, "data-out").forEach((el) => { el.style.opacity = "1"; });
  items(fig, "data-static").forEach((el) => { el.style.opacity = "1"; });
  fig.querySelector(".mid").classList.remove("busy");
}
function stopFig(fig) {
  fig.runId = (fig.runId || 0) + 1;
  fig.querySelectorAll(".ghost").forEach((g) => g.remove());
  restState(fig);
}

// Loops for about a minute, then rests on the finished picture.
const LOOP_FOR_MS = 60000;
async function play(fig) {
  const id = fig.runId = (fig.runId || 0) + 1;
  const started = performance.now();
  while (id === fig.runId) {
    const finished = await runOnce(fig, id);
    if (!finished) { return; }
    await wait(1800);
    if (id !== fig.runId) { return; }
    if (performance.now() - started > LOOP_FOR_MS) {
      stopFig(fig);
      return;
    }
  }
}

async function runOnce(fig, id) {
  fig.querySelectorAll(".ghost").forEach((g) => g.remove());
  const srcs = items(fig, "data-src");
  const outs = items(fig, "data-out");
  const statics = items(fig, "data-static");
  const mid = fig.querySelector(".mid");
  srcs.forEach((el) => { el.style.opacity = "1"; });
  outs.forEach((el) => { el.style.opacity = "0"; });
  statics.forEach((el) => { el.style.opacity = "0"; });
  await wait(450);
  if (id !== fig.runId) { return false; }
  statics.forEach((el) => {
    el.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 400 });
    el.style.opacity = "1";
  });

  for (const [i, src] of srcs.entries()) {
    if (id !== fig.runId) { return false; }
    const base = fig.getBoundingClientRect();
    const rect = src.getBoundingClientRect();
    const ghost = src.cloneNode(true);
    ghost.removeAttribute("data-src");
    ghost.classList.add("ghost");
    ghost.style.left = `${rect.left - base.left}px`;
    ghost.style.top = `${rect.top - base.top}px`;
    ghost.style.width = `${rect.width}px`;
    ghost.style.opacity = "1";
    fig.append(ghost);
    src.style.opacity = "0.4";
    const from = centre(src, base);
    const to = centre(mid, base);
    const trip = ghost.animate([
      { transform: "translate(0, 0) scale(1)", opacity: 1 },
      { transform: `translate(${to.x - from.x}px, ${to.y - from.y}px) scale(0.55)`, opacity: 0 }
    ], { duration: 750, easing: "cubic-bezier(0.45, 0, 0.55, 1)", fill: "forwards" });
    await trip.finished.catch(() => {});
    ghost.remove();
    if (id !== fig.runId) { return false; }
    mid.classList.add("busy");
    await wait(280);
    mid.classList.remove("busy");
    if (id !== fig.runId) { return false; }
    const out = outs[i];
    const outAt = centre(out, base);
    const midAt = centre(mid, base);
    out.style.opacity = "1";
    out.animate([
      { transform: `translate(${(midAt.x - outAt.x) * 0.45}px, ${(midAt.y - outAt.y) * 0.45}px) scale(0.7)`, opacity: 0 },
      { transform: "translate(0, 0) scale(1)", opacity: 1 }
    ], { duration: 550, easing: "cubic-bezier(0.2, 0.7, 0.3, 1)" });
    await wait(550);
  }
  return id === fig.runId;
}

const match = /^#p(\d+)$/.exec(location.hash);
show(match ? Number(match[1]) - 1 : 0, false);
