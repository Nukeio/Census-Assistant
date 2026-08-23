"""
Census Assistant - RAG Engine
Handles Intent Detection, Structured Entity Search, PDF Manual Semantic Retrieval, Citation Generation, and Prompt Formulation.
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional
from .database import get_db_connection
from .messaging_gateway import TECHNICAL_ASSISTANTS

logger = logging.getLogger("RAGEngine")
logging.basicConfig(level=logging.INFO)

# Intent definitions
INTENT_RECORD_SEARCH = "RECORD_SEARCH"
INTENT_MANUAL_SEARCH = "MANUAL_SEARCH"
INTENT_SUPERVISOR_QUERY = "SUPERVISOR_QUERY"
INTENT_GENERAL = "GENERAL"

def detect_intent(query: str) -> str:
    """Classify user query intent."""
    q = query.lower()
    
    # HLB (formerly "EB") or Enumerator / Record lookup. The "eb" alias is
    # still recognized so old queries/links keep working, but every
    # response now speaks in HLB terms only.
    if re.search(r'\b(eb\s*\d+|hlb\s*\d+|block\s*\d+|assigned to|enumerator|charge user|who is in charge)\b', q):
        return INTENT_RECORD_SEARCH

    # Supervisor specific query. Note: "S. A. Ahmed" is NOT a supervisor —
    # he is one of the two Technical Assistants — so his name is
    # deliberately excluded from this trigger.
    if re.search(r'\b(supervisor|zonal supervisor|circle supervisor|supervisory circle)\b', q) and not re.search(r'\b(duty|duties|role|guideline|manual|rule)\b', q):
        return INTENT_SUPERVISOR_QUERY
        
    # Manual, Guidelines, Procedures, Definitions
    if re.search(r'\b(manual|guideline|rule|procedure|duty|duties|definition|criteria|form\s*\d+[a-z]?|household|building|census house|how to|faq)\b', q):
        return INTENT_MANUAL_SEARCH
        
    return INTENT_GENERAL

def search_structured_records(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search functionaries and HLB allocations for matching records."""
    conn = get_db_connection()
    cursor = conn.cursor()
    results = []

    # 1. Check for HLB number (accepts the legacy "eb"/"block" wording too)
    eb_match = re.search(r'\b(?:eb|hlb|block)\s*#?\s*0*(\d+)\b', query, re.IGNORECASE)
    if eb_match:
        eb_num = eb_match.group(1)
        # Pad to 4 digits (e.g. '0012') or search exact/like
        padded_eb = eb_num.zfill(4)
        cursor.execute("""
            SELECT h.*, f.mobile_number as enum_mobile, f.district, f.sub_district
            FROM hlb_allocations h
            LEFT JOIN functionaries f ON (h.enumerator_user_id = f.user_id OR h.enumerator_name = f.name)
            WHERE h.hlb_no = ? OR h.hlb_no LIKE ? OR h.supervisory_circle_no = ?
            LIMIT ?
        """, (padded_eb, f"%{eb_num}", eb_num.zfill(3), limit))
        for row in cursor.fetchall():
            results.append({
                "type": "hlb_allocation",
                "hlb_no": row["hlb_no"],
                "circle_no": row["supervisory_circle_no"],
                "supervisor_name": row["supervisor_name"],
                "enumerator_name": row["enumerator_name"],
                "enumerator_user_id": row["enumerator_user_id"],
                "allotment_date": row["allotment_date"],
                "mobile": row["enum_mobile"] or "+91 84534 41975",
                "district": row["district"] or "Goalpara",
                "source": "Census Record DB - 2024 (HLB Allocation)"
            })

    # 2. Check for Name or Mobile or User ID in functionaries
    clean_words = [w for w in re.split(r'[^a-zA-Z0-9]', query) if len(w) >= 3 and w.lower() not in ["who", "what", "is", "assigned", "to", "the", "for", "show", "details", "census", "find", "search"]]
    if clean_words:
        fts_query = " OR ".join([f'"{w}"*' for w in clean_words])
        try:
            cursor.execute("""
                SELECT f.* FROM functionaries f
                JOIN functionaries_fts fts ON f.id = fts.rowid
                WHERE functionaries_fts MATCH ?
                LIMIT ?
            """, (fts_query, limit))
            for row in cursor.fetchall():
                # Avoid duplicates
                if not any(r.get("user_id") == row["user_id"] for r in results):
                    results.append({
                        "type": "functionary",
                        "user_id": row["user_id"],
                        "name": row["name"],
                        "functionary_type": row["functionary_type"],
                        "mobile_number": row["mobile_number"],
                        "district": row["district"],
                        "sub_district": row["sub_district"],
                        "status": row["status"],
                        "source": "Census Record DB - 2024 (All Users)"
                    })
        except Exception as e:
            logger.debug(f"FTS functionaries query error: {e}")

    # Fallback to direct LIKE query if FTS gave no results
    if not results and clean_words:
        for word in clean_words[:2]:
            cursor.execute("""
                SELECT * FROM functionaries 
                WHERE name LIKE ? OR user_id LIKE ? OR mobile_number LIKE ?
                LIMIT ?
            """, (f"%{word}%", f"%{word}%", f"%{word}%", limit))
            for row in cursor.fetchall():
                if not any(r.get("user_id") == row["user_id"] for r in results):
                    results.append({
                        "type": "functionary",
                        "user_id": row["user_id"],
                        "name": row["name"],
                        "functionary_type": row["functionary_type"],
                        "mobile_number": row["mobile_number"],
                        "district": row["district"],
                        "sub_district": row["sub_district"],
                        "status": row["status"],
                        "source": "Census Record DB - 2024 (All Users)"
                    })

    conn.close()
    return results

def search_manual_chunks(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Retrieve relevant excerpts from PDF manuals and FAQ using FTS ranking."""
    conn = get_db_connection()
    cursor = conn.cursor()
    results = []

    clean_words = [w for w in re.split(r'[^a-zA-Z0-9]', query) if len(w) >= 3 and w.lower() not in ["who", "what", "is", "are", "the", "for", "in", "and", "tell", "explain", "about"]]
    if not clean_words:
        clean_words = ["census", "guidelines"]

    def _run_fts(fts_query):
        cursor.execute("""
            SELECT m.*, rank FROM manual_chunks m
            JOIN manual_chunks_fts fts ON m.id = fts.rowid
            WHERE manual_chunks_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (fts_query, limit))
        return cursor.fetchall()

    def _term_clause(w):
        # The Porter stemmer unifies plenty of pairs on its own (duty/duties,
        # define/defined), but not derivational ones like definition/defined
        # — those diverge too early for the stemmer to merge. For longer
        # words, OR in a short 5-char prefix alongside the full-word prefix;
        # empirically this catches most of those cases (definition↔defined,
        # criteria↔criterion, allocation↔allocated, supervisor↔supervisory)
        # without being so short it starts matching unrelated words.
        if len(w) > 8:
            return f'("{w}"* OR "{w[:5]}"*)'
        return f'"{w}"*'

    rows = []
    # Try an AND match first — every keyword must appear (as a stemmed
    # prefix) in the same chunk. This is far more precise than OR: for a
    # query like "household definition criteria", an OR match matches almost
    # every chunk in the document (since "household" appears on nearly every
    # page), and ranking alone doesn't reliably surface the one chunk that
    # actually defines it. Requiring all terms narrows that down sharply.
    # Only fall back to OR (then plain LIKE) if AND finds nothing at all.
    if len(clean_words) > 1:
        and_query = " AND ".join([_term_clause(w) for w in clean_words])
        try:
            rows = _run_fts(and_query)
        except Exception as e:
            logger.debug(f"Manual FTS AND query error: {e}")

    if not rows:
        or_query = " OR ".join([f'"{w}"*' for w in clean_words])
        try:
            rows = _run_fts(or_query)
        except Exception as e:
            logger.debug(f"Manual FTS OR query error: {e}")

    for row in rows:
        results.append({
            "source_file": row["source_file"],
            "doc_title": row["doc_title"],
            "page_number": row["page_number"],
            "section_header": row["section_header"],
            "chunk_text": row["chunk_text"],
            "source": f"{row['doc_title']}, Page {row['page_number']}"
        })

    # Fallback to LIKE
    if not results and clean_words:
        for word in clean_words[:2]:
            cursor.execute("""
                SELECT * FROM manual_chunks
                WHERE chunk_text LIKE ? OR section_header LIKE ?
                LIMIT ?
            """, (f"%{word}%", f"%{word}%", limit))
            for row in cursor.fetchall():
                results.append({
                    "source_file": row["source_file"],
                    "doc_title": row["doc_title"],
                    "page_number": row["page_number"],
                    "section_header": row["section_header"],
                    "chunk_text": row["chunk_text"],
                    "source": f"{row['doc_title']}, Page {row['page_number']}"
                })
                if len(results) >= limit:
                    break

    conn.close()
    return results

def retrieve_rag_context(query: str) -> Dict[str, Any]:
    """Orchestrate dual-source retrieval and build grounded context."""
    intent = detect_intent(query)
    record_results = []
    manual_results = []

    if intent in [INTENT_RECORD_SEARCH, INTENT_SUPERVISOR_QUERY, INTENT_GENERAL]:
        record_results = search_structured_records(query, limit=5)
    
    if intent in [INTENT_MANUAL_SEARCH, INTENT_GENERAL] or not record_results:
        manual_results = search_manual_chunks(query, limit=3)

    # Compile context strings
    context_parts = []
    citations = []

    if record_results:
        context_parts.append("### OFFICIAL CENSUS RECORDS (EXCEL DATA):")
        for idx, rec in enumerate(record_results, 1):
            if rec.get("type") == "hlb_allocation":
                context_parts.append(
                    f"{idx}. HLB Number: {rec['hlb_no']} | Circle: {rec['circle_no']} | "
                    f"Enumerator: {rec['enumerator_name']} (ID: {rec['enumerator_user_id']}) | "
                    f"Supervisor: {rec['supervisor_name']} | Allotment Date: {rec['allotment_date']}"
                )
                citations.append(rec['source'])
            else:
                context_parts.append(
                    f"{idx}. Name: {rec['name']} | User ID: {rec['user_id']} | "
                    f"Role: {rec['functionary_type']} | Mobile: {rec['mobile_number']} | "
                    f"District: {rec['district']} | Sub-District: {rec['sub_district']} | Status: {rec['status']}"
                )
                citations.append(rec['source'])

    if manual_results:
        context_parts.append("\n### OFFICIAL MANUAL & FAQ GUIDELINES (PDF DATA):")
        for idx, doc in enumerate(manual_results, 1):
            header = f" [{doc['section_header']}]" if doc.get('section_header') else ""
            context_parts.append(
                f"{idx}. Source: {doc['doc_title']} (Page {doc['page_number']}){header}:\n"
                f'"{doc["chunk_text"]}"'
            )
            citations.append(doc['source'])

    # Standard technical assistant contact block. Both Technical Assistants
    # are listed here — neither of them is a supervisor; real supervisor
    # names come only from the matched HLB allocation / functionary
    # records above.
    ta_lines = "\n".join(
        f"Technical Assistant: {ta['name']} ({ta['phone']}, WhatsApp: {ta['whatsapp_link']})"
        for ta in TECHNICAL_ASSISTANTS
    )
    contact_block = f"{ta_lines}\nCircle: Lakhipur Circle"

    return {
        "intent": intent,
        "query": query,
        "record_results": record_results,
        "manual_results": manual_results,
        "context_text": "\n".join(context_parts),
        "citations": list(set(citations)),
        "contact_info": contact_block
    }
