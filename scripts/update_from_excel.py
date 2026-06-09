import sys, json, openpyxl
sys.stdout.reconfigure(encoding='utf-8')

BASE = r'c:\Users\denis_particleformen\Desktop\Cursor Projects\shipbob-boxes-calculator'
XLSX = r'C:\Users\denis_particleformen\Downloads\SINGLE UNIT DIMS.xlsx'

# ── Load Excel ────────────────────────────────────────────────────────────────
wb  = openpyxl.load_workbook(XLSX)
ws  = wb.active

# Columns: 0=#, 1=SKU, 2=Name, 3=CaseQty, 4=H(in), 5=W(in), 6=L(in), 7=Wt(lbs)
excel_products = []
for row in ws.iter_rows(values_only=True):
    num = row[0]
    if not isinstance(num, int):
        continue                    # skip header / section rows
    name   = str(row[2] or '').strip()
    h, w, l = row[4], row[5], row[6]
    wt      = row[7]
    if not (h and w and l):
        continue                    # skip packaging / items without dims
    excel_products.append({
        'name': name,
        'height': float(h),   # Excel H → our 'length' (tallest dim)
        'width':  float(w),   # Excel W → our 'width'
        'length': float(l),   # Excel L → our 'height'
        'weight': float(wt) if wt else None,
    })
    print(f"  Excel: {name:45} H={h} W={w} L={l}")

# ── Name-matching map: Excel name → keywords to match against product titles ──
NAME_MAP = {
    'Particle Face Cream':          'Face Cream',
    'Face Wash':                    'Face Wash',
    'Neck Cream':                   'Neck Cream',
    'Anti Gray Serum':              'Anti-Gray Serum',
    'Shaving Cream':                'Shaving Gel',
    'Hand Cream':                   'Hand Cream',
    'Lip Balm':                     'Lip Balm',
    'Gravite':                      'Gravité',
    'Varros':                       'Varros',
    'Face Mask':                    'Face Mask',
    'Shampoo':                      'Shampoo',
    'Body Wash':                    'Body Wash',
    'Hair Revival Kit':             'Hair Revival Kit',
    'Beard Oil':                    'Beard Oil',
    'Scar Gel':                     'Scar',
    'AB Cream':                     'Ab Firming',
    'Sunscreen':                    'Face Shield',
    'Particle Hair Vitamin Gummy':  'Hair Vitamin',
    'Particle Skin Vitamin Gummy':  'Skin Vitamin',
    'Scalp Massager':               'Scalp',
    'Instant Eye Cream':            'Eye',
    'Comb':                         'Comb',
    'Nose Trimmer':                 'Nose',
    'Infinite Male':                'Infinite Male',
    'Deodorant':                    'Deodorant',
}

# ── Load products.json ────────────────────────────────────────────────────────
with open(f'{BASE}/data/products.json', encoding='utf-8') as f:
    products = json.load(f)

# ── Apply updates ─────────────────────────────────────────────────────────────
updated = 0
not_found = []

for ep in excel_products:
    keyword = NAME_MAP.get(ep['name'])
    if not keyword:
        not_found.append(f"No mapping for: {ep['name']}")
        continue

    match = next(
        (p for p in products
         if keyword.lower() in p['title'].lower() and not p.get('components')),
        None
    )

    if not match:
        not_found.append(f"No product found for: {ep['name']} (keyword={keyword})")
        continue

    old = match.get('dimensions', {})
    # Excel convention: H=tallest, W=width, L=depth
    # Our convention:  length=tallest, width=width, height=depth
    match['dimensions'] = {
        'length': round(ep['height'], 4),
        'width':  round(ep['width'],  4),
        'height': round(ep['length'], 4),
    }
    if ep['weight'] is not None:
        match['unit_weight_lbs'] = round(ep['weight'], 4)

    updated += 1
    print(f"  UPDATED {match['title']}")
    print(f"    old: {old}")
    print(f"    new: {match['dimensions']}")

# ── Save ──────────────────────────────────────────────────────────────────────
with open(f'{BASE}/data/products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

print(f"\n✓ Updated {updated} products")
if not_found:
    print("\nNot matched:")
    for m in not_found:
        print(f"  - {m}")
