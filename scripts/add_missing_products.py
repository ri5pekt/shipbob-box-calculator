"""
Adds Scalp Massager, Comb, Nose Trimmer, Gravite Tester, Shaving Cream Stand
to products.json (dims from Excel) and tries to find their ShipBob inventory IDs.
"""
import sys, json, urllib.request, urllib.error, time
sys.stdout.reconfigure(encoding='utf-8')

BASE = r'c:\Users\denis_particleformen\Desktop\Cursor Projects\shipbob-boxes-calculator'

API_KEY  = "3E673925F80C19A56356A01DEA7E6CA85E4D5A6A50B0512AC92E2977AF37EBBD-1"
BASE_URL = "https://api.shipbob.com/2025-07"
HEADERS  = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept":        "application/json",
    "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

def api_get(path, params=""):
    url = f"{BASE_URL}{path}{'?' + params if params else ''}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def search_inventory_by_id(inv_id):
    try:
        return api_get(f"/inventory/{inv_id}")
    except urllib.error.HTTPError:
        return None

def search_by_barcode(barcode):
    try:
        data = api_get("/inventory", f"Barcode={barcode}")
        items = data if isinstance(data, list) else data.get("items", [])
        return items[0] if items else None
    except urllib.error.HTTPError:
        return None

# ── New products with dims from Excel (H→length, W→width, L→height) ──────────
# Excel cols: H(in), W(in), L(in)
NEW_PRODUCTS = [
    {
        "title":          "Particle Scalp Massager",
        "sku":            "6005.0001",
        "category":       "accessory",
        "dimensions":     {"length": 3.0, "width": 3.5,  "height": 3.0},
        "unit":           "in",
        "hint_inv_id":    14648937,   # from Excel note
        "search_barcode": "6005.0001",
    },
    {
        "title":          "Particle Comb",
        "sku":            None,
        "category":       "accessory",
        "dimensions":     {"length": 0.1, "width": 7.2,  "height": 1.5},
        "unit":           "in",
        "hint_inv_id":    None,
        "search_barcode": None,
    },
    {
        "title":          "Particle Nose Trimmer",
        "sku":            None,
        "category":       "accessory",
        "dimensions":     {"length": 1.3, "width": 2.5,  "height": 2.0},
        "unit":           "in",
        "hint_inv_id":    None,
        "search_barcode": None,
    },
    {
        "title":          "Particle Gravité Tester 1.5ml",
        "sku":            None,
        "category":       "accessory",
        "dimensions":     {"length": 0.3, "width": 4.0,  "height": 2.3},
        "unit":           "in",
        "hint_inv_id":    None,
        "search_barcode": None,
    },
    {
        "title":          "Particle Shaving Cream Stand",
        "sku":            None,
        "category":       "accessory",
        "dimensions":     {"length": 1.5, "width": 8.0,  "height": 4.0},
        "unit":           "in",
        "hint_inv_id":    None,
        "search_barcode": None,
    },
]

# ── Load existing products ────────────────────────────────────────────────────
with open(f'{BASE}/data/products.json', encoding='utf-8') as f:
    products = json.load(f)

max_id = max(p['id'] for p in products if isinstance(p.get('id'), int))
next_id = max_id + 1

existing_titles = {p['title'].lower() for p in products}

# ── Try to resolve ShipBob IDs ────────────────────────────────────────────────
print("Searching ShipBob for inventory IDs...\n")
added = []

for np in NEW_PRODUCTS:
    if np['title'].lower() in existing_titles:
        print(f"  SKIP (already exists): {np['title']}")
        continue

    inv_id = None
    inv_name = None

    # Try hint ID first
    if np['hint_inv_id']:
        print(f"  Trying hint ID {np['hint_inv_id']} for {np['title']}...")
        result = search_inventory_by_id(np['hint_inv_id'])
        if result:
            inv_id   = result.get('id')
            inv_name = result.get('name')
            print(f"    ✓ Found: {inv_name} (id={inv_id})")

    # Try barcode search
    if not inv_id and np['search_barcode']:
        print(f"  Searching barcode '{np['search_barcode']}' for {np['title']}...")
        result = search_by_barcode(np['search_barcode'])
        if result:
            inv_id   = result.get('id')
            inv_name = result.get('name')
            print(f"    ✓ Found: {inv_name} (id={inv_id})")

    if not inv_id:
        print(f"  ✗ No ShipBob ID found for {np['title']} — adding without ID")

    entry = {
        "id":       next_id,
        "title":    np['title'],
        "sku":      np['sku'] or "",
        "dimensions": np['dimensions'],
        "unit":     "in",
        "category": np['category'],
    }
    if inv_id:
        entry["shipbob_inventory_id"]   = inv_id
        entry["shipbob_inventory_name"] = inv_name

    products.append(entry)
    added.append(np['title'])
    print(f"  + Added: {np['title']}  dims={np['dimensions']}")
    next_id += 1
    time.sleep(0.2)

# ── Save ──────────────────────────────────────────────────────────────────────
with open(f'{BASE}/data/products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

print(f"\n✓ Added {len(added)} products to products.json")
for t in added:
    print(f"  + {t}")
