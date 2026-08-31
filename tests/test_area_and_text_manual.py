"""
Tests for area/village search and text-manual ingestion.

Area search
-----------
Village and ward names live in hlb_descriptions, not on the functionary or
the allocation, so finding "who works in Bhairabpur" means driving off that
table and joining outwards. These tests cover the dedicated Area filter, the
All filter picking area up without the user switching filters, and the
Supervisor tab answering "who supervises that place?".

Text manuals
------------
The HLO manual PDF is a scan: every page yields only the print shop's job
ticket, so nothing usable can be indexed from it. These tests cover the
replacement route — upload OCR'd text, have it indexed with real page
numbers, and have the assistant quote and cite it — plus the guard that stops
a scanned PDF filling the index with printer boilerplate.

Run against a server on the same database:

    python tests/test_area_and_text_manual.py
"""

import io
import os
import sys
import sqlite3
import requests

BASE = os.environ.get("APP_BASE", "http://localhost:8140")
ADMIN_USER = os.environ.get("ADMIN_USERNAME", "testadmin")
ADMIN_PASS = os.environ.get("ADMIN_PASSWORD", "TestPass123")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("CENSUS_DB", os.path.join(ROOT, "census_assistant.db"))

PASSED, FAILED = 0, 0


def check(label, condition, detail=""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  FAIL  {label} {detail}")


# (hlb_no, village, landmark, boundary, enumerator, supervisor, circle)
FIXTURE = [
    ("0142", "Bhairabpur (12)", "Bhairabpur LP School",
     "North: Kalain Road, South: paddy field, East: Bhairabpur LP School, West: canal",
     "Abdul Baten", "S. A. Ahmed", "07"),
    ("0143", "Bhairabpur (12)", "Bhairabpur Market",
     "North: canal, South: Kalain Road, East: market shed, West: village path",
     "Rina Devi", "S. A. Ahmed", "07"),
    ("0155", "Jarailtola", "Jarailtola Namghar",
     "North: hillock, South: Jarailtola Namghar, East: tea garden, West: stream",
     "Nabin Sharma", "Hasina Begum", "09"),
    ("0161", "Katigorah Part-II", "Katigorah Bazar",
     "North: NH-6, South: Katigorah Bazar, East: mosque, West: pond",
     "Rekha Bora", "Hasina Begum", "09"),
]


def seed():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()
    cur.execute("DELETE FROM hlb_descriptions")
    cur.execute("DELETE FROM hlb_allocations")
    cur.execute("DELETE FROM functionaries")

    for hlb, village, landmark, boundary, enum_name, sup_name, circle in FIXTURE:
        enum_id = f"en_{hlb}"
        sup_id = f"sv_{circle}"
        cur.execute("""INSERT OR IGNORE INTO functionaries
            (user_id, functionary_type, name, mobile_number, district, sub_district, village_town, status)
            VALUES (?, 'Enumerator', ?, ?, 'Cachar', 'Lakhipur', ?, 'ACTIVE')""",
            (enum_id, enum_name, f"90000{hlb}", village.split(" (")[0]))
        cur.execute("""INSERT OR IGNORE INTO functionaries
            (user_id, functionary_type, name, mobile_number, district, sub_district, village_town, status)
            VALUES (?, 'Supervisor', ?, ?, 'Cachar', 'Lakhipur', 'Lakhipur', 'ACTIVE')""",
            (sup_id, sup_name, f"98000{circle}0000"[:10]))
        cur.execute("""INSERT OR REPLACE INTO hlb_allocations
            (supervisory_circle_no, hlb_no, supervisor_name, enumerator_name, enumerator_user_id, allotment_date)
            VALUES (?, ?, ?, ?, ?, '2027-01-15')""",
            (circle, hlb, sup_name, enum_name, enum_id))
        cur.execute("""INSERT OR REPLACE INTO hlb_descriptions
            (hlb_no, village_ward_name, landmark, boundary_description)
            VALUES (?, ?, ?, ?)""", (hlb, village, landmark, boundary))

    conn.commit()
    n = cur.execute("SELECT COUNT(*) FROM hlb_descriptions").fetchone()[0]
    conn.close()
    return n


def search(q, filter_by="all"):
    return requests.get(f"{BASE}/api/records/search",
                        params={"q": q, "filter": filter_by}, timeout=30).json()


def main():
    print(f"\nArea search + text manual tests against {BASE}\n" + "-" * 62)
    check("fixture seeded", seed() == len(FIXTURE))

    admin = requests.post(f"{BASE}/api/auth/admin-login",
                          json={"username": ADMIN_USER, "password": ADMIN_PASS}, timeout=30).json()
    if not admin.get("success"):
        print(f"admin login failed: {admin}")
        sys.exit(1)
    admin_h = {"Authorization": f"Bearer {admin['token']}"}

    # ---------------- Area filter ----------------
    print("\nArea / village filter on Search Records")
    res = search("Bhairabpur", "area")
    names = [r["name"] for r in res["results"]]
    check("village name returns its blocks", res["total"] == 2, f"total={res['total']}")
    check("both enumerators for that village are listed",
          {"Abdul Baten", "Rina Devi"} == set(names), str(names))
    check("results carry the HLB numbers", {r["hlb_number"] for r in res["results"]} == {"0142", "0143"})
    check("results carry the supervisor", all(r["supervisor"] == "S. A. Ahmed" for r in res["results"]))
    check("area name is returned for display",
          all(r["area_name"] == "Bhairabpur" for r in res["results"]),
          str([r["area_name"] for r in res["results"]]))
    check("boundary description is returned",
          all("Kalain Road" in r["boundary_description"] or "canal" in r["boundary_description"]
              for r in res["results"]))
    check("a map link is built", all(r["maps_url"] for r in res["results"]))

    res = search("Jarailtola", "area")
    check("a second village resolves independently",
          res["total"] == 1 and res["results"][0]["name"] == "Nabin Sharma", str(res["total"]))

    res = search("Namghar", "area")
    check("a landmark finds the block", res["total"] == 1 and res["results"][0]["hlb_number"] == "0155")

    res = search("tea garden", "area")
    check("a boundary-only landmark finds the block (field staff know blocks by these)",
          res["total"] == 1 and res["results"][0]["hlb_number"] == "0155", str(res["total"]))

    res = search("Katigorah", "area")
    check("a ward with a Part suffix matches", res["total"] == 1)
    check("the ward suffix is stripped for display",
          res["results"][0]["area_name"] == "Katigorah Part-II", res["results"][0]["area_name"])

    check("an unknown village returns nothing", search("Nowhereville", "area")["total"] == 0)
    check("area search paginates cleanly",
          "page" in search("Bhairabpur", "area") and search("Bhairabpur", "area")["filter"] == "area")

    # ---------------- All filter picks up area ----------------
    print("\nThe All filter finds an area without switching filters")
    res = search("Bhairabpur", "all")
    check("village name works under All", res["total"] >= 2, f"total={res['total']}")
    check("the right people come back",
          {"Abdul Baten", "Rina Devi"} <= {r["name"] for r in res["results"]},
          str([r["name"] for r in res["results"]]))
    check("name search still works under All",
          any(r["name"] == "Abdul Baten" for r in search("Abdul Baten", "all")["results"]))
    check("HLB number search still works under All",
          search("0142", "all")["results"][0]["hlb_number"] == "0142")
    check("mobile search still works under All", search("900000142", "all")["total"] >= 1)

    # ---------------- Supervisor tab ----------------
    print("\nArea search on the Supervisor tab")
    sup = requests.get(f"{BASE}/api/records/supervisor", params={"q": "Bhairabpur"}, timeout=30).json()
    sup_names = [s["name"] for s in sup.get("supervisors", [])]
    check("a village finds the supervisor covering it",
          sup_names == ["S. A. Ahmed"], str(sup_names))

    sup = requests.get(f"{BASE}/api/records/supervisor", params={"q": "Jarailtola"}, timeout=30).json()
    check("a different village finds a different supervisor",
          [s["name"] for s in sup.get("supervisors", [])] == ["Hasina Begum"],
          str([s["name"] for s in sup.get("supervisors", [])]))

    sup = requests.get(f"{BASE}/api/records/supervisor", params={"q": "Katigorah Bazar"}, timeout=30).json()
    check("a landmark finds the supervisor",
          [s["name"] for s in sup.get("supervisors", [])] == ["Hasina Begum"])

    sup = requests.get(f"{BASE}/api/records/supervisor", params={"q": "Hasina"}, timeout=30).json()
    check("supervisor name search still works",
          [s["name"] for s in sup.get("supervisors", [])] == ["Hasina Begum"])

    sup = requests.get(f"{BASE}/api/records/supervisor", params={"q": "07"}, timeout=30).json()
    check("circle-number search still works",
          [s["name"] for s in sup.get("supervisors", [])] == ["S. A. Ahmed"],
          str([s["name"] for s in sup.get("supervisors", [])]))

    check("an unknown village finds no supervisor",
          requests.get(f"{BASE}/api/records/supervisor",
                       params={"q": "Nowhereville"}, timeout=30).json().get("supervisors") == [])

    # ---------------- The AI area path (previously crashed) ----------------
    print("\nThe assistant's area lookup no longer crashes")
    chat = requests.post(f"{BASE}/api/chat",
                         json={"query": "Which enumerator covers Bhairabpur LP School?", "lang": "en"},
                         timeout=60)
    check("an area question returns 200 rather than a server error",
          chat.status_code == 200, f"HTTP {chat.status_code}")
    check("and produces an answer", bool(chat.json().get("answer")))

    # ---------------- Text manual ingestion ----------------
    print("\nUploading a manual as text")
    manual = (
        "===== PAGE 41 =====\n"
        "Q. 14: OWNERSHIP STATUS OF THIS HOUSE\n\n"
        "Record the ownership status of the census house occupied by the household. "
        "Write code 1 for owned, 2 for rented and 3 for any other status. A house "
        "provided by an employer is treated as rented for this purpose.\n\n"
        "===== PAGE 57 =====\n"
        "Q. 20: ACCESS TO LATRINE\n\n"
        "Ascertain whether the household has access to a latrine within the premises. "
        "If the household uses a public latrine, record code 6. If members resort to "
        "open defecation, record code 7 and note the reason in the remarks column.\n"
    )
    files = {"file": ("HLO_Manual_OCR.txt", io.BytesIO(manual.encode()), "text/plain")}
    up = requests.post(f"{BASE}/api/admin/upload-text", files=files, headers=admin_h, timeout=60).json()
    check("the text manual uploads", up.get("success") is True, str(up))
    check("chunks are indexed", (up.get("chunks") or 0) >= 2, str(up.get("chunks")))

    check("text upload is admin-only",
          requests.post(f"{BASE}/api/admin/upload-text", files={
              "file": ("x.txt", io.BytesIO(b"hello world this is a test"), "text/plain")
          }, timeout=30).status_code == 403)

    bad = requests.post(f"{BASE}/api/admin/upload-text", files={
        "file": ("notes.exe", io.BytesIO(b"binary"), "application/octet-stream")
    }, headers=admin_h, timeout=30)
    check("a non-text extension is refused", bad.status_code == 400)

    print("\nThe assistant can now answer from the manual text")
    search_res = requests.get(f"{BASE}/api/manuals/search", params={"q": "latrine"}, timeout=30).json()
    check("manual search finds the OCR'd text", len(search_res.get("results", [])) >= 1, str(search_res)[:150])

    ans = requests.post(f"{BASE}/api/chat",
                        json={"query": "What code is recorded when a household uses a public latrine?",
                              "lang": "en"}, timeout=60).json()
    check("the question is grounded in the manual",
          ans.get("grounded_in_local_sources") is True, str(ans.get("citations")))
    check("the citation keeps the printed page number",
          any("Page 57" in c for c in ans.get("citations", [])), str(ans.get("citations")))

    ans = requests.post(f"{BASE}/api/chat",
                        json={"query": "How is ownership status of a house recorded?", "lang": "en"},
                        timeout=60).json()
    check("a second manual question cites its own page",
          any("Page 41" in c for c in ans.get("citations", [])), str(ans.get("citations")))

    ans = requests.post(f"{BASE}/api/chat",
                        json={"query": "Who wrote the play Hamlet?", "lang": "en"}, timeout=60).json()
    check("an unrelated question is not given a manual citation",
          ans.get("citations") == [], str(ans.get("citations")))

    # ---------------- Scanned PDF guard ----------------
    print("\nA scanned PDF no longer pollutes the index")
    from backend.ingestion import _is_pdf_boilerplate
    check("the real job ticket is recognised as boilerplate",
          _is_pdf_boilerplate("Tender Work F Instruction Manual ENGLISH AU-136PAGE DGT.job\n Sig13 SideA"))
    check("a short scrap of text is not indexed", _is_pdf_boilerplate("Page 12"))
    check("genuine manual prose is NOT treated as boilerplate",
          not _is_pdf_boilerplate(
              "Record the ownership status of the census house occupied by the household. "
              "Write code 1 for owned, 2 for rented and 3 for any other status, and make sure "
              "the entry is legible in black lead pencil."))

    conn = sqlite3.connect(DB_PATH)
    junk = conn.execute(
        "SELECT COUNT(*) FROM manual_chunks WHERE chunk_text LIKE '%SideA%' OR chunk_text LIKE '%.job%'"
    ).fetchone()[0]
    conn.close()
    check("no printer boilerplate sits in the manual index", junk == 0, f"{junk} junk chunks")

    print("-" * 62)
    print(f"{PASSED} passed, {FAILED} failed\n")
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    sys.path.insert(0, ROOT)
    main()
