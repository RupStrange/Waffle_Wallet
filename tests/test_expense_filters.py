"""
Tests for GET /api/expenses — filter, sort, paginate, auth.

Groups
──────
Baseline            — no filters, empty result
Each filter alone   — category, start_date, end_date, min_amount, max_amount
Combined filters    — AND semantics
Validation (422s)   — schema rejects bad input before any DB access
Sort & pagination   — ordering, stable total, deterministic tie-break
Security            — user isolation (IDOR guard), unauthenticated → 401 JSON
Serialisation       — Decimal as string
"""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from dependencies import get_current_user, get_db
from main import app

URL = "/api/expenses"


# ── Baseline ──────────────────────────────────────────────────────────────────

def test_no_filters_returns_all_expenses(client, make_expense, seed_users):
    user_a, _ = seed_users
    make_expense(user_a.id, amount="10.00", expense_date=date(2026, 1, 1))
    make_expense(user_a.id, amount="25.00", expense_date=date(2026, 2, 1))
    make_expense(user_a.id, amount="50.00", expense_date=date(2026, 3, 1))

    resp = client.get(URL)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3
    assert body["limit"] == 50
    assert body["offset"] == 0


def test_empty_result_is_200_not_404(client):
    """No expenses seeded → 200 with empty items list, not 404."""
    resp = client.get(URL, params={"category": "Food"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


# ── Each filter in isolation ──────────────────────────────────────────────────

def test_filter_by_category(client, make_expense, seed_users):
    user_a, _ = seed_users
    make_expense(user_a.id, category="Food")
    make_expense(user_a.id, category="Transport")

    resp = client.get(URL, params={"category": "Food"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["category"] == "Food"


def test_start_date_is_inclusive(client, make_expense, seed_users):
    user_a, _ = seed_users
    make_expense(user_a.id, expense_date=date(2026, 3, 1))

    resp_on = client.get(URL, params={"start_date": "2026-03-01"})
    assert resp_on.json()["total"] == 1, "expense ON start_date must be included"

    resp_after = client.get(URL, params={"start_date": "2026-03-02"})
    assert resp_after.json()["total"] == 0, "expense before start_date must be excluded"


def test_end_date_is_inclusive(client, make_expense, seed_users):
    user_a, _ = seed_users
    make_expense(user_a.id, expense_date=date(2026, 3, 31))

    resp_on = client.get(URL, params={"end_date": "2026-03-31"})
    assert resp_on.json()["total"] == 1, "expense ON end_date must be included"

    resp_before = client.get(URL, params={"end_date": "2026-03-30"})
    assert resp_before.json()["total"] == 0, "expense after end_date must be excluded"


def test_min_amount_is_inclusive(client, make_expense, seed_users):
    user_a, _ = seed_users
    make_expense(user_a.id, amount="25.00")

    assert client.get(URL, params={"min_amount": "25.00"}).json()["total"] == 1
    assert client.get(URL, params={"min_amount": "25.01"}).json()["total"] == 0


def test_max_amount_is_inclusive(client, make_expense, seed_users):
    user_a, _ = seed_users
    make_expense(user_a.id, amount="25.00")

    assert client.get(URL, params={"max_amount": "25.00"}).json()["total"] == 1
    assert client.get(URL, params={"max_amount": "24.99"}).json()["total"] == 0


def test_min_amount_zero_is_not_dropped(client, make_expense, seed_users):
    """Decimal('0') is falsy — a truthiness check would silently drop min_amount=0."""
    user_a, _ = seed_users
    make_expense(user_a.id, amount="10.00")

    resp = client.get(URL, params={"min_amount": "0"})
    assert resp.json()["total"] == 1


# ── Combined filters ──────────────────────────────────────────────────────────

def test_combined_filters_are_anded(client, make_expense, seed_users):
    user_a, _ = seed_users
    target = make_expense(user_a.id, category="Food",      expense_date=date(2026, 1, 10), amount="25.00")
    _wrong_date = make_expense(user_a.id, category="Food", expense_date=date(2026, 1, 5),  amount="25.00")
    _wrong_cat  = make_expense(user_a.id, category="Transport", expense_date=date(2026, 1, 10), amount="25.00")

    resp = client.get(URL, params={
        "category": "Food",
        "start_date": "2026-01-08",
        "end_date": "2026-01-15",
    })
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == target.id


# ── Validation (schema errors → 422) ─────────────────────────────────────────

def test_invalid_category_returns_422(client):
    resp = client.get(URL, params={"category": "Groceries"})
    assert resp.status_code == 422


def test_start_after_end_returns_422(client):
    resp = client.get(URL, params={"start_date": "2026-03-01", "end_date": "2026-01-01"})
    assert resp.status_code == 422


def test_min_above_max_returns_422(client):
    resp = client.get(URL, params={"min_amount": "100", "max_amount": "10"})
    assert resp.status_code == 422


def test_limit_above_ceiling_returns_422(client):
    resp = client.get(URL, params={"limit": "101"})
    assert resp.status_code == 422


def test_unknown_param_returns_422(client):
    """extra='forbid': a typo in a param name is a loud 422, not a silent no-op."""
    resp = client.get(URL, params={"categroy": "Food"})
    assert resp.status_code == 422


def test_injection_attempt_in_sort_returns_422(client):
    """Sort allowlist turns an injection attempt into a boring 422."""
    resp = client.get(URL, params={"sort": "amount; DROP TABLE expenses"})
    assert resp.status_code == 422


# ── Sorting and pagination ────────────────────────────────────────────────────

def test_default_sort_is_newest_first(client, make_expense, seed_users):
    user_a, _ = seed_users
    make_expense(user_a.id, expense_date=date(2026, 1, 1))
    make_expense(user_a.id, expense_date=date(2026, 2, 1))
    make_expense(user_a.id, expense_date=date(2026, 3, 1))

    resp = client.get(URL)
    items = resp.json()["items"]
    assert items[0]["date"] == "2026-03-01"
    assert items[-1]["date"] == "2026-01-01"


def test_sort_amt_asc(client, make_expense, seed_users):
    user_a, _ = seed_users
    make_expense(user_a.id, amount="100.00")
    make_expense(user_a.id, amount="10.00")
    make_expense(user_a.id, amount="50.00")

    resp = client.get(URL, params={"sort": "amt-asc"})
    amounts = [item["amount"] for item in resp.json()["items"]]
    assert amounts == sorted(amounts, key=float)


def test_pagination_total_is_stable_across_pages(client, make_expense, seed_users):
    user_a, _ = seed_users
    ids = [make_expense(user_a.id, expense_date=date(2026, 1, i + 1)).id for i in range(5)]

    page1 = client.get(URL, params={"limit": 2, "offset": 0}).json()
    page2 = client.get(URL, params={"limit": 2, "offset": 2}).json()
    page3 = client.get(URL, params={"limit": 2, "offset": 4}).json()

    assert page1["total"] == 5
    assert page2["total"] == 5
    assert page3["total"] == 5
    assert len(page1["items"]) == 2
    assert len(page2["items"]) == 2
    assert len(page3["items"]) == 1

    seen = [i["id"] for i in page1["items"] + page2["items"] + page3["items"]]
    assert len(seen) == len(set(seen)), "no id should appear twice across pages"


def test_offset_past_end_returns_empty_page(client, make_expense, seed_users):
    user_a, _ = seed_users
    make_expense(user_a.id)
    make_expense(user_a.id)

    resp = client.get(URL, params={"offset": 999})
    body = resp.json()
    assert resp.status_code == 200
    assert body["items"] == []
    assert body["total"] == 2


def test_tied_dates_are_ordered_deterministically(client, make_expense, seed_users):
    """Rows sharing a date must never repeat or disappear across pages."""
    user_a, _ = seed_users
    same_date = date(2026, 6, 15)
    all_ids = {make_expense(user_a.id, expense_date=same_date).id for _ in range(4)}

    page1 = client.get(URL, params={"limit": 2, "offset": 0}).json()
    page2 = client.get(URL, params={"limit": 2, "offset": 2}).json()

    seen = {i["id"] for i in page1["items"] + page2["items"]}
    assert seen == all_ids, "all 4 ids must appear exactly once across both pages"


# ── Security ─────────────────────────────────────────────────────────────────

def test_user_isolation(make_expense, seed_users, db_session):
    """The most important test: user A must never see user B's expenses.

    Uses manual override management because requesting both `client` and
    `client_as_b` in the same test causes them to overwrite the same
    app.dependency_overrides[get_current_user] key — the second fixture
    wins and both clients end up authenticated as the same user.
    """
    user_a, user_b = seed_users
    a_ids = {make_expense(user_a.id).id for _ in range(3)}
    b_ids = {make_expense(user_b.id).id for _ in range(2)}

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: user_a
    try:
        resp_a = TestClient(app).get(URL)
    finally:
        app.dependency_overrides.clear()

    body_a = resp_a.json()
    assert body_a["total"] == 3
    returned_a = {i["id"] for i in body_a["items"]}
    assert returned_a == a_ids, "user A must only see their own expenses"
    assert not returned_a.intersection(b_ids), "user A must not see user B's expenses"

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: user_b
    try:
        resp_b = TestClient(app).get(URL)
    finally:
        app.dependency_overrides.clear()

    body_b = resp_b.json()
    assert body_b["total"] == 2
    returned_b = {i["id"] for i in body_b["items"]}
    assert returned_b == b_ids
    assert not returned_b.intersection(a_ids)


def test_unauthenticated_returns_401_with_json_body(db_session):
    """No session → 401. Body must be JSON with our error shape, not plain-text 'None'."""
    app.dependency_overrides[get_db] = lambda: db_session
    # deliberately do NOT override get_current_user
    c = TestClient(app)
    resp = c.get(URL)
    app.dependency_overrides.clear()

    assert resp.status_code == 401
    body = resp.json()
    assert "error" in body, f"expected JSON error envelope, got: {body}"
    assert body["error"]["message"], "error message must be non-empty"


# ── Serialisation ─────────────────────────────────────────────────────────────

def test_amount_serialises_as_decimal_string(client, make_expense, seed_users):
    """Pydantic v2 serialises Decimal as a string to preserve precision."""
    user_a, _ = seed_users
    make_expense(user_a.id, amount="25.00")

    resp = client.get(URL)
    item = resp.json()["items"][0]
    assert item["amount"] == "25.00", (
        f"expected '25.00' (string), got {item['amount']!r}. "
        "Float would lose precision on money values."
    )
