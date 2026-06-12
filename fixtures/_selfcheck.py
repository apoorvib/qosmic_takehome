#!/usr/bin/env python3
"""Fixture self-check / expected-results oracle.

This is NOT the eval. It is a Module-1 authoring aid that proves:
  - fixtures/sample_store/        is internally consistent (the PASS oracle)
  - fixtures/sample_store_broken/ trips each injected fault (the FAIL oracle)

Codex can use the printed expectations to assert validate.py / score_report.py
behaviour. Resolution conventions mirror WORK_SPLIT / the schemas README:
  cro_signals : "<sid>.cro_signals.<key>.present=<bool>"
  network     : "<sid>.network.responses[].status=<code>"
  visual      : "visual_findings.<id>"
  paths       : relative to the store root
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))


def profile_tokens(prof):
    toks = set()
    toks.add(prof.get("niche", ""))
    for f in prof.get("families", []):
        toks.add(f["name"]); toks.update(f.get("products", []))
    for key in ("jobs_to_be_done", "segments", "proof_points", "content_themes"):
        toks.update(prof.get(key, []))
    return {t.lower() for t in toks if t}


def ref_overlaps(ref, toks):
    for part in ref.replace(";", ",").split(","):
        val = part.split(":", 1)[-1].strip().lower()
        if val and any(val in t or t in val for t in toks):
            return True
    return False


def resolve_signal(sig, pages, visual_ids):
    if sig.startswith("visual_findings."):
        return sig.split(".", 1)[1] in visual_ids
    sid = sig.split(".", 1)[0]
    page = pages.get(sid)
    if not page:
        return False
    if ".network.responses[].status=" in sig:
        code = int(sig.split("=")[-1])
        return any(r.get("status") == code for r in page["network"]["responses"])
    if ".cro_signals." in sig:
        key = sig.split(".cro_signals.")[1].split(".")[0]
        want = sig.split("=")[-1].strip().lower() == "true"
        node = page.get("cro_signals", {}).get(key)
        return bool(node) and node.get("present") is want
    return False


def check(store_root: Path):
    root = ROOT / store_root
    manifest = load(root / "manifest.json")
    pages = {s["id"]: load(root / s["page_json"]) for s in manifest["surfaces"]}
    visual = load(root / "reason/visual_findings.json")
    visual_ids = {f["id"] for f in visual["findings"]}
    exps = load(root / "reason/experiments.json")["experiments"]
    prof = load(root / "reason/store_profile.json")
    toks = profile_tokens(prof)
    comps = load(root / "reason/competitors.json")["competitors"]
    tech = load(root / "reason/tech_checks.json")["checks"]

    faults = []
    # counts / coverage
    if len(exps) != 10:
        faults.append(f"count: {len(exps)} experiments (want 10)")
    pillars = {e["pillar"] for e in exps}
    missing = {"Conversion", "AOV", "Retention", "Acquisition", "Performance"} - pillars
    if missing:
        faults.append(f"pillar-gap: missing {sorted(missing)}")
    if not (3 <= len(comps) <= 4):
        faults.append(f"competitors: {len(comps)} rows (want 3-4)")
    if not (13 <= len(tech) <= 17):
        faults.append(f"tech-rows: {len(tech)} (want ~15)")
    # per-experiment
    bands = {"direct structural absence": (80, 88), "strong inference": (70, 80), "pattern / best-practice": (65, 72)}
    for i, e in enumerate(exps):
        ev = e["evidence"]
        if not (root / ev["screenshot"]).exists():
            faults.append(f"experiments[{i}].evidence.screenshot: missing file {ev['screenshot']}")
        if not resolve_signal(ev["triggering_signal"], pages, visual_ids):
            faults.append(f"experiments[{i}].evidence.triggering_signal: unresolved {ev['triggering_signal']}")
        if not ref_overlaps(ev["store_profile_ref"], toks):
            faults.append(f"experiments[{i}].evidence.store_profile_ref: no specificity overlap ({ev['store_profile_ref']})")
        lo, hi = bands.get(e["confidence_basis"], (0, 100))
        if not (lo <= e["confidence"] <= hi):
            faults.append(f"experiments[{i}].confidence: {e['confidence']} outside band {lo}-{hi} for '{e['confidence_basis']}'")
    # tech truthfulness
    for j, c in enumerate(tech):
        if c["status"] in ("Pass", "Fail") and (not c.get("grounded_in") or c["grounded_in"] == "not inspected"):
            faults.append(f"tech_checks[{j}] ({c['name']}): {c['status']} without resolvable grounded_in")
    return faults


def main():
    for name, expect_clean in [("sample_store", True), ("sample_store_broken", False)]:
        faults = check(Path(name))
        print(f"\n=== {name} === ({'expected CLEAN' if expect_clean else 'expected FAULTS'})")
        if not faults:
            print("  no faults")
        for f in faults:
            print(f"  - {f}")
        ok = (len(faults) == 0) == expect_clean
        print(f"  ORACLE: {'OK' if ok else 'UNEXPECTED'}")


if __name__ == "__main__":
    main()
