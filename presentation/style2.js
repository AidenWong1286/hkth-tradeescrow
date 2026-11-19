// Visual system v2 for the final deck (and the report hero figures rendered from it).
// Navy / teal / amber palette, Georgia titles, Calibri body, card + browser-frame components.
const D = require("./deck_common.js");
const W = 13.333, H = 7.5, MX = 0.6;

const C = {
  navy: "0B1F3A", navy2: "132C52", navy3: "1E3A66", ink: "0F172A", slate: "475569", mute: "64748B",
  line: "E2E8F0", bg: "F4F7FB", white: "FFFFFF",
  teal: "0E9384", tealD: "0B6E63", tealL: "DDF3EF", tealXL: "EFFAF7",
  amber: "F59E0B", orange: "E8772E", orangeD: "9A4A0B", orangeL: "FDEEDF",
  blue: "2563EB", blueL: "E3ECFD", green: "15803D", greenL: "DCF3E3", red: "DC2626", redL: "FDE5E5",
  purple: "7C3AED", grey: "A3ABB8",
};
const HF = "Georgia", BF = "Calibri";
const STATE = D.STATE_HEX;
const CHAPTERS = ["Problem", "Design", "Evidence", "Outlook"];

const shadow = () => ({ type: "outer", blur: 8, offset: 2, angle: 90, color: "0B1F3A", opacity: 0.14 });

function T(s, t, o) {
  s.addText(t, Object.assign({ isTextBox: true, fontSize: 18, color: C.ink, valign: "top", margin: 0.03, fontFace: BF }, o));
}
function R(s, pres, x, y, w, h, fill, o = {}) {
  s.addShape(o.round ? pres.shapes.ROUNDED_RECTANGLE : pres.shapes.RECTANGLE, Object.assign({
    x, y, w, h, fill: { color: fill }, line: o.line ? { color: o.line, width: o.lw || 1 } : { color: fill, width: 0 },
    rectRadius: o.round || 0, shadow: o.shadow ? shadow() : undefined, objectName: o.name || "shape" }, o.extra || {}));
}
function card(s, pres, x, y, w, h, o = {}) {
  R(s, pres, x, y, w, h, o.fill || C.white, { round: 0.08, line: o.line || C.line, lw: 1, shadow: o.shadow !== false, name: o.name || "card" });
  if (o.top) R(s, pres, x, y, w, 0.09, o.top, { name: (o.name || "card") + "_bar" });
}
function circle(s, pres, x, y, d, fill, label, o = {}) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: o.line || fill, width: o.lw || 0 }, objectName: o.name || "dot" });
  if (label !== undefined) T(s, String(label), { x, y, w: d, h: d, fontSize: o.size || d * 30, bold: true, color: o.color || C.white,
    align: "center", valign: "middle", margin: 0, fontFace: o.font || BF });
}
function pill(s, pres, x, y, w, h, label, fill, o = {}) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: h / 2, fill: { color: fill }, line: { color: o.line || fill, width: o.lw || 0 }, objectName: o.name || "pill" });
  T(s, label, { x, y, w, h, fontSize: o.size || 14, bold: true, color: o.color || C.white, align: "center", valign: "middle", margin: 0, charSpacing: o.cs || 0 });
}
function arrow(s, pres, x1, y1, x2, y2, hex, w, o = {}) {
  s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.001, h: Math.abs(y2 - y1) || 0.001,
    flipH: x2 < x1, flipV: y2 < y1, line: { color: hex || C.mute, width: w || 2, endArrowType: o.noHead ? undefined : "triangle", dashType: o.dash }, objectName: "arrow" });
}

// evidence-type tag (outline pill, top right)
const EV = {
  TEST: ["EXECUTED TESTS · synthetic data", C.teal], MODEL: ["TEAM PROCESS MODEL · not measured savings", C.orange],
  TIMING: ["ASSUMED TIMINGS · simulated days", C.purple], FACT: ["OFFICIAL PUBLIC SOURCE", C.blue],
  DEMO: ["REAL APP SCREENSHOT · synthetic data", C.teal],
};
function evidence(s, pres, kind, x, y) {
  const [label, hex] = EV[kind];
  const w = Math.max(2.5, 0.45 + label.length * 0.078);
  const px = x === undefined ? W - MX - w : x, py = y === undefined ? 0.98 : y;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: px, y: py, w, h: 0.32, rectRadius: 0.16, fill: { color: C.white }, line: { color: hex, width: 1.25 }, objectName: "evidence" });
  circle(s, pres, px + 0.12, py + 0.1, 0.12, hex);
  T(s, label, { x: px + 0.28, y: py, w: w - 0.32, h: 0.32, fontSize: 10.5, bold: true, color: hex, valign: "middle", margin: 0, charSpacing: 0.5 });
}

// standard content slide chrome
function content(pres, o) {
  const s = pres.addSlide({ masterName: "C2", sectionTitle: o.section || "Main" });
  // kicker
  const ch = o.chapter;
  if (ch !== undefined) {
    T(s, `${String(ch + 1).padStart(2, "0")}  ·  ${CHAPTERS[ch].toUpperCase()}`, { x: MX, y: 0.32, w: 4, h: 0.3, fontSize: 12, bold: true, color: C.teal, charSpacing: 2, margin: 0 });
    // chapter tracker (top right)
    let x = W - MX - CHAPTERS.length * 1.25;
    CHAPTERS.forEach((c, i) => {
      R(s, pres, x + i * 1.25, 0.43, 1.12, 0.06, i === ch ? C.teal : C.line, { name: "track" + i });
      T(s, c, { x: x + i * 1.25, y: 0.5, w: 1.12, h: 0.25, fontSize: 9.5, color: i === ch ? C.teal : C.grey, bold: i === ch, margin: 0 });
    });
  } else if (o.kicker) {
    T(s, o.kicker, { x: MX, y: 0.32, w: 6, h: 0.3, fontSize: 12, bold: true, color: C.teal, charSpacing: 2, margin: 0 });
  }
  const tw = W - 2 * MX, tsize = Math.max(21, Math.min(o.titleSize || 28, Math.floor(tw * 72 / (0.575 * o.title.length))));
  T(s, o.title, { x: MX, y: 0.62, w: tw, h: 0.75, fontSize: tsize, bold: true, color: C.navy, fontFace: HF, valign: "middle", margin: 0, fit: "shrink" });
  if (o.evidence) evidence(s, pres, o.evidence, MX + (ch !== undefined ? 2.25 : 2.6), 0.27);
  R(s, pres, MX, 1.42, 0.7, 0.05, C.amber, { name: "title_rule" });
  return s;
}
function source(s, pres, txt, links) {
  const parts = [{ text: txt, options: { color: C.mute } }];
  (links || []).forEach((l, i) => parts.push({ text: (i || txt ? "   " : "") + l.text, options: { hyperlink: { url: l.url }, color: C.blue, underline: { style: "sng" } } }));
  s.addText(parts, { x: MX, y: H - 0.86, w: W - 2 * MX - 1.2, h: 0.32, fontSize: 11, italic: true, valign: "bottom", margin: 0, fontFace: BF, objectName: "source" });
}

// browser-window frame around a real screenshot (frame is drawn around, never on, the pixels)
function browser(s, pres, imgPath, x, y, w, h, o = {}) {
  const bar = 0.32;
  R(s, pres, x, y, w, h, C.white, { round: 0.06, line: "CBD5E1", shadow: true, name: "browser" });
  R(s, pres, x, y, w, bar, "E8EDF3", { round: 0.06, name: "browser_bar" });
  R(s, pres, x, y + bar - 0.08, w, 0.08, "E8EDF3", { name: "browser_bar2" });
  ["F87171", "FBBF24", "34D399"].forEach((c, i) => circle(s, pres, x + 0.15 + i * 0.2, y + 0.1, 0.12, c));
  R(s, pres, x + 0.85, y + 0.06, Math.min(w - 1.0, 4.2), 0.2, C.white, { round: 0.1, name: "url" });
  T(s, o.url || "127.0.0.1:5050  ·  TradeEscrow console (synthetic data)", { x: x + 0.95, y: y + 0.06, w: Math.min(w - 1.1, 4.0), h: 0.2, fontSize: 9, color: C.mute, valign: "middle", margin: 0 });
  return D.fit(s, imgPath, x + 0.08, y + bar + 0.06, w - 0.16, h - bar - 0.12, { align: o.align, valign: o.valign || "top", alt: o.alt });
}

// big KPI card
function kpi(s, pres, x, y, w, h, big, label, hex, o = {}) {
  card(s, pres, x, y, w, h, { top: hex, name: o.name || "kpi" });
  T(s, big, { x: x + 0.25, y: y + 0.25, w: w - 0.5, h: h * 0.45, fontSize: o.size || 44, bold: true, color: hex, valign: "middle", fontFace: BF, margin: 0 });
  T(s, label, { x: x + 0.25, y: y + 0.25 + h * 0.45, w: w - 0.5, h: h * 0.5 - 0.3, fontSize: o.lsize || 16, color: C.slate, margin: 0 });
}

function defineMasters(pres) {
  pres.defineLayout({ name: "WIDE", width: W, height: H });
  pres.layout = "WIDE";
  pres.theme = { headFontFace: HF, bodyFontFace: BF };
  pres.defineSlideMaster({
    title: "C2", background: { color: C.white },
    slideNumber: { x: W - MX - 0.6, y: H - 0.45, w: 0.6, h: 0.3, fontSize: 11, color: C.mute, align: "right", fontFace: BF },
    objects: [
      { rect: { x: 0, y: H - 0.55, w: W, h: 0.55, fill: { color: C.bg } } },
      { rect: { x: 0, y: H - 0.55, w: W, h: 0.02, fill: { color: C.line } } },
      { text: { text: "HK–TH TradeEscrow", options: { x: MX, y: H - 0.45, w: 2.2, h: 0.3, fontSize: 11, bold: true, color: C.navy, fontFace: BF, margin: 0 } } },
      { text: { text: "FTEC3002 Group 1  ·  Final presentation  ·  synthetic simulation only", options: { x: MX + 1.75, y: H - 0.45, w: 7, h: 0.3, fontSize: 11, color: C.mute, fontFace: BF, margin: 0 } } },
    ],
  });
  pres.defineSlideMaster({ title: "DARK", background: { color: C.navy }, objects: [] });
}

module.exports = { C, HF, BF, W, H, MX, STATE, CHAPTERS, T, R, card, circle, pill, arrow, evidence, content, source, browser, kpi, defineMasters, shadow };
