/* TradeEscrow console: progressive enhancement over the server-rendered pages.
   - Intercepts form posts on the console, fetches the re-rendered page and swaps it in place.
   - Animates the difference between the previous and new snapshot (#snap), which the server builds
     only from data this role can already see. Nothing here decides an outcome: every animation
     replays a result the engine has already journalled.
   - Film mode replays a scenario one step at a time through /sim/step (operator control).
   Without JavaScript the pages work exactly as plain forms. */
(() => {
  "use strict";
  if (!document.body.classList.contains("page-console")) return;

  const RM = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const sleep = (ms) => new Promise((r) => setTimeout(r, RM ? 0 : ms));
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const fmt = (minor) => Math.round(minor / 100).toLocaleString("en-US");
  const center = (el) => { const r = el.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; };
  const readSnap = (root = document) => { const el = root.querySelector("#snap"); return el ? JSON.parse(el.textContent) : null; };
  const segClass = (el) => (el.classList.contains("ok") ? "ok" : el.classList.contains("bad") ? "bad" : "");
  let busy = false;

  // ------------------------------------------------------------------ swap
  function capture() {
    return {
      snap: readSnap(),
      segs: Object.fromEntries($$("#ring .seg").map((s) => [s.dataset.gate, segClass(s)])),
      chainLeft: ($("#chain") || {}).scrollLeft || 0,
    };
  }

  async function postForm(action, fd) {
    const res = await fetch(action, { method: "POST", body: fd, credentials: "same-origin" });
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      const j = await res.json().catch(() => ({}));
      throw new Error(j.error || "REQUEST_FAILED");
    }
    return res.text();
  }

  async function swap(html) {
    const before = capture();
    const doc = new DOMParser().parseFromString(html, "text/html");
    const app = doc.querySelector("#app");
    if (!app) { window.location.reload(); return; }
    const top = doc.querySelector("#topbar");
    if (top) $("#topbar").replaceWith(top);
    $("#app").replaceWith(app);
    await animate(before, readSnap());
  }

  // ------------------------------------------------------------------ animations
  async function animate(b, a) {
    if (!b.snap || !a) return;
    document.body.classList.add("animating");
    try { await animateInner(b, a); } finally { document.body.classList.remove("animating"); }
  }

  async function animateInner(b, a) {
    const chain = $("#chain");
    if (b.snap.viewer !== a.viewer) {          // role switch: the lens re-projects the same escrow
      if (chain) chain.scrollLeft = chain.scrollWidth;
      return lens();
    }
    const known = new Set(b.snap.events.map((e) => e.id));
    const fresh = a.events.filter((e) => !known.has(e.id));
    fresh.forEach((e) => $$(`[data-id="${CSS.escape(e.id)}"]`).forEach((el) => el.classList.add("fresh")));
    if (chain) { chain.scrollLeft = b.chainLeft; requestAnimationFrame(() => chain.scrollTo({ left: chain.scrollWidth, behavior: RM ? "auto" : "smooth" })); }

    const guardIsNew = a.guard && (!b.snap.guard || b.snap.guard.id !== a.guard.id);
    const stateChanged = b.snap.state !== a.state;
    const ring = $("#ring");
    const wasOpen = ring && ring.classList.contains("open");
    if (ring && guardIsNew) ring.classList.remove("open");

    // Prime numbers with their previous values so they can count up/down later.
    const counters = $$("[data-k]").map((el) => {
      const k = el.dataset.k, to = Number(el.dataset.amt);
      let from = b.snap.corridor[k];
      if (from === null || from === undefined) from = (k === "escrow" && !b.snap.state) ? 0 : to;
      if (from !== to) el.textContent = fmt(from);
      return { el, from, to };
    }).filter((c) => c.from !== c.to);

    if (guardIsNew) await gateSequence(a.guard);
    else await gateDiff(b.segs);
    if (ring && wasOpen === false && ring && a.state === "Released") ring.classList.add("open");
    if (ring && guardIsNew && a.state === "Released") ring.classList.add("open");

    const jobs = [];
    if (stateChanged) {
      jobs.push(comet(b.snap.state, a.state));
      const flow = flowFor(b.snap.state, a.state);
      if (flow) jobs.push(fly(flow[0], flow[1], counters));
      else jobs.push(countAll(counters, 0));
      stateWord(b.snap.state);
    } else {
      jobs.push(countAll(counters, 0));
    }
    if (b.snap.journal_ok && !a.journal_ok) jobs.push(crack());
    await Promise.all(jobs);
  }

  function stateWord(prev) {
    const w = $("#stateword");
    if (!w || RM) return;
    const word = w.querySelector("span");
    if (prev) {
      const old = document.createElement("span");
      old.textContent = prev;
      old.style.cssText = "position:absolute;left:0;top:0";
      w.style.position = "relative";
      w.appendChild(old);
      const out = old.animate([{ transform: "none", opacity: 1 }, { transform: "translateY(-100%)", opacity: 0 }], { duration: 650, easing: "cubic-bezier(.6,0,.2,1)", fill: "forwards" });
      out.finished.then(() => old.remove()).catch(() => old.remove());
    }
    word.animate([{ transform: "translateY(100%)", opacity: 0 }, { transform: "none", opacity: 1 }], { duration: 750, delay: prev ? 120 : 0, easing: "cubic-bezier(.2,.8,.2,1)", fill: "backwards" });
    const sig = w.querySelector(".sig");
    if (sig) sig.animate([{ transform: "scale(0)" }, { transform: "scale(1.4)" }, { transform: "none" }], { duration: 600, delay: 700, fill: "backwards" });
  }

  function flowFor(from, to) {
    if (!from && to === "Created") return ["#vault-importer", "#ring"];
    if (to === "Released") return ["#ring", "#vault-exporter"];
    if (to === "Refunded/Terminated") return ["#ring", "#vault-importer"];
    return null;
  }

  async function gateSequence(guard) {
    const segs = $$("#ring .seg"), items = $$("#guard .gates li");
    const finals = segs.map(segClass), finalsLi = items.map((li) => li.className);
    segs.forEach((s) => s.classList.remove("ok", "bad"));
    items.forEach((li) => { li.className = "pending"; });
    await sleep(250);
    for (let i = 0; i < segs.length; i++) {
      const s = segs[i], li = items[i];
      if (finals[i]) s.classList.add(finals[i]);
      if (li) li.className = finalsLi[i];
      if (!RM) s.animate([{ strokeWidth: 4, opacity: 0.25 }, { strokeWidth: 10, opacity: 1 }, { strokeWidth: 4, opacity: 1 }], { duration: 440, easing: "ease-out" });
      if (finals[i] === "bad") {
        const ring = $("#ring");
        ring.classList.remove("shake"); void ring.offsetWidth; ring.classList.add("shake");
        if (li && !RM) li.animate([{ transform: "translateX(-5px)" }, { transform: "translateX(5px)" }, { transform: "none" }], { duration: 300 });
        await sleep(420);
      } else {
        await sleep(170);
      }
    }
    await sleep(260);
  }

  async function gateDiff(oldSegs) {
    const changed = $$("#ring .seg").filter((s) => (oldSegs[s.dataset.gate] || "") !== segClass(s));
    for (const s of changed) {
      const now = segClass(s), li = $(`#guard li[data-gate="${s.dataset.gate}"]`);
      s.classList.remove("ok", "bad");
      if (oldSegs[s.dataset.gate]) s.classList.add(oldSegs[s.dataset.gate]);
      await sleep(120);
      s.classList.remove("ok", "bad");
      if (now) s.classList.add(now);
      if (!RM) {
        s.animate([{ strokeWidth: 4 }, { strokeWidth: 10 }, { strokeWidth: 4 }], { duration: 480, easing: "ease-out" });
        if (li) li.animate([{ background: now === "bad" ? "rgba(232,102,91,.22)" : "rgba(127,127,127,.18)" }, { background: "transparent" }], { duration: 1200 });
      }
    }
  }

  function countAll(counters, delay) {
    return Promise.all(counters.map((c) => count(c, delay)));
  }

  function count({ el, from, to }, delay = 0, dur = 1100) {
    return new Promise((done) => {
      if (RM) { el.textContent = fmt(to); return done(); }
      setTimeout(() => {
        const t0 = performance.now();
        const tick = (t) => {
          const p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3);
          el.textContent = fmt(from + (to - from) * e);
          if (p < 1) requestAnimationFrame(tick); else done();
        };
        requestAnimationFrame(tick);
      }, delay);
    });
  }

  async function fly(fromSel, toSel, counters) {
    const fromEl = $(fromSel), toEl = $(toSel);
    if (!fromEl || !toEl || RM) return countAll(counters, 0);
    const A = center(fromEl), B = center(toEl);
    const lanes = $$(".lane");
    lanes.forEach((l) => l.classList.add("live"));
    const tok = document.createElement("div");
    tok.className = "token";
    const ghosts = [1, 2, 3, 4].map(() => { const g = document.createElement("div"); g.className = "token ghost"; g.style.opacity = "0"; document.body.appendChild(g); return g; });
    document.body.appendChild(tok);
    const lift = Math.min(110, Math.abs(B.x - A.x) * 0.25 + 40);
    const mid = { x: (A.x + B.x) / 2, y: Math.min(A.y, B.y) - lift };
    const at = (p, s, o = 1) => ({ transform: `translate(${p.x}px,${p.y}px) scale(${s})`, opacity: o });
    const outCount = counters.filter((c) => c.to < c.from), inCount = counters.filter((c) => c.to >= c.from);
    countAll(outCount, 150);
    const path = [at(A, 0.4, 0), { ...at(A, 1.1), offset: 0.12 }, { ...at(mid, 1.25), offset: 0.55 }, { ...at(B, 1), offset: 0.9 }, at(B, 0.3, 0)];
    const timing = { duration: 1500, easing: "cubic-bezier(.45,.05,.35,1)" };
    const anim = tok.animate(path, timing);
    ghosts.forEach((g, n) => {
      const trail = g.animate(path.map((f) => ({ ...f, opacity: f.opacity === 0 ? 0 : 0.42 - n * 0.09 })), { ...timing, delay: (n + 1) * 45 });
      trail.finished.then(() => g.remove()).catch(() => g.remove());
    });
    await sleep(1250);
    const vault = toEl.classList.contains("vault") ? toEl : null;
    if (vault) vault.classList.add("glow");
    if (toEl.id === "ring" && !RM) toEl.animate([{ transform: "scale(1)" }, { transform: "scale(1.05)" }, { transform: "none" }], { duration: 500 });
    await Promise.all([countAll(inCount, 0), anim.finished.catch(() => {})]);
    tok.remove();
    lanes.forEach((l) => l.classList.remove("live"));
    setTimeout(() => vault && vault.classList.remove("glow"), 900);
  }

  function comet(from, to) {
    return new Promise((done) => {
      const trail = from ? $(`#metro .trail[data-from="${CSS.escape(from)}"][data-to="${CSS.escape(to)}"]`) : null;
      const node = $(`#metro .node[data-state="${CSS.escape(to || "")}"]`);
      const pulse = () => { if (node && !RM) node.animate([{ opacity: 0.4 }, { opacity: 1 }], { duration: 500 }); done(); };
      if (!trail || RM) return pulse();
      const L = trail.getTotalLength(), rev = trail.dataset.rev === "1";
      trail.style.strokeDasharray = `${L} ${L}`;
      trail.style.strokeDashoffset = rev ? -L : L;
      const svg = trail.ownerSVGElement;
      const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      dot.setAttribute("r", "6"); dot.setAttribute("class", "comet");
      svg.appendChild(dot);
      const dur = 900, t0 = performance.now();
      const tick = (t) => {
        const p = Math.min(1, (t - t0) / dur), e = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
        const pt = trail.getPointAtLength(rev ? L * (1 - e) : L * e);
        dot.setAttribute("cx", pt.x); dot.setAttribute("cy", pt.y);
        trail.style.strokeDashoffset = (rev ? -L : L) * (1 - e);
        if (p < 1) requestAnimationFrame(tick);
        else { dot.remove(); trail.style.strokeDasharray = ""; trail.style.strokeDashoffset = ""; pulse(); }
      };
      requestAnimationFrame(tick);
    });
  }

  async function crack() {
    const broken = $$("#chain .blk.broken");
    broken.forEach((b) => b.classList.remove("broken"));
    const chain = $("#chain");
    if (chain && broken[0]) chain.scrollTo({ left: broken[0].offsetLeft - 40, behavior: RM ? "auto" : "smooth" });
    await sleep(400);
    for (const b of broken) {
      b.classList.add("broken");
      if (!RM) b.animate([{ transform: "translateY(0)" }, { transform: "translateY(-4px) rotate(-2deg)" }, { transform: "none" }], { duration: 260 });
      await sleep(90);
    }
  }

  async function lens() {
    for (const host of [$("#stage"), $("#lens")]) {
      if (!host) continue;
      const scan = document.createElement("div");
      scan.className = "lens-scan";
      host.appendChild(scan);
      setTimeout(() => scan.remove(), 1000);
    }
    if (RM) return;
    $$(".field").forEach((f, i) => f.animate([{ opacity: 0, transform: "translateY(4px)" }, { opacity: 1, transform: "none" }],
      { duration: 380, delay: 250 + i * 35, fill: "backwards", easing: "ease-out" }));
    $$(".redact, .ring .hidden").forEach((r) => r.animate([{ filter: "blur(6px)", opacity: 0 }, { filter: "none", opacity: 1 }], { duration: 600, delay: 300, fill: "backwards" }));
    await sleep(900);
  }

  // ------------------------------------------------------------------ form interception
  document.addEventListener("submit", async (ev) => {
    const form = ev.target;
    if (!form.closest("#app")) return;
    ev.preventDefault();
    if (busy || film.playing) return;
    busy = true;
    const btn = ev.submitter || form.querySelector("button");
    if (btn) btn.classList.add("busy");
    try {
      if (form.getAttribute("action") === "/sim/reset" || form.getAttribute("action") === "/sim/autoplay") film.i = 0;
      await swap(await postForm(form.getAttribute("action"), new FormData(form)));
    } catch (err) {
      form.submit();   // fall back to a normal post
    } finally {
      busy = false;
    }
  });

  // ------------------------------------------------------------------ film mode
  const film = { playing: false, i: 0, variant: null };
  const stepsEl = $("#filmsteps");
  const STEPS = stepsEl ? JSON.parse(stepsEl.textContent) : {};
  const playBtn = $("#filmplay"), varSel = $("#filmvar"), cap = $("#filmcap"), sub = $("#filmsub"), dots = $("#filmdots");

  function drawDots(n, i) {
    if (!dots) return;
    dots.innerHTML = "";
    for (let k = 0; k < n; k++) {
      const d = document.createElement("i");
      if (k < i) d.className = "done"; else if (k === i) d.className = "now";
      dots.appendChild(d);
    }
  }

  async function playFilm() {
    const v = varSel.value;
    if (film.variant !== v) { film.variant = v; film.i = 0; }
    const steps = STEPS[v] || [];
    film.playing = true;
    document.body.classList.add("filming");
    playBtn.textContent = "❚❚"; playBtn.setAttribute("aria-label", "Pause");
    while (film.playing && film.i < steps.length) {
      const s = steps[film.i];
      drawDots(steps.length, film.i);
      cap.textContent = `${s.role}: ${s.label}`;
      sub.textContent = `Step ${film.i + 1} of ${steps.length}. ${s.help || ""}`;
      await sleep(film.i === 0 ? 600 : 1000);
      const fd = new FormData(); fd.set("variant", v); fd.set("i", String(film.i));
      try { await swap(await postForm("/sim/step", fd)); }
      catch (e) { cap.textContent = "Playback stopped"; sub.textContent = String(e.message || e); break; }
      film.i += 1;
      await sleep(1500);
    }
    const finished = film.i >= steps.length;
    film.playing = false;
    document.body.classList.remove("filming");
    playBtn.textContent = finished ? "↻" : "▶"; playBtn.setAttribute("aria-label", finished ? "Replay" : "Resume");
    if (finished) {
      drawDots(steps.length, steps.length);
      const snap = readSnap();
      cap.textContent = `Scenario complete: escrow ${snap && snap.state ? snap.state.toLowerCase() : "closed"}`;
      sub.textContent = "Switch participant to see how the same escrow looks to each role.";
      film.i = 0;
    }
  }

  const cine = $("#cinema");
  const setCinema = (on) => { document.body.classList.toggle("cinema", on); if (cine) cine.setAttribute("aria-pressed", String(on)); };
  if (cine) cine.addEventListener("click", () => setCinema(!document.body.classList.contains("cinema")));
  document.addEventListener("keydown", (e) => {
    if (e.key.toLowerCase() !== "c" || e.ctrlKey || e.metaKey || /INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)) return;
    setCinema(!document.body.classList.contains("cinema"));
  });

  if (playBtn) {
    playBtn.addEventListener("click", () => { if (film.playing) film.playing = false; else if (!busy) playFilm(); });
    varSel.addEventListener("change", () => { film.i = 0; film.variant = varSel.value; drawDots((STEPS[varSel.value] || []).length, -1); playBtn.textContent = "▶"; });
    drawDots((STEPS[varSel.value] || []).length, -1);
    document.addEventListener("keydown", (e) => {
      if (e.code !== "Space" || /INPUT|SELECT|TEXTAREA|BUTTON/.test(document.activeElement.tagName)) return;
      e.preventDefault(); playBtn.click();
    });
  }

  // ------------------------------------------------------------------ first paint: one entrance
  if (!RM) {
    $$("#ring .seg").forEach((s, i) => s.animate([{ opacity: 0, strokeWidth: 1 }, { opacity: 1, strokeWidth: 4 }], { duration: 500, delay: 120 + i * 70, fill: "backwards", easing: "ease-out" }));
    $$(".vault").forEach((v, i) => v.animate([{ opacity: 0, transform: "translateY(10px)" }, { opacity: 1, transform: "none" }], { duration: 600, delay: i * 140, fill: "backwards", easing: "cubic-bezier(.2,.8,.2,1)" }));
  }
  const ch = $("#chain"); if (ch) ch.scrollLeft = ch.scrollWidth;
})();
