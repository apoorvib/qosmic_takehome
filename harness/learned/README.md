# harness/learned — promoted deterministic checks (the self-learning lane)

This directory holds checks the eval system **learned** from recurring failures. It is the running-code slice of `EVAL_LOOP.md`'s lane *"deterministic checks absorb recurring mechanical failures."*

## How it works

1. `harness/scripts/self_learn.py` aggregates failures across a committed corpus (`fixtures/learning/failure_corpus.jsonl`) plus any live eval reports, and clusters them by category.
2. For the top **mechanizable, not-yet-covered** cluster it proposes one additive rule — appended to `registry.json` as **DATA** (patterns + parameters), interpreted by a vetted function in `harness/scripts/learned_checks.py`. No code is generated or executed.
3. The proposal is **gated** before anything is kept:
   - **no false positives** on known-good audits (regression guard),
   - a **true positive** on a committed known-bad example (`fixtures/learning/known_bad_generic.json`) — it must actually help,
   - the **existing test suite still passes** (don't break existing code),
   - the eval contract still **validates the passing fixture**.
4. Only if the gate passes is the change **committed** — a scoped, revertible git commit touching **only** this directory. If the gate fails, the working tree is restored and nothing is kept.

## Safety model (why an autonomous run can't break the repo)

- **Data, not code.** Learned rules are JSON parameters for vetted rule types. The loop never writes or executes generated Python.
- **Gate before commit.** Every check above must pass first; any failure → full restore, no commit.
- **Scoped commits.** The loop uses `git commit -- <paths>` (pathspec) — it never runs `git add -A` and never touches your other staged/untracked files.
- **One commit per change.** Each accepted rule is its own commit, so `git revert <hash>` undoes exactly that rule and nothing else.

## Using / reverting

```bash
# propose + gate + commit (on pass)
python -m harness.scripts.self_learn

# analyze + gate only, change nothing
python -m harness.scripts.self_learn --dry-run

# run the learned checks against an audit (advisory)
python -m harness.scripts.learned_checks artifacts/<store>

# undo a specific learned rule
git revert <commit-hash>
```

Learned checks are also run as an **advisory** pass inside `run_audit.py` after validation, so promoted rules immediately affect future audits.

## Files
- `registry.json` — active learned rules (data). Edited only by gated, committed `self_learn.py` runs.
- `learning_log.jsonl` — append-only record of accepted promotions.
