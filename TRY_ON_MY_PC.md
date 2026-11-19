# Prompt for Claude Code — run and try HK–TH TradeEscrow on my PC

Copy everything below the line into Claude Code, opened in the unzipped `HKTH-TradeEscrow` folder.

---

You are helping me run and try my FTEC3002 project, **HK–TH TradeEscrow**, on this computer. Read `CLAUDE.md` first: it has the file map, commands and rules. Do the steps below in order, tell me the result of each step in one or two lines, and stop to ask me before changing any project code.

**1. Check my machine.** Report my OS and the versions of Python (need ≥ 3.11), pip and Node (need ≥ 20, only for rebuilding the report and deck). Say whether LibreOffice (`soffice`) and poppler (`pdftotext`, `pdfinfo`) are installed. These are only needed to rebuild the report PDF. If something is missing, tell me the exact install command for my OS, but don't install anything system-wide without asking.

**2. Set up Python in a virtual environment** (do not touch my global Python):
- create `.venv` in the project folder and activate it
- `pip install -r requirements.txt`

**3. Run the tests:** `python -m pytest -q`. Expected: **77 passed**. If anything fails, show me the failing test names and the first error, explain the cause in plain words, and propose a fix without applying it.

**4. Run the experiments:** `python scripts/run_experiments.py`. Then show me these lines from `results/metrics.csv`: M-01 (77/77), M-04 (17/17), M-09 (0 of 5,935), M-10 (5,312), M-11 (13/14). Only M-30 (wall-clock compute time) is expected to differ from the report.

**5. Start the Streamlit app**, the main demo: `streamlit run ui_streamlit/streamlit_app.py`. Give me the local URL and a 2-minute click-through to try:
- **TC-001 normal trade:** auto-play, then check the state bar (Created → Pending → Released), the release-guard panel and the audit trail.
- **TC-002 document mismatch:** as Bank H, click "Trigger contract release" and read the refusal (`ESCROW_UNDER_REVIEW`).
- **TC-003 AML alert:** auto-play, then switch to Regulator and check that the audit trail shows metadata only.
- **Ledger tab:** switch roles and confirm that Bank H sees everything, importer/exporter see only their own trades, and logistics/customs are denied.

**6. Start the Flask console**, the backup demo, in a second terminal: `python -m ui_flask.app`, then open http://127.0.0.1:5050. Give me the same three scenarios as a short checklist.

**7. Optional, only if I say "rebuild":** `npm install`, then `bash scripts/rebuild_all.sh` (on Windows use Git Bash or WSL). This regenerates `results/`, all diagrams and charts, `report/FTEC3002_Group1_Final_Report.docx/.pdf` and `presentation/HKTH_TradeEscrow_Final_Presentation_paper.pptx`. Afterwards, show me the line `Sections 1–10 are numbered pages 1–N`. **N must stay ≤ 15.**

**8. Finish with a short summary:** what worked, what didn't, and anything I must fix before the presentation on 24 Nov.

Rules for this session:
- All data is synthetic; never invent results, survey answers or screenshots.
- If I later ask you to change the UI or a function, follow the "If you change the UI or a function — what to update" table in `CLAUDE.md`. Then re-run the tests and the rebuild, and log the change in `CHANGELOG.md`.
- Keep the report palette: navy `#0B1730`, teal `#1F8A82`, gold `#B07A22`, red only for refusals.
