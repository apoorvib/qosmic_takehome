#!/usr/bin/env python3
"""render_report.py — Write-phase assembly helper (Module 1, Phase 3).

The agent authors the only free-prose section (the executive summary) as
`artifacts/<store>/reason/exec_summary.md`. This helper templates the structured
sections (experiments, competitor table, technical checks) from reason/*.json
1:1 with the calibration anchor and assembles sample_output/<store>.md.

Run validate.py first; do not render an invalid audit.

Usage: python harness/scripts/render_report.py artifacts/<store> [--out sample_output/<store>.md]
"""
import argparse, json
from pathlib import Path


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def render(store_root: Path) -> str:
    r = store_root / "reason"
    syn = load(r / "synthesis.json")
    exps = load(r / "experiments.json")["experiments"]
    comps = load(r / "competitors.json")
    tech = load(r / "tech_checks.json")["checks"]
    exec_path = r / "exec_summary.md"
    exec_summary = exec_path.read_text(encoding="utf-8").strip() if exec_path.exists() else \
        "\n\n".join(t["summary"] for t in syn["themes"])

    out = [f"# {syn['headline']}", "", "## Executive summary", "", exec_summary, "", "## Proposed experiments", ""]
    for e in exps:
        lift = e["expected_lift"]
        out += [
            f"### {e['exp_id']} — {e['title']}", "",
            f"**Pillar:** {e['pillar']}  ",
            f"**Affected surface:** {e['affected_surface']}  ",
            f"**URL:** {e['url']}  ",
            f"**Evidence:** `{e['evidence']['screenshot']}` (signal: `{e['evidence']['triggering_signal']}`)  ",
            f"**Hypothesis:** {e['hypothesis']}  ",
            f"**Primary change:** {e['primary_change']}  ",
            f"**Primary KPI:** {e['primary_kpi']}  ",
            f"**Decision rule:** {e['decision_rule']}  ",
            f"**Expected lift:** +{lift['low']}–{lift['high']}{lift['unit']}  ",
            f"**Confidence:** {e['confidence']}%", "",
        ]

    out += ["## Competitor analysis", "",
            f"Competitors in {comps['niche']} make the shopping job easier through clearer use-case "
            "navigation and retailer handoffs; the patterns below are the ones worth adapting.", "",
            "| Competitor | Domain | Positioning | What they make easier | Our edge | Pattern to adapt |",
            "|---|---|---|---|---|---|"]
    for c in comps["competitors"]:
        out.append(f"| {c['name']} | {c['domain']} | {c['positioning']} | {c['makes_easier']} | "
                   f"{c['our_edge']} | {c['pattern_to_adapt']} |")

    out += ["", "## Technical checks", "", "| Check | Status | Detail |", "|---|---|---|"]
    for c in tech:
        out.append(f"| {c['name']} | {c['status']} | {c['detail']} |")
    out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("store_root")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    store_root = Path(args.store_root)
    store = store_root.name
    out_path = Path(args.out or f"sample_output/{store}.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render(store_root), encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
