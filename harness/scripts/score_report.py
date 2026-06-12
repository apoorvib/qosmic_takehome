#!/usr/bin/env python3
"""Deterministic scoring for Qosmic audit artifacts.

This script performs mechanical scoring only. It emits LLM judge tasks for the
evaluate-audit skill to run and merge later.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from harness.scripts.validate import PILLARS, ValidationError, validate_audit


DIMENSIONS = {
    "structure_compliance": {"weight": 15, "categories": {"schema", "contract"}},
    "evidence_resolvability": {"weight": 15, "categories": {"evidence"}},
    "evidence_claim_coherence": {"weight": 20, "categories": {"confidence"}},
    "pillar_coverage": {"weight": 10, "paths": {"experiments[*].pillar"}},
    "store_specificity": {"weight": 15, "categories": {"specificity"}},
    "technical_truthfulness": {"weight": 10, "categories": {"technical_truthfulness"}},
    "competitor_grounding": {"weight": 5, "paths": {"competitors"}},
    "report_quality": {"weight": 10, "categories": set()},
}


def score_audit(store_root: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(store_root)
    validation = validate_audit(root)
    errors = validation.errors
    experiments = _load_optional(root / "reason" / "experiments.json", {}).get("experiments", [])
    synthesis = _load_optional(root / "reason" / "synthesis.json", {})
    manifest = _load_optional(root / "manifest.json", {})

    dimension_scores = _score_dimensions(errors, experiments)
    judge_tasks = _build_judge_tasks(experiments, synthesis)
    overall = sum(item["score"] for item in dimension_scores.values())

    report = {
        "store": manifest.get("store", root.name),
        "store_root": str(root),
        "overall_score": overall,
        "acceptance": {
            "passes": validation.ok and overall >= 80 and _no_zero_critical_dimensions(dimension_scores),
            "threshold": 80,
            "critical_dimensions": [
                "evidence_resolvability",
                "technical_truthfulness",
                "store_specificity",
            ],
        },
        "layer1": validation.to_dict(),
        "dimension_scores": dimension_scores,
        "judge_tasks": judge_tasks,
    }

    out_dir = Path(output_dir) if output_dir else root / "eval"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "eval_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "eval_summary.md").write_text(_render_summary(report), encoding="utf-8")
    return report


def _score_dimensions(errors: list[ValidationError], experiments: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    scores: dict[str, dict[str, Any]] = {}
    for name, config in DIMENSIONS.items():
        failures = _matching_failures(errors, config)
        weight = config["weight"]
        if name == "evidence_claim_coherence":
            coherence_errors = _evidence_errors(errors) + _matching_failures(errors, config)
            score = weight if not coherence_errors else max(0, weight - 5 * len(coherence_errors))
        elif name == "report_quality":
            score = weight if len(experiments) == 10 and not _schema_errors(errors) else max(0, weight - 5)
        else:
            score = weight if not failures else 0
        scores[name] = {
            "weight": weight,
            "score": score,
            "failures": [failure.__dict__ for failure in failures],
        }
    return scores


def _matching_failures(errors: list[ValidationError], config: dict[str, Any]) -> list[ValidationError]:
    categories = config.get("categories", set())
    paths = config.get("paths", set())
    matched = []
    for error in errors:
        if error.category in categories or error.path in paths:
            matched.append(error)
    return matched


def _evidence_errors(errors: list[ValidationError]) -> list[ValidationError]:
    return [error for error in errors if error.category == "evidence"]


def _schema_errors(errors: list[ValidationError]) -> list[ValidationError]:
    return [error for error in errors if error.category == "schema"]


def _no_zero_critical_dimensions(scores: dict[str, dict[str, Any]]) -> bool:
    return all(scores[name]["score"] > 0 for name in ("evidence_resolvability", "technical_truthfulness", "store_specificity"))


def _build_judge_tasks(experiments: list[dict[str, Any]], synthesis: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = []
    for idx, experiment in enumerate(experiments):
        tasks.append(
            {
                "id": f"judge-experiment-{idx + 1}",
                "type": "experiment",
                "object_path": f"experiments[{idx}]",
                "exp_id": experiment.get("exp_id"),
                "checks": [
                    "evidence_supports_hypothesis",
                    "recommendation_is_store_specific",
                ],
                "input_refs": {
                    "evidence": experiment.get("evidence", {}),
                    "hypothesis": experiment.get("hypothesis", ""),
                    "primary_change": experiment.get("primary_change", ""),
                },
                "expected_output_schema": {
                    "score": "0-100 integer",
                    "rationale": "short string",
                    "failing_object_paths": "array of object-path strings",
                },
            }
        )
    tasks.append(
        {
            "id": "judge-executive-summary",
            "type": "executive_summary",
            "object_path": "executive_summary",
            "checks": ["summary_faithful_to_synthesis_and_top_leaks"],
            "input_refs": {
                "headline": synthesis.get("headline", ""),
                "themes": synthesis.get("themes", []),
            },
            "expected_output_schema": {
                "score": "0-100 integer",
                "rationale": "short string",
                "failing_object_paths": "array of object-path strings",
            },
        }
    )
    return tasks


def _render_summary(report: dict[str, Any]) -> str:
    lines = [
        f"# Eval Summary - {report['store']}",
        "",
        f"Overall score: {report['overall_score']}/100",
        f"Layer-1 validation: {'PASS' if report['layer1']['ok'] else 'FAIL'}",
        f"Acceptance: {'PASS' if report['acceptance']['passes'] else 'FAIL'}",
        "",
        "## Dimension Scores",
        "",
        "| Dimension | Score | Weight | Failures |",
        "|---|---:|---:|---:|",
    ]
    for name, dimension in report["dimension_scores"].items():
        lines.append(f"| {name} | {dimension['score']} | {dimension['weight']} | {len(dimension['failures'])} |")
    lines.extend(["", "## Layer-1 Failures", ""])
    if not report["layer1"]["errors"]:
        lines.append("No Layer-1 failures.")
    else:
        for failure in report["layer1"]["errors"]:
            lines.append(f"- `{failure['path']}`: {failure['message']}")
    lines.extend(["", "## Judge Tasks", "", f"{len(report['judge_tasks'])} judge tasks emitted."])
    return "\n".join(lines) + "\n"


def _load_optional(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score Qosmic audit artifacts deterministically.")
    parser.add_argument("store_root", help="Store artifact root, e.g. fixtures/sample_store")
    parser.add_argument("--output-dir", default=None, help="Directory for eval_report.json and eval_summary.md")
    args = parser.parse_args(argv)
    report = score_audit(args.store_root, args.output_dir)
    print(json.dumps(report, indent=2))
    return 0 if report["acceptance"]["passes"] else 1


if __name__ == "__main__":
    sys.exit(main())
