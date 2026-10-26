// Page navigation (progress bar, contents, Back/Next, arrow keys) and the looping diagram animations
// for index.html. Pages are the .lesson sections; data-part groups them into Part 1 and Part 2.
(function () {
  var pages = Array.prototype.slice.call(document.querySelectorAll(".lesson"));
  var partNames = { "1": "Part 1 · The big picture", "2": "Part 2 · Contributing" };
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var current = 0;

  var partsEl = document.getElementById("parts");
  var contentsEl = document.getElementById("contents");
  var contentsBtn = document.getElementById("contentsBtn");
  var prev = document.getElementById("prev");
  var next = document.getElementById("next");
  var count = document.getElementById("count");

  // Group pages by part for the progress bar and the contents list.
  var groups = [];
  pages.forEach(function (page, index) {
    var part = page.dataset.part;
    var last = groups[groups.length - 1];
    if (!last || last.part !== part) { last = { part: part, pages: [] }; groups.push(last); }
    last.pages.push(index);
  });

  var segs = [];
  var contentItems = [];
  var partEls = [];
  groups.forEach(function (group) {
    var partEl = document.createElement("div");
    partEl.className = "part";
    partEl.style.flex = String(group.pages.length);
    var label = document.createElement("div");
    label.className = "part-label";
    label.textContent = partNames[group.part];
    var row = document.createElement("div");
    row.className = "segs";
    partEl.appendChild(label);
    partEl.appendChild(row);
    partsEl.appendChild(partEl);
    partEls.push({ el: partEl, part: group.part });

    var block = document.createElement("div");
    var heading = document.createElement("h3");
    heading.textContent = partNames[group.part];
    var list = document.createElement("ol");
    block.appendChild(heading);
    block.appendChild(list);
    contentsEl.appendChild(block);

    group.pages.forEach(function (index, n) {
      var seg = document.createElement("button");
      seg.type = "button";
      seg.className = "seg";
      seg.setAttribute("aria-label", "Go to " + pages[index].dataset.title);
      seg.title = pages[index].dataset.title;
      seg.addEventListener("click", function () { show(index, true); });
      row.appendChild(seg);
      segs[index] = seg;

      var item = document.createElement("li");
      var go = document.createElement("button");
      go.type = "button";
      var num = document.createElement("span");
      num.textContent = String(n + 1);
      go.appendChild(num);
      go.appendChild(document.createTextNode(pages[index].dataset.title));
      go.addEventListener("click", function () { setContents(false); show(index, true); });
      item.appendChild(go);
      list.appendChild(item);
      contentItems[index] = go;
    });
  });

  function setContents(open) {
    contentsEl.hidden = !open;
    contentsBtn.setAttribute("aria-expanded", open ? "true" : "false");
  }
  contentsBtn.addEventListener("click", function () { setContents(contentsEl.hidden); });

  function positionInPart(index) {
    var group = groups.filter(function (g) { return g.pages.indexOf(index) !== -1; })[0];
    return { part: group.part, n: group.pages.indexOf(index) + 1, of: group.pages.length };
  }

  function show(index, scroll) {
    var previous = pages[current];
    current = Math.max(0, Math.min(pages.length - 1, index));
    pages.forEach(function (page, i) { page.hidden = i !== current; });
    segs.forEach(function (seg, i) {
      seg.classList.toggle("done", i < current);
      seg.classList.toggle("now", i === current);
      seg.setAttribute("aria-current", i === current ? "step" : "false");
    });
    contentItems.forEach(function (item, i) { item.setAttribute("aria-current", i === current ? "true" : "false"); });
    var pos = positionInPart(current);
    partEls.forEach(function (p) { p.el.classList.toggle("on", p.part === pos.part); });
    count.innerHTML = "<b>Part " + pos.part + "</b> · " + pos.n + " of " + pos.of;
    prev.disabled = current === 0;
    next.disabled = current === pages.length - 1;

    var previousFig = previous && previous !== pages[current] ? previous.querySelector(".anim") : null;
    if (previousFig) { stopFig(previousFig); }
    var fig = pages[current].querySelector(".anim");
    if (fig) {
      if (reduceMotion) { stopFig(fig); } else { play(fig); }
    }
    if (scroll) { partsEl.scrollIntoView({ block: "nearest" }); }
  }

  prev.addEventListener("click", function () { show(current - 1, true); });
  next.addEventListener("click", function () { show(current + 1, true); });
  document.querySelectorAll("[data-go]").forEach(function (button) {
    button.addEventListener("click", function () {
      var target = button.dataset.go === "next" ? current + 1 : parseInt(button.dataset.go, 10);
      show(target, true);
    });
  });
  document.addEventListener("keydown", function (event) {
    if (event.altKey || event.ctrlKey || event.metaKey) { return; }
    // Leave arrow keys alone inside code blocks, which scroll sideways.
    if (event.target.closest && event.target.closest("pre")) { return; }
    if (event.key === "Escape") { setContents(false); }
    if (event.key === "ArrowRight") { show(current + 1, false); }
    if (event.key === "ArrowLeft") { show(current - 1, false); }
  });

  // Animation: each input item travels into the machine, then its output appears.
  function wait(ms) { return new Promise(function (resolve) { setTimeout(resolve, ms); }); }
  function centre(el, base) {
    var r = el.getBoundingClientRect();
    return { x: r.left - base.left + r.width / 2, y: r.top - base.top + r.height / 2 };
  }
  function items(fig, attr) { return Array.prototype.slice.call(fig.querySelectorAll("[" + attr + "]")); }
  function restState(fig) {
    items(fig, "data-src").forEach(function (el) { el.style.opacity = "0.4"; });
    items(fig, "data-out").forEach(function (el) { el.style.opacity = "1"; });
    items(fig, "data-static").forEach(function (el) { el.style.opacity = "1"; });
    fig.querySelector(".mid").classList.remove("busy");
  }
  function stopFig(fig) {
    fig.runId = (fig.runId || 0) + 1;
    fig.querySelectorAll(".ghost").forEach(function (g) { g.remove(); });
    restState(fig);
  }

  // Loops for about a minute, then rests on the finished picture.
  var LOOP_FOR_MS = 60000;
  async function play(fig) {
    var id = fig.runId = (fig.runId || 0) + 1;
    var started = performance.now();
    while (id === fig.runId) {
      var finished = await runOnce(fig, id);
      if (!finished) { return; }
      await wait(1800);
      if (id !== fig.runId) { return; }
      if (performance.now() - started > LOOP_FOR_MS) { stopFig(fig); return; }
    }
  }

  async function runOnce(fig, id) {
    fig.querySelectorAll(".ghost").forEach(function (g) { g.remove(); });
    var srcs = items(fig, "data-src");
    var outs = items(fig, "data-out");
    var statics = items(fig, "data-static");
    var mid = fig.querySelector(".mid");
    srcs.forEach(function (el) { el.style.opacity = "1"; });
    outs.forEach(function (el) { el.style.opacity = "0"; });
    statics.forEach(function (el) { el.style.opacity = "0"; });
    await wait(450);
    if (id !== fig.runId) { return false; }
    statics.forEach(function (el) { el.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 400 }); el.style.opacity = "1"; });

    for (var i = 0; i < srcs.length; i++) {
      if (id !== fig.runId) { return false; }
      var base = fig.getBoundingClientRect();
      var src = srcs[i];
      var rect = src.getBoundingClientRect();
      var ghost = src.cloneNode(true);
      ghost.removeAttribute("data-src");
      ghost.classList.add("ghost");
      ghost.style.left = (rect.left - base.left) + "px";
      ghost.style.top = (rect.top - base.top) + "px";
      ghost.style.width = rect.width + "px";
      ghost.style.opacity = "1";
      fig.appendChild(ghost);
      src.style.opacity = "0.4";
      var from = centre(src, base);
      var to = centre(mid, base);
      var trip = ghost.animate([
        { transform: "translate(0, 0) scale(1)", opacity: 1 },
        { transform: "translate(" + (to.x - from.x) + "px, " + (to.y - from.y) + "px) scale(0.55)", opacity: 0 }
      ], { duration: 750, easing: "cubic-bezier(0.45, 0, 0.55, 1)", fill: "forwards" });
      await trip.finished.catch(function () {});
      ghost.remove();
      if (id !== fig.runId) { return false; }
      mid.classList.add("busy");
      await wait(280);
      mid.classList.remove("busy");
      if (id !== fig.runId) { return false; }
      var out = outs[i];
      var outAt = centre(out, base);
      var midAt = centre(mid, base);
      out.style.opacity = "1";
      out.animate([
        { transform: "translate(" + (midAt.x - outAt.x) * 0.45 + "px, " + (midAt.y - outAt.y) * 0.45 + "px) scale(0.7)", opacity: 0 },
        { transform: "translate(0, 0) scale(1)", opacity: 1 }
      ], { duration: 550, easing: "cubic-bezier(0.2, 0.7, 0.3, 1)" });
      await wait(550);
    }
    return id === fig.runId;
  }

  var match = /^#p(\d+)$/.exec(location.hash);
  show(match ? parseInt(match[1], 10) - 1 : 0, false);
})();
