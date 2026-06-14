# gingerpeople_degraded — injected flaws (eval-loop demo input)

Schema-valid copy of artifacts/gingerpeople/ with three injected quality flaws.

| # | Class | Object path | Caught by | What's wrong |
|---|---|---|---|---|
| A | confidence coherence | `experiments[3].confidence` | validate.py | 92 with basis 'pattern / best-practice' (band 65-72) |
| B | tech truthfulness | `tech_checks[2]` (Sitemap) | validate.py | Pass with unresolvable grounded_in |
| C | store specificity / generic advice | `experiments[2]` | LLM judge | mechanically valid but generic CRO boilerplate (urgency timers/popups) |

Expected loop: validate.py -> INVALID on A+B with object paths; judge -> flags C (low specificity / weak evidence-claim coherence) despite passing mechanical checks. Repair the three sections, re-validate + re-score, and record the before->after delta.
