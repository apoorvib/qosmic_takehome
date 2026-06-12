#!/usr/bin/env python3
"""One-off authoring of the zenrojas reason/*.json (the SAMPLE deliverable, unseen store).

Encodes the audit content reasoned from artifacts/zenrojas/ (live crawl + screenshots Read).
zenrojas is direct-sell (prices + add-to-cart + working cart) — the opposite commerce model
to gingerpeople — so the leaks differ. Not part of the generalizable harness. Gate with validate.py.
"""
import hashlib, json
from pathlib import Path

STORE = "zenrojas"
ROOT = Path("artifacts/zenrojas")
SS = lambda sid, kind="fullpage": f"{sid}/screenshots/{sid}-{kind}.png"

HOME = "home"
COLL_TEAS = "collection-teas"
COLL_BEST = "collection-best-sellers"
PDP_SLEEP = "pdp-organicsleeptea"
PDP_HEART = "pdp-heartburntea"
PDP_SAMP = "pdp-looseleafsamplers"
CART = "cart"
FAQS = "content-faqs"
BLOG = "content-weekly-blog"


def w(name, obj):
    p = ROOT / "reason" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def exp_id(title, surface):
    return f"exp-{hashlib.sha1(f'{STORE}|{title}|{surface}'.encode()).hexdigest()[:12]}"


store_profile = {
    "store": "zenrojas.com", "niche": "premium organic loose-leaf tea",
    "commerce_model": "direct",
    "families": [
        {"name": "Functional teas", "type": "tea", "products": ["Organic Sleep Tea", "Heartburn Organic Tea", "Bodyguard Organic Tea"]},
        {"name": "Classic teas", "type": "tea", "products": ["Premium Sencha Green Tea", "Organic Black Tea"]},
        {"name": "Samplers", "type": "tea", "products": ["Tea Bag Samplers", "Loose Leaf Samplers"]},
        {"name": "Accessories", "type": "accessory", "products": ["Zen Rojas Mug", "Tea Infuser", "Tea Bags"]},
    ],
    "jobs_to_be_done": ["better sleep", "digestive relief/heartburn", "immunity", "daily ritual/relaxation", "gifting", "discovery/trying"],
    "segments": ["wellness-seeker", "tea-enthusiast", "gift-buyer", "ritual-seeker"],
    "proof_points": ["organic", "premium loose leaf", "Find Your Moment of Zen", "founder Jesse Rojas story", "free shipping on $50+"],
    "content_themes": ["tea education", "founder/blog", "ambassador program", "ritual"],
    "brand_voice": "calm, premium, mindful wellness",
}

visual_findings = {"findings": [
    {"id": "vf-intrusive-popup", "observation": "A full-screen email-capture popup ('Subscribe to get a reward now / REVEAL REWARD') overlays the hero on load across homepage and PDPs, blocking the first impression and the product.",
     "screenshot_ref": SS(HOME, "hero"), "region": "hero/overlay", "severity": "high", "pillar": "Conversion"},
    {"id": "vf-collection-no-benefit-filter", "observation": "Collection grids list teas by name with no benefit-led navigation (sleep / digestion / immunity), so shoppers must decode products instead of shopping their goal.",
     "screenshot_ref": SS(COLL_TEAS), "region": "grid", "severity": "medium", "pillar": "Conversion"},
    {"id": "vf-no-ritual-bundle", "observation": "Teas and accessories (mug, infuser, tea bags) are sold separately; no 'ritual kit' bundles tea with brewing accessories.",
     "screenshot_ref": SS(COLL_TEAS), "region": "grid", "severity": "medium", "pillar": "AOV"},
    {"id": "vf-pdp-no-crosssell", "observation": "PDP has no 'complete your ritual' cross-sell or sampler suggestion near the buy box.",
     "screenshot_ref": SS(PDP_SLEEP), "region": "buy-box", "severity": "medium", "pillar": "AOV"},
    {"id": "vf-pdp-no-subscription", "observation": "Consumable tea PDP offers a one-time add-to-cart only; no subscribe-and-save / refill option for a repeat-consumption product.",
     "screenshot_ref": SS(PDP_SLEEP), "region": "buy-box", "severity": "medium", "pillar": "Retention"},
    {"id": "vf-ambassador-buried", "observation": "The Ambassador Program (a referral/loyalty asset) is buried in the footer and never surfaced at purchase or post-purchase moments.",
     "screenshot_ref": SS(HOME), "region": "footer", "severity": "low", "pillar": "Retention"},
    {"id": "vf-blog-uncommercialized", "observation": "Functional benefits (sleep, heartburn, immunity) live in product copy and blog but have no dedicated intent landing pages to capture search demand.",
     "screenshot_ref": SS(BLOG), "region": "article-list", "severity": "medium", "pillar": "Acquisition"},
    {"id": "vf-founder-uncommercialized", "observation": "Strong founder/family story content (Jesse Rojas) is not connected to product modules or a brand-story shopping path.",
     "screenshot_ref": SS(BLOG), "region": "article-list", "severity": "low", "pillar": "Acquisition"},
    {"id": "vf-perf-heavy", "observation": "Pages fire 200+ requests with ~20 console errors (failed shop.app third-party scripts); the best-sellers collection took ~10s to load in capture.",
     "screenshot_ref": SS(COLL_BEST), "region": "page", "severity": "high", "pillar": "Performance"},
]}

E = [
 ("Trigger the email popup on exit-intent instead of blocking the hero on load", "Conversion", HOME,
  "https://zenrojas.com/", SS(HOME, "hero"),
  "visual_findings.vf-intrusive-popup", "visual", "segment:wellness-seeker; ritual",
  "Bounce rate / homepage engagement", (5, 12), 78, "strong inference",
  "A full-screen subscribe popup overlays the hero on load across the homepage and PDPs, taxing the first impression before a visitor sees the product or value proposition.",
  "Switch the email popup to fire on exit-intent or after ~20s/scroll, and keep the reward offer; never overlay the hero on first load."),
 ("Add visible social proof and trust badges to PDPs", "Conversion", PDP_SLEEP,
  "https://zenrojas.com/products/organicsleeptea", SS(PDP_SLEEP),
  f"{PDP_SLEEP}.cro_signals.trust_badges.present=false", "cro_signals", "proof:organic; segment:wellness-seeker",
  "Add-to-cart / PDP conversion rate", (8, 15), 82, "direct structural absence",
  "The Organic Sleep Tea PDP has a review widget but no visible review count, rating, organic-certification badge, or guarantee near the buy box, so a premium-priced product lacks reassurance at the decision point.",
  "Surface star rating + review count, an organic/quality badge, and a satisfaction guarantee directly under the price and add-to-cart."),
 ("Add benefit-led navigation to collections", "Conversion", COLL_TEAS,
  "https://zenrojas.com/collections/teas", SS(COLL_TEAS),
  "visual_findings.vf-collection-no-benefit-filter", "visual", "job:better sleep; job:digestive relief/heartburn",
  "Collection click-through to PDP", (6, 12), 74, "strong inference",
  "Collections list teas by name with no benefit filters, asking shoppers to decode products rather than shop their goal (sleep, digestion, immunity).",
  "Add benefit chips/filters ('For sleep', 'For digestion', 'For immunity', 'Daily ritual') and benefit-led section headers to the collection."),
 ("Launch a tea + accessory ritual bundle", "AOV", COLL_TEAS,
  "https://zenrojas.com/collections/teas", SS(COLL_TEAS),
  "visual_findings.vf-no-ritual-bundle", "visual", "family:Accessories; ritual",
  "Average order value", (8, 16), 71, "pattern / best-practice",
  "Teas and accessories (mug, infuser, tea bags) are sold separately; the brand's 'ritual' positioning is a natural fit for a starter kit that lifts basket size.",
  "Create a 'Zen Ritual Starter Kit' bundling a featured tea + mug + infuser at a modest bundle discount, merchandised on home and collections."),
 ("Add 'complete your ritual' cross-sell to PDPs", "AOV", PDP_SLEEP,
  "https://zenrojas.com/products/organicsleeptea", SS(PDP_SLEEP),
  "visual_findings.vf-pdp-no-crosssell", "visual", "family:Samplers; family:Accessories",
  "Average order value / units per order", (6, 12), 71, "pattern / best-practice",
  "The PDP has no cross-sell near the buy box, missing the obvious accessory and sampler attach for a ritual product.",
  "Add a 'Complete your ritual' module under add-to-cart suggesting an infuser, mug, or a complementary sampler."),
 ("Offer subscribe-and-save on consumable teas", "Retention", PDP_SLEEP,
  "https://zenrojas.com/products/organicsleeptea", SS(PDP_SLEEP),
  "visual_findings.vf-pdp-no-subscription", "visual", "job:daily ritual/relaxation; segment:wellness-seeker",
  "Subscription opt-in rate / repeat purchase rate", (7, 14), 74, "strong inference",
  "Tea is a repeat-consumption ritual product, but PDPs offer only one-time purchase, leaving recurring revenue and retention on the table.",
  "Add a subscribe-and-save option (e.g. 10% off, monthly/bi-monthly) to consumable tea PDPs with easy management."),
 ("Surface the Ambassador / loyalty program at key moments", "Retention", HOME,
  "https://zenrojas.com/", SS(HOME),
  "visual_findings.vf-ambassador-buried", "visual", "content_theme:ambassador program; segment:tea-enthusiast",
  "Referral / repeat-customer rate", (4, 9), 68, "pattern / best-practice",
  "The Ambassador Program is buried in the footer and never surfaced at purchase or post-purchase, so an existing loyalty asset goes unused.",
  "Promote the Ambassador Program in the post-purchase flow, account area, and a homepage band, with a clear reward and share path."),
 ("Build functional intent landing pages", "Acquisition", BLOG,
  "https://zenrojas.com/blogs/weekly-blog", SS(BLOG),
  "visual_findings.vf-blog-uncommercialized", "visual", "job:better sleep; job:immunity",
  "Organic landing-page sessions and conversion", (10, 20), 71, "pattern / best-practice",
  "High-intent functional searches ('best organic tea for sleep', 'tea for heartburn') have no dedicated landing pages; the benefit content is buried in product copy and blog posts.",
  "Create benefit landing pages (sleep, digestion, immunity) with the relevant teas, proof, FAQs and internal links from blog content."),
 ("Commercialize the founder and education content", "Acquisition", BLOG,
  "https://zenrojas.com/blogs/weekly-blog", SS(BLOG),
  "visual_findings.vf-founder-uncommercialized", "visual", "proof:founder Jesse Rojas story; content_theme:tea education",
  "Content-attributed sessions to PDP", (5, 10), 70, "pattern / best-practice",
  "The founder/family story and tea-education content build trust but do not route readers to products or a brand-story shopping path.",
  "Add product modules and 'shop the story' CTAs into the founder post and education articles, linking to relevant teas and samplers."),
 ("Reduce page weight and failed third-party scripts", "Performance", COLL_BEST,
  "https://zenrojas.com/collections/best-sellers", SS(COLL_BEST),
  "visual_findings.vf-perf-heavy", "visual", "segment:wellness-seeker; ritual",
  "Page load time (LCP) and bounce", (8, 18), 78, "strong inference",
  "Pages fire 200+ requests with ~20 console errors from failed third-party (shop.app) scripts, and the best-sellers collection took ~10s to load in capture — a real speed and reliability drag on conversion.",
  "Audit and lazy-load imagery, defer/remove failing third-party scripts, and compress hero/product images to cut requests and load time."),
]

experiments = {"experiments": []}
for (title, pillar, sid, url, shot, sig, sigtype, ref, kpi, lift, conf, basis, hyp, change) in E:
    experiments["experiments"].append({
        "exp_id": exp_id(title, sid), "title": title, "pillar": pillar,
        "affected_surface": sid, "url": url,
        "evidence": {"screenshot": shot, "triggering_signal": sig, "signal_type": sigtype, "store_profile_ref": ref},
        "hypothesis": hyp, "primary_change": change, "primary_kpi": kpi,
        "decision_rule": f"Ship if {kpi} improves without hurting site-wide conversion.",
        "expected_lift": {"low": lift[0], "high": lift[1], "unit": "%"},
        "confidence": conf, "confidence_basis": basis,
    })

leaks = {"leaks": [
    {"id": f"leak{i+1}", "pillar": e[1], "surface_id": e[2], "triggering_signal": e[5],
     "signal_type": e[6], "severity": "high" if e[10] >= 80 else "medium", "description": e[0]}
    for i, e in enumerate(E)
]}

competitors = {"niche": "premium organic wellness tea", "competitors": [
    {"name": "Pukka Herbs", "domain": "pukkaherbs.com", "positioning": "Organic herbal wellness teas",
     "makes_easier": "Benefit-led navigation (sleep, detox, energy)", "our_edge": "Loose-leaf premium ritual + founder story",
     "pattern_to_adapt": "Benefit-first collection navigation and clear functional outcomes", "source_url": "https://www.pukkaherbs.com/"},
    {"name": "Traditional Medicinals", "domain": "traditionalmedicinals.com", "positioning": "Wellness teas with specific functional uses",
     "makes_easier": "Condition-specific product discovery", "our_edge": "Premium loose-leaf and a curated ritual experience",
     "pattern_to_adapt": "Symptom/benefit landing pages with proof", "source_url": "https://www.traditionalmedicinals.com/"},
    {"name": "Vahdam Teas", "domain": "vahdam.com", "positioning": "Premium Indian-origin teas, direct-to-consumer",
     "makes_easier": "Subscriptions, bundles, strong reviews/social proof", "our_edge": "Tighter functional ritual focus and brand story",
     "pattern_to_adapt": "Subscribe-and-save, gift bundles, prominent ratings", "source_url": "https://www.vahdam.com/"},
    {"name": "Art of Tea", "domain": "artoftea.com", "positioning": "Premium loose-leaf tea and accessories",
     "makes_easier": "Tea + accessory bundles and starter kits", "our_edge": "Functional wellness positioning and founder narrative",
     "pattern_to_adapt": "Ritual starter kits pairing tea with brewing accessories", "source_url": "https://www.artoftea.com/"},
]}

tech_checks = {"checks": [
    {"name": "SSL Certificate", "status": "Pass", "detail": "HTTPS storefront with security headers present.", "grounded_in": "home.network.security_headers"},
    {"name": "HTTPS Redirect", "status": "Pass", "detail": "Storefront resolves over HTTPS.", "grounded_in": "home.url resolves over https"},
    {"name": "Sitemap", "status": "Warn", "detail": "Not inspected in this browser-first crawl.", "grounded_in": "not inspected"},
    {"name": "Robots.txt", "status": "Warn", "detail": "Not inspected in this browser-first crawl.", "grounded_in": "not inspected"},
    {"name": "Critical Pages Loading", "status": "Pass", "detail": "Home, collections, PDPs and cart all returned 200.", "grounded_in": "home.status all critical pages 200"},
    {"name": "Meta Tags & Social Previews", "status": "Pass", "detail": "Title and meta description present on homepage.", "grounded_in": "home.meta.title"},
    {"name": "Structured Data", "status": "Fail", "detail": "No JSON-LD structured data detected on homepage.", "grounded_in": "home.meta.jsonld is empty"},
    {"name": "Favicon", "status": "Warn", "detail": "Not evaluated from captured evidence.", "grounded_in": "not inspected"},
    {"name": "Mobile-Friendly", "status": "Warn", "detail": "Desktop-only crawl.", "grounded_in": "not inspected"},
    {"name": "Page Speed Mobile", "status": "Warn", "detail": "No mobile Lighthouse run performed.", "grounded_in": "not inspected"},
    {"name": "Page Speed Desktop", "status": "Warn", "detail": "No Lighthouse run; best-sellers collection took ~10s in capture.", "grounded_in": "not inspected"},
    {"name": "Broken Links", "status": "Warn", "detail": "No 4xx among inspected surfaces; not exhaustively crawled.", "grounded_in": "not inspected"},
    {"name": "Image Optimization", "status": "Warn", "detail": "Not byte-measured; 200+ requests/page observed.", "grounded_in": "not inspected"},
    {"name": "Cookie/Privacy", "status": "Warn", "detail": "Consent mechanics not inspected.", "grounded_in": "not inspected"},
    {"name": "Checkout Reachable", "status": "Pass", "detail": "Cart reachable (200); checkout not entered (safety).", "grounded_in": "cart.status"},
]}

ids = [e["exp_id"] for e in experiments["experiments"]]
synthesis = {
    "headline": "Zen Rojas audit — premium tea, but the path from intent to ritual leaks",
    "themes": [
        {"title": "The first impression fights the shopper",
         "summary": "A full-screen email popup blocks the hero on load and PDPs lack visible social proof, so a premium-priced catalog loses trust and momentum at the decision point.",
         "supporting_exp_ids": [ids[0], ids[1]]},
        {"title": "The ritual positioning is under-monetized",
         "summary": "Tea, accessories and samplers are sold separately with no bundles, cross-sell, or subscribe-and-save — leaving basket size and recurring revenue on the table.",
         "supporting_exp_ids": [ids[3], ids[4], ids[5]]},
        {"title": "Functional demand and content go uncaptured",
         "summary": "Benefit-led navigation, intent landing pages, and commercialized founder/education content would convert search and story into shopping; meanwhile page weight drags speed.",
         "supporting_exp_ids": [ids[2], ids[7], ids[8], ids[9]]},
    ],
}

w("store_profile.json", store_profile)
w("visual_findings.json", visual_findings)
w("leaks.json", leaks)
w("experiments.json", experiments)
w("competitors.json", competitors)
w("tech_checks.json", tech_checks)
w("synthesis.json", synthesis)
print("wrote", ROOT / "reason", "pillars:", sorted({e['pillar'] for e in experiments['experiments']}))
