"""Tests for the self-learning loop and its safety gate."""
import json
from pathlib import Path

from harness.scripts import learned_checks, self_learn

ROOT = Path(__file__).resolve().parents[1]
KNOWN_BAD = ROOT / "fixtures" / "learning" / "known_bad_generic.json"
PASSING = ROOT / "fixtures" / "sample_store"


def _candidate():
    return self_learn.REMEDIATIONS["generic_recommendation"](5)


def test_generic_rule_flags_generic_but_not_specific():
    reg = {"rules": [_candidate()]}
    findings = learned_checks.run_on_example(KNOWN_BAD, reg)
    paths = {f["path"] for f in findings}
    assert "experiments[0]" in paths            # generic urgency/popup experiment -> flagged
    assert "experiments[1]" not in paths        # GIN GINS buying-box experiment -> not flagged


def test_rule_does_not_fire_on_passing_fixture():
    reg = {"rules": [_candidate()]}
    assert learned_checks.run_on_store(PASSING, reg) == []


def test_token_suppression_spares_store_specific_generic_phrasing():
    # generic phrase present BUT a store token present -> not a violation
    exps = [{"title": "Add a countdown timer to the GIN GINS launch", "hypothesis": "", "primary_change": ""}]
    profile = {"families": [{"name": "GIN GINS"}]}
    assert learned_checks.run_rules(exps, profile, {"rules": [_candidate()]}) == []


def test_aggregate_ranks_generic_recommendation_top():
    counter = self_learn.aggregate()
    assert counter["generic_recommendation"] >= counter["unsupported_evidence"]
    assert counter["generic_recommendation"] >= 1


def test_select_skips_already_covered_categories():
    # confidence / technical_truthfulness are caught by validate.py -> no remediation offered
    assert "confidence" not in self_learn.REMEDIATIONS
    assert "technical_truthfulness" not in self_learn.REMEDIATIONS


def test_select_returns_nothing_when_rule_already_present():
    counter = self_learn.aggregate()
    registry_with_rule = {"rules": [_candidate()]}
    assert self_learn.select_candidate(counter, registry_with_rule) is None


def test_gate_accepts_real_candidate():
    ok, reasons = self_learn.gate(_candidate(), self_learn.DEFAULT_GOOD, KNOWN_BAD, run_tests=False)
    assert ok, reasons


def test_gate_rejects_rule_with_no_true_positive():
    bad = dict(_candidate(), id="noop", patterns=["zzz-nonexistent-phrase"])
    ok, reasons = self_learn.gate(bad, self_learn.DEFAULT_GOOD, KNOWN_BAD, run_tests=False)
    assert not ok
    assert any("true positive" in r for r in reasons)


def test_gate_rejects_rule_that_false_positives_on_good_audit(tmp_path):
    # an over-broad rule that flags a store-specific good experiment must be rejected
    good = tmp_path / "store"
    (good / "reason").mkdir(parents=True)
    (good / "reason" / "experiments.json").write_text(json.dumps({"experiments": [
        {"title": "Add a countdown timer", "hypothesis": "generic", "primary_change": "generic"}]}), encoding="utf-8")
    (good / "reason" / "store_profile.json").write_text(json.dumps({"families": [{"name": "Acme"}]}), encoding="utf-8")
    ok, reasons = self_learn.gate(_candidate(), [good], KNOWN_BAD, run_tests=False)
    assert not ok
    assert any("false positive" in r for r in reasons)
