#!/usr/bin/env python3
"""End-to-end test script for PLAYBOOK application."""

import requests
import json
import sys

API_BASE = "http://localhost:8001/api/v1"
FRONTEND = "http://localhost:5173"

errors = []
warnings = []

def log_error(msg):
    errors.append(msg)
    print(f"  [FAIL] {msg}")

def log_warn(msg):
    warnings.append(msg)
    print(f"  [WARN] {msg}")

def log_ok(msg):
    print(f"  [OK]   {msg}")

def test_backend_health():
    print("\n--- BACKEND HEALTH ---")
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        if r.status_code == 200:
            data = r.json()
            log_ok(f"Health check: {data.get('status')} (DB: {data.get('components', {}).get('database')})")
        else:
            log_error(f"Health check returned {r.status_code}")
    except Exception as e:
        log_error(f"Health check failed: {e}")

def test_auth_flow():
    print("\n--- AUTH FLOW ---")
    token = None
    # Login
    try:
        r = requests.post(
            f"{API_BASE}/auth/login",
            json={"email": "demo@playbook.local", "password": "demo123"},
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("success") and data.get("data", {}).get("access_token"):
                token = data["data"]["access_token"]
                user = data["data"].get("user", {})
                log_ok(f"Login succeeded for {user.get('email')} (role: {user.get('role')})")
            else:
                log_error(f"Login response missing token: {data}")
        else:
            log_error(f"Login returned {r.status_code}: {r.text[:200]}")
    except Exception as e:
        log_error(f"Login failed: {e}")
        return None

    # Get current user
    if token:
        try:
            r = requests.get(
                f"{API_BASE}/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )
            if r.status_code == 200:
                data = r.json()
                log_ok(f"/auth/me returned user: {data.get('data', {}).get('email')}")
            else:
                log_error(f"/auth/me returned {r.status_code}: {r.text[:200]}")
        except Exception as e:
            log_error(f"/auth/me failed: {e}")

    return token

def test_dashboard(token):
    print("\n--- DASHBOARD ---")
    try:
        r = requests.get(
            f"{API_BASE}/dashboard",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            stats = data.get("data", {})
            log_ok(f"Dashboard stats: incidents={stats.get('total_incidents')}, agents={stats.get('total_agents')}")
        else:
            log_error(f"Dashboard returned {r.status_code}: {r.text[:200]}")
    except Exception as e:
        log_error(f"Dashboard failed: {e}")

def test_incidents(token):
    print("\n--- INCIDENTS ---")
    try:
        r = requests.get(
            f"{API_BASE}/incidents?page=1&page_size=5",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            # Backend returns {"data": [...], "total": N, "page": 1, "page_size": 5}
            items = data.get("data", [])
            total = data.get("total", 0)
            log_ok(f"Incidents list: {len(items)} items (total={total})")
            if items:
                incident_id = items[0]["id"]
                r2 = requests.get(
                    f"{API_BASE}/incidents/{incident_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5
                )
                if r2.status_code == 200:
                    log_ok(f"Incident detail fetch OK for {incident_id[:8]}...")
                else:
                    log_error(f"Incident detail returned {r2.status_code}")
            else:
                log_warn("No incidents in database")
        else:
            log_error(f"Incidents list returned {r.status_code}: {r.text[:200]}")
    except Exception as e:
        log_error(f"Incidents failed: {e}")

def test_agents(token):
    print("\n--- AGENTS ---")
    try:
        r = requests.get(
            f"{API_BASE}/agents",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            # Backend returns {"data": {"agents": [...], "total": N}}
            agents = data.get("data", {}).get("agents", [])
            log_ok(f"Agents list: {len(agents)} agents")
            if len(agents) == 0:
                log_warn("No agents in database")
        else:
            log_error(f"Agents returned {r.status_code}: {r.text[:200]}")
    except Exception as e:
        log_error(f"Agents failed: {e}")

def test_compliance(token):
    print("\n--- COMPLIANCE ---")
    try:
        r = requests.get(
            f"{API_BASE}/compliance/frameworks",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            frameworks = data.get("data", {}).get("frameworks", [])
            log_ok(f"Frameworks: {len(frameworks)} frameworks")
            if frameworks:
                fw = frameworks[0]["name"]
                r2 = requests.get(
                    f"{API_BASE}/compliance/mapping?framework={fw}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5
                )
                if r2.status_code == 200:
                    log_ok(f"Mapping for {fw}: OK")
                else:
                    log_error(f"Mapping returned {r2.status_code}: {r2.text[:200]}")
            else:
                log_warn("No frameworks returned — seed data may be missing")
        else:
            log_error(f"Frameworks returned {r.status_code}: {r.text[:200]}")
    except Exception as e:
        log_error(f"Compliance failed: {e}")

def test_policy_builder(token):
    print("\n--- POLICY BUILDER ---")
    try:
        r = requests.get(
            f"{API_BASE}/policy-builder/templates",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if r.status_code == 200:
            log_ok("Templates: OK")
        else:
            log_error(f"Templates returned {r.status_code}: {r.text[:200]}")

        r2 = requests.get(
            f"{API_BASE}/policy-builder/nist-baseline",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if r2.status_code == 200:
            data = r2.json()
            items = data.get("data", {}).get("items", [])
            log_ok(f"NIST baselines: {len(items)} items")
            if len(items) == 0:
                log_warn("No NIST baseline items — seed data may be missing")
        else:
            log_error(f"NIST baseline returned {r2.status_code}: {r2.text[:200]}")
    except Exception as e:
        log_error(f"Policy builder failed: {e}")

def test_review_queue(token):
    print("\n--- REVIEW QUEUE ---")
    # Frontend calls /incidents?status=escalated — test that path
    try:
        r = requests.get(
            f"{API_BASE}/incidents?status=escalated&page_size=100",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            items = data.get("data", [])
            log_ok(f"Review queue (via /incidents?status=escalated): {len(items)} items")
        else:
            log_error(f"Review queue returned {r.status_code}: {r.text[:200]}")
    except Exception as e:
        log_error(f"Review queue failed: {e}")

def test_settings(token):
    print("\n--- SETTINGS ---")
    try:
        r = requests.get(
            f"{API_BASE}/settings/public",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            log_ok(f"Public settings: env={data.get('data', {}).get('environment')}, demo={data.get('data', {}).get('demo_mode')}")
        else:
            log_error(f"Settings returned {r.status_code}: {r.text[:200]}")
    except Exception as e:
        log_error(f"Settings failed: {e}")

def test_websocket(token):
    print("\n--- WEBSOCKET ---")
    try:
        import websocket
        ws_url = f"ws://localhost:8001/api/v1/ws/incidents?token={token}"
        ws = websocket.create_connection(ws_url, timeout=5)
        ws.settimeout(3)
        msg = ws.recv()
        data = json.loads(msg)
        if data.get("event_type") == "connection_established":
            log_ok(f"WebSocket connected, received: {data.get('event_type')}")
        else:
            log_warn(f"WebSocket unexpected message: {data}")
        ws.close()
    except ImportError:
        log_warn("websocket-client not installed, skipping WebSocket test")
    except Exception as e:
        log_error(f"WebSocket failed: {e}")

def test_frontend_routes():
    print("\n--- FRONTEND ROUTES ---")
    routes = ["/", "/login", "/dashboard", "/incidents", "/agents", "/compliance", "/policy-builder", "/settings"]
    for route in routes:
        try:
            r = requests.get(f"{FRONTEND}{route}", timeout=5)
            if r.status_code == 200:
                content_type = r.headers.get("content-type", "")
                if "text/html" in content_type:
                    if "root" not in r.text and 'div id="root"' not in r.text:
                        log_warn(f"{route} - HTML missing root div")
                    else:
                        log_ok(f"{route} - HTML OK")
                else:
                    log_ok(f"{route} - {content_type}")
            else:
                log_error(f"{route} returned {r.status_code}")
        except Exception as e:
            log_error(f"{route} failed: {e}")

def test_cors():
    print("\n--- CORS ---")
    try:
        r = requests.options(
            f"{API_BASE}/auth/login",
            headers={
                "Origin": FRONTEND,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization",
            },
            timeout=5
        )
        if r.status_code == 200:
            allow_origin = r.headers.get("access-control-allow-origin", "")
            if FRONTEND in allow_origin or "*" in allow_origin:
                log_ok(f"CORS preflight OK (allow-origin: {allow_origin})")
            else:
                log_warn(f"CORS allow-origin is '{allow_origin}', expected '{FRONTEND}'")
        else:
            log_error(f"CORS preflight returned {r.status_code}")
    except Exception as e:
        log_error(f"CORS test failed: {e}")

def test_data_consistency(token):
    print("\n--- DATA CONSISTENCY ---")
    try:
        r = requests.get(
            f"{API_BASE}/incidents?page=1&page_size=100",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            items = data.get("data", [])
            # Check for incidents without agent_id
            missing_agent = [i for i in items if not i.get("agent_id")]
            if missing_agent:
                log_warn(f"{len(missing_agent)} incidents missing agent_id")
            else:
                log_ok("All incidents have agent_id")

            # Check for duplicate IDs
            ids = [i["id"] for i in items]
            dupes = [i for i in set(ids) if ids.count(i) > 1]
            if dupes:
                log_error(f"Duplicate incident IDs found: {dupes}")
            else:
                log_ok("No duplicate incident IDs")
        else:
            log_error(f"Incidents list returned {r.status_code}")
    except Exception as e:
        log_error(f"Data consistency check failed: {e}")

def main():
    print("=" * 60)
    print("PLAYBOOK END-TO-END TEST")
    print("=" * 60)

    test_backend_health()
    token = test_auth_flow()
    test_cors()

    if token:
        test_dashboard(token)
        test_incidents(token)
        test_agents(token)
        test_compliance(token)
        test_policy_builder(token)
        test_review_queue(token)
        test_settings(token)
        test_websocket(token)
        test_data_consistency(token)
    else:
        log_error("Skipping authenticated tests - no token obtained")

    test_frontend_routes()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Errors:   {len(errors)}")
    print(f"Warnings: {len(warnings)}")

    if errors:
        print("\nFAILURES:")
        for e in errors:
            print(f"  - {e}")
    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  - {w}")

    if not errors:
        print("\nAll critical tests passed!")
        return 0
    else:
        print(f"\n{len(errors)} critical issue(s) found")
        return 1

if __name__ == "__main__":
    sys.exit(main())
