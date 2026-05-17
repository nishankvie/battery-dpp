"""
odoo_client.py — Odoo ERP integration for Battery DPP Platform
Uses Python's built-in xmlrpc.client. No extra dependencies required.
"""
import xmlrpc.client

# ─── Battery → Odoo product name mapping ──────────────────────────────────────
BATTERY_ODOO_MAP = {
    "Battery A": ("volvo",       "ex90_nmc811_111kwh"),
    "Battery B": ("bmw",         "ix_nmc712_105kwh"),
    "Battery C": ("generic_oem", "lfp_80kwh"),
}

# Level 2 Physical Sensor Verification status per manufacturer
PHYSICAL_VERIFIED = {
    "volvo":       True,
    "bmw":         True,
    "generic_oem": False,
}


def _creds():
    """Return (url, db, username, password). Tries st.secrets first, falls back to hardcoded."""
    try:
        import streamlit as st
        cfg = st.secrets["odoo"]
        return cfg["url"], cfg["db"], cfg["username"], cfg["password"]
    except Exception:
        return (
            "https://vericell.odoo.com",
            "vericell",
            "nishankvie@gmail.com",
            "965c0baac1e41eec4e215d1f97a667c346d2cfab",
        )


def connect():
    """Authenticate with Odoo. Returns (uid, models_proxy) or raises on failure."""
    url, db, username, password = _creds()
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})
    if not uid:
        raise ConnectionError("Odoo authentication failed — check credentials.")
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    return uid, models


def fetch_products():
    """
    Pull all products from Odoo. Returns list of {id, name} dicts.
    Returns [] on any connection or auth failure (graceful degradation).
    """
    try:
        url, db, username, password = _creds()
        uid, models = connect()
        products = models.execute_kw(
            db, uid, password,
            "product.product", "search_read",
            [[]],
            {"fields": ["id", "name"]},
        )
        # Filter to only products we know about
        known = set(BATTERY_ODOO_MAP.keys())
        return [p for p in products if p["name"] in known]
    except Exception as e:
        print(f"[odoo_client] fetch_products failed: {e}")
        return []


def push_verification_result(product_id: int, model_id: str, score: float, decision: str) -> bool:
    """Write verification result to an Odoo product's description field."""
    try:
        url, db, username, password = _creds()
        uid, models = connect()
        models.execute_kw(
            db, uid, password,
            "product.product", "write",
            [[product_id], {
                "description": f"{model_id} | Trust Score: {score:.1f}/100 | {decision} | VeriCell DPP"
            }],
        )
        return True
    except Exception as e:
        print(f"[odoo_client] push_verification_result failed: {e}")
        return False


def push_status_update(product_id: int, status: str) -> bool:
    """Write a technician status update to an Odoo product's description field."""
    try:
        url, db, username, password = _creds()
        uid, models = connect()
        models.execute_kw(
            db, uid, password,
            "product.product", "write",
            [[product_id], {
                "description": f"Technician Status: {status} | Updated via VeriCell DPP Platform"
            }],
        )
        return True
    except Exception as e:
        print(f"[odoo_client] push_status_update failed: {e}")
        return False


# ─── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Odoo connection...")

    products = fetch_products()
    if products:
        print(f"✅ fetch_products: {products}")
    else:
        print("❌ fetch_products returned empty — check connection")
        exit(1)

    # Test push_verification_result on first known product
    p = products[0]
    mfr_id, model_id = BATTERY_ODOO_MAP[p["name"]]
    ok = push_verification_result(p["id"], model_id, 71.5, "REVIEW")
    print(f"{'✅' if ok else '❌'} push_verification_result on product {p['id']} ({p['name']})")

    # Test push_status_update
    ok2 = push_status_update(p["id"], "Operational")
    print(f"{'✅' if ok2 else '❌'} push_status_update on product {p['id']}")

    print("Done.")
