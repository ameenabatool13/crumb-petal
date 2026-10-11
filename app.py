"""Crumb & Petal: Flask app. Run with `python app.py`, then open http://127.0.0.1:5000"""
import logging
import os
import time
from collections import defaultdict, deque
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()  # reads .env (optional: the site works without it)

import chatbot  # noqa: E402  (after load_dotenv so it sees the env)
import orders  # noqa: E402
from shop import ITEMS, SHOP, hours_text, info_sheet  # noqa: E402

logging.basicConfig(level=logging.INFO)
# Static files live in public/ because Vercel only serves static assets from there. URLs stay /static/...
app = Flask(__name__, static_folder="public/static")
if os.getenv("TRUST_PROXY", "").strip() in ("1", "true", "yes") or os.getenv("VERCEL"):
    # Behind a host's proxy, request.remote_addr is the proxy, not the visitor. Without this every
    # visitor would share ONE rate-limit bucket. Only enable behind a proxy you trust (spoofable otherwise).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # forms and chat messages are tiny

# Keep the info sheet file in sync with data/shop.json every time the app starts.
try:
    (Path(__file__).parent / "data" / "info_sheet.md").write_text(info_sheet(), encoding="utf-8")
except OSError:  # read-only filesystem on serverless hosts; the sheet is also built in memory when needed
    logging.warning("Could not write data/info_sheet.md (read-only filesystem); continuing")

_hits = defaultdict(deque)


RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MIN", "30"))


def rate_limited(ip, limit=None, window=60):
    """Tiny in-memory limiter so nobody can burn your API credit through /chat."""
    limit = RATE_LIMIT if limit is None else limit
    now, q = time.time(), _hits[ip]
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= limit:
        return True
    q.append(now)
    return False


@app.context_processor
def inject():
    return {"shop": SHOP, "hours": hours_text(), "chat_mode": chatbot.current_mode()}


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/bakery")
def bakery():
    return render_template("menu.html", page="bakery", title="Bakery", categories=SHOP["bakery"],
                           intro="Baked at dawn, in small batches. Croissants, sourdough, cookies and macarons.",
                           note="Gift boxes and big orders need a little notice.", cta=("order", "Order a gift box or event order"))


@app.route("/coffee")
def coffee():
    return render_template("menu.html", page="coffee", title="Coffee & tea", categories=SHOP["drinks"],
                           intro="Espresso drinks poured slow, plus matcha and tea.",
                           note=SHOP["lactose_free_milk"], cta=None)


@app.route("/flowers")
def flowers():
    return render_template("flowers.html", categories=SHOP["flowers"], d=SHOP["delivery"])


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/gallery")
def gallery():
    folder = Path(app.static_folder) / "gallery"
    photos = sorted(p.name for p in folder.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
    return render_template("gallery.html", photos=photos)


@app.route("/order", methods=["GET", "POST"])
def order():
    if request.method == "POST":
        clean, errors = orders.validate(request.form)
        if errors:
            return render_template("order.html", errors=errors, f=clean, types=orders.TYPES, today=orders.date.today()), 400
        ref = orders.save(clean)
        return render_template("order_done.html", ref=ref, f=clean, kind=orders.TYPES[clean["type"]])
    pre = request.args.get("type", "")
    return render_template("order.html", errors=[], f={"type": pre if pre in orders.TYPES else ""},
                           types=orders.TYPES, today=orders.date.today())


@app.route("/chat", methods=["POST"])
def chat():
    if rate_limited(request.remote_addr or "?"):
        return jsonify(reply="You're asking very fast! Please wait a moment and try again.", mode="limited"), 429
    data = request.get_json(silent=True) or {}
    reply, mode = chatbot.answer(data.get("messages", []))
    return jsonify(reply=reply, mode=mode)


@app.route("/health")
def health():
    return jsonify(ok=True, chat_mode=chatbot.current_mode(), items=len(ITEMS))


if __name__ == "__main__":
    # debug is OFF by default (debug=True exposes an interactive console). Set FLASK_DEBUG=1 locally if you want it.
    app.run(debug=os.getenv("FLASK_DEBUG") == "1", port=int(os.getenv("PORT", 5000)))
