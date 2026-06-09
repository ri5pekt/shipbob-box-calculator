import sys, json
sys.stdout.reconfigure(encoding='utf-8')
with open(r'c:\Users\denis_particleformen\Desktop\Cursor Projects\shipbob-boxes-calculator\data\products.json', encoding='utf-8') as f:
    products = json.load(f)

print("=== Individual products WITHOUT ShipBob ID ===")
for p in products:
    if not p.get('components') and not p.get('shipbob_inventory_id'):
        print(f"  {p['title']}")

print()
print("=== Individual products WITH ShipBob ID ===")
for p in products:
    if not p.get('components') and p.get('shipbob_inventory_id'):
        print(f"  {p['shipbob_inventory_id']:12}  {p['title']}")
