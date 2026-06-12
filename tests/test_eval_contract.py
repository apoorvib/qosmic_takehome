from pathlib import Path

from harness.scripts.merge_judge_results import merge_judge_results
from harness.scripts.score_report import score_audit
from harness.scripts.validate import validate_audit


ROOT = Path(__file__).resolve().parents[1]
PASSING_STORE = ROOT / "fixtures" / "sample_store"
BROKEN_STORE = ROOT / "fixtures" / "sample_store_broken"


def test_validate_accepts_passing_fixture():
    result = validate_audit(PASSING_STORE)

    assert result.ok
    assert result.errors == []


def test_validate_reports_all_seeded_broken_fixture_failures():
    result = validate_audit(BROKEN_STORE)

    assert not result.ok
    paths = {error.path for error in result.errors}
    assert "experiments" in paths
    assert "experiments[*].pillar" in paths
    assert "experiments[0].evidence.screenshot" in paths
    assert "experiments[1].confidence" in paths
    assert "experiments[2].evidence.store_profile_ref" in paths
    assert "experiments[3].evidence.triggering_signal" in paths
    assert "tech_checks[2].grounded_in" in paths


def test_score_report_emits_scores_and_judge_tasks_for_passing_fixture(tmp_path):
    report = score_audit(PASSING_STORE, output_dir=tmp_path)

    assert report["store"] == "sample-ginger-co"
    assert report["layer1"]["ok"] is True
    assert report["overall_score"] >= 80
    assert report["dimension_scores"]["evidence_resolvability"]["score"] > 0
    assert report["dimension_scores"]["technical_truthfulness"]["score"] > 0
    assert report["dimension_scores"]["store_specificity"]["score"] > 0
    assert len(report["judge_tasks"]) == 11
    assert {task["type"] for task in report["judge_tasks"]} == {
        "experiment",
        "executive_summary",
    }
    assert (tmp_path / "eval_report.json").exists()
    assert (tmp_path / "eval_summary.md").exists()


def test_score_report_surfaces_broken_fixture_failures(tmp_path):
    report = score_audit(BROKEN_STORE, output_dir=tmp_path)

    assert report["layer1"]["ok"] is False
    assert report["overall_score"] < 80
    failing_paths = {
        failure["path"]
        for dimension in report["dimension_scores"].values()
        for failure in dimension["failures"]
    }
    assert "experiments[0].evidence.screenshot" in failing_paths
    assert "experiments[2].evidence.store_profile_ref" in failing_paths
    assert "tech_checks[2].grounded_in" in failing_paths


def test_merge_judge_results_updates_acceptance_and_summary(tmp_path):
    score_audit(PASSING_STORE, output_dir=tmp_path)
    judge_results = [
        {
            "task_id": "judge-experiment-1",
            "score": 90,
            "rationale": "Evidence supports the recommendation.",
            "failing_object_paths": [],
        },
        {
            "task_id": "judge-executive-summary",
            "score": 70,
            "rationale": "Summary misses one top leak.",
            "failing_object_paths": ["executive_summary"],
        },
    ]

    merged = merge_judge_results(tmp_path, judge_results)

    assert merged["judge_score_average"] == 80
    assert merged["acceptance"]["passes"] is False
    assert merged["judge_failures"] == [
        {
            "task_id": "judge-executive-summary",
            "path": "executive_summary",
            "rationale": "Summary misses one top leak.",
        }
    ]
    assert "Judge Results" in (tmp_path / "eval_summary.md").read_text(encoding="utf-8")
