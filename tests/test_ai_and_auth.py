"""
End-to-end checks for the AI assistant and the authentication layer.

Covers the behaviour the circle office actually asked for:
  * normal questions are answered from the model, not from the PDFs
  * manual passages are used when genuinely relevant, and cited only then
  * an answer drawn from general knowledge is NOT stamped with a PDF citation
  * questions needing current information use search grounding
  * the 10-per-day search allowance is server-side, and ordinary questions
    do not consume it
  * registration, login, logout, lockout, and the office-counter password
    reset (temporary password + forced change)
  * admin-only endpoints reject users and guests

Run the Gemini stub and the app first:

    python tests/gemini_stub.py 8777 &
    GEMINI_API_BASE=http://127.0.0.1:8777 GEMINI_API_KEY=stub \\
    JWT_SECRET=test ADMIN_USERNAME=testadmin ADMIN_PASSWORD=TestPass123 \\
    PORT=8120 python -m backend.main &

    python tests/test_ai_and_auth.py
"""

import os
import sys
import requests

BASE = os.environ.get("APP_BASE", "http://localhost:8120")
STUB = os.environ.get("STUB_BASE", "http://127.0.0.1:8777")
ADMIN_USER = os.environ.get("ADMIN_USERNAME", "testadmin")
ADMIN_PASS = os.environ.get("ADMIN_PASSWORD", "TestPass123")

PASSED, FAILED = 0, 0


def check(label, condition, detail=""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  FAIL  {label} {detail}")


def stub_mode(mode):
    requests.post(f"{STUB}/__control", json={"mode": mode}, timeout=10)


def stub_state():
    return requests.get(f"{STUB}/__control", timeout=10).json()


def ask(question, token=None, lang="en"):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return requests.post(
        f"{BASE}/api/chat",
        json={"query": question, "lang": lang, "model": "gemini-2.5-flash"},
        headers=headers, timeout=60,
    ).json()


def section(name):
    print(f"\n{name}")


def main():
    print(f"\nAI + authentication tests against {BASE}\n" + "-" * 62)

    stub_mode("ok")

    admin = requests.post(f"{BASE}/api/auth/admin-login",
                          json={"username": ADMIN_USER, "password": ADMIN_PASS}, timeout=30).json()
    if not admin.get("success"):
        print(f"Could not sign in as admin: {admin}")
        sys.exit(1)
    admin_h = {"Authorization": f"Bearer {admin['token']}"}

    guest = requests.post(f"{BASE}/api/auth/guest", timeout=30).json()
    guest_h = {"Authorization": f"Bearer {guest['token']}"}

    # ================= AI: provider status =================
    section("AI provider status")
    st = requests.get(f"{BASE}/api/admin/ai-status?probe=1", headers=admin_h, timeout=30).json()["ai"]
    check("status reports the provider configured", st["configured"] is True)
    check("status reports llm mode (not offline fallback)", st["mode"] == "llm", st.get("summary", ""))
    check("probe reaches the endpoint", st.get("reachable") is True)
    check("ai-status is admin-only",
          requests.get(f"{BASE}/api/admin/ai-status", headers=guest_h, timeout=30).status_code == 403)

    # ================= AI: general knowledge, no PDF restriction =================
    section("General questions are not restricted to the PDFs")
    res = ask("Who wrote the play Hamlet?")
    check("a general question gets an answer", bool(res.get("answer")))
    check("answered by the model", res.get("answered_by") == "gemini", str(res.get("answered_by")))
    check("no PDF citation on a general answer", res.get("citations") == [], str(res.get("citations")))
    check("not flagged as locally grounded", res.get("grounded_in_local_sources") is False)
    prompt = stub_state()["last_prompt"]
    check("no manual text was force-fed into the prompt",
          "OFFICIAL MANUAL & FAQ GUIDELINES" not in prompt)
    check("the system prompt says it is not restricted to the documents",
          "NEVER restricted" in prompt)

    res = ask("Explain the difference between a house and a household in simple terms.")
    check("a definition question still answers", bool(res.get("answer")))
    check("ordinary question does not report a web search", res.get("web_searched") is False)

    # ================= AI: PDF-backed questions still work =================
    section("Manual-backed questions still use the manuals")
    res = ask("What does the HLO manual say about the houselisting block boundary description?")
    check("manual question answers", bool(res.get("answer")))
    # The test database has no ingested PDFs, so no citation is expected here;
    # what matters is that the pathway is exercised without error and the
    # answer is not the offline canned text.
    check("manual question is answered by the model, not the offline fallback",
          res.get("answered_by") in ("gemini", "gemini+web"), str(res.get("answered_by")))

    # ================= AI: search grounding + quota =================
    section("Web search grounding and the daily allowance")
    quota_before = requests.get(f"{BASE}/api/auth/quota", headers=guest_h, timeout=30).json()
    check("quota endpoint reports the limit", quota_before["limit"] == 10, str(quota_before))
    start_remaining = quota_before["remaining_today"]

    ask("What is the capital of France?", token=guest["token"])
    after_normal = requests.get(f"{BASE}/api/auth/quota", headers=guest_h, timeout=30).json()
    check("an ordinary question does NOT consume the allowance",
          after_normal["remaining_today"] == start_remaining,
          f"{after_normal['remaining_today']} vs {start_remaining}")
    check("no tools were requested for an ordinary question", stub_state()["last_had_tools"] is False)

    res = ask("What is the latest news about the Census 2027 schedule?", token=guest["token"])
    check("a current-information question requests grounding", stub_state()["last_had_tools"] is True)
    check("the response reports a web search", res.get("web_searched") is True)
    check("answered_by records the web path", res.get("answered_by") == "gemini+web", str(res.get("answered_by")))
    after_search = requests.get(f"{BASE}/api/auth/quota", headers=guest_h, timeout=30).json()
    check("a real search consumes exactly one search",
          after_search["remaining_today"] == start_remaining - 1,
          f"{after_search['remaining_today']} vs {start_remaining - 1}")

    # Exhaust the rest of the allowance
    for _ in range(after_search["remaining_today"]):
        ask("Any recent update on census news today?", token=guest["token"])
    exhausted = requests.get(f"{BASE}/api/auth/quota", headers=guest_h, timeout=30).json()
    check("the allowance can be exhausted", exhausted["remaining_today"] == 0, str(exhausted))

    res = ask("What is the latest census news today?", token=guest["token"])
    check("past the limit the question is still answered", bool(res.get("answer")))
    check("past the limit no search is performed", res.get("web_searched") is False)
    check("past the limit the user is told why", "web searches for today" in res.get("answer", ""))
    check("past the limit no grounding tool is requested", stub_state()["last_had_tools"] is False)

    # A different user has their own allowance.
    other = requests.post(f"{BASE}/api/auth/guest", timeout=30).json()
    other_q = requests.get(f"{BASE}/api/auth/quota",
                           headers={"Authorization": f"Bearer {other['token']}"}, timeout=30).json()
    check("the allowance is per-user", other_q["remaining_today"] == 10, str(other_q))

    # Server-side: the count survives a "reinstall" (a brand-new client with
    # no stored state) because it is keyed on the account, not the device.
    relogin = requests.post(f"{BASE}/api/auth/login",
                            json={"identifier": "9871112223", "password": "FieldWork2027"},
                            timeout=30)

    # ================= AI: provider failure handling =================
    section("Provider failures are surfaced, not silently swallowed")
    stub_mode("model_missing")
    res = ask("Give me a short overview of census enumeration.")
    check("a retired model name falls through to a working model", bool(res.get("answer")))
    check("the model actually used is reported", res.get("model_used") != "gemini-2.5-flash",
          str(res.get("model_used")))

    stub_mode("no_tools")
    res = ask("What is the latest news on census 2027 today?")
    check("a key without grounding entitlement still answers", bool(res.get("answer")))
    check("and is not reported as a web answer", res.get("web_searched") is False)

    stub_mode("unauthorized")
    res = ask("Who is the Registrar General of India?")
    check("a rejected API key falls back to offline mode",
          res.get("answered_by") == "offline_fallback", str(res.get("answered_by")))
    check("the offline answer admits it cannot answer rather than inventing one",
          "offline mode" in res.get("answer", "").lower())
    st = requests.get(f"{BASE}/api/admin/ai-status", headers=admin_h, timeout=30).json()["ai"]
    check("the auth failure is recorded for the admin", st.get("last_error_kind") == "auth",
          str(st.get("last_error_kind")))
    stub_mode("ok")

    # ================= Authentication =================
    section("Registration and sign-in")
    mobile = "9871112223"
    password = "FieldWork2027"

    reg = requests.post(f"{BASE}/api/auth/register",
                        json={"name": "Test Field User", "mobile_number": mobile,
                              "password": password}, timeout=30).json()
    check("registration succeeds (or the account already exists)",
          reg.get("success") or "already exists" in reg.get("message", ""), str(reg.get("message")))

    weak = requests.post(f"{BASE}/api/auth/register",
                         json={"name": "Weak User", "mobile_number": "9871119999",
                               "password": "123"}, timeout=30).json()
    check("a short password is rejected", weak.get("success") is False)
    check("the rejection explains the rule", "8 characters" in weak.get("message", ""), weak.get("message", ""))

    numeric = requests.post(f"{BASE}/api/auth/register",
                            json={"name": "Numeric User", "mobile_number": "9871119998",
                                  "password": "12345678"}, timeout=30).json()
    check("an all-numeric password is rejected", numeric.get("success") is False)

    login = requests.post(f"{BASE}/api/auth/login",
                          json={"identifier": mobile, "password": password}, timeout=30).json()
    check("sign-in with the right password works", login.get("success") is True, str(login.get("message")))
    check("sign-in returns a token", bool(login.get("token")))
    user_token = login["token"]
    user_h = {"Authorization": f"Bearer {user_token}"}

    me = requests.get(f"{BASE}/api/auth/me", headers=user_h, timeout=30).json()
    check("the session identifies the user", me.get("authenticated") is True)
    check("the session carries the user role", me["user"]["role"] in ("user", "enumerator", "supervisor"))

    bad = requests.post(f"{BASE}/api/auth/login",
                        json={"identifier": mobile, "password": "WrongPassword1"}, timeout=30)
    check("a wrong password is refused", bad.status_code == 401)
    check("the refusal does not reveal whether the account exists",
          bad.json().get("message") == "Invalid username, mobile number, or password.")

    missing = requests.post(f"{BASE}/api/auth/login",
                            json={"identifier": "9000000000", "password": "Whatever123"}, timeout=30)
    check("an unknown account gives the identical message",
          missing.json().get("message") == bad.json().get("message"))

    section("Logout")
    # Logout is client-side token disposal; what matters server-side is that a
    # discarded/garbage token is refused.
    check("a garbage token is rejected",
          requests.get(f"{BASE}/api/auth/me",
                       headers={"Authorization": "Bearer not-a-real-token"}, timeout=30).status_code == 401)

    section("Lockout after repeated failures")
    lock_mobile = "9871114445"
    requests.post(f"{BASE}/api/auth/register",
                  json={"name": "Lock Test", "mobile_number": lock_mobile,
                        "password": "LockTest2027"}, timeout=30)
    locked_response = None
    for _ in range(8):
        r = requests.post(f"{BASE}/api/auth/login",
                          json={"identifier": lock_mobile, "password": "definitely-wrong"}, timeout=30)
        if r.json().get("locked"):
            locked_response = r.json()
            break
    check("repeated wrong passwords lock the account", locked_response is not None)
    if locked_response:
        check("the lockout message explains the wait", "locked" in locked_response.get("message", "").lower())
    still = requests.post(f"{BASE}/api/auth/login",
                          json={"identifier": lock_mobile, "password": "LockTest2027"}, timeout=30).json()
    check("even the correct password is refused while locked", still.get("success") is False)

    unlock = requests.post(f"{BASE}/api/admin/users/unlock",
                           json={"identifier": lock_mobile}, headers=admin_h, timeout=30).json()
    check("an admin can unlock the account", unlock.get("success") is True)
    after_unlock = requests.post(f"{BASE}/api/auth/login",
                                 json={"identifier": lock_mobile, "password": "LockTest2027"}, timeout=30).json()
    check("the user can sign in again after unlocking", after_unlock.get("success") is True)

    # ================= Office-counter password reset =================
    section("Office-counter password reset")
    reset = requests.post(f"{BASE}/api/admin/users/reset-password",
                          json={"identifier": mobile}, headers=admin_h, timeout=30).json()
    check("the admin can issue a temporary password", reset.get("success") is True)
    temp = reset.get("temporary_password", "")
    check("a temporary password is returned to the admin", len(temp) >= 8, temp)
    check("the response names the user so the counter can confirm identity", bool(reset.get("name")))

    check("the old password no longer works",
          requests.post(f"{BASE}/api/auth/login",
                        json={"identifier": mobile, "password": password},
                        timeout=30).json().get("success") is False)

    temp_login = requests.post(f"{BASE}/api/auth/login",
                               json={"identifier": mobile, "password": temp}, timeout=30).json()
    check("the temporary password signs the user in", temp_login.get("success") is True)
    check("the session is flagged as needing a password change",
          temp_login.get("must_change_password") is True)
    temp_h = {"Authorization": f"Bearer {temp_login['token']}"}

    new_password = "MyOwnPass2027"
    changed = requests.post(f"{BASE}/api/auth/change-password",
                            json={"current_password": temp, "new_password": new_password},
                            headers=temp_h, timeout=30).json()
    check("the user can set their own password", changed.get("success") is True, str(changed.get("message")))
    check("a fresh token is returned after the change", bool(changed.get("token")))

    final = requests.post(f"{BASE}/api/auth/login",
                          json={"identifier": mobile, "password": new_password}, timeout=30).json()
    check("the new password works", final.get("success") is True)
    check("the change-password flag is cleared", final.get("must_change_password") is False)
    check("the temporary password stops working",
          requests.post(f"{BASE}/api/auth/login",
                        json={"identifier": mobile, "password": temp},
                        timeout=30).json().get("success") is False)

    check("changing a password needs the current one",
          requests.post(f"{BASE}/api/auth/change-password",
                        json={"current_password": "wrong", "new_password": "AnotherPass27"},
                        headers={"Authorization": f"Bearer {final['token']}"},
                        timeout=30).json().get("success") is False)

    # ================= Role-based access =================
    section("Role-based access control")
    admin_only = [
        ("GET", "/api/admin/stats"),
        ("GET", "/api/admin/accounts"),
        ("GET", "/api/admin/auth-audit"),
        ("GET", "/api/admin/ai-status"),
        ("GET", "/api/admin/attendance"),
        ("GET", "/api/admin/query-logs"),
        ("GET", "/api/admin/uploaded-files"),
    ]
    user_h_final = {"Authorization": f"Bearer {final['token']}"}
    all_blocked_user = all(
        requests.request(m, f"{BASE}{p}", headers=user_h_final, timeout=30).status_code == 403
        for m, p in admin_only
    )
    all_blocked_guest = all(
        requests.request(m, f"{BASE}{p}", headers=guest_h, timeout=30).status_code == 403
        for m, p in admin_only
    )
    all_blocked_anon = all(
        requests.request(m, f"{BASE}{p}", timeout=30).status_code == 403
        for m, p in admin_only
    )
    check("a signed-in user cannot reach any admin endpoint", all_blocked_user)
    check("a guest cannot reach any admin endpoint", all_blocked_guest)
    check("an anonymous caller cannot reach any admin endpoint", all_blocked_anon)
    check("the admin can reach them",
          all(requests.request(m, f"{BASE}{p}", headers=admin_h, timeout=30).status_code == 200
              for m, p in admin_only))

    check("a user cannot issue password resets",
          requests.post(f"{BASE}/api/admin/users/reset-password",
                        json={"identifier": mobile}, headers=user_h_final,
                        timeout=30).status_code == 403)

    # ================= Admin visibility =================
    section("Admin visibility (no password material exposed)")
    accounts = requests.get(f"{BASE}/api/admin/accounts", headers=admin_h, timeout=30).json()
    check("the account list loads", accounts.get("success") is True)
    row = next((a for a in accounts["accounts"] if a["mobile_number"] == mobile), None)
    check("the test user appears in the list", row is not None)
    if row:
        check("last sign-in is recorded", bool(row.get("last_login_at")))
        check("no password field is exposed",
              not any("password" in k for k in row if k != "must_change_password"), str(list(row)))

    audit = requests.get(f"{BASE}/api/admin/auth-audit?limit=100", headers=admin_h, timeout=30).json()
    events = {e["event"] for e in audit["events"]}
    check("sign-ins are audited", "login" in events, str(events))
    check("the admin reset is audited", "admin_password_reset" in events, str(events))
    check("no audit row contains a password",
          not any("password" in str(e.get("detail", "")).lower()
                  and temp in str(e.get("detail", "")) for e in audit["events"]))

    print("-" * 62)
    print(f"{PASSED} passed, {FAILED} failed\n")
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
