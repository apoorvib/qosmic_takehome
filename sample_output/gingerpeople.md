# Ginger People audit — the proof is strong; the buy path is the constraint

## Executive summary

**Ginger People has the proof; the purchase handoff is leaking the demand.** The live storefront loads as a branded, content-rich site — Products, Bulk Ingredients, Recipes, a Health Blog, and Where To Buy — and the hero GIN GINS Original PDP carries real intent signals: 86 reviews, "Voted Best Candy," "10% fresh ginger," and "World's #1 selling ginger candy." But the captured buying area is plain text ("Buy online or find it in the candy aisle…") with no price, add-to-cart, or structured retailer module, and every surface's primary call to action is the same generic "WHERE TO BUY." For a retailer-routed brand, ambiguity at the moment of intent is the single largest conversion leak.

**The two adjacent purchase surfaces compound the problem.** The primary-nav Where To Buy page resolves to an error banner ("There was something wrong!") over blog cards, with no store locator, retailer list, or online-buying choices — so the most explicit purchase-intent link in the nav resolves intent for no one. And `/cart` returns a branded 404; even for a retailer-routed brand, that URL is a common destination for returning users, old links, tracking tools, and partner referrals, so high-intent sessions silently die there. Together these mean every product page that says "find it locally" is weaker than it could be.

**The content moat is strong and under-commercialized.** Recipes, the health blog, and the GLP-1 education page (which notes nausea affects up to half of GLP-1 patients) are acquisition and retention surfaces waiting to be turned into guided shopping, reorderable routines, and condition landing pages — and the broad format range (candy, lozenges, tablets, juices) supports kits and samplers that lift basket size. The first tests should be structural: add a buying box to PDPs, rebuild Where To Buy into a real handoff, and fix the `/cart` 404. Mission-based navigation, need quizzes, and content-led routines follow.

## Proposed experiments

### exp-37868b457e66 — Add a buying box to every product page

**Pillar:** Conversion  
**Affected surface:** pdp-gin-gins-original-ginger-chews  
**URL:** https://gingerpeople.com/products/gin-gins-original-ginger-chews/  
**Evidence:** `pdp-gin-gins-original-ginger-chews/screenshots/pdp-gin-gins-original-ginger-chews-fullpage.png` (signal: `pdp-gin-gins-original-ginger-chews.cro_signals.add_to_cart.present=false`)  
**Hypothesis:** The GIN GINS PDP creates strong intent (86 reviews, 'Voted Best Candy', 10% fresh ginger) but the buying area is ambiguous text with no price, add-to-cart, or retailer module — so high-intent shoppers have no clear next step.  
**Primary change:** Add a persistent 'Choose how to buy' box under the product title: 'Buy online', 'Find near me', plus compact retailer logos.  
**Primary KPI:** Outbound retailer click rate  
**Decision rule:** Ship if Outbound retailer click rate improves without hurting site-wide conversion or PDP engagement.  
**Expected lift:** +12–20%  
**Confidence:** 84%

### exp-36a71e50f2e5 — Rebuild the Where To Buy page into a purchase handoff

**Pillar:** Conversion  
**Affected surface:** page-where-to-buy-the-ginger-people-products  
**URL:** https://gingerpeople.com/where-to-buy-the-ginger-people-products/  
**Evidence:** `page-where-to-buy-the-ginger-people-products/screenshots/page-where-to-buy-the-ginger-people-products-fullpage.png` (signal: `visual_findings.vf-wtb-broken`)  
**Hypothesis:** The most explicit purchase-intent nav link resolves to an error banner and blog cards with no store locator or retailer list, so every PDP that says 'find it locally' is weaker than it could be.  
**Primary change:** Replace the body with a ZIP/store locator, 'Shop online' retailer cards, product-family filters, and a 'Can't find it? Tell us your ZIP' capture.  
**Primary KPI:** Outbound retailer click rate  
**Decision rule:** Ship if Outbound retailer click rate improves without hurting site-wide conversion or PDP engagement.  
**Expected lift:** +15–25%  
**Confidence:** 79%

### exp-983f6011ec3a — Turn the homepage into shopper-mission cards

**Pillar:** Conversion  
**Affected surface:** home  
**URL:** https://gingerpeople.com/  
**Evidence:** `home/screenshots/home-hero.png` (signal: `visual_findings.vf-home-single-cta`)  
**Hypothesis:** A single broad entrance asks too much of a first-time visitor when the buyer split is functional relief vs candy vs cooking vs wholesale.  
**Primary change:** Rebuild the first screen into mission cards: 'Settle my stomach', 'Find ginger candy', 'Cook with ginger', 'Buy for my business', each linking to the right category.  
**Primary KPI:** Homepage click-through to category  
**Decision rule:** Ship if Homepage click-through to category improves without hurting site-wide conversion or PDP engagement.  
**Expected lift:** +6–10%  
**Confidence:** 73%

### exp-7a69a513f9f6 — Sell a travel nausea kit from the Ginger Rescue formats

**Pillar:** AOV  
**Affected surface:** pdp-ginger-rescue-hard-ginger-lozenges  
**URL:** https://gingerpeople.com/products/ginger-rescue-hard-ginger-lozenges/  
**Evidence:** `pdp-ginger-rescue-hard-ginger-lozenges/screenshots/pdp-ginger-rescue-hard-ginger-lozenges-fullpage.png` (signal: `visual_findings.vf-rescue-no-bundle`)  
**Hypothesis:** Travel/motion-sickness is one of the highest-intent jobs, but the Ginger Rescue lozenge and tablet formats are merchandised separately with no kit.  
**Primary change:** Launch a 'Travel Stomach Rescue Kit' bundling the lozenge + chewable tablet formats, promoted on Ginger Rescue PDPs and a travel-nausea page.  
**Primary KPI:** AOV among Ginger Rescue visitors  
**Decision rule:** Ship if AOV among Ginger Rescue visitors improves without hurting site-wide conversion or PDP engagement.  
**Expected lift:** +8–14%  
**Confidence:** 71%

### exp-1b3fb2cdfea3 — Build a GIN GINS flavor sampler pack

**Pillar:** AOV  
**Affected surface:** page-gin-gins  
**URL:** https://gingerpeople.com/gin-gins/  
**Evidence:** `page-gin-gins/screenshots/page-gin-gins-fullpage.png` (signal: `visual_findings.vf-gingins-no-sampler`)  
**Hypothesis:** First-time candy shoppers face a long flavor list with no low-risk way to try several, suppressing basket size.  
**Primary change:** Launch a 'GIN GINS Flavor Tour' sampler spanning Original, Mandarin, Lemon, Spicy Apple and Ginger Spice Drops.  
**Primary KPI:** AOV among first-time candy shoppers  
**Decision rule:** Ship if AOV among first-time candy shoppers improves without hurting site-wide conversion or PDP engagement.  
**Expected lift:** +7–12%  
**Confidence:** 71%

### exp-18102ea2895e — Package a GLP-1 ginger + turmeric support routine

**Pillar:** Retention  
**Affected surface:** page-boost-your-glp-1-naturally-the-power-of-  
**URL:** https://gingerpeople.com/boost-your-glp-1-naturally-the-power-of-ginger-turmeric/  
**Evidence:** `page-boost-your-glp-1-naturally-the-power-of-/screenshots/page-boost-your-glp-1-naturally-the-power-of--fullpage.png` (signal: `visual_findings.vf-glp1-no-routine`)  
**Hypothesis:** The GLP-1 article states nausea affects up to 50% of GLP-1 patients and recommends ginger/turmeric formats, but shoppers must assemble the routine themselves.  
**Primary change:** Create a 'GLP-1 Ginger + Turmeric Daily Support Routine' merchandising chews, lozenges and turmeric juice with reorder guidance, placed in the article.  
**Primary KPI:** 30-day repeat purchase rate (GLP-1 article visitors)  
**Decision rule:** Ship if 30-day repeat purchase rate (GLP-1 article visitors) improves without hurting site-wide conversion or PDP engagement.  
**Expected lift:** +6–12%  
**Confidence:** 68%

### exp-49c9c8d5b7ce — Add an 'add to my ginger routine' reorder path on PDPs

**Pillar:** Retention  
**Affected surface:** pdp-gin-gins-original-ginger-chews  
**URL:** https://gingerpeople.com/products/gin-gins-original-ginger-chews/  
**Evidence:** `pdp-gin-gins-original-ginger-chews/screenshots/pdp-gin-gins-original-ginger-chews-fullpage.png` (signal: `visual_findings.vf-pdp-no-reorder`)  
**Hypothesis:** These are consumable products bought for ongoing relief, but there is no path to set a routine or reorder reminder, so repeat demand is left to memory.  
**Primary change:** Add an 'Add to my ginger routine' opt-in on PDPs that emails reorder reminders and a retailer/online link for the chosen formats.  
**Primary KPI:** Repeat purchase / reorder-reminder opt-in rate  
**Decision rule:** Ship if Repeat purchase / reorder-reminder opt-in rate improves without hurting site-wide conversion or PDP engagement.  
**Expected lift:** +5–10%  
**Confidence:** 72%

### exp-8e982fbe6a42 — Create a Find-Your-Ginger need quiz

**Pillar:** Acquisition  
**Affected surface:** page-the-ginger-people-products  
**URL:** https://gingerpeople.com/the-ginger-people-products/  
**Evidence:** `page-the-ginger-people-products/screenshots/page-the-ginger-people-products-fullpage.png` (signal: `visual_findings.vf-products-clutter`)  
**Hypothesis:** The catalog asks shoppers to decode product names instead of shopping their job; need language exists but is buried in dense grids.  
**Primary change:** Create '/find-your-ginger/' with prompts (nausea, travel, cooking, daily wellness, candy) that route to a recommended family with proof and buy/find choices.  
**Primary KPI:** Landing-page conversion rate  
**Decision rule:** Ship if Landing-page conversion rate improves without hurting site-wide conversion or PDP engagement.  
**Expected lift:** +10–18%  
**Confidence:** 72%

### exp-d5b9f2e0fd37 — Create a morning-sickness ginger landing page

**Pillar:** Acquisition  
**Affected surface:** page-boost-your-glp-1-naturally-the-power-of-  
**URL:** https://gingerpeople.com/boost-your-glp-1-naturally-the-power-of-ginger-turmeric/  
**Evidence:** `page-boost-your-glp-1-naturally-the-power-of-/screenshots/page-boost-your-glp-1-naturally-the-power-of--fullpage.png` (signal: `visual_findings.vf-glp1-health-pattern`)  
**Hypothesis:** Morning-sickness intent is high-anxiety and disperses across blog, category and PDPs; the existing health-content pattern could anchor one compliant destination.  
**Primary change:** Create '/morning-sickness-ginger/' mirroring the health-content layout with testimonials, FAQ, 'ask your clinician' language and Ginger Rescue / GIN GINS choices.  
**Primary KPI:** Landing-page conversion rate  
**Decision rule:** Ship if Landing-page conversion rate improves without hurting site-wide conversion or PDP engagement.  
**Expected lift:** +10–16%  
**Confidence:** 70%

### exp-ea80b9088891 — Replace the /cart 404 with a purchase-recovery page

**Pillar:** Performance  
**Affected surface:** cart  
**URL:** https://gingerpeople.com/cart  
**Evidence:** `cart/screenshots/cart-fullpage.png` (signal: `cart.network.responses[].status=404`)  
**Hypothesis:** The /cart URL returns a branded 404. Even for a retailer-routed brand it is a common destination for returning users, old links, tracking tools and partner referrals — so high-intent sessions silently die.  
**Primary change:** Replace the /cart 404 with a purchase-recovery page: 'Continue shopping', 'Find a store', 'Shop online retailers' and support links.  
**Primary KPI:** /cart exit rate  
**Decision rule:** Ship if /cart exit rate improves without hurting site-wide conversion or PDP engagement.  
**Expected lift:** +10–20%  
**Confidence:** 85%

## Competitor analysis

Competitors in ginger functional foods + candy make the shopping job easier through clearer use-case navigation and retailer handoffs; the patterns below are the ones worth adapting.

| Competitor | Domain | Positioning | What they make easier | Our edge | Pattern to adapt |
|---|---|---|---|---|---|
| Dramamine | dramamine.com | OTC motion-sickness relief | Immediate use-case clarity for nausea/travel | Natural ginger formats and candy/snack permission | Dedicated nausea/travel pages with product-choice modules |
| Tummydrops | tummydrops.com | Ginger/peppermint drops for nausea & digestive comfort | Symptom-specific shopping | Broader catalog, recipes, mainstream candy formats | Symptom-led navigation and format comparisons |
| Reed's | drinkreeds.com | Ginger beverages and ginger candy | Beverage-led discovery and retail familiarity | Deeper ginger specialization and health education | Stronger retailer handoff per product family |
| Chimes Gourmet | chimesgourmet.com | Ginger chews and candy variety | Simple flavor-led candy shopping | Stronger functional use cases, reviews, recipes, family story | Flavor sampler and heat/flavor comparison |

## Technical checks

| Check | Status | Detail |
|---|---|---|
| SSL Certificate | Pass | HTTPS storefront loaded successfully (200). |
| HTTPS Redirect | Pass | Storefront resolves over HTTPS. |
| Sitemap | Warn | Not inspected in this browser-first crawl. |
| Robots.txt | Warn | Not inspected in this browser-first crawl. |
| Critical Pages Loading | Warn | Home, categories and PDPs loaded; /cart returned 404. |
| Meta Tags & Social Previews | Pass | Page title and meta description present on homepage. |
| Structured Data | Pass | JSON-LD structured data detected on homepage. |
| Favicon | Warn | Not evaluated from captured evidence. |
| Mobile-Friendly | Warn | Desktop-only crawl. |
| Page Speed Mobile | Warn | No mobile Lighthouse run performed. |
| Page Speed Desktop | Warn | No Lighthouse run; navigation timing only. |
| Broken Links | Fail | /cart returned a branded 404. |
| Image Optimization | Warn | Not byte-measured; PDPs use large visual assets. |
| Cookie/Privacy | Warn | Consent mechanics not inspected in this crawl. |
| Checkout Reachable | Fail | /cart unreachable (404); retailer-routed, no checkout entered. |
