# WORK_SPLIT.md — Claude × Codex parallel build

Coordination contract for building the Qosmic audit harness. Both agents follow this.
Mapping: **Module 1 = Runtime Harness** (Part 1, Phases 1–3) · **Module 2 = Eval System** (Part 2, Phase 4).

## Producer / consumer boundary

- **Claude → Module 1 (producer).** Generates artifacts and the rendered report: `extract.py`, the crawl/reason/write skills, `AGENTS.md`/`CLAUDE.md`, `sample_output/`, `artifacts/<store>/`.
- **Codex → Module 2 (consumer).** Validates, scores, emits repair signals, owns the loop: `validate.py`, `score_report.py`, the `evaluate-audit` skill, `artifacts/<store>/eval/*`, `EVAL_LOOP.md`.

The fixed JSON schemas are the interface. Freeze them + seed shared fixtures → both tracks build in parallel, meet only at integration.

## Frozen contract (formal, not prose)

- **Schemas live as machine-readable files in `harness/schemas/*.json` (JSON Schema)** — `manifest.schema.json`, `page.schema.json`, `experiments.schema.json`, `store_profile.schema.json`, `visual_findings.schema.json`, `leaks.schema.json`, `competitors.schema.json`, `tech_checks.schema.json`, `synthesis.schema.json`. Eval derives required fields from these, **not** from the prose examples in `plan.md`. (Codex adjustment #4.)
- **Both the reason JSON and the crawl JSON (`page.json`/`manifest.json`) are part of the contract** — Codex's "signal path exists" check parses dotted paths into `page.json`, so the crawl schema is frozen too.
- **Change rule:** any schema change = a two-line note + the other side's ack before merge. No unilateral edits.

## Boundary decisions (encoded — agreed by both)

1. **`score_report.py` stays deterministic / API-key-free.** It runs all mechanical checks and emits mechanical scores **plus `judge_tasks[]`** (a.k.a. `judge_required` entries) marking what needs an LLM pass. The **`evaluate-audit` skill** orchestrates the LLM-judge passes and merges their results into the final `eval_report.json`. (Codex adjustment #1.)
2. **Judge granularity = per-experiment + one summary-level judge.** One judge task per experiment (evidence↔hypothesis support, store-specificity) for actionable repair paths, **plus** a single summary-level judge for executive-summary faithfulness to the top-ranked leaks. `eval_report.json` failure paths are per-object (`experiments[4].evidence...`, `executive_summary`). (Codex adjustment #2.)

## Step 0 — Claude owns, Codex reviews before building (the handshake)

Claude seeds, then **Codex sanity-checks fixtures before building eval** so the eval doesn't accidentally encode producer assumptions. (Codex adjustment #3.) Claude delivers:

1. `harness/schemas/*.json` — the formal JSON Schemas above.
2. `fixtures/sample_store/` — a complete, **schema-valid passing** mini-audit: `manifest.json`, `page.json`(s), screenshots, full `reason/*.json`, derived from `target_report.md` so it's realistic.
3. `fixtures/sample_store_broken/` — a twin that exercises **all key failure classes**, so the eval is proven to *catch*, not just pass:
   - only 9 experiments (count fail)
   - a missing pillar (coverage fail)
   - a dangling `evidence.screenshot` path (resolvability fail)
   - a `tech_checks` `Pass` with no resolvable `grounded_in` (truthfulness fail)
   - **a store-generic experiment that passes schema but fails specificity** — schema-valid, no `store_profile` overlap — the hardest quality failure to catch. (Codex adjustment #6.)
4. **Screenshot policy in fixtures** (Codex adjustment #7):
   - Placeholder PNGs are fine for **mechanical** tests (path resolves, file exists).
   - For **LLM-judge** quality tests, do **not** use blank placeholders — either omit screenshots from those judge cases or use clearly-labeled simple images so the judge has something non-blank to assess.

**Gate:** Codex reviews `harness/schemas/` + `fixtures/` and acks (or requests changes) before either track starts real implementation.

## File ownership (disjoint — clean merges)

| Claude — Module 1 | Codex — Module 2 |
|---|---|
| `harness/scripts/extract.py` | `harness/scripts/validate.py` |
| `harness/skills/crawl-storefront.md` | `harness/scripts/score_report.py` |
| `harness/skills/reason-audit.md` | `harness/skills/evaluate-audit.md` |
| `harness/skills/write-report.md` | `artifacts/<store>/eval/*` |
| `AGENTS.md` (initial), `CLAUDE.md` | `EVAL_LOOP.md` |
| `harness/schemas/*` (seed in Step 0) | `fixtures/` test harness (after seed) |
| `sample_output/*`, `artifacts/<store>/` (producer) | |

**AGENTS.md ownership (Codex adjustment #5):** Claude owns the initial `AGENTS.md`. Codex owns `evaluate-audit.md` and, **during integration only**, appends a small "eval commands" section to `AGENTS.md` — the two modules never edit the entrypoint at the same time.

## Coordination rules

1. Schemas frozen after Step 0 ack; changes need a note + ack (above).
2. **`validate.py` is Codex-owned but ships first.** Claude `import`s it read-only in the Write pre-render gate; never edits it. Until it lands, Claude gates against a thin local stub, then swaps.
3. **Separate branches/worktrees**, merge at integration. The ownership table is disjoint, so merges should be clean.

## Sequencing

```
Step 0 (Claude): harness/schemas/* + fixtures/ (passing + broken)  →  Codex review/ack
   ├── Track A (Claude): extract.py → crawl → reason → write → run gingerpeople + zenrojas
   └── Track B (Codex):  validate.py (ship early) → score_report.py mechanical + judge_tasks[]
                         → evaluate-audit skill (judge orchestration + merge) → EVAL_LOOP.md
Integration (both): point eval at Claude's real artifacts; reconcile; tune deferred rubric cutoffs;
                    Codex appends eval-commands section to AGENTS.md.
```

## Definition of done for parallelism

- **Codex track is independent when:** `validate.py fixtures/sample_store/reason` passes, `fixtures/sample_store_broken/` fails on every seeded class, and `score_report.py` emits an `eval_report.json` with mechanical scores + `judge_tasks[]` — all without any real harness run.
- **Claude track is independent when:** `extract.py` + skills produce `reason/*.json` that conforms to `harness/schemas/*` and renders to `sample_output/<store>.md` for both stores.
- **Integration done when:** Codex's eval scores Claude's real gingerpeople + zenrojas outputs with no Layer-1 failures and the agreed acceptance targets.
