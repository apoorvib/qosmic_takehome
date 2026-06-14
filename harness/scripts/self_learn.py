#!/usr/bin/env python3
"""self_learn.py — git-gated self-improvement loop for the eval system.

Closes the "failures become harness changes, gated on a holdout" lane of EVAL_LOOP.md
as running code, with hard safety guarantees so an autonomous run can never leave the
repo broken.

WHAT IT DOES
  1. AGGREGATE  failures across a committed corpus (+ optional live eval reports),
                cluster by category.
  2. PROPOSE    one additive improvement for the top *mechanizable, not-yet-covered*
                cluster — a DATA-only rule appended to harness/learned/registry.json
                (interpreted by a vetted function in learned_checks.py; no code is
                generated or executed).
  3. GATE       before keeping anything:
                  - no false positives on known-GOOD audits (regression guard)
                  - true positive on a committed known-BAD example (it must actually help)
                  - the existing test suite still passes (don't break existing code)
                  - the eval contract still validates the passing fixture
  4. COMMIT     only if the gate passes — a scoped, revertible git commit touching
                ONLY the learned-rule files. Otherwise the working tree is restored
                from an in-memory snapshot and nothing is kept.

SAFETY INVARIANTS
  * Proposals are DATA, never generated/executed code.
  * Scoped commits via pathspec (`git commit -- <paths>`); never `git add -A`; the
    user's other staged/untracked files are left untouched.
  * Gate runs BEFORE commit; any failure -> full restore, no commit.
  * Each accepted change is its own commit -> `git revert <hash>` undoes exactly it.

Usage:
    python -m harness.scripts.self_learn --dry-run     # analyze + gate, change nothing
    python -m harness.scripts.self_learn --no-commit   # apply + gate, keep tree, no commit
    python -m harness.scripts.self_learn               # apply + gate + commit on pass
"""
from __future__ import annotations
import argparse, json, subprocess, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEARNED_DIR = ROOT / "harness" / "learned"
REGISTRY_PATH = LEARNED_DIR / "registry.json"
LOG_PATH = LEARNED_DIR / "learning_log.jsonl"
CORPUS = ROOT / "fixtures" / "learning" / "failure_corpus.jsonl"
KNOWN_BAD = ROOT / "fixtures" / "learning" / "known_bad_generic.json"
PASSING_FIXTURE = ROOT / "fixtures" / "sample_store"
DEFAULT_GOOD = [PASSING_FIXTURE, ROOT / "artifacts" / "gingerpeople", ROOT / "artifacts" / "zenrojas"]

sys.path.insert(0, str(ROOT))
from harness.scripts import learned_checks  # noqa: E402
from harness.scripts.validate import validate_audit  # noqa: E402

# category -> a vetted remediation (DATA appended to the registry). Only categories that
# are mechanizable AND not already covered by validate.py appear here.
REMEDIATIONS = {
    "generic_recommendation": lambda n: {
        "id": "generic_recommendation",
        "type": "generic_phrasing",
        "patterns": ["urgency timer", "countdown timer", "exit-intent popup", "exit intent popup",
                     "low-stock badge", "low stock badge", "social proof badge", "scarcity banner",
                     "flash sale", "fomo"],
        "severity": "warn",
        "detail": f"generic CRO tactic without store-specific grounding (promoted from {n} recurring judge findings)",
        "added_by": "self_learn",
    },
}


# ---- 1. aggregate -----------------------------------------------------------
def aggregate(corpus: Path = CORPUS, live_glob: str = "artifacts/*/eval/eval_report.json") -> Counter:
    counter: Counter = Counter()
    if corpus.exists():
        for line in corpus.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            counter[rec["category"]] += 1
    # best-effort live ingestion (never required; never fatal)
    for report in ROOT.glob(live_glob):
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
            for err in data.get("layer1", {}).get("errors", []):
                counter[err.get("category", "unknown")] += 1
            jr = report.parent / "judge_results.json"
            if jr.exists():
                for task in json.loads(jr.read_text(encoding="utf-8")):
                    if task.get("failing_object_paths"):
                        r = (task.get("rationale", "")).lower()
                        cat = "generic_recommendation" if ("generic" in r or "not specific" in r or "store-specific" in r) \
                            else "unsupported_evidence"
                        counter[cat] += 1
        except Exception:
            continue
    return counter


def select_candidate(counter: Counter, registry: dict) -> tuple[str, dict] | None:
    have = {r.get("id") for r in registry.get("rules", [])}
    ranked = [(cat, n) for cat, n in counter.most_common()
              if cat in REMEDIATIONS and REMEDIATIONS[cat](n)["id"] not in have]
    if not ranked:
        return None
    cat, n = ranked[0]
    return cat, REMEDIATIONS[cat](n)


# ---- 3. gate ----------------------------------------------------------------
def _snapshot(paths: list[Path]) -> dict[Path, bytes | None]:
    return {p: (p.read_bytes() if p.exists() else None) for p in paths}


def _restore(snap: dict[Path, bytes | None]) -> None:
    for p, data in snap.items():
        if data is None:
            if p.exists():
                p.unlink()
        else:
            p.write_bytes(data)


def gate(candidate_rule: dict, good: list[Path], known_bad: Path, run_tests: bool = True) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    reg = learned_checks.load_registry()
    reg.setdefault("rules", []).append(candidate_rule)

    # (a) regression guard: zero findings on known-good audits
    for src in good:
        if not (src / "reason" / "experiments.json").exists():
            continue  # holdout audit not present locally -> skip (corpus/fixture still gate)
        f = learned_checks.run_on_store(src, reg)
        if f:
            reasons.append(f"false positive on good audit {src.name}: {len(f)} finding(s) -> would regress")

    # (b) true positive: the CANDIDATE (in isolation) must catch the targeted failure
    tp = learned_checks.run_on_example(known_bad, {"rules": [candidate_rule]})
    if not tp:
        reasons.append("no true positive on the known-bad example -> change does not address the failure")

    # (c) the existing test suite must still pass (don't break existing code)
    if run_tests:
        r = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"],
                           cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            reasons.append(f"test suite failed:\n{r.stdout[-600:]}")

    # (d) the eval contract still validates the passing fixture
    if not validate_audit(PASSING_FIXTURE).ok:
        reasons.append("passing fixture no longer validates -> contract regression")

    return (len(reasons) == 0, reasons)


# ---- git (scoped, safe) -----------------------------------------------------
def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def scoped_commit(paths: list[Path], message: str) -> str | None:
    rels = [str(p.relative_to(ROOT)).replace("\\", "/") for p in paths if p.exists()]
    add = _git("add", "--", *rels)
    if add.returncode != 0:
        return None
    commit = _git("commit", "-m", message, "--", *rels)  # pathspec -> ONLY these files
    if commit.returncode != 0:
        return None
    return _git("rev-parse", "--short", "HEAD").stdout.strip()


# ---- orchestrate ------------------------------------------------------------
def apply_rule(candidate_rule: dict) -> None:
    reg = learned_checks.load_registry()
    reg.setdefault("rules", []).append(candidate_rule)
    REGISTRY_PATH.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def log_attempt(entry: dict) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run(dry_run: bool = False, no_commit: bool = False, good: list[Path] | None = None) -> int:
    good = good or DEFAULT_GOOD
    counter = aggregate()
    print("Aggregated failure clusters:", dict(counter.most_common()))
    registry = learned_checks.load_registry()
    picked = select_candidate(counter, registry)
    if not picked:
        print("No actionable cluster (nothing mechanizable + uncovered). Nothing to do.")
        return 0
    category, rule = picked
    print(f"Top actionable cluster: '{category}' (x{counter[category]}) -> propose rule '{rule['id']}' (type={rule['type']})")

    passed, reasons = gate(rule, good, KNOWN_BAD)
    print(f"\nGATE: {'PASS' if passed else 'FAIL'}")
    for r in reasons:
        print(f"  - {r}")

    if dry_run:
        print("\n[dry-run] no changes written.")
        return 0 if passed else 1

    if not passed:
        print("\nRejected: change not kept, working tree untouched.")
        return 1

    # apply (snapshot first so we can restore if commit fails)
    snap = _snapshot([REGISTRY_PATH, LOG_PATH])
    apply_rule(rule)
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "category": category,
             "rule_id": rule["id"], "type": rule["type"], "count": counter[category], "accepted": True}
    log_attempt(entry)

    if no_commit:
        print("\n[--no-commit] rule applied to working tree (not committed).")
        return 0

    msg = (f"self-learn: add deterministic check '{rule['id']}' for {category}\n\n"
           f"Promoted from {counter[category]} recurring failures. Gated: 0 FP on known-good audits, "
           f"TP on known-bad example, test suite green, passing fixture still valid.")
    h = scoped_commit([REGISTRY_PATH, LOG_PATH], msg)
    if h is None:
        _restore(snap)
        print("\nCommit failed -> working tree restored, nothing kept.")
        return 1
    print(f"\nCommitted {h} (scoped to harness/learned/). To undo exactly this change:  git revert {h}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Git-gated self-learning loop for the eval system.")
    ap.add_argument("--dry-run", action="store_true", help="analyze + gate only; write nothing")
    ap.add_argument("--no-commit", action="store_true", help="apply + gate; keep working tree; do not commit")
    args = ap.parse_args(argv)
    return run(dry_run=args.dry_run, no_commit=args.no_commit)


if __name__ == "__main__":
    raise SystemExit(main())
