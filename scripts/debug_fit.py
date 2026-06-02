import json
from pathlib import Path

products = json.loads(Path("data/products.json").read_text(encoding="utf-8"))
boxes = json.loads(Path("data/boxes.json").read_text(encoding="utf-8"))

PADDING = 0.03

def padded(b):
    return sorted([b["length"] - PADDING, b["width"] - PADDING, b["height"] - PADDING], reverse=True)

def sorted_dims(d):
    return sorted([d["length"], d["width"], d["height"]])  # ascending: small → large

def fits(item_dims, box_padded_sorted_desc):
    # best case: orient item so its smallest dim goes along box's shortest axis
    item_s = sorted_dims(item_dims)  # ascending
    box_s = list(reversed(box_padded_sorted_desc))  # ascending
    return item_s[0] <= box_s[0] and item_s[1] <= box_s[1] and item_s[2] <= box_s[2]

names = ["Particle Skin Vitamin Gummies", "Particle Neck Cream", "Particle Lip Balm"]

for box in boxes:
    bp = padded(box["dimensions"])
    print(f"\n=== {box['name']} ===")
    print(f"  Inner:  {box['dimensions']['length']:.4f} × {box['dimensions']['width']:.4f} × {box['dimensions']['height']:.4f} in")
    print(f"  Padded: {bp[0]:.4f} × {bp[1]:.4f} × {bp[2]:.4f} in  (min axis = {min(bp):.4f} in)")
    for name in names:
        p = next(x for x in products if x["title"] == name)
        d = p["dimensions"]
        item_s = sorted_dims(d)
        result = fits(d, bp)
        print(f"\n  {name}")
        print(f"    dims: {d['length']} × {d['width']} × {d['height']} in  (source: {p.get('dimensions_source')})")
        print(f"    sorted (small to large): {[round(x,4) for x in item_s]}")
        print(f"    min item dim: {item_s[0]:.4f} in  vs  min box axis: {min(bp):.4f} in")
        print(f"    fits: {'YES' if result else 'NO -- min item dim exceeds min box axis'}")
