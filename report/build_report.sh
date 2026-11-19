#!/bin/bash
# Two-pass build: render, locate headings in the PDF, rebuild with a static table of contents.
set -e
cd "$(dirname "$0")/.."
# Requirements: node (with 'docx' from package.json: run `npm install` in the project root, or set NODE_PATH),
# LibreOffice (soffice) and poppler-utils (pdfinfo, pdftotext). Override the converter with SOFFICE=/path/to/soffice.
SOFFICE=${SOFFICE:-soffice}
export NODE_PATH=${NODE_PATH:-$(pwd)/node_modules:$(npm root -g)}
build() { node report/build_report.js >/dev/null; (cd report && (zip -dq FTEC3002_Group1_Final_Report.docx '*/' >/dev/null 2>&1 || true) && "$SOFFICE" --headless --convert-to pdf FTEC3002_Group1_Final_Report.docx >/dev/null 2>&1); }
unset TOC_JSON; build
python3 - <<'PY'
import subprocess, json, re
pdf="report/FTEC3002_Group1_Final_Report.pdf"
n=int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo",pdf],capture_output=True,text=True).stdout).group(1))
pages=[subprocess.run(["pdftotext","-f",str(i),"-l",str(i),"-layout",pdf,"-"],capture_output=True,text=True).stdout for i in range(1,n+1)]
heads=[]
for i,t in enumerate(pages,1):
    if i<=3: continue  # cover, at-a-glance, contents
    for line in t.splitlines():
        L=re.sub(r"\s+"," ",line.strip())
        L=re.sub(r"\s+(TESTED|MODELLED|PENDING)\b.*$","",L)  # drop evidence chips from headings
        if re.match(r"^(Executive Summary|References|Appendix [A-H]\.|(?:[1-9]|10)\. [A-Z])",L) and len(L)<95: heads.append({"t":L,"p":i,"lvl":1})
        elif re.match(r"^(?:[1-9]|10)\.[0-9] [A-Z]",L) and len(L)<95: heads.append({"t":L,"p":i,"lvl":2})
# keep first occurrence of each heading
seen=set(); out=[]
for h in heads:
    if h["t"] in seen: continue
    seen.add(h["t"]); out.append(h)
s1=next(h["p"] for h in out if h["t"].startswith("1. "))
ref=next(h["p"] for h in out if h["t"]=="References")
body=f"Sections 1–10 are numbered pages 1–{ref-s1} (PDF pages {s1}–{ref-1}); only these pages carry page numbers."
json.dump({"entries":out,"body":body,"s1":s1,"ref":ref},open("/tmp/toc.json","w"))
print(body, len(out),"entries")
PY
# figure-free measurement pass (course outline §10: the 15-page limit excludes figures)
TOC_JSON=/tmp/toc.json NOFIG=1 OUT_DOCX=/tmp/nofig/report_nofig.docx bash -c 'mkdir -p /tmp/nofig && node report/build_report.js >/dev/null && cd /tmp/nofig && (zip -dq report_nofig.docx "*/" >/dev/null 2>&1 || true) && "'"$SOFFICE"'" --headless --convert-to pdf report_nofig.docx >/dev/null 2>&1'
python3 - <<'PY'
import subprocess, json, re
pdf="/tmp/nofig/report_nofig.pdf"
n=int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo",pdf],capture_output=True,text=True).stdout).group(1))
pg=[subprocess.run(["pdftotext","-f",str(i),"-l",str(i),pdf,"-"],capture_output=True,text=True).stdout for i in range(1,n+1)]
s1=next(i for i,t in enumerate(pg,1) if i>3 and re.search(r"^1\. Problem",t,re.M))
ref=next(i for i,t in enumerate(pg,1) if i>3 and re.search(r"^References$",t,re.M))
d=json.load(open("/tmp/toc.json"))
d["body"]=d["body"]+f" Without figures they occupy {ref-s1} of 15 pages (measured by rebuilding the report with figures removed)."
json.dump(d,open("/tmp/toc.json","w")); print(f"Text-only body (figures excluded) = {ref-s1} pages")
PY
TOC_JSON=/tmp/toc.json build
TOC_JSON=/tmp/toc.json python3 - <<'PY'
import subprocess,re,json
pdf="report/FTEC3002_Group1_Final_Report.pdf"
print(subprocess.run(["pdfinfo",pdf],capture_output=True,text=True).stdout.split("Pages:")[1].split()[0],"pages total")
PY
