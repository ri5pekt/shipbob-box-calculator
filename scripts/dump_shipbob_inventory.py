"""Dump all ShipBob inventory items with dims/weight for mapping."""
import json
import urllib.request
from pathlib import Path

API_KEY  = "3E673925F80C19A56356A01DEA7E6CA85E4D5A6A50B0512AC92E2977AF37EBBD-1"
BASE_URL = "https://api.shipbob.com/2025-07"
HEADERS  = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

def api_get(path, params=""):
    url = f"{BASE_URL}{path}{'?' + params if params else ''}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def fetch_all_inventory():
    items, page = [], 1
    while True:
        data  = api_get("/inventory", f"Page={page}&Limit=250")
        batch = data.get("items", data) if isinstance(data, dict) else data
        if not batch:
            break
        items.extend(batch)
        if len(batch) < 250:
            break
        page += 1
    return items

inventory = fetch_all_inventory()

# Save full dump
out_path = Path(__file__).parent / "shipbob_inventory_dump.json"
out_path.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Saved {len(inventory)} items to {out_path.name}")
print()

# Print table
print(f"{'ID':<12} {'Name':<50} {'SKU':<20} {'Validated':<10} {'L x W x H (in)':<24} Weight")
print("-" * 130)
for item in sorted(inventory, key=lambda x: x.get("name", "")):
    inv_id = item.get("inventory_id", "")
    name   = item.get("name", "")[:50]
    sku    = str(item.get("sku", ""))
    dims   = item.get("dimensions", {})
    weight = item.get("weight", {})
    valid  = dims.get("validated", False)
    l, w, h = dims.get("length", 0), dims.get("width", 0), dims.get("height", 0)
    wt    = weight.get("value", 0)
    wt_u  = weight.get("unit", "")
    dim_str = f"{l}x{w}x{h}" if valid and l > 0 else "—"
    wt_str  = f"{wt} {wt_u}" if wt > 0 else "—"
    flag = " *" if valid and l > 0 else ""
    print(f"{inv_id:<12} {name:<50} {sku:<20} {'YES' if valid else 'no':<10} {dim_str:<24} {wt_str}{flag}")
