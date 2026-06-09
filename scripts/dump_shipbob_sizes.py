"""
dump_shipbob_sizes.py
Fetches every inventory item from ShipBob and saves a CSV with:
  id, name, sku, barcode, length, width, height, weight
"""
import sys, json, csv, urllib.request, urllib.error, time
sys.stdout.reconfigure(encoding='utf-8')

API_KEY  = "3E673925F80C19A56356A01DEA7E6CA85E4D5A6A50B0512AC92E2977AF37EBBD-1"
BASE_URL = "https://api.shipbob.com/2025-07"
HEADERS  = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept":        "application/json",
    "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

BASE    = r"c:\Users\denis_particleformen\Desktop\Cursor Projects\shipbob-boxes-calculator"
OUT_CSV = rf"{BASE}\data\shipbob_sizes.csv"


def api_get(path, params=""):
    url = f"{BASE_URL}{path}{'?' + params if params else ''}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


PRODUCTS_JSON = f"{BASE}/data/products.json"

def fetch_by_ids(ids):
    items = []
    for iid in ids:
        print(f"  Fetching inventory/{iid}...", flush=True)
        try:
            data = api_get(f"/inventory/{iid}")
            items.append(data)
        except urllib.error.HTTPError as e:
            print(f"    HTTP {e.code} — skipping")
        time.sleep(0.15)
    return items


# Load inventory IDs from products.json
with open(PRODUCTS_JSON, encoding='utf-8') as f:
    all_products = json.load(f)

ids = [
    p['shipbob_inventory_id']
    for p in all_products
    if p.get('shipbob_inventory_id') and not p.get('components')
]
print(f"Fetching {len(ids)} Particle inventory items from ShipBob...")
items = fetch_by_ids(ids)
print(f"\nTotal items fetched: {len(items)}")

rows = []
for item in items:
    dims = item.get("dimensions") or {}
    rows.append({
        "id":       item.get("id", ""),
        "name":     item.get("name", ""),
        "sku":      item.get("sku", "") or "",
        "barcode":  (item.get("barcodes") or [{}])[0].get("value", "") if item.get("barcodes") else "",
        "length_in": dims.get("length", ""),
        "width_in":  dims.get("width", ""),
        "height_in": dims.get("height", ""),
        "weight_lbs": item.get("fulfillable_quantity_by_fulfillment_center", ""),
        "total_fulfillable_qty": item.get("total_fulfillable_quantity", ""),
    })

# Write CSV
with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"\n✓ Saved {len(rows)} rows to:\n  {OUT_CSV}")

# Quick preview
print("\nPreview (first 10 rows with dimensions):")
shown = 0
for r in rows:
    if r["length_in"] or r["width_in"]:
        print(f"  {r['name'][:45]:45} | L={r['length_in']} W={r['width_in']} H={r['height_in']}")
        shown += 1
        if shown >= 10:
            break
