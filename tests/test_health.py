class TestHealth:
    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_docs_available(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_redoc_available(self, client):
        resp = client.get("/redoc")
        assert resp.status_code == 200


class TestErrorContracts:
    def test_404_has_error_field(self, client, agent_headers):
        resp = client.get("/api/v1/orders/nonexistent-id", headers=agent_headers)
        assert resp.status_code == 404
        body = resp.json()
        assert "error" in body
        assert "message" in body

    def test_401_has_error_field(self, client):
        resp = client.get("/api/v1/orders")
        assert resp.status_code == 401
        body = resp.json()
        assert "error" in body
        assert "message" in body

    def test_403_has_error_field(self, client, agent_headers):
        resp = client.get("/api/v1/audit", headers=agent_headers)
        assert resp.status_code == 403
        body = resp.json()
        assert "error" in body
        assert "message" in body

    def test_422_validation_has_details(self, client, agent_headers):
        resp = client.post("/api/v1/orders", json={}, headers=agent_headers)
        assert resp.status_code == 422
        body = resp.json()
        assert "error" in body
        assert "details" in body
