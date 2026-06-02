"""
Check ShipBob API for product/inventory dimensions.
"""
import json
import urllib.request
import urllib.error

API_KEY  = "3E673925F80C19A56356A01DEA7E6CA85E4D5A6A50B0512AC92E2977AF37EBBD-1"
BASE_URL = "https://api.shipbob.com/2025-07"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
}

def get(path, params=""):
    url = f"{BASE_URL}{path}"
    if params:
        url += f"?{params}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "reason": e.reason, "body": e.read().decode()}
    except Exception as e:
        return {"error": str(e)}

print("=" * 60)
print("1. GET /inventory  (first item — all fields)")
print("=" * 60)
inv = get("/inventory", "Page=1&Limit=1")
if isinstance(inv, list) and inv:
    print(json.dumps(inv[0], indent=2))
    # highlight dimension-related keys
    item = inv[0]
    dim_keys = [k for k in item if any(w in k.lower() for w in
                ["dim", "weight", "length", "width", "height", "size", "measure"])]
    print("\nDimension-related keys found:", dim_keys if dim_keys else "NONE")
else:
    print(json.dumps(inv, indent=2))

print()
print("=" * 60)
print("2. GET /product  (first item — all fields)")
print("=" * 60)
prod = get("/product", "Page=1&Limit=1")
if isinstance(prod, list) and prod:
    print(json.dumps(prod[0], indent=2))
    item = prod[0]
    dim_keys = [k for k in item if any(w in k.lower() for w in
                ["dim", "weight", "length", "width", "height", "size", "measure"])]
    print("\nDimension-related keys found:", dim_keys if dim_keys else "NONE")
else:
    print(json.dumps(prod, indent=2))
