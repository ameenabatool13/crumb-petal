"""Single source of truth for the shop. Pages, the chatbot and the info sheet all read data/shop.json."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
SHOP = json.loads((DATA_DIR / "shop.json").read_text(encoding="utf-8"))


def _flatten():
    items = []
    for section in ("bakery", "drinks", "flowers"):
        for cat in SHOP[section]:
            for it in cat["items"]:
                items.append({**it, "section": section, "category": cat["category"],
                              "espresso": bool(cat.get("espresso"))})
    return items


ITEMS = _flatten()


def hours_text():
    return ", ".join(f"{h['days']} {h['open']}-{h['close']}" for h in SHOP["hours"])


def _item_line(i):
    s = f"{i['name']} {i['price']}"
    if i.get("unit"):
        s += f" {i['unit']}"
    notes = [n for k, n in (("gf", "gluten-free"), ("lf", "lactose-free"), ("seasonal", "seasonal")) if i.get(k)]
    return s + (f" ({', '.join(notes)})" if notes else "")


def _cats(cats):
    return "\n".join(f"{c['category']}: " + "; ".join(_item_line(i) for i in c["items"]) + "." for c in cats)


def info_sheet():
    s, d = SHOP, SHOP["delivery"]
    gf = [i for i in ITEMS if i.get("gf")]
    lf = [i for i in ITEMS if i.get("lf")]
    boxes = "; ".join(f"{b['name']} ({b['count']} items) {b['price']}" for b in s["gift_boxes"]["sizes"])
    return f"""# {s['name']} info sheet (FICTIONAL shop, for a course project)

## Basics
- Bakery, coffee bar and flower studio. Address: {s['address']} (fictional).
- Hours: {hours_text()}.
- Contact: {s['email']}, {s['phone']}.
- Payment: {s['payment']}
- Tables: {s['tables']}.
- Website: an order request form for custom bouquets, bakery gift boxes and large orders. We confirm every request by email.

## Bakery (prices in CZK)
{_cats(s['bakery'])}

## Coffee and tea
{_cats(s['drinks'])}
{s['lactose_free_milk']}

## Dietary
- Gluten-free items: {' and '.join(f"{i['name']} ({i['price']})" for i in gf)} only.
- Lactose-free items: {lf[0]['name']}, and any espresso drink made with lactose-free milk.
- {s['dietary_notes'][0]}
- {s['dietary_notes'][1]}

## Flowers
{_cats(s['flowers'])}
Custom bouquets: from {s['custom_bouquet']['from_price']} CZK budget, order at least {s['custom_bouquet']['notice_hours']} hours ahead by email or the order request form.

## Delivery (flowers)
- {d['area']}. Next-day delivery. Order by {d['cutoff']} for delivery the next day.
- Fee {d['fee']} CZK; free for orders over {d['free_over']} CZK.
- {d['notes'][0]}
- {d['notes'][1]}

## Special orders
- Bakery gift boxes: {boxes}. Order {s['gift_boxes']['notice_hours']} hours ahead.
- Large event orders ({s['events']['min_items']}+ items): email at least {s['events']['notice_days']} days ahead for a quote.

## Not covered by this sheet
{', '.join(s['not_covered'])}. Holiday opening hours, vegan options and ingredient lists are not covered either.
"""


if __name__ == "__main__":
    (DATA_DIR / "info_sheet.md").write_text(info_sheet(), encoding="utf-8")
    print("wrote data/info_sheet.md")
