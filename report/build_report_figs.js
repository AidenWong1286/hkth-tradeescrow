// Hero figures for the report, drawn with the same visual system as the v2 deck (presentation/style2.js).
// Output: report/figs/report_figs.pptx -> rendered to PNG by report/build_report_v2.sh (LibreOffice + pdftoppm).
const pptxgen = require("pptxgenjs");
const path = require("path");
const fs = require("fs");
const D = require("../presentation/deck_common.js");
const S = require("../presentation/style2.js");
const { C, HF, BF, T, R, card, circle, pill, arrow, kpi } = S;
const { md, mv } = D;
// report palette (matches cover): navy / teal / gold; red only for exceptions
Object.assign(C, { navy: "0B1730", ink: "0B1730", teal: "1F8A82", tealD: "176A64", orange: "B07A22", amber: "B07A22", blue: "0B1730", green: "1F8A82", red: "B8342A", purple: "5B6573" });
Object.assign(S.STATE, { "Created": "7A8496", "Pending": "B07A22", "Under Review": "B8342A", "Frozen": "0B1730", "Released": "1F8A82", "Refunded/Terminated": "3E4A5E" });

(async () => {
  const pres = new pptxgen();
  pres.defineLayout({ name: "BAN", width: 13.333, height: 5.2 });
  pres.layout = "BAN";

  // 1. cover hero: corridor on navy
  let s = pres.addSlide(); s.background = { color: C.navy };
  const cy = 1.25, hx = 1.2, tx = 11.15;
  arrow(s, pres, hx + 1.1, cy + 0.55, tx - 0.05, cy + 0.55, "3B5A8A", 2.5, { noHead: true, dash: "dash" });
  circle(s, pres, hx, cy, 1.1, C.blue, "HK", { size: 26, line: "8FA3C4", lw: 3 });
  circle(s, pres, tx, cy, 1.1, C.orange, "TH", { size: 26, line: "E3C68E", lw: 3 });
  T(s, "Hong Kong importer", { x: hx - 0.7, y: cy + 1.2, w: 2.5, h: 0.35, fontSize: 15, color: "C9D6E8", align: "center" });
  T(s, "Thai exporter", { x: tx - 0.7, y: cy + 1.2, w: 2.5, h: 0.35, fontSize: 15, color: "C9D6E8", align: "center" });
  const vx = 5.0, vw = 3.33;
  R(s, pres, vx, cy - 0.75, vw, 2.4, C.navy2, { round: 0.12, line: C.teal, lw: 2.5, name: "vault" });
  T(s, "ESCROW  ·  TOKENISED DEPOSITS", { x: vx, y: cy - 0.6, w: vw, h: 0.35, fontSize: 13, bold: true, color: "7DD3C0", align: "center", charSpacing: 2 });
  T(s, "HKD 250,000", { x: vx, y: cy - 0.15, w: vw, h: 0.75, fontSize: 36, bold: true, color: C.white, align: "center", valign: "middle" });
  T(s, "locked until all three gates pass", { x: vx, y: cy + 0.65, w: vw, h: 0.4, fontSize: 15, color: "C9D6E8", align: "center" });
  arrow(s, pres, hx + 1.15, cy + 0.2, vx - 0.1, cy + 0.2, "7DD3C0", 2.5);
  T(s, "pre-funds", { x: hx + 1.3, y: cy - 0.25, w: 2.4, h: 0.35, fontSize: 14, color: "7DD3C0", italic: true });
  arrow(s, pres, vx + vw + 0.1, cy + 0.2, tx - 0.15, cy + 0.2, "9FD3CC", 2.5);
  T(s, "released once", { x: vx + vw + 0.35, y: cy - 0.25, w: 2.4, h: 0.35, fontSize: 14, color: "9FD3CC", italic: true });
  [["1", "Shipment"], ["2", "Documents"], ["3", "Compliance"]].forEach(([n, g], i) => {
    const gx = 3.75 + i * 2.05, gy = 3.5;
    R(s, pres, gx, gy, 1.85, 0.55, i === 2 ? C.orange : C.teal, { round: 0.27, name: "gate" + i });
    T(s, `${n}  ${g}`, { x: gx, y: gy, w: 1.85, h: 0.55, fontSize: 16, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
    arrow(s, pres, gx + 0.925, gy - 0.03, vx + vw / 2 + (i - 1) * 0.9, cy + 1.66, "5B7BA8", 1.75, { noHead: true });
  });

  // 2. how the release decision works (gates + exception routes)

  s = pres.addSlide(); s.background = { color: C.white };
  const gates = [["Shipment", "attested for THIS trade's shipment ID", "Logistics"], ["Documents", "latest revisions match the contract", "Bank H ops"], ["Compliance", "fresh KYC/AML (≤ 48 h) and no active hold", "Bank H compliance"]];
  const gw = 2.9, gh = 2.45, gy = 0.3, MX = 0.4;
  gates.forEach(([t, b, who], i) => {
    const x = MX + i * (gw + 0.25);
    card(s, pres, x, gy, gw, gh, { top: C.teal, name: "gate" + i, shadow: false });
    circle(s, pres, x + 0.25, gy + 0.32, 0.62, C.teal, i + 1, { size: 22 });
    T(s, t, { x: x + 1.0, y: gy + 0.32, w: gw - 1.1, h: 0.62, fontSize: 20, bold: true, color: C.navy, fontFace: HF, valign: "middle", margin: 0 });
    T(s, b, { x: x + 0.25, y: gy + 1.1, w: gw - 0.5, h: 0.85, fontSize: 17, color: C.slate, margin: 0 });
    pill(s, pres, x + 0.25, gy + 1.95, Math.min(gw - 0.5, 0.35 + ("attested by " + who).length * 0.085), 0.34, "attested by " + who, C.tealL, { size: 11.5, color: C.tealD });
  });
  const rx = MX + 3 * (gw + 0.25) + 0.4, rw = 13.333 - MX - rx;
  arrow(s, pres, rx - 0.55, gy + gh / 2, rx - 0.05, gy + gh / 2, C.navy, 3);
  R(s, pres, rx, gy, rw, gh, C.green, { round: 0.1, name: "released" });
  T(s, "ALL PASS", { x: rx, y: gy + 0.3, w: rw, h: 0.3, fontSize: 13, bold: true, color: "CFE8E4", align: "center", charSpacing: 2 });
  T(s, "RELEASED", { x: rx, y: gy + 0.65, w: rw, h: 0.7, fontSize: 30, bold: true, color: C.white, align: "center", valign: "middle", fontFace: HF });
  T(s, "exactly once,\nfunds conserved", { x: rx, y: gy + 1.45, w: rw, h: 0.8, fontSize: 17, color: "E4F2EF", align: "center" });
  T(s, "IF A GATE FAILS", { x: MX, y: 3.05, w: 4, h: 0.3, fontSize: 13, bold: true, color: C.mute, charSpacing: 2, margin: 0 });
  [["Document mismatch", "UNDER REVIEW", S.STATE["Under Review"], "Human reviewer revalidates, or terminates and refunds"],
   ["AML / sanctions alert", "FROZEN", S.STATE.Frozen, "Compliance clears (then re-screens), or confirms and refunds"]].forEach(([cause, st, hex, who], i) => {
    const fw = (13.333 - 2 * MX - 0.3) / 2, x = MX + i * (fw + 0.3), y = 3.45;
    card(s, pres, x, y, fw, 1.4, { name: "fail" + i, shadow: false });
    R(s, pres, x, y, 0.1, 1.4, hex, { name: "failbar" + i });
    T(s, cause, { x: x + 0.3, y: y + 0.15, w: 3.0, h: 0.5, fontSize: 18, bold: true, color: C.ink, valign: "middle", margin: 0 });
    arrow(s, pres, x + 3.2, y + 0.4, x + 3.6, y + 0.4, C.mute, 1.75);
    pill(s, pres, x + 3.7, y + 0.2, 2.3, 0.42, st, hex, { size: 14 });
    T(s, who, { x: x + 0.3, y: y + 0.8, w: fw - 0.5, h: 0.45, fontSize: 15.5, italic: true, color: C.slate, margin: 0 });
  });
  // the HOW slide needs its own size: pptxgenjs has one layout per file, so write two files
  const out = path.join(D.ROOT, "report", "figs");
  fs.mkdirSync(out, { recursive: true });
  await pres.writeFile({ fileName: path.join(out, "report_figs.pptx") });

  // 3. architecture (light, native) — separate file because it needs its own page size
  const { icon } = require("../presentation/v3/icons.js");
  const L = { card: "FFFFFF", line: "D8E0EA", txt: "0B1730", sub: "475569", mute: "64748B", teal: "1F8A82", orange: "B07A22", sky: "2B4570", violet: "5B6573", blue: "0B1730", bg: "F6F8FB" };
  const ap = new pptxgen();
  ap.defineLayout({ name: "ARCH", width: 13.333, height: 6.15 }); ap.layout = "ARCH";
  const a = ap.addSlide(); a.background = { color: "FFFFFF" };
  const AT = (t, o) => a.addText(t, Object.assign({ fontFace: "Inter", fontSize: 13, color: L.sub, margin: 0, valign: "top" }, o));
  const AB = (x, y, w, h, o = {}) => a.addShape(o.oval ? ap.shapes.OVAL : ap.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: o.r === undefined ? 0.1 : o.r,
    fill: { color: o.fill || L.card, transparency: o.tr || 0 }, line: o.line === null ? { type: "none" } : { color: o.line || L.line, width: o.lw || 1, dashType: o.dash } });
  const AL = (x1, y1, x2, y2, col, w = 1.75) => a.addShape(ap.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.max(Math.abs(x2 - x1), 0.001), h: Math.max(Math.abs(y2 - y1), 0.001), flipH: x2 < x1, flipV: y2 < y1, line: { color: col, width: w, endArrowType: "triangle" } });
  const AI = async (n, col, x, y, sz) => a.addImage({ path: await icon(n, col, 256), x, y, w: sz, h: sz });
  const M0 = 0.35, AW = 13.333 - 2 * M0;
  AT("PARTICIPANTS  ·  seven business roles, selected in the UI; permissions enforced server-side", { x: M0, y: 0.15, w: 10, h: 0.3, fontSize: 11, bold: true, color: L.mute, charSpacing: 1.5 });
  const roles = [["Building2", "HK importer"], ["Factory", "Thai exporter"], ["Landmark", "Bank H operations"], ["ShieldCheck", "Bank H compliance"], ["Building", "Thai Bank O (observer)"], ["Truck", "Logistics provider"], ["Stamp", "Customs authority"], ["Eye", "Regulator (read-only)"]];
  const arw = (AW - 7 * 0.12) / 8;
  for (let i = 0; i < 8; i++) { const x = M0 + i * (arw + 0.12); AB(x, 0.5, arw, 0.66, { fill: L.bg }); await AI(roles[i][0], i === 7 ? L.sky : L.sub, x + 0.1, 0.68, 0.3); AT(roles[i][1], { x: x + 0.46, y: 0.5, w: arw - 0.5, h: 0.66, fontSize: 10.5, bold: true, color: L.txt, valign: "middle" }); }
  AB(M0 + 3.0, 1.42, 6.6, 0.62, { fill: "EEF1F6", line: "C9D3E3" });
  await AI("MonitorPlay", L.blue, M0 + 3.15, 1.58, 0.3);
  AT([{ text: "Presentation  ", options: { bold: true, color: L.blue } }, { text: "Streamlit app  ·  Flask console (verified fallback)", options: { color: L.txt } }], { x: M0 + 3.55, y: 1.42, w: 6.0, h: 0.62, fontSize: 12.5, valign: "middle" });
  AL(13.333 / 2, 1.18, 13.333 / 2, 1.4, L.mute); AL(13.333 / 2, 2.06, 13.333 / 2, 2.3, L.mute);
  const aey = 2.35, aeh = 2.65;
  AB(M0, aey, 4.15, aeh, { fill: "F8F1E3", line: L.orange, lw: 1.5, dash: "dash", r: 0.14 });
  AT("TRUST BOUNDARY  ·  OFF-CHAIN (simulated)", { x: M0 + 0.2, y: aey + 0.15, w: 3.9, h: 0.28, fontSize: 10, bold: true, color: L.orange, charSpacing: 1 });
  const att = [["Truck", "Shipment", "logistics, per shipment ID"], ["FileSearch", "Documents", "contract · invoice · B/L"], ["UserCheck", "KYC / AML", "creation + pre-release"]];
  for (let i = 0; i < 3; i++) { const y = aey + 0.55 + i * 0.68; AB(M0 + 0.18, y, 3.8, 0.58); await AI(att[i][0], L.orange, M0 + 0.3, y + 0.13, 0.32);
    AT([{ text: att[i][1] + "   ", options: { bold: true, color: L.txt } }, { text: att[i][2], options: { color: L.mute } }], { x: M0 + 0.75, y, w: 3.2, h: 0.58, fontSize: 11.5, valign: "middle" }); }
  AL(M0 + 4.2, aey + aeh / 2, M0 + 4.62, aey + aeh / 2, L.orange, 2.25);
  const agx = M0 + 4.7, agw = 4.35;
  AB(agx, aey, agw, aeh, { fill: "EEF7F5", line: L.teal, alw: 2, r: 0.14 });
  await AI("Cpu", L.teal, agx + 0.25, aey + 0.22, 0.48);
  AT("ESCROW SERVICE LAYER  ·  BANK H", { x: agx + 0.85, y: aey + 0.2, w: 3.4, h: 0.26, fontSize: 10, bold: true, color: L.teal, charSpacing: 1.5 });
  AT("Simulated smart contract", { x: agx + 0.85, y: aey + 0.45, w: 3.4, h: 0.35, fontSize: 16, bold: true, color: L.txt });
  const inner = [["Command authorisation", "role + party scope"], ["Six-state machine", "+ release guard (7 checks)"], ["Append-only journal", "SHA-256 hash chain"]];
  inner.forEach(([t, b], i) => { const y = aey + 0.98 + i * 0.53; AB(agx + 0.25, y, agw - 0.5, 0.45); AT([{ text: t + "   ", options: { bold: true, color: L.txt } }, { text: b, options: { color: L.mute } }], { x: agx + 0.4, y, w: agw - 0.7, h: 0.45, fontSize: 11.5, valign: "middle" }); });
  AL(agx + agw + 0.05, aey + aeh / 2, agx + agw + 0.45, aey + aeh / 2, L.teal, 2.25);
  const alx = agx + agw + 0.5, alw = 13.333 - M0 - alx;
  const outs = [["Coins", "Token accounting", "TDEP-HKD · cents · conserved", L.sky], ["Database", "SQLite mock ledger", "permissioned, single operator", L.violet], ["Eye", "Role views & audit export", "own data only · regulator: metadata", L.blue]];
  for (let i = 0; i < 3; i++) { const y = aey + i * 0.9; AB(alx, y, alw, 0.8); await AI(outs[i][0], outs[i][3], alx + 0.15, y + 0.2, 0.38);
    AT(outs[i][1], { x: alx + 0.65, y: y + 0.1, w: alw - 0.75, h: 0.3, fontSize: 12.5, bold: true, color: L.txt }); AT(outs[i][2], { x: alx + 0.65, y: y + 0.42, w: alw - 0.75, h: 0.3, fontSize: 10, color: L.mute }); }
  AB(M0, 5.25, 6.4, 0.7, { fill: "F3F4F6", line: "C3C9D3", dash: "dash" });
  await AI("ArrowRightLeft", L.violet, M0 + 0.18, 5.43, 0.34);
  AT([{ text: "e-HKD extension (conceptual)  ", options: { bold: true, color: L.violet } }, { text: "2-phase commit, deposits ⇄ CeBM mock", options: { color: L.sub } }], { x: M0 + 0.65, y: 5.25, w: 5.7, h: 0.7, fontSize: 11.5, valign: "middle" });
  AB(M0 + 6.6, 5.25, AW - 6.6, 0.7, { fill: "FBEDEB", line: "E3A39D" });
  await AI("Ban", "B8342A", M0 + 6.78, 5.43, 0.34);
  AT([{ text: "NOT CONNECTED  ", options: { bold: true, color: "B8342A" } }, { text: "real banks · e-HKD · EnsembleTX · KYC/AML · FX", options: { color: L.sub } }], { x: M0 + 7.25, y: 5.25, w: AW - 7.35, h: 0.7, fontSize: 10.5, valign: "middle" });
  await ap.writeFile({ fileName: path.join(out, "arch_fig.pptx") });
  console.log("wrote figs");
})();
