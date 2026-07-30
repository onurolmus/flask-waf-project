"""
Flask RESTful API — Automated Test Suite
Run with: python tests/test_api.py
Requires the application to be running (docker compose up -d).
"""

import requests
import sys
import time
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
test_username = f"testuser_{random.randint(10000, 99999)}"

passed = 0
failed = 0

def safe_json(response):
    try:
        return response.json()
    except Exception:
        return {}

def test(name, condition, response=None):
    global passed, failed
    if condition:
        print(f"  ✅ PASS | {name}")
        passed += 1
    else:
        print(f"  ❌ FAIL | {name}")
        if response is not None:
            print(f"          Response: {response.status_code} → {response.text[:200]}")
        failed += 1


def separator(title):
    print(f"\n{'─'*50}")
    print(f"  {title}")
    print(f"{'─'*50}")


# ─────────────────────────────────────────────────
separator("POST /user/create")

session.delete(f"{BASE_URL}/user/delete/999")

r = session.post(f"{BASE_URL}/user/create", json={
    "username": test_username,
    "firstname": "Test",
    "lastname": "User",
    "birthdate": "1995-05-15",
    "email": f"{test_username}@example.com",
    "password": "Secure123"
})
test("Valid data creates a user (201)", r.status_code == 201, r)
test("Response contains 'message'", "message" in safe_json(r), r)
test("Response contains 'user'", "user" in safe_json(r), r)
test("Password hash not exposed in response", "password_hash" not in safe_json(r).get("user", {}), r)

user_id = safe_json(r).get("user", {}).get("id")

# Active-Active veritabanlarında senkronizasyonun (Bucardo) tamamlanması için bekle
time.sleep(1.5)

r = session.post(f"{BASE_URL}/user/create", json={
    "username": test_username,
    "firstname": "Test",
    "lastname": "User",
    "birthdate": "1995-05-15",
    "email": "different@example.com",
    "password": "Secure123"
})
test("Duplicate username rejected (409)", r.status_code == 409, r)

r = session.post(f"{BASE_URL}/user/create", json={
    "username": "testuser2",
    "firstname": "Test",
    "lastname": "User",
    "birthdate": "1995-05-15",
    "email": "invalid-email",
    "password": "Secure123"
})
test("Invalid email format rejected (400)", r.status_code == 400, r)

r = session.post(f"{BASE_URL}/user/create", json={
    "username": "testuser3",
    "firstname": "Test",
    "lastname": "User",
    "birthdate": "1995-05-15",
    "email": "testuser3@example.com",
    "password": "weak"
})
test("Weak password rejected (400)", r.status_code == 400, r)

r = session.post(f"{BASE_URL}/user/create", json={"username": "testuser4"})
test("Missing required fields rejected (400)", r.status_code == 400, r)

# ─────────────────────────────────────────────────
separator("GET /user/list")

r = session.get(f"{BASE_URL}/user/list")
test("User list returned (200)", r.status_code == 200, r)
test("Response contains 'users' list", "users" in safe_json(r), r)
test("List is not empty", len(safe_json(r).get("users", [])) > 0, r)

# ─────────────────────────────────────────────────
separator("PUT /user/update/<id>")

r = session.put(f"{BASE_URL}/user/update/{user_id}", json={"firstname": "Updated"})
test("User updated (200)", r.status_code == 200, r)
test("Updated field reflects new value", safe_json(r).get("user", {}).get("firstname") == "Updated", r)

r = session.put(f"{BASE_URL}/user/update/99999", json={"firstname": "Ghost"})
test("Non-existent user returns 404", r.status_code == 404, r)

# ─────────────────────────────────────────────────
separator("POST /login")

r = session.post(f"{BASE_URL}/login", json={
    "username": test_username,
    "password": "Secure123"
})
test("Valid credentials accepted (200)", r.status_code == 200, r)
test("Response contains 'ip'", "ip" in safe_json(r), r)
test("Response contains 'message'", "message" in safe_json(r), r)

r = session.post(f"{BASE_URL}/login", json={
    "username": test_username,
    "password": "WrongPassword99"
})
test("Wrong password rejected (401)", r.status_code == 401, r)
test("Error does not reveal username existence",
     safe_json(r).get("error") == "Invalid username or password.", r)

r = session.post(f"{BASE_URL}/login", json={
    "username": "nonexistent_user",
    "password": "AnyPassword1"
})
test("Non-existent user returns same 401 error",
     r.status_code == 401 and safe_json(r).get("error") == "Invalid username or password.", r)

# Senkronizasyon beklemesi
time.sleep(1.5)

# ─────────────────────────────────────────────────
separator("GET /onlineusers")

r = session.get(f"{BASE_URL}/onlineusers")
test("Online users returned (200)", r.status_code == 200, r)
test("Response contains 'online_count'", "online_count" in safe_json(r), r)
test("Response contains 'online_users'", "online_users" in safe_json(r), r)
test("testuser is in online list", any(
    u["username"] == test_username
    for u in safe_json(r).get("online_users", [])
), r)

# Senkronizasyon beklemesi
time.sleep(1.5)

# ─────────────────────────────────────────────────
separator("POST /logout")

r = session.post(f"{BASE_URL}/logout", json={"username": test_username})
test("Logout successful (200)", r.status_code == 200, r)

# Senkronizasyon beklemesi
time.sleep(1.5)

r = session.post(f"{BASE_URL}/logout", json={"username": test_username})
test("Already logged out user returns 404", r.status_code == 404, r)

# Senkronizasyon beklemesi
time.sleep(1.5)

r = session.get(f"{BASE_URL}/onlineusers")
test("User removed from online list after logout", not any(
    u["username"] == test_username
    for u in safe_json(r).get("online_users", [])
), r)

# ─────────────────────────────────────────────────
separator("DELETE /user/delete/<id>")

r = session.delete(f"{BASE_URL}/user/delete/{user_id}")
test("User deleted (200)", r.status_code == 200, r)

# Senkronizasyon beklemesi
time.sleep(1.5)

r = session.delete(f"{BASE_URL}/user/delete/{user_id}")
test("Deleted user cannot be deleted again (404)", r.status_code == 404, r)

# ─────────────────────────────────────────────────
total = passed + failed
print(f"\n{'═'*50}")
print(f"  RESULT: {passed}/{total} tests passed", end="")
if failed == 0:
    print(" 🎉 All tests passed!")
else:
    print(f" ⚠️  {failed} test(s) failed!")
print(f"{'═'*50}\n")

sys.exit(0 if failed == 0 else 1)
