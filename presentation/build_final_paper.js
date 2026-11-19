// FINAL presentation — paper & ink edition. Theory-led and deliberately different from the interim (9 Nov) deck.
// Run after: python presentation/v3/cover_art.py && python -c "import sys;sys.path.insert(0,'presentation/v3');import inkkit;inkkit.paper_bg();inkkit.all_v2()" (+ python presentation/v3/inkkit.py once)
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");
const D = require("./deck_common.js");
// Student IDs live in team.local.json (git-ignored); without it footers show names only.
const _TEAM_FILE = path.join(__dirname, "..", "team.local.json");
const TEAM_IDS = fs.existsSync(_TEAM_FILE) ? JSON.parse(fs.readFileSync(_TEAM_FILE, "utf8")).ids : {};
const { icon } = require("./v3/icons.js");
const S3 = require("./v3/style3.js");
const { mv, md } = D;
const W = 13.333, H = 7.5, MX = 0.7;
const V = p => path.join(__dirname, "v3", p);
const K = { ink: "1D1B18", ink2: "3A352E", sub: "4A443B", mute: "7A7264", rule: "C9BFAE", paper: "F7F3EB", card: "FBF8F2",
  teal: "1F8A82", tealL: "DCEFEC", gold: "B07A22", goldL: "F6E7C8", red: "B8342A", redL: "F5DDD8", blue: "2F5E9E", blueL: "DDE6F2", violet: "6B4FA0", violetL: "E8E1F2" };
const SERIF = "Georgia", SANS = "Inter", MONO = "Courier New";
const PARTS = ["Why escrow", "The design", "The evidence", "The verdict"];
const counts = D.readCSV("results/process_counts.csv");
const tl = D.readCSV("results/timelines.csv");
const eh = D.readCSV("results/ehkd_results.csv");
const cnt = (sc, m) => +counts.find(c => c.scenario === sc && c.model === m).manual_settlement_tasks;
const TLr = (m, term = "0") => tl.find(r => r.scenario === "normal" && r.model === m && r.assumption_level === "base" && r.payment_term_days === term);
const URL = {
  exim: "https://www.exim.go.th/EN/Newsroom/newsactivities/EXIM-BANK-%E0%B8%A5%E0%B8%87%E0%B8%99%E0%B8%B2%E0%B8%A1-MOU-%E0%B8%81%E0%B8%9A%E0%B8%AD%E0%B8%87%E0%B8%84%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%AA%E0%B8%A0%E0%B8%B2%E0%B8%9E%E0%B8%92%E0%B8%99%E0%B8%B2%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%84%E0%B8%B2%E0%B8%AE%E0%B8%AD%E0%B8%87%E0%B8%81%E0%B8%87-%E0%B8%AA%E0%B8%99%E0%B8%9A%E0%B8%AA.aspx",
  adb: "https://www.adb.org/news/demand-trade-finance-rise-amid-supply-chain-realignment-adb-report",
  cargox: "https://cdi.hkma.gov.hk/wp-content/uploads/Project_CargoX_Recommendation_Report.pdf",
  cargoxPilot: "https://www.hkma.gov.hk/eng/news-and-media/press-releases/2026/05/20260507-7/",
  ensembleTX: "https://www.hkma.gov.hk/eng/news-and-media/press-releases/2026/11/20261102-5/",
  ensemble: "https://www.hkma.gov.hk/eng/news-and-media/press-releases/2025/11/20251113-3/",
  ehkd: "https://www.hkma.gov.hk/eng/news-and-media/press-releases/2025/10/20251028-4/",
  mbridge: "https://www.bis.org/project/mbridge",
};

function T(s, t, o) { s.addText(t, Object.assign({ isTextBox: true, fontFace: SANS, fontSize: 14, color: K.sub, valign: "top", margin: 0 }, o)); }
function L(s, pres, x1, y1, x2, y2, col = K.ink2, w = 1, o = {}) {
  s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.max(Math.abs(x2 - x1), 0.001), h: Math.max(Math.abs(y2 - y1), 0.001), flipH: x2 < x1, flipV: y2 < y1,
    line: { color: col, width: w, dashType: o.dash, endArrowType: o.head ? "arrow" : undefined }, objectName: o.name || "line" });
}
function R(s, pres, x, y, w, h, o = {}) {
  s.addShape(o.oval ? pres.shapes.OVAL : (o.r ? pres.shapes.ROUNDED_RECTANGLE : pres.shapes.RECTANGLE), { x, y, w, h, rectRadius: o.r || 0,
    fill: o.fill === null ? { type: "none" } : { color: o.fill || K.card, transparency: o.tr || 0 },
    line: o.line === null ? { type: "none" } : { color: o.line || K.rule, width: o.lw || 0.75, dashType: o.dash }, objectName: o.name || "box" });
}
async function I(s, name, col, x, y, sz, nm) { s.addImage({ path: await icon(name, col, 256, 1.6), x, y, w: sz, h: sz, objectName: nm || "icon" }); }
function pill(s, pres, x, y, w, t, col, bg, o = {}) {
  R(s, pres, x, y, w, o.h || 0.3, { r: (o.h || 0.3) / 2, fill: bg || K.paper, line: col, name: o.name });
  T(s, t, { x, y, w, h: o.h || 0.3, fontSize: o.size || 9, bold: true, color: col, align: "center", valign: "middle", charSpacing: 1.2 });
}
function img(s, file, x, y, w, ratio, nm) { s.addImage({ path: V(`ink/${file}.png`), x, y, w, h: w * ratio, objectName: nm || "ink_" + file }); }
const TAG = { TEST: ["EXECUTED TESTS · SYNTHETIC DATA", K.teal], MODEL: ["TEAM PROCESS MODEL · NOT MEASURED", K.gold], TIMING: ["ASSUMED TIMINGS · SIMULATED DAYS", K.gold],
  DEMO: ["REAL APP · SYNTHETIC DATA", K.teal], FACT: ["OFFICIAL PUBLIC SOURCES", K.blue], QUAL: ["QUALITATIVE COMPARISON", K.blue] };
let NUM = 0;
function page(pres, o) {
  const s = pres.addSlide({ masterName: "PAPER", sectionTitle: o.section || "Main" }); NUM++;
  if (o.part !== undefined) {
    T(s, `PART ${o.part + 1}  ·  ${PARTS[o.part].toUpperCase()}`, { x: MX, y: 0.42, w: 6, h: 0.26, fontSize: 10, bold: true, color: K.teal, charSpacing: 3, objectName: "kicker" });
    const tw = 1.05, gx = W - MX - 4 * tw - 0.3;
    PARTS.forEach((p, i) => {
      L(s, pres, gx + i * (tw + 0.1), 0.5, gx + i * (tw + 0.1) + tw, 0.5, K.rule, 1.5, { name: "trk" + i });
      T(s, p, { x: gx + i * (tw + 0.1), y: 0.56, w: tw, h: 0.22, fontSize: 8.5, italic: true, color: i === o.part ? K.ink : K.mute, bold: i === o.part, fontFace: SERIF });
    });
    s.addShape(pres.shapes.LINE, { x: gx + o.part * (tw + 0.1), y: 0.5, w: tw, h: 0, line: { color: K.teal, width: 3 }, objectName: "!!trk" });
  } else T(s, o.kicker || "", { x: MX, y: 0.42, w: 8, h: 0.26, fontSize: 10, bold: true, color: K.teal, charSpacing: 3, objectName: "kicker" });
  T(s, o.title, { x: MX, y: 0.74, w: W - 2 * MX, h: 0.62, fontSize: o.ts || Math.min(29, Math.floor((W - 2 * MX) * 72 / (0.6 * o.title.length))), bold: true, color: K.ink, fontFace: SERIF, valign: "middle", objectName: "!!title" });
  if (o.sub) T(s, o.sub, { x: MX, y: 1.36, w: W - 2 * MX, h: 0.32, fontSize: 13.5, italic: true, color: K.mute, fontFace: SERIF, valign: "middle", objectName: "subtitle" });
  L(s, pres, MX, H - 0.52, W - MX, H - 0.52, K.rule, 0.75, { name: "frule" });
  if (o.presenter) T(s, [{ text: "HK–TH TradeEscrow", options: { bold: true, color: K.ink2 } }, { text: "   ·   Presented by  ", options: { color: K.mute } }, { text: "WONG HO MING" + (TEAM_IDS["Wong Ho Ming"] ? "  ·  " + TEAM_IDS["Wong Ho Ming"] : ""), options: { bold: true, color: K.teal } }], { x: MX, y: H - 0.45, w: 6, h: 0.28, fontSize: 9.5, valign: "middle", objectName: "footer" });
  else T(s, [{ text: "HK–TH TradeEscrow", options: { bold: true, color: K.ink2 } }, { text: "   ·   FTEC3002 Group 1   ·   Final presentation", options: { color: K.mute } }], { x: MX, y: H - 0.45, w: 6, h: 0.28, fontSize: 9.5, valign: "middle", objectName: "footer" });
  T(s, `— ${String(NUM).padStart(2, "0")} —`, { x: W / 2 - 0.6, y: H - 0.45, w: 1.2, h: 0.28, fontSize: 10, italic: true, color: K.mute, fontFace: SERIF, align: "center", valign: "middle", objectName: "pnum" });
  if (o.tag) {
    const [t, c] = TAG[o.tag], w = 0.6 + t.length * 0.085;
    R(s, pres, W - MX - w, H - 0.46, w, 0.27, { fill: null, line: c, lw: 0.9, name: "tag" });
    T(s, t, { x: W - MX - w, y: H - 0.46, w, h: 0.27, fontSize: 8, bold: true, color: c, align: "center", valign: "middle", charSpacing: 1.5 });
  }
  return s;
}
function srcline(s, txt, links = []) {
  const parts = [{ text: txt, options: { color: K.mute } }];
  links.forEach((l, i) => parts.push({ text: (txt || i ? "   " : "") + l.text, options: { hyperlink: { url: l.url }, color: K.blue } }));
  s.addText(parts, { x: MX, y: H - 0.86, w: W - 2 * MX, h: 0.26, fontSize: 8.5, italic: true, fontFace: SERIF, valign: "bottom", margin: 0 });
}

(async () => {
  const pres = new pptxgen();
  pres.defineLayout({ name: "WIDE", width: W, height: H }); pres.layout = "WIDE";
  pres.author = "FTEC3002 Group 1"; pres.title = "HK–TH TradeEscrow — Final Presentation";
  pres.theme = { headFontFace: SERIF, bodyFontFace: SANS };
  pres.defineSlideMaster({ title: "PAPER", background: { path: V("bg_paper.jpg") }, objects: [] });
  pres.addSection({ title: "Main" });
  let s;

  // ═══ 1 COVER ═══
  s = pres.addSlide({ sectionTitle: "Main" }); NUM++;
  s.background = { color: K.paper };
  s.addImage({ path: V("cover_art.jpg"), x: 0, y: 0, w: W, h: H, objectName: "cover_art", altText: "Ink illustration: Hong Kong and Bangkok joined by a trade route with an escrow lock" });
  const lab = (t, x, y, w) => { R(s, pres, x, y, w, 0.3, { r: 0.15, fill: K.paper, tr: 12, line: K.teal }); T(s, t, { x, y, w, h: 0.3, fontSize: 9.5, bold: true, color: K.teal, align: "center", valign: "middle", charSpacing: 1.5 }); };
  lab("HONG KONG  ·  香港", 2.6, 4.32, 1.75); lab("BANGKOK  ·  กรุงเทพฯ", 9.95, 4.48, 1.9);
  T(s, "HKD 250,000 held in escrow", { x: 5.6, y: 2.05, w: 2.96, h: 0.3, fontSize: 10.5, italic: true, bold: true, color: K.gold, align: "center", fontFace: SERIF });
  T(s, "until shipment, documents and compliance all pass", { x: 5.35, y: 2.32, w: 3.46, h: 0.25, fontSize: 9, italic: true, color: "6B6459", align: "center", fontFace: SERIF });
  T(s, "FTEC3002  ·  INTRODUCTION TO FINANCIAL INFRASTRUCTURE", { x: 0.65, y: 5.86, w: 7.4, h: 0.26, fontSize: 9.5, bold: true, color: K.teal, charSpacing: 1.5, objectName: "kicker" });
  T(s, [{ text: "HK–TH ", options: { color: K.ink } }, { text: "TradeEscrow", options: { color: K.teal } }], { x: 0.65, y: 6.1, w: 7.6, h: 0.75, fontSize: 40, bold: true, fontFace: SERIF, valign: "middle", objectName: "!!title" });
  L(s, pres, 8.35, 5.88, 8.35, 6.83, "6B6459", 0.75);
  T(s, "Does conditional escrow make cross-border trade settlement safer and more auditable — and what does it cost?", { x: 8.6, y: 5.84, w: 4.1, h: 0.72, fontSize: 12.5, italic: true, color: K.ink2, fontFace: SERIF });
  T(s, "FINAL PRESENTATION  ·  WORKING PROTOTYPE, SYNTHETIC DATA", { x: 8.6, y: 6.6, w: 4.3, h: 0.22, fontSize: 8, bold: true, color: K.teal, charSpacing: 1.2 });
  L(s, pres, 0.65, 6.95, W - 0.65, 6.95, "B8AFA2", 0.75);
  T(s, "Tang Yu Hin (Alex)   ·   Chow Ka Shing (Marcus)   ·   Wong Ho Ming (Michael)   ·   So Lai Chun (Jeff)", { x: 0.65, y: 7.02, w: 9, h: 0.3, fontSize: 11, color: K.sub, valign: "middle" });
  T(s, "FTEC3002 GROUP 1  ·  2026", { x: W - 0.65 - 3.5, y: 7.02, w: 3.5, h: 0.3, fontSize: 9.5, bold: true, color: "6B6459", align: "right", valign: "middle", charSpacing: 2 });
  s.addNotes("(20 s) Title. At the interim we showed that the prototype runs. Today we answer the research question: does conditional escrow make HK–Thailand settlement safer and more auditable, and what does it cost? Four parts: why escrow, the design principles, the evidence, and our verdict.");

  // ═══ PART 1 — WHY ESCROW ═══
  // 2 Since the interim
  s = page(pres, { part: 0, title: "Since the interim: from “it runs” to “does it answer the question?”", sub: "What we added after the interim snapshot — and what an independent review made us fix" });
  const tlx0 = MX + 0.3, tlx1 = W - MX - 0.3, ty = 2.55;
  L(s, pres, tlx0, ty, tlx1, ty, K.ink2, 1.5, { name: "timeline" });
  [["7 Nov", "Interim snapshot", "prototype runs; 47 tests; 3 scenarios", K.mute, 0.0], ["8 Nov", "Independent review", "found a UI data-access bypass → fixed", K.red, 0.3],
   ["For the final report", "Evaluation built", "hypotheses H1–H5, fair-scope comparison, financing model", K.teal, 0.62], ["Today", "Final answer", "verdict on each hypothesis", K.gold, 1.0]].forEach(([d, t, b, col, f], i) => {
    const x = tlx0 + (tlx1 - tlx0) * f;
    R(s, pres, x - 0.11, ty - 0.11, 0.22, 0.22, { oval: true, fill: col, line: K.paper, lw: 2, name: "tl" + i });
    const ax = Math.min(Math.max(x - 1.2, MX), W - MX - 2.4);
    T(s, d, { x: ax, y: ty - 0.62, w: 2.4, h: 0.26, fontSize: 10, bold: true, italic: true, color: col, fontFace: SERIF, align: f === 0 ? "left" : f === 1 ? "right" : "center" });
    T(s, t, { x: ax, y: ty + 0.2, w: 2.4, h: 0.3, fontSize: 13, bold: true, color: K.ink, fontFace: SERIF, align: f === 0 ? "left" : f === 1 ? "right" : "center" });
    T(s, b, { x: ax, y: ty + 0.5, w: 2.4, h: 0.45, fontSize: 9.5, color: K.sub, align: f === 0 ? "left" : f === 1 ? "right" : "center" });
  });
  const deltas = [["TestTube", "Tests", "47", md("M-01"), "+30 access-control tests per role", K.teal],
    ["ShieldAlert", "UI data leak", "open", "fixed", "ledger page now role-projected", K.red],
    ["Scale", "Efficiency claim", "−57%", `−${mv("M-32")}%`, "honest matched-scope comparison", K.gold],
    ["Hourglass", "Financing cost", "unmeasured", "measured", "who waits, and how long", K.violet],
    ["ArrowRightLeft", "Interbank leg", "none", `${md("M-12")}`, "conceptual e-HKD two-leg commit", K.blue]];
  const dw = (W - 2 * MX - 0.8) / 5;
  for (let i = 0; i < 5; i++) {
    const [ic, t, a, b, n, col] = deltas[i], x = MX + i * (dw + 0.2), y = 3.75;
    R(s, pres, x, y, dw, 2.75, { fill: K.card, line: K.rule, name: "d" + i });
    L(s, pres, x, y, x + dw, y, col, 3);
    await I(s, ic, col, x + 0.2, y + 0.25, 0.38);
    T(s, t, { x: x + 0.68, y: y + 0.25, w: dw - 0.8, h: 0.38, fontSize: 13, bold: true, color: K.ink, fontFace: SERIF, valign: "middle" });
    T(s, a, { x: x + 0.2, y: y + 0.85, w: dw - 0.4, h: 0.3, fontSize: 13, color: K.mute, strike: "sngStrike" });
    T(s, "→ " + b, { x: x + 0.2, y: y + 1.15, w: dw - 0.4, h: 0.55, fontSize: b.length > 6 ? 19 : 24, bold: true, color: col, fontFace: SERIF, valign: "middle" });
    T(s, n, { x: x + 0.2, y: y + 1.85, w: dw - 0.4, h: 0.7, fontSize: 10.5, italic: true, color: K.sub, fontFace: SERIF });
  }
  s.addNotes("(40 s) At the interim we showed the prototype running. Since then we did three things. First, an independent review found a real flaw: the ledger page showed every account to every role, even though all 47 tests passed. We fixed it and added 30 tests. Second, we built a proper evaluation: five hypotheses and a fair comparison. That cut our own efficiency claim from 57% to 28.6%. Third, we measured the cost we had ignored: who has to fund the escrow.");

  // 3 Three ways to settle
  s = page(pres, { part: 0, title: "Three ways to settle the same HKD 250,000 shipment", sub: "Every settlement method is a choice about who carries the risk — and who pays to remove it", tag: "QUAL" });
  const cols = [["Open account", "today's baseline", K.blue, "ship_small", 380 / 900],
    ["Documentary credit (L/C)", "the traditional safe option", K.violet, "sheet_wide", 600 / 940],
    ["Pre-funded escrow", "this project", K.teal, "vault_closed", 760 / 900]];
  const rowsQ = [["Exporter paid", ["after the credit term", "on complying documents", "automatically, when 3 gates pass"]],
    ["Non-payment risk", ["exporter (unsecured)", "issuing bank", "largely removed — funds locked"]],
    ["Who funds the trade", ["exporter extends credit", "importer's bank credit line", "importer pre-funds in cash"]],
    ["Document checking", ["importer, by hand", "banks, by hand (UCP 600)", "machine match + human review"]],
    ["Audit trail", ["fragmented", "bank records, paper", "shared hash-chained journal"]]];
  const risk = [[K.red, K.gold, K.teal], [K.red, K.teal, K.teal], [K.gold, K.gold, K.red], [K.red, K.gold, K.teal], [K.red, K.gold, K.teal]];
  const lw0 = 2.1, cw3 = (W - 2 * MX - lw0) / 3, hy = 1.9;
  for (let c = 0; c < 3; c++) {
    const [t, sub, col, im, ratio] = cols[c], x = MX + lw0 + c * cw3;
    if (c === 2) R(s, pres, x + 0.05, hy - 0.08, cw3 - 0.1, 4.2, { fill: K.tealL, tr: 55, line: K.teal, lw: 1, name: "hl" });
    const iw = im === "vault_closed" ? 0.75 : im === "sheet_wide" ? 0.95 : 1.15;
    img(s, im, x + 0.2, hy + 0.02, iw, ratio);
    T(s, t, { x: x + iw + 0.3, y: hy + 0.0, w: cw3 - iw - 0.4, h: 0.5, fontSize: 13, bold: true, color: col, fontFace: SERIF, valign: "bottom" });
    T(s, sub, { x: x + iw + 0.3, y: hy + 0.52, w: cw3 - iw - 0.4, h: 0.24, fontSize: 9.5, italic: true, color: K.mute, fontFace: SERIF });
  }
  rowsQ.forEach(([lb, vals], r) => {
    const y = 2.85 + r * 0.66;
    L(s, pres, MX, y - 0.06, W - MX, y - 0.06, K.rule, 0.5, { dash: "dash" });
    T(s, lb, { x: MX, y, w: lw0 - 0.1, h: 0.5, fontSize: 11.5, bold: true, color: K.ink2, valign: "middle" });
    vals.forEach((v, c) => {
      const x = MX + lw0 + c * cw3;
      R(s, pres, x + 0.22, y + 0.18, 0.14, 0.14, { oval: true, fill: risk[r][c], line: null });
      T(s, v, { x: x + 0.48, y, w: cw3 - 0.6, h: 0.5, fontSize: 11.5, color: K.ink, fontFace: SERIF, valign: "middle" });
    });
  });
  [["good for the exporter / system", K.teal], ["mixed", K.gold], ["weak point", K.red]].forEach(([t, c], i) => {
    R(s, pres, MX + i * 2.6, 6.28, 0.13, 0.13, { oval: true, fill: c, line: null }); T(s, t, { x: MX + i * 2.6 + 0.22, y: 6.22, w: 2.3, h: 0.25, fontSize: 9.5, italic: true, color: K.sub, fontFace: SERIF });
  });
  T(s, "Escrow buys an L/C-like guarantee without bank credit — paid for in importer cash.", { x: MX + 6.6, y: 6.2, w: W - 2 * MX - 6.6, h: 0.32, fontSize: 11, bold: true, italic: true, color: K.teal, fontFace: SERIF, align: "right" });
  s.addNotes("(45 s) The interim compared escrow only with open account. That is an unfair comparison: banks already sell a safe product, the letter of credit. Read the rows: escrow gives the exporter L/C-like certainty, replaces manual document examination with machine matching plus human review, and leaves one shared audit trail. But look at the red dot: the importer must fund in cash up front. That trade-off is what Part 4 measures.");

  // 4 The missing layer
  s = page(pres, { part: 0, title: "Hong Kong is building the rails — but not the conditions", sub: "Each programme solves one layer; none holds money against trade conditions", tag: "FACT" });
  const layers = [["Data", "Project CargoX", "cargo & trade data for credit decisions; pilot with 21 banks (May 2026)", K.mute, "Database", URL.cargoxPilot],
    ["★ Conditional settlement", "our prototype", "hold funds against shipment, documents and compliance; route exceptions to people; regulator view", K.teal, "LockKeyhole", null],
    ["Money", "Ensemble / e-HKD", "tokenised deposits; e-HKD Phase 2 pilots (mainly retail use cases)", K.mute, "Coins", URL.ehkd],
    ["Interbank rails", "EnsembleTX · mBridge", "24/7 settlement in tokenised central-bank money (Nov 2026); multi-CBDC cross-border", K.mute, "ArrowRightLeft", URL.ensembleTX]];
  const lx0 = MX + 0.3, lwid = 7.6;
  for (let i = 0; i < layers.length; i++) {
    const [nm, who, what, col, ic, u] = layers[i];
    const y = 1.95 + i * 1.08, mine = col === K.teal, off = (3 - i) * 0.12;
    R(s, pres, lx0 + off, y, lwid - 2 * off, 0.88, { fill: mine ? K.tealL : K.card, line: mine ? K.teal : K.rule, lw: mine ? 1.75 : 0.75, dash: mine ? "dash" : undefined, name: "layer" + i });
    await I(s, ic, mine ? K.teal : K.ink2, lx0 + off + 0.22, y + 0.24, 0.4);
    T(s, nm, { x: lx0 + off + 0.8, y: y + 0.1, w: 2.6, h: 0.34, fontSize: 14, bold: true, color: mine ? K.teal : K.ink, fontFace: SERIF });
    T(s, who, { x: lx0 + off + 0.8, y: y + 0.46, w: 2.6, h: 0.3, fontSize: 10.5, italic: true, color: K.mute, fontFace: SERIF, hyperlink: u ? { url: u } : undefined });
    T(s, what, { x: lx0 + off + 3.4, y: y + 0.08, w: lwid - 2 * off - 3.6, h: 0.72, fontSize: 10.5, color: K.sub, valign: "middle" });
  }
  const gx = MX + 8.4, gw2 = W - MX - gx;
  T(s, "THE GAP WE TARGET", { x: gx, y: 1.95, w: gw2, h: 0.26, fontSize: 10, bold: true, color: K.teal, charSpacing: 2 });
  ["holds funds against shipment, document and compliance conditions", "routes discrepancies and alerts to an accountable human", "gives the regulator a privacy-limited reconstruction"].forEach((t, i) => {
    T(s, ["i.", "ii.", "iii."][i], { x: gx, y: 2.35 + i * 0.9, w: 0.45, h: 0.35, fontSize: 15, bold: true, italic: true, color: K.teal, fontFace: SERIF });
    T(s, t, { x: gx + 0.5, y: 2.35 + i * 0.9, w: gw2 - 0.5, h: 0.8, fontSize: 12.5, color: K.ink, fontFace: SERIF });
  });
  R(s, pres, gx, 5.15, gw2, 1.2, { fill: K.goldL, tr: 30, line: null });
  L(s, pres, gx, 5.15, gx, 6.35, K.gold, 3);
  T(s, "None of the public programmes describes this layer. EnsembleTX (2 Nov 2026) is the rail it could sit on — we are not connected to it.", { x: gx + 0.2, y: 5.2, w: gw2 - 0.3, h: 1.1, fontSize: 10.5, italic: true, color: K.ink2, fontFace: SERIF, valign: "middle" });
  srcline(s, "HKMA press releases and reports, dated as shown; BIS Project mBridge. Click a programme name to open its source.");
  s.addNotes("(40 s) Why build this at all, if HKMA is already tokenising money? Because the programmes solve different layers: data (CargoX), money (Ensemble, e-HKD), and interbank rails (EnsembleTX, mBridge). None of them, as publicly described, holds funds against trade conditions and routes exceptions to people. That missing middle layer is what we prototyped.");

  // 5 Research question + hypotheses
  s = page(pres, { part: 0, title: "One question, five falsifiable hypotheses", sub: "We wrote down what would prove us wrong before looking at the results" });
  R(s, pres, MX, 1.85, W - 2 * MX, 1.05, { fill: K.card, line: K.rule, name: "rq" });
  T(s, "“", { x: MX + 0.15, y: 1.72, w: 0.6, h: 0.8, fontSize: 54, bold: true, color: K.teal, fontFace: SERIF });
  T(s, "Can a pre-funded escrow of simulated tokenised deposits make HK–TH trade settlement more efficient, transparent and auditable — while preserving compliance controls?",
    { x: MX + 0.75, y: 1.9, w: W - 2 * MX - 1.0, h: 0.95, fontSize: 15.5, italic: true, color: K.ink, fontFace: SERIF, valign: "middle" });
  const hyp = [["H1", "Efficiency", "fewer manual tasks and shorter post-shipment latency, under the same assumptions", "BPMN task inventory · timeline model", "Gauge"],
    ["H2", "Safe release", "no release unless every gate is current", `17 unsafe attempts · ${Number(D.METRICS["M-09"].denominator).toLocaleString("en")} random checks`, "LockKeyhole"],
    ["H3", "Safe exceptions", "mismatch → review, AML alert → freeze, never a silent release", "TC-002 · TC-003 · exception tests", "ShieldAlert"],
    ["H4", "Auditability", "reviewers can reconstruct events without unrelated commercial data", "role-visibility rules · regulator export", "ScrollText"],
    ["H5", "Honest cost", "pre-funding shifts liquidity burden — and this must be measured", "who-waits timeline per model", "Scale"]];
  const hw = (W - 2 * MX - 0.8) / 5;
  for (let i = 0; i < 5; i++) {
    const [id, t, claim, test, ic] = hyp[i], x = MX + i * (hw + 0.2), y = 3.15;
    R(s, pres, x, y, hw, 3.35, { fill: K.card, line: K.rule, name: "!!h" + i });
    T(s, id, { x: x + 0.2, y: y + 0.15, w: 0.8, h: 0.5, fontSize: 24, bold: true, italic: true, color: K.teal, fontFace: SERIF, objectName: "!!hid" + i });
    await I(s, ic, K.ink2, x + hw - 0.6, y + 0.22, 0.38);
    T(s, t, { x: x + 0.2, y: y + 0.7, w: hw - 0.4, h: 0.32, fontSize: 13.5, bold: true, color: K.ink, fontFace: SERIF, objectName: "!!ht" + i });
    T(s, claim, { x: x + 0.2, y: y + 1.05, w: hw - 0.4, h: 1.2, fontSize: 10.5, color: K.sub });
    L(s, pres, x + 0.2, y + 2.35, x + hw - 0.2, y + 2.35, K.rule, 0.5, { dash: "dash" });
    T(s, "tested by", { x: x + 0.2, y: y + 2.42, w: hw - 0.4, h: 0.22, fontSize: 8.5, italic: true, color: K.mute, fontFace: SERIF });
    T(s, test, { x: x + 0.2, y: y + 2.64, w: hw - 0.4, h: 0.6, fontSize: 9.5, bold: true, color: K.teal });
  }
  s.addNotes("(35 s) Our research question splits into five hypotheses, each with a test that could fail. H1 efficiency, H2 no unsafe release, H3 exceptions go to people, H4 auditability without over-sharing, and H5 — the uncomfortable one — the cost of pre-funding must be measured, not ignored. Part 3 tests them; Part 4 gives the verdicts.");

  // ═══ PART 2 — THE DESIGN ═══
  // 6 Oracle problem
  s = page(pres, { part: 1, title: "A smart contract cannot see a ship", sub: "The oracle problem: the code can only check what someone accountable tells it — so we drew the boundary explicitly" });
  const bx = 5.05;
  T(s, "THE REAL WORLD", { x: MX, y: 1.9, w: 4, h: 0.26, fontSize: 10, bold: true, color: K.gold, charSpacing: 2 });
  img(s, "ship_small", MX, 2.3, 2.3, 380 / 900);
  T(s, "goods loaded?  documents genuine?  buyer on a sanctions list?", { x: MX, y: 3.35, w: 4.1, h: 0.5, fontSize: 11.5, italic: true, color: K.ink2, fontFace: SERIF });
  R(s, pres, bx - 0.05, 1.85, 0.0, 4.75, { fill: null, line: null });
  L(s, pres, bx, 1.85, bx, 6.75, K.gold, 2, { dash: "dash", name: "boundary" });
  T(s, "TRUST BOUNDARY", { x: bx + 0.12, y: 6.5, w: 1.9, h: 0.24, fontSize: 9, bold: true, color: K.gold, align: "center", charSpacing: 2 });
  T(s, "THE ENGINE", { x: bx + 0.35, y: 1.9, w: 4, h: 0.26, fontSize: 10, bold: true, color: K.teal, charSpacing: 2 });
  const att = [["Truck", "Shipment attestation", "logistics provider", "shipment ID, on-board date"], ["FileCheck", "Document attestation", "Bank H operations", "field-by-field match, digest of each revision"], ["UserCheck", "KYC / AML attestation", "Bank H compliance", "PASS / FAIL, timestamp, expiry"]];
  for (let i = 0; i < 3; i++) {
    const [ic, t, who, carries] = att[i], y = 4.05 + i * 0.82;
    R(s, pres, MX, y, 4.1, 0.7, { fill: K.card, line: K.rule });
    await I(s, ic, K.gold, MX + 0.15, y + 0.17, 0.36);
    T(s, [{ text: t + "  ", options: { bold: true, color: K.ink } }, { text: "by " + who, options: { italic: true, color: K.mute } }], { x: MX + 0.62, y: y + 0.05, w: 3.4, h: 0.32, fontSize: 11, fontFace: SERIF });
    T(s, carries, { x: MX + 0.62, y: y + 0.36, w: 3.4, h: 0.28, fontSize: 9.5, color: K.sub });
    L(s, pres, MX + 4.12, y + 0.35, bx - 0.05, y + 0.35, K.gold, 1.25, { head: true });
  }
  const ex0 = bx + 0.35, ew = W - MX - ex0;
  T(s, "can VERIFY itself", { x: ex0, y: 2.3, w: ew / 2 - 0.1, h: 0.3, fontSize: 12, bold: true, italic: true, color: K.teal, fontFace: SERIF });
  T(s, "must TRUST", { x: ex0 + ew / 2 + 0.1, y: 2.3, w: ew / 2 - 0.1, h: 0.3, fontSize: 12, bold: true, italic: true, color: K.red, fontFace: SERIF });
  const ver = ["attestation is for THIS trade", "document revision is the latest", "screening is fresh (≤ 48 h)", "who issued it, and their role", "amounts add up; supply conserved"];
  const tru = ["the goods were really loaded", "documents are genuine", "the sanctions list was current", "attesters are not colluding"];
  ver.forEach((t, i) => T(s, [{ text: "✓  ", options: { color: K.teal, bold: true } }, { text: t, options: { color: K.ink } }], { x: ex0, y: 2.7 + i * 0.4, w: ew / 2 - 0.1, h: 0.36, fontSize: 11, fontFace: SERIF }));
  tru.forEach((t, i) => T(s, [{ text: "?  ", options: { color: K.red, bold: true } }, { text: t, options: { color: K.ink } }], { x: ex0 + ew / 2 + 0.1, y: 2.7 + i * 0.4, w: ew / 2 - 0.1, h: 0.36, fontSize: 11, fontFace: SERIF }));
  R(s, pres, ex0, 4.95, ew, 1.45, { fill: K.goldL, tr: 30, line: null, name: "!!panel" });
  L(s, pres, ex0, 4.95, ex0, 6.4, K.gold, 3);
  T(s, [{ text: "Design consequence. ", options: { bold: true, color: K.gold } }, { text: "Every attestation names an accountable issuer, a trade ID, a content digest and an expiry. The engine re-checks all of them at the moment of release — so a stale, swapped or revised fact cannot release money.", options: { color: K.ink2 } }],
    { x: ex0 + 0.2, y: 5.0, w: ew - 0.35, h: 1.35, fontSize: 11.5, fontFace: SERIF, valign: "middle" });
  s.addNotes("(45 s) The core design problem is the oracle problem: code cannot see a ship. So we made the trust boundary explicit. On the left, three accountable parties issue attestations. The engine can verify that an attestation is for this trade, is the latest revision, is fresh, and comes from the right role. It must trust that the goods were really loaded and the documents are genuine. That is why every attestation carries an issuer, a trade ID, a digest and an expiry — and why the engine re-checks them at the moment of release.");

  // 7 Each check closes a loophole
  s = page(pres, { part: 1, title: "Seven release checks — each one closes a specific loophole", sub: "Read across: the check, the attack it stops, and the test that tried that attack", tag: "TEST" });
  const chk = [["Shipment", "shipment attested for this trade's shipment ID", "use another trade's shipment evidence", "NC-17", "ESCROW_NOT_READY", K.teal],
    ["Documents", "documents PASS on the current revision (digest-pinned)", "get approval, then quietly revise the invoice", "NC-05", "DOCUMENTS_NOT_VERIFIED", K.teal],
    ["Compliance", "pre-release screening less than 48 h old", "rely on an old screening result", "NC-07", "PRE_RELEASE_KYC_EXPIRED", K.blue],
    ["Compliance", "screening newer than the last approval and hold", "clear a hold without re-screening", "NC-11", "PRE_RELEASE_KYC_MISSING", K.blue],
    ["Compliance", "no active compliance hold", "release after an analyst adds a manual hold", "NC-10", "ESCROW_FROZEN", K.blue],
    ["State", "escrow is Pending and holds the full amount", "release twice, or before shipment", "NC-12", "TERMINAL_STATE", K.gold],
    ["Role", "only the contract engine may move funds", "importer, exporter or regulator presses Release", "NC-14–16", "RBAC_DENIED", K.violet]];
  const cx = [MX, MX + 1.35, MX + 5.1, MX + 8.75, MX + 9.85], cwd = [1.25, 3.65, 3.55, 1.0, 2.1];
  ["GATE", "THE CHECK", "THE LOOPHOLE IT CLOSES", "TEST", "ENGINE SAYS"].forEach((h, i) => T(s, h, { x: cx[i], y: 1.88, w: cwd[i], h: 0.24, fontSize: 9, bold: true, color: K.mute, charSpacing: 1.5 }));
  L(s, pres, MX, 2.15, W - MX, 2.15, K.ink2, 1);
  chk.forEach(([g, c, lp, t, code, col], i) => {
    const y = 2.25 + i * 0.6;
    if (i % 2 === 0) R(s, pres, MX - 0.05, y - 0.04, W - 2 * MX + 0.1, 0.56, { fill: K.card, tr: 20, line: null });
    pill(s, pres, cx[0], y + 0.1, 1.1, g, col, K.paper, { h: 0.28, size: 8.5 });
    T(s, c, { x: cx[1], y, w: cwd[1], h: 0.48, fontSize: 11, color: K.ink, fontFace: SERIF, valign: "middle" });
    T(s, [{ text: "✗  ", options: { color: K.red, bold: true } }, { text: lp, options: { color: K.ink2, italic: true } }], { x: cx[2], y, w: cwd[2], h: 0.48, fontSize: 11, fontFace: SERIF, valign: "middle" });
    T(s, t, { x: cx[3], y, w: cwd[3], h: 0.48, fontSize: 10.5, bold: true, color: K.ink, valign: "middle" });
    T(s, code, { x: cx[4], y, w: cwd[4], h: 0.48, fontSize: 9, bold: true, color: K.teal, fontFace: MONO, valign: "middle" });
  });
  L(s, pres, MX, 6.5, W - MX, 6.5, K.ink2, 1);
  T(s, `All ${md("M-04")} attempts refused with funds unchanged; the positive control (all gates valid) released once.`, { x: MX, y: 6.55, w: W - 2 * MX, h: 0.3, fontSize: 10.5, italic: true, bold: true, color: K.teal, fontFace: SERIF });
  s.addNotes("(50 s) At the interim we listed the seven guard conditions. Here is why each exists. Each row is an attack someone could try, the check that stops it, and the named test that actually tried it. For example: get documents approved, then quietly revise the invoice — the approval is pinned to a digest, so the revision voids it (NC-05). Or clear a compliance hold without re-screening (NC-11). All seventeen attempts were refused and the money did not move.");

  // 8 Safety invariants
  s = page(pres, { part: 1, title: "Five properties that must hold after every single command", sub: "Not features — invariants. If any one breaks, the system is wrong, whatever the screen says" });
  const inv = [["Scale", "Conservation", "total token supply never changes; escrow balance = locked amount", "checked after every command", `0 / ${Number(D.METRICS["M-09"].denominator).toLocaleString("en")} violations`, K.teal],
    ["Repeat", "Exactly once", "a release or refund cannot happen twice, even if the command is re-sent", "idempotency keys + terminal states", "duplicate release refused", K.teal],
    ["Ban", "Default deny", "a state change not in the 15-move table is an error, not a choice", "transition table in code", "illegal moves raise & log", K.red],
    ["KeyRound", "Least privilege", "each role sees and does only its own part; regulator sees metadata", "server-side permissions + projections", `${md("M-08")} visibility rules`, K.violet],
    ["Link", "Tamper evidence", "every accepted and refused command is chained by SHA-256", "verifier recomputes the chain", "edits & deletions detected", K.gold]];
  const iw2 = (W - 2 * MX - 0.8) / 5;
  for (let i = 0; i < 5; i++) {
    const [ic, t, b, how, ev, col] = inv[i], x = MX + i * (iw2 + 0.2), y = 1.95;
    R(s, pres, x, y, iw2, 4.55, { fill: K.card, line: K.rule, name: "inv" + i });
    R(s, pres, x + iw2 / 2 - 0.45, y + 0.3, 0.9, 0.9, { oval: true, fill: K.paper, line: col, lw: 1.25 });
    await I(s, ic, col, x + iw2 / 2 - 0.24, y + 0.51, 0.48);
    T(s, t, { x: x + 0.15, y: y + 1.35, w: iw2 - 0.3, h: 0.4, fontSize: 15, bold: true, color: K.ink, fontFace: SERIF, align: "center" });
    T(s, b, { x: x + 0.2, y: y + 1.8, w: iw2 - 0.4, h: 1.15, fontSize: 10.5, color: K.sub, align: "center" });
    L(s, pres, x + 0.3, y + 3.0, x + iw2 - 0.3, y + 3.0, K.rule, 0.5, { dash: "dash" });
    T(s, how, { x: x + 0.15, y: y + 3.08, w: iw2 - 0.3, h: 0.5, fontSize: 9.5, italic: true, color: K.mute, fontFace: SERIF, align: "center" });
    T(s, ev, { x: x + 0.15, y: y + 3.65, w: iw2 - 0.3, h: 0.7, fontSize: 11.5, bold: true, color: col, align: "center", valign: "middle" });
  }
  s.addNotes("(40 s) Beyond the gates, we specified five invariants that must hold after every command, whatever happens: money is conserved, nothing executes twice, anything not explicitly allowed is refused, each role sees only its own data, and every command — accepted or refused — is chained so tampering is detectable. The bottom line of each card is how we checked it. The state diagram is in backup B2.");

  // ═══ PART 3 — THE EVIDENCE ═══
  // 9–12: Part 3 (presented by WONG HO MING) — see presentation/part3_upgraded.js
  await require("./part3_upgraded.js")({ pres, page, T, L, R, I, pill, img, K, SERIF, SANS, MONO, D, md, mv, W, H, MX, V });
  NUM = NUM; // page() keeps numbering
  s = null;

  // ═══ PART 4 — THE VERDICT ═══
  // 13 How big is the efficiency claim
  s = page(pres, { part: 3, title: "How big is the efficiency gain, really?", sub: "Our first figure flattered the escrow. A fair comparison halves the claim — the direction survives", tag: "MODEL" });
  const ax0 = MX + 2.4, ax1 = MX + 7.9, X = v => ax0 + (ax1 - ax0) * v / 10;
  for (let v = 0; v <= 10; v += 2) { L(s, pres, X(v), 2.25, X(v), 5.35, K.rule, 0.5, { dash: v ? "sysDot" : undefined }); T(s, String(v), { x: X(v) - 0.25, y: 5.4, w: 0.5, h: 0.22, fontSize: 9, italic: true, color: K.mute, fontFace: SERIF, align: "center" }); }
  T(s, "manual settlement tasks per trade", { x: ax1 - 3, y: 5.62, w: 3, h: 0.22, fontSize: 9, italic: true, color: K.mute, fontFace: SERIF, align: "right" });
  [["normal", "Normal trade"], ["mismatch", "Document mismatch"], ["aml", "AML alert"]].forEach(([k, lbl], i) => {
    const y = 2.65 + i * 1.0, b = cnt(k, "baseline"), p = cnt(k, "proposed"), e = cnt(k, "proposed_e2e");
    T(s, lbl, { x: MX, y: y - 0.2, w: 2.3, h: 0.4, fontSize: 12.5, bold: true, color: K.ink, fontFace: SERIF, valign: "middle" });
    s.addShape(pres.shapes.LINE, { x: X(p), y, w: X(b) - X(p), h: 0, line: { color: K.rule, width: 5 } });
    [[b, K.blue, true], [e, K.gold, false], [p, K.teal, true]].forEach(([v, col, solid]) => {
      R(s, pres, X(v) - 0.15, y - 0.15, 0.3, 0.3, { oval: true, fill: solid ? col : K.paper, line: col, lw: 2 });
      T(s, String(v), { x: X(v) - 0.25, y: y - 0.5, w: 0.5, h: 0.28, fontSize: 11, bold: true, color: col, align: "center", fontFace: SERIF });
    });
  });
  [["Open account", K.blue, true], ["Escrow, prototype scope", K.teal, true], ["Escrow + the steps to reach Bank O (matched scope)", K.gold, false]].forEach(([t, c, solid], i) => {
    const x = MX + [0, 1.75, 4.05][i]; R(s, pres, x, 5.98, 0.18, 0.18, { oval: true, fill: solid ? c : K.paper, line: c, lw: 1.5 }); T(s, t, { x: x + 0.26, y: 5.93, w: 3.6, h: 0.28, fontSize: 9.5, color: K.sub });
  });
  const fx = MX + 8.4, fw2 = W - MX - fx;
  T(s, "WHY THE FIRST NUMBER WAS UNFAIR", { x: fx, y: 1.95, w: fw2, h: 0.26, fontSize: 10, bold: true, color: K.gold, charSpacing: 1.5 });
  T(s, "The baseline ends when Bank O credits the exporter. Our prototype ends earlier — at a Bank H release. Adding the missing steps (redemption, cross-bank payment, Bank O credit, reconciliation) gives a like-for-like count.",
    { x: fx, y: 2.3, w: fw2, h: 1.7, fontSize: 11, color: K.ink2, fontFace: SERIF });
  [[`−${mv("M-15")}%`, "prototype scope", K.mute, true], [`−${mv("M-32")}%`, "matched scope — the claim we stand by", K.gold, false]].forEach(([b, t, col, strike], i) => {
    const y = 4.2 + i * 1.0;
    T(s, b, { x: fx, y, w: 1.9, h: 0.6, fontSize: 30, bold: true, color: col, fontFace: SERIF, valign: "middle", strike: strike ? "sngStrike" : undefined });
    T(s, t, { x: fx + 1.95, y, w: fw2 - 1.95, h: 0.6, fontSize: 11, italic: true, color: K.sub, fontFace: SERIF, valign: "middle" });
  });
  srcline(s, "BPMN task inventory (results/process_counts.csv); goods, customs, carriage and FX tasks excluded in all models. Full maps: backup B3–B4.");
  s.addNotes("(45 s) H1 in detail. Our first figure said escrow removes 57% of manual settlement tasks. That was unfair: the baseline ends when the Thai bank credits the exporter, but our prototype stops earlier, at Bank H. When we add the steps the escrow would still need to reach the Thai bank, the reduction is 7 to 5, about 29%. Smaller, but the direction holds in all three scenarios. That is the number we stand by — and it is still a model, not a measurement.");

  // 14 Who pays
  s = page(pres, { part: 3, title: "Faster release is paid for by earlier importer funding", sub: "Who waits, and for how long — normal trade, base assumptions, simulated days", tag: "TIMING" });
  const rows = [["Open account · pay at once", "baseline", "0"], ["Open account · 30-day term", "baseline", "30"], ["Escrow (prototype)", "proposed", "0"], ["Escrow + cross-bank leg (hyp.)", "proposed_e2e", "0"]];
  const g0 = MX + 2.6, g1 = 8.1, dmax = 45, Xd = d => g0 + (g1 - g0) * d / dmax;
  for (let d = 0; d <= dmax; d += 5) { L(s, pres, Xd(d), 2.1, Xd(d), 5.55, K.rule, 0.5, { dash: d ? "sysDot" : undefined }); T(s, String(d), { x: Xd(d) - 0.25, y: 5.6, w: 0.5, h: 0.22, fontSize: 9, color: K.mute, align: "center", italic: true, fontFace: SERIF }); }
  T(s, "days from contract", { x: g1 - 2, y: 5.83, w: 2, h: 0.22, fontSize: 9, italic: true, color: K.mute, fontFace: SERIF, align: "right" });
  rows.forEach(([lb, m, term], i) => {
    const r = TLr(m, term), y = 2.3 + i * 0.82, tf = +r.t_funded_d, ts = +r.t_shipment_d, tc = +r.t_credited_d, un = +r.exporter_unsecured_receivable_d;
    T(s, lb, { x: MX, y: y - 0.02, w: 2.5, h: 0.5, fontSize: 11.5, bold: true, color: i > 1 ? K.teal : K.blue, fontFace: SERIF, valign: "middle" });
    R(s, pres, Xd(tf), y + 0.03, Math.max(Xd(tc) - Xd(tf), 0.05), 0.18, { fill: K.teal, line: null });
    R(s, pres, Xd(ts), y + 0.25, Math.max(Xd(tc) - Xd(ts), 0.05), 0.18, un > 0 ? { fill: K.red, line: null } : { fill: K.paper, line: K.ink2, lw: 0.75, dash: "sysDash" });
    L(s, pres, Xd(ts), y - 0.06, Xd(ts), y + 0.52, K.ink, 1.5);
    R(s, pres, Xd(tc) - 0.07, y + 0.16, 0.14, 0.14, { oval: true, fill: K.gold, line: K.ink, lw: 0.75 });
    const txt = `importer ${+r.importer_funds_committed_d} d${un > 0 ? "  ·  exporter at risk " + un + " d" : ""}`;
    if (Xd(tc) + 2.4 < 8.3) T(s, txt, { x: Xd(tc) + 0.15, y: y + 0.02, w: 2.5, h: 0.42, fontSize: 10, italic: true, color: K.sub, fontFace: SERIF, valign: "middle" });
    else T(s, txt, { x: Xd(ts) + 0.1, y: y + 0.25, w: Xd(tc) - Xd(ts) - 0.2, h: 0.18, fontSize: 9, bold: true, color: K.paper, align: "right", valign: "middle" });
  });
  [["Importer cash committed", K.teal, null], ["Exporter unpaid & unsecured", K.red, null], ["Exporter waiting (escrow-secured)", K.paper, K.ink2]].forEach(([t, c, ln], i) => {
    const x = MX + i * 2.5; R(s, pres, x, 6.2, 0.32, 0.14, { fill: c, line: ln || null, dash: ln ? "sysDash" : undefined }); T(s, t, { x: x + 0.42, y: 6.13, w: 3.2, h: 0.28, fontSize: 9.5, color: K.sub });
  });
  const scx = 8.55, scw = 4.1;
  img(s, "scale", scx, 1.9, scw, 1200 / 1800);
  T(s, "importer's cash", { x: scx - 0.01, y: 3.72, w: 1.6, h: 0.28, fontSize: 10.5, italic: true, bold: true, color: K.teal, fontFace: SERIF, align: "center" });
  T(s, "exporter's goods & wait", { x: scx + 2.36, y: 3.33, w: 1.9, h: 0.28, fontSize: 10.5, italic: true, bold: true, color: K.gold, fontFace: SERIF, align: "center" });
  T(s, "Escrow does not remove financing cost — it moves it from the exporter to the importer.", { x: scx - 0.15, y: 4.75, w: scw + 0.3, h: 0.85, fontSize: 13.5, bold: true, italic: true, color: K.ink, fontFace: SERIF, align: "center" });
  T(s, `Shipment → release: ${TLr("baseline").post_shipment_latency_d} → ${TLr("proposed").post_shipment_latency_d} simulated days`, { x: scx - 0.1, y: 5.75, w: scw + 0.2, h: 0.3, fontSize: 11, color: K.teal, bold: true, align: "center" });
  s.addNotes("(45 s) H5 in detail. Each row is a timeline from contract. Red is the exporter shipped but unpaid and unsecured; teal is the importer's cash committed. Under open account with a 30-day term, the exporter is exposed for 37 days. Under escrow, the exporter's risk drops to zero — but the importer's cash is locked for 7.5 days instead of 2.5. So escrow is not free efficiency; it is a risk transfer. A real product would need a bank to finance or pay interest on the escrow balance.");

  // 15 What must be true
  s = page(pres, { part: 3, title: "What would have to be true for this to work for real", sub: "Each simplification we made is a question a bank, a regulator or a lawyer would have to answer" });
  const mt = [["Eye", "Attestations are honest", "a false bill of lading would pass our gates", "signed e-B/L or CargoX-type trade data, with liability", K.red],
    ["Landmark", "Settlement is final across borders", "Bank O only observes a HKD claim on Bank H", "an interbank leg in tokenised central-bank money (e.g. EnsembleTX)", K.blue],
    ["Gavel", "Tokenised escrow is legally sound", "ownership, segregation and insolvency not modelled", "legal opinion in both jurisdictions", K.violet],
    ["Coins", "Someone finances the wait", "importer locks cash for 7.5 days", "bank finances or remunerates the escrow balance", K.gold],
    ["Network", "Shared ledger beats a shared database", "one Bank H database could run the same rules", "only true with independent bank and regulator nodes", K.teal]];
  const m0 = [MX, MX + 4.0, MX + 7.75], m0w = [3.85, 3.3, 4.2];
  ["WHAT MUST BE TRUE", "IN OUR PROTOTYPE", "WHAT COULD MAKE IT TRUE"].forEach((h, i) => T(s, h, { x: m0[i] + (i ? 0 : 0.55), y: 1.88, w: m0w[i], h: 0.24, fontSize: 9, bold: true, color: K.mute, charSpacing: 1.5 }));
  L(s, pres, MX, 2.15, W - MX, 2.15, K.ink2, 1);
  for (let i = 0; i < 5; i++) {
    const [ic, a, b, c, col] = mt[i], y = 2.27 + i * 0.83;
    await I(s, ic, col, MX, y + 0.13, 0.38);
    T(s, a, { x: MX + 0.55, y, w: m0w[0] - 0.6, h: 0.65, fontSize: 13, bold: true, color: K.ink, fontFace: SERIF, valign: "middle" });
    T(s, b, { x: m0[1], y, w: m0w[1], h: 0.65, fontSize: 10.5, italic: true, color: K.red, fontFace: SERIF, valign: "middle" });
    L(s, pres, m0[2] - 0.32, y + 0.33, m0[2] - 0.08, y + 0.33, K.mute, 1, { head: true });
    T(s, c, { x: m0[2], y, w: m0w[2], h: 0.65, fontSize: 10.5, color: K.teal, bold: true, valign: "middle" });
    L(s, pres, MX, y + 0.75, W - MX, y + 0.75, K.rule, 0.5, { dash: "dash" });
  }
  srcline(s, "HKMA press releases: EnsembleTX (2 Nov 2026), CargoX pilot (7 May 2026).", [{ text: "EnsembleTX", url: URL.ensembleTX }, { text: "CargoX", url: URL.cargoxPilot }]);
  s.addNotes("(45 s) Instead of a list of limitations, here is what would have to be true for this to work in the real world. Attestations must be honest — that needs signed electronic bills of lading or CargoX-type data. Settlement must be final across the border — that needs an interbank leg such as EnsembleTX. The legal status of tokenised escrow needs an opinion in both jurisdictions. Someone has to finance the wait. And honestly: a single database could run our rules; a shared ledger only adds value with independent bank and regulator nodes.");

  // 16 Close
  s = page(pres, { part: 3, title: "Our answer: a qualified yes", sub: "Within a synthetic simulation — and with the conditions stated" });
  const ans = [["CircleCheck", "Safer & auditable", "Every release, review and freeze rule held; every action is reconstructable — and the regulator sees only metadata.", "H2 · H3 · H4", K.teal],
    ["Gauge", "Modestly more efficient", `About ${mv("M-32")}% fewer manual settlement tasks at matched scope — a model, not a measurement.`, "H1", K.gold],
    ["Scale", "Not free", "It moves financing cost from exporter to importer. Real value depends on trusted data, finality and law.", "H5", K.red]];
  for (let i = 0; i < 3; i++) {
    const [ic, t, b, h, col] = ans[i], aw = (W - 2 * MX - 0.5) / 3, x = MX + i * (aw + 0.25), y = 1.95;
    R(s, pres, x, y, aw, 3.2, { fill: K.card, line: K.rule, name: "ans" + i });
    L(s, pres, x, y, x + aw, y, col, 3);
    await I(s, ic, col, x + 0.3, y + 0.35, 0.55);
    T(s, h, { x: x + aw - 1.6, y: y + 0.4, w: 1.3, h: 0.3, fontSize: 11, bold: true, italic: true, color: col, fontFace: SERIF, align: "right" });
    T(s, t, { x: x + 0.3, y: y + 1.05, w: aw - 0.6, h: 0.45, fontSize: 17, bold: true, color: K.ink, fontFace: SERIF });
    T(s, b, { x: x + 0.3, y: y + 1.65, w: aw - 0.6, h: 1.4, fontSize: 12, color: K.sub, fontFace: SERIF });
  }
  T(s, "Next: connect the shipment gate to signed trade data · add an interbank leg · replace our assumptions with practitioner timings.", { x: MX, y: 5.45, w: W - 2 * MX, h: 0.4, fontSize: 12.5, italic: true, color: K.ink2, fontFace: SERIF, align: "center" });
  T(s, "Thank you — questions?", { x: MX, y: 5.95, w: W - 2 * MX, h: 0.6, fontSize: 26, bold: true, color: K.teal, fontFace: SERIF, align: "center", valign: "middle" });
  s.addNotes("(30 s) Our answer is a qualified yes. Safer and auditable: supported. More efficient: somewhat, about 29% fewer manual tasks, as a model. Not free: it moves the financing cost to the importer, and its real-world value depends on trusted data, settlement finality and law. Next steps are on the slide. Thank you — questions. Backups B1–B9 hold the full diagrams, permissions, the e-HKD leg and sources.");

  // ═══ BACKUPS ═══
  pres.addSection({ title: "Backup" });
  s = page(pres, { kicker: "APPENDIX", title: "Backup slides", section: "Backup" });
  ["Full architecture", "Escrow state machine", "Baseline BPMN", "Proposed BPMN", "Who may do what", "Demo fallback: real screenshots", "e-HKD two-leg cases", "Sources", "Likely questions"].forEach((t, i) => {
    const col = i < 5 ? 0 : 1, row = i % 5, x = MX + col * 6.0, y = 2.0 + row * 0.82;
    T(s, `B${i + 1}`, { x, y, w: 0.8, h: 0.5, fontSize: 22, bold: true, italic: true, color: K.teal, fontFace: SERIF, valign: "middle" });
    T(s, t, { x: x + 0.85, y, w: 4.8, h: 0.5, fontSize: 16, color: K.ink, fontFace: SERIF, valign: "middle" });
    L(s, pres, x + 0.85, y + 0.6, x + 5.5, y + 0.6, K.rule, 0.5, { dash: "dash" });
  });
  const dia = [
    ["B1", "Full architecture and trust boundaries", "report/figs/architecture.png",
      ["Top row: the 7 business roles. Each acts through the same UI; the role is picked in a selector, permissions are checked by the server.",
       "Orange box: facts from outside (shipment, documents, KYC/AML). They arrive as attestations — the engine cannot observe them.",
       "Green box: the engine. It authorises each command, runs the state machine and writes every command to a hash-chained journal.",
       "Right: outputs — token accounts, the SQLite ledger and role-limited views. Red box: what is NOT connected."],
      [["Is this a blockchain?", "No. It is a single permissioned service with a hash-chained log — tamper-evident, not distributed. We say so on slide 15."],
       ["Why is Bank H in the middle?", "Bank H holds the escrow account and operates the engine; Bank O only observes. A real version needs an interbank leg."]]],
    ["B2", "Escrow state machine — six states, fifteen legal moves", "diagrams/team/state_machine_team.jpg",
      ["Happy path: Created → Pending (shipment attested) → Released (green: only through the release guard).",
       "Dashed red: exceptions. A document failure sends a trade to Under Review; an AML alert sends it to Frozen — from any open state.",
       "Exits from exceptions need a named human: a reviewer revalidates, or compliance clears (then re-screens), or either terminates and refunds.",
       "Double border = terminal. Released and Refunded accept no further command (TERMINAL_STATE). Any move not drawn is rejected and logged."],
      [["Can Frozen go straight to Released?", "No. Compliance can only clear it back to Pending; release then needs a fresh pre-release screening (tested: NC-11)."],
       ["Why can Under Review go back to Created?", "If documents are fixed before the goods have shipped, there is no shipment attestation yet, so the trade returns to Created."]]],
    ["B3", "Baseline BPMN: open-account settlement", "diagrams/slide/baseline_bpmn_slide.png",
      ["Swimlanes = parties: importer, Bank H, Bank O, exporter, logistics/customs. Read left → right.",
       "Part 1: contract → exporter ships → documents couriered and checked by hand. Part 2: after the payment term the importer instructs payment; banks screen and pay.",
       "Orange boxes = manual settlement tasks; these are what we count (7 in a normal trade).",
       "Dashed red = exception paths (document discrepancy, screening alert)."],
      [["How did you count manual tasks?", "Orange tasks only, same granularity in both maps; goods, customs, carriage and FX tasks are excluded from both."],
       ["Is this how every bank works?", "No — it is a standard-practice model we drew. Another analyst could draw it differently (threat to validity in the report)."]]],
    ["B4", "Proposed BPMN: pre-funded escrow", "diagrams/slide/proposed_bpmn_slide.png",
      ["Part 1: importer funds the escrow and passes creation KYC/AML before shipment — the money is locked first.",
       "Part 2: attestations arrive; teal boxes are automated checks (document matching, pre-release screening, guarded release).",
       "Only 3 manual settlement tasks remain in a normal trade: importer creates & funds the escrow, exporter uploads invoice & B/L, Bank O acknowledges.",
       "Exceptions still go to people: a mismatch to a reviewer, an alert to compliance."],
      [["Why does this map end at Bank H?", "Our prototype stops at a Bank H release. That is why slide 13 adds the missing cross-bank steps (7 → 5) for a fair comparison."],
       ["Are the automated steps really free?", "No — we assume 0 days for them, which is optimistic. The time results are scenario analysis, not measurement."]]]];
  for (const [b, t, p, how, qa] of dia) {
    s = page(pres, { kicker: `BACKUP  ·  ${b}`, title: t, section: "Backup" });
    const dw2 = 8.25, px = MX + dw2 + 0.25, pw = W - MX - px;
    R(s, pres, MX, 1.8, dw2, 4.95, { fill: "FFFFFF", line: K.rule });
    D.fit(s, p, MX + 0.1, 1.9, dw2 - 0.2, 4.75, { alt: t });
    T(s, "HOW TO READ IT", { x: px, y: 1.8, w: pw, h: 0.24, fontSize: 9, bold: true, color: K.teal, charSpacing: 2 });
    how.forEach((h, k) => T(s, [{ text: `${k + 1}  `, options: { bold: true, italic: true, color: K.teal, fontFace: SERIF } }, { text: h, options: { color: K.ink2 } }],
      { x: px, y: 2.08 + k * 0.62, w: pw, h: 0.6, fontSize: 9.2 }));
    L(s, pres, px, 4.6, px + pw, 4.6, K.rule, 0.5, { dash: "dash" });
    T(s, "IF ASKED", { x: px, y: 4.68, w: pw, h: 0.24, fontSize: 9, bold: true, color: K.gold, charSpacing: 2 });
    qa.forEach(([q, a], k) => T(s, [{ text: q + "  ", options: { bold: true, color: K.ink, fontFace: SERIF } }, { text: a, options: { color: K.sub } }],
      { x: px, y: 4.95 + k * 0.9, w: pw, h: 0.88, fontSize: 9.2 }));
  }
  s = page(pres, { kicker: "BACKUP  ·  B5", title: "Who may do what — enforced inside the engine", section: "Backup" });
  const th = t => ({ text: t, options: { bold: true, color: K.paper, fill: { color: K.ink2 }, fontSize: 11, charSpacing: 1 } });
  const rl = [["HK importer", "create & fund escrow; upload contract; dispute", "release; compliance decisions; other trades"], ["Thai exporter", "submit invoice / bill of lading; dispute", "clear AML hold; screening; release"],
    ["Bank H operations", "document check; resolve review; trigger release", "terminate during an AML hold"], ["Bank H compliance", "screening; raise / clear / confirm holds", "release directly after clearance"],
    ["Thai Bank O", "acknowledge receipt (observation)", "any fund movement"], ["Logistics / customs", "shipment attestation / customs declaration", "another trade's shipment"], ["Regulator", "metadata-only audit export", "every state-changing command"]];
  s.addTable([[th("ROLE"), th("✓  MAY ISSUE"), th("✗  REFUSED (TESTED)")], ...rl.map((r, k) => r.map((c, j) => ({ text: c, options: { bold: j === 0, color: j === 2 ? K.red : K.ink, fill: { color: k % 2 ? K.card : K.paper }, fontFace: j === 0 ? SERIF : SANS } })))],
    { x: MX, y: 1.8, w: W - 2 * MX, colW: [2.6, 5.0, 4.33], fontSize: 12.5, fontFace: SANS, rowH: 0.58, margin: [0.04, 0.14, 0.04, 0.14], valign: "middle", border: { type: "solid", color: K.rule, pt: 0.75 }, autoPage: false });
  s = page(pres, { kicker: "BACKUP  ·  B6", title: "Demo fallback: the three scenarios in the real console", section: "Backup", tag: "DEMO" });
  [["TC-001 · released once", "S_TC001_panel"], ["TC-002 · Under Review", "S_TC002_panel"], ["TC-003 · Frozen", "S_TC003_panel"]].forEach(([t, k], i) => {
    const w3 = (W - 2 * MX - 0.4) / 3, x = MX + i * (w3 + 0.2);
    T(s, t, { x, y: 1.85, w: w3, h: 0.3, fontSize: 12, bold: true, italic: true, color: K.ink, fontFace: SERIF });
    R(s, pres, x, 2.2, w3, 4.45, { fill: "FFFFFF", line: K.rule });
    D.fit(s, `presentation/assets/${k}.jpg`, x + 0.05, 2.25, w3 - 0.1, 4.35, { valign: "top", alt: t });
  });
  s = page(pres, { kicker: "BACKUP  ·  B7", title: "Conceptual e-HKD leg: both legs commit, or neither", section: "Backup", tag: "TEST" });
  s.addTable([[th("CASE"), th("OUTCOME"), th("ALL-OR-NOTHING")], ...eh.map((e, k) => [
      { text: e.description, options: { color: K.ink, fill: { color: k % 2 ? K.card : K.paper }, fontFace: SERIF } },
      { text: e.outcome, options: { bold: true, color: e.outcome.startsWith("COMMIT") ? K.teal : K.blue, fill: { color: k % 2 ? K.card : K.paper }, fontFace: MONO } },
      { text: e.all_or_nothing_ok === "True" ? "✓  yes" : "✗  NO", options: { bold: true, color: e.all_or_nothing_ok === "True" ? K.teal : K.red, fill: { color: k % 2 ? K.card : K.paper } } }])],
    { x: MX, y: 1.8, w: W - 2 * MX, colW: [7.2, 2.9, 1.83], fontSize: 12.5, fontFace: SANS, rowH: 0.62, margin: [0.04, 0.14, 0.04, 0.14], valign: "middle", border: { type: "solid", color: K.rule, pt: 0.75 }, autoPage: false });
  T(s, "A toy two-phase commit across two mock ledgers: not distributed, not legally final, not HKMA-linked.", { x: MX, y: 5.9, w: W - 2 * MX, h: 0.4, fontSize: 12, italic: true, color: K.mute, fontFace: SERIF });
  s = page(pres, { kicker: "BACKUP  ·  B8", title: "Sources (click to open)", section: "Backup", tag: "FACT" });
  [["EXIM Thailand", "HK 13th-largest partner, US$13.7bn (2023) · 23 Feb 2024", URL.exim], ["ADB", "Global trade-finance gap US$2.5tn in 2025 · 15 Jan 2026", URL.adb],
   ["HKMA · CargoX report", "p.16: HK 2024 gap HK$311.2–519.1bn (KPMG desktop estimate) · 19 Jan 2026", URL.cargox], ["HKMA · CargoX pilot", "Pilot with 21 banks · 7 May 2026", URL.cargoxPilot],
   ["HKMA · Project Ensemble", "New phase · 13 Nov 2025", URL.ensemble], ["HKMA · EnsembleTX", "24/7 tokenised CeBM settlement · 2 Nov 2026", URL.ensembleTX],
   ["HKMA · e-HKD Phase 2", "Report, 28 Oct 2025 (mainly retail use cases)", URL.ehkd], ["BIS", "Project mBridge", URL.mbridge]].forEach(([who, what, u], i) => {
    const col = i % 2, row = Math.floor(i / 2), bw = (W - 2 * MX - 0.3) / 2, x = MX + col * (bw + 0.3), y = 1.85 + row * 1.15;
    T(s, `[${i + 1}]`, { x, y, w: 0.5, h: 0.35, fontSize: 13, bold: true, italic: true, color: K.teal, fontFace: SERIF });
    T(s, who, { x: x + 0.55, y, w: bw - 0.6, h: 0.35, fontSize: 13.5, bold: true, color: K.blue, fontFace: SERIF, hyperlink: { url: u } });
    T(s, what, { x: x + 0.55, y: y + 0.38, w: bw - 0.6, h: 0.5, fontSize: 10.5, color: K.sub });
  });
  s = page(pres, { kicker: "BACKUP  ·  B9", title: "Likely questions", section: "Backup" });
  [["Why not a central database?", "It could enforce the same rules. A shared ledger only adds value with independent bank and regulator nodes (slide 15)."],
   ["Is the efficiency gain real?", `It is a process model. The claim we stand by is ${mv("M-32")}% at matched scope (slide 13).`],
   ["Who pays for pre-funding?", "The importer in our model. A real product needs the bank to finance or remunerate the escrow (slide 14)."],
   ["Is the role selector a login?", "No — it is demo impersonation. Permissions are enforced server-side and tested per role (slide 11)."]].forEach(([q, a], i) => {
    const col = i % 2, row = Math.floor(i / 2), bw = (W - 2 * MX - 0.3) / 2, x = MX + col * (bw + 0.3), y = 1.9 + row * 2.2;
    R(s, pres, x, y, bw, 1.95, { fill: K.card, line: K.rule });
    T(s, "Q.", { x: x + 0.25, y: y + 0.2, w: 0.5, h: 0.4, fontSize: 18, bold: true, italic: true, color: K.gold, fontFace: SERIF });
    T(s, q, { x: x + 0.75, y: y + 0.2, w: bw - 1.0, h: 0.4, fontSize: 15, bold: true, color: K.ink, fontFace: SERIF, valign: "middle" });
    T(s, a, { x: x + 0.75, y: y + 0.75, w: bw - 1.0, h: 1.0, fontSize: 12, color: K.sub });
  });

  const out = path.join(D.ROOT, "presentation", "HKTH_TradeEscrow_Final_Presentation_paper.pptx");
  await pres.writeFile({ fileName: out });
  const JSZip = (() => { try { return require("jszip"); } catch (_) { return require(require.resolve("jszip", { paths: [require.resolve("pptxgenjs")] })); } })();
  const zip = await JSZip.loadAsync(fs.readFileSync(out));
  for (const f of Object.keys(zip.files)) { const m = f.match(/^ppt\/slides\/slide(\d+)\.xml$/); if (m) zip.file(f, S3.morphAll(await zip.file(f).async("string"), m[1] === "1")); }
  // rebuild with files only ([Content_Types].xml first): PowerPoint rejects packages that contain folder entries
  const clean = new JSZip();
  const names = Object.keys(zip.files).filter(n => !zip.files[n].dir).sort((a, b) => (a === "[Content_Types].xml" ? -1 : b === "[Content_Types].xml" ? 1 : 0));
  for (const n of names) clean.file(n, await zip.file(n).async("nodebuffer"), { createFolders: false });
  fs.writeFileSync(out, await clean.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
  console.log("wrote", out, NUM, "slides");
})();
