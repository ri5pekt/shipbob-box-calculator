import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
products = json.loads((ROOT / "data/products.json").read_text(encoding="utf-8"))
boxes = json.loads((ROOT / "data/boxes.json").read_text(encoding="utf-8"))

def sorted_dims(d):
    return sorted([d["length"], d["width"], d["height"]], reverse=True)

large = boxes[1]["dimensions"]
small = boxes[0]["dimensions"]
large_s = sorted_dims(large)
small_s = sorted_dims(small)

print("Large shipper (sorted L/M/S):", [round(x, 2) for x in large_s])
print("Small shipper (sorted L/M/S):", [round(x, 2) for x in small_s])
print()

def fits_in_box(prod, box_sorted):
    ps = sorted_dims(prod["dimensions"])
    return ps[0] <= box_sorted[0] and ps[1] <= box_sorted[1] and ps[2] <= box_sorted[2]

oversized_large = []
oversized_small = []
for p in products:
    if not fits_in_box(p, large_s):
        oversized_large.append(p)
    if not fits_in_box(p, small_s):
        oversized_small.append(p)

print(f"Products NOT fitting large shipper ({len(oversized_large)}):")
for p in sorted(oversized_large, key=lambda x: max(sorted_dims(x["dimensions"])), reverse=True):
    d = p["dimensions"]
    ps = sorted_dims(d)
    print(f"  {p['title'][:45]:45} {d['length']:.2f}x{d['width']:.2f}x{d['height']:.2f}  sorted={[round(x,2) for x in ps]}  src={p.get('dimensions_source','?')}")
