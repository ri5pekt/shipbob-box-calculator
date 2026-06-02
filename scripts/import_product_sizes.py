"""
Import product dimensions from Particle_Product_Database_Export.xlsx
and merge into data/products.json.
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_PATH = ROOT / "data" / "products.json"
DEFAULT_XLSX = Path.home() / "Downloads" / "Particle_Product_Database_Export.xlsx"

# Excel product name -> products.json title
NAME_ALIASES: dict[str, str] = {
    "particle face cream": "Particle Face Cream",
    "face wash": "Particle Face Wash",
    "neck cream": "Particle Neck Cream",
    "anti gray serum": "Particle Anti-Gray Serum",
    "shaving cream": "Particle 43 Anti-Aging Shaving Gel",
    "hand cream": "Particle Hand Cream",
    "lip balm": "Particle Lip Balm",
    "gravite": "Particle Gravité",
    "varros": "Particle Varros",
    "face mask": "Particle Face Mask",
    "shampoo": "Particle Hair Thickening Shampoo",
    "body wash": "Particle Body Wash",
    "hair revival kit": "Particle Hair Revival Kit",
    "beard oil": "Particle Beard Oil",
    "ab cream": "Particle Ab Firming Cream",
    "particle hair vitamin gummy": "Particle Hair Vitamin Gummies",
    "particle skin vitamin gummy": "Particle Skin Vitamin Gummies",
}


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def _is_number(value: object) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def round_dim(value: float) -> float:
    return round(value, 4)


def derive_dimensions(volume_cu_in: float, category: str) -> dict[str, float]:
    """Estimate L×W×H from volume when only cubic inches are available."""
    vol = max(volume_cu_in, 0.1)

    if category == "stick":
        w = max(vol ** (1 / 3) * 0.6, 0.5)
        h = vol / (w * w)
        return {"length": round_dim(w), "width": round_dim(w), "height": round_dim(h)}

    if category in ("bottle", "tube", "dropper"):
        w = vol ** (1 / 3) * 0.75
        h = vol / (w * w * 1.1)
        return {"length": round_dim(w * 1.1), "width": round_dim(w), "height": round_dim(h)}

    if category in ("kit", "bundle"):
        side = vol ** (1 / 3)
        return {
            "length": round_dim(side * 1.3),
            "width": round_dim(side),
            "height": round_dim(vol / (side * side * 1.3)),
        }

    # jar, supplement, default — roughly cubic
    side = vol ** (1 / 3)
    return {"length": round_dim(side), "width": round_dim(side), "height": round_dim(side)}


def parse_product_database(xlsx_path: Path) -> list[dict]:
    df = pd.read_excel(xlsx_path, sheet_name="Product Database", header=None)
    records: list[dict] = []

    for _, row in df.iterrows():
        num = row.iloc[0]
        if pd.isna(num) or not str(num).strip().isdigit():
            continue

        sku = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else None
        brand = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else None
        name = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else None
        if not name:
            continue

        case_qty = row.iloc[5] if pd.notna(row.iloc[5]) else None
        dim_l = float(row.iloc[6]) if pd.notna(row.iloc[6]) else None
        dim_w = float(row.iloc[7]) if pd.notna(row.iloc[7]) else None
        dim_h = float(row.iloc[8]) if pd.notna(row.iloc[8]) else None
        dim_type = str(row.iloc[9]).strip() if pd.notna(row.iloc[9]) else None
        unit_vol = float(row.iloc[10]) if pd.notna(row.iloc[10]) else None
        unit_wt_lbs = float(row.iloc[11]) if pd.notna(row.iloc[11]) else None

        records.append(
            {
                "inventory_sku": None if sku and sku.startswith("⚠") else sku,
                "brand": brand,
                "name": name,
                "case_qty": int(case_qty) if case_qty is not None else None,
                "dim_l": dim_l,
                "dim_w": dim_w,
                "dim_h": dim_h,
                "dim_type": dim_type,
                "unit_volume_cu_in": unit_vol,
                "unit_weight_lbs": unit_wt_lbs,
            }
        )

    return records


def parse_unit_reference(xlsx_path: Path) -> dict[str, dict]:
    df = pd.read_excel(xlsx_path, sheet_name="Unit Size Reference", header=None)
    by_name: dict[str, dict] = {}

    for _, row in df.iterrows():
        sku = row.iloc[0]
        name = row.iloc[1]
        if pd.isna(name) or str(name).startswith("⚠ TBD ="):
            continue
        if pd.isna(sku) or not isinstance(name, str):
            continue
        if str(sku).strip().lower() in ("sku", "#"):
            continue

        unit_vol_raw = row.iloc[3]
        unit_vol = float(unit_vol_raw) if pd.notna(unit_vol_raw) and _is_number(unit_vol_raw) else None

        by_name[normalize_name(name)] = {
            "inventory_sku": None if str(sku).startswith("⚠") else str(sku).strip(),
            "unit_volume_cu_in": unit_vol,
            "unit_weight_lbs": float(row.iloc[4]) if pd.notna(row.iloc[4]) and _is_number(row.iloc[4]) else None,
            "unit_weight_oz": float(row.iloc[5]) if pd.notna(row.iloc[5]) and _is_number(row.iloc[5]) else None,
            "dim_source": str(row.iloc[9]).strip() if pd.notna(row.iloc[9]) else None,
            "notes": str(row.iloc[10]).strip() if pd.notna(row.iloc[10]) else None,
        }

    return by_name


def build_xlsx_lookup(xlsx_path: Path) -> dict[str, dict]:
    db_records = parse_product_database(xlsx_path)
    unit_ref = parse_unit_reference(xlsx_path)
    lookup: dict[str, dict] = {}

    for record in db_records:
        key = normalize_name(record["name"])
        merged = {**record, **unit_ref.get(key, {})}
        lookup[key] = merged

    return lookup


def resolve_title(excel_name: str) -> str | None:
    key = normalize_name(excel_name)
    return NAME_ALIASES.get(key)


def merge_into_products(xlsx_path: Path) -> tuple[list[dict], list[str], list[str]]:
    lookup = build_xlsx_lookup(xlsx_path)
    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    products_by_title = {p["title"]: p for p in products}

    matched: list[str] = []
    unmatched_xlsx: list[str] = []

    for excel_key, xlsx_row in lookup.items():
        title = resolve_title(xlsx_row["name"])
        if not title:
            unmatched_xlsx.append(xlsx_row["name"])
            continue

        product = products_by_title.get(title)
        if not product:
            unmatched_xlsx.append(xlsx_row["name"])
            continue

        category = product.get("category", "jar")
        dim_type = xlsx_row.get("dim_type")

        if dim_type == "Unit" and all(xlsx_row.get(k) for k in ("dim_l", "dim_w", "dim_h")):
            product["dimensions"] = {
                "length": round_dim(xlsx_row["dim_l"]),
                "width": round_dim(xlsx_row["dim_w"]),
                "height": round_dim(xlsx_row["dim_h"]),
            }
            product["dimensions_source"] = "xlsx_unit"
        elif xlsx_row.get("unit_volume_cu_in"):
            product["dimensions"] = derive_dimensions(xlsx_row["unit_volume_cu_in"], category)
            product["dimensions_source"] = "xlsx_volume_derived"

        product["unit_volume_cu_in"] = xlsx_row.get("unit_volume_cu_in")
        product["unit_weight_lbs"] = xlsx_row.get("unit_weight_lbs")
        product["inventory_sku"] = xlsx_row.get("inventory_sku")
        product["dim_type"] = dim_type
        product["dim_source"] = xlsx_row.get("dim_source") or dim_type

        matched.append(title)

    still_placeholder = [
        p["title"]
        for p in products
        if p.get("dimensions_source", "placeholder") == "placeholder"
        or "dimensions_source" not in p
    ]

    for p in products:
        if "dimensions_source" not in p:
            p["dimensions_source"] = "placeholder"

    PRODUCTS_PATH.write_text(json.dumps(products, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return products, matched, still_placeholder


def main() -> int:
    xlsx_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_XLSX
    if not xlsx_path.exists():
        print(f"File not found: {xlsx_path}", file=sys.stderr)
        return 1

    products, matched, still_placeholder = merge_into_products(xlsx_path)

    print(f"Updated {len(matched)} products from {xlsx_path.name}")
    print("\nMatched:")
    for title in sorted(matched):
        p = next(x for x in products if x["title"] == title)
        d = p["dimensions"]
        src = p["dimensions_source"]
        print(f"  {title}: {d['length']}×{d['width']}×{d['height']} in ({src})")

    if still_placeholder:
        print(f"\nStill using placeholder dimensions ({len(still_placeholder)}):")
        for title in still_placeholder:
            print(f"  {title}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
