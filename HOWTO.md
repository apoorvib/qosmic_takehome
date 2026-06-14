# HOW TO USE

A step-by-step guide to installing and running the Qosmic audit harness + eval system. For the design rationale see `SOLUTION.md` and `plan.md`.

> **What this does:** point it at a Shopify storefront URL → it produces a CRO audit report (`sample_output/<store>.md`) and an eval score for that report.

---

## 1. Prerequisites

- **Python 3.11+** (developed on 3.13)
- **Google Chrome** installed (the crawler prefers the real Chrome channel; it falls back to bundled Chromium)
- Internet access (the crawler visits live storefronts)

Check:
```bash
python --version
```

## 2. Install dependencies

From the repo root:
```bash
pip install -r requirements.txt
python -m playwright install chromium
```
This installs `playwright`, `jsonschema`, and `Pillow`, then downloads the Chromium browser Playwright drives.

> Windows note: all commands below work in PowerShell or Git Bash. Use `python` (not `python3`).

---

## 3. Quickstart — run the two included sample audits

Two stores are already crawled and reasoned (`artifacts/gingerpeople/`, `artifacts/zenrojas/`). To (re)write their reports and score them:

```bash
python run_audit.py --store gingerpeople --skip-crawl
python run_audit.py --store zenrojas --skip-crawl
```

Each prints `VALID` and `Overall score: 100/100`. **Now read the outputs (they are files, not just terminal text):**

| What | Where |
|---|---|
| **The audit report** (main deliverable) | `sample_output/gingerpeople.md`, `sample_output/zenrojas.md` |
| **Eval score breakdown** (human-readable) | `artifacts/<store>/eval/eval_summary.md` |
| **Eval report** (machine-readable + judge tasks) | `artifacts/<store>/eval/eval_report.json` |
| **Structured reasoning** | `artifacts/<store>/reason/*.json` |
| **Evidence screenshots** (cited in the report) | `artifacts/<store>/<surface>/screenshots/*.png` |

Open the two reports side by side — they are deliberately different (gingerpeople is *retailer-routed*, zenrojas is *direct-sell*), which demonstrates that the harness generalizes.

---

## 4. Run a fresh audit on a new store

An audit has three phases: **Crawl → Reason → Write**. Crawl and Write are scripts; **Reason is an LLM step** (a coding agent acts as the audit agent), so the run pauses for it.

**Phase 1 — Crawl.** Give the runner the store and a representative set of URLs (homepage first, then a couple of products, a collection, `/cart`, and a content page):
```bash
python run_audit.py --store mystore \
  --url https://mystore.com/ \
  --url https://mystore.com/products/some-product \
  --url https://mystore.com/collections/all \
  --url https://mystore.com/cart \
  --url https://mystore.com/pages/faq
```
This writes `artifacts/mystore/` (manifest, page.json per surface, screenshots) and then **stops at the REASON step**.

**Phase 2 — Reason (agent step).** Open this repo in **Claude Code** (or Codex) and ask it to:
> "Run the `reason-audit` skill on `artifacts/mystore`."

The agent reads the artifacts + screenshots and writes `artifacts/mystore/reason/*.json` (store profile, visual findings, leaks, 10 experiments, competitors, tech checks, synthesis). It also authors `artifacts/mystore/reason/exec_summary.md`.

**Phase 3 — Write + evaluate.** Re-run the orchestrator to render, validate, and score:
```bash
python run_audit.py --store mystore --skip-crawl
```
Result: `sample_output/mystore.md` + `artifacts/mystore/eval/`.

> Tip: not sure which URLs to use? Crawl just the homepage first (`--url https://mystore.com/`), open `artifacts/mystore/home/page.json`, and read the `elements[]` hrefs to pick real nav links.

---

## 5. The eval system (run it directly)

The runner calls these for you, but you can run them standalone from the repo root:

```bash
# Layer 1 — structural gate (exits non-zero + lists object-path failures if invalid)
python -m harness.scripts.validate artifacts/<store>

# Layer 2 — deterministic dimension scores + emitted LLM judge_tasks
python -m harness.scripts.score_report artifacts/<store>
#   -> writes artifacts/<store>/eval/eval_report.json + eval_summary.md
```

To run the **LLM judge** (Layer 2's qualitative half): have a coding agent execute the `evaluate-audit` skill, which consumes the `judge_tasks` in `eval_report.json`, writes `artifacts/<store>/eval/judge_results.json`, then merge:
```bash
python -m harness.scripts.merge_judge_results artifacts/<store>/eval artifacts/<store>/eval/judge_results.json
```

---

## 6. Verify the eval actually catches problems

The eval ships with a passing fixture and a deliberately-broken one:
```bash
python -m harness.scripts.validate fixtures/sample_store          # -> VALID
python -m harness.scripts.validate fixtures/sample_store_broken   # -> INVALID + 7 faults (each with an object path)
python fixtures/_selfcheck.py                                     # oracle: clean vs 7 faults
```

See the self-improving **repair loop** in action (degraded audit → eval catches flaws → repair → re-score):
```bash
python scratch/build_gingerpeople_degraded.py                      # regenerate the flawed input
python -m harness.scripts.validate artifacts/gingerpeople_degraded # -> INVALID
cat artifacts/gingerpeople_degraded/eval/loop_demo.md              # a worked before->after (85/FAIL -> 100/PASS)
```

---

## 7. Troubleshooting

- **A page returns 403 / "Attention Required":** some stores (e.g. Cloudflare) rate-limit rapid requests. `extract.py` already uses a fresh browser context per URL + a polite delay + retry; a surface still blocked after retry is recorded as blocked and treated as `Warn` (never fabricated).
- **`ModuleNotFoundError: harness`** when running a script directly: use the module form (`python -m harness.scripts.score_report ...`) from the repo root, or `run_audit.py`, which sets the path for you.
- **`playwright` not found / browser missing:** re-run `python -m playwright install chromium`.
- **Crawl picks the wrong surface type:** non-standard URLs may be typed `other`; the content is still captured and reasoned over, so the audit is unaffected.

---

## 8. File map (where everything lives)

```
run_audit.py               end-to-end orchestrator
requirements.txt           dependencies
AGENTS.md / CLAUDE.md      harness entry points (read by the coding agent)
harness/skills/            crawl-storefront, reason-audit, write-report, evaluate-audit
harness/scripts/           extract.py, render_report.py | validate.py, score_report.py, merge_judge_results.py
harness/schemas/           the JSON-Schema contract
sample_output/             the audit reports (the deliverable)
artifacts/<store>/         per-store crawl + reason + eval artifacts
fixtures/                  pass + broken eval fixtures
SOLUTION.md / plan.md      architecture + design rationale
```
