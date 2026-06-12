---
name: evaluate-audit
description: Evaluate a completed Qosmic audit artifact tree, run deterministic checks, perform LLM judge passes, and emit repair-ready eval output.
---

# Evaluate Audit

Use this skill after an audit run has produced a store artifact root containing:

- `manifest.json`
- per-surface `page.json` files
- `reason/*.json`
- optionally `sample_output/<store>.md`

The artifact root should look like `artifacts/<store>/` in real runs or `fixtures/sample_store/` in tests.

## Step 1: Run deterministic validation

```bash
python -m harness.scripts.validate <store_root> --json
```

If Layer-1 validation fails, do not judge prose quality yet. Report the object paths and ask the audit agent to regenerate only the failed JSON section.

## Step 2: Run deterministic scoring

```bash
python -m harness.scripts.score_report <store_root>
```

This writes:

- `<store_root>/eval/eval_report.json`
- `<store_root>/eval/eval_summary.md`

`score_report.py` is deterministic and API-key-free. It does not call an LLM. It emits `judge_tasks[]` for this skill to complete.

## Step 3: Run LLM judge tasks

For each `judge_tasks[]` item:

- If `type=experiment`, inspect the cited experiment, its `evidence`, the referenced page/signal, `store_profile.json`, and screenshot if available.
- Score 0-100 for whether the evidence supports the hypothesis and whether the recommendation is store-specific.
- If `type=executive_summary`, compare the rendered executive summary, `synthesis.json`, and the top-ranked experiments.

Each judge result must be JSON:

```json
{
  "task_id": "judge-experiment-1",
  "score": 85,
  "rationale": "Evidence directly supports the purchase-path hypothesis and the change names the observed product family.",
  "failing_object_paths": []
}
```

## Step 4: Merge judge results

Save the judge output array as `<store_root>/eval/judge_results.json`, then merge it:

```bash
python -m harness.scripts.merge_judge_results <store_root>/eval <store_root>/eval/judge_results.json
```

This updates `eval_report.json` with:

- `judge_results[]`
- `judge_score_average`
- any new failures from `failing_object_paths[]`
- an updated `acceptance.passes` value

Acceptance requires:

- Layer-1 validation passes.
- deterministic `overall_score >= 80`.
- no zero in evidence resolvability, technical truthfulness, or store specificity.
- judge score average is at least 80.
- no judge failure on `evidence_supports_hypothesis`.

Then update `eval_summary.md` with a concise human-readable critique and repair instructions grouped by failure type.

## Repair Loop

Repair prompts should be targeted. Name the exact object path and failure mode:

- `experiments[3].evidence.triggering_signal`: unresolved visual finding.
- `experiments[6].evidence.store_profile_ref`: no overlap with store profile.
- `tech_checks[2].grounded_in`: `Pass` status lacks artifact proof.

Regenerate only the failed section, then rerun this skill from Step 1.
