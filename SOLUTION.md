# Qosmic take-home — solution overview

A runtime harness that turns any coding agent into a Qosmic CRO audit agent, plus a two-layer eval system with a self-improving loop. Start here; `plan.md` has the full design rationale and `WORK_SPLIT.md` the build split.

## What it does

Point it at a Shopify URL → a structured CRO audit (`sample_output/<store>.md`): executive summary, 10 evidence-bound experiments spanning all 5 pillars, a competitor table, and ~15 technical checks. Then the eval system scores that audit and can repair it.

## Architecture

**Runtime harness — three phases (`harness/skills/`):**
1. **Crawl** (`crawl-storefront` + `harness/scripts/extract.py`) — agent discovers surfaces in the browser; a deterministic Playwright script captures screenshots, role-based DOM, present/absent CRO signals, and network facts to `artifacts/<store>/`.
2. **Reason** (`reason-audit`) — the agent turns artifacts into structured JSON (`artifacts/<store>/reason/*.json`): a store profile, a visual-critique pass over the screenshots, leak detection, and 10 experiments that each bind to **evidence + a resolvable signal + a store-specific reference**.
3. **Write** (`write-report` + `render_report.py`) — the agent authors the executive summary; the rest templates 1:1 with the calibration anchor.

**Eval system (two layers + loop):**
- **Layer 1 — `validate.py`** (deterministic gate): exactly 10 experiments, all 5 pillars, every screenshot/signal resolves, specificity overlap, confidence↔basis coherence, tech-check truthfulness.
- **Layer 2 — `score_report.py` + the judge**: deterministic dimension scores + emitted `judge_tasks[]`; the `evaluate-audit` skill runs the LLM judge (per-experiment + a summary judge) and merges results.
- **Loop:** failures (with object paths) → targeted repair prompts → regenerate only the failed sections → re-score. See `EVAL_LOOP.md` for the autonomy story and `artifacts/gingerpeople_degraded/eval/loop_demo.md` for a worked before→after.

**The contract:** every cross-component artifact has a JSON Schema in `harness/schemas/`. Markdown is presentation; the JSON is authoritative — evals grade the structured intermediates, not prose.

## Run it

```bash
pip install -r requirements.txt
python -m playwright install chromium

# Phase 1 — crawl (agent picks the URLs; here a few are passed directly)
python run_audit.py --store acme \
  --url https://acme.com/ --url https://acme.com/products/x --url https://acme.com/cart
# -> stops at the REASON step (an LLM/agent phase)

# Phase 2 — run the `reason-audit` skill on artifacts/acme/ (writes reason/*.json)

# Phase 3 — write + validate + score in one command
python run_audit.py --store acme --skip-crawl
```

The orchestrator does the deterministic bookends and hands off to the agent for the reasoning phase.

## What's in the repo

```
AGENTS.md / CLAUDE.md      harness entry points (agent-neutral + Claude adapter)
harness/skills/            crawl-storefront, reason-audit, write-report, evaluate-audit
harness/scripts/           extract.py, render_report.py | validate.py, score_report.py (eval)
harness/schemas/           the frozen JSON-Schema contract
run_audit.py               end-to-end orchestrator
sample_output/             gingerpeople.md, zenrojas.md (the two deliverable audits)
artifacts/<store>/         crawl + reason + eval artifacts per store
fixtures/                  pass + broken eval fixtures (oracle for the eval system)
EVAL_LOOP.md               how the eval becomes autonomous + self-learning
plan.md / WORK_SPLIT.md    design rationale + build split
```

## Generalization (the key test)

The same harness produced two genuinely different audits from evidence alone:
- **gingerpeople** — inferred **retailer-routed** (every CTA is "Where to buy", no price/add-to-cart, `/cart` 404) → buying-box, where-to-buy rebuild, cart-recovery experiments.
- **zenrojas** (unseen) — inferred **direct-sell** (prices, add-to-cart, working cart) → intrusive-popup, PDP social-proof, subscribe-and-save, bundle, and a network-grounded performance experiment.

No store-specific shortcuts; surface discovery is nav-driven, and `extract.py` defeats Cloudflare-style rate limiting with a fresh context per URL.

## Known limits (honest)
- `triggering_signal` is gaining `network` metric predicates (nav-timing / requests / console-error count) so Performance can cite measured evidence directly instead of via a visual finding.
- `extract.py` popup dismissal misses some delayed popups (captured as evidence regardless); non-standard URLs are typed `other` (content is still captured and reasoned over).
- Confidence is scored for *coherence with evidence strength*, not realized lift — true calibration needs live A/B outcomes (the dimension we don't yet measure).
