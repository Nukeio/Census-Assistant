"""
Verifies the manual/PDF grounding behaviour after the relevance gate.

The risk in making retrieval relevance-gated is over-correcting: if the bar is
too high, genuine manual questions stop being answered from the manuals. This
seeds a handful of realistic HLO/FAQ passages and checks both directions —

  * a question the manuals genuinely answer IS grounded in them and cited
  * a question they do not answer is NOT dressed up with a manual citation
    just because it shares a common word like "house" or "form"

Run against a server started on the same database:

    python tests/test_pdf_grounding.py
"""

import os
import sys
import sqlite3
import requests

BASE = os.environ.get("APP_BASE", "http://localhost:8121")
DB_PATH = os.environ.get(
    "CENSUS_DB",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "census_assistant.db"),
)

PASSED, FAILED = 0, 0

SEED_CHUNKS = [
    (
        "HLO_Manual_English.pdf", "HLO Manual (English)", 42,
        "Definition of Census House",
        "A Census House is a building or part of a building having a separate main entrance "
        "from the road or common courtyard or staircase, used or recognised as a separate unit. "
        "It may be occupied or vacant. It may be used for a residential or non-residential purpose "
        "or both. The enumerator must record every Census House in the houselisting block.",
    ),
    (
        "HLO_Manual_English.pdf", "HLO Manual (English)", 57,
        "Boundary Description of Houselisting Block",
        "Every houselisting block must have a clearly written boundary description recording the "
        "north, south, east and west limits of the block using permanent landmarks such as roads, "
        "canals, temples or schools. The boundary description must be verified by the supervisor "
        "before the enumerator begins houselisting operations.",
    ),
    (
        "FAQ.pdf", "Census FAQ (Enumerators & Supervisors)", 9,
        "Use of Pencil in Schedules",
        "All entries in the houselisting schedule must be made in black lead pencil only. "
        "Ink pens are not permitted because entries may need correction during supervisory checks.",
    ),
]


def check(label, condition, detail=""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  FAIL  {label} {detail}")


def seed_manual_chunks():
    """Insert the passages and rebuild the FTS index the way startup does."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("DELETE FROM manual_chunks WHERE source_file IN ('HLO_Manual_English.pdf', 'FAQ.pdf')")
    for source_file, doc_title, page, header, text in SEED_CHUNKS:
        cur.execute("""
            INSERT INTO manual_chunks (source_file, doc_title, page_number, section_header, chunk_text)
            VALUES (?, ?, ?, ?, ?)
        """, (source_file, doc_title, page, header, text))
    cur.execute("DROP TABLE IF EXISTS manual_chunks_fts")
    cur.execute("""
        CREATE VIRTUAL TABLE manual_chunks_fts USING fts5(
            source_file, doc_title, page_number, section_header, chunk_text,
            content='manual_chunks', content_rowid='id',
            tokenize = 'porter unicode61'
        )
    """)
    cur.execute("INSERT INTO manual_chunks_fts(manual_chunks_fts) VALUES('rebuild')")
    conn.commit()
    count = cur.execute("SELECT COUNT(*) FROM manual_chunks").fetchone()[0]
    conn.close()
    return count


def ask(question):
    return requests.post(
        f"{BASE}/api/chat",
        json={"query": question, "lang": "en", "model": "gemini-2.5-flash"},
        timeout=60,
    ).json()


def main():
    print(f"\nPDF grounding tests against {BASE}\n" + "-" * 62)
    seeded = seed_manual_chunks()
    check("manual passages seeded into the database", seeded >= len(SEED_CHUNKS), str(seeded))

    print("\nQuestions the manuals genuinely answer")
    res = ask("What is the definition of a Census House?")
    check("the manual question is answered", bool(res.get("answer")))
    check("it is grounded in local sources", res.get("grounded_in_local_sources") is True,
          str(res.get("citations")))
    check("the HLO Manual is cited",
          any("HLO Manual" in c for c in res.get("citations", [])), str(res.get("citations")))
    check("the citation names the page",
          any("Page 42" in c for c in res.get("citations", [])), str(res.get("citations")))

    res = ask("What must the boundary description of a houselisting block contain?")
    check("a second manual question is grounded", res.get("grounded_in_local_sources") is True,
          str(res.get("citations")))
    check("it cites the right page",
          any("Page 57" in c for c in res.get("citations", [])), str(res.get("citations")))

    res = ask("Which pencil should be used to fill the houselisting schedule?")
    check("the FAQ question is grounded", res.get("grounded_in_local_sources") is True,
          str(res.get("citations")))
    check("the FAQ is cited",
          any("FAQ" in c for c in res.get("citations", [])), str(res.get("citations")))

    print("\nQuestions the manuals do NOT answer")
    # Each of these shares a common word with a seeded passage ("house",
    # "form", "supervisor", "school") — precisely the overlap that used to be
    # enough to drag a manual chunk in and stamp a citation on the answer.
    for question in [
        "Who wrote the play Hamlet?",
        "What is the capital city of Australia?",
        "How do I form a good habit of waking up early?",
        "What is the population of Japan?",
    ]:
        res = ask(question)
        check(f"no manual citation on: {question[:44]!r}",
              res.get("citations") == [], str(res.get("citations")))

    res = ask("Explain in general terms why a national census matters.")
    check("a general census question is answered without a PDF citation",
          bool(res.get("answer")) and res.get("citations") == [], str(res.get("citations")))
    check("and it is answered by the model", res.get("answered_by") == "gemini",
          str(res.get("answered_by")))

    print("\nThe manuals remain browsable regardless")
    search = requests.get(f"{BASE}/api/manuals/search", params={"q": "census house"}, timeout=30)
    check("manual search still returns passages", search.status_code == 200 and
          len(search.json().get("results", [])) > 0, search.text[:120])

    print("-" * 62)
    print(f"{PASSED} passed, {FAILED} failed\n")
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
