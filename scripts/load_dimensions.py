import openpyxl, json

EXCEL_MAP = {
    'BODY WASH':   '636665869678',
    'SHAMPOO':     '636665869661',
    'FACE CREAM':  '751889384926',
    'BEARD OIL':   '860005339723',
    'DEODORANT':   '860012469710',
    'HAND CREAM':  '00860014497216',
    'GRAVITE':     '860005339785',
    'VARROS':      '00860012469765',
    'NECK CREAM':  '860005339778',
    'EYE CREAM':   '00860012469796',
    'SHAVING GEL': '00860012469772',
    'AB CREAM':    '860010338421',
    'ANTI GRAY':   '860012469703',
    'FACE WASH':   '636665869647',
}

wb = openpyxl.load_workbook(r'C:\Users\denis_particleformen\Downloads\Product_Dimensions.xlsx')
ws = wb.active

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

by_sku = {p['sku']: i for i, p in enumerate(products)}
updated = []

for row in ws.iter_rows(min_row=2, values_only=True):
    name, length, width, height = row
    key = (name or '').strip().upper()
    sku = EXCEL_MAP.get(key)
    if not sku or sku not in by_sku:
        print('  SKIP:', name)
        continue
    i = by_sku[sku]
    old = products[i]['dimensions']
    products[i]['dimensions'] = {'length': length, 'width': width, 'height': height}
    title = products[i]['title']
    updated.append((title, old, products[i]['dimensions']))

with open('data/products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

print(f'Updated {len(updated)} products:')
for title, old, new in updated:
    print(f'  {title}')
    print(f'    old: {old}')
    print(f'    new: {new}')
