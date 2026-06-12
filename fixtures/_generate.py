#!/usr/bin/env python3
"""Deterministic generator for the Step-0 eval fixtures.

Produces two store artifact trees that Module 2 (eval) develops against without
needing a real crawl:

  fixtures/sample_store/         a complete, schema-valid PASSING mini-audit
  fixtures/sample_store_broken/  a twin with injected faults exercising every
                                 key failure class (see FAULTS below)

Path convention (frozen): every path inside reason JSON / page.json is RELATIVE
TO THE STORE ROOT (e.g. "pdp-gingins/screenshots/gingins-fullpage.png").
validate.py / score_report.py are invoked with the store root as base dir, so
fixtures and real artifacts/<store>/ are structurally identical.

triggering_signal conventions (frozen):
  cro_signals : "<surface_id>.cro_signals.<key>.present=<bool>"
  network     : "<surface_id>.network.responses[].status=<code>"
  visual      : "visual_findings.<finding_id>"

Run:  python fixtures/_generate.py
Requires: Pillow (screenshots). Stdlib otherwise.
"""
import json, os, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PASS = ROOT / "sample_store"
BROKEN = ROOT / "sample_store_broken"

try:
    from PIL import Image, ImageDraw
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False


# ---------------------------------------------------------------- helpers
def w(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def png(path: Path, label: str, h: int = 600):
    path.parent.mkdir(parents=True, exist_ok=True)
    if HAVE_PIL:
        img = Image.new("RGB", (800, h), (243, 238, 230))
        d = ImageDraw.Draw(img)
        d.rectangle([8, 8, 792, h - 8], outline=(140, 90, 40), width=3)
        d.text((24, 24), "FIXTURE SCREENSHOT", fill=(140, 90, 40))
        for i, line in enumerate(label.split("\n")):
            d.text((24, 60 + i * 22), line, fill=(40, 40, 40))
        img.save(path)
    else:  # fallback: 1x1 valid PNG so mechanical path checks still pass
        path.write_bytes(bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
            "890000000a49444154789c6300010000050001a5f645400000000049454e44ae426082"))


def signal(present, **extra):
    s = {"present": present}
    s.update(extra)
    return s


# ---------------------------------------------------------------- crawl artifacts
SURFACES = [
    ("home", "homepage", "https://sample-ginger-co.example/", 200),
    ("pdp-gingins", "product", "https://sample-ginger-co.example/products/gin-gins-original/", 200),
    ("collection-candy", "collection", "https://sample-ginger-co.example/collections/candy/", 200),
    ("cart", "cart", "https://sample-ginger-co.example/cart", 404),
    ("where-to-buy", "content", "https://sample-ginger-co.example/where-to-buy/", 200),
    ("content-glp1", "content", "https://sample-ginger-co.example/blog/glp-1-ginger/", 200),
]

SEC_HEADERS = {"strict-transport-security": "max-age=31536000", "content-security-policy": "default-src 'self'"}


def page_json(sid, stype, url, status):
    base = {
        "url": url, "type": stype, "status": status,
        "meta": {
            "title": f"{sid} | Sample Ginger Co",
            "description": "Ginger candy and natural nausea relief.",
            "og": {"og:title": "Sample Ginger Co"},
            "viewport": "width=device-width, initial-scale=1",
            "jsonld": [],
        },
        "elements": [],
        "cro_signals": {},
        "text_blocks": [{"role": "h1", "text": sid}],
        "content": "",
        "screenshots": [f"{sid}/screenshots/{sid}-fullpage.png"],
        "network": {
            "nav_timing_ms": 1800, "requests": 70, "transfer_kb": 4200,
            "redirects": [{"from": url.replace("https", "http"), "to": url, "status": 301}],
            "security_headers": SEC_HEADERS,
            "responses": [{"url": url, "status": status}],
        },
        "console_errors": [],
    }

    full = signal(False)
    if sid == "home":
        base["cro_signals"] = {
            "price": signal(False), "add_to_cart": signal(False), "reviews": signal(False),
            "trust_badges": signal(True, items=["America's #1 selling ginger candy"]),
            "search": signal(True), "promo_bar": signal(True),
            "primary_cta": signal(True, text="SHOP NOW"),
        }
        base["content"] = ("Sample Ginger Co — ginger candy, lozenges and juice. Settle your stomach, "
                           "calm motion sickness, cook with real ginger. America's #1 selling ginger candy.")
        base["screenshots"].append("home/screenshots/home-hero.png")
    elif sid == "pdp-gingins":
        base["cro_signals"] = {
            "price": signal(False), "add_to_cart": signal(False),
            "reviews": signal(True, value="86 reviews"),
            "trust_badges": signal(True, items=["America's #1 selling ginger candy", "award-winning"]),
            "search": signal(True), "promo_bar": signal(True),
            "primary_cta": signal(True, text="Buy online or find it in store"),
        }
        base["content"] = ("GIN GINS Original Ginger Chews — 10% fresh ginger, individually wrapped. "
                           "Great for nausea, motion sickness and morning sickness. 86 reviews.")
        base["screenshots"].append("pdp-gingins/screenshots/pdp-gingins-hero.png")
    elif sid == "collection-candy":
        base["cro_signals"] = {
            "price": signal(True), "add_to_cart": signal(False), "reviews": signal(False),
            "trust_badges": signal(False), "search": signal(True), "promo_bar": signal(True),
            "primary_cta": signal(True, text="VIEW PRODUCT"),
        }
        base["content"] = ("GIN GINS candy: Original, Mandarin Orange, Lemon. Ginger Rescue lozenges and "
                           "chewable tablets for travel and motion sickness. Nine flavors, no sampler.")
        base["screenshots"].append("collection-candy/screenshots/collection-candy-hero.png")
    elif sid == "cart":
        base["cro_signals"] = {k: signal(False) for k in
                               ["price", "add_to_cart", "reviews", "trust_badges", "search", "promo_bar", "primary_cta"]}
        base["content"] = "Page not found."
        base["network"]["responses"] = [{"url": url, "status": 404}]
    elif sid == "where-to-buy":
        base["cro_signals"] = {
            "price": signal(False), "add_to_cart": signal(False), "reviews": signal(False),
            "trust_badges": signal(False), "search": signal(True), "promo_bar": signal(True),
            "primary_cta": signal(False),
        }
        base["content"] = ("Where to buy: blog cards and footer links only. No store locator, no retailer "
                           "list, no online buying cards.")
    elif sid == "content-glp1":
        base["cro_signals"] = {
            "price": signal(False), "add_to_cart": signal(False), "reviews": signal(False),
            "trust_badges": signal(False), "search": signal(True), "promo_bar": signal(True),
            "primary_cta": signal(False),
        }
        base["content"] = ("Boost your GLP-1 naturally. Nausea affects up to 50% of patients on GLP-1 "
                           "medications; ginger and turmeric formats can help. No reorderable routine offered.")
    return base


def build_crawl(store_root: Path):
    surfaces = []
    for sid, stype, url, status in SURFACES:
        pj = page_json(sid, stype, url, status)
        w(store_root / sid / "page.json", pj)
        for shot in pj["screenshots"]:
            png(store_root / shot, f"{sid}\n{Path(shot).name}", h=600 if "fullpage" in shot else 300)
        surfaces.append({"id": sid, "type": stype, "url": url, "status": status, "page_json": f"{sid}/page.json"})
    w(store_root / "manifest.json", {"store": "sample-ginger-co", "crawled_at": "2026-06-12T00:00:00Z",
                                     "surfaces": surfaces})


# ---------------------------------------------------------------- reason artifacts
STORE_PROFILE = {
    "store": "sample-ginger-co", "niche": "ginger functional foods + candy",
    "commerce_model": "retailer-routed",
    "families": [
        {"name": "GIN GINS", "type": "candy", "products": ["Original", "Mandarin Orange", "Lemon"]},
        {"name": "Ginger Rescue", "type": "lozenges/tablets", "products": ["Extra Strength Lozenges", "Chewable Tablets"]},
        {"name": "Ginger Juice", "type": "juice", "products": ["Original Juice", "Turmeric Juice"]},
    ],
    "jobs_to_be_done": ["nausea", "travel/motion-sickness", "GLP-1 side-effects", "morning sickness", "cooking"],
    "segments": ["functional-relief", "candy-snacker", "cook", "wholesale"],
    "proof_points": ["86 reviews", "America's #1 selling ginger candy", "10% fresh ginger", "award-winning"],
    "content_themes": ["recipes", "health education", "GLP-1", "where-to-buy"],
    "brand_voice": "warm, health-forward family brand",
}

VISUAL_FINDINGS = {"findings": [
    {"id": "vf-home-single-cta", "observation": "Single broad 'SHOP NOW' CTA above the fold; no mission routing for distinct buyer needs.",
     "screenshot_ref": "home/screenshots/home-hero.png", "region": "hero/above-fold", "severity": "medium", "pillar": "Conversion"},
    {"id": "vf-home-no-need-routing", "observation": "Need language (nausea, travel, cooking) absent from hero; visitors not routed by job-to-be-done.",
     "screenshot_ref": "home/screenshots/home-fullpage.png", "region": "hero", "severity": "medium", "pillar": "Acquisition"},
    {"id": "vf-collection-no-bundle", "observation": "Ginger Rescue formats shown as separate tiles; no travel/kit bundle entry point.",
     "screenshot_ref": "collection-candy/screenshots/collection-candy-fullpage.png", "region": "grid", "severity": "medium", "pillar": "AOV"},
    {"id": "vf-collection-no-sampler", "observation": "Nine GIN GINS flavors listed with no multi-flavor sampler/trial option.",
     "screenshot_ref": "collection-candy/screenshots/collection-candy-hero.png", "region": "grid", "severity": "medium", "pillar": "AOV"},
    {"id": "vf-pdp-no-reorder", "observation": "PDP has no subscribe-and-save or reorder control for a consumable product.",
     "screenshot_ref": "pdp-gingins/screenshots/pdp-gingins-fullpage.png", "region": "buy-box", "severity": "medium", "pillar": "Retention"},
    {"id": "vf-glp1-no-routine", "observation": "GLP-1 article educates but offers no packaged, reorderable ginger+turmeric routine.",
     "screenshot_ref": "content-glp1/screenshots/content-glp1-fullpage.png", "region": "article-body", "severity": "medium", "pillar": "Retention"},
    {"id": "vf-content-health-pattern", "observation": "Health-content layout (testimonials + FAQ) exists and could anchor a condition landing page.",
     "screenshot_ref": "content-glp1/screenshots/content-glp1-fullpage.png", "region": "article-body", "severity": "low", "pillar": "Acquisition"},
]}

# exp_id, title, pillar, surface_id, url, screenshot, signal, signal_type, profile_ref, kpi, lift(lo,hi), conf, basis
EXPERIMENTS_SPEC = [
    ("exp-1a2b3c4d5e6f", "Add a buying box to every product", "Conversion", "pdp-gingins",
     "https://sample-ginger-co.example/products/gin-gins-original/", "pdp-gingins/screenshots/pdp-gingins-fullpage.png",
     "pdp-gingins.cro_signals.add_to_cart.present=false", "cro_signals", "family:GIN GINS; job:purchase-clarity",
     "Outbound retailer click rate", (12, 20), 82, "direct structural absence"),
    ("exp-2b3c4d5e6f70", "Rebuild the Where To Buy page into a purchase handoff", "Conversion", "where-to-buy",
     "https://sample-ginger-co.example/where-to-buy/", "where-to-buy/screenshots/where-to-buy-fullpage.png",
     "where-to-buy.cro_signals.primary_cta.present=false", "cro_signals", "content_theme:where-to-buy; job:purchase-clarity",
     "Outbound retailer click rate", (15, 25), 83, "direct structural absence"),
    ("exp-3c4d5e6f7081", "Turn the homepage into shopper-mission cards", "Conversion", "home",
     "https://sample-ginger-co.example/", "home/screenshots/home-hero.png",
     "visual_findings.vf-home-single-cta", "visual", "segment:candy-snacker; job:nausea",
     "Homepage click-through to category", (6, 10), 72, "strong inference"),
    ("exp-4d5e6f708192", "Sell a travel nausea kit from the Ginger Rescue formats", "AOV", "collection-candy",
     "https://sample-ginger-co.example/collections/candy/", "collection-candy/screenshots/collection-candy-fullpage.png",
     "visual_findings.vf-collection-no-bundle", "visual", "family:Ginger Rescue; job:travel/motion-sickness",
     "AOV among Ginger Rescue visitors", (8, 14), 72, "strong inference"),
    ("exp-5e6f708192a3", "Build a GIN GINS flavor sampler pack", "AOV", "collection-candy",
     "https://sample-ginger-co.example/collections/candy/", "collection-candy/screenshots/collection-candy-hero.png",
     "visual_findings.vf-collection-no-sampler", "visual", "family:GIN GINS; segment:candy-snacker",
     "AOV (first-time candy shoppers)", (7, 12), 71, "strong inference"),
    ("exp-6f708192a3b4", "Package a GLP-1 ginger + turmeric support routine", "Retention", "content-glp1",
     "https://sample-ginger-co.example/blog/glp-1-ginger/", "content-glp1/screenshots/content-glp1-fullpage.png",
     "visual_findings.vf-glp1-no-routine", "visual", "job:GLP-1 side-effects; content_theme:GLP-1",
     "30-day repeat purchase rate (GLP-1 visitors)", (6, 12), 68, "pattern / best-practice"),
    ("exp-708192a3b4c5", "Add subscribe-and-save reorder to consumable PDPs", "Retention", "pdp-gingins",
     "https://sample-ginger-co.example/products/gin-gins-original/", "pdp-gingins/screenshots/pdp-gingins-fullpage.png",
     "visual_findings.vf-pdp-no-reorder", "visual", "segment:functional-relief; job:nausea",
     "Repeat purchase rate (PDP buyers)", (5, 10), 70, "strong inference"),
    ("exp-8192a3b4c5d6", "Create a Find-Your-Ginger need quiz", "Acquisition", "home",
     "https://sample-ginger-co.example/", "home/screenshots/home-fullpage.png",
     "visual_findings.vf-home-no-need-routing", "visual", "job:nausea; job:travel/motion-sickness",
     "Landing-page conversion rate", (10, 18), 72, "pattern / best-practice"),
    ("exp-92a3b4c5d6e7", "Create a morning-sickness ginger landing page", "Acquisition", "content-glp1",
     "https://sample-ginger-co.example/blog/glp-1-ginger/", "content-glp1/screenshots/content-glp1-fullpage.png",
     "visual_findings.vf-content-health-pattern", "visual", "job:morning sickness; content_theme:health education",
     "Landing-page conversion rate", (10, 16), 70, "pattern / best-practice"),
    ("exp-a3b4c5d6e7f8", "Replace the /cart 404 with a purchase-recovery page", "Performance", "cart",
     "https://sample-ginger-co.example/cart", "cart/screenshots/cart-fullpage.png",
     "cart.network.responses[].status=404", "network", "segment:functional-relief; job:purchase-clarity",
     "/cart exit rate", (10, 20), 85, "direct structural absence"),
]


def make_experiment(spec):
    (xid, title, pillar, sid, url, shot, sig, sigtype, ref, kpi, lift, conf, basis) = spec
    return {
        "exp_id": xid, "title": title, "pillar": pillar, "affected_surface": f"{sid} surface",
        "url": url,
        "evidence": {"screenshot": shot, "triggering_signal": sig, "signal_type": sigtype, "store_profile_ref": ref},
        "hypothesis": f"{title}: this addresses a leak grounded in {sig}.",
        "primary_change": title,
        "primary_kpi": kpi,
        "decision_rule": f"Ship if {kpi} improves without hurting site-wide conversion.",
        "expected_lift": {"low": lift[0], "high": lift[1], "unit": "%"},
        "confidence": conf, "confidence_basis": basis,
    }


def make_leaks():
    leaks = []
    for i, spec in enumerate(EXPERIMENTS_SPEC, 1):
        (xid, title, pillar, sid, url, shot, sig, sigtype, ref, kpi, lift, conf, basis) = spec
        leaks.append({"id": f"leak{i}", "pillar": pillar, "surface_id": sid, "triggering_signal": sig,
                      "signal_type": sigtype, "severity": "high" if conf >= 80 else "medium",
                      "description": title})
    return {"leaks": leaks}


COMPETITORS = {"niche": "ginger functional foods + candy", "competitors": [
    {"name": "Dramamine", "domain": "dramamine.com", "positioning": "OTC motion sickness relief",
     "makes_easier": "Immediate use-case clarity", "our_edge": "Natural ginger formats and candy permission",
     "pattern_to_adapt": "Dedicated nausea/travel pages with product-choice modules", "source_url": "https://www.dramamine.com/"},
    {"name": "Tummydrops", "domain": "tummydrops.com", "positioning": "Ginger/peppermint drops for nausea",
     "makes_easier": "Symptom-specific shopping", "our_edge": "Broader catalog, recipes, mainstream candy",
     "pattern_to_adapt": "Symptom-led navigation and format comparisons", "source_url": "https://tummydrops.com/"},
    {"name": "Reed's", "domain": "drinkreeds.com", "positioning": "Ginger beverages and candy",
     "makes_easier": "Beverage-led discovery", "our_edge": "Deeper ginger specialization and health education",
     "pattern_to_adapt": "Stronger retailer handoff per product family", "source_url": "https://drinkreeds.com/"},
    {"name": "Chimes Gourmet", "domain": "chimesgourmet.com", "positioning": "Ginger chews and candy variety",
     "makes_easier": "Simple flavor-led candy shopping", "our_edge": "Stronger functional use cases and reviews",
     "pattern_to_adapt": "Flavor sampler and heat/flavor comparison", "source_url": "https://www.chimesgourmet.com/"},
]}

TECH_CHECKS = {"checks": [
    {"name": "SSL Certificate", "status": "Pass", "detail": "HTTPS storefront loaded.", "grounded_in": "home.network.security_headers"},
    {"name": "HTTPS Redirect", "status": "Pass", "detail": "HTTP redirected to HTTPS (301).", "grounded_in": "home.network.redirects"},
    {"name": "Sitemap", "status": "Warn", "detail": "Not inspected in this crawl.", "grounded_in": "not inspected"},
    {"name": "Robots.txt", "status": "Warn", "detail": "Not inspected in this crawl.", "grounded_in": "not inspected"},
    {"name": "Critical Pages Loading", "status": "Warn", "detail": "Home/collection 200; /cart 404.", "grounded_in": "cart.network.responses[].status=404"},
    {"name": "Meta Tags & Social Previews", "status": "Pass", "detail": "Title and description present.", "grounded_in": "home.meta.title"},
    {"name": "Structured Data", "status": "Warn", "detail": "No JSON-LD detected.", "grounded_in": "home.meta.jsonld (empty)"},
    {"name": "Favicon", "status": "Warn", "detail": "Not evaluated from captured evidence.", "grounded_in": "not inspected"},
    {"name": "Mobile-Friendly", "status": "Warn", "detail": "Desktop-only crawl.", "grounded_in": "not inspected"},
    {"name": "Page Speed Mobile", "status": "Warn", "detail": "No mobile speed run performed.", "grounded_in": "not inspected"},
    {"name": "Page Speed Desktop", "status": "Warn", "detail": "No Lighthouse run; nav timing only.", "grounded_in": "not inspected"},
    {"name": "Broken Links", "status": "Fail", "detail": "/cart returned 404.", "grounded_in": "cart.network.responses[].status=404"},
    {"name": "Image Optimization", "status": "Warn", "detail": "Not measured.", "grounded_in": "not inspected"},
    {"name": "Cookie/Privacy", "status": "Warn", "detail": "Privacy link in footer; consent not inspected.", "grounded_in": "not inspected"},
    {"name": "Checkout Reachable", "status": "Fail", "detail": "/cart unreachable (404); no checkout entered.", "grounded_in": "cart.network.responses[].status=404"},
]}

SYNTHESIS = {"headline": "Sample Ginger Co audit — the buy path is the constraint", "themes": [
    {"title": "The purchase handoff is leaking demand",
     "summary": "Strong product proof but no buying box on PDPs, an empty Where To Buy, and a /cart 404.",
     "supporting_exp_ids": ["exp-1a2b3c4d5e6f", "exp-2b3c4d5e6f70", "exp-a3b4c5d6e7f8"]},
    {"title": "The content moat is under-commercialized",
     "summary": "GLP-1 and health content can become reorderable routines and condition landing pages.",
     "supporting_exp_ids": ["exp-6f708192a3b4", "exp-92a3b4c5d6e7", "exp-8192a3b4c5d6"]},
]}


def build_reason_pass(store_root: Path):
    w(store_root / "reason" / "store_profile.json", STORE_PROFILE)
    w(store_root / "reason" / "visual_findings.json", VISUAL_FINDINGS)
    w(store_root / "reason" / "leaks.json", make_leaks())
    w(store_root / "reason" / "experiments.json", {"experiments": [make_experiment(s) for s in EXPERIMENTS_SPEC]})
    w(store_root / "reason" / "competitors.json", COMPETITORS)
    w(store_root / "reason" / "tech_checks.json", TECH_CHECKS)
    w(store_root / "reason" / "synthesis.json", SYNTHESIS)


# ---------------------------------------------------------------- broken fixture
# FAULTS injected (each must be caught by validate.py / score_report.py):
#   F1 count        : 9 experiments (Performance exp removed)
#   F2 pillar-gap   : Performance pillar now absent
#   F3 screenshot   : experiments[0].evidence.screenshot -> missing file
#   F4 tech-truth   : Sitemap row flipped to Pass with unresolvable grounded_in
#   F5 specificity  : experiments[2] is generic; store_profile_ref overlaps nothing
#   F6 confidence   : experiments[1].confidence=95 with basis "pattern / best-practice" (band 65-72)
#   F7 bad-signal   : experiments[3].evidence.triggering_signal -> nonexistent visual finding
def build_reason_broken(store_root: Path):
    exps = [make_experiment(s) for s in EXPERIMENTS_SPEC]
    exps = exps[:9]                                                   # F1 + F2 (drops Performance)
    exps[0]["evidence"]["screenshot"] = "pdp-gingins/screenshots/MISSING.png"   # F3
    exps[1]["confidence"] = 95                                        # F6
    exps[3]["evidence"]["triggering_signal"] = "visual_findings.vf-does-not-exist"  # F7
    exps[2] = {                                                       # F5 generic / no specificity overlap
        "exp_id": "exp-3c4d5e6f7081", "title": "Add urgency banners and countdown timers",
        "pillar": "Conversion", "affected_surface": "site-wide", "url": "https://sample-ginger-co.example/",
        "evidence": {"screenshot": "home/screenshots/home-hero.png",
                     "triggering_signal": "visual_findings.vf-home-single-cta", "signal_type": "visual",
                     "store_profile_ref": "best-practice:urgency"},
        "hypothesis": "Adding urgency increases conversions (generic CRO best practice).",
        "primary_change": "Add countdown timers and low-stock banners across the site.",
        "primary_kpi": "Conversion rate", "decision_rule": "Ship if conversion improves.",
        "expected_lift": {"low": 5, "high": 10, "unit": "%"},
        "confidence": 70, "confidence_basis": "pattern / best-practice",
    }
    tech = json.loads(json.dumps(TECH_CHECKS))
    for c in tech["checks"]:
        if c["name"] == "Sitemap":                                   # F4
            c["status"] = "Pass"
            c["detail"] = "Sitemap present."
            c["grounded_in"] = "not inspected"
    w(store_root / "reason" / "store_profile.json", STORE_PROFILE)
    w(store_root / "reason" / "visual_findings.json", VISUAL_FINDINGS)
    w(store_root / "reason" / "leaks.json", make_leaks())
    w(store_root / "reason" / "experiments.json", {"experiments": exps})
    w(store_root / "reason" / "competitors.json", COMPETITORS)
    w(store_root / "reason" / "tech_checks.json", tech)
    w(store_root / "reason" / "synthesis.json", SYNTHESIS)


def main():
    for d in (PASS, BROKEN):
        if d.exists():
            shutil.rmtree(d)
    build_crawl(PASS)
    build_reason_pass(PASS)
    build_crawl(BROKEN)          # same crawl artifacts; only reason is faulted
    build_reason_broken(BROKEN)
    print(f"PIL screenshots: {HAVE_PIL}")
    print(f"wrote {PASS}")
    print(f"wrote {BROKEN}")


if __name__ == "__main__":
    main()
