"""
Basic unit / integration / API tests using FastAPI's TestClient.

Run with:
    pytest -v
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DATABASE_URL"] = "sqlite:///./test_finance_tracker.db"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_finance_tracker.db"):
        os.remove("test_finance_tracker.db")


@pytest.fixture(scope="module")
def auth_token():
    resp = client.post("/api/auth/register", json={
        "full_name": "Test User", "email": "test@example.com", "password": "testpass123",
    })
    assert resp.status_code == 201
    return resp.json()["access_token"]


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_and_login():
    resp = client.post("/api/auth/register", json={
        "full_name": "Jane Doe", "email": "jane@example.com", "password": "securepass",
    })
    assert resp.status_code == 201
    assert "access_token" in resp.json()

    resp2 = client.post("/api/auth/login", data={"username": "jane@example.com", "password": "securepass"})
    assert resp2.status_code == 200


def test_duplicate_registration_fails():
    client.post("/api/auth/register", json={
        "full_name": "Dup", "email": "dup@example.com", "password": "password1",
    })
    resp = client.post("/api/auth/register", json={
        "full_name": "Dup2", "email": "dup@example.com", "password": "password2",
    })
    assert resp.status_code == 400


def test_add_and_list_expense(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.post("/api/expenses/", json={
        "amount": 250.0, "category": "Food", "description": "Pizza",
        "payment_mode": "UPI",
    }, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["category"] == "Food"

    resp2 = client.get("/api/expenses/", headers=headers)
    assert resp2.status_code == 200
    assert len(resp2.json()) >= 1


def test_categorize_endpoint():
    resp = client.post("/api/expenses/categorize", json={"text": "Uber ride to office"})
    assert resp.status_code == 200
    assert resp.json()["category"] == "Transport"


def test_add_income(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.post("/api/income/", json={
        "amount": 50000, "source": "Salary", "description": "Monthly salary",
    }, headers=headers)
    assert resp.status_code == 201


def test_dashboard_summary(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.get("/api/dashboard/summary", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "financial_score" in body
    assert body["total_income"] >= 0


def test_budget_creation_and_progress(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.post("/api/budgets/", json={
        "month": "2026-07", "limit_amount": 10000, "category": "Food",
    }, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["limit_amount"] == 10000


def test_unauthorized_access_blocked():
    resp = client.get("/api/expenses/")
    assert resp.status_code == 401
