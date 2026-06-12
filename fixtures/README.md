# fixtures — Step-0 eval fixtures (Claude-seeded, Codex to review)

Two store artifact trees so Module 2 (eval) can be built and tested **without a real crawl**. Per WORK_SPLIT, Codex reviews/acks these before building eval, so the eval doesn't accidentally encode producer assumptions.

```
fixtures/
  sample_store/          PASS oracle — complete, schema-valid, internally consistent
  sample_store_broken/   FAIL oracle — same crawl artifacts, reason/ with injected faults
  _generate.py           deterministic generator (regenerates both trees + screenshots)
  _selfcheck.py          authoring oracle (NOT the eval) — prints expected pass/fail results
  README.md              this file
```

Regenerate / verify:
```
python fixtures/_generate.py     # rebuilds both trees (needs Pillow for screenshots)
python fixtures/_selfcheck.py    # sample_store -> CLEAN ; sample_store_broken -> 7 faults
```
Both trees validate against `harness/schemas/*.json` (Draft 2020-12). `_selfcheck.py` is a Module-1 aid and an expected-results reference — it is **not** `validate.py` (Codex owns that).

## Frozen conventions (the parts Codex's resolver must match)

**Paths are relative to the store root.** `validate.py` / `score_report.py` take the store root as base dir, so `fixtures/sample_store/` and a real `artifacts/<store>/` are structurally identical. (Note: `plan.md`'s inline example showed a repo-root path like `artifacts/gingerpeople/...`; we standardize on **store-root-relative** for fixture/real parity.)

**`triggering_signal` grammar:**
| signal_type | format | resolves against |
|---|---|---|
| `cro_signals` | `<surface_id>.cro_signals.<key>.present=<bool>` | `page.json.cro_signals[key].present` |
| `network` | `<surface_id>.network.responses[].status=<code>` | any `page.json.network.responses[].status` |
| `visual` | `visual_findings.<finding_id>` | `visual_findings.json findings[].id` |

**`store_profile_ref`** is `key:value` tokens joined by `;` or `,` (e.g. `family:GIN GINS; job:purchase-clarity`). Specificity passes if any value overlaps a `store_profile` token (family name, product, job, segment, proof point, content theme, or niche).

## `sample_store` (PASS oracle)

6 surfaces (`home`, `pdp-gingins`, `collection-candy`, `cart`(404), `where-to-buy`, `content-glp1`), full `reason/*.json`. Properties the eval should score as clean:
- exactly **10** experiments; all **5** pillars present (Conversion 3, AOV 2, Retention 2, Acquisition 2, Performance 1)
- every `evidence.screenshot` resolves; every `triggering_signal` resolves; every `store_profile_ref` overlaps the profile
- all 3 signal types exercised (`cro_signals`, `network`, `visual`)
- confidence within band for its `confidence_basis` (80–88 / 70–80 / 65–72)
- competitors = 4 rows w/ `source_url`; tech checks = 15 rows; every `Pass`/`Fail` has a resolvable `grounded_in`, rest are `Warn`

## `sample_store_broken` (FAIL oracle)

Same crawl artifacts; `reason/` carries 7 injected faults. Every key failure class is represented, including the hardest (schema-valid-but-generic specificity miss):

| # | Class | Object path | What's wrong |
|---|---|---|---|
| F1 | count | `experiments` | only 9 experiments (want 10) |
| F2 | pillar gap | `experiments[*].pillar` | Performance pillar absent |
| F3 | evidence resolvability | `experiments[0].evidence.screenshot` | points to `MISSING.png` |
| F4 | tech truthfulness | `tech_checks[2]` (Sitemap) | `Pass` with unresolvable `grounded_in` |
| F5 | **store specificity** | `experiments[2].evidence.store_profile_ref` | generic ("urgency banners"); `best-practice:urgency` overlaps nothing |
| F6 | confidence coherence | `experiments[1].confidence` | 95 with basis `direct structural absence` (band 80–88) |
| F7 | signal resolvability | `experiments[3].evidence.triggering_signal` | `visual_findings.vf-does-not-exist` |

`_selfcheck.py` prints exactly these 7. A correct `validate.py` + `score_report.py` should surface every one with its object path so they can drive targeted repair prompts.

## Screenshot policy

PNGs are simple **labeled** images (surface + filename drawn on them), not blank placeholders — usable for both mechanical path checks and non-blank LLM-judge tests. If `Pillow` is absent, `_generate.py` falls back to 1×1 valid PNGs (mechanical checks still pass; not suitable for judge tests).
