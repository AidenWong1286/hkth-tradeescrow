// Shared theme, layouts and helpers for the interim and final decks (pptxgenjs, 16:9 wide 13.33 x 7.5 in).
// Projection-readability targets (audit §7): titles 28–32 pt, body 18–24 pt, one takeaway per main slide.
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");

const THEME = {
  name: "HKTH TradeEscrow",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "14213D", lt1: "FFFFFF", dk2: "0B3C49", lt2: "EEF3F6",
    accent1: "0F766E", accent2: "E07A1F", accent3: "2A78D6", accent4: "15803D",
    accent5: "1D4ED8", accent6: "7C3AED", hlink: "0F5FA6", folHlink: "0B3C49",
  },
};
const HEX = THEME.colors;
const MUTED = "5B6573", LINE = "C7D0DA", RED = "B91C1C", GREY = "8A94A6";
const STATE_HEX = { "Created": "64748B", "Pending": "B7791F", "Under Review": "C2410C", "Frozen": "1D4ED8",
                    "Released": "15803D", "Refunded/Terminated": "7C3AED" };
const W = 13.333, H = 7.5, MX = 0.6;

// Evidence-type legend (audit §7: executed tests / process model / assumed timings / official facts)
const EVIDENCE = {
  TEST: { label: "EXECUTED TESTS · synthetic data", hex: "0F766E" },
  MODEL: { label: "TEAM-DEFINED PROCESS MODEL · not measured savings", hex: "B45309" },
  TIMING: { label: "ASSUMED TIMINGS · simulated days, not bank data", hex: "9333EA" },
  FACT: { label: "OFFICIAL PUBLIC SOURCE", hex: "1D4ED8" },
  DEMO: { label: "REAL APP SCREENSHOT · synthetic data", hex: "0F766E" },
};

function defineLayouts(pres, footerText) {
  pres.defineLayout({ name: "WIDE", width: W, height: H });
  pres.layout = "WIDE";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.defineSlideMaster({
    title: "TITLE_DARK",
    background: { color: HEX.dk1 },
    objects: [
      { rect: { x: 0, y: H - 0.12, w: W, h: 0.12, fill: { color: HEX.accent2 } } },
      { placeholder: { options: { name: "title", type: "title", x: MX, y: 1.7, w: 12.1, h: 1.9, fontSize: 40, bold: true,
          align: "left", color: "FFFFFF", valign: "bottom", fontFace: THEME.headFontFace }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "CONTENT",
    background: { color: "FFFFFF" },
    slideNumber: { x: W - 1.0, y: H - 0.42, w: 0.5, h: 0.3, fontSize: 12, color: MUTED, align: "right" },
    objects: [
      { rect: { x: 0, y: 0, w: 0.14, h: H, fill: { color: HEX.accent1 } } },
      { text: { text: footerText, options: { x: MX, y: H - 0.42, w: 8.5, h: 0.3, fontSize: 11, color: MUTED } } },
      { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.3, w: W - 2 * MX, h: 0.95, fontSize: 30, bold: true,
          align: "left", color: HEX.dk1, valign: "middle", fontFace: THEME.headFontFace }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "SECTION_DARK",
    background: { color: HEX.dk2 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: MX, y: 2.6, w: 12.1, h: 1.3, fontSize: 36, bold: true,
          align: "left", color: "FFFFFF", fontFace: THEME.headFontFace }, text: "" } },
    ],
  });
}

function text(slide, t, o) {
  slide.addText(t, Object.assign({ isTextBox: true, fontSize: 20, color: HEX.dk1, valign: "top", margin: 0.04,
    fontFace: THEME.bodyFontFace }, o));
}
function box(slide, pres, x, y, w, h, fill, line, name) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.1, fill: { color: fill || HEX.lt2 },
    line: { color: line || fill || HEX.lt2, width: line ? 1.5 : 0.75 }, objectName: name || "box" });
}
function rect(slide, pres, x, y, w, h, fill, name) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill }, objectName: name || "rect" });
}
function arrow(slide, pres, x1, y1, x2, y2, hex, w) {
  slide.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.001,
    h: Math.abs(y2 - y1) || 0.001, flipH: x2 < x1, flipV: y2 < y1,
    line: { color: hex || MUTED, width: w || 2.5, endArrowType: "triangle" }, objectName: "arrow" });
}
function stat(slide, pres, x, y, w, h, big, label, hex, name) {
  box(slide, pres, x, y, w, h, HEX.lt2, null, name);
  text(slide, big, { x: x + 0.2, y: y + 0.15, w: w - 0.4, h: h * 0.5, fontSize: 44, bold: true, color: hex || HEX.accent1,
    fontFace: THEME.headFontFace, valign: "middle", objectName: name + "_value" });
  text(slide, label, { x: x + 0.2, y: y + h * 0.55, w: w - 0.4, h: h * 0.42, fontSize: 18, color: "374151",
    objectName: name + "_label" });
}
function pill(slide, pres, x, y, w, h, label, hex, size, name) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: h / 2, fill: { color: hex }, line: { color: hex },
    objectName: name || "pill" });
  text(slide, label, { x, y, w, h, fontSize: size || 16, bold: true, color: "FFFFFF", align: "center", valign: "middle",
    margin: 0, objectName: (name || "pill") + "_t" });
}
// small coloured tag naming the evidence type of what the slide shows
function evidence(slide, pres, kind, x, y) {
  const e = EVIDENCE[kind];
  const w = Math.max(2.6, e.label.length * 0.092);
  pill(slide, pres, x === undefined ? W - MX - w : x, y === undefined ? 0.08 : y, w, 0.3, e.label, e.hex, 11, "evidence_" + kind);
}
function source(slide, s, links) {
  // links: optional [{text, url}] rendered as clickable hyperlinks after s
  const parts = [{ text: s, options: { color: MUTED } }];
  (links || []).forEach((l, i) => parts.push({ text: (i || s ? "  " : "") + l.text,
    options: { hyperlink: { url: l.url }, color: HEX.hlink, underline: { style: "sng" } } }));
  slide.addText(parts, { x: MX, y: H - 0.82, w: W - 2 * MX - 0.6, h: 0.36, fontSize: 12, italic: true, valign: "bottom",
    margin: 0.02, objectName: "source" });
}
function img(p) { return path.join(ROOT, p); }
function imgSize(p) {
  const buf = fs.readFileSync(img(p));
  if (buf[0] === 0x89) return [buf.readUInt32BE(16), buf.readUInt32BE(20)];
  let i = 2;
  while (i < buf.length) {
    const len = buf.readUInt16BE(i + 2);
    if (buf[i + 1] >= 0xC0 && buf[i + 1] <= 0xC2) return [buf.readUInt16BE(i + 7), buf.readUInt16BE(i + 5)];
    i += 2 + len;
  }
  throw new Error("size? " + p);
}
// place an image inside a box keeping aspect ratio; returns the placed rectangle
function fit(slide, p, x, y, w, h, o = {}) {
  const [iw, ih] = imgSize(p);
  let pw = w, ph = w * ih / iw;
  if (ph > h) { ph = h; pw = h * iw / ih; }
  const px = x + (o.align === "left" ? 0 : (w - pw) / 2), py = y + (o.valign === "top" ? 0 : (h - ph) / 2);
  slide.addImage({ path: img(p), x: px, y: py, w: pw, h: ph, altText: o.alt || path.basename(p), objectName: o.name || "image" });
  if (o.border) slide.addShape("rect", { x: px, y: py, w: pw, h: ph, fill: { type: "none" }, line: { color: LINE, width: 1 } });
  return { x: px, y: py, w: pw, h: ph };
}
function readCSV(p) {
  const txt = fs.readFileSync(img(p), "utf8").replace(/^﻿/, "");
  const rows = []; let row = [], cur = "", q = false;
  for (let i = 0; i < txt.length; i++) {
    const ch = txt[i];
    if (q) { if (ch === '"' && txt[i + 1] === '"') { cur += '"'; i++; } else if (ch === '"') q = false; else cur += ch; }
    else if (ch === '"') q = true; else if (ch === ",") { row.push(cur); cur = ""; }
    else if (ch === "\n") { row.push(cur); rows.push(row); row = []; cur = ""; } else if (ch !== "\r") cur += ch;
  }
  if (cur || row.length) { row.push(cur); rows.push(row); }
  const [h, ...r] = rows; return r.filter(x => x.length > 1).map(x => Object.fromEntries(h.map((k, i) => [k, x[i]])));
}
const METRICS = Object.fromEntries(readCSV("results/metrics.csv").map(m => [m.metric_id, m]));
const mv = id => METRICS[id].value;
const md = id => `${METRICS[id].value}/${METRICS[id].denominator}`;
const MANIFEST = JSON.parse(fs.readFileSync(img("results/run_manifest.json"), "utf8"));

module.exports = { THEME, HEX, MUTED, LINE, RED, GREY, STATE_HEX, W, H, MX, EVIDENCE, defineLayouts, text, box, rect, arrow,
  stat, pill, evidence, source, img, imgSize, fit, readCSV, METRICS, mv, md, MANIFEST, ROOT };
