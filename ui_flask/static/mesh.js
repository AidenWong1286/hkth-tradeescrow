/* Animated 2D SVG wireframe wave mesh (no WebGL) + light/dark theme switch.
   Two diagonal "ribbons", each drawn as ONE <path> of ~34 hairlines (1px, low opacity) plus one
   <path> of faint cross-lines. Every line follows the same slow wave; a signed twist term spreads
   the lines apart and folds them back through zero, which reads as a faux-3D topographic ribbon.
   ~30 fps, paused while the tab is hidden, a single static frame under prefers-reduced-motion. */
(() => {
  "use strict";
  // ---------------------------------------------------------------- theme switch (all pages)
  const root = document.documentElement;
  document.addEventListener("click", (e) => {
    if (!e.target.closest("#themetoggle")) return;
    const next = root.dataset.theme === "light" ? "dark" : "light";
    root.dataset.theme = next;
    try { localStorage.setItem("te-theme", next); } catch (err) { /* storage unavailable: still switches */ }
  });

  // ---------------------------------------------------------------- mesh
  const svg = document.getElementById("mesh");
  if (!svg) return;
  const NS = "http://www.w3.org/2000/svg";
  const RM = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const TAU = Math.PI * 2;
  const SAMPLES = 110;

  // cy/amp/width are fractions of the viewport height; speeds are cycles per second (slow: ~20-30 s).
  const RIBBONS = [
    { cy: 0.15, amp: 0.085, width: 0.15, k1: 1.25, k2: 2.6, s1: 0.035, s2: -0.024, twist: 1.6, ts: 0.028, phase: 0.0, lines: 34, rot: -9 },
    { cy: 0.88, amp: 0.080, width: 0.14, k1: 1.05, k2: 2.3, s1: -0.03, s2: 0.021, twist: 1.35, ts: -0.024, phase: 2.4, lines: 34, rot: -9 },
  ];

  let W = 0, H = 0;
  const groups = RIBBONS.map(() => {
    const g = document.createElementNS(NS, "g");
    const ln = document.createElementNS(NS, "path");
    const xl = document.createElementNS(NS, "path");
    ln.setAttribute("class", "ln");
    xl.setAttribute("class", "xl");
    g.append(xl, ln);
    svg.appendChild(g);
    return { g, ln, xl };
  });

  function resize() {
    W = window.innerWidth; H = window.innerHeight;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    RIBBONS.forEach((r, k) => groups[k].g.setAttribute("transform", `rotate(${r.rot} ${W / 2} ${H / 2})`));
  }

  function draw(t) {
    const x0 = -0.2 * W, span = 1.4 * W;
    RIBBONS.forEach((r, k) => {
      const N = r.lines;
      const ys = new Array(N);
      for (let i = 0; i < N; i++) ys[i] = new Float32Array(SAMPLES + 1);
      const xs = new Float32Array(SAMPLES + 1);
      for (let j = 0; j <= SAMPLES; j++) {
        const u = j / SAMPLES;
        xs[j] = x0 + u * span;
        const base = H * (r.cy
          + r.amp * Math.sin(u * r.k1 * TAU + t * r.s1 * TAU + r.phase)
          + r.amp * 0.45 * Math.sin(u * r.k2 * TAU + t * r.s2 * TAU + r.phase * 1.7));
        const tw = Math.sin(u * r.twist * TAU + t * r.ts * TAU + r.phase);           // signed twist, -1..1
        const depth = 1 + 0.22 * Math.cos(u * r.twist * TAU + t * r.ts * TAU + r.phase); // near/far swell
        const half = H * r.width * depth;
        for (let i = 0; i < N; i++) {
          const s = (i / (N - 1)) * 2 - 1;                                            // -1..1 across the ribbon
          const ripple = H * 0.0035 * Math.sin(u * 11 + i * 0.42 + t * 0.35);
          ys[i][j] = base + s * half * tw + s * s * H * 0.018 * depth + ripple;
        }
      }
      let d = "";
      for (let i = 0; i < N; i++) {
        d += `M${xs[0].toFixed(1)} ${ys[i][0].toFixed(1)}`;
        for (let j = 1; j <= SAMPLES; j++) d += `L${xs[j].toFixed(1)} ${ys[i][j].toFixed(1)}`;
      }
      let dx = "";
      for (let j = 0; j <= SAMPLES; j += 3) {
        dx += `M${xs[j].toFixed(1)} ${ys[0][j].toFixed(1)}`;
        for (let i = 1; i < N; i++) dx += `L${xs[j].toFixed(1)} ${ys[i][j].toFixed(1)}`;
      }
      groups[k].ln.setAttribute("d", d);
      groups[k].xl.setAttribute("d", dx);
    });
  }

  resize();
  window.addEventListener("resize", () => { resize(); draw(clock()); });
  const start = performance.now();
  const clock = () => (performance.now() - start) / 1000 + 40;   // start mid-cycle for a good first frame
  draw(clock());
  if (RM) return;

  let last = 0, raf = 0;
  const loop = (now) => {
    raf = requestAnimationFrame(loop);
    if (now - last < 33) return;   // ~30 fps is plenty for a slow ambient drift
    last = now;
    draw(clock());
  };
  raf = requestAnimationFrame(loop);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) cancelAnimationFrame(raf);
    else { last = 0; raf = requestAnimationFrame(loop); }
  });
})();
