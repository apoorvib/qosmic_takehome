#!/usr/bin/env python3
"""extract.py — deterministic Shopify storefront capture (Module 1, Phase 1).

Model 2: the agent discovers which URLs to crawl (via Playwright MCP) and hands
them to this script. extract.py re-navigates each URL itself, so popup-dismissal
and extraction live in one place and runs are reproducible.

Per URL it captures: full-page + hero screenshots, a role-based DOM extraction,
explicit present/absent CRO signals, bounded readable content, and network facts
(status, redirects, security headers, console errors). Writes one page.json per
surface plus a manifest.json, all conforming to harness/schemas/*.

Paths inside artifacts are RELATIVE TO THE STORE ROOT (the --out dir), so a real
artifacts/<store>/ is structurally identical to fixtures/sample_store/.

Usage:
    python extract.py --store <slug> [--out artifacts/<slug>] <url> [<url> ...]

Safety: visits /cart but never proceeds through checkout.
"""
import argparse, json, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
VIEWPORT = {"width": 1366, "height": 900}
NAV_TIMEOUT = 45000
SETTLE_MS = 1800
INTER_URL_DELAY_S = 3.0   # polite gap between surfaces; some stores (e.g. Cloudflare) rate-limit rapid hits
LAUNCH_ARGS = ["--disable-blink-features=AutomationControlled"]
EXTRA_HEADERS = {"Accept-Language": "en-US,en;q=0.9", "Upgrade-Insecure-Requests": "1"}
STEALTH_JS = (
    "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
    "Object.defineProperty(navigator,'languages',{get:()=>['en-US','en']});"
    "Object.defineProperty(navigator,'plugins',{get:()=>[1,2,3,4,5]});"
    "window.chrome={runtime:{}};"
)


def launch_browser(p):
    """Prefer real Chrome channel (passes more bot checks); fall back to bundled chromium."""
    try:
        return p.chromium.launch(headless=True, channel="chrome", args=LAUNCH_ARGS)
    except Exception:
        return p.chromium.launch(headless=True, args=LAUNCH_ARGS)


def new_context(browser):
    ctx = browser.new_context(user_agent=UA, viewport=VIEWPORT, locale="en-US",
                              extra_http_headers=EXTRA_HEADERS)
    ctx.add_init_script(STEALTH_JS)
    return ctx

POPUP_CLOSE_SELECTORS = [
    "[aria-label='Close']", "[aria-label='close']", "button.close", ".close-button",
    ".modal__close", ".needsclick.klaviyo-close-form", "#onetrust-accept-btn-handler",
    "button:has-text('Accept')", "button:has-text('No thanks')", "button:has-text('Close')",
    ".pop-up-close", ".popup-close", "[data-testid='close-button']",
]

# ---- JS extraction (runs in page context) ---------------------------------
EXTRACT_JS = r"""
() => {
  const cap = (s, n) => (s || "").replace(/\s+/g, " ").trim().slice(0, n);
  const vis = (el) => {
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    return r.width > 1 && r.height > 1 && st.display !== "none" && st.visibility !== "hidden" && st.opacity !== "0"
      ? r : null;
  };
  const H = window.innerHeight || 900;

  // elements: interactive + form
  const sel = "a,button,input,select,textarea,[role=button],form";
  const els = [];
  for (const el of document.querySelectorAll(sel)) {
    const r = vis(el);
    const tag = el.tagName.toLowerCase();
    const role = el.getAttribute("role") || tag;
    const text = cap(el.innerText || el.value || el.getAttribute("aria-label") || el.getAttribute("title"), 120);
    const o = { role, text, visible: !!r, aboveFold: r ? r.top < H : false };
    if (el.getAttribute("href")) o.href = el.getAttribute("href");
    if (el.getAttribute("type")) o.type = el.getAttribute("type");
    if (el.getAttribute("name")) o.name = el.getAttribute("name");
    if (el.getAttribute("placeholder")) o.placeholder = el.getAttribute("placeholder");
    if (r) o.bbox = [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
    if (o.text || o.href || tag === "input" || tag === "form") els.push(o);
  }
  // prioritize visible + above-fold, cap 60
  els.sort((a, b) => (b.visible + b.aboveFold) - (a.visible + a.aboveFold));
  const elements = els.slice(0, 60);

  const bodyText = cap(document.body ? document.body.innerText : "", 400000);
  const sig = (present, extra) => Object.assign({ present }, extra || {});

  // price
  let price = null;
  const priceEl = document.querySelector("[class*=price i],[data-price],.money,[itemprop=price]");
  const priceTxt = (priceEl && cap(priceEl.innerText, 40)) || "";
  const priceMatch = /(\$|€|£)\s?\d+(\.\d{2})?/.test(priceTxt) || /(\$|€|£)\s?\d+(\.\d{2})?/.test(bodyText.slice(0, 4000));
  price = sig(!!(priceEl && /\d/.test(priceTxt)) || priceMatch, priceTxt ? { value: priceTxt } : null);

  // add to cart
  let atc = null;
  for (const el of document.querySelectorAll("button,input[type=submit],[role=button],a")) {
    const t = (el.innerText || el.value || "").toLowerCase();
    if (/add to (cart|bag|basket)|buy now|add to my/.test(t)) { atc = sig(true, { text: cap(el.innerText || el.value, 40) }); break; }
  }
  if (!atc && document.querySelector("form[action*='/cart/add'],button[name='add']")) atc = sig(true);
  if (!atc) atc = sig(false);

  // reviews
  let reviews = sig(false);
  const rm = bodyText.match(/\b(\d{1,5})\s+reviews?\b/i);
  if (rm) reviews = sig(true, { value: cap(rm[0], 40) });
  else if (document.querySelector("[class*=review i],[class*=rating i],[data-reviews],.stamped-badge,.yotpo,.okeReviews"))
    reviews = sig(true, { value: "review widget present" });

  // trust badges
  const badges = [];
  const bm = bodyText.match(/#1[^.\n]{0,40}|award[\-\s]?winning|best[\-\s]?selling|clinically (proven|tested)|money[\-\s]?back guarantee/gi);
  if (bm) for (const m of bm.slice(0, 3)) badges.push(cap(m, 60));
  const trust_badges = badges.length ? sig(true, { items: [...new Set(badges)] }) : sig(false);

  // search
  const search = sig(!!document.querySelector("input[type=search],[role=search],form[action*=search],[name=q]"));

  // promo bar
  let promo = sig(false);
  for (const el of document.querySelectorAll("[class*=announce i],[class*=promo i],[class*=marquee i],[class*=topbar i],header [class*=banner i]")) {
    const r = vis(el);
    if (r && r.top < 200) { promo = sig(true, { text: cap(el.innerText, 80) }); break; }
  }

  // primary CTA: first prominent above-fold action element
  let cta = sig(false);
  for (const el of document.querySelectorAll("a,button,[role=button]")) {
    const r = vis(el); if (!r || r.top > H) continue;
    const t = (el.innerText || "").trim();
    if (t && /\b(shop|buy|add|get|start|find|order|explore)\b/i.test(t)) { cta = sig(true, { text: cap(t, 40) }); break; }
  }

  const cro_signals = { price, add_to_cart: atc, reviews, trust_badges, search, promo_bar: promo, primary_cta: cta };

  // headings
  const text_blocks = [];
  for (const h of document.querySelectorAll("h1,h2,h3")) {
    const t = cap(h.innerText, 120);
    if (t) text_blocks.push({ role: h.tagName.toLowerCase(), text: t });
    if (text_blocks.length >= 12) break;
  }

  // readable content: main/article else body, minus nav/footer
  let scope = document.querySelector("main,article,[role=main]") || document.body;
  const parts = [];
  if (scope) for (const el of scope.querySelectorAll("h1,h2,h3,h4,p,li")) {
    if (el.closest("nav,footer,header")) continue;
    const r = vis(el); if (!r) continue;
    const t = cap(el.innerText, 300);
    if (t && t.length > 2) parts.push(t);
    if (parts.join(" ").length > 1800) break;
  }
  const content = cap(parts.join(" "), 1800);

  // meta
  const metaC = (q) => { const m = document.querySelector(q); return m ? m.getAttribute("content") : undefined; };
  const og = {};
  for (const m of document.querySelectorAll("meta[property^='og:']")) og[m.getAttribute("property")] = m.getAttribute("content");
  const jsonld = [];
  for (const s of document.querySelectorAll("script[type='application/ld+json']")) {
    try { jsonld.push(JSON.parse(s.textContent)); } catch (e) {}
  }
  const meta = {
    title: cap(document.title, 200), description: metaC("meta[name=description]"),
    og, viewport: metaC("meta[name=viewport]"), jsonld,
  };

  return { title: cap(document.title, 200), meta, elements, cro_signals, text_blocks, content };
}
"""


def classify(url: str) -> str:
    p = urlparse(url).path.rstrip("/")
    if "/products/" in url:
        return "product"
    if "/collections/" in url:
        return "collection"
    if p.endswith("/cart") or p == "/cart":
        return "cart"
    if p in ("", "/"):
        return "homepage"
    if "/pages/" in url or "/blogs/" in url or "/blog/" in url:
        return "content"
    return "other"


def slugify(url: str) -> str:
    seg = [s for s in urlparse(url).path.split("/") if s]
    s = seg[-1] if seg else "home"
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "page"


def surface_id(stype: str, url: str, seen: set) -> str:
    if stype == "homepage":
        base = "home"
    elif stype == "cart":
        base = "cart"
    elif stype == "product":
        base = f"pdp-{slugify(url)}"
    elif stype == "collection":
        base = f"collection-{slugify(url)}"
    elif stype == "content":
        base = f"content-{slugify(url)}"
    else:
        base = f"page-{slugify(url)}"
    sid, i = base, 2
    while sid in seen:
        sid = f"{base}-{i}"; i += 1
    seen.add(sid)
    return sid


def dismiss_popups(page):
    for sel in POPUP_CLOSE_SELECTORS:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible(timeout=300):
                loc.click(timeout=600)
                time.sleep(0.2)
        except Exception:
            pass
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass


def scroll_through(page):
    try:
        h = page.evaluate("document.body.scrollHeight")
        step = VIEWPORT["height"]
        y = 0
        while y < min(h, step * 12):
            page.evaluate(f"window.scrollTo(0,{y})"); time.sleep(0.15); y += step
        page.evaluate("window.scrollTo(0,0)"); time.sleep(0.3)
    except Exception:
        pass


def redirect_chain(resp):
    chain = []
    try:
        req = resp.request
        rf = req.redirected_from
        while rf is not None:
            r = rf.response()
            chain.append({"from": rf.url, "to": req.url, "status": r.status if r else None})
            req = rf
            rf = rf.redirected_from
    except Exception:
        pass
    return list(reversed(chain))


SEC_KEYS = ["strict-transport-security", "content-security-policy", "x-frame-options", "x-content-type-options"]


def capture(page, url, sid, store_root: Path):
    responses, errors = [], []
    page.on("response", lambda r: responses.append({"url": r.url, "status": r.status}))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    t0 = time.time()
    try:
        resp = page.goto(url, wait_until="load", timeout=NAV_TIMEOUT)
    except Exception as e:
        resp = None
        errors.append(f"navigation error: {type(e).__name__}: {str(e)[:120]}")
    nav_ms = round((time.time() - t0) * 1000)

    time.sleep(SETTLE_MS / 1000)
    try:
        page.wait_for_selector("h1, main", timeout=3000)
    except Exception:
        pass
    dismiss_popups(page)
    scroll_through(page)

    sdir = store_root / sid / "screenshots"
    sdir.mkdir(parents=True, exist_ok=True)
    shots = []
    for name, kw in [(f"{sid}-fullpage.png", {"full_page": True}), (f"{sid}-hero.png", {})]:
        try:
            page.screenshot(path=str(sdir / name), timeout=15000, **kw)
            shots.append(f"{sid}/screenshots/{name}")
        except Exception as e:
            errors.append(f"screenshot {name} failed: {str(e)[:80]}")

    try:
        data = page.evaluate(EXTRACT_JS)
    except Exception as e:
        data = {"title": "", "meta": {}, "elements": [], "text_blocks": [], "content": "",
                "cro_signals": {k: {"present": False} for k in
                                ["price", "add_to_cart", "reviews", "trust_badges", "search", "promo_bar", "primary_cta"]}}
        errors.append(f"extract JS failed: {str(e)[:100]}")

    # drop null meta fields (absent tags come back as None over the JS bridge → would violate schema string types)
    if isinstance(data.get("meta"), dict):
        data["meta"] = {k: v for k, v in data["meta"].items() if v is not None}

    status = resp.status if resp else 0
    headers = resp.headers if resp else {}
    sec = {k: headers[k] for k in SEC_KEYS if k in headers}
    # keep main doc + any error responses, deduped, capped
    main = {"url": page.url, "status": status}
    errs = [r for r in responses if r["status"] >= 400]
    seen, compact = set(), [main]
    for r in errs + responses:
        key = (r["url"], r["status"])
        if key in seen:
            continue
        seen.add(key); compact.append(r)
        if len(compact) >= 60:
            break

    return {
        "url": page.url, "type": classify(url), "status": status,
        "title": data.get("title", ""),
        "meta": data.get("meta", {}),
        "elements": data.get("elements", []),
        "cro_signals": data["cro_signals"],
        "text_blocks": data.get("text_blocks", []),
        "content": data.get("content", ""),
        "screenshots": shots or [f"{sid}/screenshots/{sid}-fullpage.png"],
        "network": {
            "nav_timing_ms": nav_ms,
            "requests": len(responses),
            "redirects": redirect_chain(resp) if resp else [],
            "security_headers": sec,
            "responses": compact,
        },
        "console_errors": errors[:20],
    }


def _empty_signals():
    return {k: {"present": False} for k in
            ["price", "add_to_cart", "reviews", "trust_badges", "search", "promo_bar", "primary_cta"]}


def is_blocked(pj):
    t = (pj.get("title") or "").lower()
    return pj.get("status") in (403, 429, 503) or "attention required" in t or "just a moment" in t


def crawl_one(browser, url, sid, stype, store_root):
    """Fresh context per URL (avoids same-session rate-limit blocks); retry once on a block."""
    pj = None
    for attempt in (1, 2):
        ctx = new_context(browser)
        page = ctx.new_page()
        try:
            pj = capture(page, url, sid, store_root)
        except Exception as e:
            pj = {"url": url, "type": stype, "status": 0, "title": "", "meta": {}, "elements": [],
                  "cro_signals": _empty_signals(), "text_blocks": [], "content": "", "screenshots": [],
                  "network": {"responses": [{"url": url, "status": 0}]},
                  "console_errors": [f"capture failed: {str(e)[:120]}"]}
        finally:
            page.close(); ctx.close()
        if not is_blocked(pj) or attempt == 2:
            if is_blocked(pj):
                pj.setdefault("console_errors", []).append("blocked by bot protection (Warn: surface not inspected)")
            return pj
        time.sleep(6)
    return pj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("urls", nargs="+")
    args = ap.parse_args()

    store_root = Path(args.out or f"artifacts/{args.store}")
    store_root.mkdir(parents=True, exist_ok=True)
    seen, surfaces = set(), []

    with sync_playwright() as p:
        browser = launch_browser(p)
        for i, url in enumerate(args.urls):
            if i:
                time.sleep(INTER_URL_DELAY_S)
            stype = classify(url)
            sid = surface_id(stype, url, seen)
            pj = crawl_one(browser, url, sid, stype, store_root)
            (store_root / sid).mkdir(parents=True, exist_ok=True)
            (store_root / sid / "page.json").write_text(json.dumps(pj, indent=2, ensure_ascii=False), encoding="utf-8")
            surfaces.append({"id": sid, "type": stype, "url": pj.get("url", url),
                             "status": pj.get("status", 0), "page_json": f"{sid}/page.json"})
            print(f"  [{sid}] {pj.get('status')} {url}")
        browser.close()

    manifest = {"store": args.store, "crawled_at": datetime.now(timezone.utc).isoformat(), "surfaces": surfaces}
    (store_root / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {store_root}/manifest.json ({len(surfaces)} surfaces)")


if __name__ == "__main__":
    main()
