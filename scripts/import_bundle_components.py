"""
Read bundle compositions from ShipBob /product endpoint and add a
`components` array to each bundle entry in products.json.

Each component entry:
  { "sku": "...", "title": "...", "quantity": N }

The bundle's own `dimensions` and `dimensions_source` are cleared since
the packing calculator will explode it into individual items.
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

API_KEY = "3E673925F80C19A56356A01DEA7E6CA85E4D5A6A50B0512AC92E2977AF37EBBD-1"
BASE    = "https://api.shipbob.com/2025-07"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept":        "application/json",
    "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

ROOT          = Path(__file__).resolve().parent.parent
PRODUCTS_PATH = ROOT / "data" / "products.json"

# Map ShipBob product name  →  our products.json title
# Only needed where names differ
BUNDLE_NAME_MAP: dict[str, str] = {
    "Particle Lady Killer Kit":          "Particle Lady Killer Kit",
    "Particle Gravite Bundle":           "Particle Gravité Bundle",
    "Particle Gravité Bundle":           "Particle Gravité Bundle",
    "Bold Moves Bundle":                 "Bold Moves Bundle",
    "Bold Moves Bundle ":                "Bold Moves Bundle",
    "Head Turner Set":                   "Head Turner Set",
    "Dark Spot Remover Set":             "Dark Spot Remover Set",
    "The Smooth Skin Set":               "The Smooth Skin Set",
    "Men's gift bundle":                 "Men's Gift Bundle",
    "Men's Gift Bundle":                 "Men's Gift Bundle",
    "Golfers Bundle":                    "Particle Golfer's Bundle",
    "Particle Golfer's Bundle":          "Particle Golfer's Bundle",
    "Hair Growth Bundle":                "Hair Growth Bundle",
    "Power Shower Set":                  "Power Shower Set",
    "Starter Bundle":                    "Starter Bundle",
    "Particle Essential Bundle":         "Essential Bundle",
    "Essential Bundle":                  "Essential Bundle",
    "Particle Advanced Bundle":          "Advanced Bundle",
    "Particle  Advanced Bundle":         "Advanced Bundle",   # double-space in ShipBob
    "Advanced Bundle":                   "Advanced Bundle",
    "Particle Father's Day Gift Bundle": "Particle Father's Day Gift Bundle",
    "Father's Day Gift Bundle":          "Particle Father's Day Gift Bundle",
    "2025 Holiday Gift Bundle":          "Particle Father's Day Gift Bundle",
    "Restoration Bundle":                "Starter Bundle",   # ShipBob alias
    "Hair Growth Set":                   "Hair Growth Bundle",
}

# Map ShipBob variant SKU / name  →  our products.json title
# Needed where ShipBob uses a different SKU or product name
COMPONENT_SKU_MAP: dict[str, str] = {
    # ShipBob SKU           : our title
    "00860012469772":        "Particle 43 Anti-Aging Shaving Gel",
    "860005339785":          "Particle Gravité",
    "860012469710":          "Particle Gravité Deodorant",
    "636665869661":          "Particle Hair Thickening Shampoo",
    "860010338483":          "Particle Face Shield",
    "00860012469765":        "Particle Varros",
    "00860014497216":        "Particle Hand Cream",
}

def api_get(path: str) -> list | dict:
    url = f"{BASE}{path}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

# ShipBob product IDs for our bundles (from the ShipBob UI — Bundle Details tab)
# Format: our products.json title -> ShipBob product ID
KNOWN_PRODUCT_IDS: dict[str, int] = {
    "Particle Lady Killer Kit":          8354688,
    "Particle Gravité Bundle":           7584646,
    "Bold Moves Bundle":                 9059312,
    "Head Turner Set":                   10057310,
    "Dark Spot Remover Set":             9473008,
    "The Smooth Skin Set":               9473007,
    "Men's Gift Bundle":                 9367115,
    "Particle Golfer's Bundle":          7818477,
    "Hair Growth Bundle":                None,   # not found yet
    "Power Shower Set":                  None,
    "Starter Bundle":                    None,
    "Essential Bundle":                  2706911,   # from screenshot
    "Advanced Bundle":                   None,
    "Particle Father's Day Gift Bundle": 8952718,   # ShipBob: "2025 Holiday Gift Bundle"
}


def fetch_product_by_id(product_id: int) -> dict | None:
    try:
        data = api_get(f"/product/{product_id}")
        return data
    except Exception as e:
        print(f"    Error fetching product id={product_id}: {e}")
        return None


def search_product_by_sku(sku: str) -> dict | None:
    """Search /product?SKU= — returns a list, take first Bundle match."""
    if not sku:
        return None
    try:
        from urllib.parse import quote
        data = api_get(f"/product?SKU={quote(sku)}&Limit=10")
        items = data.get("items", data) if isinstance(data, dict) else data
        # Prefer Bundle type
        for item in items:
            if item.get("type") == "Bundle":
                return item
        if items:
            return items[0]
    except Exception as e:
        print(f"    SKU search error ({sku}): {e}")
    return None


def fetch_relevant_products(our_bundles: list) -> list:
    """Fetch only the specific bundle products we care about."""
    results = []
    seen_ids = set()

    for p in our_bundles:
        title   = p["title"]
        sku     = str(p.get("sku", "")).strip()
        prod_id = KNOWN_PRODUCT_IDS.get(title)

        sb_p = None
        if prod_id:
            sb_p = fetch_product_by_id(prod_id)
        if not sb_p:
            print(f"  Searching by SKU for: {title!r}  (SKU={sku})")
            sb_p = search_product_by_sku(sku)

        if sb_p:
            iid = sb_p.get("id")
            if iid not in seen_ids:
                seen_ids.add(iid)
                results.append(sb_p)
                print(f"  Found: {title!r} -> ShipBob '{sb_p.get('name')}' (id={iid})")
        else:
            print(f"  Not found: {title!r}")

    return results

def main():
    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))

    # Build our title → product lookup
    by_title = {p["title"].strip().lower(): p for p in products}
    by_sku   = {str(p.get("sku", "")).strip(): p for p in products}

    # Only fetch ShipBob data for our bundle products
    our_bundles = [p for p in products if p.get("category") in ("bundle", "kit")]

    print(f"Fetching ShipBob data for {len(our_bundles)} bundle products...\n")
    sb_products = fetch_relevant_products(our_bundles)
    print(f"\nFetched {len(sb_products)} ShipBob bundle products\n")

    def find_our_product(sb_name: str, sku: str) -> dict | None:
        # 1. explicit override by SKU
        override = COMPONENT_SKU_MAP.get(sku.strip())
        if override:
            return by_title.get(override.lower())
        # 2. exact SKU match
        p = by_sku.get(sku.strip())
        if p:
            return p
        # 3. title match (case-insensitive)
        return by_title.get(sb_name.strip().lower())

    updated   = []
    not_found = []

    for sb_p in sb_products:
        sb_name = sb_p.get("name", "").strip()

        # Resolve to our title
        our_title = BUNDLE_NAME_MAP.get(sb_name, sb_name)
        our_p     = by_title.get(our_title.strip().lower())
        if not our_p:
            not_found.append(f"ShipBob '{sb_name}' → looking for '{our_title}'")
            continue

        # Pull bundle_definition from first variant that has it
        bundle_def = []
        for v in sb_p.get("variants", []):
            bd = v.get("bundle_definition", [])
            if bd:
                bundle_def = bd
                break

        if not bundle_def:
            not_found.append(f"'{our_title}' — no bundle_definition in ShipBob")
            continue

        # Build components list
        components = []
        missing_components = []
        for item in bundle_def:
            comp_sku  = str(item.get("variant_sku", "")).strip()
            comp_name = item.get("variant_name", "").strip()
            qty       = item.get("quantity", 1)

            comp_p = find_our_product(comp_name, comp_sku)
            if comp_p:
                components.append({
                    "sku":      comp_p["sku"],
                    "title":    comp_p["title"],
                    "quantity": qty,
                })
            else:
                missing_components.append(f"{comp_name} (SKU {comp_sku})")

        if missing_components:
            print(f"  WARNING '{our_title}': components not matched: {missing_components}")

        if components:
            our_p["components"] = components
            # Remove stale placeholder dimensions — bundle is now virtual
            our_p.pop("dimensions",          None)
            our_p.pop("dimensions_source",   None)
            our_p.pop("unit",                None)
            our_p.pop("unit_volume_cu_in",   None)
            our_p.pop("unit_weight_lbs",     None)
            our_p.pop("unit_weight_oz",      None)
            updated.append(our_title)

    PRODUCTS_PATH.write_text(
        json.dumps(products, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Updated {len(updated)} bundles with component lists:")
    for t in updated:
        p = by_title[t.strip().lower()]
        comps = ", ".join(f"{c['quantity']}x {c['title']}" for c in p["components"])
        print(f"  {t}: [{comps}]")

    if not_found:
        print(f"\nNot matched ({len(not_found)}):")
        for s in not_found:
            print(f"  {s}")

if __name__ == "__main__":
    main()
