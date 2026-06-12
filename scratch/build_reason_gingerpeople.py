#!/usr/bin/env python3
"""One-off authoring of the gingerpeople reason/*.json (the SAMPLE deliverable).

This encodes the audit *content* I reasoned from artifacts/gingerpeople/ (live
crawl: cro_signals, network, and the screenshots I Read). It is NOT part of the
generalizable harness (that's harness/skills + harness/scripts) — it just
serializes one store's reasoning into the frozen schema, the way the reason-audit
agent would emit JSON. Run, then gate with harness/scripts/validate.py.
"""
import hashlib, json
from pathlib import Path

STORE = "gingerpeople"
ROOT = Path("artifacts/gingerpeople")
SS = lambda sid, kind="fullpage": f"{sid}/screenshots/{sid}-{kind}.png"

# real surface ids from the crawl
HOME = "home"
PRODUCTS = "page-the-ginger-people-products"
GINGINS = "page-gin-gins"
PDP_CANDY = "pdp-gin-gins-original-ginger-chews"
PDP_RESCUE = "pdp-ginger-rescue-hard-ginger-lozenges"
CART = "cart"
WTB = "page-where-to-buy-the-ginger-people-products"
BLOG = "page-health-blog"
GLP1 = "page-boost-your-glp-1-naturally-the-power-of-"


def w(name, obj):
    p = ROOT / "reason" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def exp_id(title, surface):
    h = hashlib.sha1(f"{STORE}|{title}|{surface}".encode()).hexdigest()[:12]
    return f"exp-{h}"


store_profile = {
    "store": "gingerpeople.com", "niche": "ginger & turmeric functional foods + candy",
    "commerce_model": "retailer-routed",
    "families": [
        {"name": "GIN GINS", "type": "candy", "products": ["Original Ginger Chews", "Mandarin Orange", "Lemon", "Spicy Apple", "Ginger Spice Drops", "Boost Red Magic"]},
        {"name": "Ginger Rescue", "type": "lozenges/tablets", "products": ["Hard Ginger Lozenges", "Chewable Ginger Tablets", "Digestive Wellness Lozenges"]},
        {"name": "Ginger Soother", "type": "beverage", "products": ["Turmeric Gingerade"]},
        {"name": "Fiji Ginger Juice", "type": "juice", "products": ["Fiji Ginger Juice", "Fiji Turmeric Juice"]},
    ],
    "jobs_to_be_done": ["nausea", "travel/motion-sickness", "GLP-1 side-effects", "morning sickness", "digestive wellness", "cooking"],
    "segments": ["functional-relief", "candy-snacker", "cook", "wholesale"],
    "proof_points": ["World's #1 selling ginger candy", "86 reviews", "10% fresh ginger", "Voted Best Candy", "#1 source for ginger and turmeric"],
    "content_themes": ["recipes", "health blog", "GLP-1", "where-to-buy"],
    "brand_voice": "warm, health-forward, ginger-specialist family brand",
}

visual_findings = {"findings": [
    {"id": "vf-pdp-no-buybox", "observation": "PDP buying area is plain text ('Buy online or find it in the candy aisle…') with no price, add-to-cart, or structured retailer module where the eye lands.",
     "screenshot_ref": SS(PDP_CANDY, "hero"), "region": "buy-box/above-fold", "severity": "high", "pillar": "Conversion"},
    {"id": "vf-wtb-broken", "observation": "Where To Buy shows an error banner ('There was something wrong!') and blog cards — no store locator, retailer list, or online-buying cards.",
     "screenshot_ref": SS(WTB, "hero"), "region": "main", "severity": "high", "pillar": "Conversion"},
    {"id": "vf-home-single-cta", "observation": "Homepage leads with one product focus and a single 'WHERE TO BUY' route; no mission cards for the distinct buyer jobs (relief vs candy vs cooking).",
     "screenshot_ref": SS(HOME, "hero"), "region": "hero", "severity": "medium", "pillar": "Conversion"},
    {"id": "vf-products-clutter", "observation": "All-products grid lists many SKUs by product name with no need-first grouping; shoppers must decode product names rather than shop a job.",
     "screenshot_ref": SS(PRODUCTS), "region": "grid", "severity": "medium", "pillar": "Acquisition"},
    {"id": "vf-gingins-no-sampler", "observation": "GIN GINS category presents many flavors with no multi-flavor sampler or trial entry point.",
     "screenshot_ref": SS(GINGINS), "region": "grid", "severity": "medium", "pillar": "AOV"},
    {"id": "vf-rescue-no-bundle", "observation": "Ginger Rescue formats are shown separately; no travel/motion-sickness kit bundles the lozenge + tablet formats.",
     "screenshot_ref": SS(PDP_RESCUE), "region": "grid", "severity": "medium", "pillar": "AOV"},
    {"id": "vf-glp1-no-routine", "observation": "GLP-1 article educates (nausea affects up to 50% of GLP-1 patients) but offers no packaged, reorderable ginger+turmeric routine.",
     "screenshot_ref": SS(GLP1), "region": "article-body", "severity": "medium", "pillar": "Retention"},
    {"id": "vf-pdp-no-reorder", "observation": "Consumable PDP has no 'add to routine' / reorder-reminder path for repeat usage.",
     "screenshot_ref": SS(PDP_CANDY), "region": "buy-box", "severity": "medium", "pillar": "Retention"},
    {"id": "vf-glp1-health-pattern", "observation": "Health-content layout (education + formats) exists and could anchor condition landing pages like morning sickness.",
     "screenshot_ref": SS(GLP1), "region": "article-body", "severity": "low", "pillar": "Acquisition"},
]}

# (title, pillar, surface_id, url, screenshot, signal, signal_type, profile_ref, kpi, (lo,hi), conf, basis, hypothesis, change)
E = [
 ("Add a buying box to every product page", "Conversion", PDP_CANDY,
  "https://gingerpeople.com/products/gin-gins-original-ginger-chews/", SS(PDP_CANDY),
  f"{PDP_CANDY}.cro_signals.add_to_cart.present=false", "cro_signals", "family:GIN GINS; job:purchase-clarity",
  "Outbound retailer click rate", (12, 20), 84, "direct structural absence",
  "The GIN GINS PDP creates strong intent (86 reviews, 'Voted Best Candy', 10% fresh ginger) but the buying area is ambiguous text with no price, add-to-cart, or retailer module — so high-intent shoppers have no clear next step.",
  "Add a persistent 'Choose how to buy' box under the product title: 'Buy online', 'Find near me', plus compact retailer logos."),
 ("Rebuild the Where To Buy page into a purchase handoff", "Conversion", WTB,
  "https://gingerpeople.com/where-to-buy-the-ginger-people-products/", SS(WTB),
  "visual_findings.vf-wtb-broken", "visual", "content_theme:where-to-buy; segment:functional-relief",
  "Outbound retailer click rate", (15, 25), 79, "strong inference",
  "The most explicit purchase-intent nav link resolves to an error banner and blog cards with no store locator or retailer list, so every PDP that says 'find it locally' is weaker than it could be.",
  "Replace the body with a ZIP/store locator, 'Shop online' retailer cards, product-family filters, and a 'Can't find it? Tell us your ZIP' capture."),
 ("Turn the homepage into shopper-mission cards", "Conversion", HOME,
  "https://gingerpeople.com/", SS(HOME, "hero"),
  "visual_findings.vf-home-single-cta", "visual", "segment:candy-snacker; job:nausea",
  "Homepage click-through to category", (6, 10), 73, "strong inference",
  "A single broad entrance asks too much of a first-time visitor when the buyer split is functional relief vs candy vs cooking vs wholesale.",
  "Rebuild the first screen into mission cards: 'Settle my stomach', 'Find ginger candy', 'Cook with ginger', 'Buy for my business', each linking to the right category."),
 ("Sell a travel nausea kit from the Ginger Rescue formats", "AOV", PDP_RESCUE,
  "https://gingerpeople.com/products/ginger-rescue-hard-ginger-lozenges/", SS(PDP_RESCUE),
  "visual_findings.vf-rescue-no-bundle", "visual", "family:Ginger Rescue; job:travel/motion-sickness",
  "AOV among Ginger Rescue visitors", (8, 14), 71, "pattern / best-practice",
  "Travel/motion-sickness is one of the highest-intent jobs, but the Ginger Rescue lozenge and tablet formats are merchandised separately with no kit.",
  "Launch a 'Travel Stomach Rescue Kit' bundling the lozenge + chewable tablet formats, promoted on Ginger Rescue PDPs and a travel-nausea page."),
 ("Build a GIN GINS flavor sampler pack", "AOV", GINGINS,
  "https://gingerpeople.com/gin-gins/", SS(GINGINS),
  "visual_findings.vf-gingins-no-sampler", "visual", "family:GIN GINS; segment:candy-snacker",
  "AOV among first-time candy shoppers", (7, 12), 71, "pattern / best-practice",
  "First-time candy shoppers face a long flavor list with no low-risk way to try several, suppressing basket size.",
  "Launch a 'GIN GINS Flavor Tour' sampler spanning Original, Mandarin, Lemon, Spicy Apple and Ginger Spice Drops."),
 ("Package a GLP-1 ginger + turmeric support routine", "Retention", GLP1,
  "https://gingerpeople.com/boost-your-glp-1-naturally-the-power-of-ginger-turmeric/", SS(GLP1),
  "visual_findings.vf-glp1-no-routine", "visual", "job:GLP-1 side-effects; content_theme:GLP-1",
  "30-day repeat purchase rate (GLP-1 article visitors)", (6, 12), 68, "pattern / best-practice",
  "The GLP-1 article states nausea affects up to 50% of GLP-1 patients and recommends ginger/turmeric formats, but shoppers must assemble the routine themselves.",
  "Create a 'GLP-1 Ginger + Turmeric Daily Support Routine' merchandising chews, lozenges and turmeric juice with reorder guidance, placed in the article."),
 ("Add an 'add to my ginger routine' reorder path on PDPs", "Retention", PDP_CANDY,
  "https://gingerpeople.com/products/gin-gins-original-ginger-chews/", SS(PDP_CANDY),
  "visual_findings.vf-pdp-no-reorder", "visual", "family:GIN GINS; segment:functional-relief",
  "Repeat purchase / reorder-reminder opt-in rate", (5, 10), 72, "strong inference",
  "These are consumable products bought for ongoing relief, but there is no path to set a routine or reorder reminder, so repeat demand is left to memory.",
  "Add an 'Add to my ginger routine' opt-in on PDPs that emails reorder reminders and a retailer/online link for the chosen formats."),
 ("Create a Find-Your-Ginger need quiz", "Acquisition", PRODUCTS,
  "https://gingerpeople.com/the-ginger-people-products/", SS(PRODUCTS),
  "visual_findings.vf-products-clutter", "visual", "job:nausea; job:cooking",
  "Landing-page conversion rate", (10, 18), 72, "pattern / best-practice",
  "The catalog asks shoppers to decode product names instead of shopping their job; need language exists but is buried in dense grids.",
  "Create '/find-your-ginger/' with prompts (nausea, travel, cooking, daily wellness, candy) that route to a recommended family with proof and buy/find choices."),
 ("Create a morning-sickness ginger landing page", "Acquisition", GLP1,
  "https://gingerpeople.com/boost-your-glp-1-naturally-the-power-of-ginger-turmeric/", SS(GLP1),
  "visual_findings.vf-glp1-health-pattern", "visual", "job:morning sickness; content_theme:health blog",
  "Landing-page conversion rate", (10, 16), 70, "pattern / best-practice",
  "Morning-sickness intent is high-anxiety and disperses across blog, category and PDPs; the existing health-content pattern could anchor one compliant destination.",
  "Create '/morning-sickness-ginger/' mirroring the health-content layout with testimonials, FAQ, 'ask your clinician' language and Ginger Rescue / GIN GINS choices."),
 ("Replace the /cart 404 with a purchase-recovery page", "Performance", CART,
  "https://gingerpeople.com/cart", SS(CART),
  f"{CART}.network.responses[].status=404", "network", "segment:functional-relief; job:purchase-clarity",
  "/cart exit rate", (10, 20), 85, "direct structural absence",
  "The /cart URL returns a branded 404. Even for a retailer-routed brand it is a common destination for returning users, old links, tracking tools and partner referrals — so high-intent sessions silently die.",
  "Replace the /cart 404 with a purchase-recovery page: 'Continue shopping', 'Find a store', 'Shop online retailers' and support links."),
]

experiments = {"experiments": []}
for (title, pillar, sid, url, shot, sig, sigtype, ref, kpi, lift, conf, basis, hyp, change) in E:
    experiments["experiments"].append({
        "exp_id": exp_id(title, sid), "title": title, "pillar": pillar,
        "affected_surface": sid, "url": url,
        "evidence": {"screenshot": shot, "triggering_signal": sig, "signal_type": sigtype, "store_profile_ref": ref},
        "hypothesis": hyp, "primary_change": change, "primary_kpi": kpi,
        "decision_rule": f"Ship if {kpi} improves without hurting site-wide conversion or PDP engagement.",
        "expected_lift": {"low": lift[0], "high": lift[1], "unit": "%"},
        "confidence": conf, "confidence_basis": basis,
    })

leaks = {"leaks": [
    {"id": f"leak{i+1}", "pillar": e[1], "surface_id": e[2], "triggering_signal": e[5],
     "signal_type": e[6], "severity": "high" if e[10] >= 80 else "medium", "description": e[0]}
    for i, e in enumerate(E)
]}

competitors = {"niche": "ginger functional foods + candy", "competitors": [
    {"name": "Dramamine", "domain": "dramamine.com", "positioning": "OTC motion-sickness relief",
     "makes_easier": "Immediate use-case clarity for nausea/travel", "our_edge": "Natural ginger formats and candy/snack permission",
     "pattern_to_adapt": "Dedicated nausea/travel pages with product-choice modules", "source_url": "https://www.dramamine.com/"},
    {"name": "Tummydrops", "domain": "tummydrops.com", "positioning": "Ginger/peppermint drops for nausea & digestive comfort",
     "makes_easier": "Symptom-specific shopping", "our_edge": "Broader catalog, recipes, mainstream candy formats",
     "pattern_to_adapt": "Symptom-led navigation and format comparisons", "source_url": "https://www.tummydrops.com/"},
    {"name": "Reed's", "domain": "drinkreeds.com", "positioning": "Ginger beverages and ginger candy",
     "makes_easier": "Beverage-led discovery and retail familiarity", "our_edge": "Deeper ginger specialization and health education",
     "pattern_to_adapt": "Stronger retailer handoff per product family", "source_url": "https://drinkreeds.com/"},
    {"name": "Chimes Gourmet", "domain": "chimesgourmet.com", "positioning": "Ginger chews and candy variety",
     "makes_easier": "Simple flavor-led candy shopping", "our_edge": "Stronger functional use cases, reviews, recipes, family story",
     "pattern_to_adapt": "Flavor sampler and heat/flavor comparison", "source_url": "https://www.chimesgourmet.com/"},
]}

tech_checks = {"checks": [
    {"name": "SSL Certificate", "status": "Pass", "detail": "HTTPS storefront loaded successfully (200).", "grounded_in": "home.status confirms https 200 load"},
    {"name": "HTTPS Redirect", "status": "Pass", "detail": "Storefront resolves over HTTPS.", "grounded_in": "home.url resolves over https"},
    {"name": "Sitemap", "status": "Warn", "detail": "Not inspected in this browser-first crawl.", "grounded_in": "not inspected"},
    {"name": "Robots.txt", "status": "Warn", "detail": "Not inspected in this browser-first crawl.", "grounded_in": "not inspected"},
    {"name": "Critical Pages Loading", "status": "Warn", "detail": "Home, categories and PDPs loaded; /cart returned 404.", "grounded_in": f"{CART}.network.responses[].status=404"},
    {"name": "Meta Tags & Social Previews", "status": "Pass", "detail": "Page title and meta description present on homepage.", "grounded_in": "home.meta.title + home.meta.description"},
    {"name": "Structured Data", "status": "Pass", "detail": "JSON-LD structured data detected on homepage.", "grounded_in": "home.meta.jsonld"},
    {"name": "Favicon", "status": "Warn", "detail": "Not evaluated from captured evidence.", "grounded_in": "not inspected"},
    {"name": "Mobile-Friendly", "status": "Warn", "detail": "Desktop-only crawl.", "grounded_in": "not inspected"},
    {"name": "Page Speed Mobile", "status": "Warn", "detail": "No mobile Lighthouse run performed.", "grounded_in": "not inspected"},
    {"name": "Page Speed Desktop", "status": "Warn", "detail": "No Lighthouse run; navigation timing only.", "grounded_in": "not inspected"},
    {"name": "Broken Links", "status": "Fail", "detail": "/cart returned a branded 404.", "grounded_in": f"{CART}.network.responses[].status=404"},
    {"name": "Image Optimization", "status": "Warn", "detail": "Not byte-measured; PDPs use large visual assets.", "grounded_in": "not inspected"},
    {"name": "Cookie/Privacy", "status": "Warn", "detail": "Consent mechanics not inspected in this crawl.", "grounded_in": "not inspected"},
    {"name": "Checkout Reachable", "status": "Fail", "detail": "/cart unreachable (404); retailer-routed, no checkout entered.", "grounded_in": f"{CART}.network.responses[].status=404"},
]}

ids = [e["exp_id"] for e in experiments["experiments"]]
synthesis = {
    "headline": "Ginger People audit — the proof is strong; the buy path is the constraint",
    "themes": [
        {"title": "The purchase handoff is leaking demand",
         "summary": "Strong product proof (86 reviews, World's #1 selling ginger candy, 10% fresh ginger) but no buying box on PDPs, a broken Where To Buy, and a /cart 404 mean high-intent sessions have no clear next step.",
         "supporting_exp_ids": [ids[0], ids[1], ids[9]]},
        {"title": "A broad catalog asks shoppers to decode product names",
         "summary": "Homepage and grids lead with SKUs, not jobs; mission cards and a need quiz would route relief, candy, and cooking shoppers faster.",
         "supporting_exp_ids": [ids[2], ids[7]]},
        {"title": "The content moat is under-commercialized",
         "summary": "GLP-1 and health education can become reorderable routines and condition landing pages, and the format range supports kits and samplers.",
         "supporting_exp_ids": [ids[5], ids[8], ids[3], ids[4]]},
    ],
}

w("store_profile.json", store_profile)
w("visual_findings.json", visual_findings)
w("leaks.json", leaks)
w("experiments.json", experiments)
w("competitors.json", competitors)
w("tech_checks.json", tech_checks)
w("synthesis.json", synthesis)
print("wrote", ROOT / "reason", "(10 experiments, pillars:",
      sorted({e['pillar'] for e in experiments['experiments']}), ")")
