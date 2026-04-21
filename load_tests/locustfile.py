"""
Load test — Lab Scheduling API
Run: locust -f load_tests/locustfile.py --host=http://localhost:8000

Scenarios:
  - ReadOnlyUser  : browses the exam catalog (no auth needed, high RPS)
  - AgentUser     : authenticates as agent — creates, reads and cancels orders
  - AdminUser     : authenticates as admin — reads audit logs

Typical command for a quick smoke test (30s, 20 users):
  locust -f load_tests/locustfile.py --host=http://localhost:8000 \
         --users 20 --spawn-rate 5 --run-time 30s --headless \
         --html load_tests/report.html
"""
import random
from datetime import datetime, timezone, timedelta
from locust import HttpUser, task, between, events

AGENT_KEY = "agent-key-change-in-prod"
ADMIN_KEY = "admin-key-change-in-prod"

AGENT_HEADERS = {"X-API-Key": AGENT_KEY}
ADMIN_HEADERS = {"X-API-Key": ADMIN_KEY}

# Exam codes seeded in the DB — a sample to use in order creation
EXAM_POOL = [
    "EXM-0001", "EXM-0002", "EXM-0011", "EXM-0029",
    "EXM-0030", "EXM-0041", "EXM-0061", "EXM-0086",
    "EXM-0091", "EXM-0101",
]


def _random_order_payload() -> dict:
    codes = random.sample(EXAM_POOL, k=random.randint(1, 4))
    now = datetime.now(timezone.utc)
    return {
        "user_ref": f"USR-{random.randint(1, 999):04d}",
        "org_ref": f"ORG-{random.randint(1, 10):04d}",
        "exam_codes": codes,
        "window_start": (now + timedelta(days=1)).isoformat(),
        "window_end": (now + timedelta(days=1, hours=4)).isoformat(),
    }


class ReadOnlyUser(HttpUser):
    """Simulates a system that only reads the exam catalog."""
    weight = 3
    wait_time = between(0.5, 1.5)

    @task(5)
    def list_exams(self):
        page = random.randint(1, 5)
        self.client.get(f"/api/v1/exams?page={page}&page_size=20", name="/api/v1/exams")

    @task(2)
    def get_exam_by_code(self):
        code = random.choice(EXAM_POOL)
        self.client.get(f"/api/v1/exams/{code}", name="/api/v1/exams/{code}")

    @task(1)
    def search_exams(self):
        terms = ["Sintético", "Hemograma", "Glicose", "TSH", "PCR"]
        term = random.choice(terms)
        self.client.get(f"/api/v1/exams?search={term}", name="/api/v1/exams?search=*")

    @task(1)
    def health_check(self):
        self.client.get("/health")


class AgentUser(HttpUser):
    """Simulates a scheduling agent creating and managing orders."""
    weight = 5
    wait_time = between(0.3, 1.0)

    def on_start(self):
        self._order_ids: list[str] = []

    @task(4)
    def create_order(self):
        payload = _random_order_payload()
        with self.client.post(
            "/api/v1/orders",
            json=payload,
            headers=AGENT_HEADERS,
            name="/api/v1/orders [POST]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                order_id = resp.json().get("id")
                if order_id:
                    self._order_ids.append(order_id)
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}: {resp.text[:200]}")

    @task(3)
    def list_orders(self):
        self.client.get(
            "/api/v1/orders?page=1&page_size=20",
            headers=AGENT_HEADERS,
            name="/api/v1/orders [GET]",
        )

    @task(2)
    def get_order_detail(self):
        if not self._order_ids:
            return
        order_id = random.choice(self._order_ids)
        self.client.get(
            f"/api/v1/orders/{order_id}",
            headers=AGENT_HEADERS,
            name="/api/v1/orders/{id} [GET]",
        )

    @task(2)
    def get_order_status(self):
        if not self._order_ids:
            return
        order_id = random.choice(self._order_ids)
        self.client.get(
            f"/api/v1/orders/{order_id}/status",
            headers=AGENT_HEADERS,
            name="/api/v1/orders/{id}/status",
        )

    @task(1)
    def cancel_order(self):
        if not self._order_ids:
            return
        order_id = self._order_ids.pop(0)
        with self.client.patch(
            f"/api/v1/orders/{order_id}/cancel",
            json={"reason": "Load test cancellation"},
            headers=AGENT_HEADERS,
            name="/api/v1/orders/{id}/cancel",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 409):
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}")

    @task(1)
    def list_statuses(self):
        self.client.get(
            "/api/v1/orders/statuses",
            headers=AGENT_HEADERS,
            name="/api/v1/orders/statuses",
        )


class AdminUser(HttpUser):
    """Simulates an admin auditor querying logs."""
    weight = 1
    wait_time = between(1.0, 3.0)

    @task(3)
    def list_audit_logs(self):
        self.client.get(
            "/api/v1/audit?page=1&page_size=20",
            headers=ADMIN_HEADERS,
            name="/api/v1/audit",
        )

    @task(1)
    def list_audit_filtered(self):
        self.client.get(
            "/api/v1/audit?resource=orders&page=1&page_size=10",
            headers=ADMIN_HEADERS,
            name="/api/v1/audit?resource=orders",
        )


# ── Event hooks for summary stats ─────────────────────────────────────────────

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stats = environment.stats
    print("\n" + "=" * 60)
    print("LOAD TEST SUMMARY")
    print("=" * 60)
    for name, entry in stats.entries.items():
        print(
            f"{name[1]:45s} | "
            f"RPS={entry.current_rps:6.1f} | "
            f"p50={entry.get_response_time_percentile(0.50) or 0:5.0f}ms | "
            f"p95={entry.get_response_time_percentile(0.95) or 0:5.0f}ms | "
            f"fail={entry.num_failures}"
        )
    total = stats.total
    print("-" * 60)
    print(
        f"{'TOTAL':45s} | "
        f"RPS={total.current_rps:6.1f} | "
        f"p50={total.get_response_time_percentile(0.50) or 0:5.0f}ms | "
        f"p95={total.get_response_time_percentile(0.95) or 0:5.0f}ms | "
        f"fail={total.num_failures}"
    )
    print("=" * 60)
