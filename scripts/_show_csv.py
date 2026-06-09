import sys, csv
sys.stdout.reconfigure(encoding='utf-8')
with open(r'c:\Users\denis_particleformen\Desktop\Cursor Projects\shipbob-boxes-calculator\data\shipbob_sizes.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
print(f'Total rows in CSV: {len(rows)}\n')
no_dims = []
for r in rows:
    has = r['length_in'] or r['width_in']
    flag = '' if has else '  ← NO DIMS'
    name = r['name']
    print(f"{name[:50]:50}  L={r['length_in']:6}  W={r['width_in']:6}  H={r['height_in']:6}{flag}")
    if not has:
        no_dims.append(name)

print()
print(f'Products WITHOUT dimensions: {len(no_dims)}')
for n in no_dims:
    print(f'  - {n}')
