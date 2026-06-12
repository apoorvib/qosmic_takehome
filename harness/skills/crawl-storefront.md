---
name: crawl-storefront
description: Phase 1 of a Qosmic audit. Use when given a Shopify storefront URL to capture. Discovers a representative set of surfaces via the browser, then runs extract.py to produce durable artifacts (page.json + screenshots + network facts) that the reason-audit skill consumes.
---

# Crawl a storefront

You are the Qosmic audit agent. Goal of this phase: turn one storefront URL into a frozen artifact set under `artifacts/<store>/`, conforming to `harness/schemas/manifest.schema.json` and `page.schema.json`.

**Division of labor (Model 2):** you discover *which* URLs to crawl using the browser; `extract.py` does the deterministic capture. You do **not** hand-extract DOM — that is the script's job, so runs stay reproducible.

## Step 1 — Discover surfaces (browser, nav-driven)

Open the storefront homepage with the Playwright MCP browser. Read the header nav and footer links. **Do not hardcode paths** — classify links by Shopify conventions (`/products/`, `/collections/`, `/cart`, `/pages/`, `/blogs/`) and by the store's own nav labels (some stores use custom paths, e.g. `/where-to-buy-...`).

Pick a representative set, **capped at ~8–10 surfaces**:

- homepage
- 1–2 product pages (PDPs) — sample real product links from a collection/grid
- 1 collection / catalog page
- `/cart`
- 2–3 intent/content pages — e.g. Where-to-buy, FAQ, About, a key blog/education page

Prefer surfaces that reveal the buying path and the brand's highest-intent jobs. **Safety: include `/cart` but never proceed through checkout.**

## Step 2 — Capture with extract.py

Hand the chosen URLs to the script. It re-navigates each URL itself (fresh browser context per URL — this defeats Cloudflare-style rate-limit blocks — plus popup dismissal, scroll/lazy-load, full-page + hero screenshots, role-based DOM extraction, present/absent CRO signals, and network facts):

```
python harness/scripts/extract.py --store <store-slug> --out artifacts/<store-slug> \
  "<homepage-url>" "<pdp-url>" "<collection-url>" "<cart-url>" "<content-url>" ...
```

Notes:
- Pass the homepage URL **first**.
- The script prints `[surface-id] <status> <url>` per surface and writes `manifest.json`.
- A surface that returns 403/blocked after retry is recorded with a console-error note → treat downstream as **Warn "not inspected"**, never fabricate.

## Step 3 — Confirm and hand off

Read `artifacts/<store>/manifest.json` and skim each `page.json`. Sanity-check that:
- the homepage, a PDP, a collection, `/cart`, and content pages were captured
- `cro_signals` look right (e.g. a PDP with no `add_to_cart.present` is a real, high-value finding — keep it)
- real `network.responses` statuses are present (e.g. a `/cart` 404)

Then proceed to **reason-audit**. The reason phase reads these artifacts (including `Read`-ing the saved screenshots) and never re-crawls.

## Deferred / known limits
- `extract.py` classifies surface `type` from URL patterns; stores with non-standard paths may be typed `other`. The content is still captured — rely on `content`/`title` when reasoning, not just `type`.
- `security_headers` capture is best-effort; ground the SSL/HSTS tech check in the successful HTTPS load when headers are absent.
