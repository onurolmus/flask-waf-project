"""
Flask WAF — Automated Security (OWASP) Test Suite
Run with: python tests/test_waf.py
"""

import requests
import sys
import urllib3
import random

# Suppress insecure request warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Use a session with verify=False for WAF HTTPS endpoint
session = requests.Session()
session.verify = False
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"})

# WAF is exposed on port 8443 via HTTPS
BASE_URL = "https://localhost:8443"

passed = 0
failed = 0

def test(name, condition, response=None):
    global passed, failed
    if condition:
        print(f"  ✅ PASS (Blocked) | {name}")
        passed += 1
    else:
        print(f"  ❌ FAIL (Allowed) | {name}")
        if response:
            print(f"          Response: {response.status_code}")
        failed += 1


def separator(title):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


print("\n🛡️  STARTING OWASP WAF SECURITY TESTS 🛡️\n")
print("These tests simulate malicious attacks. The WAF MUST return 403 Forbidden (or 400).")

# ─────────────────────────────────────────────────
separator("1. SQL Injection (SQLi) Tests")

sql_payloads = [
    "' OR 1=1 --",
    "admin' OR '1'='1",
    "1'; DROP TABLE users; --"
]

for payload in sql_payloads:
    # Test SQLi in JSON body
    r = session.post(f"{BASE_URL}/login", json={
        "username": payload,
        "password": "AnyPassword1"
    })
    test(f"SQLi in JSON Body: {payload}", r.status_code == 403, r)

    # Test SQLi in URL Query String (even if endpoint doesn't use it, WAF should block)
    r = session.get(f"{BASE_URL}/user/list?search={payload}")
    test(f"SQLi in Query String: {payload}", r.status_code == 403, r)

# ─────────────────────────────────────────────────
separator("2. Cross-Site Scripting (XSS) Tests")

xss_payloads = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert(1)"
]

for payload in xss_payloads:
    r = session.post(f"{BASE_URL}/user/create", json={
        "username": f"user_{random.randint(100,999)}",
        "firstname": payload,
        "lastname": "Test",
        "birthdate": "2000-01-01",
        "email": "test@example.com",
        "password": "Secure123"
    })
    test(f"XSS in JSON Body: {payload}", r.status_code == 403, r)

# ─────────────────────────────────────────────────
separator("3. Path Traversal / LFI Tests")

path_payloads = [
    "../../../../etc/passwd",
    "....//....//....//etc/passwd",
    "../../../../windows/win.ini"
]

for payload in path_payloads:
    # We use a query parameter because requests.get() normalizes URL paths (e.g. removes ../)
    # before sending, which ruins the test. ModSecurity checks all params.
    r = session.get(f"{BASE_URL}/user/list?file={payload}")
    test(f"Path Traversal in URL: {payload}", r.status_code == 403 or r.status_code == 400, r)


# ─────────────────────────────────────────────────
separator("4. Command Injection Tests")

cmd_payloads = [
    "| whoami",
    "; cat /etc/passwd",
    "$(whoami)"
]

for payload in cmd_payloads:
    r = session.post(f"{BASE_URL}/login", json={
        "username": payload,
        "password": "AnyPassword1"
    })
    test(f"Command Injection in JSON: {payload}", r.status_code == 403, r)

# ─────────────────────────────────────────────────
total = passed + failed
print(f"\n{'═'*60}")
print(f"  RESULT: {passed}/{total} malicious payloads blocked", end="")
if failed == 0:
    print("\n  🛡️  SUCCESS: WAF is successfully defending the API!")
else:
    print(f"\n  ⚠️  WARNING: {failed} attack(s) bypassed the WAF!")
print(f"{'═'*60}\n")

sys.exit(0 if failed == 0 else 1)
