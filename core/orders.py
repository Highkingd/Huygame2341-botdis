import os, json, uuid
from .logger import log

order_file = "orders.json"
orders = {}
if os.path.exists(order_file):
    try:
        with open(order_file, "r", encoding="utf-8") as f:
            orders = json.load(f)
    except json.JSONDecodeError:
        log("⚠️ Lỗi đọc orders.json, khởi tạo lại dữ liệu")
        orders = {}

for o in orders.values():
    o.setdefault("da_nhac_het_gio", False)
    o.setdefault("qua_han", False)

def save_orders():
    with open(order_file, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=4, ensure_ascii=False)

def generate_order_id() -> str:
    return str(uuid.uuid4())[:8]
