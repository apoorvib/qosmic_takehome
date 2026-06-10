# Qosmic take-home — build plan

Living plan. We finalize one part at a time and append it here.

## Locked top-level decisions

- **Runtime substrate:** Claude Code skills (YAML frontmatter + progressive-disclosure bodies) + a `CLAUDE.md` entry point. The agent *is* the audit agent; skills are the harness.
- **Crawl:** live browser via Playwright. MCP drives navigation/discovery/popup-dismissal; a deterministic `extract.py` does the structured DOM + screenshot + network capture.
- **Time weighting:** thin runtime harness, deep eval loop. Part 2 (eval system + autonomy) is the headline and gets the marginal hour.
- **Output contract (per README):** one report file with exactly — (1) executive summary prose, (2) 10 experiments spanning all 5 pillars, (3) competitor table (3–4), (4) ~15-row technical-checks table (Pass/Warn/Fail + one-line detail).
- **Generalization is a hard requirement:** runs on `gingerpeople.com` (calibration) and `zenrojas.com` (unseen). No store-specific shortcuts.

---

## Phase 1 — Crawl (FINALIZED)

Goal: turn a single Shopify URL into a set of durable, re-referenceable artifacts that the Reason phase consumes without ever re-crawling, and that the eval system can use to verify evidence grounding.

### Locked decisions
- **Execution model = Model 2 (self-contained script).** The agent uses Playwright **MCP only for discovery + judgment** (read homepage nav, decide which surfaces matter, handle weird interactive cases). It then hands a URL list to **`extract.py`**, which does the *entire* deterministic capture per URL and saves all artifacts. The agent reasons over the saved artifacts — including `Read`-ing the saved PNGs — not over a live browser.
  - **Why not "navigate in MCP then extract the live page":** Playwright MCP and a Python script are *separate browser processes* and don't share state (cookies, session, dismissed-popup state). So a script can't read the page the agent set up in MCP without a shared-CDP attach. Model 2 sidesteps this: the script re-navigates each URL itself, so popup-dismiss logic lives in **one** place and runs are reproducible.
  - **`extract.py` is a synchronous subprocess**, invoked via the Bash tool, run once per URL (or batched over the list). It captures, writes artifacts, and exits — not a background daemon. The agent waits, then reads the files.
- **`extract.py` owns screenshots.** It saves full-page stitch **+** key viewport shots (hero / above-fold CTA region) per surface to `screenshots/<slug>-<state>.png`. Those exact paths become the report's `Evidence:` lines. One artifact, three consumers: the writer cites it, the agent reasons over it, the eval verifies against it.
- **Mobile:** desktop-only crawl. Mobile-friendly / mobile-speed tech checks are honestly marked **Warn** (matches the anchor), not fabricated.

### Flow (per audit)
1. **Discover surfaces (MCP, nav-driven — NOT hardcoded paths).** Load homepage, read header nav + footer links, classify by Shopify conventions (`/products/`, `/collections/`, `/cart`, `/pages/`, `/blogs/`). Pick a representative set, capped at ~8–10 surfaces:
   - homepage
   - 1–2 PDPs (sampled from a collection)
   - 1 collection / catalog page
   - `/cart`
   - 2–3 intent/content pages (Where-to-buy / FAQ / blog / about)
2. **Capture (`extract.py`, per surface, deterministic):** for each URL the agent selected, the script does the whole pipeline itself — navigate → wait → dismiss popups → scroll/lazy-load → screenshots (full-page + viewport) → role-based DOM extraction → CRO-signal presence/absence → network capture → write artifacts → exit.
3. **Reason (agent):** read `manifest.json` + each `page.json` + the saved screenshots → identify leaks → build experiments. Never re-crawls.

### Wait strategy (avoid `networkidle`)
`networkidle` is unreliable on Shopify (analytics pixels, chat widgets, A/B tools, review apps keep the network alive). Use: `load` → short settle (~1.5–2s) → optional wait for a known selector (`h1`/`main`) → hard timeout cap. Then scroll to trigger lazy-load before capture.

### Popup / modal handling
Shopify stores spawn cookie banners and email-capture modals on load.
- Capture the **first** screenshot *with* the popup present — it is itself CRO evidence ("intrusive interstitial on load").
- Then dismiss: close button → `Escape` → click-outside fallback.
- Continue so downstream screenshots aren't poisoned by the overlay.

### `extract.py` responsibilities
- **Role-based DOM extraction (not a tag dump).** Flat list of interactive + proof elements, each with: role/tag, text/label/aria-label, `href`/`type`/`name`/`placeholder`, `isVisible`, bounding box, `aboveFold`. No raw divs (avoids crowding).
- **Bounded main-content text (`content`).** Readability-style extraction of the *readable body* — product descriptions, use-case/category copy, meaningful paragraphs — cleaned and capped. NOT raw divs; the article/main text. This feeds the Phase-2 `store_profile` and is what makes recommendations product-specific instead of generic.
- **Expected-CRO-element presence/absence check** (general across stores). For each surface type, explicitly mark present/absent: price, add-to-cart / buy button, reviews/ratings, trust badges, search, promo/announcement bar, primary CTA. **Recording absence is high-signal** — "no add-to-cart, no price, no next step" is exactly the leak the anchor's #1 experiment is built on.
- **Screenshots:** full-page stitch + key viewport shots (hero / CTA region), named `<slug>-<state>.png`.
- **Network capture (free wins):** every response status + headers + redirect chain + nav timing + request count / transfer size. Hands us, for free: 404 / broken-link detection, SSL + security-header checks, redirect checks, rough perf signals — turning the technical-checks table into real Pass/Fail instead of all-Warn.
- **Console errors** per page.
- **Token-budget caps:** top-N elements per page, prioritize visible + above-fold + CTA/proof, truncate long text, per-page JSON size budget.

### Safety
Visit `/cart`; **never proceed through checkout**. Hard boundary.

### Artifact layout (the Crawl→Reason contract; also what eval reads)
```
artifacts/<store>/
  manifest.json              # index of surfaces crawled + classification
  <surface>/
    page.json                # url, status, title, meta tags, elements[], cro_signals{}, timing, console_errors[]
    screenshots/
      <slug>-fullpage.png
      <slug>-hero.png
      <slug>-<state>.png
```
Reason reads `manifest.json` + each `page.json` — never re-crawls. Report evidence paths point straight at these files.

### Reproducibility note
Live sites change run-to-run (and popups randomize). For eval reproducibility we **freeze the artifact set** and score evals against the frozen artifacts rather than re-crawling each time. (Carried into Phase 2 design.)

### Open / deferred
- Bot/Cloudflare blocking: realistic UA + graceful degradation + honest Warn if blocked.
- Exact surface-selection heuristics (how to sample PDPs) to be finalized when we write the `crawl-storefront` skill.

---

## Phase 2 — Reason (FINALIZED)

Goal: turn the frozen Phase-1 artifacts into **structured JSON intermediates** — one per report section — that are evidence-bound, span all 5 pillars, and are store-specific (not generic CRO boilerplate). Write is a thin renderer over these (see Reason/Write split below).

### Inputs (the Crawl→Reason contract)

`manifest.json` — surface index:
```json
{ "store":"gingerpeople.com","crawled_at":"...",
  "surfaces":[ {"id":"home","type":"homepage","url":"...","status":200,"page_json":"home/page.json"},
               {"id":"pdp-gingins","type":"product","url":"...","status":200,"page_json":"..."},
               {"id":"cart","type":"cart","url":".../cart","status":404,"page_json":"..."} ] }
```

`<surface>/page.json` — per-page record. The two highest-weight fields for reasoning are **`cro_signals` (esp. `present:false`)** and **`network`** — absence-of-element + status/timing data are what make leaks specific instead of generic:
```json
{ "url":"...","type":"product","status":200,"title":"...",
  "meta":{"title":"...","description":"...","og":{...},"viewport":"...","jsonld":[...]},
  "elements":[ {"role":"button","text":"Add to cart","visible":true,"aboveFold":true,"bbox":[...]},
               {"role":"link","text":"WHERE TO BUY","href":"/where-to-buy","nav":true} ],
  "cro_signals":{ "price":{"present":false}, "add_to_cart":{"present":false},
                  "reviews":{"present":true,"value":"86 reviews"},
                  "trust_badges":{"present":true,"items":["America's #1 selling ginger candy"]},
                  "search":{"present":true}, "promo_bar":{"present":false},
                  "primary_cta":{"present":true,"text":"Buy online or find it…"} },
  "text_blocks":[{"role":"h1","text":"GIN GINS Original…"}],
  "content":"GIN GINS Original Ginger Chews… 10% fresh ginger… for nausea, motion sickness, morning sickness… (readable body, capped)",
  "screenshots":["product/screenshots/gingins-fullpage.png","…-hero.png"],
  "network":{"nav_timing_ms":2400,"requests":88,"transfer_kb":5400,
             "redirects":[...],"security_headers":{...},
             "responses":[{"url":".../cart","status":404}]},
  "console_errors":[...] }
```

### Three grounding forces (why Reason needs more than DOM signals)

`cro_signals` only know presence/absence — they can't tell whether something *looks* bad, and they don't make advice *product-specific*. Reason composes three forces:

| Force | Source | Answers |
|---|---|---|
| **Factual** | `cro_signals` / `network` (DOM) | what exists / is broken |
| **Perceptual** | screenshots + **vision** (agent `Read`s PNGs) | does it *look* unclear / cluttered / low-contrast |
| **Specificity** | **`store_profile.json`** (built first from `content`) | what this store actually sells, to whom |

Leak playbook → *coverage*; store profile → *specificity*; evidence binding (DOM **+** network **+** visual) → *grounding*.

### One structured intermediate per report section

| Report section | Reason output | Data source |
|---|---|---|
| 10 experiments | `experiments.json` | LLM reasoning over artifacts (core pipeline) |
| Executive summary | `synthesis.json` (top 2–3 themes) | rollup of top-ranked leaks |
| Competitor analysis | `competitors.json` | **web research** — niche inferred from artifacts |
| Technical checks | `tech_checks.json` | LLM-written, **artifact-grounded** (see guardrail) |

**Reason/Write split (locked):** Reason emits the JSON above; **Write is a thin renderer** to the report format. The eval system reads the structured JSON directly rather than parsing prose.

### The experiment pipeline (core — locked: structured, not single-pass)

0. **Store profile (built first).** Read `content` + product names + meta across surfaces → `store_profile.json`: product families, **jobs-to-be-done / use-cases**, customer segments, proof points, content themes, brand voice. This is the specificity anchor every experiment must connect to.
1. **Visual-critique pass.** Agent `Read`s the saved screenshots and emits **located, evidence-bound** findings (not vibes) → `visual_findings.json`: `{observation, screenshot_ref, region, severity, pillar}`. CRO-visual rubric: above-fold clarity, visual hierarchy / primary-action prominence, CTA contrast & legibility, clutter / cognitive load, imagery quality & brand consistency, visual prominence of proof.
2. **Leak detection (per surface).** Walk each `page.json` through the pillar → leak-pattern playbook (below) as a *coverage lens*. Every detected leak names its **triggering signal** — now one of **three types**: a `cro_signals` fact (`pdp-gingins.cro_signals.add_to_cart.present=false`), a `network` fact (`cart.status=404`), or a `visual_findings` entry. → `leaks.json`
3. **Candidate experiments (evidence-bound + specificity-bound).** Each candidate binds `{surface_id, screenshot_path, triggering_signal}` **and** must name a concrete product / family / page / use-case from `store_profile.json`.
   - **No evidence binding → dropped** (anti-hallucination).
   - **Fails the specificity guard → dropped** ("add a bundle" is rejected; "Travel Stomach Rescue Kit from the 3 Ginger Rescue formats" passes). Both checks are mechanical and eval-visible.
4. **Score + select with pillar-coverage guard.** Generate >10 candidates, score each by `impact × evidence_strength × confidence`, select 10 subject to **≥1 per pillar (all 5 present)**. Empty pillar → loop back / down-rank an over-represented pillar. Skew is allowed (anchor was Conversion 4 / AOV 2 / Acquisition 2 / Retention 1 / Performance 1); **gaps are not**.
5. **Derive confidence + expected-lift from evidence strength** via rubric (below) — not vibes. Lets the eval later check confidence↔evidence **coherence** instead of unknowable realized lift.

### Pillar → leak-pattern playbook (the coverage lens)

- **Conversion** — missing/ambiguous CTA, no price, no add-to-cart, broken purchase path, no above-fold proof.
- **AOV** — no bundles/kits, no cross-sell/upsell, no sampler, no volume/subscription tiers.
- **Retention** — no subscribe-and-save/reorder, no account/loyalty, no post-purchase routine, weak email-capture value.
- **Acquisition** — thin/missing high-intent landing pages, SEO meta gaps, missing structured data, un-commercialized content.
- **Performance** — slow `nav_timing_ms`, heavy `transfer_kb`, 404s/broken links, console errors, unreachable cart/checkout.

The two "hard" pillars are data-backed, not vibes: **Performance maps to `network`**, **Acquisition maps to `meta`/content surfaces** — which is exactly why Phase 1 captures both.

### Confidence + expected-lift derivation rubric

- Direct structural absence observed in artifact (e.g. no add-to-cart) → **80–88%**, larger lift band.
- Strong inference from present signals (proof exists but path ambiguous) → **70–80%**.
- Pattern / best-practice with partial evidence, or a net-new page → **65–72%**, flagged as inferential.

### Technical checks (locked: LLM-written + grounding guardrail)

Agent writes the ~15-row table itself, but **each row must cite the artifact field it rests on** (e.g. `/cart` Fail ← `network.responses[].status=404`; SSL Pass ← HTTPS load + `security_headers`). If no artifact field covers a check → honest **Warn "not inspected"** (anchor posture). LLM writes the prose; it cannot claim a Pass it can't point at. The eval's evidence-grounding check polices this.

### Competitor analysis (locked: web research)

Infer the store's niche from artifacts (what it sells, category language) → `WebSearch` for 3–4 real competitors → compare positioning / what they make easier / patterns to adapt. Web-grounded so it generalizes to unseen stores (zenrojas) rather than relying on stale model memory.

### Reason output schemas (the FIXED contract Write + Eval consume)

All under `artifacts/<store>/reason/`.

**`experiments.json`** — canonical schema; `evidence` carries all three bindings (screenshot + structured signal + specificity) so the eval can check them mechanically:
```json
{ "experiments":[ {
  "exp_id":"exp-e06feea44fdb",          // "exp-"+first 12 hex of hash(store+title+surface) — stable/reproducible
  "title":"Add a buying box to every product", "pillar":"Conversion",
  "affected_surface":"GIN GINS Original PDP (pattern applies to all PDPs)",
  "url":"https://gingerpeople.com/products/gin-gins-original-ginger-chews/",
  "evidence":{ "screenshot":"artifacts/gingerpeople/pdp-gingins/screenshots/gingins-fullpage.png",
               "triggering_signal":"pdp-gingins.cro_signals.add_to_cart.present=false",
               "signal_type":"cro_signals|network|visual",
               "store_profile_ref":"family:GIN GINS; job:purchase-clarity" },
  "hypothesis":"...", "primary_change":"...",
  "primary_kpi":"Outbound retailer click rate",
  "decision_rule":"Ship if outbound retailer click rate improves without hurting PDP bounce.",
  "expected_lift":{"low":12,"high":20,"unit":"%"}, "confidence":78,
  "confidence_basis":"direct structural absence"   // ties to derivation rubric → eval coherence check
} ] }
```

**`store_profile.json`** — `commerce_model` is load-bearing (retailer-routed ⇒ KPIs are outbound-retailer-click, not add-to-cart):
```json
{ "store":"gingerpeople.com","niche":"ginger functional foods + candy",
  "commerce_model":"retailer-routed|direct|hybrid",
  "families":[{"name":"GIN GINS","type":"candy","products":["Original","Mandarin"]},{"name":"Ginger Rescue"}],
  "jobs_to_be_done":["nausea","travel/motion-sickness","GLP-1 side-effects","morning sickness","cooking"],
  "segments":["functional-relief","candy-snacker","cook","wholesale"],
  "proof_points":["86 reviews","America's #1 selling ginger candy","10% fresh ginger"],
  "content_themes":["recipes","health education","GLP-1"], "brand_voice":"..." }
```

**`visual_findings.json`** `{ "findings":[ {"id":"vf1","observation":"...","screenshot_ref":"...","region":"hero/above-fold","severity":"high","pillar":"Conversion"} ] }`

**`leaks.json`** `{ "leaks":[ {"id":"leak1","pillar":"...","surface_id":"...","triggering_signal":"...","signal_type":"cro_signals|network|visual","severity":"high","description":"..."} ] }`

**`competitors.json`** — `source_url` per row keeps the table web-grounded:
```json
{ "niche":"...","competitors":[ {"name":"Dramamine","domain":"dramamine.com","positioning":"...",
  "makes_easier":"...","our_edge":"...","pattern_to_adapt":"...","source_url":"https://..."} ] }
```

**`tech_checks.json`** — `grounded_in` enforces the no-fabricated-Pass guardrail:
```json
{ "checks":[ {"name":"SSL Certificate","status":"Pass","detail":"HTTPS storefront loaded.","grounded_in":"home.network.security_headers + https load"},
  {"name":"Broken Links","status":"Fail","detail":"/cart returned 404.","grounded_in":"cart.network.responses[].status=404"} ] }
```

**`synthesis.json`** — themes + supporting `exp_id` refs. **No prose** — the exec summary is authored in Write (locked below):
```json
{ "headline":"Ginger People audit — the buy path is now the constraint",
  "themes":[ {"title":"Purchase handoff is leaking demand","summary":"...","supporting_exp_ids":["exp-...","exp-..."]} ] }
```

### Open / deferred
- Exact scoring weights for `impact × evidence_strength × confidence` — tune when writing the `reason-pillars` skill.
- Whether `synthesis.json` is a separate step or falls out of the experiment ranking — decide during build.

---

## Phase 3 — Write (FINALIZED)

Goal: assemble the Phase-2 JSON intermediates into `report.md`, matching the anchor's output contract exactly. The structured data is already authored in Reason; Write's only original prose is the executive summary.

### Locked decisions
- **Write is an LLM step (the `write-report` skill).** The agent (a) **composes the 2–3 paragraph executive summary** from `synthesis.themes` (+ the supporting experiments it references), and (b) **template-assembles** the structured sections from JSON. Prose ownership sits in Write; everything else is mechanical templating.
- **Shared `validate.py` (one validator, two callers).** A single structural validator is the pre-render gate here AND the eval's Layer-1 scoring component — write once, reuse. DRY seam into Part 2.

### Steps
1. **Pre-render gate — `validate.py`.** Exactly 10 experiments? All 5 pillars present? Every schema field non-empty? Every `evidence.screenshot` path resolves to a real file? Tech table ~15 rows? **Fail loudly** rather than render a broken report (and loop back to Reason if needed).
2. **Compose executive summary (LLM).** 2–3 flowing paragraphs from `synthesis.themes`, grounded in the actual 10 (theme → `supporting_exp_ids`). The only free-prose part of the report.
3. **Template-assemble the rest** in anchor order: title (`synthesis.headline`) → exec summary → **10 experiments** (loop `experiments.json` → labeled-field blocks matching the anchor's `Pillar:` / `Affected surface:` / `URL:` / `Evidence:` / `Hypothesis:` / `Primary change:` / `Primary KPI:` / `Decision rule:` / `Expected lift:` / `Confidence:` layout 1:1) → **competitor** intro + table (`competitors.json`) → **technical checks** table (`tech_checks.json`).
4. **Emit** to `sample_output/<store>.md`.

### Notes
- The anchor's experiment format is **literally labeled fields**, so the template maps 1:1 — no creative rendering needed beyond the exec summary.
- Output format is `.md` (README allows `.md`/`.html`, styling irrelevant; `.md` is diff-able and matches the anchor). HTML is a trivial later swap.
- Reproducibility caveat (accepted): because the exec summary is LLM-authored, Write is not bit-reproducible. Everything else (experiments/competitor/tech tables) is deterministic templating, so only ~3 paragraphs vary run-to-run.
