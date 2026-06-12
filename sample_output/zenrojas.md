# Zen Rojas audit — premium tea, but the path from intent to ritual leaks

## Executive summary

**Zen Rojas sells a premium ritual, but the path from intent to purchase is taxed at every step.** The storefront is a clean, direct-sell Shopify catalog of organic functional teas — Sleep, Heartburn, Bodyguard immunity, Sencha, plus samplers and accessories — with real prices and a working cart. The problem is not the product; it is the friction around it. A full-screen email-capture popup ("Subscribe to get a reward now") overlays the hero on load across the homepage and product pages, blocking the first impression before a visitor sees the value proposition. And on a premium-priced PDP (Organic Sleep Tea at over Rs. 1,150), there is a review widget but no visible rating, review count, organic-certification badge, or guarantee near the buy box — so the highest-stakes moment lacks reassurance.

**The "ritual" positioning is under-monetized.** Teas, accessories (mug, infuser, tea bags), and samplers are all sold separately, with no starter kits, no "complete your ritual" cross-sell near the buy box, and no subscribe-and-save on what is fundamentally a repeat-consumption product. For a brand built on daily ritual, the absence of bundles and subscription is the clearest path to higher average order value and recurring revenue. The existing Ambassador Program — a ready-made loyalty asset — sits buried in the footer, never surfaced at the moments that would activate it.

**Functional demand and strong content go uncaptured, and the pages are heavy.** Benefit-led navigation (shop by sleep / digestion / immunity), dedicated intent landing pages, and a commercialized founder/education story would turn search traffic and brand narrative into shopping; today that intent disperses across product copy and blog posts. Underneath, the site is technically heavy — 200+ requests per page, ~20 console errors from failing third-party scripts, and a best-sellers collection that took roughly ten seconds to load in capture, plus missing structured data. The first tests should be structural: tame the popup, add social proof to PDPs, and introduce bundles and subscribe-and-save; navigation, landing pages, and a performance pass follow.

## Proposed experiments

### exp-66a199e63076 — Trigger the email popup on exit-intent instead of blocking the hero on load

**Pillar:** Conversion  
**Affected surface:** home  
**URL:** https://zenrojas.com/  
**Evidence:** `home/screenshots/home-hero.png` (signal: `visual_findings.vf-intrusive-popup`)  
**Hypothesis:** A full-screen subscribe popup overlays the hero on load across the homepage and PDPs, taxing the first impression before a visitor sees the product or value proposition.  
**Primary change:** Switch the email popup to fire on exit-intent or after ~20s/scroll, and keep the reward offer; never overlay the hero on first load.  
**Primary KPI:** Bounce rate / homepage engagement  
**Decision rule:** Ship if Bounce rate / homepage engagement improves without hurting site-wide conversion.  
**Expected lift:** +5–12%  
**Confidence:** 78%

### exp-42f57ce0b20a — Add visible social proof and trust badges to PDPs

**Pillar:** Conversion  
**Affected surface:** pdp-organicsleeptea  
**URL:** https://zenrojas.com/products/organicsleeptea  
**Evidence:** `pdp-organicsleeptea/screenshots/pdp-organicsleeptea-fullpage.png` (signal: `pdp-organicsleeptea.cro_signals.trust_badges.present=false`)  
**Hypothesis:** The Organic Sleep Tea PDP has a review widget but no visible review count, rating, organic-certification badge, or guarantee near the buy box, so a premium-priced product lacks reassurance at the decision point.  
**Primary change:** Surface star rating + review count, an organic/quality badge, and a satisfaction guarantee directly under the price and add-to-cart.  
**Primary KPI:** Add-to-cart / PDP conversion rate  
**Decision rule:** Ship if Add-to-cart / PDP conversion rate improves without hurting site-wide conversion.  
**Expected lift:** +8–15%  
**Confidence:** 82%

### exp-6d09faf9a241 — Add benefit-led navigation to collections

**Pillar:** Conversion  
**Affected surface:** collection-teas  
**URL:** https://zenrojas.com/collections/teas  
**Evidence:** `collection-teas/screenshots/collection-teas-fullpage.png` (signal: `visual_findings.vf-collection-no-benefit-filter`)  
**Hypothesis:** Collections list teas by name with no benefit filters, asking shoppers to decode products rather than shop their goal (sleep, digestion, immunity).  
**Primary change:** Add benefit chips/filters ('For sleep', 'For digestion', 'For immunity', 'Daily ritual') and benefit-led section headers to the collection.  
**Primary KPI:** Collection click-through to PDP  
**Decision rule:** Ship if Collection click-through to PDP improves without hurting site-wide conversion.  
**Expected lift:** +6–12%  
**Confidence:** 74%

### exp-dd40992149d1 — Launch a tea + accessory ritual bundle

**Pillar:** AOV  
**Affected surface:** collection-teas  
**URL:** https://zenrojas.com/collections/teas  
**Evidence:** `collection-teas/screenshots/collection-teas-fullpage.png` (signal: `visual_findings.vf-no-ritual-bundle`)  
**Hypothesis:** Teas and accessories (mug, infuser, tea bags) are sold separately; the brand's 'ritual' positioning is a natural fit for a starter kit that lifts basket size.  
**Primary change:** Create a 'Zen Ritual Starter Kit' bundling a featured tea + mug + infuser at a modest bundle discount, merchandised on home and collections.  
**Primary KPI:** Average order value  
**Decision rule:** Ship if Average order value improves without hurting site-wide conversion.  
**Expected lift:** +8–16%  
**Confidence:** 71%

### exp-44b11a3e464c — Add 'complete your ritual' cross-sell to PDPs

**Pillar:** AOV  
**Affected surface:** pdp-organicsleeptea  
**URL:** https://zenrojas.com/products/organicsleeptea  
**Evidence:** `pdp-organicsleeptea/screenshots/pdp-organicsleeptea-fullpage.png` (signal: `visual_findings.vf-pdp-no-crosssell`)  
**Hypothesis:** The PDP has no cross-sell near the buy box, missing the obvious accessory and sampler attach for a ritual product.  
**Primary change:** Add a 'Complete your ritual' module under add-to-cart suggesting an infuser, mug, or a complementary sampler.  
**Primary KPI:** Average order value / units per order  
**Decision rule:** Ship if Average order value / units per order improves without hurting site-wide conversion.  
**Expected lift:** +6–12%  
**Confidence:** 71%

### exp-bb38b538987f — Offer subscribe-and-save on consumable teas

**Pillar:** Retention  
**Affected surface:** pdp-organicsleeptea  
**URL:** https://zenrojas.com/products/organicsleeptea  
**Evidence:** `pdp-organicsleeptea/screenshots/pdp-organicsleeptea-fullpage.png` (signal: `visual_findings.vf-pdp-no-subscription`)  
**Hypothesis:** Tea is a repeat-consumption ritual product, but PDPs offer only one-time purchase, leaving recurring revenue and retention on the table.  
**Primary change:** Add a subscribe-and-save option (e.g. 10% off, monthly/bi-monthly) to consumable tea PDPs with easy management.  
**Primary KPI:** Subscription opt-in rate / repeat purchase rate  
**Decision rule:** Ship if Subscription opt-in rate / repeat purchase rate improves without hurting site-wide conversion.  
**Expected lift:** +7–14%  
**Confidence:** 74%

### exp-71555c487d72 — Surface the Ambassador / loyalty program at key moments

**Pillar:** Retention  
**Affected surface:** home  
**URL:** https://zenrojas.com/  
**Evidence:** `home/screenshots/home-fullpage.png` (signal: `visual_findings.vf-ambassador-buried`)  
**Hypothesis:** The Ambassador Program is buried in the footer and never surfaced at purchase or post-purchase, so an existing loyalty asset goes unused.  
**Primary change:** Promote the Ambassador Program in the post-purchase flow, account area, and a homepage band, with a clear reward and share path.  
**Primary KPI:** Referral / repeat-customer rate  
**Decision rule:** Ship if Referral / repeat-customer rate improves without hurting site-wide conversion.  
**Expected lift:** +4–9%  
**Confidence:** 68%

### exp-13ceb164e75c — Build functional intent landing pages

**Pillar:** Acquisition  
**Affected surface:** content-weekly-blog  
**URL:** https://zenrojas.com/blogs/weekly-blog  
**Evidence:** `content-weekly-blog/screenshots/content-weekly-blog-fullpage.png` (signal: `visual_findings.vf-blog-uncommercialized`)  
**Hypothesis:** High-intent functional searches ('best organic tea for sleep', 'tea for heartburn') have no dedicated landing pages; the benefit content is buried in product copy and blog posts.  
**Primary change:** Create benefit landing pages (sleep, digestion, immunity) with the relevant teas, proof, FAQs and internal links from blog content.  
**Primary KPI:** Organic landing-page sessions and conversion  
**Decision rule:** Ship if Organic landing-page sessions and conversion improves without hurting site-wide conversion.  
**Expected lift:** +10–20%  
**Confidence:** 71%

### exp-27c70334829a — Commercialize the founder and education content

**Pillar:** Acquisition  
**Affected surface:** content-weekly-blog  
**URL:** https://zenrojas.com/blogs/weekly-blog  
**Evidence:** `content-weekly-blog/screenshots/content-weekly-blog-fullpage.png` (signal: `visual_findings.vf-founder-uncommercialized`)  
**Hypothesis:** The founder/family story and tea-education content build trust but do not route readers to products or a brand-story shopping path.  
**Primary change:** Add product modules and 'shop the story' CTAs into the founder post and education articles, linking to relevant teas and samplers.  
**Primary KPI:** Content-attributed sessions to PDP  
**Decision rule:** Ship if Content-attributed sessions to PDP improves without hurting site-wide conversion.  
**Expected lift:** +5–10%  
**Confidence:** 70%

### exp-786caca48c5c — Reduce page weight and failed third-party scripts

**Pillar:** Performance  
**Affected surface:** collection-best-sellers  
**URL:** https://zenrojas.com/collections/best-sellers  
**Evidence:** `collection-best-sellers/screenshots/collection-best-sellers-fullpage.png` (signal: `visual_findings.vf-perf-heavy`)  
**Hypothesis:** Pages fire 200+ requests with ~20 console errors from failed third-party (shop.app) scripts, and the best-sellers collection took ~10s to load in capture — a real speed and reliability drag on conversion.  
**Primary change:** Audit and lazy-load imagery, defer/remove failing third-party scripts, and compress hero/product images to cut requests and load time.  
**Primary KPI:** Page load time (LCP) and bounce  
**Decision rule:** Ship if Page load time (LCP) and bounce improves without hurting site-wide conversion.  
**Expected lift:** +8–18%  
**Confidence:** 78%

## Competitor analysis

Competitors in premium organic wellness tea make the shopping job easier through clearer use-case navigation and retailer handoffs; the patterns below are the ones worth adapting.

| Competitor | Domain | Positioning | What they make easier | Our edge | Pattern to adapt |
|---|---|---|---|---|---|
| Pukka Herbs | pukkaherbs.com | Organic herbal wellness teas | Benefit-led navigation (sleep, detox, energy) | Loose-leaf premium ritual + founder story | Benefit-first collection navigation and clear functional outcomes |
| Traditional Medicinals | traditionalmedicinals.com | Wellness teas with specific functional uses | Condition-specific product discovery | Premium loose-leaf and a curated ritual experience | Symptom/benefit landing pages with proof |
| Vahdam Teas | vahdam.com | Premium Indian-origin teas, direct-to-consumer | Subscriptions, bundles, strong reviews/social proof | Tighter functional ritual focus and brand story | Subscribe-and-save, gift bundles, prominent ratings |
| Art of Tea | artoftea.com | Premium loose-leaf tea and accessories | Tea + accessory bundles and starter kits | Functional wellness positioning and founder narrative | Ritual starter kits pairing tea with brewing accessories |

## Technical checks

| Check | Status | Detail |
|---|---|---|
| SSL Certificate | Pass | HTTPS storefront with security headers present. |
| HTTPS Redirect | Pass | Storefront resolves over HTTPS. |
| Sitemap | Warn | Not inspected in this browser-first crawl. |
| Robots.txt | Warn | Not inspected in this browser-first crawl. |
| Critical Pages Loading | Pass | Home, collections, PDPs and cart all returned 200. |
| Meta Tags & Social Previews | Pass | Title and meta description present on homepage. |
| Structured Data | Fail | No JSON-LD structured data detected on homepage. |
| Favicon | Warn | Not evaluated from captured evidence. |
| Mobile-Friendly | Warn | Desktop-only crawl. |
| Page Speed Mobile | Warn | No mobile Lighthouse run performed. |
| Page Speed Desktop | Warn | No Lighthouse run; best-sellers collection took ~10s in capture. |
| Broken Links | Warn | No 4xx among inspected surfaces; not exhaustively crawled. |
| Image Optimization | Warn | Not byte-measured; 200+ requests/page observed. |
| Cookie/Privacy | Warn | Consent mechanics not inspected. |
| Checkout Reachable | Pass | Cart reachable (200); checkout not entered (safety). |
