import json
from pathlib import Path

products = json.loads(Path("data/products.json").read_text(encoding="utf-8"))
boxes    = json.loads(Path("data/boxes.json").read_text(encoding="utf-8"))

PADDING = 0.03

def sorted_desc(d):
    return sorted([d["length"], d["width"], d["height"]], reverse=True)

def fits(item_d, box_d):
    i = sorted([item_d["length"], item_d["width"], item_d["height"]])
    b = sorted([box_d["length"] - PADDING, box_d["width"] - PADDING, box_d["height"] - PADDING])
    return i[0] <= b[0] and i[1] <= b[1] and i[2] <= b[2]

small = boxes[0]
large = boxes[1]

print("Source legend:")
print("  xlsx_unit            = exact unit dims from XLS")
print("  xlsx_volume_derived  = estimated from case volume (XLS has no unit dims)")
print("  placeholder          = not in XLS at all, using original guesses")
print()

print(f"{'Product':<44} {'Source':<24} {'L x W x H (in)':<22} FitsSmall FitsLarge")
print("-" * 110)

for p in sorted(products, key=lambda x: (x["category"] in ("bundle","kit"), x["title"])):
    d  = p["dimensions"]
    fs = fits(d, small["dimensions"])
    fl = fits(d, large["dimensions"])
    src = p.get("dimensions_source", "?")
    dims = f"{d['length']:.2f}x{d['width']:.2f}x{d['height']:.2f}"
    tag_s = "YES" if fs else "NO "
    tag_l = "YES" if fl else "NO "
    flag = "  <-- check" if not fl else ""
    print(f"  {p['title']:<42} {src:<24} {dims:<22} {tag_s}       {tag_l}{flag}")
