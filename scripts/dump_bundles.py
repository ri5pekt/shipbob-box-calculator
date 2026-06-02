"""Show ShipBob product/bundle compositions via the /product endpoint."""
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

API_KEY = "3E673925F80C19A56356A01DEA7E6CA85E4D5A6A50B0512AC92E2977AF37EBBD-1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

def api_get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

# Fetch all products
BASE = "https://api.shipbob.com/2025-07"
data = api_get(f"{BASE}/product?Page=1&Limit=200")
products = data.get("items", data) if isinstance(data, dict) else data
print(f"Products returned: {len(products)}")
print()

# Save full dump for inspection
with open("scripts/shipbob_products_dump.json", "w", encoding="utf-8") as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

# Print structure of first product to understand the schema
if products:
    print("=== First product keys:", list(products[0].keys()))
    print(json.dumps(products[0], indent=2, ensure_ascii=False)[:1500])
    print()

# Show all products with their inventory components
print("=== Products with inventory components:")
for p in products:
    name = p.get("name", "")
    sku  = str(p.get("sku", "") or "")
    # Try different field names ShipBob might use
    components = (
        p.get("inventory_items") or
        p.get("fulfillment_inventory_items") or
        p.get("channel_products") or
        []
    )
    if components:
        print(f"  {name!r}  (SKU={sku})")
        for c in components:
            iid = c.get("inventory_item_id") or c.get("id") or "?"
            qty = c.get("quantity") or c.get("qty") or 1
            print(f"    -> inventory_id={iid}  qty={qty}")
