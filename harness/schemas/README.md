# harness/schemas — the frozen contract

Machine-readable JSON Schemas (draft 2020-12) for every artifact crossing the Module 1 ↔ Module 2 boundary. Eval derives required fields from **these files**, not from the prose examples in `plan.md`.

| Schema | Producer (Module 1) | Consumers |
|---|---|---|
| `manifest.schema.json` | `extract.py` | Reason, Eval (surface-id + signal-path resolution) |
| `page.schema.json` | `extract.py` | Reason, Eval (dotted-path resolution) |
| `store_profile.schema.json` | reason skill | Write, Eval (specificity overlap) |
| `visual_findings.schema.json` | reason skill | Eval (signal_type=visual resolution) |
| `leaks.schema.json` | reason skill | Eval (traceability) |
| `experiments.schema.json` | reason skill | Write, Eval (core) |
| `competitors.schema.json` | reason skill | Write, Eval |
| `tech_checks.schema.json` | reason skill | Write, Eval (truthfulness) |
| `synthesis.schema.json` | reason skill | Write (exec summary), Eval (faithfulness judge) |

## Division of responsibility: schema vs `validate.py`

**Schemas validate SHAPE** — field presence, types, enums, patterns, value ranges within a single object.

**`validate.py` validates AUDIT-CONTRACT RULES** — things a single-object schema cannot express, especially counts and cross-file references:

- exactly **10** experiments
- all **5** pillars present across experiments
- competitor table has **3–4** rows
- technical checks table has **~15** rows
- every `evidence.screenshot` path resolves to a real file on disk
- every `evidence.triggering_signal` dotted path resolves into the right `page.json` / `visual_findings.json` / `network` field
- every `evidence.store_profile_ref` overlaps a real `store_profile` entry (specificity)
- `tech_checks` `Pass`/`Fail` have a resolvable `grounded_in`; otherwise must be `Warn`
- `confidence` is coherent with `confidence_basis` band (80–88 / 70–80 / 65–72)

This split is deliberate: the broken fixture's "9 experiments" case stays schema-valid so it fails at the **Layer-1 gate with a clean object-path message**, not at schema load.

## Dependency note (Module 2)

`jsonschema` is not currently installed in this environment. Codex's `validate.py` should declare it (e.g. `pip install jsonschema`) or implement equivalent shape checks. Everything else (path/signal resolution, counts, coherence) is stdlib.

## Change rule

Frozen after the Step-0 review/ack. Any change = a two-line note + the other module's ack before merge. No unilateral edits.
