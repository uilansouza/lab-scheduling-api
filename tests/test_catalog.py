import pytest


class TestListExams:
    def test_list_exams_public_no_auth(self, client, seeded_exams):
        """Catalog endpoint is public — no API key required."""
        resp = client.get("/api/v1/exams")
        assert resp.status_code == 200

    def test_list_exams_returns_pagination_shape(self, client, seeded_exams):
        resp = client.get("/api/v1/exams")
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data

    def test_list_exams_active_only_by_default(self, client, seeded_exams):
        resp = client.get("/api/v1/exams")
        codes = [e["code"] for e in resp.json()["items"]]
        assert "EXM-T004" not in codes  # inactive exam should not appear

    def test_list_exams_include_inactive(self, client, seeded_exams):
        resp = client.get("/api/v1/exams", params={"active_only": False})
        codes = [e["code"] for e in resp.json()["items"]]
        assert "EXM-T004" in codes

    def test_list_exams_pagination(self, client, seeded_exams):
        resp = client.get("/api/v1/exams", params={"page": 1, "page_size": 2})
        data = resp.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    def test_list_exams_page_size_too_large(self, client):
        resp = client.get("/api/v1/exams", params={"page_size": 9999})
        assert resp.status_code == 422

    def test_list_exams_filter_by_code(self, client, seeded_exams):
        resp = client.get("/api/v1/exams", params={"code": "EXM-T001"})
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["code"] == "EXM-T001"

    def test_list_exams_filter_by_search(self, client, seeded_exams):
        resp = client.get("/api/v1/exams", params={"search": "Alpha"})
        data = resp.json()
        assert data["total"] >= 1
        assert any("Alpha" in e["name"] for e in data["items"])

    def test_list_exams_search_no_match(self, client, seeded_exams):
        resp = client.get("/api/v1/exams", params={"search": "NONEXISTENT_XYZZY"})
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []


class TestGetExam:
    def test_get_exam_by_code(self, client, seeded_exams):
        resp = client.get("/api/v1/exams/EXM-T001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "EXM-T001"
        assert data["name"] == "Exam Test Alpha"
        assert data["active"] is True

    def test_get_exam_not_found(self, client):
        resp = client.get("/api/v1/exams/EXM-DOES-NOT-EXIST")
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"] == "NOT_FOUND"

    def test_get_exam_case_insensitive(self, client, seeded_exams):
        resp = client.get("/api/v1/exams/exm-t001")
        assert resp.status_code == 200
        assert resp.json()["code"] == "EXM-T001"
