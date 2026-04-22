import pytest
from datetime import datetime, timezone, timedelta


def _create_order(client, agent_headers):
    now = datetime.now(timezone.utc)
    return client.post(
        "/api/v1/orders",
        json={
            "user_ref": "USR-0001",
            "exam_codes": ["EXM-T001"],
            "window_start": (now + timedelta(days=1)).isoformat(),
            "window_end": (now + timedelta(days=1, hours=4)).isoformat(),
        },
        headers=agent_headers,
    ).json()


class TestAuditLogs:
    def test_audit_requires_admin(self, client, agent_headers):
        """Agent key should NOT access audit logs."""
        resp = client.get("/api/v1/audit", headers=agent_headers)
        assert resp.status_code == 403
        assert resp.json()["error"] == "FORBIDDEN"

    def test_audit_requires_auth(self, client):
        resp = client.get("/api/v1/audit")
        assert resp.status_code == 401

    def test_audit_accessible_by_admin(self, client, seeded_exams, admin_headers):
        resp = client.get("/api/v1/audit", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_audit_log_created_on_order_create(self, client, seeded_exams, agent_headers, admin_headers):
        order = _create_order(client, agent_headers)
        resp = client.get(
            "/api/v1/audit",
            params={"resource_id": order["id"]},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        actions = [log["action"] for log in data["items"]]
        assert "ORDER_CREATED" in actions

    def test_audit_log_created_on_cancel(self, client, seeded_exams, agent_headers, admin_headers):
        order = _create_order(client, agent_headers)
        client.patch(
            f"/api/v1/orders/{order['id']}/cancel",
            json={"reason": "audit test"},
            headers=agent_headers,
        )
        resp = client.get(
            "/api/v1/audit",
            params={"resource_id": order["id"]},
            headers=admin_headers,
        )
        actions = [log["action"] for log in resp.json()["items"]]
        assert "ORDER_CANCELLED" in actions

    def test_audit_filter_by_correlation_id(self, client, seeded_exams, agent_headers, admin_headers):
        order = _create_order(client, agent_headers)
        corr_id = order["correlation_id"]
        resp = client.get(
            "/api/v1/audit",
            params={"correlation_id": corr_id},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        for log in resp.json()["items"]:
            assert log["correlation_id"] == corr_id

    def test_audit_response_shape(self, client, seeded_exams, agent_headers, admin_headers):
        _create_order(client, agent_headers)
        resp = client.get("/api/v1/audit", headers=admin_headers)
        data = resp.json()
        if data["items"]:
            log = data["items"][0]
            assert "id" in log
            assert "action" in log
            assert "resource" in log
            assert "actor" in log
            assert "created_at" in log

    def test_audit_pagination(self, client, seeded_exams, agent_headers, admin_headers):
        resp = client.get("/api/v1/audit", params={"page": 1, "page_size": 2}, headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
