import pytest
from datetime import datetime, timezone, timedelta


def _future_window():
    now = datetime.now(timezone.utc)
    return {
        "window_start": (now + timedelta(days=1)).isoformat(),
        "window_end": (now + timedelta(days=1, hours=4)).isoformat(),
    }


def _create_order(client, agent_headers, exam_codes=None, extra=None):
    payload = {
        "user_ref": "USR-0001",
        "exam_codes": exam_codes or ["EXM-T001", "EXM-T002"],
        **_future_window(),
    }
    if extra:
        payload.update(extra)
    return client.post("/api/v1/orders", json=payload, headers=agent_headers)


class TestCreateOrder:
    def test_create_order_success(self, client, seeded_exams, agent_headers):
        resp = _create_order(client, agent_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "PENDING"
        assert len(data["items"]) == 2
        assert data["correlation_id"]
        assert data["user_ref"] == "USR-0001"

    def test_create_order_sets_initial_status_history(self, client, seeded_exams, agent_headers):
        resp = _create_order(client, agent_headers)
        data = resp.json()
        history = data["status_history"]
        assert len(history) == 1
        assert history[0]["status"] == "PENDING"

    def test_create_order_invalid_exam_code(self, client, seeded_exams, agent_headers):
        resp = _create_order(client, agent_headers, exam_codes=["EXM-T001", "EXM-INVALID"])
        assert resp.status_code == 422
        body = resp.json()
        assert body["error"] == "INVALID_EXAM_CODES"
        assert "EXM-INVALID" in body["details"]["invalid_codes"]

    def test_create_order_inactive_exam_rejected(self, client, seeded_exams, agent_headers):
        resp = _create_order(client, agent_headers, exam_codes=["EXM-T004"])
        assert resp.status_code == 422
        assert "EXM-T004" in resp.json()["details"]["invalid_codes"]

    def test_create_order_duplicate_codes_rejected(self, client, seeded_exams, agent_headers):
        resp = _create_order(client, agent_headers, exam_codes=["EXM-T001", "EXM-T001"])
        assert resp.status_code == 422

    def test_create_order_empty_codes_rejected(self, client, seeded_exams, agent_headers):
        payload = {"user_ref": "USR-0001", "exam_codes": []}
        resp = client.post("/api/v1/orders", json=payload, headers=agent_headers)
        assert resp.status_code == 422

    def test_create_order_missing_user_ref(self, client, seeded_exams, agent_headers):
        payload = {"exam_codes": ["EXM-T001"]}
        resp = client.post("/api/v1/orders", json=payload, headers=agent_headers)
        assert resp.status_code == 422

    def test_create_order_window_end_before_start(self, client, seeded_exams, agent_headers):
        now = datetime.now(timezone.utc)
        payload = {
            "user_ref": "USR-0001",
            "exam_codes": ["EXM-T001"],
            "window_start": (now + timedelta(days=2)).isoformat(),
            "window_end": (now + timedelta(days=1)).isoformat(),
        }
        resp = client.post("/api/v1/orders", json=payload, headers=agent_headers)
        assert resp.status_code == 422

    def test_create_order_requires_auth(self, client, seeded_exams):
        resp = _create_order(client, {})
        assert resp.status_code == 401

    def test_create_order_wrong_key(self, client, seeded_exams):
        resp = _create_order(client, {"X-API-Key": "wrong-key"})
        assert resp.status_code == 401

    def test_create_order_with_org_ref(self, client, seeded_exams, agent_headers):
        resp = _create_order(client, agent_headers, extra={"org_ref": "ORG-0001"})
        assert resp.status_code == 201
        assert resp.json()["org_ref"] == "ORG-0001"


class TestListOrders:
    def test_list_orders(self, client, seeded_exams, agent_headers):
        _create_order(client, agent_headers)
        resp = client.get("/api/v1/orders", headers=agent_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total"] >= 1

    def test_list_orders_filter_by_status(self, client, seeded_exams, agent_headers):
        _create_order(client, agent_headers)
        resp = client.get("/api/v1/orders", params={"status": "PENDING"}, headers=agent_headers)
        assert resp.status_code == 200
        for order in resp.json()["items"]:
            assert order["status"] == "PENDING"

    def test_list_orders_filter_by_user_ref(self, client, seeded_exams, agent_headers):
        _create_order(client, agent_headers, extra={"user_ref": "USR-FILTER-TEST"})
        resp = client.get("/api/v1/orders", params={"user_ref": "USR-FILTER-TEST"}, headers=agent_headers)
        assert resp.status_code == 200
        for order in resp.json()["items"]:
            assert order["user_ref"] == "USR-FILTER-TEST"

    def test_list_orders_requires_auth(self, client):
        resp = client.get("/api/v1/orders")
        assert resp.status_code == 401


class TestGetOrder:
    def test_get_order_detail(self, client, seeded_exams, agent_headers):
        order_id = _create_order(client, agent_headers).json()["id"]
        resp = client.get(f"/api/v1/orders/{order_id}", headers=agent_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == order_id
        assert len(data["items"]) == 2
        for item in data["items"]:
            assert item["exam_name"] is not None

    def test_get_order_not_found(self, client, agent_headers):
        resp = client.get("/api/v1/orders/00000000-0000-0000-0000-000000000000", headers=agent_headers)
        assert resp.status_code == 404
        assert resp.json()["error"] == "NOT_FOUND"

    def test_get_order_status(self, client, seeded_exams, agent_headers):
        order_id = _create_order(client, agent_headers).json()["id"]
        resp = client.get(f"/api/v1/orders/{order_id}/status", headers=agent_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "PENDING"
        assert len(data["status_history"]) >= 1

    def test_list_statuses_endpoint(self, client, agent_headers):
        resp = client.get("/api/v1/orders/statuses", headers=agent_headers)
        assert resp.status_code == 200
        statuses = resp.json()
        assert "PENDING" in statuses
        assert "CONFIRMED" in statuses
        assert "COLLECTED" in statuses
        assert "CANCELLED" in statuses


class TestCancelOrder:
    def test_cancel_order(self, client, seeded_exams, agent_headers):
        order_id = _create_order(client, agent_headers).json()["id"]
        resp = client.patch(
            f"/api/v1/orders/{order_id}/cancel",
            json={"reason": "Test cancellation"},
            headers=agent_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "CANCELLED"

    def test_cancel_order_records_history(self, client, seeded_exams, agent_headers):
        order_id = _create_order(client, agent_headers).json()["id"]
        client.patch(f"/api/v1/orders/{order_id}/cancel", json={}, headers=agent_headers)
        resp = client.get(f"/api/v1/orders/{order_id}/status", headers=agent_headers)
        history_statuses = [h["status"] for h in resp.json()["status_history"]]
        assert "PENDING" in history_statuses
        assert "CANCELLED" in history_statuses

    def test_cancel_already_cancelled_returns_409(self, client, seeded_exams, agent_headers):
        order_id = _create_order(client, agent_headers).json()["id"]
        client.patch(f"/api/v1/orders/{order_id}/cancel", json={}, headers=agent_headers)
        resp = client.patch(f"/api/v1/orders/{order_id}/cancel", json={}, headers=agent_headers)
        assert resp.status_code == 409
        assert resp.json()["error"] == "ALREADY_CANCELLED"

    def test_cancel_nonexistent_order_returns_404(self, client, agent_headers):
        resp = client.patch(
            "/api/v1/orders/00000000-0000-0000-0000-000000000000/cancel",
            json={},
            headers=agent_headers,
        )
        assert resp.status_code == 404

    def test_cancel_requires_auth(self, client, seeded_exams, agent_headers):
        order_id = _create_order(client, agent_headers).json()["id"]
        resp = client.patch(f"/api/v1/orders/{order_id}/cancel", json={})
        assert resp.status_code == 401
