import json, sys
sys.stdout.reconfigure(encoding="utf-8")

data = json.loads(open("scripts/shipbob_inventory_dump.json", encoding="utf-8").read())

keywords = ["shav", "gel", "43", "scar", "lip", "balm", "eye", "serum"]
print("=== Matches for keywords:", keywords)
for item in data:
    name = item.get("name", "")
    sku  = str(item.get("sku", ""))
    if any(k in name.lower() for k in keywords):
        dims  = item.get("dimensions", {})
        valid = dims.get("validated", False)
        l, w, h = dims.get("length", 0), dims.get("width", 0), dims.get("height", 0)
        dim_s = f"{l}x{w}x{h}" if valid else "—"
        iid = item.get("inventory_id", "")
        print(f"  ID={iid}  SKU={sku:<22}  valid={valid}  dims={dim_s}  name={name!r}")

print()
print(f"Total items: {len(data)}")
print(f"Items with validated dims: {sum(1 for i in data if i.get('dimensions',{}).get('validated'))}")
