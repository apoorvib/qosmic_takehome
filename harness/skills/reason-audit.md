---
name: reason-audit
description: Phase 2 of a Qosmic audit. Use after crawl-storefront has produced artifacts/<store>/. Reasons over the frozen artifacts (page.json + screenshots) to emit the structured JSON intermediates the report is built from — evidence-bound, store-specific, spanning all 5 pillars.
---

# Reason over the artifacts

Input: `artifacts/<store>/manifest.json` + each `page.json` + the saved screenshots. Output: seven JSON files under `artifacts/<store>/reason/`, each conforming to its schema in `harness/schemas/`. **Read the schemas — they are the contract.** Do not re-crawl.

## Three grounding forces

Every recommendation must be grounded. Compose three forces:

1. **Factual** — `cro_signals` (esp. `present:false`) and `network` in each `page.json`. What exists / is broken.
2. **Perceptual** — `Read` the saved screenshots and judge what *looks* unclear, cluttered, low-contrast, or buried. The script cannot see; you can.
3. **Specificity** — `store_profile.json`, built first. What this store actually sells, to whom.

## Step 0 — Build `store_profile.json`

Read every `page.json` `content`, `title`, `text_blocks`, and product links. Emit `store_profile.json` (schema: `store_profile.schema.json`): `families`, `jobs_to_be_done`, `segments`, `proof_points`, `content_themes`, `brand_voice`, `niche`, and **`commerce_model`** (`retailer-routed` | `direct` | `hybrid`). 

`commerce_model` is load-bearing: if the buying CTA routes to retailers (e.g. primary CTA "Where to buy", no add-to-cart), it is **retailer-routed** → KPIs are *outbound retailer click rate*, not add-to-cart/checkout.

## Step 1 — Visual-critique pass → `visual_findings.json`

`Read` the screenshots. Emit located, evidence-bound findings (schema: `visual_findings.schema.json`): `{id, observation, screenshot_ref, region, severity, pillar}`. Findings must be specific and tied to a screenshot — not vibes. Rubric: above-fold clarity, visual hierarchy / primary-action prominence, CTA contrast & legibility, clutter / cognitive load, imagery quality & brand consistency, visual prominence of proof.

## Step 2 — Leak detection → `leaks.json`

Walk each `page.json` through the **pillar → leak-pattern playbook** as a coverage lens. Each leak names a **triggering signal** (schema: `leaks.schema.json`).

- **Conversion** — missing/ambiguous CTA, no price, no add-to-cart, broken purchase path, no above-fold proof.
- **AOV** — no bundles/kits, no cross-sell/upsell, no sampler, no volume/subscription tiers.
- **Retention** — no subscribe-and-save/reorder, no account/loyalty, no post-purchase routine, weak email-capture value.
- **Acquisition** — thin/missing high-intent landing pages, SEO meta gaps, missing structured data, un-commercialized content.
- **Performance** — slow `nav_timing_ms`, heavy transfer, 404s/broken links, console errors, unreachable cart/checkout.

## Step 3 — Candidate experiments → score → `experiments.json`

Build candidates (schema: `experiments.schema.json`). Each must pass **two mechanical gates** (the eval checks both):

1. **Evidence binding** — `evidence = {screenshot, triggering_signal, signal_type, store_profile_ref}`. The screenshot path must exist; the signal must resolve. **No binding → drop the candidate.**
2. **Specificity** — `store_profile_ref` must name a concrete family / product / job / segment / proof / content-theme from `store_profile.json`. Generic ("add a bundle") is **rejected**; "Travel kit from the 3 Ginger Rescue formats" passes.

`triggering_signal` grammar (must resolve):
| signal_type | format |
|---|---|
| `cro_signals` | `<surface_id>.cro_signals.<key>.present=<bool>` |
| `network` | `<surface_id>.network.responses[].status=<code>` |
| `network` | `<surface_id>.network.nav_timing_ms>=<ms>` (Performance) |
| `network` | `<surface_id>.network.requests>=<n>` (Performance) |
| `network` | `<surface_id>.console_errors.count>=<n>` (Performance) |
| `visual` | `visual_findings.<finding_id>` |

For **Performance** experiments, prefer a direct `network` metric predicate (slow `nav_timing_ms`, heavy `requests`, or `console_errors.count`) over routing through a visual finding — it cites the measured evidence directly.

Generate >10 candidates, score by `impact × evidence_strength × confidence`, then **select exactly 10 subject to a pillar-coverage guard: all 5 pillars must appear.** Skew is allowed; gaps are not. Set `exp_id` = `"exp-" + first 12 hex of a hash(store + title + surface)`. Paths are **relative to the store root** (e.g. `pdp-x/screenshots/pdp-x-fullpage.png`).

### Confidence + expected-lift rubric (numbers must be defensible)
- Direct structural absence in an artifact (e.g. no add-to-cart) → confidence **80–88**, `confidence_basis:"direct structural absence"`, larger lift band.
- Strong inference from present signals (proof exists but path ambiguous) → **70–80**, `"strong inference"`.
- Pattern / best-practice with partial evidence, or a net-new page → **65–72**, `"pattern / best-practice"`.

KPIs must match `commerce_model` (retailer-routed → outbound retailer click rate, etc.).

## Step 4 — Competitor analysis → `competitors.json`

Infer the niche from `store_profile`, then **WebSearch** for 3–4 real competitors. Emit `competitors.json` (schema: `competitors.schema.json`) with `source_url` per row — web-grounded, not recalled.

## Step 5 — Technical checks → `tech_checks.json`

~15 rows (schema: `tech_checks.schema.json`). **Status truthfulness is mandatory:**
- `Pass` requires a concrete artifact field proving the positive claim; put it in `grounded_in`.
- `Fail` requires a concrete artifact field proving the failure (e.g. `cart.network.responses[].status=404`).
- Anything missing, partial, or out-of-scope (mobile, Lighthouse, sitemap not inspected) is **`Warn`** with `grounded_in:"not inspected"`.

## Step 6 — Synthesis → `synthesis.json`

Emit `headline` + 2–3 `themes`, each with `supporting_exp_ids` referencing real `exp_id`s (schema: `synthesis.schema.json`). **No prose** — the executive summary is authored in the write-report phase.

When all seven files exist, proceed to **write-report**.
