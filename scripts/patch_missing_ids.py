"""
Fetches ShipBob dims for the 5 missing products using their inventory IDs,
updates products.json, and appends rows to shipbob_sizes.csv.
"""
import sys, json, csv, urllib.request, urllib.error, time
sys.stdout.reconfigure(encoding='utf-8')

BASE = r'c:\Users\denis_particleformen\Desktop\Cursor Projects\shipbob-boxes-calculator'
API_KEY  = "3E673925F80C19A56356A01DEA7E6CA85E4D5A6A50B0512AC92E2977AF37EBBD-1"
BASE_URL = "https://api.shipbob.com/2025-07"
HEADERS  = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept":        "application/json",
    "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

KNOWN = [
    {"our_title": "Particle Scalp Massager",          "inv_id": 14648937, "sku": "9162027"},
    {"our_title": "Particle Comb",                    "inv_id": 22472758, "sku": "70113000"},
    {"our_title": "Particle Nose Trimmer",             "inv_id": 22472759, "sku": "70114000"},
    {"our_title": "Particle Gravité Tester 1.5ml",    "inv_id": 22817579, "sku": "70117000"},
    {"our_title": "Particle Shaving Cream Stand",     "inv_id": 20985718, "sku": "00860012469758"},
]

def api_get(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

# ── Fetch from ShipBob ────────────────────────────────────────────────────────
fetched = []
for k in KNOWN:
    print(f"Fetching {k['inv_id']} ({k['our_title']})...")
    try:
        data = api_get(f"/inventory/{k['inv_id']}")
        dims = data.get("dimensions") or {}
        fetched.append({
            "our_title":  k["our_title"],
            "sku":        k["sku"],
            "inv_id":     k["inv_id"],
            "sb_name":    data.get("name", ""),
            "length_in":  dims.get("length", ""),
            "width_in":   dims.get("width",  ""),
            "height_in":  dims.get("height", ""),
            "weight_lbs": data.get("weight", ""),
        })
        print(f"  {data.get('name')} → L={dims.get('length')} W={dims.get('width')} H={dims.get('height')}")
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} — skipping")
    time.sleep(0.2)

# ── Update products.json ──────────────────────────────────────────────────────
with open(f'{BASE}/data/products.json', encoding='utf-8') as f:
    products = json.load(f)

for row in fetched:
    product = next((p for p in products if p['title'].lower() == row['our_title'].lower()), None)
    if not product:
        print(f"  WARN: '{row['our_title']}' not found in products.json")
        continue

    product['shipbob_inventory_id']   = row['inv_id']
    product['shipbob_inventory_name'] = row['sb_name']
    product['sku'] = row['sku']

    # Keep Excel dims (more accurate) but fill in if missing
    if not product.get('dimensions') and row['length_in']:
        product['dimensions'] = {
            'length': float(row['length_in']),
            'width':  float(row['width_in']),
            'height': float(row['height_in']),
        }

    print(f"  Updated {row['our_title']} → inv_id={row['inv_id']}, sku={row['sku']}")

with open(f'{BASE}/data/products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)
print("✓ products.json saved")

# ── Append to CSV ─────────────────────────────────────────────────────────────
CSV_PATH = f'{BASE}/data/shipbob_sizes.csv'
with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
    fieldnames = ['id','name','sku','barcode','length_in','width_in','height_in','weight_lbs','total_fulfillable_qty']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    for row in fetched:
        writer.writerow({
            'id':        row['inv_id'],
            'name':      row['sb_name'] or row['our_title'],
            'sku':       row['sku'],
            'barcode':   '',
            'length_in': row['length_in'],
            'width_in':  row['width_in'],
            'height_in': row['height_in'],
            'weight_lbs': row['weight_lbs'],
            'total_fulfillable_qty': '',
        })
print(f"✓ Appended {len(fetched)} rows to shipbob_sizes.csv")
