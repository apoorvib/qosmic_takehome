---
name: write-report
description: Phase 3 of a Qosmic audit. Use after reason-audit has emitted artifacts/<store>/reason/*.json. Validates the structured intermediates, composes the executive summary, and assembles the final report into sample_output/<store>.md matching the Qosmic output contract.
---

# Write the report

Input: `artifacts/<store>/reason/*.json`. Output: `sample_output/<store>.md`. The structured data is already authored; your only original prose here is the executive summary.

## Step 1 — Validate (gate)

Run the shared validator before writing anything:

```
python harness/scripts/validate.py artifacts/<store>
```

It enforces the audit contract (exactly 10 experiments, all 5 pillars, every field present, every `evidence.screenshot` resolves, every `triggering_signal` resolves, competitor 3–4 rows, ~15 tech rows). **If it fails, do not render** — fix the specific object paths it reports by regenerating only the failed `reason/*.json` section, then re-validate. (Note: `validate.py` is owned by the eval module; if it is not yet present, do the structural checks by hand against `harness/schemas/`.)

## Step 2 — Compose the executive summary (prose)

From `synthesis.json` `themes` (and the experiments their `supporting_exp_ids` point to), write **2–3 flowing paragraphs**: the highest-level read on what is costing the store sales right now. Decisive, store-specific, grounded in the actual 10. This is the only free-prose section.

## Step 3 — Assemble `sample_output/<store>.md`

Render in this exact order, matching the calibration anchor's format:

1. **Title** — `synthesis.headline` as an H1.
2. **Executive summary** — the prose from Step 2.
3. **Proposed experiments** — loop `experiments.json`; each as a labeled-field block (H3 = `exp_id — title`), then:
   `**Pillar:** … / **Affected surface:** … / **URL:** … / **Evidence:** <screenshot path> / **Hypothesis:** … / **Primary change:** … / **Primary KPI:** … / **Decision rule:** … / **Expected lift:** +low–high% / **Confidence:** N%`
4. **Competitor analysis** — one intro sentence + a markdown table from `competitors.json` (Competitor | Domain | Positioning | What they make easier | Our edge | Pattern to adapt).
5. **Technical checks** — a markdown table from `tech_checks.json` (Check | Status | Detail).

Output format is `.md` (styling irrelevant; content and grounding are what is read).

## Quality bar
- Every experiment's `Evidence:` line is a real screenshot path under `artifacts/<store>/`.
- The 10 experiments span all 5 pillars.
- KPIs and language match the store's `commerce_model`.
- No claim without an artifact behind it.
