# Eval Summary - sample-ginger-co

Overall score: 15/100
Layer-1 validation: FAIL
Acceptance: FAIL

## Dimension Scores

| Dimension | Score | Weight | Failures |
|---|---:|---:|---:|
| structure_compliance | 0 | 15 | 2 |
| evidence_resolvability | 0 | 15 | 2 |
| evidence_claim_coherence | 5 | 20 | 1 |
| pillar_coverage | 0 | 10 | 1 |
| store_specificity | 0 | 15 | 1 |
| technical_truthfulness | 0 | 10 | 1 |
| competitor_grounding | 5 | 5 | 0 |
| report_quality | 5 | 10 | 0 |

## Layer-1 Failures

- `experiments`: 9 experiments found; expected exactly 10
- `experiments[*].pillar`: Missing pillars: Performance
- `experiments[0].evidence.screenshot`: Screenshot does not exist: pdp-gingins/screenshots/MISSING.png
- `experiments[1].confidence`: 95 outside 80-88 for direct structural absence
- `experiments[2].evidence.store_profile_ref`: No store_profile overlap for best-practice:urgency
- `experiments[3].evidence.triggering_signal`: Signal does not resolve: visual_findings.vf-does-not-exist
- `tech_checks[2].grounded_in`: Pass without resolvable grounded_in: not inspected

## Judge Tasks

10 judge tasks emitted.
