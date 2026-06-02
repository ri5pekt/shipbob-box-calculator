import json
from pathlib import Path

products = json.loads(Path("data/products.json").read_text(encoding="utf-8"))
boxes = json.loads(Path("data/boxes.json").read_text(encoding="utf-8"))

neck = next(p for p in products if "Neck" in p["title"])
large = boxes[1]

PADDING = 0.1
d = neck["dimensions"]
b = large["dimensions"]

bL = b["length"] - PADDING
bW = b["width"] - PADDING
bH = b["height"] - PADDING

max_item = max(d["length"], d["width"], d["height"])

print("=== Particle Neck Cream ===")
print(f"  dimensions: {d['length']} x {d['width']} x {d['height']} in")
print(f"  source: {neck.get('dimensions_source')}")
print(f"  max dimension: {max_item:.4f} in")
print()
print("=== Large Shipper ===")
print(f"  inner: {b['length']} x {b['width']} x {b['height']} in")
print(f"  padded (–0.1): {bL:.4f} x {bW:.4f} x {bH:.4f} in")
print(f"  shortest padded side: {bH:.4f} in")
print()
print(f"Gap: {bH - max_item:.4f} in  (negative = doesn't fit)")
print(f"Fits WITHOUT padding? {max_item <= b['height']}")
print(f"Fits WITH 0.1 in padding? {max_item <= bH}")
print()
print("=== Root cause ===")
print("Neck Cream is volume-derived (cube root of case volume / qty).")
print("A jar that is 3.08 x 3.08 x 3.08 in barely exceeds the padded")
print("box height of 3.05 in. Without padding it fits fine.")
