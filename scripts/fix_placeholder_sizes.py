"""Cap bundle placeholder dimensions to fit inside the large shipper inner specs."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_PATH = ROOT / "data" / "products.json"
BOXES_PATH = ROOT / "data" / "boxes.json"

# Large shipper inner (in) — logistics: 22 × 17 × 8 cm
LARGE_INNER = [8.6614, 6.6929, 3.1496]

# Realistic bundle sizes (L × W × H in), all fit inside large shipper when sorted
BUNDLE_DIMS = {
    "Starter Bundle": (7.5, 5.5, 2.5),
    "Dark Spot Remover Set": (7.5, 5.5, 2.5),
    "The Smooth Skin Set": (7.5, 5.5, 2.5),
    "Particle Gravité Bundle": (8.0, 6.0, 2.8),
    "Particle Lady Killer Kit": (8.0, 6.0, 2.8),
    "Power Shower Set": (8.0, 6.0, 2.8),
    "Hair Growth Bundle": (8.0, 6.0, 2.8),
    "Bold Moves Bundle": (8.0, 6.0, 2.8),
    "Head Turner Set": (8.0, 6.0, 2.8),
    "Essential Bundle": (8.5, 6.5, 3.0),
    "Advanced Bundle": (8.5, 6.5, 3.0),
    "Particle Golfer's Bundle": (8.5, 6.5, 3.0),
    "Particle Father's Day Gift Bundle": (8.5, 6.5, 3.0),
    "Men's Gift Bundle": (8.5, 6.5, 3.0),
}

# Volume-derived single products — use realistic unit sizes (in)
UNIT_FIXES = {
    "Particle Gravité": (2.0, 2.0, 4.5),
    "Particle Varros": (2.0, 2.0, 4.5),
    "Particle Face Cream": (2.5, 2.5, 2.5),
}


def sorted_dims(d):
    return sorted(d, reverse=True)


def fits_large(d):
    s = sorted_dims([d["length"], d["width"], d["height"]])
    l = sorted_dims(LARGE_INNER)
    return s[0] <= l[0] and s[1] <= l[1] and s[2] <= l[2]


def main():
    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    updated = 0

    for p in products:
        title = p["title"]

        if title in BUNDLE_DIMS and p.get("dimensions_source") == "placeholder":
            l, w, h = BUNDLE_DIMS[title]
            p["dimensions"] = {"length": l, "width": w, "height": h}
            p["dimensions_source"] = "placeholder_capped_for_shipper"
            updated += 1

        if title in UNIT_FIXES:
            l, w, h = UNIT_FIXES[title]
            p["dimensions"] = {"length": l, "width": w, "height": h}
            p["dimensions_source"] = "manual_unit_estimate"
            updated += 1

    PRODUCTS_PATH.write_text(json.dumps(products, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    still_bad = [p["title"] for p in products if not fits_large(p["dimensions"])]
    print(f"Updated {updated} products")
    if still_bad:
        print(f"Still exceed large shipper ({len(still_bad)}):")
        for t in still_bad:
            print(f"  {t}")
    else:
        print("All products fit large shipper (any rotation).")


if __name__ == "__main__":
    main()
