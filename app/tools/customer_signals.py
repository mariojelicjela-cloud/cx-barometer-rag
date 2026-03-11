import json
from pathlib import Path


def get_customer_signals(customer_id: str):
    path = Path("data/seed/customer_signals.json")

    if not path.exists():
        return {
            "customer_id": customer_id,
            "error": "customer_signals.json not found"
        }

    data = json.loads(path.read_text(encoding="utf-8"))

    for item in data:
        if item.get("customer_id") == customer_id:
            return item

    return {
        "customer_id": customer_id,
        "error": "Customer not found"
    }