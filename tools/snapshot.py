"""Refresh assets/products.json from MMF Fusion's WooCommerce store (in-stock only).
Run: python tools/snapshot.py              (MMF's live store)
     python tools/snapshot.py --sample     (rebuild the sample stock from the CloudVapor template, see below)

Same shape as the template, plus:
  vid  product id for WooCommerce add-to-cart links (?add-to-cart=<vid>&quantity=<q>)
  var  True when the product has options (flavour, colour, strength)
and per product in assets/details/: i (big image), d (description), a (specs), v (variants: [id, title, price]), o (option name)."""
import json, re, html, sys, urllib.request, pathlib

STORE = "https://mmffusion.com"
MAX_TERMS = 8
MAX_VARIANTS = 40
SHARDS = 40  # must match DETAIL_SHARDS in assets/site.js
MAIN = {"Vape": "vape", "Hookah": "hookah", "Snus": "snus"}
SKIP = {"December Sale", "NEW ARRIVALS", "Uncategorized", "MTL", "Vape", "Hookah"}
ROOT = pathlib.Path(__file__).resolve().parent.parent
SAMPLE = pathlib.Path(r"C:\Users\HP\CloudVapor Site\assets")
SAMPLE_STORE = "https://cloudsidevapor.co.za"
# not vape stock: hookah, cigars, papers, cannabis / THC lines
SKIP_WORDS = r"\b(hookah|shisha|coals?|rolling papers?|cigars?|backwoods|thc|cbd|cannabis|kush|indica|sativa|hybrid|strain|bud brothers|leaf buddy)\b"

def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60))

def text(h, cap):
    t = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[\s\S]*?</\1>", "", h or "")))
    t = re.sub(r"\s+", " ", t).strip()
    return t if len(t) <= cap else t[:cap].rsplit(" ", 1)[0] + "…"

def money(pr):
    div = 10 ** pr["currency_minor_unit"]
    return int(pr["price_range"]["min_amount"] if pr.get("price_range") else pr["price"]) / div

def variants(store, p):
    """[[variation id, "Mango Ice", price], ...] for the in-stock options, and the option name ("Flavour")."""
    out, name = [], ""
    for v in p.get("variations", [])[:MAX_VARIANTS]:
        try: d = get(f"{store}/wp-json/wc/store/v1/products/{v['id']}")
        except Exception: continue
        if not d.get("is_in_stock") or not d.get("is_purchasable", True): continue
        price = money(d["prices"])
        if not 0 < price < 5000: continue
        # slugs like "ice-pick" / "3mg" -> "Ice Pick" / "3mg"
        attrs = [" ".join(w.capitalize() if w.isalpha() else w for w in html.unescape(a["value"]).replace("-", " ").split()) if a["value"].islower() else html.unescape(a["value"]) for a in v["attributes"]]
        name = name or html.unescape(v["attributes"][0]["name"]) if v["attributes"] else name
        out.append([v["id"], " / ".join(a for a in attrs if a) or f"Option {len(out) + 1}", price])
    return out, (name or "Option").replace("pa_", "").title()

def write(out, details):
    out.sort(key=lambda o: (not o["new"], not o["t"], o["n"]))
    path = ROOT / "assets" / "products.json"
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    ddir = path.parent / "details"; ddir.mkdir(exist_ok=True)  # sharded so a product page downloads ~1/40th
    for old in ddir.glob("*.json"): old.unlink()
    for k in range(SHARDS):
        part = {i: v for i, v in details.items() if int(i) % SHARDS == k}
        (ddir / f"{k}.json").write_text(json.dumps(part, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(out)} products -> {path.name} ({path.stat().st_size // 1024} KB) + {SHARDS} detail shards")

def live():
    out, details = [], {}
    for n in range(1, 100):
        batch = get(f"{STORE}/wp-json/wc/store/v1/products?per_page=100&stock_status=instock&page={n}")
        if not batch: break
        for p in batch:
            if not p.get("is_in_stock") or not p.get("is_purchasable", True): continue
            cats = [html.unescape(c["name"]) for c in p["categories"]]
            name = html.unescape(p["name"])
            price = money(p["prices"])
            if price <= 0 or price >= 5000: price = 0  # typos like R64,999 for a pod kit or R199.99 typed as R19,999 show as "Ask for price"
            puffs = re.search(r"(\d{1,3}(?:[ ,]\d{3})+|\d+(?:\.\d+)?)\s*k?\s*puffs?", name, re.I)
            mg = re.search(r"(\d+(?:\.\d+)?)\s*mg", name, re.I)
            img = p["images"][0] if p["images"] else {}
            attrs = {a["name"]: ", ".join(t["name"] for t in a["terms"]) for a in p["attributes"] if a.get("terms") and len(a["terms"]) <= MAX_TERMS}
            desc = text(p["short_description"] or p["description"], 700)
            det = {"i": img.get("src", ""), "d": "" if desc.lower() in ("none", "") else desc, "a": attrs}
            if p["type"] == "variable":
                det["v"], det["o"] = variants(STORE, p)
                if not det["v"]: continue
            details[p["id"]] = det
            out.append({
                "id": p["id"], "n": name, "p": price, "c": next((MAIN[c] for c in cats if c in MAIN), "vape"),
                "s": next((c for c in cats if c not in SKIP), "Other"),
                "b": html.unescape(p["brands"][0]["name"]) if p.get("brands") else "",
                "t": img.get("thumbnail", ""), "u": p["permalink"], "vid": p["id"],
                "new": "NEW ARRIVALS" in cats, "var": p["type"] == "variable",
                "puffs": re.sub(r"[ ,]", "", puffs.group(1)) if puffs else "", "mg": mg.group(1) if mg else "",
            })
    assert out, "no in-stock products: the shop is still empty, keep the sample stock (python tools/snapshot.py --sample)"
    assert sum(o["p"] > 0 for o in out) > len(out) * 0.9, "prices look wrong"
    write(out, details)

def sample():
    """Sample stock until MMF's own shop has products: the CloudVapor template catalogue without hookah and
    nicotine pouches (MMF doesn't list them), with flavour options pulled for the variable products."""
    out = [p for p in json.loads((SAMPLE / "products.json").read_text(encoding="utf-8"))
           if p["c"] == "vape" and p["s"] != "Other" and not re.search(SKIP_WORDS, p["n"] + " " + p["s"], re.I)]
    details = {}
    for f in (SAMPLE / "details").glob("*.json"): details.update(json.loads(f.read_text(encoding="utf-8")))
    keep = {str(p["id"]) for p in out}
    details = {k: v for k, v in details.items() if k in keep}
    for p in out:
        p["vid"] = p["id"]
        if p["var"]:
            try: d, o = variants(SAMPLE_STORE, get(f"{SAMPLE_STORE}/wp-json/wc/store/v1/products/{p['id']}"))
            except Exception: d, o = [], ""
            if d: details.setdefault(str(p["id"]), {"i": "", "d": "", "a": {}}).update(v=d, o=o); print(f"  {p['n']}: {len(d)} options")
            else: p["var"] = False  # no options found: add it straight to the bag
    write(out, details)

if __name__ == "__main__":
    sample() if "--sample" in sys.argv else live()
