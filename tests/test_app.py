"""Smoke tests: every page loads, the chatbot works with NO api key, and the order rules are enforced.
Run:  python -m pytest -q"""
import os
import sys
from datetime import date, timedelta
from pathlib import Path

os.environ["CHAT_MODE"] = "local"
os.environ.pop("ANTHROPIC_API_KEY", None)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

import app as app_module  # noqa: E402
import orders  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(orders, "ORDERS_FILE", tmp_path / "orders.jsonl")
    app_module._hits.clear()
    return app_module.app.test_client()


@pytest.mark.parametrize("path", ["/", "/bakery", "/coffee", "/flowers", "/about", "/gallery", "/order", "/health"])
def test_pages_load(client, path):
    assert client.get(path).status_code == 200


def test_home_cards_link_to_own_pages(client):
    html = client.get("/").get_data(as_text=True)
    for p in ("/bakery", "/coffee", "/flowers"):
        assert f'class="path' in html and f'href="{p}"' in html


def test_menu_matches_info_sheet(client):
    sheet = Path(app_module.__file__).parent.joinpath("data", "info_sheet.md").read_text(encoding="utf-8")
    from shop import ITEMS
    for i in ITEMS:
        assert i["name"] in sheet, i["name"]
    page = client.get("/bakery").get_data(as_text=True)
    assert "Flourless almond cookie" in page and "Apple galette slice" in page


def test_chat_works_without_api_key(client):
    r = client.post("/chat", json={"messages": [{"role": "user", "content": "How much is a flat white?"}]})
    j = r.get_json()
    assert r.status_code == 200 and "85" in j["reply"] and j["mode"] == "local"


def test_chat_rejects_garbage_input(client):
    for body in ({}, {"messages": "x"}, {"messages": [{"role": "system", "content": "x"}]}, {"messages": [{"role": "user", "content": 5}]}):
        r = client.post("/chat", json=body)
        assert r.status_code == 200 and r.get_json()["reply"]


def test_chat_falls_back_when_claude_fails(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("CHAT_MODE", "auto")
    monkeypatch.setattr("chatbot.claude_answer", lambda m: (_ for _ in ()).throw(RuntimeError("no credit")))
    j = client.post("/chat", json={"messages": [{"role": "user", "content": "What are your hours?"}]}).get_json()
    assert j["mode"] == "local-fallback" and "8:00-19:00" in j["reply"]


def test_chat_rate_limit(client):
    for _ in range(30):
        client.post("/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert client.post("/chat", json={"messages": [{"role": "user", "content": "hi"}]}).status_code == 429


def good(**kw):
    d = {"type": "custom_bouquet", "name": "Eva", "email": "eva@example.com", "date": str(date.today() + timedelta(days=3)),
         "budget": "900", "fulfilment": "pickup"}
    d.update(kw)
    return d


def test_order_ok_and_saved(client):
    r = client.post("/order", data=good())
    assert r.status_code == 200 and "Thank you" in r.get_data(as_text=True)
    assert orders.ORDERS_FILE.read_text(encoding="utf-8").count("\n") == 1


@pytest.mark.parametrize("bad,why", [
    (dict(date=str(date.today() + timedelta(days=1))), "48"),
    (dict(budget="500"), "790"),
    (dict(fulfilment="delivery", address=""), "Prague"),
    (dict(email="nope"), "email"),
    (dict(type="event", items="10", date=str(date.today() + timedelta(days=6))), "20"),
    (dict(type="event", items="30", date=str(date.today() + timedelta(days=3))), "5 days"),
    (dict(type="gift_box", box_size="huge"), "size"),
    (dict(website="http://spam"), "wrong"),
])
def test_order_rules(client, bad, why):
    r = client.post("/order", data=good(**bad))
    assert r.status_code == 400 and why.lower() in r.get_data(as_text=True).lower()
    assert not orders.ORDERS_FILE.exists()


def test_chat_input_is_capped(client):
    from chatbot import clean_messages
    msgs = [{"role": "user", "content": "x" * 5000}] * 30
    out = clean_messages(msgs)
    assert len(out) <= 10 and all(len(m["content"]) <= 600 for m in out)


def test_oversized_body_rejected(client):
    r = client.post("/chat", data="x" * (70 * 1024), content_type="application/json")
    assert r.status_code == 413


def test_daily_claude_budget_falls_back_to_offline(client, monkeypatch):
    import chatbot
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("CHAT_MODE", "auto")
    monkeypatch.setattr(chatbot, "DAILY_CLAUDE_LIMIT", 1)
    monkeypatch.setattr(chatbot, "_budget", {"day": None, "n": 0})
    calls = []
    monkeypatch.setattr(chatbot, "claude_answer", lambda m: calls.append(1) or "claude says hi")
    body = {"messages": [{"role": "user", "content": "How much is a flat white?"}]}
    assert client.post("/chat", json=body).get_json()["mode"] == "claude"
    j = client.post("/chat", json=body).get_json()
    assert j["mode"] == "local-budget" and "85" in j["reply"] and len(calls) == 1


def test_rate_limit_is_per_visitor_behind_proxy(client):
    for _ in range(30):
        client.post("/chat", json={"messages": [{"role": "user", "content": "hi"}]}, environ_base={"REMOTE_ADDR": "1.1.1.1"})
    assert client.post("/chat", json={"messages": [{"role": "user", "content": "hi"}]}, environ_base={"REMOTE_ADDR": "1.1.1.1"}).status_code == 429
    assert client.post("/chat", json={"messages": [{"role": "user", "content": "hi"}]}, environ_base={"REMOTE_ADDR": "2.2.2.2"}).status_code == 200


def test_static_assets_served(client):
    for p in ("/static/css/style.css", "/static/js/chat.js", "/static/js/bouquet3d.js"):
        assert client.get(p).status_code == 200
