"""Order request form: validation + storage. Rules come from data/shop.json, not from the browser."""
import json
import os
import re
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

from shop import SHOP

# Serverless hosts (Vercel) have a read-only project folder; only /tmp is writable, and it is temporary.
ORDERS_FILE = Path("/tmp/orders.jsonl") if os.getenv("VERCEL") else Path(__file__).parent / "data" / "orders.jsonl"
TYPES = {
    "custom_bouquet": "Custom bouquet",
    "gift_box": "Bakery gift box",
    "event": "Large event order",
}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def min_days(kind):
    if kind == "event":
        return SHOP["events"]["notice_days"]
    hours = SHOP["gift_boxes"]["notice_hours"] if kind == "gift_box" else SHOP["custom_bouquet"]["notice_hours"]
    return hours // 24


def validate(form, today=None):
    """Returns (clean_dict, errors_list)."""
    today = today or date.today()
    f = {k: (form.get(k) or "").strip() for k in
         ("type", "name", "email", "phone", "date", "budget", "box_size", "items", "fulfilment", "address", "notes", "website")}
    errors = []
    if f["website"]:  # honeypot field: real people leave it empty
        return f, ["Something went wrong. Please try again."]
    if f["type"] not in TYPES:
        errors.append("Please choose what you would like to order.")
    if len(f["name"]) < 2:
        errors.append("Please enter your name.")
    if not EMAIL_RE.match(f["email"]):
        errors.append("Please enter a valid email address, since we confirm every request by email.")
    try:
        wanted = datetime.strptime(f["date"], "%Y-%m-%d").date()
        need = min_days(f["type"]) if f["type"] in TYPES else 2
        if wanted < today + timedelta(days=need):
            errors.append(f"For this kind of order we need at least {need} days' notice. "
                          f"The earliest date is {(today + timedelta(days=need)).strftime('%d %b %Y')}.")
    except ValueError:
        errors.append("Please choose the date you need it.")
    if f["type"] == "custom_bouquet":
        floor = SHOP["custom_bouquet"]["from_price"]
        if not f["budget"].isdigit() or int(f["budget"]) < floor:
            errors.append(f"Custom bouquets start from a {floor} CZK budget.")
        if f["fulfilment"] not in ("pickup", "delivery"):
            errors.append("Please choose pickup or delivery.")
        if f["fulfilment"] == "delivery" and len(f["address"]) < 6:
            errors.append("Please enter a Prague delivery address. We deliver in Prague only.")
    if f["type"] == "gift_box" and f["box_size"] not in [b["name"] for b in SHOP["gift_boxes"]["sizes"]]:
        errors.append("Please choose a gift box size.")
    if f["type"] == "event":
        mn = SHOP["events"]["min_items"]
        if not f["items"].isdigit() or int(f["items"]) < mn:
            errors.append(f"Large event orders start at {mn} items. For smaller orders, just visit us or order a gift box.")
    if len(f["notes"]) > 1000:
        errors.append("Notes are too long (max 1000 characters).")
    return f, errors


def save(clean):
    ref = uuid.uuid4().hex[:8].upper()
    rec = {"ref": ref, "received": datetime.now().isoformat(timespec="seconds"),
           **{k: v for k, v in clean.items() if k != "website"}}
    ORDERS_FILE.parent.mkdir(exist_ok=True)
    with ORDERS_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return ref
