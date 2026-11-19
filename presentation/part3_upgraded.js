// PART 3 — THE EVIDENCE (slides 9–12), upgraded. Presented by WONG HO MING.
// Inserted into build_final_paper.js; all figures read from results/ (run of record).
module.exports = async function part3(ctx) {
  const { pres, page, T, L, R, I, pill, img, K, SERIF, SANS, MONO, D, md, mv, W, H, MX, V } = ctx;
  const rob = Object.fromEntries(D.readCSV("results/robustness.csv").map(r => [r.metric, r.value]));
  const ctrl = D.readCSV("results/control_matrix.csv");
  const mut = D.readCSV("results/mutation_analysis.csv");
  const tests = D.readCSV("results/test_results.csv");
  const ST = { Created: "64748B", Pending: "B7791F", "Under Review": "C2410C", Frozen: "2F5E9E", Released: "15803D", "Refunded/Terminated": "6B4FA0", "No escrow": "A8A29E" };
  const N = x => Number(x).toLocaleString("en");
  let s;

  // ─────────────────────────────── 9 · LIVE DEMO
  s = page(pres, { part: 2, presenter: true, title: "Live: one engine, four moments to watch", sub: "Same trade, different people at the keyboard — watch what each one is allowed to do", tag: "DEMO" });
  const lw = 7.1, lx = MX - 0.05, ly = 1.85, lh = lw * 1560 / 2400;
  s.addImage({ path: V("ink/laptop.png"), x: lx, y: ly, w: lw, h: lh, objectName: "!!laptop" });
  const fr = [0.14416666666666667, 0.06794871794871794, 0.7116666666666667, 0.7038461538461539];
  const sx = lx + fr[0] * lw, sy = ly + fr[1] * lh, sw = fr[2] * lw, sh = fr[3] * lh;
  D.fit(s, "presentation/assets/S_TC001_panel.jpg", sx, sy, sw, sh, { valign: "top", alt: "TradeEscrow console, TC-001" });
  // annotations on the real screen: what each part means
  const ann = [["A", 0.05, 0.08, "lifecycle — where the trade is now"], ["B", 0.72, 0.30, "release guard — every check, live"], ["C", 0.66, 0.167, "ledger — supply conserved"]];
  ann.forEach(([k, fx, fy, txt], i) => {
    const cx = sx + fx * sw, cy = sy + fy * sh;
    R(s, pres, cx - 0.15, cy - 0.15, 0.3, 0.3, { oval: true, fill: K.gold, line: K.paper, lw: 1.5, name: "ann" + k });
    T(s, k, { x: cx - 0.15, y: cy - 0.15, w: 0.3, h: 0.3, fontSize: 10, bold: true, color: K.paper, align: "center", valign: "middle", fontFace: SERIF });
    const kx = MX + i * 2.45;
    R(s, pres, kx, ly + lh + 0.07, 0.24, 0.24, { oval: true, fill: K.gold, line: null });
    T(s, k, { x: kx, y: ly + lh + 0.07, w: 0.24, h: 0.24, fontSize: 8.5, bold: true, color: K.paper, align: "center", valign: "middle", fontFace: SERIF });
    T(s, txt, { x: kx + 0.3, y: ly + lh + 0.06, w: 2.15, h: 0.26, fontSize: 9, italic: true, color: K.ink2, fontFace: SERIF, valign: "middle" });
  });
  // demo route — a drawn line with four stops
  const rx = 8.05, rw = W - MX - rx, top = 1.95;
  T(s, "THE ROUTE", { x: rx, y: top, w: 3, h: 0.24, fontSize: 9.5, bold: true, color: K.teal, charSpacing: 2.5 });
  const stops = [
    ["Building2", "Bank H ops", "TC-001 · clean trade", [["Created", "Created"], ["Pending", "Pending"], ["Released", "Released"]], "guard turns all green; one release, supply unchanged", K.teal],
    ["Eye", "Regulator", "presses “Release funds”", null, "refused: RBAC_DENIED — and the refusal is journalled", K.violet],
    ["FileWarning", "Bank H reviewer", "TC-002 · invoice HKD 245,000", [["Pending", "Pending"], ["Under Review", "Review"], ["Released", "Released"]], "mismatch → human review → fresh gates → release", K.red],
    ["Snowflake", "Bank H compliance", "TC-003 · watchlist hit", [["Pending", "Pending"], ["Frozen", "Frozen"]], "release and refund both refused until compliance decides", K.blue]];
  const sh2 = 1.13, lineX = rx + 0.2;
  L(s, pres, lineX, top + 0.5, lineX, top + 0.4 + 3 * sh2 + 0.2, K.ink2, 2, { name: "route" });
  for (let i = 0; i < 4; i++) {
    const [ic, who, what, path_, out, col] = stops[i], y = top + 0.38 + i * sh2;
    R(s, pres, lineX - 0.2, y, 0.4, 0.4, { oval: true, fill: K.paper, line: col, lw: 2, name: "stop" + i });
    await I(s, ic, col, lineX - 0.12, y + 0.08, 0.24);
    T(s, [{ text: "acting as  ", options: { italic: true, color: K.mute } }, { text: who, options: { bold: true, color: col } }], { x: rx + 0.55, y: y - 0.03, w: rw - 0.55, h: 0.24, fontSize: 9.5, fontFace: SERIF });
    T(s, what, { x: rx + 0.55, y: y + 0.2, w: rw - 0.55, h: 0.28, fontSize: 12.5, bold: true, color: K.ink, fontFace: SERIF });
    if (path_) {
      path_.forEach(([st, lab], k) => {
        const px = rx + 0.55 + k * 1.05;
        R(s, pres, px, y + 0.53, 0.9, 0.24, { r: 0.12, fill: ST[st], line: null });
        T(s, lab, { x: px, y: y + 0.53, w: 0.9, h: 0.24, fontSize: 8, bold: true, color: K.paper, align: "center", valign: "middle" });
        if (k < path_.length - 1) T(s, "›", { x: px + 0.88, y: y + 0.5, w: 0.2, h: 0.28, fontSize: 12, bold: true, color: K.mute, align: "center" });
      });
    } else {
      R(s, pres, rx + 0.55, y + 0.52, 1.6, 0.27, { fill: K.redL, line: K.red, lw: 1 });
      T(s, "RBAC_DENIED", { x: rx + 0.55, y: y + 0.52, w: 1.6, h: 0.27, fontSize: 9.5, bold: true, color: K.red, fontFace: MONO, align: "center", valign: "middle" });
    }
    T(s, out, { x: rx + 0.55, y: y + 0.8, w: rw - 0.55, h: 0.3, fontSize: 9, italic: true, color: K.sub, fontFace: SERIF });
  }
  s.addNotes("(2–3 min) LIVE DEMO — run: python -m ui_flask.app. Before starting, point at A (lifecycle), B (release guard) and C (ledger line) on the screen so the audience knows where to look.\n1) As Bank H ops, TC-001 Auto-play: the guard turns green, one release, supply unchanged.\n2) Switch to Regulator, press Try to release funds: RBAC_DENIED, and show the refusal in the journal — the regulator can see but never move money.\n3) TC-002: invoice says HKD 245,000 against a 250,000 contract → Under Review; exporter corrects, reviewer revalidates, fresh screening, release.\n4) TC-003: watchlist hit → Frozen; try refund → refused.\nFallback: recorded video, then backup B6.");

  // ─────────────────────────────── 10 · FOUR WAYS WE TRIED TO BREAK IT
  s = page(pres, { part: 2, presenter: true, title: "Four ways we tried to break it", sub: "Each panel: what we threw at the engine, and what came back", tag: "TEST" });
  const pw = (W - 2 * MX - 0.45) / 4, py = 1.85, ph = 4.55;
  const heads = [["CheckCheck", "THE SUITE", md("M-01"), "tests pass"], ["ShieldAlert", "ATTACKS ON RELEASE", md("M-04"), "refused, funds unchanged"],
    ["Shuffle", "RANDOM STRESS", `0 / ${N(rob.invariant_checks)}`, "invariant violations"], ["Bug", "SEEDED BUGS", md("M-11"), "caught by the suite"]];
  for (let i = 0; i < 4; i++) {
    const x = MX + i * (pw + 0.15), [ic, hd, big, lb] = heads[i];
    R(s, pres, x, py, pw, ph, { fill: K.card, line: K.rule, name: "pan" + i });
    await I(s, ic, K.teal, x + 0.18, py + 0.16, 0.26);
    T(s, hd, { x: x + 0.52, y: py + 0.17, w: pw - 0.6, h: 0.24, fontSize: 8.5, bold: true, color: K.teal, charSpacing: 2 });
    L(s, pres, x + 0.18, py + ph - 0.98, x + pw - 0.18, py + ph - 0.98, K.rule, 0.5, { dash: "dash" });
    T(s, big, { x: x + 0.18, y: py + ph - 0.92, w: pw - 0.3, h: 0.5, fontSize: big.length > 6 ? 23 : 28, bold: true, color: K.ink, fontFace: SERIF, valign: "middle" });
    T(s, lb, { x: x + 0.18, y: py + ph - 0.42, w: pw - 0.3, h: 0.26, fontSize: 10.5, italic: true, color: K.sub, fontFace: SERIF });
  }
  // panel 1 — what the 77 tests cover (real counts by module)
  let x = MX;
  const mods = [["Escrow engine", tests.filter(t => t.test_name.startsWith("tests.test_escrow")).length, K.teal, "gates, states, roles, idempotency, hash chain"],
                ["Web UI, per role", tests.filter(t => t.test_name.startsWith("tests.test_ui_access")).length, K.violet, "every participant hits every page"],
                ["e-HKD two-leg", tests.filter(t => t.test_name.startsWith("tests.test_ehkd")).length, K.blue, "commit / roll back / recover"]];
  const tot = mods.reduce((a, m) => a + m[1], 0), bw = pw - 0.36;
  let bx = x + 0.18;
  mods.forEach(([, n, col]) => { R(s, pres, bx, py + 0.6, bw * n / tot, 0.3, { fill: col, line: K.paper, lw: 1 }); bx += bw * n / tot; });
  mods.forEach(([nm, n, col, d], k) => {
    const y = py + 1.1 + k * 0.7;
    R(s, pres, x + 0.18, y + 0.06, 0.14, 0.14, { fill: col, line: null });
    T(s, [{ text: `${n}  `, options: { bold: true, color: col, fontFace: SERIF } }, { text: nm, options: { bold: true, color: K.ink } }], { x: x + 0.4, y, w: pw - 0.5, h: 0.26, fontSize: 11 });
    T(s, d, { x: x + 0.4, y: y + 0.26, w: pw - 0.5, h: 0.36, fontSize: 9, italic: true, color: K.mute, fontFace: SERIF });
  });
  T(s, "since the interim: 47 → 77", { x: x + 0.18, y: py + 3.25, w: pw - 0.3, h: 0.24, fontSize: 9, bold: true, color: K.gold });
  // panel 2 — the 17 attacks bouncing off the guard (real control list)
  x = MX + (pw + 0.15);
  const wallX = x + pw - 0.5;
  s.addImage({ path: V("ink/guard_wall.png"), x: wallX, y: py + 0.55, w: 0.28, h: 2.95 });
  const nc = ctrl.filter(c => c.control_id.startsWith("NC"));
  const short = { "NC-01": "no shipment proof", "NC-02": "documents never checked", "NC-03": "document mismatch", "NC-04": "customs field missing", "NC-05": "docs revised after approval",
    "NC-06": "no pre-release screen", "NC-07": "screening 49 h old", "NC-08": "screen older than approval", "NC-09": "AML alert (Frozen)", "NC-10": "manual hold added",
    "NC-11": "hold cleared, no re-screen", "NC-12": "second release", "NC-13": "already refunded", "NC-14": "regulator presses release", "NC-15": "exporter presses release",
    "NC-16": "importer presses release", "NC-17": "another trade's shipment" };
  nc.forEach((c, k) => {
    const y = py + 0.56 + k * 0.172;
    T(s, [{ text: c.control_id.slice(3) + " ", options: { bold: true, color: K.red, fontFace: MONO } }, { text: short[c.control_id] || c.unsafe_condition, options: { color: K.ink2 } }],
      { x: x + 0.12, y, w: wallX - x - 0.4, h: 0.17, fontSize: 7.2, valign: "middle" });
    L(s, pres, wallX - 0.3, y + 0.085, wallX - 0.03, y + 0.085, c.blocked === "True" ? K.red : K.teal, 0.9, { head: true });
  });
  // panel 3 — random stress: what the 200 trades actually went through
  x = MX + 2 * (pw + 0.15);
  img(s, "dice", x + 0.16, py + 0.52, 0.62, 380 / 640);
  T(s, `${N(rob.trades)} trades · ${N(rob.commands)} random commands, any role`, { x: x + 0.85, y: py + 0.5, w: pw - 0.95, h: 0.42, fontSize: 9, italic: true, color: K.ink2, fontFace: SERIF });
  const acc = +rob.accepted, rej = +rob.rejected, aw2 = pw - 0.36;
  R(s, pres, x + 0.18, py + 1.05, aw2 * acc / (acc + rej), 0.22, { fill: K.teal, line: null });
  R(s, pres, x + 0.18 + aw2 * acc / (acc + rej), py + 1.05, aw2 * rej / (acc + rej), 0.22, { fill: K.red, tr: 30, line: null });
  T(s, [{ text: `${N(acc)} accepted`, options: { color: K.teal, bold: true } }, { text: `   ${N(rej)} refused`, options: { color: K.red, bold: true } }], { x: x + 0.18, y: py + 1.3, w: aw2, h: 0.22, fontSize: 8.5 });
  T(s, "where the 200 trades ended", { x: x + 0.18, y: py + 1.6, w: aw2, h: 0.2, fontSize: 8.5, italic: true, color: K.mute, fontFace: SERIF });
  const fin = Object.keys(rob).filter(k => k.startsWith("final_state::")).map(k => [k.slice(13), +rob[k]]).sort((a, b) => b[1] - a[1]);
  let fx = x + 0.18;
  fin.forEach(([st, n]) => { const w2 = aw2 * n / +rob.trades; R(s, pres, fx, py + 1.83, w2, 0.22, { fill: ST[st] || K.mute, line: K.paper, lw: 0.75 }); fx += w2; });
  fin.forEach(([st, n], k) => {
    const cx2 = x + 0.18 + (k % 2) * (aw2 / 2), cy = py + 2.13 + Math.floor(k / 2) * 0.22;
    R(s, pres, cx2, cy + 0.05, 0.11, 0.11, { fill: ST[st] || K.mute, line: null });
    T(s, `${st === "Refunded/Terminated" ? "Refunded" : st} ${n}`, { x: cx2 + 0.15, y: cy, w: aw2 / 2 - 0.15, h: 0.2, fontSize: 7.8, color: K.ink2 });
  });
  T(s, "after every step: money conserved · only legal moves · release only with all gates · never paid twice", { x: x + 0.18, y: py + 2.82, w: aw2, h: 0.6, fontSize: 8.5, bold: true, color: K.teal });
  // panel 4 — the 14 seeded bugs, by name
  x = MX + 3 * (pw + 0.15);
  const bshort = { M01: "guard ignores holds", M02: "approval not pinned to revision", M03: "screening never expires", M04: "permission checks off",
    M05: "screening order ignored", M06: "cross-trade shipment ok", M07: "new revision keeps approval", M08: "creation KYC skipped", M09: "hash check skips content",
    M10: "regulator sees full data", M11: "version check removed", M12: "refund during AML hold", M13: "matching ignores amounts", M14: "duplicate commands run" };
  mut.forEach((m, k) => {
    const y = py + 0.56 + k * 0.205, killed = m.killed_by_suite === "True";
    T(s, [{ text: (killed ? "✓ " : "○ "), options: { bold: true, color: killed ? K.teal : K.mute } }, { text: m.mutant + " ", options: { bold: true, color: killed ? K.ink : K.mute, fontFace: MONO } },
          { text: bshort[m.mutant] || m.seeded_defect, options: { color: killed ? K.ink2 : K.mute, italic: !killed } }], { x: x + 0.14, y, w: pw - 0.24, h: 0.2, fontSize: 7.6, valign: "middle" });
  });
  T(s, "M11 survives: the database lock already serialises writes — redundant, not missing.", { x: x + 0.14, y: py + 3.45, w: pw - 0.26, h: 0.4, fontSize: 7.8, italic: true, color: K.mute, fontFace: SERIF });
  T(s, "Margin note — these are our own tests of our own rules, on synthetic data. They cannot show that real attestations are honest, that the system resists attackers, or that it scales.",
    { x: MX, y: 6.5, w: W - 2 * MX, h: 0.32, fontSize: 9.5, italic: true, color: K.gold, fontFace: SERIF });
  s.addNotes(`(60 s) Four kinds of evidence, each answering a different doubt. One: the suite — 77 tests, 30 of them added after the interim to log in as every role and check every page. Two: we attacked the release directly seventeen ways — stale screening, revised invoice, regulator pressing release — all refused, money unchanged. Three: a random stress test — ${N(rob.commands)} random commands from any role across 200 trades; ${N(acc)} were accepted and the trades really moved — ${rob["final_state::Released"]} released, ${rob["final_state::Frozen"]} frozen, ${rob["final_state::Refunded/Terminated"]} refunded — and after every one of ${N(rob.invariant_checks)} steps money was conserved and nothing was paid twice. Four: would our tests even notice a bug? We planted fourteen; thirteen were caught, and the survivor is redundant. Margin note: our own tests, synthetic data.`);

  // ─────────────────────────────── 11 · THREE TIMES GREEN WAS WRONG
  s = page(pres, { part: 2, presenter: true, title: "Three times a green result was wrong — and how we caught it", sub: "The most useful thing we learned: a passing check is only as good as what it actually checks" });
  // main case: the UI leak
  const mx0 = MX, mw = 7.7;
  T(s, "1 · THE LEAK  —  found by an independent review, 8 Nov", { x: mx0, y: 1.85, w: mw, h: 0.24, fontSize: 9.5, bold: true, color: K.red, charSpacing: 1.5 });
  const pw2 = 3.05;
  // before (schematic)
  R(s, pres, mx0, 2.2, pw2, 2.3, { fill: "FFFFFF", line: K.red, lw: 1.25 });
  T(s, "Ledger · acting as importer #2", { x: mx0 + 0.12, y: 2.27, w: pw2 - 0.2, h: 0.22, fontSize: 8.5, bold: true, color: K.ink2 });
  [["importer_hk_01", "150,000", 0], ["importer_hk_02", "100,000", 1], ["exporter_th_01", "250,000", 0], ["escrow ESC-001", "0", 0]].forEach(([a, b, own], k) => {
    const ry = 2.58 + k * 0.4;
    L(s, pres, mx0 + 0.12, ry - 0.03, mx0 + pw2 - 0.12, ry - 0.03, K.rule, 0.5);
    T(s, a, { x: mx0 + 0.12, y: ry, w: 1.45, h: 0.32, fontSize: 8.5, color: K.ink, fontFace: MONO, valign: "middle" });
    T(s, b, { x: mx0 + 1.55, y: ry, w: 0.75, h: 0.32, fontSize: 8.5, color: K.ink, fontFace: MONO, valign: "middle", align: "right" });
    if (!own) T(s, "✗ leak", { x: mx0 + 2.35, y: ry, w: 0.65, h: 0.32, fontSize: 8.5, bold: true, color: K.red, valign: "middle" });
  });
  T(s, "schematic of the interim page (illustrative balances)", { x: mx0, y: 4.53, w: pw2, h: 0.2, fontSize: 7.8, italic: true, color: K.mute, fontFace: SERIF });
  // the fix mechanism
  const fx0 = mx0 + pw2 + 0.12, fw = mw - 2 * pw2 - 0.24;
  T(s, "the fix", { x: fx0, y: 2.25, w: fw, h: 0.22, fontSize: 9, bold: true, italic: true, color: K.teal, fontFace: SERIF, align: "center" });
  [["request", K.ink2], ["role check", K.teal], ["projection", K.teal], ["page", K.ink2]].forEach(([t2, col], k) => {
    const yy = 2.55 + k * 0.48;
    R(s, pres, fx0 + 0.05, yy, fw - 0.1, 0.32, { r: 0.08, fill: K.paper, line: col, lw: 1 });
    T(s, t2, { x: fx0 + 0.05, y: yy, w: fw - 0.1, h: 0.32, fontSize: 8.5, bold: true, color: col, align: "center", valign: "middle" });
    if (k < 3) L(s, pres, fx0 + fw / 2, yy + 0.33, fx0 + fw / 2, yy + 0.47, col, 1, { head: true });
  });
  T(s, "server-side", { x: fx0, y: 4.5, w: fw, h: 0.2, fontSize: 8, italic: true, color: K.teal, fontFace: SERIF, align: "center" });
  // after (real)
  const ax = fx0 + fw + 0.12;
  R(s, pres, ax, 2.2, pw2, 2.3, { fill: "FFFFFF", line: K.teal, lw: 1.25 });
  T(s, "Ledger · acting as importer #2", { x: ax + 0.12, y: 2.27, w: pw2 - 0.2, h: 0.22, fontSize: 8.5, bold: true, color: K.ink2 });
  T(s, [{ text: "Projection: ", options: { color: K.ink2 } }, { text: "own accounts and own-trade events only", options: { bold: true, color: K.ink } }],
    { x: ax + 0.12, y: 2.5, w: pw2 - 0.2, h: 0.3, fontSize: 7.8 });
  L(s, pres, ax + 0.12, 2.85, ax + pw2 - 0.12, 2.85, K.rule, 0.5);
  T(s, "importer_hk_02", { x: ax + 0.12, y: 2.88, w: 1.45, h: 0.32, fontSize: 8.5, color: K.ink, fontFace: MONO, valign: "middle" });
  T(s, "100,000", { x: ax + 1.55, y: 2.88, w: 0.75, h: 0.32, fontSize: 8.5, color: K.ink, fontFace: MONO, valign: "middle", align: "right" });
  T(s, "✓ own", { x: ax + 2.35, y: 2.88, w: 0.65, h: 0.32, fontSize: 8.5, bold: true, color: K.teal, valign: "middle" });
  R(s, pres, ax + 0.12, 3.3, pw2 - 0.24, 0.85, { fill: K.tealL, tr: 40, line: K.teal, lw: 0.75, dash: "dash" });
  T(s, "3 other accounts and every other trade's events are never sent to this browser", { x: ax + 0.22, y: 3.3, w: pw2 - 0.44, h: 0.85, fontSize: 8.8, italic: true, color: K.teal, fontFace: SERIF, valign: "middle", align: "center" });
  T(s, [{ text: "Conservation check ", options: { color: K.ink2 } }, { text: "OK", options: { bold: true, color: K.teal } }, { text: "  ·  hash chain ", options: { color: K.ink2 } }, { text: "intact", options: { bold: true, color: K.teal } }],
    { x: ax + 0.12, y: 4.2, w: pw2 - 0.2, h: 0.24, fontSize: 7.8 });
  T(s, "transcribed from the real page after the fix", { x: ax, y: 4.53, w: pw2, h: 0.2, fontSize: 7.8, italic: true, color: K.mute, fontFace: SERIF });
  T(s, [{ text: "Why the tests missed it: ", options: { bold: true, color: K.ink } }, { text: "all 47 checked the engine; none logged in as a role and looked at the web page. ", options: { color: K.ink2 } },
        { text: "Now: ", options: { bold: true, color: K.teal } }, { text: "30 tests do exactly that, for every participant and page.", options: { color: K.ink2 } }],
    { x: mx0, y: 4.85, w: mw, h: 0.6, fontSize: 10.5, fontFace: SERIF });
  // two smaller cases
  const cx0 = MX + mw + 0.3, cw = W - MX - cx0;
  const cases = [["2 · THE BUG COUNTER", "14 / 14", md("M-11"), "Our mutation harness forgot to copy the web code into its sandbox, so every planted bug crashed the tests — and a crash looked like “caught”.", "now refuses to score if the clean copy fails"],
    ["3 · THE STRESS TEST", `0 of 5,427`, `${N(acc)} accepted`, "After the 8 Nov fix changed a function's inputs, the random-walk harness called it the old way. Every call errored, and errors were counted as “refused” — so it tested nothing.", "found in final review; Python errors now stop the run"]];
  cases.forEach(([hd, before, after, why, now], k) => {
    const y = 1.85 + k * 1.85;
    R(s, pres, cx0, y, cw, 1.7, { fill: K.card, line: K.rule });
    T(s, hd, { x: cx0 + 0.18, y: y + 0.1, w: cw - 0.3, h: 0.22, fontSize: 9, bold: true, color: K.gold, charSpacing: 1.5 });
    T(s, [{ text: before, options: { color: K.mute, strike: "sngStrike" } }, { text: "  →  ", options: { color: K.mute } }, { text: after, options: { bold: true, color: K.teal } }],
      { x: cx0 + 0.18, y: y + 0.34, w: cw - 0.3, h: 0.32, fontSize: 14, fontFace: SERIF, valign: "middle" });
    T(s, why, { x: cx0 + 0.18, y: y + 0.7, w: cw - 0.3, h: 0.68, fontSize: 8.6, color: K.ink2 });
    T(s, "✓ " + now, { x: cx0 + 0.18, y: y + 1.38, w: cw - 0.3, h: 0.24, fontSize: 8.5, bold: true, italic: true, color: K.teal, fontFace: SERIF });
  });
  R(s, pres, MX, 5.62, W - 2 * MX, 0.95, { fill: K.goldL, tr: 30, line: null });
  L(s, pres, MX, 5.62, MX, 6.57, K.gold, 3);
  await I(s, "Lightbulb", K.gold, MX + 0.25, 5.88, 0.42);
  T(s, [{ text: "Lesson.  ", options: { bold: true, italic: true, color: K.gold } }, { text: "Test the tests. Every check now has a positive control that must pass and a broken case that must fail — a harness that cannot tell them apart refuses to report a number.", options: { color: K.ink2 } }],
    { x: MX + 0.85, y: 5.62, w: W - 2 * MX - 1.05, h: 0.95, fontSize: 12, fontFace: SERIF, valign: "middle" });
  s.addNotes(`(60 s) Our most useful lesson: three times, a green result was wrong. One — the leak. At the interim, all 47 tests passed, yet the ledger page showed every account to every role, because no test logged in as a role and looked at the page. An independent review caught it; we moved the access rule server-side and added 30 tests that check every participant on every page. Two — our bug counter said 14 out of 14 because a missing file made every planted bug crash the tests; the honest number is 13. Three — in final review we found the random stress test had been testing nothing since the 8 November fix: every command errored and was counted as refused. Fixed, it now runs ${N(acc)} accepted commands with zero violations. The lesson: test the tests.`);

  // ─────────────────────────────── 12 · SCORECARD ON AN EVIDENCE LADDER
  s = page(pres, { part: 2, presenter: true, title: "Scorecard: how strong is the evidence for each hypothesis?", sub: "A verdict is only as strong as the rung it stands on — and the top rung is still empty" });
  const rungs = [["Assumed", "inputs we chose", K.mute], ["Modelled", "process & timing model", K.gold], ["Simulated", "executed on our prototype", K.teal], ["Measured", "real banks, real trades", K.blue]];
  const gx = MX, gw = W - 2 * MX, colw = (gw - 0.45) / 4, gy = 1.95;
  // ladder axis
  L(s, pres, gx, gy + 0.62, gx + gw, gy + 0.62, K.ink2, 1.5, { head: true, name: "axis" });
  T(s, "stronger evidence →", { x: gx + gw - 2.2, y: gy + 0.66, w: 2.2, h: 0.2, fontSize: 8.5, italic: true, color: K.mute, fontFace: SERIF, align: "right" });
  rungs.forEach(([t2, sub2, col], i) => {
    const cx = gx + i * (colw + 0.15);
    T(s, t2, { x: cx, y: gy, w: colw, h: 0.32, fontSize: 15, bold: true, color: col, fontFace: SERIF });
    T(s, sub2, { x: cx, y: gy + 0.3, w: colw, h: 0.24, fontSize: 9.5, italic: true, color: K.mute, fontFace: SERIF });
    R(s, pres, cx + 0.05, gy + 0.56, 0.12, 0.12, { oval: true, fill: col, line: null });
  });
  const card = async (col, i, k, id, nm, verdict, vcol, ev, ref) => {
    const cx = gx + col * (colw + 0.15), y = gy + 1.0 + k * 1.08;
    R(s, pres, cx, y, colw, 0.98, { fill: K.card, line: K.rule, name: "!!hc" + i });
    L(s, pres, cx, y, cx, y + 0.98, vcol, 3);
    T(s, id, { x: cx + 0.15, y: y + 0.06, w: 0.6, h: 0.34, fontSize: 17, bold: true, italic: true, color: vcol, fontFace: SERIF, objectName: "!!hid" + i });
    T(s, nm, { x: cx + 0.7, y: y + 0.08, w: colw - 1.4, h: 0.3, fontSize: 11.5, bold: true, color: K.ink, fontFace: SERIF, objectName: "!!ht" + i });
    T(s, ref, { x: cx + colw - 0.72, y: y + 0.1, w: 0.62, h: 0.26, fontSize: 8, italic: true, color: K.mute, fontFace: SERIF, align: "right" });
    R(s, pres, cx + 0.15, y + 0.42, 1.55, 0.22, { fill: null, line: vcol, lw: 1.25 });
    T(s, verdict, { x: cx + 0.15, y: y + 0.42, w: 1.55, h: 0.22, fontSize: 7.3, bold: true, color: vcol, align: "center", valign: "middle", charSpacing: 1 });
    T(s, ev, { x: cx + 0.15, y: y + 0.68, w: colw - 0.25, h: 0.26, fontSize: 8.6, color: K.ink2, valign: "middle" });
  };
  // Assumed column: what the models rest on
  ["durations of each manual step", "automated steps take 0 days", "48 h screening window", "HKD 5 m trade limit"].forEach((t2, k) =>
    T(s, [{ text: "~  ", options: { color: K.mute, bold: true } }, { text: t2, options: { color: K.sub, italic: true } }], { x: gx, y: gy + 1.05 + k * 0.38, w: colw, h: 0.34, fontSize: 10, fontFace: SERIF }));
  T(s, "everything on the Modelled rung inherits these", { x: gx, y: gy + 2.65, w: colw, h: 0.4, fontSize: 8.5, bold: true, color: K.gold });
  await card(1, 0, 0, "H1", "Efficiency", "SUPPORTED · MODEL", K.gold, `tasks 7 → 3 (${cnt5()} at matched scope)`, "slide 13");
  await card(1, 4, 1, "H5", "Honest cost", "TRADE-OFF REAL", K.red, `importer cash ${mv("M-24")} → ${mv("M-25")} d · exporter risk → 0`, "slide 14");
  await card(2, 1, 0, "H2", "Safe release", "SUPPORTED · SIM", K.teal, `${md("M-04")} refused · 0 / ${N(rob.invariant_checks)} violations`, "slide 10");
  await card(2, 2, 1, "H3", "Safe exceptions", "SUPPORTED · SIM", K.teal, "mismatch → review · alert → freeze", "slide 9");
  await card(2, 3, 2, "H4", "Auditability", "SUPPORTED · SIM", K.teal, `${md("M-08")} rules · regulator rebuilt ${md("M-07")} paths`, "slides 10–11");
  // Measured column: empty on purpose
  const mxc = gx + 3 * (colw + 0.15);
  R(s, pres, mxc, gy + 1.0, colw, 3.14, { fill: null, line: K.blue, lw: 1.25, dash: "dash" });
  await I(s, "Telescope", K.blue, mxc + colw / 2 - 0.25, gy + 1.45, 0.5);
  T(s, "Nothing here yet", { x: mxc + 0.15, y: gy + 2.05, w: colw - 0.3, h: 0.32, fontSize: 13, bold: true, italic: true, color: K.blue, fontFace: SERIF, align: "center" });
  T(s, "No hypothesis has real-world evidence. Moving up this rung is the next step: practitioner timings, bank feedback, a pilot on real trade data.", { x: mxc + 0.2, y: gy + 2.45, w: colw - 0.4, h: 1.3, fontSize: 9.5, color: K.sub, align: "center" });
  T(s, [{ text: "Reading it:  ", options: { bold: true, color: K.ink } }, { text: "H2–H4 are supported because we ran them; H1 only because we modelled it; H5 is a real cost our model surfaced. Part 4 tests H1 and H5 harder.", options: { color: K.ink2 } }],
    { x: MX, y: 6.28, w: W - 2 * MX, h: 0.42, fontSize: 10.5, fontFace: SERIF, valign: "middle" });
  s.addNotes("(50 s) Instead of ticking boxes, we place each verdict on an evidence ladder. On the left, the assumptions our models rest on. H1 efficiency and H5 cost sit on the Modelled rung — they are only as good as those assumptions. H2, H3 and H4 sit on the Simulated rung: we actually executed them on the prototype. And the Measured rung is empty — on purpose. No hypothesis has real-world evidence yet; getting there is the next step. Part 4 now looks at H1 and H5 more closely.");

  function cnt5() { const c = D.readCSV("results/process_counts.csv").find(r => r.scenario === "normal" && r.model === "proposed_e2e"); return `7 → ${c.manual_settlement_tasks}`; }
};
