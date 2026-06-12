# WORKFLOWS.md

How I work with coding agents day-to-day. (Not about this take-home — though it's a representative sample.)

> Personalize the **Tool stack** line and any specifics below to your actual setup before submitting.

## Tool stack

- **Primary drivers:** Claude Code and Codex, often **run in parallel** on the same repo against a shared contract.
- **Browser/automation:** Playwright (MCP for interactive discovery; a deterministic script for capture).
- **Verification:** schema validators + small self-check oracles I write alongside the artifacts, plus the test runner the project already uses.
- *(Add your editor, model defaults, and any MCP servers you run: e.g. filesystem, web search, a DB/API MCP, etc.)*

## Delegation patterns — what I let agents drive vs. always take the wheel on

**Agents drive:**
- Implementation once the interface is pinned — scripts, schemas, fixtures, glue, and the mechanical reasoning that follows from a spec.
- Debugging loops where the agent can observe and iterate (it found and fixed the Cloudflare block here without me touching code).
- Verification and grunt work — running validators, diffing outputs, reconciling artifacts.

**I keep the wheel:**
- **Architecture and interface design** — the data contracts between components are mine; I make agents propose options and I pick. Cheap to decide, expensive to get wrong.
- **Anything irreversible or outward-facing** — schema freezes, what gets committed/pushed, deletions.
- **Taste calls** — when the agent's recommendation is reasonable but I disagree (here: I overrode a "deterministic tech-checks" rec in favor of LLM-written-with-a-guardrail).

## How I actually run a build

1. **Design in a living doc first.** I make the agent build a `plan.md` phase by phase and answer **structured option-forks** rather than free-text — it's faster and leaves an auditable decision trail.
2. **Contract before code.** I freeze the interfaces as machine-readable schemas + seed **fixtures (a passing one and a deliberately-broken one)** so parallel work can't drift, and so every consumer has something to build against on day one.
3. **Parallelize across a clean producer/consumer seam.** Two agents, disjoint file ownership, one shared validator, a review/ack gate before either starts. The schemas are the only coupling.
4. **Determinism where it pays.** Capture/validation/scoring are scripts (reproducible, gradeable); judgment (reasoning, prose, aesthetics) stays with the LLM. The same artifact a model reasons over is the one the evals check — no second source of truth.
5. **Verify before claiming done.** Self-check oracles and validators run before I believe an output; I'd rather the tool catch my fixture bug than the reviewer (it did).

## Custom skills / commands / MCP I lean on

- **Skills as the harness:** I encode procedures as agent-readable skills (YAML frontmatter + progressive-disclosure body) with an agent-neutral `AGENTS.md` entry point and a thin `CLAUDE.md` adapter — so the same harness runs on Claude Code or Codex.
- **MCP for live/interactive steps** (browser discovery, search), **scripts for deterministic steps** — I don't make the model hand-do what a script should do reproducibly.
- *(List your own reusable skills/slash-commands/MCP servers here.)*

## The one rule

Agents are fastest when the **interface is unambiguous and the feedback loop is mechanical**. Most of my effort goes into making those two things true; the implementation then mostly writes itself.
