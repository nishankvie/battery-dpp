import xmlrpc.client
from engine.verification_engine import run_full_verification
from engine.verification_engine import run_full_verification, load_battery
BATTERY_MAPPING = {
    "Battery A": ("volvo", "ex90_nmc811_111kwh"),
    "Battery B": ("bmw", "ix_nmc712_105kwh"),
    "Battery C": ("generic_oem", "lfp_80kwh"),
}
url = "https://vericell.odoo.com"
db = "vericell"
username = "nishankvie@gmail.com"
password = "965c0baac1e41eec4e215d1f97a667c346d2cfab"


# Step 1: authenticate
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})

if not uid:
    print("❌ Connection failed")
    exit()

print("✅ Connected! UID:", uid)

# Step 2: CREATE models (THIS WAS MISSING)
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

# Step 3: fetch products
products = models.execute_kw(
    db, uid, password,
    'product.product', 'search_read',
    [[]],
    {'fields': ['id', 'name']}
)

print("📦 Products:", products)

# Pick first product

product_id = products[0]['id']

# Update description field

models.execute_kw(

    db, uid, password,

    'product.product', 'write',

    [[product_id], {

        'description': 'Updated from Python: TEST SUCCESS'

    }]

)

print("✅ Product updated successfully")
import json

for p in products:

    name = p["name"]

    if name not in BATTERY_MAPPING:
        print(f"⚠️ No mapping for {name}")
        continue

    manufacturer_id, model_id = BATTERY_MAPPING[name]

    # LOAD REAL JSON
    battery_data = load_battery(manufacturer_id, model_id)

    # RUN ENGINE
    report = run_full_verification(battery_data)

    score = report.trust_score

    # DECISION
    if score > 85:
        decision = "APPROVE"
    elif score > 65:
        decision = "REVIEW"
    else:
        decision = "BLOCK"

    # UPDATE ERP
    models.execute_kw(
        db, uid, password,
        'product.product', 'write',
        [[p['id']], {
            'description': f"{model_id} | Score: {score} | {decision}"
        }]
    )

    print(f"✅ Updated {name}")


