// v3 visual system: dark "midnight fintech" — gradient backgrounds, glass cards, Lucide icons, Inter.
// Objects whose names start with "!!" are paired across consecutive slides by PowerPoint Morph.
const path = require("path");
const { icon } = require("./icons.js");
const D = require("../deck_common.js");
const W = 13.333, H = 7.5, MX = 0.65;
const V3 = path.join(__dirname);
const F = "Inter";
const C = {
  bg: "050C18", card: "0D1B2E", card2: "122641", line: "24406A", line2: "1B3152",
  txt: "F1F5F9", sub: "B9C6D8", mute: "7F93B0", dim: "4B5F7E",
  mint: "2DD4BF", mintD: "0F766E", sky: "38BDF8", amber: "FBBF24", coral: "FB7185", orange: "FB923C",
  violet: "A78BFA", green: "4ADE80", greenD: "16A34A", blue: "60A5FA", white: "FFFFFF",
};
const ST = { Created: "94A3B8", Pending: "F59E0B", "Under Review": "F97316", Frozen: "3B82F6", Released: "22C55E", "Refunded/Terminated": "A78BFA" };
const CHAPTERS = ["Problem", "Design", "Evidence", "Outlook"];

const glow = (hex, op = 0.45, blur = 16) => ({ type: "outer", blur, offset: 0, angle: 90, color: hex, opacity: op });
const drop = () => ({ type: "outer", blur: 14, offset: 4, angle: 90, color: "000000", opacity: 0.45 });

function T(s, t, o) {
  s.addText(t, Object.assign({ isTextBox: true, fontFace: F, fontSize: 16, color: C.sub, valign: "top", margin: 0 }, o));
}
function box(s, pres, x, y, w, h, o = {}) {
  const shape = o.shape === "oval" ? pres.shapes.OVAL : (o.r === 0 ? pres.shapes.RECTANGLE : pres.shapes.ROUNDED_RECTANGLE);
  s.addShape(shape, {
    x, y, w, h, rectRadius: o.r === undefined ? 0.12 : o.r,
    fill: o.fill === null ? { type: "none" } : { color: o.fill || C.card, transparency: o.tr || 0 },
    line: o.line === null ? { type: "none" } : { color: o.line || C.line2, width: o.lw || 1, dashType: o.dash },
    shadow: o.glow ? glow(o.glow, o.gop, o.gblur) : (o.drop ? drop() : undefined),
    objectName: o.name || "box", flipH: o.flipH, rotate: o.rot,
  });
}
function line(s, pres, x1, y1, x2, y2, hex, w = 1.5, o = {}) {
  s.addShape(pres.shapes.LINE, {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.max(Math.abs(x2 - x1), 0.001), h: Math.max(Math.abs(y2 - y1), 0.001),
    flipH: x2 < x1, flipV: y2 < y1,
    line: { color: hex, width: w, dashType: o.dash, endArrowType: o.head ? "triangle" : undefined, beginArrowType: o.tail ? "oval" : undefined, transparency: o.tr },
    objectName: o.name || "line",
  });
}
function dot(s, pres, x, y, d, hex, o = {}) { box(s, pres, x, y, d, d, Object.assign({ shape: "oval", fill: hex, line: null }, o)); }
function pill(s, pres, x, y, w, h, label, hex, o = {}) {
  box(s, pres, x, y, w, h, { r: h / 2, fill: o.solid ? hex : hex, tr: o.solid ? 0 : 80, line: o.solid ? null : hex, lw: 1, name: o.name || "pill", glow: o.glow });
  T(s, label, { x, y, w, h, fontSize: o.size || 12, bold: true, color: o.solid ? (o.color || "0B1220") : (o.color || hex), align: "center", valign: "middle", charSpacing: o.cs || 0.5 });
}
async function ico(s, name, hex, x, y, sz, o = {}) {
  const p = await icon(name, hex, 256, o.stroke);
  s.addImage({ path: p, x, y, w: sz, h: sz, objectName: o.name || "icon_" + name, altText: name });
}
// tinted rounded square with icon
async function badge(s, pres, name, hex, x, y, sz, o = {}) {
  box(s, pres, x, y, sz, sz, { r: sz * 0.28, fill: hex, tr: 84, line: hex, lw: 0.75, name: o.name || "badge", glow: o.glow ? hex : undefined, gop: 0.35 });
  await ico(s, name, hex, x + sz * 0.22, y + sz * 0.22, sz * 0.56, { name: (o.name || "badge") + "_i" });
}
function bg(s, kind = "main") {
  s.background = { path: path.join(V3, `bg_${kind}.png`) };
}
const EVID = {
  TEST: ["EXECUTED TESTS", "synthetic data", C.mint], MODEL: ["TEAM PROCESS MODEL", "not measured savings", C.orange],
  TIMING: ["ASSUMED TIMINGS", "simulated days", C.violet], FACT: ["OFFICIAL PUBLIC SOURCE", "context only", C.sky],
  DEMO: ["REAL APP SCREENSHOT", "synthetic data", C.mint],
};
function chrome(s, pres, o) {
  // kicker with accent bar
  const ch = o.chapter;
  const kick = ch !== undefined ? `${String(ch + 1).padStart(2, "0")}   ${CHAPTERS[ch].toUpperCase()}` : (o.kicker || "");
  box(s, pres, MX, 0.56, 0.42, 0.055, { r: 0, fill: C.mint, line: null, name: "!!accent", glow: C.mint, gop: 0.6, gblur: 8 });
  T(s, kick, { x: MX + 0.55, y: 0.44, w: 5, h: 0.3, fontSize: 11.5, bold: true, color: C.mint, charSpacing: 3, valign: "middle", objectName: "kicker" });
  if (ch !== undefined) {
    const tw = 1.05, gx = W - MX - CHAPTERS.length * (tw + 0.1) + 0.1;
    CHAPTERS.forEach((c, i) => {
      box(s, pres, gx + i * (tw + 0.1), 0.5, tw, 0.05, { r: 0, fill: C.line2, line: null, name: "trk_bg" + i });
      T(s, c, { x: gx + i * (tw + 0.1), y: 0.6, w: tw, h: 0.25, fontSize: 9.5, color: i === ch ? C.txt : C.dim, bold: i === ch, objectName: "trk_t" + i });
    });
    box(s, pres, gx + ch * (tw + 0.1), 0.5, tw, 0.05, { r: 0, fill: C.mint, line: null, name: "!!trk", glow: C.mint, gop: 0.7, gblur: 6 });
  }
  const ts = o.titleSize || Math.max(24, Math.min(32, Math.floor((W - 2 * MX) * 72 / (0.56 * o.title.length))));
  T(s, o.title, { x: MX, y: 0.86, w: W - 2 * MX, h: 0.7, fontSize: ts, bold: true, color: C.txt, valign: "middle", objectName: "!!title" });
  if (o.sub) T(s, o.sub, { x: MX, y: 1.52, w: W - 2 * MX, h: 0.36, fontSize: 15, color: C.mute, valign: "middle", objectName: "subtitle" });
  // footer
  box(s, pres, MX, H - 0.5, 0.09, 0.09, { shape: "oval", fill: C.mint, line: null, name: "f_dot" });
  T(s, [{ text: "HK–TH TradeEscrow", options: { bold: true, color: C.sub } }, { text: "   FTEC3002 · Group 1", options: { color: C.dim } }],
    { x: MX + 0.2, y: H - 0.6, w: 5, h: 0.3, fontSize: 10, valign: "middle", objectName: "footer" });
  if (o.evidence) {
    const [a, b, hex] = EVID[o.evidence];
    const w = 0.75 + (a.length + b.length) * 0.088;
    const x = W - MX - 0.75 - w;
    box(s, pres, x, H - 0.64, w, 0.32, { r: 0.16, fill: hex, tr: 86, line: hex, lw: 0.75, name: "evid" });
    dot(s, pres, x + 0.14, H - 0.53, 0.1, hex, { name: "evid_dot" });
    T(s, [{ text: a, options: { bold: true, color: hex } }, { text: "  ·  " + b, options: { color: C.sub } }], { x: x + 0.32, y: H - 0.64, w: w - 0.35, h: 0.32, fontSize: 9.5, valign: "middle", charSpacing: 0.5 });
  }
  if (o.num) T(s, String(o.num).padStart(2, "0"), { x: W - MX - 0.6, y: H - 0.6, w: 0.6, h: 0.3, fontSize: 10, color: C.mute, align: "right", valign: "middle", bold: true });
}
function src(s, txt, links) {
  const parts = [{ text: txt, options: { color: C.dim } }];
  (links || []).forEach((l, i) => parts.push({ text: (txt || i ? "   " : "") + l.text, options: { hyperlink: { url: l.url }, color: C.sky } }));
  s.addText(parts, { x: MX, y: H - 0.98, w: W - 2 * MX, h: 0.3, fontSize: 10, italic: true, fontFace: F, valign: "bottom", margin: 0, objectName: "source" });
}
// dark browser window around a real screenshot (frame only; pixels untouched)
function browser(s, pres, img, x, y, w, h, o = {}) {
  const bar = 0.34, nm = o.name || "browser";
  box(s, pres, x, y, w, h, { r: 0.1, fill: "0A1526", line: "2A4672", lw: 1, glow: o.glow || C.sky, gop: 0.22, gblur: 22, name: nm });
  box(s, pres, x, y, w, bar, { r: 0.1, fill: "15243B", line: null, name: nm + "_bar" });
  box(s, pres, x, y + bar - 0.1, w, 0.1, { r: 0, fill: "15243B", line: null, name: nm + "_bar2" });
  ["FF5F57", "FEBC2E", "28C840"].forEach((c, i) => dot(s, pres, x + 0.16 + i * 0.2, y + 0.115, 0.11, c, { name: nm + "_d" + i }));
  const uw = Math.min(w - 1.1, 4.4);
  box(s, pres, x + 0.85, y + 0.07, uw, 0.2, { r: 0.1, fill: "0B1626", line: null, name: nm + "_url" });
  T(s, o.url || "127.0.0.1:5050 · TradeEscrow console · synthetic data", { x: x + 0.97, y: y + 0.07, w: uw - 0.2, h: 0.2, fontSize: 8.5, color: C.mute, valign: "middle", objectName: nm + "_urlt" });
  return D.fit(s, img, x + 0.07, y + bar + 0.05, w - 0.14, h - bar - 0.12, { align: o.align, valign: o.valign || "top", alt: o.alt });
}
function morphAll(xml, first) {
  if (first) return xml;
  const tr = '<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">' +
    '<mc:Choice xmlns:p159="http://schemas.microsoft.com/office/powerpoint/2015/09/main" Requires="p159">' +
    '<p:transition xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main" spd="slow" p14:dur="1100"><p159:morph option="byObject"/></p:transition>' +
    '</mc:Choice><mc:Fallback><p:transition spd="slow"><p:fade/></p:transition></mc:Fallback></mc:AlternateContent>';
  if (xml.includes("</p:clrMapOvr>")) return xml.replace("</p:clrMapOvr>", "</p:clrMapOvr>" + tr);
  return xml.replace("</p:cSld>", "</p:cSld>" + tr);
}
module.exports = { C, ST, F, W, H, MX, CHAPTERS, T, box, line, dot, pill, ico, badge, bg, chrome, src, browser, glow, drop, morphAll, EVID };
