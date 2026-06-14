#!/usr/bin/env python3
"""run_audit.py — end-to-end orchestrator for a Qosmic audit.

Chains the scriptable phases and clearly marks the one agent (LLM) step:

    crawl (extract.py)  ->  [REASON: run the reason-audit skill]  ->  write (render_report.py)
                                                                  ->  validate.py  ->  score_report.py

Because Reason is an LLM step (the agent reads artifacts + screenshots and authors
reason/*.json), this runner does the deterministic bookends and stops to hand off to
the agent when reason/ is missing. Re-run after reasoning to finish + evaluate.

Examples:
    # fresh store: crawl, then hand off to the reason-audit skill
    python run_audit.py --store acme --url https://acme.com/ --url https://acme.com/products/x

    # after the agent has written artifacts/acme/reason/*.json: write + validate + score
    python run_audit.py --store acme --skip-crawl
"""
import argparse, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable


def run(cmd, **kw):
    print(f"\n$ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, **kw)


def main():
    ap = argparse.ArgumentParser(description="Run an end-to-end Qosmic audit.")
    ap.add_argument("--store", required=True, help="store slug, e.g. gingerpeople")
    ap.add_argument("--url", action="append", default=[], help="surface URL (repeatable)")
    ap.add_argument("--out", default=None, help="artifact root (default artifacts/<store>)")
    ap.add_argument("--skip-crawl", action="store_true")
    ap.add_argument("--skip-eval", action="store_true")
    args = ap.parse_args()

    out = Path(args.out or f"artifacts/{args.store}")

    # 1) Crawl
    if args.url and not args.skip_crawl:
        r = run([PY, "harness/scripts/extract.py", "--store", args.store, "--out", str(out), *args.url])
        if r.returncode != 0:
            print("crawl failed"); return 1
    elif not args.skip_crawl and not args.url:
        print("No --url given and --skip-crawl not set; assuming artifacts already crawled.")

    # 2) Reason (agent step) — stop here if reason artifacts are missing
    if not (out / "reason" / "experiments.json").exists():
        print(f"\n>>> REASON STEP (agent): run the `reason-audit` skill on {out}")
        print(f"    It reads {out}/manifest.json + page.json + screenshots and writes {out}/reason/*.json.")
        print(f"    Then re-run: python run_audit.py --store {args.store} --skip-crawl")
        return 0

    # 3) Write
    r = run([PY, "harness/scripts/render_report.py", str(out)])
    if r.returncode != 0:
        print("render failed"); return 1

    # 4) Validate
    r = run([PY, "harness/scripts/validate.py", str(out)])
    valid = r.returncode == 0

    # 4b) Advisory: learned deterministic checks promoted by self_learn.py (non-fatal)
    try:
        sys.path.insert(0, str(ROOT))
        from harness.scripts import learned_checks
        findings = learned_checks.run_on_store(out)
        if findings:
            print(f"\n[learned-checks] {len(findings)} advisory finding(s):")
            for f in findings:
                print(f"  - {f['path']} [{f['rule_id']}] {f['detail']}")
    except Exception:
        pass

    # 5) Score
    if valid and not args.skip_eval:
        env = dict(os.environ, PYTHONPATH=str(ROOT))
        run([PY, "harness/scripts/score_report.py", str(out)], env=env)
        summary = out / "eval" / "eval_summary.md"
        if summary.exists():
            line = next((l for l in summary.read_text(encoding="utf-8").splitlines()
                         if l.lower().startswith("overall score")), "")
            print(f"\n=== {args.store}: report=sample_output/{args.store}.md | validate={'VALID' if valid else 'INVALID'} | {line} ===")
    else:
        print(f"\n=== {args.store}: validate={'VALID' if valid else 'INVALID'} (eval skipped) ===")
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
