#!/usr/bin/env python3
"""Merge LLM judge results into a deterministic eval report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def merge_judge_results(eval_dir: str | Path, judge_results: list[dict[str, Any]]) -> dict[str, Any]:
    out_dir = Path(eval_dir)
    report_path = out_dir / "eval_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))

    average = round(sum(result["score"] for result in judge_results) / len(judge_results), 2) if judge_results else 0
    judge_failures = []
    for result in judge_results:
        for path in result.get("failing_object_paths", []):
            judge_failures.append(
                {
                    "task_id": result["task_id"],
                    "path": path,
                    "rationale": result.get("rationale", ""),
                }
            )

    report["judge_results"] = judge_results
    report["judge_score_average"] = average
    report["judge_failures"] = judge_failures
    report["acceptance"]["judge_threshold"] = 80
    report["acceptance"]["passes"] = bool(
        report["acceptance"].get("passes")
        and average >= 80
        and not judge_failures
        and not _has_evidence_support_failure(judge_results)
    )

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "eval_summary.md").write_text(_render_summary(report), encoding="utf-8")
    return report


def _has_evidence_support_failure(judge_results: list[dict[str, Any]]) -> bool:
    for result in judge_results:
        if result.get("score", 100) < 80 and "evidence" in result.get("rationale", "").lower():
            return True
    return False


def _render_summary(report: dict[str, Any]) -> str:
    lines = [
        f"# Eval Summary - {report['store']}",
        "",
        f"Deterministic score: {report['overall_score']}/100",
        f"Judge average: {report.get('judge_score_average', 0)}/100",
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
    lines.extend(["", "## Judge Results", ""])
    for result in report.get("judge_results", []):
        paths = ", ".join(f"`{path}`" for path in result.get("failing_object_paths", [])) or "none"
        lines.append(f"- `{result['task_id']}`: {result['score']}/100; failures: {paths}; {result.get('rationale', '')}")
    lines.extend(["", "## Repair Prompts", ""])
    if not report.get("judge_failures"):
        lines.append("No judge repair prompts.")
    else:
        for failure in report["judge_failures"]:
            lines.append(f"- Repair `{failure['path']}` from `{failure['task_id']}`: {failure['rationale']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Merge LLM judge results into eval_report.json.")
    parser.add_argument("eval_dir", help="Directory containing eval_report.json")
    parser.add_argument("judge_results", help="JSON file containing an array of judge results")
    args = parser.parse_args(argv)

    results = json.loads(Path(args.judge_results).read_text(encoding="utf-8"))
    report = merge_judge_results(args.eval_dir, results)
    print(json.dumps(report, indent=2))
    return 0 if report["acceptance"]["passes"] else 1


if __name__ == "__main__":
    sys.exit(main())
