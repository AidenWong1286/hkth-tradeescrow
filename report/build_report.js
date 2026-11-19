// Final Project Report generator. Run: node report/build_report.js
// Key figures are read from results/*.csv so the report cannot drift from the evidence.
const fs = require("fs");
const path = require("path");
const {
  HorizontalPositionRelativeFrom, VerticalPositionRelativeFrom,
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType,
  ShadingType, ImageRun, PageBreak, PageOrientation, TableOfContents, Footer, PageNumber, LevelFormat, BorderStyle, Header,
  ExternalHyperlink, SectionType,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
function parseCSV(p) {
  const txt = fs.readFileSync(path.join(ROOT, p), "utf8").replace(/^﻿/, "");
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
const M = Object.fromEntries(parseCSV("results/metrics.csv").map(m => [m.metric_id, m]));
const v = id => M[id].value;
const vd = id => `${M[id].value}/${M[id].denominator}`;
const tl = parseCSV("results/timelines.csv");
const T = (scen, model, field, level = "base", term = "0") => tl.find(r => r.scenario === scen && r.model === model && r.assumption_level === level && r.payment_term_days === term)[field];
const ctrl = parseCSV("results/control_matrix.csv");
const audit = parseCSV("results/audit_completeness.csv");
const mut = parseCSV("results/mutation_analysis.csv");
const mut1 = parseCSV("results/mutation_analysis_run1_before_test_fixes.csv");
const tests = parseCSV("results/test_results.csv");
const rob = Object.fromEntries(parseCSV("results/robustness.csv").map(r => [r.metric, r.value]));
const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, "results/run_manifest.json"), "utf8"));
const humans = parseCSV("results/measured_human_commands.csv");

// ------------------------------------------------------------------ styling helpers
// palette shared with the cover: navy / teal / gold, red only for warnings
const FONT = "Calibri", HFONT = "Georgia", INK = "1C2433", NAVY = "0B1730", TEAL = "1F8A82", TEALD = "176A64", AMBER = "B07A22", GREY = "5B6573";
const URL_RE = /(https?:\/\/[^\s)]+[^\s).,;])/;
function plain(part, base, out) {   // turn bare URLs into clickable hyperlinks (P1-5)
  part.split(URL_RE).forEach((seg, i) => {
    if (!seg) return;
    if (i % 2 === 1) out.push(new ExternalHyperlink({ link: seg, children: [new TextRun({ text: seg, style: "Hyperlink", ...base, color: "2B4570", underline: {} })] }));
    else out.push(new TextRun({ text: seg, ...base }));
  });
}
function runs(s, base = {}) {   // **bold** and %%italic%% markup; URLs become hyperlinks
  const out = [];
  s.split(/(\*\*[^*]+\*\*|%%[^%]+%%|\[\[[^\]]+\]\])/).forEach(part => {
    if (!part) return;
    if (part.startsWith("[[")) { out.push(...chipRuns(part.slice(2, -2))); return; }
    if (part.startsWith("**")) out.push(new TextRun({ text: part.slice(2, -2), bold: true, ...base }));
    else if (part.startsWith("%%") && part.endsWith("%%")) out.push(new TextRun({ text: part.slice(2, -2), italics: true, ...base }));
    else plain(part, base, out);
  });
  return out;
}
// ---------- design system (matches cover and at-a-glance page) ----------
const HAIR = "E3E7EE", PALE = "F6F7F9", RED = "B8342A", MUTE = "7A8496", MONO = "Consolas";
const CHIPC = { TESTED: [TEAL, "E8F3F1"], MODELLED: [AMBER, "F7F1E4"], ASSUMED: [MUTE, "F1F3F6"], SANITY: [MUTE, "F1F3F6"], PENDING: [AMBER, "F7F1E4"],
  PASS: [TEAL, "E8F3F1"], BLOCKED: [TEAL, "E8F3F1"], yes: [TEAL, "E8F3F1"], SURVIVOR: [AMBER, "F7F1E4"], FAIL: [RED, "FBEDEB"], no: [AMBER, "F7F1E4"] };
function chipColor(t) { const k = Object.keys(CHIPC).find(k => t.toUpperCase().startsWith(k.toUpperCase()) || t.toUpperCase().includes(" " + k.toUpperCase())); return CHIPC[k] || [NAVY, "EEF1F6"]; }
function chipRuns(t, size = 14) {
  const [c, f] = chipColor(t);
  return [new TextRun({ text: ` ${t.toUpperCase()} `, font: FONT, size, bold: true, color: c, characterSpacing: 16, shading: { type: ShadingType.CLEAR, color: "auto", fill: f } }),
          new TextRun({ text: " ", size })];
}
const NB = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const HAIRB = { style: BorderStyle.SINGLE, size: 4, color: HAIR };
const NAVYB = (sz = 8) => ({ style: BorderStyle.SINGLE, size: sz, color: NAVY });
const CALLOUT = {
  "**The gap.**": ["EEF7F5", TEAL, "KEY GAP"],
  "**What the mutation analysis taught us.**": ["EEF7F5", TEAL, "KEY FINDING", "report/figs/design/side_mutation.png"],
  "**Matched scope.**": ["F7F1E4", AMBER, "SENSITIVITY  ·  HYPOTHETICAL CROSS-BANK LEG", "report/figs/design/side_matched.png"],
  "**H5: the trade-off is real.**": ["F7F1E4", AMBER, "THE TRADE-OFF"],
  "**Conclusion.**": ["EEF1F6", NAVY, "CONCLUSION"] };
const labelPara = (t, c, o = {}) => new Paragraph({ keepNext: true, spacing: { before: o.before || 0, after: o.after === undefined ? 50 : o.after },
  children: [new TextRun({ text: t, font: FONT, size: o.size || 15, bold: true, color: c, characterSpacing: 40 })] });
function sideImg(p) {
  const buf = fs.readFileSync(path.join(ROOT, p)); const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20); const px = (w / 300) * 96 * 0.8;
  return new Paragraph({ children: [new ImageRun({ type: "png", data: buf, transformation: { width: px, height: px * h / w }, altText: { title: p, description: "summary graphic", name: path.basename(p) } })] });
}
function boxed(children, fill, edge, widthTw = 9746, side = null) {
  const sideTw = side ? 2500 : 0, mainTw = widthTw - sideTw;
  const mk = (w, ch, extra = {}) => new TableCell({ width: { size: w, type: WidthType.DXA }, shading: { type: ShadingType.CLEAR, color: "auto", fill },
    borders: { top: { style: BorderStyle.SINGLE, size: 18, color: edge }, bottom: NB, left: NB, right: NB }, margins: { top: 170, bottom: 130, left: 240, right: 240 }, children: ch, ...extra });
  const cells = [mk(mainTw, children)];
  if (side) cells.push(mk(sideTw, [sideImg(side)], { margins: { top: 200, bottom: 100, left: 120, right: 120 } }));
  return new Table({ width: { size: widthTw, type: WidthType.DXA }, columnWidths: side ? [mainTw, sideTw] : [widthTw], rows: [new TableRow({ cantSplit: false, children: cells })] });
}
const P0 = (s, o = {}) => new Paragraph({ children: runs(s, o.run || {}), spacing: { after: 60, line: 240 }, alignment: o.align || AlignmentType.JUSTIFIED, ...o.p });
const P = (s, o = {}) => {
  const k = Object.keys(CALLOUT).find(key => s.startsWith(key));
  if (!k) return P0(s, o);
  const [fill, edge, lab, side] = CALLOUT[k];
  return [new Paragraph({ text: "", spacing: { after: 40 } }), boxed([labelPara(lab, edge, { after: 70 }), P0(s, { ...o, align: AlignmentType.LEFT })], fill, edge, 9746, side),
          new Paragraph({ text: "", spacing: { after: 100 } })];
};
const H1 = (s, o = {}) => {
  const m = s.match(/^(\d+\.|Appendix [A-H]\.)\s(.*)$/);
  const p = new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: !!o.newPage, children: m ? [new TextRun({ text: m[1] + " ", color: AMBER }), new TextRun({ text: m[2] })] : [new TextRun({ text: s })] });
  p._h1 = s; return p;
};
const H2CHIP = { "7.1": "TESTED · SYNTHETIC DATA", "7.2": "MODELLED · NOT MEASURED", "7.3": "TESTED · SYNTHETIC DATA", "7.4": "PENDING" };
const H2 = s => {
  const m = s.match(/^(\d+\.\d+|[A-H]\.\d+)\s(.*)$/);
  const kids = m ? [new TextRun({ text: m[1] + "  ", color: AMBER }), new TextRun({ text: m[2] })] : [new TextRun({ text: s })];
  if (m && H2CHIP[m[1]]) kids.push(new TextRun({ text: "   " }), ...chipRuns(H2CHIP[m[1]], 13).slice(0, 1));
  return new Paragraph({ heading: HeadingLevel.HEADING_2, children: kids });
};
const B = (s, lvl = 0) => new Paragraph({ children: runs(s), numbering: { reference: "bul", level: lvl }, spacing: { after: 40, line: 240 } });
const N = (s) => new Paragraph({ children: runs(s), numbering: { reference: "num", level: 0 }, spacing: { after: 60, line: 252 } });
const PB = () => new Paragraph({ children: [new PageBreak()] });
const cap = s => new Paragraph({ children: runs(s, { size: 14, color: MUTE }), spacing: { before: 30, after: 140 }, border: { top: { ...HAIRB, space: 4 } } });
// exhibit headline: what the figure or table SHOWS (finding-first), original caption kept as the source line
const HEADS = {
  "Figure ES1": "Funds move only when all three gates pass; a failed gate goes to a person, not to a payment",
  "Figure 1": "Seven roles act through one service layer; everything the contract cannot see enters as an attestation",
  "Figure 2": "Fifteen permitted transitions, and exactly one path to Released",
  "Figure 3": "Open account: seven manual settlement tasks, and the exporter ships unsecured",
  "Figure 4": "Escrow: funds locked before shipment; three attested gates decide the release",
  "Figure 5": "Under an AML hold the guard refuses release, and HKD 250,000 stays locked",
  "Figure 6": "Escrow cuts manual settlement tasks — but the honest comparison is 7 → 5, not 7 → 3",
  "Figure 7": "The exporter is credited sooner in every scenario and under every payment term",
  "Figure 8": "Escrow moves the financing burden from exporter to importer; it does not remove it",
  "Table 1": "Hong Kong is building the rails; none of these initiatives offers conditional trade settlement",
  "Table 2": "Escrow sits between open account and the letter of credit",
  "Table 3": "Each role can do only its own job, and every refusal is tested",
  "Table 3a": "Both models settle the same trade, but the prototype stops earlier",
  "Table 4": "Every control and invariant held; the test suite itself caught 13 of 14 planted bugs",
  "Table 5": "The direction of the result holds at the low and high end of every assumption",
};
function exhibitHead(label, head, o = {}) {
  return new Paragraph({ keepNext: true, spacing: { before: o.before === undefined ? 120 : o.before, after: 40 }, border: { bottom: { ...NAVYB(10), space: 4 } },
    children: [new TextRun({ text: label.toUpperCase() + " ", font: FONT, size: 15, bold: true, color: TEAL, characterSpacing: 40 }),
               new TextRun({ text: head, font: HFONT, size: o.size || 19, bold: true, color: NAVY })] });
}
function splitCaption(caption, o) {
  const m = caption.match(/^((?:Figure|Table) [A-Z]*\d*[a-z]?(?: \(= Figure \d+\))?)\.\s(.*)$/);
  if (!m) return { label: o.label || "IN BRIEF", head: o.head || caption, src: o.head ? caption : null };
  const key = m[1].replace(/ \(=.*\)/, "");
  const head = o.head || HEADS[key];
  return head ? { label: m[1], head, src: m[2] } : { label: m[1], head: m[2], src: null };
}
// NOFIG=1 builds a figure-free copy, used only to measure the page count the course outline defines (figures excluded)
const NOFIG = process.env.NOFIG === "1";
function fig(p, wcm, caption, o = {}) {
  if (NOFIG) return [];
  const file = path.join(ROOT, p);
  const buf = fs.readFileSync(file);
  let w, h;
  if (buf[0] === 0x89) { w = buf.readUInt32BE(16); h = buf.readUInt32BE(20); }
  else { let i = 2; while (i < buf.length) { const len = buf.readUInt16BE(i + 2); if (buf[i + 1] >= 0xC0 && buf[i + 1] <= 0xC2) { h = buf.readUInt16BE(i + 5); w = buf.readUInt16BE(i + 7); break; } i += 2 + len; } }
  const FSC = /^Figure H/.test(caption) ? 1 : (+process.env.FIGSCALE || 0.65);
  const px = wcm * FSC / 2.54 * 96;
  const c = splitCaption(caption, o);
  return [exhibitHead(c.label, c.head, { size: wcm > 20 ? 21 : 19 }),
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: !!c.src, spacing: { before: 60, after: c.src ? 20 : 120 },
    children: [o.svg && fs.existsSync(path.join(ROOT, o.svg))
      ? new ImageRun({ type: "svg", data: fs.readFileSync(path.join(ROOT, o.svg)), fallback: { type: "png", data: buf }, transformation: { width: px, height: px * h / w },
          altText: { title: c.head, description: caption, name: path.basename(o.svg) } })
      : new ImageRun({ type: p.endsWith(".png") ? "png" : "jpg", data: buf, transformation: { width: px, height: px * h / w },
      altText: { title: c.head, description: caption, name: path.basename(p) } })] }),
    ...(c.src ? [cap("Source: " + c.src)] : [])];
}
const STATUS_RE = /^(PASS|FAIL|yes|no \(expected for PC-01\)|BLOCKED|1 SURVIVOR|SANITY)$/;
const FILE_RE = /(\.csv|\.py|\.xml|\.jsonl|\.md)\b/;
const ID_RE = /^(TC|NC|PC|M|B|E)-?\d+[a-z]?\b/;
function cellRuns(t, o, head) {
  if (head) return [new TextRun({ text: String(t).toUpperCase(), font: FONT, size: 13, bold: true, color: MUTE, characterSpacing: 8 })];
  if (STATUS_RE.test(t)) return chipRuns(t === "no (expected for PC-01)" ? "no · PC-01" : t, 13).slice(0, 1);
  if (FILE_RE.test(t) && !/\s{2}/.test(t) && String(t).length < 60) return [new TextRun({ text: String(t), font: MONO, size: (o.size || 17) - 3, color: GREY })];
  if (ID_RE.test(t) && String(t).length < 9) return [new TextRun({ text: String(t), font: MONO, size: (o.size || 17) - 1, bold: true, color: NAVY })];
  return runs(String(t), { size: o.size || 17, color: INK });
}
function table(header, rows, widthsCm, o = {}) {
  const tw = widthsCm.map(c => Math.round(c * 567));
  const total = tw.reduce((a, b) => a + b, 0);
  const n = rows.length;
  const cell = (t, i, head, k) => new TableCell({
    width: { size: tw[i], type: WidthType.DXA },
    borders: { top: NB, left: NB, right: NB, bottom: head ? NAVYB(10) : (k === n - 1 ? NAVYB(8) : HAIRB) },
    shading: !head && k % 2 === 1 ? { type: ShadingType.CLEAR, color: "auto", fill: PALE } : undefined,
    margins: { top: head ? 30 : 40, bottom: head ? 50 : 40, left: 90, right: 90 },
    children: String(t).split("\n").map(line => new Paragraph({ children: cellRuns(line, o, head), spacing: { after: 0, line: 240 } })),
  });
  const c = o.caption ? splitCaption(o.caption, o) : null;
  return [...(c ? [exhibitHead(c.label, c.head)] : []),
    new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: tw,
    rows: [new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, i, true, -1)) }),
           ...rows.map((r, k) => new TableRow({ cantSplit: true, children: r.map((x, i) => cell(x, i, false, k)) }))] }),
    c && c.src ? cap("Source: " + c.src) : new Paragraph({ text: "", spacing: { after: 160 } })];
}
const brief = (p, head, src, w = 15.0) => fig(p, w, src, { label: "IN BRIEF", head });

// peer feedback: real responses from results/survey_anonymised.csv only (never simulated)
function peerFeedback() {
  const f = path.join(ROOT, "results/survey_anonymised.csv");
  const rows = fs.existsSync(f) ? parseCSV("results/survey_anonymised.csv").filter(r => [1, 2, 3, 4, 5].every(i => String(r["Q" + i] || "").trim())) : [];
  if (!rows.length) return [
    P(`The proposal planned 8–10 peer reviews on a 5-point questionnaire (§7.6). **[TEAM TO COMPLETE: insert real results here, or keep this sentence.]** At the time of writing, peer feedback had not yet been collected. The protocol, task script and anonymised template are in docs/peer_feedback_protocol.md, and no results are reported. Even when collected, a sample of about eight classmates supports formative feedback on clarity, not conclusions about practitioners.`),
    ...brief("report/figs/design/g_survey.png", "The peer questionnaire is ready: five items on a 5-point scale, plus two open questions", "docs/peer_feedback_protocol.md (task script: TC-001, TC-002, TC-003)", 16.0)];
  const n = rows.length, Q = ["status was easy to understand", "release steps were clear", "mismatch block was understandable", "AML freeze was understandable", "simulation vs real system was clear"];
  const agree = [1, 2, 3, 4, 5].map(i => rows.filter(r => +r["Q" + i] >= 4).length / n);
  const lo = agree.indexOf(Math.min(...agree)), hi = agree.indexOf(Math.max(...agree));
  return [P(`We ran the peer-feedback protocol (proposal §7.6) with **${n} classmates**. Each followed the TC-001 to TC-003 task script and answered five items on a 5-point scale. Agreement (4 or 5) was highest for Q${hi + 1} (${Q[hi]}, ${Math.round(agree[hi] * 100)}%) and lowest for Q${lo + 1} (${Q[lo]}, ${Math.round(agree[lo] * 100)}%). **[TEAM: one sentence on the change made in response.]** With n = ${n} classmates this is formative feedback on clarity, not evidence about practitioners.`),
    ...brief("report/figs/design/g_survey.png", `What ${n} classmates said after using the prototype`, "results/survey_anonymised.csv (anonymised; distribution per item, centred on neutral)", 16.0)];
}

// ------------------------------------------------------------------ content
// Student IDs live in team.local.json (git-ignored); without it the report is built with no IDs.
const TEAM_IDS = fs.existsSync(path.join(ROOT, "team.local.json")) ? JSON.parse(fs.readFileSync(path.join(ROOT, "team.local.json"), "utf8")).ids : {};
const members = [["Tang Yu Hin", "Alex"], ["Chow Ka Shing", "Marcus"], ["Wong Ho Ming", "Michael"], ["So Lai Chun", "Jeff"]].map(([n, a]) => [`${n}, ${a}`, TEAM_IDS[n] || ""]);
const testsPass = tests.filter(t => t.status === "PASS").length;
const negBlocked = ctrl.filter(c => c.control_id.startsWith("NC") && c.blocked === "True").length;
const negTotal = ctrl.filter(c => c.control_id.startsWith("NC")).length;
const auditReq = audit.reduce((a, r) => a + +r.required_lifecycle_events, 0), auditOk = audit.reduce((a, r) => a + +r.present_with_required_fields, 0);
const mutKilled = mut.filter(m => m.killed_by_suite === "True").length, mut1Killed = mut1.filter(m => m.killed_by_suite === "True").length;

const R_ = (t, o = {}) => new TextRun({ text: t, font: o.font || FONT, size: o.size || 22, bold: o.bold, italics: o.italics, color: o.color || INK, characterSpacing: o.cs });
const PP = (runsArr, o = {}) => new Paragraph({ children: runsArr, alignment: o.align || AlignmentType.LEFT, spacing: Object.assign({ before: o.before || 0, after: o.after === undefined ? 80 : o.after }, o.line === null ? {} : { line: o.line || 260 }) });
function imgPara(p, wcm, o = {}) {
  const buf = fs.readFileSync(path.join(ROOT, p)); const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20); const px = wcm / 2.54 * 96;
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: o.before || 0, after: o.after || 0 }, keepNext: o.keepNext,
    children: [new ImageRun({ type: "png", data: buf, transformation: { width: px, height: px * h / w }, altText: { title: o.alt || p, description: o.alt || p, name: path.basename(p) } })] });
}
// Cover and "at a glance" are full-page A4 artworks (report/make_covers_AD.py, report/make_glance.py), anchored to the page.
const COVER = process.env.COVER || "report/figs/cover_D.png";
const fullPage = (p, alt) => new Paragraph({ spacing: { before: 0, after: 0 }, children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(ROOT, p)),
  transformation: { width: 793.7, height: 1122.5 }, altText: { title: alt, description: alt, name: path.basename(p) },
  floating: { horizontalPosition: { relative: HorizontalPositionRelativeFrom.PAGE, offset: 0 }, verticalPosition: { relative: VerticalPositionRelativeFrom.PAGE, offset: 0 },
    behindDocument: true, allowOverlap: true, lockAnchor: true } })] });
const ART_PAGE = { page: { margin: { top: 0, bottom: 0, left: 0, right: 0, header: 0, footer: 0 } } };
const cover = [fullPage(COVER, "Cover. HK–TH TradeEscrow: A Tokenised-Deposit Escrow Prototype for Hong Kong–Thailand Cross-Border Trade Finance. FTEC3002 Group 1 final project report, CUHK Department of SEEM, submitted 19 November 2026. Members: " + members.map(([n, id]) => `${n.replace(",", "")}${id ? " " + id : ""}`).join("; ") + ". All transaction data are synthetic.")];
const glance = [fullPage("report/figs/glance_a4.png", "Report at a glance: our answer is a qualified yes. Safer and auditable (simulated); modestly more efficient (modelled, manual tasks 7 to 5 at matched scope); not free (importer cash committed 2.5 to 7.5 days while exporter risk falls 7 to 0 days). Key results: 91/91 tests, 17/17 unsafe releases refused, 0 violations in 5,935 checks, 13/14 seeded defects caught.")];

const TOCDATA = process.env.TOC_JSON ? JSON.parse(fs.readFileSync(process.env.TOC_JSON, "utf8")) : { entries: [], body: "" };
const { TabStopType } = require("docx");
const PARTLAB = { "1. ": "PART 01  ·  WHY ESCROW", "4. ": "PART 02  ·  THE DESIGN", "6. ": "PART 03  ·  THE EVIDENCE", "8. ": "PART 04  ·  THE VERDICT AND REFLECTIONS", "References": "REFERENCES AND APPENDICES" };
const tocLines = (TOCDATA.entries.length ? TOCDATA.entries : [{ t: "Contents are generated on the second build pass", p: "", lvl: 1 }]).flatMap(e => {
  const k = Object.keys(PARTLAB).find(k => e.t.startsWith(k));
  const m = e.t.match(/^(\d+\.\d*|Appendix [A-H]\.)\s(.*)$/);
  const line = new Paragraph({ spacing: { after: e.lvl === 1 ? 20 : 0, line: 228 }, indent: { left: e.lvl === 1 ? 0 : 420 },
    tabStops: [{ type: TabStopType.RIGHT, position: 9720, leader: "dot" }],
    children: [...(m ? [new TextRun({ text: m[1] + " ", bold: e.lvl === 1, size: e.lvl === 1 ? 20 : 18, color: AMBER })] : []),
      new TextRun({ text: `${m ? m[2] : e.t}`, bold: e.lvl === 1, size: e.lvl === 1 ? 20 : 18, color: e.lvl === 1 ? NAVY : INK }),
      new TextRun({ text: `\t${(TOCDATA.s1 && e.p >= TOCDATA.s1 && e.p < TOCDATA.ref) ? e.p - TOCDATA.s1 + 1 : "PDF " + e.p}`, size: e.lvl === 1 ? 20 : 18, color: (TOCDATA.s1 && e.p >= TOCDATA.s1 && e.p < TOCDATA.ref) ? (e.lvl === 1 ? NAVY : GREY) : MUTE, font: HFONT, italics: true })] });
  return k ? [labelPara(PARTLAB[k], AMBER, { before: 130, after: 50, size: 15 }), line] : [line];
});
const toc = [new Paragraph({ children: [new TextRun({ text: "CONTENTS", bold: true, size: 17, color: TEAL, characterSpacing: 60 })], spacing: { after: 40 } }),
  new Paragraph({ children: [new TextRun({ text: "Contents", bold: true, size: 40, font: HFONT, color: NAVY })], spacing: { after: 220 }, border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: AMBER, space: 6 } } }),
  ...tocLines,
  P(`%%Page count (course outline §10; limit 15 pages excluding cover, contents, executive summary, appendices, figures and references): ${TOCDATA.body || "Body pages are computed on the second build pass."} Individual self-reflections are inside the counted body (Section 10).%%`, { run: { size: 16, color: GREY } }),
];

function kpiStrip(items) {
  const cw = Math.floor(9746 / items.length);
  return new Table({ width: { size: cw * items.length, type: WidthType.DXA }, columnWidths: items.map(() => cw), rows: [new TableRow({ cantSplit: true, children: items.map(([big, lab, col]) =>
    new TableCell({ width: { size: cw, type: WidthType.DXA }, shading: { type: ShadingType.CLEAR, color: "auto", fill: PALE },
      borders: { top: { style: BorderStyle.SINGLE, size: 12, color: col }, bottom: NB, left: { style: BorderStyle.SINGLE, size: 24, color: "FFFFFF" }, right: { style: BorderStyle.SINGLE, size: 24, color: "FFFFFF" } },
      margins: { top: 120, bottom: 100, left: 160, right: 120 }, children: [
        PP([R_(big, { size: 30, bold: true, color: NAVY, font: HFONT })], { after: 20, line: 240 }),
        PP([R_(lab, { size: 16, color: GREY })], { after: 0, line: 230 })] })) })] });
}
const exec = [
  H1("Executive Summary", { newPage: true }),
  P(`Cross-border trade finance between Hong Kong and Thailand, a corridor worth US$13.7 billion in 2023 [6], still depends on manual document checks, fragmented records and repeated compliance work. Under open-account terms the exporter ships first and carries an unsecured receivable until the importer pays. This project asked whether a **pre-funded smart-contract escrow holding simulated tokenised deposits** could make settlement more efficient, traceable and auditable without weakening compliance controls, as set out in our submitted proposal [P1].`),
  P(`We built and tested a working low-fidelity prototype. A Python escrow engine (the simulated smart contract) locks synthetic HKD tokenised deposits and releases them only when three off-chain attestation gates are current: shipment (for the right trade), four-document matching (on the latest document revisions) and KYC/AML (at creation and fresh before release, with no active hold). The engine implements the proposal's six states (Created, Pending, Under Review, Frozen, Released, Refunded/Terminated), seven role-limited participant views, integer-cent token accounting with a conservation check, and a SHA-256 hash-chained journal that records every accepted and refused command. Streamlit and Flask interfaces, BPMN 2.0 process maps, Solidity-like pseudocode and a conceptual e-HKD two-leg atomic-settlement extension complete the artefacts.`),
  ...fig("report/figs/how_it_works.png", 14.0, "Figure ES1. How the escrow decides: funds are released only when all three attestation gates pass; a failed gate routes the trade to an accountable human decision"),
  labelPara("RESULTS AT A GLANCE  ·  SIMULATION ON SYNTHETIC DATA", TEAL, { before: 80, after: 80 }),
  kpiStrip([[`${testsPass}/${tests.length}`, "automated tests pass", TEAL], [vd("M-04"), "unsafe release attempts blocked", TEAL],
            [`0/${Number(M["M-09"].denominator).toLocaleString("en")}`, "invariant violations (random sequences)", NAVY], [`${v("M-13")} → ${v("M-14")}`, "manual settlement tasks (process model, not measured)", AMBER]]),
  new Paragraph({ text: "", spacing: { after: 140 } }),
  P(`**Findings (simulation results on synthetic data).** ${testsPass}/${tests.length} automated tests passed, covering all 24 planned test cases. The three flagship scenarios (normal, document mismatch, AML alert) followed their specified state paths in ${vd("M-02")} assertions. ${negBlocked}/${negTotal} unsafe release attempts were blocked with funds unchanged, while a positive control released correctly. Across 200 randomised synthetic trades (${Number(rob.commands).toLocaleString("en")} commands), ${rob.invariant_checks} invariant checks found **zero** violations. Audit completeness was ${auditOk}/${auditReq} required lifecycle events, and the regulator reconstructed every state path from metadata alone without seeing commercial document values. Mutation analysis showed the test suite detected ${mutKilled}/${mut.length} deliberately seeded defects (up from ${mut1Killed}/${mut1.length} after we closed two test gaps it exposed).`),
  P(`**Comparison with open account (team-defined process model; not measured industry savings).** In our BPMN models, manual settlement tasks fall from ${v("M-13")} to ${v("M-14")} in the normal case (and from 8 to 4 in each exception case). This compares unequal end points: the prototype stops at a Bank H release while the baseline ends with a Bank O credit. If the escrow is given hypothetical steps to reach the same end point, the reduction is ${v("M-13")} to ${v("M-31")} (${v("M-32")}%). Under our stated base-case durations, post-shipment latency to exporter credit falls from ${v("M-21")} to ${v("M-22")} simulated days with immediate payment terms. The trade-off is that escrow moves the financing burden: the importer's cash is committed for ${v("M-25")} days instead of ${v("M-24")}, while the exporter's unsecured receivable (37 days under a 30-day term) disappears. These durations are team assumptions, not field measurements, so the results show %%where%% the design removes hand-offs, not real-world savings. After an independent audit, we also closed a UI data-access gap (the ledger page bypassed role views) and added HTTP-level regression tests.`),
  P0(`**Conclusion.** Rule-driven escrow can enforce release, review and freeze controls consistently and produce a reconstructable audit trail. Its value, however, depends on trustworthy off-chain attestations, on who funds the pre-funding, and on unresolved legal questions about tokenised-deposit ownership and settlement finality. HKMA's 2 November 2026 move of EnsembleTX to 24/7 settlement in tokenised central-bank money [5] makes the conceptual e-HKD leg more relevant, but our prototype is not connected to it.`),
];

const body = [
  H1("1. Problem Definition and Current Financial Infrastructure"),
  H2("1.1 The corridor and the financing problem"),
  P(`Hong Kong was Thailand's 13th-largest trading partner in 2023, with total trade of US$13.7 billion (2.4% of Thailand's trade) [6]. Trade at this scale relies on trade finance and payment infrastructure that is still largely document-driven. The Asian Development Bank's latest survey estimates the global trade-finance gap (unmet demand) at **US$2.5 trillion in 2025**, about 10% of global trade, unchanged from 2023 [9]; our proposal cited the earlier **2020** estimate of US$1.7 trillion [8]. The two surveys are different years and are not combined here. For Hong Kong, HKMA's Project CargoX report estimates a **2024** trade-finance gap of HK$311.2–519.1 billion [10]. This is an overall estimate, not an SME-only figure.`),
  H2("1.2 How settlement works today and where it is weak"),
  P(`Under **open account**, the most common arrangement between trusted counterparties, the exporter ships goods and sends the commercial invoice and bill of lading to the importer, who checks them and pays at the end of an agreed credit term. Banks screen and execute the payment but do not hold funds against conditions. Documentary credits (letters of credit) give the exporter bank assurance but at higher cost and processing effort; they are a different product and not our baseline. Following the trade-services treatment in the course text [15], we identify four weaknesses relevant to this corridor:`),
  B("**Risk sits with the exporter.** From shipment until payment the exporter holds an unsecured receivable (in our base case 7 days with immediate terms, 37 days on 30-day terms)."),
  B("**Manual, sequential verification.** Documents are compiled, couriered or emailed, and checked by hand against the contract by different parties, with discrepancies resolved by email."),
  B("**Fragmented records.** Each party keeps its own copy; there is no shared, tamper-evident record of who approved what and when, which makes disputes and supervisory review slow. HKMA describes the resulting proliferation of disconnected platforms as the “digital islands” problem [7]."),
  B("**Compliance repeated without coordination.** KYC/AML screening happens inside each bank at payment time, separate from the commercial workflow, so a late alert can stop a payment after goods have shipped."),
  ...brief("report/figs/design/g_weaknesses.png", "The exporter carries the risk from shipment to payment while documents move by hand", "team process model, base case (results/timelines.csv); numbers refer to the four weaknesses above"),
  P(`The course's learning outcomes ask us to identify such weaknesses in early implementations and design an improvement [C1]. Our improvement keeps banks and compliance in control while making the release conditions explicit, machine-checked and auditable.`),

  H1("2. Existing Initiatives and Gap Analysis"),
  P(`Hong Kong is building the infrastructure our design assumes. Table 1 compares the most relevant initiatives with what our prototype adds and what it does not.`),
  ...table(["Initiative (date)", "Money / infrastructure", "Demonstrated capability", "Gap for our use case", "Relation to prototype"], [
    ["Project Ensemble / EnsembleTX (pilot launched 13 Nov 2025; 24/7 CeBM from 2 Nov 2026) [2], [5]", "Tokenised deposits; interbank settlement first via HKD RTGS, now tokenised central-bank money", "Real-value tokenised-deposit transactions; 24/7 interbank settlement; 12 banks, 20 industry pioneers", "No trade-specific conditional release, document matching or exception workflow", "We model the escrow logic that could sit on such rails; e-HKD leg is conceptual"],
    ["e-HKD Pilot Programme Phase 2 (report 28 Oct 2025) [12]", "CBDC concept vs tokenised deposits", "11 pilots: tokenised-asset settlement, programmability, offline payments; HKMA prioritises wholesale use", "Policy direction, not a trade-escrow service", "Motivates separating commercial-bank money from CeBM"],
    ["Project mBridge (MVP mid-2024; BIS handed over to partners Oct 2024) [4]", "Multi-CBDC cross-border platform", "Central banks of HK, Thailand, China, UAE, Saudi Arabia", "CBDC-to-CBDC payments; no trade-document conditions", "Not used; our prototype is single-currency HKD"],
    ["Project CargoX (report 19 Jan 2026; pilot with 21 banks from 7 May 2026) [10], [11]", "Cargo/trade data via Commercial Data Interchange", "Data-driven credit assessment; 20 recommendations", "Improves data and credit access, not settlement conditionality", "Cargo data could become a trusted shipment attestation source"],
  ], [3.2, 2.9, 3.6, 3.2, 3.1], { caption: "Table 1. Existing initiatives and the remaining gap (official sources, dated)", size: 16 }),
  ...brief("report/figs/design/g_stack.png", "Hong Kong is building the money rails; the conditional-settlement layer is still empty", "Table 1 above (official sources, dated)", 16.0),
  P(`**The gap.** These programmes provide settlement rails, digital money and better data, but none of them, as publicly described, offers a **trade-specific conditional settlement layer** that (i) holds funds against shipment, documentary and compliance conditions; (ii) routes discrepancies and alerts to accountable human reviewers; and (iii) gives a regulator a privacy-limited reconstruction of the transaction. Our project prototypes that layer. We note that the 2 November 2026 EnsembleTX upgrade happened after our proposal (25 September 2026); we treat it as new context, not as something the proposal predicted. We also correct a date in our proposal: the CargoX Recommendation Report was published on 19 January 2026 [10], not in 2025 as our proposal's reference [9] stated.`),

  H2("2.1 Design alternatives for the same trade"),
  P(`The chart below (full comparison in Table 2, Appendix D) compares three ways to settle the same HKD 250,000 shipment. The comparison is qualitative and based on standard trade-services practice [15]; it is not a measured result. Escrow sits between the two traditional products: it gives the exporter a payment assurance similar to a documentary credit, but replaces bank examination of paper documents with machine-checked attestations, and it requires the importer to fund in advance rather than relying on bank credit.`),
  ...brief("report/figs/design/g_spectrum.png", "Escrow gives the exporter L/C-like assurance, but swaps bank credit and manual checks for pre-funding and automation", "Table 2 (Appendix D); qualitative", 16.0),
  H1("3. Research Question, Scope and Assumptions"),
  P(`**Research question.** Can a simulated pre-funded smart-contract escrow with tokenised deposits improve the efficiency, transparency and auditability of Hong Kong–Thailand trade-finance settlement while preserving compliance controls? We evaluated five hypotheses, without assuming success: **H1** fewer manual tasks and shorter post-shipment latency under the same declared assumptions; **H2** no release unless all gates are current; **H3** a mismatch leads to review and an AML alert to freeze, never to silent release; **H4** authorised reviewers can reconstruct events without unrelated commercial data; **H5** pre-funding changes liquidity burden and risk allocation, and this must be measured, not ignored.`),
  ...brief("report/figs/design/g_ladder.png", "Five hypotheses, and the strongest kind of evidence this project can give each one", "H1–H5 as defined above; evidence levels as reported in Sections 7–8"),
  P(`**Scope.** The prototype is a low-fidelity simulation using synthetic data only (fixture FX-2026.11.07-v1: one importer, one exporter, a HKD 250,000 stoneware shipment, four trade documents). The core escrow is **single-currency HKD**. Thai Bank O observes and acknowledges releases but no Thai-baht credit, FX or cross-bank finality is modelled. KYC/AML outcomes are simulation inputs driven by a synthetic watchlist and party registry; they are not regulatory clearance. The “smart contract” is a Python service backed by SQLite, with Solidity-like pseudocode documenting the same rules; nothing was deployed on a blockchain or public testnet.`),
  P(`**Key assumptions.** All business durations used in the comparison (Section 6) are team assumptions stated as low/base/high ranges and fixed before the comparison was run. Automated engine steps are modelled as taking zero business days, which is optimistic. Customs clearance, goods preparation and carriage are treated as common to both processes. The HKD 5,000,000 per-trade limit, the 48-hour pre-release screening window, the fictional 0/30-day payment terms and the HKD 250,000 test trade are **team parameters**, not HKMA or legal requirements.`),

  H1("4. Architecture and Innovation"),
  P(`Figure 1 shows the architecture. Seven business participants act through a role selector. Every command goes through a **single service layer** that the Streamlit app, the Flask console, the ${tests.length}-test suite and the experiment runner all share, so no behaviour exists only in a user interface. Both user interfaces read ledger data only through the same role projections; the participant selector is a demonstration impersonation control for a single-operator localhost demo, not authentication.`),
  ...fig("report/figs/architecture.png", 16.0, "Figure 1. Architecture and trust boundaries: seven roles, one escrow service layer, simulated off-chain attestations (full-size: Appendix H)"),
  H2("4.1 Innovative elements"),
  B("**Smart-contract escrow logic (proposal §6.1).** A deterministic state machine with an explicit 15-edge transition table; any other transition raises an error. Release is a single guarded function whose evaluation, token posting and journal append commit in one serialised database transaction."),
  B("**Compliance-by-design (§6.2).** KYC/AML is enforced at two checkpoints (creation, and fresh pre-release within a 48-hour window, a team parameter). An alert at any time opens a hold that blocks release and refund until an authorised compliance decision; a per-trade HKD 5,000,000 limit (team parameter) is enforced at creation."),
  B("**Attestation integrity.** Shipment evidence must name this trade's shipment ID. Each document approval is pinned to a digest of the latest revisions, so a new revision automatically revokes earlier approvals. Ties between revisions are resolved by a strict revision counter, not by timestamp."),
  B("**Role-based views and least-privilege audit (§6.4).** Importers and exporters see only their own trades. Logistics and customs see only their reference fields. The regulator receives event metadata, reason codes and hashes, but not document bodies, goods descriptions, prices or user identifiers. Refused reads and commands are themselves logged."),
  B("**Tamper-evident journal.** Each event stores SHA-256(previous hash + canonical event). A verifier detects edits, deletions and reordering. This is a tamper-evidence demonstration, not distributed consensus."),
  B("**Simulated e-HKD interoperability (§6.3).** A separate two-phase-commit illustration moves a tokenised-deposit leg and a central-bank-money leg together, or neither."),
  H2("4.2 Why off-chain attestations, and why a mock ledger"),
  P(`A contract cannot observe that goods were loaded or that a sanctions screen was clean. These facts must enter as **attestations** from accountable sources: a carrier or electronic bill-of-lading platform, a document checker, and the bank's compliance function. Our design therefore makes the trust boundary explicit (orange in Figure 1) and records each attestation's issuer, time, result, input digest and expiry. A permissioned DLT would let banks, logistics and the regulator share one record without a single operator. Our prototype uses a single SQLite database with a hash-chained journal, which is enough to test the rules and auditability but cannot show the governance or resilience benefits of a real network. We do not claim DLT is superior to a well-governed central database.`),
  H2("4.3 Money model"),
  P(`The prototype distinguishes three things that are often conflated: a **simulated tokenised commercial-bank deposit** (a claim on Bank H, the escrow asset), a **simulated central-bank-money leg** (used only in the e-HKD extension) and the **trade denomination** (HKD). All amounts are integer cents. The supply of tokens is issued once at set-up, and after every command the engine checks that the sum of holder balances equals issued supply, that no balance is negative, that each escrow account equals its locked amount, and that replaying all postings reproduces every balance.`),

  H1("5. Smart-Contract Escrow and Exception Logic"),
  ...fig("diagrams/report/state_machine_slide.png", 13.4, "Figure 2. Six-state escrow machine; the 15 drawn transitions are exactly the engine's TRANSITIONS table in tradeescrow/model.py (teal = the only release path; dashed red = exception paths; full-size: Appendix H)"),
  H2("5.1 The release guard"),
  P(`A release succeeds only if all seven gates hold at evaluation time: (1) the state is Pending and the locked amount equals the trade amount; (2) there is no active compliance hold; (3) the latest shipment attestation is PASS for this trade's shipment ID; (4) the latest document attestation is PASS and its digest equals the current documents' digest; (5) creation KYC/AML passed; (6) the latest KYC/AML result is a pre-release PASS issued after the latest document approval and the latest hold; (7) that PASS is less than 48 hours old. A missing attestation is never treated as a PASS. Each refusal returns the first failing gate as a reason code (for example PRE_RELEASE_KYC_EXPIRED) and is written to the journal with the full gate evaluation.`),
  ...brief("report/figs/design/g_guard.png", "All seven checks must hold at the moment of release; the first failure becomes the reason code", "tradeescrow release guard; reason codes listed in Appendix C"),
  H2("5.2 Exception paths"),
  P(`**Document mismatch (Under Review).** When matching fails (for example invoice HKD 245,000 against a contract of HKD 250,000), the escrow moves to Under Review and the findings list the conflicting fields. Release is refused. The only exits are (a) a Bank H reviewer revalidates, which is allowed only after corrected documents produce a fresh PASS on the latest revision, returning the escrow to Pending, where a fresh pre-release screening is again required; or (b) the reviewer terminates with a review reference, refunding the importer. A document mismatch is never treated as an AML event.`),
  P(`**AML alert (Frozen).** A screening ALERT or FAIL at any checkpoint, or a manual hold by Bank H compliance, freezes the escrow. Release, refund by the operations reviewer, and any self-approval by other roles are all refused while the hold is active. A compliance officer may (a) clear the alert as a false positive with a mandatory review reference, which records a disposition and returns the escrow to the stage justified by its evidence (Pending, Created or Under Review), never directly to Released; or (b) confirm the alert and permit termination with a refund. In practice a confirmed suspicious transaction might require reporting and continued holding rather than a refund; Section 8 discusses this simplification.`),
  H2("5.3 Permissions and safety properties"),
  ...brief("report/figs/design/g_roles.png", "Who may see what: 63 visibility rules across nine principals, all obeyed", "results/audit_access_matrix.csv (core projection layer); filled = may see", 13.0),
  P(`Commands may carry an idempotency key; a replayed key returns the stored result without re-executing, and a second release on a terminal escrow is refused (TC-012, TC-013). The release and refund paths use an optimistic version check inside BEGIN IMMEDIATE transactions; with eight concurrent release commands, exactly one succeeds and seven are refused (TC-019).`),

  H1("6. Experimentation Methodology"),
  H2("6.1 Scenarios and test design"),
  P(`We implemented the proposal's three scenarios as reproducible scripts using the same fixture and a deterministic simulated clock: **TC-001** normal settlement; **TC-002** invoice amount mismatch (resolved either by correction and revalidation, or by termination); and **TC-003** a synthetic sanctions-list hit injected before pre-release screening (resolved either by false-positive clearance or by confirmed termination). These were supplemented by the 21 edge and negative cases specified in our test plan (TC-004 to TC-024), all executed through the service layer with pytest, not through user-interface clicks. We also ran:`),
  B(`a **control matrix** of ${negTotal} distinct unsafe release attempts plus one positive control;`),
  B(`a **randomised robustness study**: 200 synthetic trades (seed 3002), 30 steps each, mixing the next valid step (60%) with any action including forbidden ones (40%), clock jumps and watchlist injections, checking conservation, legal transitions, release-gate integrity and single settlement after every step;`),
  B(`**mutation analysis**: ${mut.length} defects deliberately seeded into the guard, RBAC, journal, matching and views, to test whether the suite detects them;`),
  B("a **UI end-to-end check**: a Playwright script ran through all three scenarios in a real headless browser against the Flask console and captured the screenshots used in this report and the slides;"),
  B("**UI access-control regression tests**: Flask test-client requests for every participant against the ledger page, the audit export and the operator controls, plus checks that each UI action is journalled under the participant selected in the interface."),
  ...brief("report/figs/design/g_testdesign.png", "Four layers of testing, from scripted cases to deliberately planted bugs", "results/test_results.csv, control_matrix.csv, robustness.csv, mutation_analysis.csv"),
  H2("6.2 Comparator design"),
  P(`The baseline (open account) and proposed (pre-funded escrow) processes were modelled as BPMN 2.0 maps with the same trade, parties, documents, shipment milestone and two compliance checkpoints (Figures 3 and 4). Both maps and all comparison metrics are generated from one source file (tradeescrow/process_model.py), so the diagrams and the numbers cannot diverge. Each task is classified as manual, automated, third-party manual (common to both) or waiting, with low/base/high durations stated in results/baseline_assumptions.csv. Exception classes add one manual review task (mismatch) or one compliance investigation (AML) to **each** model, so exceptions are not counted against only one side. We vary the open-account payment term (0 and 30 days) because it dominates the exporter's waiting time.`),
  ...fig("diagrams/report/baseline_bpmn_slide.png", 16.0, "Figure 3. Baseline BPMN: traditional open-account settlement, wrapped into two tiers joined at connector A (diagrams/baseline.bpmn; full-size: Appendix H)"),
  ...fig("diagrams/report/proposed_bpmn_slide.png", 16.0, "Figure 4. Proposed BPMN: pre-funded escrow with off-chain attestations, wrapped into two tiers joined at connector A (diagrams/proposed.bpmn; full-size: Appendix H)"),
  H2("6.3 Metrics and clocks"),
  P(`**Process steps** and **manual effort** are counts of executed and manual settlement tasks. Manual effort is cross-checked against the human-role commands actually executed in the prototype logs. **Execution accuracy** is correct assertions ÷ assertions. **Safety** is unsafe attempts blocked with funds unchanged ÷ attempts. **Transparency** is role-visibility rules obeyed ÷ rules specified (9 principals × 7 capabilities). **Auditability** is required lifecycle events present with all mandatory fields ÷ required, plus whether the regulator reconstructs the state path from metadata and whether commercial values leak into its export. **Time** metrics are post-shipment latency, full cycle to exporter credit, importer funds committed and exporter unsecured receivable, in **simulated business days**. These are kept strictly separate from **wall-clock engine compute time**, which we report only as a sanity check. Every figure in Section 7 comes from results/ (run of record ${manifest.run_finished_utc.slice(0, 10)}, code hash ${manifest.code_sha256_16}).`),

  H1("7. Results and Evaluation"),
  H2("7.1 Correctness and control results"),
  ...table(["Measure", "Result", "Status", "Evidence file"], [
    ["Automated tests (TC-001–TC-024, e-HKD, invariants)", `${testsPass}/${tests.length} pass`, "PASS", "test_results.csv, pytest_report.xml"],
    ["Flagship scenario assertions (7 runs)", `${vd("M-02")} (${v("M-03")}%)`, "PASS", "assertions.csv, scenarios_summary.csv"],
    ["Unsafe release attempts blocked, funds unchanged", `${negBlocked}/${negTotal}; positive control released`, "BLOCKED", "control_matrix.csv"],
    ["Random-sequence invariant checks (200 trades, seed 3002)", `${rob.violations} violations / ${rob.invariant_checks} checks; ${rob.commands} commands (${rob.accepted} accepted, ${rob.rejected} refused)`, "PASS", "robustness.csv"],
    ["Seeded defects detected by tests", `run 1: ${mut1Killed}/${mut1.length} → run 2: ${mutKilled}/${mut.length}`, "1 SURVIVOR", "mutation_analysis*.csv"],
    ["Role-visibility rules obeyed (core projection layer)", vd("M-08"), "PASS", "audit_access_matrix.csv"],
    ["UI ledger/export/control access by participant (HTTP tests)", "all pass; Bank H full, own-accounts for traders, metadata for regulator & Bank O, denied for logistics & customs", "PASS", "tests/test_ui_access.py"],
    ["Audit completeness (required lifecycle events)", `${auditOk}/${auditReq}; regulator reconstructs ${vd("M-07")} state paths; 0 commercial leaks`, "PASS", "audit_completeness.csv"],
    ["e-HKD two-leg cases meeting all-or-nothing", vd("M-12"), "PASS", "ehkd_results.csv"],
    ["Engine compute, TC-001 (wall-clock, not settlement time)", `median ${v("M-30")} ms`, "SANITY", "compute_time.csv"],
  ], [5.5, 5.0, 2.0, 3.5], { caption: "Table 4. Verification results (simulation results on synthetic data; denominators shown)" }),
  ...brief("report/figs/design/g_paths.png", "All three flagship trades followed their specified paths, and were refused where they should be", "results/scenarios_summary.csv; results/events/TC-00*.jsonl"),
  P(`All three flagship scenarios followed their specified paths. **TC-001**: Created → Pending → Released; exactly one release posting of HKD 250,000; escrow account back to zero; supply conserved; journal intact. **TC-002**: Created → Pending → Under Review with DOC_AMOUNT_MISMATCH. The contract's release attempt was refused (ESCROW_UNDER_REVIEW). After the corrected invoice (revision 2), a fresh document PASS and reviewer revalidation, the escrow returned to Pending and was released only after a new pre-release screening. **TC-003**: Created → Pending → Frozen with SANCTIONS_FLAG_SIMULATED. Release (ESCROW_FROZEN) and a refund by Bank H operations (ACTIVE_HOLD) were both refused. After false-positive clearance the escrow returned to Pending, and a release attempt **before** re-screening was refused (PRE_RELEASE_KYC_MISSING), confirming that clearance never jumps straight to Released (Figure 5).`),
  ...fig("presentation/assets/S_TC003_panel_v2.jpg", 9.0, "Figure 5. Prototype screenshot, TC-003: compliance view after a synthetic watchlist alert. Release guard shows ESCROW_FROZEN / ACTIVE_HOLD; HKD 250,000 remains locked (Flask console, redesigned interface, re-captured 19 Nov 2026)"),
  P(`**What the mutation analysis taught us.** Our first run detected only ${mut1Killed} of ${mut1.length} seeded defects. Two survivors were genuine gaps: no test sent a wrong shipment ID together with the correct trade ID (M06), and no test isolated the document-digest check from the revocation mechanism (M02). We added two tests and both defects are now detected. The remaining survivor (M11, removing the optimistic version check) is redundant, because writes are already serialised by BEGIN IMMEDIATE and the concurrency test still passes without it. We document it rather than claim 100%. This was the most useful single exercise in the project: passing tests alone did not prove the tests were strong.`),
  ...brief("report/figs/design/g_mutants.png", "Thirteen of fourteen planted bugs were caught, each by a named test", "results/mutation_analysis.csv (first failing test per mutant)", 16.0),
  H2("7.2 Efficiency comparison (team-defined process model; not measured industry savings)"),
  ...fig("results/charts/v3/manual_tasks.png", 13.0, "Figure 6. Manual settlement tasks per transaction — team-defined process model, not measured industry savings (open circle = hypothetical matched-scope variant)", { svg: "results/charts/v3/manual_tasks.svg" }),
  P(`Manual settlement tasks fall from ${v("M-13")} to ${v("M-14")} in the normal case (a ${v("M-15")}% reduction in the model), and from 8 to 4 in each exception class. The escrow removes four specific hand-offs: couriering documents to the importer, the importer's manual document check, the importer's payment instruction and the bank's manual payment approval. The prototype logs agree in substance: TC-001 needed ${humans.find(h => h.scenario === "TC-001").human_commands_settlement} human settlement-role commands (create and fund; upload invoice; upload bill of lading; Bank O acknowledgement), against 3 manual tasks in the model, because the prototype uploads the invoice and bill of lading as two commands. Exceptions still require one accountable human decision in both models. Escrow does not remove human judgement; it confines it to the cases that need it.`),
  ...brief("report/figs/design/g_lanes.png", "Where the manual work disappears: the importer's checks and Bank H's approval go; the exporter's paperwork stays", "results/baseline_assumptions.csv (main-path manual settlement tasks by participant)", 16.0),
  P(`**Matched scope.** The ${v("M-13")}→${v("M-14")} figure flatters the escrow, because the baseline includes a cross-border payment, Bank O's credit and the exporter's reconciliation, while the prototype ends with a HKD claim on Bank H that Bank O merely observes. When we add the steps the escrow would still need to reach the same end point (exporter redemption instruction, Bank H payment message, Bank O credit and reconciliation, re-using the baseline's own durations), manual tasks are ${v("M-13")}→${v("M-31")} (${v("M-32")}%) and post-shipment latency is ${v("M-21")}→${v("M-33")} simulated days, while the importer's cash is committed for ${v("M-34")} days. The direction of the result survives; its size roughly halves. This variant is hypothetical and not implemented.`),
  ...fig("results/charts/v3/latency.png", 12.6, "Figure 7. Post-shipment latency to exporter credit — assumption-driven model, simulated days, not bank timings (dot = base; bar = low–high)", { svg: "results/charts/v3/latency.svg" }),
  P(`Under base assumptions, post-shipment latency falls from ${T("normal", "baseline", "post_shipment_latency_d")} to ${T("normal", "proposed", "post_shipment_latency_d")} simulated days with immediate payment terms, and the escrow is unaffected by the payment term (37 days for the baseline at 30-day terms). Full cycle to exporter credit is ${v("M-28")} vs ${v("M-29")} days. Exceptions add the same 3-day review to both, so escrow keeps its advantage (${T("mismatch", "baseline", "post_shipment_latency_d")} vs ${T("mismatch", "proposed", "post_shipment_latency_d")} days). These results depend entirely on our duration assumptions, including the optimistic zero-time automated steps. They show the **structure** of the improvement, not its real size.`),
  ...fig("results/charts/v3/financing.png", 12.6, "Figure 8. Who carries the financing burden (normal scenario; assumption-driven model, incl. hypothetical matched-scope variant)", { svg: "results/charts/v3/financing.svg" }),
  P(`**H5: the trade-off is real.** Figure 8 shows that the escrow does not remove financing cost; it **moves** it. The importer's cash is committed for ${v("M-25")} days before the exporter is credited (base case; about ${Number(v("M-26")).toLocaleString("en")} HKD-days for HKD 250,000) instead of ${v("M-24")} days, because the escrow is funded before shipment. In exchange, the exporter's unsecured receivable falls from 7 days (immediate terms) or 37 days (30-day terms, ${Number(v("M-27")).toLocaleString("en")} HKD-days) to zero. Whether this is better overall depends on which party has cheaper funding and which bears more counterparty risk. For an SME exporter that struggles to obtain trade finance (the gap described in Section 1), the shift may be valuable; for an importer used to 30-day credit, it is a cost that a bank might need to finance. Fewer steps alone do not establish superiority.`),
  P(`**Sensitivity.** The chart below (full values in Table 5, Appendix D) repeats the timing comparison at the low and high ends of every assumption range. The direction of the result does not change: post-shipment latency is lower for escrow in every case, and the importer's committed time is higher in every case. Only the size of the effect depends on the assumptions.`),
  ...brief("report/figs/design/g_sensitivity.png", "Across every low–high assumption, the escrow range never overlaps the open-account range", "results/timelines.csv (post-shipment latency; bars = low–high, dot = base case)", 16.0),
  H2("7.3 Transparency, auditability and compliance coverage"),
  P(`All ${M["M-08"].denominator} role-visibility rules behaved as specified (H4). The regulator's export contained no goods descriptions, prices, user identifiers or the mismatched invoice value, yet it rebuilt the exact state path in every scenario from event metadata and reason codes. Every required lifecycle event, including the refused attempts, was present with actor, role, timestamp, reason code and hash (${auditOk}/${auditReq}), and the verifier detected both a modified amount and a deleted event (TC-018). Both compliance checkpoints were enforced: creation screening blocked an unverified party with balances unchanged (TC-005); an expired, missing or stale pre-release screening blocked release (TC-010, NC-06 to NC-08, NC-11); and an alert after an earlier PASS overrode it (TC-011).`),
  ...brief("report/figs/design/g_timeline.png", "Who did what, in order: trade TR-001 from creation to release in 12 journal entries", "results/events/TC-001.jsonl (timestamps are the simulated clock)", 16.0),
  ...brief("report/figs/design/g_journal.png", "Trade TR-001 in twelve hash-linked journal entries: three state changes, one release", "results/events/TC-001.jsonl"),
  ...brief("report/figs/design/g_audit.png", "Every required event was logged, refusals included, and the regulator rebuilt each path without commercial data", "results/audit_completeness.csv", 16.0),
  H2("7.4 Peer feedback"),
  ...peerFeedback(),

  H2("7.5 Threats to validity"),
  B("**Construct validity.** “Manual task” and “step” counts depend on how finely we drew the BPMN maps. We used the same granularity for both models and published the task lists, but another analyst could draw different maps."),
  B("**Internal validity.** We wrote both the engine and its tests. Mutation analysis and the randomised study reduce, but do not remove, the risk of shared blind spots."),
  B("**External validity.** One synthetic corridor, one currency, one trade size and four documents. Real trades involve partial shipments, amendments, multiple currencies and many more document types."),
  B("**Measurement validity.** Durations are assumptions, so time results are scenario analysis, not measurement. Wall-clock compute time reflects this laptop-scale setup and says nothing about production throughput."),
  H1("8. Discussion, Limitations and Feasibility"),
  P(`**What the prototype supports.** H2 and H3 are supported within the simulation: no unsafe path released funds in targeted tests, randomised sequences or the UI walk-through, and every exception was routed to an accountable, logged human decision. H4 is supported for our role model. H1 is supported only as a **modelled** result. H5 is confirmed as a material trade-off.`),
  P(`**Limitations that matter for real deployment.**`),
  B("**Oracle trust.** The escrow is only as reliable as its attestations. A false bill of lading, a colluding document checker or a stale sanctions list would pass our gates. Document consistency does not prove the goods' quality or existence. Real deployment needs signed, accountable attestation sources (for example electronic bills of lading or CargoX-type data [11]) and liability rules."),
  B("**Legal status of tokenised deposits and escrow.** We did not model deposit terms, ownership of escrowed tokens, segregation, insolvency treatment or deposit protection. Whether a contract-held tokenised deposit is an enforceable escrow under Hong Kong or Thai law needs legal analysis."),
  B("**Settlement finality and cross-border reality.** A database commit is not legal finality. Bank O only observes a HKD claim on Bank H. Real HK–TH settlement needs an interbank leg (for example in tokenised central-bank money [5]), FX and finality rules on both sides."),
  B("**Compliance accountability.** Our KYC/AML outcomes are synthetic inputs. Real AML/CFT obligations [13] include investigation, suspicious-transaction reporting and tipping-off controls. Our “confirmed alert → refund” rule is a simplification; a real bank might be required to keep holding the funds."),
  B("**Liquidity and pricing.** Pre-funding locks importer cash. A viable product would likely need the bank to finance or remunerate the escrow, which we did not model."),
  B("**Privacy and governance.** Role projections are enforced in code, not cryptographically. Regulator scope is a design choice that would need data-protection review in both jurisdictions."),
  B("**Operational resilience.** The prototype is a single SQLite file in one process, with no high availability, key management or independent validators. The hash chain is tamper-evident, not tamper-proof."),
  B("**Evidence base.** Durations are assumptions; there are no real users or transaction data; peer feedback is pending. Streamlit could not be installed in our build environment; the team launched it successfully on a member's laptop, but a full recorded click-through of every workflow is still pending, whereas the Flask console (redesigned on 19 Nov 2026) was exercised by an automated browser and HTTP tests."),
  B("**Why not a central database?** Everything the prototype demonstrates (guarded release, holds, role views, a hash-chained log) could be built on one shared database run by Bank H. Our code therefore does **not** show an advantage of distributed ledger consensus. The argument for DLT rests on multi-institution governance: several banks and a regulator sharing one record without trusting a single operator. That benefit appears only with independent nodes, which we did not build."),
  B("**Demo security.** The participant selector impersonates roles for a single-operator localhost demonstration; it is not authentication, and the console is not designed for shared or networked use."),
  P(`**Feasibility.** The logic itself is simple and testable, which is encouraging. The hard parts are institutional: trusted attestation sources, legal certainty for tokenised escrow, and who pays for pre-funding. These match the open issues HKMA has identified in its tokenisation work [2], [12]: interoperability across platforms [7] and policy clarity, rather than computation.`),

  H1("9. Conclusion and Future Work"),
  P(`We set out to test whether a pre-funded tokenised-deposit escrow could improve the efficiency, transparency and auditability of HK–Thailand trade settlement without weakening compliance. Within a synthetic simulation, the answer is a qualified yes. The escrow enforced every release, review and freeze rule we specified (${testsPass}/${tests.length} tests; ${negBlocked}/${negTotal} unsafe releases blocked; zero violations in ${rob.invariant_checks} randomised checks). It gave each participant, including a privacy-limited regulator, a reconstructable audit trail. In our process model it roughly halved manual settlement tasks. It does not make trade finance free: it moves financing cost from exporter to importer, and its integrity rests on off-chain attestations and legal arrangements that the prototype cannot supply.`),
  P(`**Future work:** (1) connect the shipment gate to a signed electronic bill-of-lading or cargo-data source; (2) replace the mock ledger with a permissioned DLT network having independent bank and regulator nodes; (3) add partial release, quality disputes and financing of the escrow balance; (4) extend the conceptual e-HKD leg to a multi-currency HKD–THB design that follows wholesale CBDC and tokenised-CeBM developments; and (5) collect practitioner feedback and real process timings to replace our assumptions.`),
  ...brief("report/figs/design/g_roadmap.png", "Five steps from a simulated prototype to a pilot-ready design", "Section 9 future work", 16.0),
];

const refs = [
  "[P1] FTEC3002 Group 1, “Project Proposal for a Smart-Contract DLT Trade Finance Simulation: HK–TH TradeEscrow,” CUHK, 25 Sep. 2026.",
  "[C1] CUHK Department of SEEM, “FTEC3002 Introduction to Financial Infrastructure — Course Outline,” v1.2, 2026–27.",
  "[1] HKMA, “FinTech 2030: DART,” speech by Eddie Yue, 3 Nov. 2025. https://www.hkma.gov.hk/chi/news-and-media/speeches/2025/11/20251103-2/",
  "[2] HKMA, “HKMA announces the new phase of Project Ensemble to support real-value transactions in tokenised deposits and digital assets,” press release, 13 Nov. 2025. https://www.hkma.gov.hk/eng/news-and-media/press-releases/2025/11/20251113-3/",
  "[3] HKMA, “Central Bank Digital Currency (CBDC).” https://www.hkma.gov.hk/eng/key-functions/international-financial-centre/fintech/central-bank-digital-currency/",
  "[4] BIS Innovation Hub, “Project mBridge.” https://www.bis.org/project/mbridge (accessed 7 Nov. 2026).",
  "[5] HKMA, “HKMA advances Project Ensemble pilot phase to 24/7 settlement in tokenised Central Bank Money,” press release, 2 Nov. 2026. https://www.hkma.gov.hk/eng/news-and-media/press-releases/2026/11/20261102-5/",
  "[6] Export-Import Bank of Thailand, “EXIM Thailand Inks MOU with Hong Kong Trade Development Council to Foster Thailand–Hong Kong Trade and Investment,” 23 Feb. 2024 (accessed 8 Nov. 2026). https://www.exim.go.th/EN/Newsroom/newsactivities/EXIM-BANK-%E0%B8%A5%E0%B8%87%E0%B8%99%E0%B8%B2%E0%B8%A1-MOU-%E0%B8%81%E0%B8%9A%E0%B8%AD%E0%B8%87%E0%B8%84%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%AA%E0%B8%A0%E0%B8%B2%E0%B8%9E%E0%B8%92%E0%B8%99%E0%B8%B2%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%84%E0%B8%B2%E0%B8%AE%E0%B8%AD%E0%B8%87%E0%B8%81%E0%B8%87-%E0%B8%AA%E0%B8%99%E0%B8%9A%E0%B8%AA.aspx",
  "[7] E. Yue, “Connecting the digital islands — next steps in trade finance,” speech, BIS, 26 Jan. 2022. https://www.bis.org/speeches/20220126-connecting-digital-islands-next-steps-trade-finance",
  "[8] Asian Development Bank, “Global Trade Finance Gap Widened to $1.7 Trillion in 2020,” news release, 12 Oct. 2021. https://www.adb.org/news/global-trade-finance-gap-widened-17-trillion-2020",
  "[9] Asian Development Bank, “Demand for Trade Finance to Rise Amid Supply Chain Realignment—ADB Report,” news release, 15 Jan. 2026. https://www.adb.org/news/demand-trade-finance-rise-amid-supply-chain-realignment-adb-report",
  "[10] HKMA, “Project CargoX Recommendation Report,” published 19 Jan. 2026, p. 16 (the 2024 gap is an estimated range derived from KPMG desktop research, not a direct count and not SME-only). https://cdi.hkma.gov.hk/wp-content/uploads/Project_CargoX_Recommendation_Report.pdf",
  "[11] HKMA, “HKMA launches CargoX Pilot Programme,” press release, 7 May 2026. https://www.hkma.gov.hk/eng/news-and-media/press-releases/2026/05/20260507-7/",
  "[12] HKMA, “HKMA completes e-HKD Pilot Programme and outlines future direction of e-HKD” (e-HKD Pilot Programme Phase 2 Report), 28 Oct. 2025 (Phase 2 primarily tested retail use cases; the wholesale/FI direction is HKMA's stated strategy, not a Phase 2 result). https://www.hkma.gov.hk/eng/news-and-media/press-releases/2025/10/20251028-4/",
  "[13] HKMA, “Anti-Money Laundering and Counter-Financing of Terrorism.” https://www.hkma.gov.hk/eng/key-functions/banking/anti-money-laundering-and-counter-financing-of-terrorism/",
  "[14] Object Management Group, “Business Process Model and Notation (BPMN), Version 2.0.2,” 2014. https://www.omg.org/spec/BPMN/2.0.2",
  "[15] R. E. Duran, Financial Services Technology: TradFi, Fintech and DeFi, 3rd ed. Singapore: Cengage Learning Asia, 2024 (Ch. 11, Trade Services and Finance).",
  "[16] ISO 20022, “Message Definitions.” https://www.iso20022.org/iso-20022-message-definitions (release events use ISO 20022-inspired mock fields only, not schema-validated messages).",
  "[17] Anthropic, Claude (Opus 5.5), https://claude.ai, used Nov. 2026 (see Appendix F).",
];

const REFLECTIONS = {
  "Wong Ho Ming, Michael": [
    "**What I did.** I carried most of the project from design to delivery. I designed the escrow logic: the six states, the fifteen permitted transitions and the seven-check release guard. I built the Python engine, both interfaces (the Streamlit app and the Flask console) and the hash-chained journal. I wrote the 77 automated tests, the 17 unsafe-release attacks, the 200-trade randomised stress test and the mutation analysis. I drew the baseline and escrow BPMN models and built the timing and liquidity comparison. I also produced this report and the final slide deck, including every diagram and chart, and I present the evidence section of our talk: the tests, the attacks, the stress test and the evidence scorecard.",
    "**Planning.** I fixed the process durations and their low–high ranges before running any comparison, so the result could not be tuned toward the escrow. I also labelled every claim by evidence level (tested, modelled or assumed), which kept us honest about what a simulation can prove.",
    "**A problem I faced.** In the final review I found that our stress test was green for the wrong reason. It reported 0 of 5,427 random commands accepted: after a change to the engine's call signature, the test harness was still calling it the old way, and every error was counted as a safe refusal. I made harness errors fail loudly and re-ran the study. Now 2,206 of 5,312 commands are accepted, with 0 invariant violations in 5,935 checks. Mutation testing taught the same lesson: my tests first caught 11 of 14 planted bugs, and 13 after I added two tests. A passing test proves little until you have seen it fail for the right reason.",
    "**Feedback and response.** Our 8 November review found that the Flask ledger page could show data without going through the role projections. I routed every page through the projection layer and added 30 access-control tests. I also cut our efficiency headline from 7→3 to a matched-scope 7→5 once I saw that the original comparison flattered the escrow.",
    "**What I learned.** An escrow is only as trustworthy as its attestations. Pre-funding does not remove liquidity cost; it moves it from exporter to importer. And when funds are frozen, the system must name a person who decides.",
    "**What I would do differently.** Agree a clearer division of work at the start, and collect peer and practitioner feedback before building the final deck rather than after.",
  ],
};
const reflection = (name) => REFLECTIONS[name] ? [
  H2(`10.${members.findIndex(m => m[0] === name) + 1} ${name}`),
  ...REFLECTIONS[name].map(t => P(t)),
] : [
  H2(`10.${members.findIndex(m => m[0] === name) + 1} ${name}`),
  P("**[TO BE WRITTEN BY THIS MEMBER IN THEIR OWN WORDS — about 250–350 words. Do not submit this placeholder.]**", { run: { color: "B91C1C" } }),
  P("Suggested prompts (course outline §10: planning, design and evaluation): (1) What did I actually do on this project, and what evidence shows it? (2) One problem I faced and how it was resolved. (3) One piece of instructor or peer feedback and how we responded. (4) What I learned about financial-infrastructure risk, such as oracle trust, pre-funding liquidity, settlement finality or compliance accountability. (5) What I would do differently.", { run: { size: 19, color: GREY, italics: true } }),
];

const appendixH = [
  H1("Appendix H. Full-Size Figures"),
  P("The four diagrams below are reproduced at full page width so they can be read without zooming. They are rendered at 300 dpi, so they also stay sharp when enlarged."),
  ...fig("report/figs/architecture.png", 24.0, "Figure H1 (= Figure 1). Architecture and trust boundaries"),
  PB(),
  ...fig("diagrams/report/state_machine_slide.png", 24.0, "Figure H2 (= Figure 2). Six-state escrow machine (15 permitted transitions, matching tradeescrow/model.py TRANSITIONS; all others rejected)"),
  PB(),
  ...fig("diagrams/report/baseline_bpmn_slide.png", 24.0, "Figure H3 (= Figure 3). Baseline BPMN: traditional open-account settlement"),
  PB(),
  ...fig("diagrams/report/proposed_bpmn_slide.png", 24.0, "Figure H4 (= Figure 4). Proposed BPMN: pre-funded escrow with off-chain attestations"),
];
const appendices = [
  H1("Appendix A. Where Each Assessment Element Is Addressed"),
  ...brief("report/figs/design/g_metrics.png", "Six metric families, and the headline result for each", "results/metrics.csv (M-01 to M-34); TESTED = executed on the prototype, MODELLED = process/timing model", 16.0),

  ...table(["Element (course outline)", "Where in this report", "Main evidence"], [
    ["Background and motivation", "§1.1, Part 1 opener", "HK–Thailand trade context [6]; exporter risk 7 / 37 days (modelled)"],
    ["Weaknesses of current implementations", "§1.2, §2", "Four weaknesses mapped onto the open-account process; Table 1 gap analysis"],
    ["Innovative elements", "§4.1", "Guarded release, compliance-by-design, attestation pinning, role-limited audit, hash-chained journal"],
    ["System design", "§4–5, Figures 1–2", "Six states, 15 transitions, seven release checks, permission matrix (Table 3, Appendix C)"],
    ["Experimentation (pilot experiments)", "§6, Figures 3–4", `${tests.length} tests, 17 attacks, 200 random trades, 14 mutants, BPMN comparison`],
    ["Outcome evaluation", "§7–8", "Table 4; Figures 6–8; sensitivity ranges; threats to validity; evidence ladder"],
    ["Feedback collection and response", "§7.4, Appendix G", "Peer questionnaire (instrument and results); changes from the proposal"],
    ["Individual self-reflections", "§10 (inside the 15-page body)", "One reflection per member on planning, design and evaluation"],
  ], [4.4, 4.0, 8.2], { caption: "Table A1. Assessment elements and where they are covered", size: 16 }),
  H1("Appendix B. Test Case Matrix (TC-001 to TC-024)"),
  ...brief("report/figs/design/g_appB.png", `${tests.length} automated tests pass; 200 random trades ended in every reachable state without an invariant violation`, "results/test_results.csv; results/robustness.csv", 16.0),
  ...table(["ID", "Scenario", "Actual result", "Status"], parseCSV("requirements/test_cases.csv").map(r => [r.test_id, r.scenario, r.actual_state_path, r.status]),
    [1.6, 5.0, 7.8, 1.6], { caption: "Table B1. Executed test cases (requirements/test_cases.csv; run of record in results/run_manifest.json)", size: 16 }),
  H1("Appendix C. Permissions and Unsafe-Release Control Matrix"),
  ...table(["Role", "May issue (server-side)", "Explicitly refused (tested)"], [
    ["HK importer", "create & fund escrow (own trade); upload contract; raise dispute", "release; compliance decisions; other trades' data (TC-017)"],
    ["Thai exporter", "submit invoice / bill of lading (own trade); raise dispute", "clear AML hold, run screening, release (TC-015)"],
    ["Bank H operations", "run document check; revalidate or terminate reviews; trigger release (guard decides)", "terminate while an AML hold is active (TC-014)"],
    ["Bank H compliance", "run screening; raise / clear / confirm holds", "release directly after clearance (TC-023)"],
    ["Thai Bank O", "acknowledge receipt (observation only)", "any fund movement"],
    ["Logistics / Customs", "shipment attestation / customs declaration", "attest another trade's shipment (TC-007)"],
    ["Regulator", "read metadata-only audit export", "every state-changing command (TC-016)"],
  ], [3.0, 6.9, 6.1], { caption: "Table 3. Command permissions (complete matrix in docs/domain_model.md)" }),

  ...brief("report/figs/design/g_attacks.png", "How the 17 unsafe release attempts were refused, by the first failing check", "results/control_matrix.csv (NC-01 to NC-17); colour = which check refused it", 16.0),
  ...table(["ID", "Unsafe condition", "Actor", "Blocked", "Reason code"], ctrl.map(c => [c.control_id, c.unsafe_condition, c.actor, c.blocked === "True" ? "yes" : "no (expected for PC-01)", c.reason_code]),
    [1.5, 6.4, 2.6, 2.5, 3.0], { caption: "Table C1. results/control_matrix.csv", size: 16 }),
  H1("Appendix D. Comparison Tables and Process Model Assumptions"),
  ...table(["Dimension", "Open account (baseline)", "Documentary credit (L/C)", "Pre-funded escrow (this project)"], [
    ["When the exporter is paid", "At the end of the credit term after shipment", "On presentation of complying documents", "Automatically, once all three gates pass after shipment"],
    ["Who bears non-payment risk", "Exporter (unsecured receivable)", "Issuing bank (and confirming bank, if any)", "Largely removed: funds locked before shipment"],
    ["Who funds the trade", "Exporter extends credit", "Importer's bank credit line / collateral", "Importer pre-funds (cash committed early)"],
    ["Document checking", "Importer, manually", "Banks, manually under UCP 600 rules", "Automated field matching + human review on mismatch"],
    ["Compliance timing", "At payment, inside each bank", "At issuance and presentation", "At creation and fresh before release; holds freeze funds"],
    ["Audit trail", "Fragmented across parties", "Bank records; paper-heavy", "Shared hash-chained journal; role-limited views"],
  ], [3.2, 4.2, 4.2, 4.4], { caption: "Table 2. Qualitative comparison of settlement options (not a project measurement)", size: 16 }),
  ...table(["Boundary", "Baseline (open account)", "Escrow, prototype scope", "Escrow + hypothetical cross-bank leg"], [
    ["Process starts", "Contract signed", "Contract signed", "Contract signed"],
    ["Importer funds committed", "Payment instruction after document check", "Escrow funded before shipment", "Escrow funded before shipment"],
    ["Settlement ends", "Bank O credits exporter; exporter reconciles", "Bank H releases a synthetic HKD claim; Bank O only acknowledges", "Exporter redeems; Bank H pays Bank O; Bank O credits; exporter reconciles (not implemented)"],
    ["Manual settlement tasks, normal", v("M-13"), v("M-14"), v("M-31")],
    ["Excluded in all models", "FX conversion, fees, legal finality, goods/customs/carriage (common)", "same", "same"],
  ], [3.2, 4.1, 4.1, 4.6], { caption: "Table 3a. Comparison boundaries (team-defined process model; hypothetical steps re-use the baseline's own durations for B10–B12)", size: 16 }),

  ...table(["Scenario", "Assumptions", "Post-shipment latency: baseline (term 0d / 30d)", "Post-shipment latency: escrow", "Importer funds committed: baseline", "Importer funds committed: escrow"],
    ["normal", "mismatch", "aml"].flatMap(sc => ["low", "base", "high"].map(l => [sc, l,
      `${T(sc, "baseline", "post_shipment_latency_d", l, "0")} / ${T(sc, "baseline", "post_shipment_latency_d", l, "30")}`,
      T(sc, "proposed", "post_shipment_latency_d", l), T(sc, "baseline", "importer_funds_committed_d", l), T(sc, "proposed", "importer_funds_committed_d", l)])),
    [2.0, 2.0, 3.6, 2.6, 2.9, 2.9], { caption: "Table 5. Sensitivity of modelled durations (simulated days; results/timelines.csv)", size: 16 }),

  ...table(["Model", "Task", "Kind", "Segment", "Path", "Days low / base / high"], parseCSV("results/baseline_assumptions.csv").map(r => [r.model, `${r.task_id} ${r.task}`, r.kind, r.segment, r.path, `${r.dur_low_d} / ${r.dur_base_d} / ${r.dur_high_d}`]),
    [1.8, 6.0, 2.4, 2.1, 1.6, 2.1], { caption: "Table D1. All durations are team assumptions fixed before the comparison; automated steps = 0 days (optimistic)", size: 15 }),
  H1("Appendix E. Reproducibility and Artefact Index"),
  B("Install: pip install -r requirements.txt (Python ≥ 3.11; tested 3.13). Tests: python -m pytest -q. Evidence: python scripts/run_experiments.py (regenerates results/ in about 10 s)."),
  B("Documents and decks: npm install (Node ≥ 20; versions pinned in package.json), then npm run build:report (needs LibreOffice and poppler-utils), npm run build:interim, npm run build:final."),
  B("Interfaces: streamlit run ui_streamlit/streamlit_app.py; fallback python -m ui_flask.app (http://127.0.0.1:5050)."),
  B("Diagrams: diagrams/baseline.bpmn, proposed.bpmn (BPMN 2.0 with diagram interchange [14]), state_machine.svg, architecture.svg. Pseudocode: docs/TradeEscrow_pseudocode.sol."),
  B(`Run of record: ${manifest.run_finished_utc}; code hash ${manifest.code_sha256_16}; fixture ${manifest.fixture_version}; Python ${manifest.python}.`),
  H1("Appendix F. Use of Generative AI (course Approach 3)"),
  P("**[TEAM TO REVIEW AND CONFIRM THIS STATEMENT IS ACCURATE BEFORE SUBMISSION.]**", { run: { color: "B91C1C" } }),
  P("We acknowledge the use of Claude (Anthropic, https://claude.ai) [17] to help implement the prototype code, tests and diagrams, run the experiments, draft this report and the presentation slides, and check public sources. Earlier, ChatGPT was used to plan the proposal structure, as acknowledged in the proposal. All AI-assisted content was reviewed by group members, and all reported numbers come from the executed experiment outputs in the project repository. The main instruction given to Claude was a project execution brief asking it to implement, test and document the HK–TH TradeEscrow prototype described in our submitted proposal, using only synthetic data and without fabricating results."),
  P("Citation: Anthropic. (2026). Claude (Opus 5.5) [Large language model]. https://claude.ai"),
  H1("Appendix G. Changes from the Proposal"),
  B("Added a Flask console alongside the proposed Streamlit app, on the same engine, as a verified fallback demo."),
  B("Redesigned the Flask console (19 Nov 2026): monochrome theme with light/dark modes, animations of the release guard, token movements and state changes driven only by journalled results, step-by-step scenario replay and a journal-tamper demonstration; 14 regression tests added (77 to 91). Engine rules, data and all other metrics are unchanged."),
  B("Bank H's compliance officer is modelled as a distinct principal within Bank H, so the seven participants are unchanged."),
  B("Added mutation analysis and randomised robustness testing beyond the proposal's measurement plan."),
  B("Corrected the CargoX Recommendation Report date (19 Jan 2026) and added post-proposal context (ADB 2025 gap [9]; EnsembleTX 24/7 CeBM [5]; CargoX pilot [11])."),
  B("Peer feedback (§7.6): pending at the time of writing (see Section 7.4)."),
];

// ------------------------------------------------------------------ page furniture
const MARG = { page: { margin: { top: 1330, bottom: 1250, left: 1080, right: 1080, header: 0, footer: 440 } } };
const FRAMES = { band_front: "frame_front", band_body: "frame_body", band_app: "frame_app", band_app_land: "frame_app_land" };
function band(name, wcm = 21) {
  const f = FRAMES[name] || name;
  const buf = fs.readFileSync(path.join(ROOT, `report/figs/design/${f}.png`)); const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20); const px = wcm / 2.54 * 96;
  return new Header({ children: [new Paragraph({ spacing: { before: 0, after: 0 }, children: [new ImageRun({ type: "png", data: buf, transformation: { width: px, height: px * h / w },
    altText: { title: "page frame", description: "HK–TH TradeEscrow running head, ledger spine and footer rule", name: f },
    floating: { horizontalPosition: { relative: HorizontalPositionRelativeFrom.PAGE, offset: 0 }, verticalPosition: { relative: VerticalPositionRelativeFrom.PAGE, offset: 0 },
      behindDocument: true, allowOverlap: true } })] })] });
}
function footBlank() { return new Footer({ children: [new Paragraph({ children: [] })] }); }
function foot(label, right = 9746) {
  // page number as a navy tab on the footer rule; the label text is part of the page frame image
  return new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { before: 0, after: 0 }, children: [
    new TextRun({ text: "PAGE  ", font: FONT, size: 13, bold: true, color: MUTE, characterSpacing: 40 }),
    new TextRun({ children: [PageNumber.CURRENT], font: HFONT, size: 24, bold: true, color: NAVY })] }),
  ] });
}
const opener = k => { if (NOFIG) return new Paragraph({ text: "" }); const buf = fs.readFileSync(path.join(ROOT, `report/figs/design/opener_p${k}.png`)); const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20); const px = 13.0 / 2.54 * 96;
  return new Paragraph({ spacing: { before: 120, after: 100 }, keepNext: true, children: [new ImageRun({ type: "png", data: buf, transformation: { width: px, height: px * h / w },
    altText: { title: `Part ${k} opener`, description: `Part ${k} opener with headline numbers`, name: `opener_p${k}` } })] }); };
const PARTNAMES = ["WHY ESCROW", "THE DESIGN", "THE EVIDENCE", "THE VERDICT"];
const BODYFLAT = body.flat(3);
const cut = ["4. ", "6. ", "8. "].map(pfx => BODYFLAT.findIndex(x => x && x._h1 && x._h1.startsWith(pfx)));
const PARTS = [BODYFLAT.slice(0, cut[0]), BODYFLAT.slice(cut[0], cut[1]), BODYFLAT.slice(cut[1], cut[2]), BODYFLAT.slice(cut[2])];
// Section 10: individual self-reflections sit inside the counted body (course outline §10)
PARTS[3].push(...[H1("10. Individual Self-Reflections"),
  P("Each member reflects on project planning, design and evaluation. Contributions are attributed only as each member confirms them."),
  ...members.flatMap(([n]) => reflection(n))].flat(3));

// ------------------------------------------------------------------ document
const doc = new Document({
  creator: "FTEC3002 Group 1", title: "HK–TH TradeEscrow — Final Project Report", description: "FTEC3002 Group 1 final report",
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 20, color: INK } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: HFONT, size: 30, bold: true, color: NAVY }, paragraph: { spacing: { before: 260, after: 120 }, keepNext: true, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: HAIR, space: 6 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: HFONT, size: 23, bold: true, color: NAVY }, paragraph: { spacing: { before: 200, after: 80 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 500, hanging: 260 } } } },
                                 { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 900, hanging: 260 } } } }] },
    { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 500, hanging: 300 } } } }] },
  ] },
  sections: [
    { properties: ART_PAGE, children: cover },
    { properties: ART_PAGE, children: glance },
    { properties: MARG, headers: { default: band("frame_front") }, footers: { default: footBlank() }, children: [...toc, ...exec].flat(3) },
    { properties: { ...MARG, page: { ...MARG.page, pageNumbers: { start: 1 } } }, headers: { default: band("frame_body") }, footers: { default: foot("") },
      children: PARTS.flatMap((ch, i) => [opener(i + 1), ...ch]) },
    { properties: MARG, headers: { default: band("frame_app") }, footers: { default: footBlank() },
      children: [H1("References"), ...refs.map(r => new Paragraph({ children: runs(r, { size: 18 }), spacing: { after: 70 }, indent: { left: 400, hanging: 400 } })),
        ...appendices.flat(3)] },
    { properties: { page: { size: { orientation: PageOrientation.LANDSCAPE }, margin: { top: 1300, bottom: 1250, left: 1100, right: 1100, header: 0, footer: 440 } } },
      headers: { default: band("band_app_land", 29.7) }, footers: { default: footBlank() },
      children: appendixH.flat(3) },
  ],
});
Packer.toBuffer(doc).then(buf => { const out = process.env.OUT_DOCX || path.join(ROOT, "report", "FTEC3002_Group1_Final_Report.docx"); fs.writeFileSync(out, buf); console.log("wrote", out); });
