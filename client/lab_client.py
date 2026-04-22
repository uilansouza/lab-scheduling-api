#!/usr/bin/env python3
"""
Lab Scheduling API — Python Client
Demonstrates the full API flow:
  1. Health check
  2. List exams with pagination
  3. Filter exams by search term
  4. Create an order
  5. Get order detail
  6. Get order status + history
  7. Query audit logs
  8. Cancel the order
"""
import sys
import json
import argparse
from datetime import datetime, timezone, timedelta

import httpx

# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_AGENT_KEY = "agent-key-change-in-prod"
DEFAULT_ADMIN_KEY = "admin-key-change-in-prod"
TIMEOUT = 10.0


# ── Helpers ───────────────────────────────────────────────────────────────────

def _headers(api_key: str) -> dict:
    return {"X-API-Key": api_key, "Content-Type": "application/json"}


def _print_section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def _print_json(data):
    print(json.dumps(data, indent=2, default=str, ensure_ascii=False))


def _handle_response(resp: httpx.Response, label: str) -> dict:
    try:
        body = resp.json()
    except Exception:
        body = resp.text
    if resp.is_error:
        print(f"❌ [{label}] HTTP {resp.status_code}")
        _print_json(body)
        sys.exit(1)
    print(f"✅ [{label}] HTTP {resp.status_code}")
    return body


# ── Steps ─────────────────────────────────────────────────────────────────────

def step_health(client: httpx.Client):
    _print_section("1 · Health Check")
    resp = client.get("/health")
    data = _handle_response(resp, "health")
    _print_json(data)


def step_list_exams(client: httpx.Client, agent_key: str):
    _print_section("2 · List Exams (page 1, size 5)")
    resp = client.get(
        "/api/v1/exams",
        params={"page": 1, "page_size": 5},
    )
    data = _handle_response(resp, "list_exams")
    print(f"   Total exams in catalog: {data['total']} | Pages: {data['pages']}")
    for exam in data["items"]:
        print(f"   • {exam['code']}  {exam['name']}")


def step_filter_exams(client: httpx.Client):
    _print_section("3 · Filter Exams by search term 'Sintético'")
    resp = client.get(
        "/api/v1/exams",
        params={"search": "Sintético", "page": 1, "page_size": 3},
    )
    data = _handle_response(resp, "filter_exams")
    print(f"   Matched: {data['total']} exams")
    for exam in data["items"]:
        print(f"   • {exam['code']}  {exam['name']}  [{exam['category']}]")


def step_create_order(client: httpx.Client, agent_key: str) -> str:
    _print_section("4 · Create Order")
    now = datetime.now(timezone.utc)
    payload = {
        "user_ref": "USR-0001",
        "org_ref": "ORG-0001",
        "exam_codes": ["EXM-0001", "EXM-0011", "EXM-0041"],
        "window_start": (now + timedelta(days=1)).isoformat(),
        "window_end": (now + timedelta(days=1, hours=4)).isoformat(),
        "notes": "Coleta matinal — jejum de 12h",
    }
    print("   Payload:")
    _print_json(payload)
    resp = client.post("/api/v1/orders", json=payload, headers=_headers(agent_key))
    data = _handle_response(resp, "create_order")
    order_id = data["id"]
    print(f"\n   Order ID:         {order_id}")
    print(f"   Correlation ID:   {data['correlation_id']}")
    print(f"   Status:           {data['status']}")
    print(f"   Items:            {[i['exam_code'] for i in data['items']]}")
    return order_id


def step_get_order(client: httpx.Client, agent_key: str, order_id: str):
    _print_section(f"5 · Get Order Detail — {order_id}")
    resp = client.get(f"/api/v1/orders/{order_id}", headers=_headers(agent_key))
    data = _handle_response(resp, "get_order")
    print(f"   Status:     {data['status']}")
    print(f"   User ref:   {data['user_ref']}")
    print(f"   Org ref:    {data['org_ref']}")
    print(f"   Items:")
    for item in data["items"]:
        print(f"     - {item['exam_code']}  {item.get('exam_name', '')}")


def step_get_status(client: httpx.Client, agent_key: str, order_id: str):
    _print_section(f"6 · Order Status & History — {order_id}")
    resp = client.get(f"/api/v1/orders/{order_id}/status", headers=_headers(agent_key))
    data = _handle_response(resp, "get_status")
    print(f"   Current status: {data['status']}")
    print("   History:")
    for h in data["status_history"]:
        print(f"     [{h['changed_at']}]  {h['status']}  (by: {h.get('changed_by', '?')})")


def step_list_all_statuses(client: httpx.Client, agent_key: str):
    _print_section("6b · List All Possible Order Statuses")
    resp = client.get("/api/v1/orders/statuses", headers=_headers(agent_key))
    data = _handle_response(resp, "list_statuses")
    print(f"   Valid statuses: {data}")


def step_audit(client: httpx.Client, admin_key: str, order_id: str):
    _print_section(f"7 · Audit Logs for order {order_id}")
    resp = client.get(
        "/api/v1/audit",
        params={"resource_id": order_id},
        headers=_headers(admin_key),
    )
    data = _handle_response(resp, "audit_logs")
    print(f"   Total audit entries: {data['total']}")
    for log in data["items"]:
        print(f"   [{log['created_at']}]  {log['action']}  actor={log['actor']}")
        if log.get("detail"):
            print(f"     detail: {log['detail']}")


def step_cancel(client: httpx.Client, agent_key: str, order_id: str):
    _print_section(f"8 · Cancel Order — {order_id}")
    resp = client.patch(
        f"/api/v1/orders/{order_id}/cancel",
        json={"reason": "Cancelamento de demonstração pelo cliente"},
        headers=_headers(agent_key),
    )
    data = _handle_response(resp, "cancel_order")
    print(f"   New status: {data['status']}")


def step_cancel_again(client: httpx.Client, agent_key: str, order_id: str):
    _print_section("9 · Try to Cancel Again (expect 409)")
    resp = client.patch(
        f"/api/v1/orders/{order_id}/cancel",
        json={"reason": "Segunda tentativa — deve falhar"},
        headers=_headers(agent_key),
    )
    print(f"   HTTP {resp.status_code} (expected 409)")
    _print_json(resp.json())


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Lab Scheduling API — Demo Client")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--agent-key", default=DEFAULT_AGENT_KEY)
    parser.add_argument("--admin-key", default=DEFAULT_ADMIN_KEY)
    args = parser.parse_args()

    print(f"\n🔬 Lab Scheduling API Client")
    print(f"   Base URL:   {args.base_url}")
    print(f"   Agent key:  {args.agent_key[:8]}...")
    print(f"   Admin key:  {args.admin_key[:8]}...")

    try:
        with httpx.Client(base_url=args.base_url, timeout=TIMEOUT) as client:
            step_health(client)
            step_list_exams(client, args.agent_key)
            step_filter_exams(client)
            order_id = step_create_order(client, args.agent_key)
            step_list_all_statuses(client, args.agent_key)
            step_get_order(client, args.agent_key, order_id)
            step_get_status(client, args.agent_key, order_id)
            step_audit(client, args.admin_key, order_id)
            step_cancel(client, args.agent_key, order_id)
            step_cancel_again(client, args.agent_key, order_id)

        print(f"\n{'═' * 60}")
        print("  ✅ Full flow completed successfully!")
        print(f"{'═' * 60}\n")

    except httpx.ConnectError:
        print(f"\n❌ Could not connect to {args.base_url}")
        print("   Make sure the API is running: docker compose up\n")
        sys.exit(1)
    except httpx.TimeoutException:
        print(f"\n❌ Request timed out after {TIMEOUT}s\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
