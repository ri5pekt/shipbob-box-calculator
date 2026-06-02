"""
Pull validated dimensions from ShipBob for every product that doesn't have them yet.
Strategy:
  1. Known inventory IDs are queried directly (GET /inventory/{id})
  2. All remaining products are searched by barcode via the inventory list filter
"""
import json
import sys
import urllib.request
import urllib.parse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

API_KEY  = "3E673925F80C19A56356A01DEA7E6CA85E4D5A6A50B0512AC92E2977AF37EBBD-1"
BASE_URL = "https://api.shipbob.com/2025-07"
HEADERS  = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept":        "application/json",
    "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

ROOT          = Path(__file__).resolve().parent.parent
PRODUCTS_PATH = ROOT / "data" / "products.json"

# Explicit: our title -> ShipBob inventory_id
# Covers items missed by SKU matching (name differences, leading-zero SKUs, no barcode, etc.)
KNOWN_IDS: dict[str, int] = {
    "Particle Face Cream":                 11091320,
    "Particle Face Wash":                  11121554,
    "Particle Face Mask":                  11121552,
    "Particle Body Wash":                  11121561,
    "Particle Hair Thickening Shampoo":    11121560,
    "Particle Beard Oil":                  11121567,
    "Particle Neck Cream":                 11623231,
    "Particle Ab Firming Cream":           15425983,
    "Particle Gravité":                    12521772,
    "Particle Hair Revival Kit":           11121569,
    "Particle Hair Vitamin Gummies":       11623233,
    "Particle Skin Vitamin Gummies":       11623234,
    "Particle 43 Anti-Aging Shaving Gel": 20985723,
    "Particle Lip Balm":                  22401575,
    "Particle Varros":                    21383637,
    "Particle Hand Cream":                21757502,
    "Particle Gravité Deodorant":         19339631,
    "Particle Infinite Male":             18727399,
}


def api_get(path: str, params: str = "") -> dict | list:
    url = f"{BASE_URL}{path}{'?' + params if params else ''}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def get_by_id(inv_id: int) -> dict | None:
    try:
        return api_get(f"/inventory/{inv_id}")
    except Exception as e:
        print(f"    Error fetching id={inv_id}: {e}")
        return None


def search_by_barcode(barcode: str) -> dict | None:
    """Try ShipBob /inventory?Barcode= filter (also strips leading zeros)."""
    if not barcode:
        return None
    candidates = [barcode, barcode.lstrip("0")]
    for bc in dict.fromkeys(candidates):   # dedupe, preserve order
        if not bc:
            continue
        try:
            enc  = urllib.parse.quote(bc)
            data = api_get("/inventory", f"Barcode={enc}&Limit=10")
            items = data.get("items", data) if isinstance(data, dict) else data
            if items:
                return items[0]
        except Exception:
            pass
    return None


def extract_dims(item: dict) -> tuple[dict | None, dict | None]:
    """Return (dimensions_dict, weight_dict) if validated, else (None, None)."""
    dims   = item.get("dimensions", {})
    weight = item.get("weight", {})
    if dims.get("validated") and dims.get("length", 0) > 0:
        return dims, weight
    return None, None


def apply_to_product(p: dict, item: dict, dims: dict, weight: dict) -> None:
    p["dimensions"] = {
        "length": round(float(dims["length"]), 4),
        "width":  round(float(dims["width"]),  4),
        "height": round(float(dims["height"]), 4),
    }
    p["unit"]                     = "in"
    p["dimensions_source"]        = "shipbob_api_validated"
    p["shipbob_inventory_id"]     = item["inventory_id"]
    p["shipbob_inventory_name"]   = item.get("name", "")
    if weight.get("value", 0) > 0:
        oz = float(weight["value"])
        p["unit_weight_oz"]  = round(oz, 4)
        p["unit_weight_lbs"] = round(oz / 16, 4)


def main():
    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))

    updated    = []
    no_dims    = []
    not_found  = []

    for p in products:
        title = p["title"]
        sku   = str(p.get("sku", "")).strip()

        # ---------- 1. Known ID lookup ----------
        inv_id = KNOWN_IDS.get(title) or p.get("shipbob_inventory_id")
        if inv_id:
            item = get_by_id(inv_id)
            if item:
                dims, weight = extract_dims(item)
                if dims:
                    apply_to_product(p, item, dims, weight)
                    updated.append((title, item.get("name", ""), p["dimensions"], p.get("unit_weight_oz")))
                    continue
                else:
                    no_dims.append(f"{title}  (id={inv_id}, ShipBob name='{item.get('name','')}')")
                    continue

        # ---------- 2. Already validated, skip ----------
        if p.get("dimensions_source") == "shipbob_api_validated":
            continue

        # ---------- 3. Barcode search ----------
        print(f"  Searching barcode for: {title}  (SKU={sku})")
        item = search_by_barcode(sku)
        if item:
            dims, weight = extract_dims(item)
            if dims:
                apply_to_product(p, item, dims, weight)
                updated.append((title, item.get("name", ""), p["dimensions"], p.get("unit_weight_oz")))
                continue
            else:
                no_dims.append(f"{title}  (id={item['inventory_id']}, ShipBob name='{item.get('name','')}')")
        else:
            not_found.append(title)

    PRODUCTS_PATH.write_text(
        json.dumps(products, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"\n{'='*70}")
    print(f"Updated {len(updated)} products with ShipBob validated dims:")
    for title, sb_name, d, oz in updated:
        match_note = "" if title == sb_name else f"  <-- ShipBob: '{sb_name}'"
        print(f"  {title:<47} {d['length']}x{d['width']}x{d['height']} in  {oz or '?'} oz{match_note}")

    print(f"\nIn ShipBob but no validated dims ({len(no_dims)}):")
    for t in no_dims:
        print(f"  {t}")

    print(f"\nNot found in ShipBob ({len(not_found)}):")
    for t in not_found:
        print(f"  {t}")


if __name__ == "__main__":
    main()
