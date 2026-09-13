"""
Lab: Complete Test Suite — Unit + Integration + Property-Based

Demonstrates all three testing layers for a simple inventory API.

Install: pip install pytest pytest-asyncio httpx hypothesis testcontainers[postgres] fastapi

Run:
  pytest labs/ -v --tb=short
"""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from hypothesis import given, settings, strategies as st

# ─────────────────────────────────────────────
# The Application Under Test
# ─────────────────────────────────────────────

app = FastAPI()
inventory: dict[str, int] = {}  # product_id → quantity

@app.post("/products/{product_id}", status_code=201)
def add_stock(product_id: str, quantity: int):
    if quantity <= 0:
        raise HTTPException(status_code=422, detail="Quantity must be positive")
    inventory[product_id] = inventory.get(product_id, 0) + quantity
    return {"product_id": product_id, "total_stock": inventory[product_id]}

@app.delete("/products/{product_id}")
def remove_stock(product_id: str, quantity: int):
    current = inventory.get(product_id, 0)
    if quantity > current:
        raise HTTPException(status_code=409, detail=f"Insufficient stock: {current}")
    inventory[product_id] = current - quantity
    return {"product_id": product_id, "remaining_stock": inventory[product_id]}

@app.get("/products/{product_id}")
def get_stock(product_id: str):
    stock = inventory.get(product_id)
    if stock is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"product_id": product_id, "stock": stock}

# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_inventory():
    """Reset inventory state before EVERY test."""
    inventory.clear()
    yield
    inventory.clear()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def stocked_client(client):
    """Client with a pre-stocked product."""
    client.post("/products/laptop", json={"quantity": 50})
    return client

# ─────────────────────────────────────────────
# LAYER 1: Unit Tests
# ─────────────────────────────────────────────

class TestAddStock:
    def test_add_stock_success(self, client):
        response = client.post("/products/laptop", json={"quantity": 10})
        assert response.status_code == 201
        assert response.json()["total_stock"] == 10

    def test_add_stock_accumulates(self, client):
        client.post("/products/laptop", json={"quantity": 10})
        response = client.post("/products/laptop", json={"quantity": 5})
        assert response.json()["total_stock"] == 15

    def test_add_zero_quantity_rejected(self, client):
        response = client.post("/products/laptop", json={"quantity": 0})
        assert response.status_code == 422

    def test_add_negative_quantity_rejected(self, client):
        response = client.post("/products/laptop", json={"quantity": -5})
        assert response.status_code == 422


class TestRemoveStock:
    def test_remove_stock_success(self, stocked_client):
        response = stocked_client.delete("/products/laptop?quantity=20")
        assert response.status_code == 200
        assert response.json()["remaining_stock"] == 30

    def test_remove_more_than_available_fails(self, stocked_client):
        response = stocked_client.delete("/products/laptop?quantity=100")
        assert response.status_code == 409
        assert "Insufficient stock" in response.json()["detail"]

    def test_remove_from_nonexistent_product(self, client):
        response = client.delete("/products/nonexistent?quantity=1")
        assert response.status_code == 409   # 0 stock, can't remove 1


class TestGetStock:
    def test_get_existing_stock(self, stocked_client):
        response = stocked_client.get("/products/laptop")
        assert response.status_code == 200
        assert response.json()["stock"] == 50

    def test_get_nonexistent_product(self, client):
        response = client.get("/products/doesnotexist")
        assert response.status_code == 404


# ─────────────────────────────────────────────
# LAYER 2: Property-Based Tests (Hypothesis)
# ─────────────────────────────────────────────

class TestInventoryProperties:
    @given(
        add_qty=st.integers(min_value=1, max_value=1000),
        remove_qty=st.integers(min_value=1, max_value=1000),
    )
    @settings(max_examples=100)
    def test_stock_never_negative(self, client, add_qty, remove_qty):
        """
        Property: Stock should NEVER go below zero, regardless of operations.
        Hypothesis will try many combinations of add/remove quantities.
        """
        client.post("/products/widget", json={"quantity": add_qty})
        client.delete(f"/products/widget?quantity={remove_qty}")

        stock_resp = client.get("/products/widget")
        if stock_resp.status_code == 200:
            assert stock_resp.json()["stock"] >= 0, "Stock went negative!"

    @given(quantities=st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=10))
    def test_add_operations_are_commutative(self, client, quantities):
        """
        Property: Adding stock in any order gives the same total.
        """
        for q in quantities:
            client.post("/products/widget", json={"quantity": q})
        result = client.get("/products/widget").json()["stock"]
        assert result == sum(quantities)
