#!/usr/bin/env python3
"""Build a deliberately-degraded gingerpeople audit for the eval-loop demo (Codex task 3).

Copies the real artifacts/gingerpeople/ tree (so screenshots + signals still resolve)
and injects three REALISTIC quality flaws into reason/, chosen so the demo shows BOTH
eval layers earning their keep:

  Flaw A (validate.py catches) — confidence<->basis mismatch
  Flaw B (validate.py catches) — fabricated tech-check Pass (unresolvable grounded_in)
  Flaw C (JUDGE catches; passes validate.py) — a generic, boilerplate experiment that is
          mechanically valid (resolvable signal + screenshot + overlapping store_profile_ref)
          but is exactly the generic-CRO-advice the judge should flag

Run, then validate.py should report INVALID with Flaws A+B (object paths), while Flaw C
slips past mechanical checks and is left for the LLM judge.
"""
import json, shutil
from pathlib import Path

SRC = Path("artifacts/gingerpeople")
DST = Path("artifacts/gingerpeople_degraded")


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def dump(p, obj):
    Path(p).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST)

    # --- Flaw A: confidence<->basis mismatch on experiments[3] -------------------
    exps = load(DST / "reason/experiments.json")
    e = exps["experiments"]
    e[3]["confidence"] = 92  # basis is "pattern / best-practice" (band 65-72) -> mismatch

    # --- Flaw C: replace experiments[2] with a generic, judge-catchable experiment ---
    # keep exp_id (so synthesis refs stay valid), pillar, a resolvable signal + existing
    # screenshot, and an OVERLAPPING store_profile_ref so it passes validate.py mechanically.
    e[2]["title"] = "Add urgency timers and exit-intent popups to lift conversion"
    e[2]["affected_surface"] = "site-wide"
    e[2]["hypothesis"] = ("Adding countdown timers, low-stock badges and exit-intent popups "
                          "creates urgency and lifts conversion, as it does on most ecommerce sites.")
    e[2]["primary_change"] = "Add countdown timers, low-stock banners and exit-intent email popups site-wide."
    e[2]["primary_kpi"] = "Conversion rate"
    e[2]["decision_rule"] = "Ship if conversion rate improves."
    e[2]["expected_lift"] = {"low": 5, "high": 12, "unit": "%"}
    e[2]["confidence"] = 70
    e[2]["confidence_basis"] = "pattern / best-practice"   # coherent -> passes the band check
    e[2]["evidence"]["store_profile_ref"] = "segment:candy-snacker"  # overlaps -> passes specificity check
    # signal_type/visual signal + screenshot left as-is (resolvable)
    dump(DST / "reason/experiments.json", exps)

    # --- Flaw B: fabricated tech-check Pass -------------------------------------
    tech = load(DST / "reason/tech_checks.json")
    for c in tech["checks"]:
        if c["name"] == "Sitemap":
            c["status"] = "Pass"
            c["detail"] = "Sitemap present and valid."
            c["grounded_in"] = "not inspected"  # Pass with unresolvable grounding -> validate catches
    dump(DST / "reason/tech_checks.json", tech)

    # --- notes for Codex --------------------------------------------------------
    (DST / "DEGRADED_NOTES.md").write_text(
        "# gingerpeople_degraded — injected flaws (eval-loop demo input)\n\n"
        "Schema-valid copy of artifacts/gingerpeople/ with three injected quality flaws.\n\n"
        "| # | Class | Object path | Caught by | What's wrong |\n"
        "|---|---|---|---|---|\n"
        "| A | confidence coherence | `experiments[3].confidence` | validate.py | 92 with basis 'pattern / best-practice' (band 65-72) |\n"
        "| B | tech truthfulness | `tech_checks[2]` (Sitemap) | validate.py | Pass with unresolvable grounded_in |\n"
        "| C | store specificity / generic advice | `experiments[2]` | LLM judge | mechanically valid but generic CRO boilerplate (urgency timers/popups) |\n\n"
        "Expected loop: validate.py -> INVALID on A+B with object paths; judge -> flags C "
        "(low specificity / weak evidence-claim coherence) despite passing mechanical checks. "
        "Repair the three sections, re-validate + re-score, and record the before->after delta.\n",
        encoding="utf-8")
    print(f"wrote {DST} (flaws A,B = validate-catchable; C = judge-catchable)")


if __name__ == "__main__":
    main()
