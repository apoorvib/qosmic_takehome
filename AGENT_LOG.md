# AGENT_LOG.md

How this take-home was built, who drove, and the prompts that steered it.

> Times are self-reported estimates — adjust to your actuals before submitting.

## Approach in one line

Two coding agents in parallel against a frozen contract: **Claude Code** built the runtime harness (Module 1), **Codex** built the eval system (Module 2). I orchestrated — making the architecture calls, then letting each agent drive implementation against shared JSON Schemas + fixtures so the two halves never blocked each other.

## Time per part

| Part | What | ~Time |
|---|---|---:|
| 0 | Design — read README + `target_report.md`, build `plan.md` phase by phase (Crawl / Reason / Write / Eval), settle architecture | ~60 min |
| 0.5 | Contract + Step 0 — `WORK_SPLIT.md`, `harness/schemas/*.json`, pass + broken fixtures, self-check oracle | ~35 min |
| 1 | Runtime harness (Claude) — `extract.py` (incl. Cloudflare debugging), 3 skills, `AGENTS.md`/`CLAUDE.md`, run both stores, render + validate | ~110 min |
| 2 | Eval system (Codex, in parallel) — `validate.py`, `score_report.py`, judge orchestration, `EVAL_LOOP.md` | ~100 min |
| 3 | Docs (AGENT_LOG, WORKFLOWS, Loom prep) | ~30 min |

Because Parts 1 and 2 ran in parallel, **wall-clock (~4–4.5h) is less than the column sum.** Scope deliberately exceeded the 4h target (per the brief), so I prioritized the eval loop and generalization over harness polish.

## Prompts I fed the agents (the steering ones)

Design phase (Claude):
- "Go through README.md thoroughly and `target_report.md`, then let's discuss."
- "Let's plan stuff out one by one and as we finalize, add to `plan.md`. First the Playwright part — simple screenshots aren't the way; we need DOM extraction… think of complications."
- "When the agent interacts via Playwright MCP, does `extract.py` run in the background, or…? Explain."
- "How would the agent provide *design* recommendations? We need advice specific to the product, not generic."
- "Fix the Phase 2 outputs, then decide exactly what Phase 3 does."

Coordination:
- "Give me a strategy for how you and Codex divide Module 1 and Module 2. Once Codex agrees I'll let you begin."
- (Pasted Codex's 7 adjustments back to Claude to fold into `WORK_SPLIT.md`.)
- "Land Step 0." → "Codex agreed; begin your work."

Most decisions were made by **answering structured option-forks** the agent surfaced (substrate, crawl method, execution model, reasoning structure, tech-check source) rather than free-text — fast, and it kept the design auditable in `plan.md`.

## Where the agent drove vs. where I took the wheel

**Agent drove (implementation + verification):**
- All code: `extract.py`, the JSON Schemas, fixtures + generator + self-check oracle, the three skills, the two entry-point files.
- Debugging — diagnosing the Cloudflare block as session rate-limiting and solving it (fresh-context-per-URL + delay + Chrome channel + stealth + retry).
- The reasoning content for both audits, grounded in live artifacts (cro_signals, network, screenshots it Read).
- Verification — schema validation, the self-check oracle, and running Codex's `validate.py`/`score_report.py` to confirm 100/100.

**I took the wheel (judgment + direction):**
- Every architecture fork: harness substrate, live-browser vs HTML, the Model-2 execution model, structured vs single-pass reasoning, decoupling Reason (JSON) from Write (prose), and the eval's two-layer shape.
- Overrode the agent's recommendation on **tech-checks** (chose LLM-written + grounding guardrail over its deterministic-rollup rec) and on the **entry point** (made `AGENTS.md` primary with `CLAUDE.md` as an adapter).
- Standardized the **path convention** (store-root-relative) and the **parallel-agent division** itself.
- Ran Codex as a separate agent and relayed its review of the contract before either side built.

## Decisions reversed / corrected mid-build
- Tech-checks moved from deterministic script → LLM-written with an artifact-grounding guardrail (my call, against the agent's rec).
- Entry point reframed to agent-neutral `AGENTS.md` + `CLAUDE.md` adapter (edited directly in `plan.md`).
- Crawl execution model resolved away from "navigate-in-MCP-then-extract" (separate browser processes don't share state) to a self-contained `extract.py`.

## Known gaps surfaced honestly (not hidden)
- `triggering_signal` grammar can't yet cite nav-timing/console errors → Performance findings are grounded via a visual finding for now (proposed contract extension to Codex).
- `extract.py` popup dismissal misses some delayed popups (captured as evidence regardless); non-standard URLs are typed `other`.
