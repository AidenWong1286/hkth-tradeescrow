"""Generate BPMN 2.0 XML (with DI), rendered swimlane PNGs, the six-state
diagram and the architecture/trust-boundary diagram from the code's own
definitions (process_model.py, model.TRANSITIONS)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Polygon, Circle, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tradeescrow import process_model as pm  # noqa: E402
from tradeescrow.model import TRANSITIONS, State  # noqa: E402

OUT = ROOT / "diagrams"
OUT.mkdir(exist_ok=True)
LANE_H, COL_W, TW, TH, X0 = 175, 165, 130, 58, 150
KIND_COLOR = {"MANUAL": "#F3E3C0", "AUTO": "#D3ECE8", "EXTERNAL_MANUAL": "#e5e7eb", "WAIT": "#E6EAF2"}
KIND_EDGE = {"MANUAL": "#B07A22", "AUTO": "#1F8A82", "EXTERNAL_MANUAL": "#6b7280", "WAIT": "#0B1730"}


def layout(model):
    lanes, tasks = pm.MODELS[model]
    tmap = {t.id: t for t in tasks}
    nodes = {}
    for nid, (lane, name) in pm.EVENTS[model].items():
        nodes[nid] = {"type": "end" if nid.startswith("end") else "start", "lane": lane, "name": name}
    for nid, (lane, name) in pm.GATEWAYS[model].items():
        nodes[nid] = {"type": "gateway", "lane": lane, "name": name}
    for t in tasks:
        nodes[t.id] = {"type": "task", "lane": t.lane, "name": t.name, "task": t}
    col = {"start": 0}
    for f in pm.FLOWS[model]:
        s, d = f[0], f[1]
        if d not in col:
            col[d] = col[s] + 1
    lower_lanes = {nodes[n]["lane"] for n in nodes if _is_exc(n, nodes)}
    for nid in col:
        n = nodes[nid]
        top = lanes.index(n["lane"]) * LANE_H
        n["x"] = X0 + col[nid] * COL_W
        if _is_exc(nid, nodes):
            n["y"] = top + 128
        elif n["lane"] in lower_lanes:
            n["y"] = top + 52
        else:
            n["y"] = top + LANE_H / 2
    # second pass to centre pairs consistently
    for nid, n in nodes.items():
        n["col"] = col[nid]
    width = X0 + (max(col.values()) + 1) * COL_W
    return lanes, nodes, width


def _is_exc(nid, nodes):
    n = nodes[nid]
    return (n["type"] == "task" and n["task"].path != "MAIN") or nid in ("end_rej", "end_ref")


def size(n):
    return {"task": (TW, TH), "gateway": (50, 50), "start": (36, 36), "end": (36, 36)}[n["type"]]


def write_bpmn(model):
    lanes, nodes, width = layout(model)
    pid = f"Process_{model}"
    flows = pm.FLOWS[model]
    tag = {"MANUAL": "userTask", "AUTO": "serviceTask", "EXTERNAL_MANUAL": "manualTask", "WAIT": "task"}
    x = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
         'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
         'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
         f'id="Defs_{model}" targetNamespace="https://example.org/hkth-tradeescrow" '
         'exporter="tradeescrow/make_diagrams.py" exporterVersion="1.0">',
         f'<bpmn:collaboration id="Collab_{model}"><bpmn:participant id="Pool_{model}" '
         f'name="{"Traditional open-account settlement (baseline)" if model == "baseline" else "Proposed pre-funded tokenised-deposit escrow"}" '
         f'processRef="{pid}"/></bpmn:collaboration>',
         f'<bpmn:process id="{pid}" isExecutable="false"><bpmn:laneSet id="LS_{model}">']
    for i, lane in enumerate(lanes):
        x.append(f'<bpmn:lane id="Lane_{model}_{i}" name="{escape(lane)}">')
        for nid, n in nodes.items():
            if n["lane"] == lane:
                x.append(f"<bpmn:flowNodeRef>{nid}</bpmn:flowNodeRef>")
        x.append("</bpmn:lane>")
    x.append("</bpmn:laneSet>")
    inc = {k: [] for k in nodes}
    out = {k: [] for k in nodes}
    for i, f in enumerate(flows):
        out[f[0]].append(f"F{i}")
        inc[f[1]].append(f"F{i}")
    for nid, n in nodes.items():
        io = "".join(f"<bpmn:incoming>{a}</bpmn:incoming>" for a in inc[nid]) + \
             "".join(f"<bpmn:outgoing>{a}</bpmn:outgoing>" for a in out[nid])
        name = escape(n["name"] if n["type"] != "task" else f'{nid} {n["name"]}')
        el = {"start": "startEvent", "end": "endEvent", "gateway": "exclusiveGateway"}.get(
            n["type"], tag[n.get("task").kind] if n["type"] == "task" else "task")
        doc = ""
        if n["type"] == "task":
            t = n["task"]
            doc = (f"<bpmn:documentation>kind={t.kind}; segment={t.segment}; path={t.path}; "
                   f"assumed duration days low/base/high={t.dur}</bpmn:documentation>")
        x.append(f'<bpmn:{el} id="{nid}" name="{name}">{doc}{io}</bpmn:{el}>')
    for i, f in enumerate(flows):
        nm = f' name="{escape(f[2])}"' if len(f) > 2 else ""
        x.append(f'<bpmn:sequenceFlow id="F{i}" sourceRef="{f[0]}" targetRef="{f[1]}"{nm}/>')
    x.append("</bpmn:process>")
    x.append(f'<bpmndi:BPMNDiagram id="D_{model}"><bpmndi:BPMNPlane id="P_{model}" bpmnElement="Collab_{model}">')
    x.append(f'<bpmndi:BPMNShape id="Pool_{model}_di" bpmnElement="Pool_{model}" isHorizontal="true">'
             f'<dc:Bounds x="0" y="0" width="{width}" height="{len(lanes) * LANE_H}"/></bpmndi:BPMNShape>')
    for i, lane in enumerate(lanes):
        x.append(f'<bpmndi:BPMNShape id="Lane_{model}_{i}_di" bpmnElement="Lane_{model}_{i}" isHorizontal="true">'
                 f'<dc:Bounds x="30" y="{i * LANE_H}" width="{width - 30}" height="{LANE_H}"/></bpmndi:BPMNShape>')
    for nid, n in nodes.items():
        w, h = size(n)
        x.append(f'<bpmndi:BPMNShape id="{nid}_di" bpmnElement="{nid}"><dc:Bounds x="{n["x"] - w / 2:.0f}" '
                 f'y="{n["y"] - h / 2:.0f}" width="{w}" height="{h}"/></bpmndi:BPMNShape>')
    for i, f in enumerate(flows):
        a, b = nodes[f[0]], nodes[f[1]]
        (aw, _), (bw, _) = size(a), size(b)
        pts = [(a["x"] + aw / 2, a["y"])]
        if a["x"] < b["x"]:
            midx = b["x"] - bw / 2 - 12
            pts += [(midx, a["y"]), (midx, b["y"]), (b["x"] - bw / 2, b["y"])]
        else:
            pts = [(a["x"], a["y"] + size(a)[1] / 2), (a["x"], a["y"] + 52), (b["x"], a["y"] + 52),
                   (b["x"], b["y"] + size(b)[1] / 2)]
        wps = "".join(f'<di:waypoint x="{px:.0f}" y="{py:.0f}"/>' for px, py in pts)
        x.append(f'<bpmndi:BPMNEdge id="F{i}_di" bpmnElement="F{i}">{wps}</bpmndi:BPMNEdge>')
    x.append("</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>")
    (OUT / f"{model}.bpmn").write_text("\n".join(x))
    return lanes, nodes, width


def render(model, title):
    lanes, nodes, width = layout(model)
    H = len(lanes) * LANE_H
    fig, ax = plt.subplots(figsize=(width / 72, H / 72 + 1.0), dpi=110)
    ax.set_xlim(0, width)
    ax.set_ylim(H + 10, -55)
    ax.axis("off")
    ax.text(10, -30, title, fontsize=15, weight="bold", color="#0B1730")
    for i, lane in enumerate(lanes):
        ax.add_patch(Rectangle((0, i * LANE_H), width, LANE_H, fc="#f8fafc" if i % 2 else "#ffffff",
                               ec="#94a3b8", lw=1))
        ax.add_patch(Rectangle((0, i * LANE_H), 34, LANE_H, fc="#0B1730", ec="#0B1730"))
        ax.text(17, i * LANE_H + LANE_H / 2, lane, rotation=90, ha="center", va="center", color="white",
                fontsize=8.2, weight="bold", wrap=True)
    for f in pm.FLOWS[model]:
        a, b = nodes[f[0]], nodes[f[1]]
        (aw, ah), (bw, bh) = size(a), size(b)
        if a["x"] < b["x"]:
            midx = b["x"] - bw / 2 - 14
            xs = [a["x"] + aw / 2, midx, midx, b["x"] - bw / 2]
            ys = [a["y"], a["y"], b["y"], b["y"]]
        else:
            yy = max(a["y"], b["y"]) + 50
            xs = [a["x"], a["x"], b["x"], b["x"]]
            ys = [a["y"] + ah / 2, yy, yy, b["y"] + bh / 2]
        exc = len(f) > 2 and any(k in f[2] for k in ("FAIL", "ALERT", "discrepancy", "alert", "terminate"))
        col = "#B8342A" if exc else "#334155"
        ax.plot(xs[:-1], ys[:-1], color=col, lw=1.1, ls="--" if exc else "-")
        ax.annotate("", xy=(xs[-1], ys[-1]), xytext=(xs[-2], ys[-2]),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=1.1, ls="--" if exc else "-"))
        if len(f) > 2:
            ax.text(xs[1] + 3, (ys[1] + ys[2]) / 2 - 4, f[2], fontsize=6.6, color=col, style="italic")
    for nid, n in nodes.items():
        if n["type"] == "task":
            t = n["task"]
            ax.add_patch(FancyBboxPatch((n["x"] - TW / 2, n["y"] - TH / 2), TW, TH, boxstyle="round,pad=0,rounding_size=9",
                                        fc=KIND_COLOR[t.kind], ec=KIND_EDGE[t.kind], lw=1.6 if t.path == "MAIN" else 1.2,
                                        ls="-" if t.path == "MAIN" else "--"))
            ax.text(n["x"], n["y"] - 19, t.id, ha="center", fontsize=7, weight="bold", color=KIND_EDGE[t.kind])
            ax.text(n["x"], n["y"] + 5, "\n".join(_wrap(t.name, 22)), ha="center", va="center", fontsize=7.2)
        elif n["type"] == "gateway":
            ax.add_patch(Polygon([(n["x"], n["y"] - 25), (n["x"] + 25, n["y"]), (n["x"], n["y"] + 25),
                                  (n["x"] - 25, n["y"])], fc="#FFFFFF", ec="#0B1730", lw=1.4))
            ax.text(n["x"], n["y"], "×", ha="center", va="center", fontsize=13, color="#0B1730")
            ax.text(n["x"], n["y"] - 31, n["name"], ha="center", fontsize=7, weight="bold")
        else:
            ax.add_patch(Circle((n["x"], n["y"]), 18, fc="#ffffff", ec="#1F8A82" if n["type"] == "start" else "#B8342A",
                                lw=1.5 if n["type"] == "start" else 3))
            ax.text(n["x"], n["y"] + 30, "\n".join(_wrap(n["name"], 16)), ha="center", va="top", fontsize=7)
    handles = [plt.Rectangle((0, 0), 1, 1, fc=KIND_COLOR[k], ec=KIND_EDGE[k]) for k in
               ("MANUAL", "AUTO", "EXTERNAL_MANUAL", "WAIT")]
    ax.legend(handles, ["Manual task", "Automated (simulated) task", "Third-party manual (common to both)",
                        "Waiting period"], loc="lower right", fontsize=7.5, ncol=4, frameon=False,
              bbox_to_anchor=(1, -0.06))
    fig.savefig(OUT / f"{model}_bpmn.png", bbox_inches="tight", dpi=300)
    plt.close(fig)


def _wrap(s, n):
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    return lines


def state_machine():
    color = {State.CREATED: "#64748b", State.PENDING: "#b7791f", State.UNDER_REVIEW: "#B07A22",
             State.FROZEN: "#1d4ed8", State.RELEASED: "#1F8A82", State.REFUNDED: "#7c3aed"}
    short = {
        (None, State.CREATED): "fund + creation KYC/AML PASS",
        (State.CREATED, State.PENDING): "shipment attested",
        (State.CREATED, State.UNDER_REVIEW): "doc FAIL / dispute",
        (State.PENDING, State.UNDER_REVIEW): "doc FAIL / dispute",
        (State.CREATED, State.FROZEN): "AML alert / hold",
        (State.PENDING, State.FROZEN): "AML alert / hold",
        (State.UNDER_REVIEW, State.FROZEN): "AML alert / hold",
        (State.PENDING, State.RELEASED): "GUARD: shipment ∧ docs(current)\\n∧ KYC×2 (fresh) ∧ no hold",
        (State.UNDER_REVIEW, State.PENDING): "reviewer revalidates",
        (State.UNDER_REVIEW, State.CREATED): "revalidated, not shipped",
        (State.UNDER_REVIEW, State.REFUNDED): "reviewer terminates",
        (State.FROZEN, State.PENDING): "compliance clears",
        (State.FROZEN, State.CREATED): "clears (not shipped)",
        (State.FROZEN, State.UNDER_REVIEW): "clears (docs failing)",
        (State.FROZEN, State.REFUNDED): "compliance terminates",
    }
    lines = ['digraph G { rankdir=LR; bgcolor="white"; nodesep=0.55; ranksep=0.9;',
             'node [shape=box style="rounded,filled" fontname="Helvetica" fontsize=13 fontcolor=white penwidth=0];',
             'edge [fontname="Helvetica" fontsize=9.5 color="#334155" fontcolor="#334155"];',
             'start [shape=circle label="" width=0.25 style=filled fillcolor="#0B1730"];']
    for s in State.ALL:
        nid = s.replace(" ", "_").replace("/", "_")
        per = ' peripheries=2 color="white"' if s in State.TERMINAL else ""
        lines.append(f'{nid} [label="{s}" fillcolor="{color[s]}"{per}];')
    for (a, b), _ in TRANSITIONS.items():
        an = "start" if a is None else a.replace(" ", "_").replace("/", "_")
        bn = b.replace(" ", "_").replace("/", "_")
        exc = b in (State.FROZEN, State.UNDER_REVIEW, State.REFUNDED)
        style = ' color="#B8342A" fontcolor="#B8342A" style=dashed' if exc else ""
        bold = ' penwidth=2.4 color="#1F8A82" fontcolor="#1F8A82"' if b == State.RELEASED else ""
        lines.append(f'{an} -> {bn} [label="{short[(a, b)]}"{style}{bold}];')
    lines.append('{rank=same; Released; Refunded_Terminated;}')
    lines.append('label="Escrow state machine (generated from tradeescrow/model.py TRANSITIONS; 15 permitted transitions; '
                 'all others rejected)"; labelloc=b; fontname="Helvetica"; fontsize=10;}')
    (OUT / "state_machine.dot").write_text("\n".join(lines))
    for fmt in ("png", "svg"):
        subprocess.run(["dot", f"-T{fmt}", "-Gdpi=170", str(OUT / "state_machine.dot"), "-o",
                        str(OUT / f"state_machine.{fmt}")], check=True)


def architecture():
    dot = r'''digraph A { rankdir=TB; newrank=true; compound=true; fontname="Helvetica"; nodesep=0.35; ranksep=0.7;
node [shape=box style="rounded,filled" fontname="Helvetica" fontsize=11 fillcolor="#ffffff" color="#94a3b8"];
edge [fontname="Helvetica" fontsize=9 color="#475569" fontcolor="#475569"];
subgraph cluster_users { label="Seven participants (role-selected; server-side RBAC)"; style="rounded,filled"; fillcolor="#f1f5f9"; color="#94a3b8";
  imp [label="HK importer"]; exp [label="Thai exporter"]; bh [label="Bank H\n(ops + compliance)"]; bo [label="Thai Bank O\n(observer)"];
  log [label="Logistics provider"]; cus [label="Customs authority"]; reg [label="Regulator\n(read-only audit)"]; }
subgraph cluster_ui { label="Presentation (same service layer)"; style="rounded,filled"; fillcolor="#eef6ff"; color="#60a5fa";
  st [label="Streamlit app"]; fl [label="Flask console\n(verified, fallback demo)"]; }
subgraph cluster_core { label="Escrow service layer — simulated smart contract (Bank H)"; style="rounded,filled"; fillcolor="#ecfdf5"; color="#10b981";
  rbac [label="Command authorisation\n(PERMISSIONS, party scope)"]; sm [label="Six-state machine\n+ release guard"];
  tok [label="Token accounting\nTDEP-HKD@Bank H\n(integer cents, conservation)"]; jr [label="Append-only journal\nSHA-256 hash chain"];
  views [label="Role projections\n& audit export"]; }
subgraph cluster_off { label="Off-chain attestation modules (SIMULATED — trust boundary)"; style="rounded,filled,dashed"; fillcolor="#fff7ed"; color="#f97316";
  docm [label="Document matching\n(contract, invoice, B/L, customs)"]; kyc [label="KYC/AML screening\n(creation + pre-release, 48h)"]; ship [label="Shipment attestation\n(logistics)"]; }
db [shape=cylinder label="SQLite mock\npermissioned ledger" fillcolor="#f8fafc"];
ext [label="e-HKD extension (conceptual)\n2-phase commit: tokenised deposits\n⇄ CeBM mock — all-or-nothing" style="rounded,filled,dashed" fillcolor="#eef2ff" color="#6366f1"];
nolive [label="NOT CONNECTED: real banks,\nHKMA e-HKD, EnsembleTX, mBridge,\nreal KYC/AML, customs, FX" shape=note fillcolor="#fef2f2" color="#ef4444" fontcolor="#991b1b"];
imp -> st [lhead=cluster_ui ltail=cluster_users]; {rank=same; imp; exp; bh; bo; log; cus; reg;} {rank=same; docm; kyc; ship; rbac;}
st -> rbac [lhead=cluster_core label="commands / reads"]; fl -> rbac [lhead=cluster_core];
rbac -> sm; sm -> tok [label="lock / release / refund"]; sm -> jr [label="every accepted\n& rejected command"]; jr -> views;
ship -> sm [label="attestation\n(PASS/FAIL)"]; docm -> sm [label="attestation\n(digest-pinned)"]; kyc -> sm [label="PASS / ALERT\n→ hold"];
tok -> db; jr -> db; sm -> ext [style=dashed label="post-release\nillustration"]; ext -> nolive [style=invis];
}'''
    (OUT / "architecture.dot").write_text(dot)
    for fmt in ("png", "svg"):
        subprocess.run(["dot", f"-T{fmt}", "-Gdpi=160", str(OUT / "architecture.dot"), "-o",
                        str(OUT / f"architecture.{fmt}")], check=True)


if __name__ == "__main__":
    for m, title in (("baseline", "Baseline: traditional open-account settlement (payment after shipment)"),
                     ("proposed", "Proposed: pre-funded tokenised-deposit escrow with off-chain attestations")):
        write_bpmn(m)
        render(m, title)
    state_machine()
    architecture()
    print("diagrams written:", sorted(p.name for p in OUT.iterdir()))
