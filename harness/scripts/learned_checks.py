#!/usr/bin/env python3
"""learned_checks.py — additive, data-driven deterministic checks.

Learned rules live in `harness/learned/registry.json` as DATA (patterns + parameters),
not generated code. Each rule's `type` maps to a vetted function here. This module is
ADDITIVE: it never imports from or modifies validate.py / score_report.py, so a learned
rule can never break the existing eval contract — at worst it emits an advisory finding.

`self_learn.py` proposes new rules and gates them before they are committed here.

Usage:
    python -m harness.scripts.learned_checks artifacts/<store>
    python -m harness.scripts.learned_checks --known-bad fixtures/learning/known_bad_generic.json
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from typing import Any

LEARNED_DIR = Path(__file__).resolve().parents[1] / "learned"
REGISTRY_PATH = LEARNED_DIR / "registry.json"


# ---- store_profile -> token set (for "is this store-specific?" tests) -------
def profile_tokens(store_profile: dict[str, Any]) -> set[str]:
    toks: set[str] = set()
    toks.add(store_profile.get("niche", ""))
    for fam in store_profile.get("families", []):
        toks.add(fam.get("name", ""))
        toks.update(fam.get("products", []))
    for key in ("jobs_to_be_done", "segments", "proof_points", "content_themes"):
        toks.update(store_profile.get(key, []))
    # split multiword tokens into words too, so "GIN GINS" matches "gin gins" substrings
    out: set[str] = set()
    for t in toks:
        t = (t or "").strip().lower()
        if len(t) >= 3:
            out.add(t)
    return out


# ---- rule types (vetted; registry only supplies parameters) -----------------
def _rule_generic_phrasing(rule: dict, experiments: list[dict], tokens: set[str]) -> list[dict]:
    """Flag an experiment whose text uses generic-CRO boilerplate AND carries no
    store-specific token — a deterministic proxy for the judge's 'generic recommendation'."""
    patterns = [p.lower() for p in rule.get("patterns", [])]
    findings = []
    for i, e in enumerate(experiments):
        text = " ".join(str(e.get(k, "")) for k in ("title", "hypothesis", "primary_change")).lower()
        if not any(p in text for p in patterns):
            continue
        if any(tok in text for tok in tokens):
            continue  # generic phrasing but still store-specific -> not a violation
        findings.append({
            "path": f"experiments[{i}]",
            "rule_id": rule.get("id", "generic_phrasing"),
            "severity": rule.get("severity", "warn"),
            "detail": rule.get("detail", "generic CRO phrasing without store-specific grounding"),
        })
    return findings


RULE_TYPES = {"generic_phrasing": _rule_generic_phrasing}


# ---- engine -----------------------------------------------------------------
def load_registry(path: Path | str = REGISTRY_PATH) -> dict:
    p = Path(path)
    if not p.exists():
        return {"rules": []}
    return json.loads(p.read_text(encoding="utf-8"))


def run_rules(experiments: list[dict], store_profile: dict, registry: dict | None = None) -> list[dict]:
    registry = registry if registry is not None else load_registry()
    tokens = profile_tokens(store_profile or {})
    findings: list[dict] = []
    for rule in registry.get("rules", []):
        fn = RULE_TYPES.get(rule.get("type"))
        if fn is None:
            continue  # unknown rule type -> ignore (forward-compatible, never errors)
        findings.extend(fn(rule, experiments, tokens))
    return findings


def run_on_store(store_root: Path | str, registry: dict | None = None) -> list[dict]:
    root = Path(store_root)
    reason = root / "reason"
    experiments = json.loads((reason / "experiments.json").read_text(encoding="utf-8")).get("experiments", [])
    store_profile = json.loads((reason / "store_profile.json").read_text(encoding="utf-8"))
    return run_rules(experiments, store_profile, registry)


def run_on_example(example_path: Path | str, registry: dict | None = None) -> list[dict]:
    data = json.loads(Path(example_path).read_text(encoding="utf-8"))
    return run_rules(data.get("experiments", []), data.get("store_profile", {}), registry)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run learned deterministic checks (advisory).")
    ap.add_argument("store_root", nargs="?", help="artifacts/<store>")
    ap.add_argument("--known-bad", help="a known-bad example JSON (experiments+store_profile)")
    ap.add_argument("--registry", default=None)
    args = ap.parse_args(argv)
    registry = load_registry(args.registry) if args.registry else load_registry()

    if args.known_bad:
        findings = run_on_example(args.known_bad, registry)
    elif args.store_root:
        findings = run_on_store(args.store_root, registry)
    else:
        ap.error("provide a store_root or --known-bad")

    if not findings:
        print("learned checks: no findings")
    else:
        print(f"learned checks: {len(findings)} finding(s)")
        for f in findings:
            print(f"  - {f['path']} [{f['rule_id']}] {f['detail']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
