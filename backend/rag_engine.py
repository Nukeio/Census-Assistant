"""
Census Assistant - RAG Engine
Handles Intent Detection, Structured Entity Search, PDF Manual Semantic Retrieval, Citation Generation, and Prompt Formulation.
"""

import re
import json
import logging
from urllib.parse import quote as url_quote
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

CIRCLE_NAME = "Lakhipur Circle"

# Common English filler/question words that carry no search signal on their
# own. These were previously NOT filtered out of the free-text keyword list,
# which is exactly why queries like "How to login hlo app" or "Do we use pen
# or pencil to draw the map" were matching random, unrelated manual chunks —
# words like "how", "do", "use" are common enough to appear in almost every
# FAQ page, so an OR-style match against them returns near-arbitrary results.
STOPWORDS = {
    "who", "what", "is", "are", "the", "for", "in", "and", "tell", "explain",
    "about", "how", "do", "does", "did", "we", "you", "your", "my", "i",
    "use", "used", "using", "to", "of", "a", "an", "this", "that", "these",
    "those", "with", "from", "by", "on", "at", "as", "it", "its", "if",
    "when", "where", "why", "which", "or", "but", "so", "can", "could",
    "would", "should", "will", "shall", "get", "got", "need", "want",
    "please", "hello", "hi", "thanks", "thank", "ok", "okay", "yes", "no",
    "not", "assigned", "show", "details", "census", "find", "search",
}
# NOTE: "app" and "login" are deliberately NOT in this stopword list — they
# carry real content meaning (e.g. "How to login hlo app"), so a question
# using them should still require a real match on them rather than being
# filtered down to a single vaguer leftover word that then matches an
# unrelated chunk by coincidence.

def _clean_keywords(query: str) -> List[str]:
    return [w for w in re.split(r'[^a-zA-Z0-9]', query) if len(w) >= 3 and w.lower() not in STOPWORDS]

def _stem(w: str) -> str:
    """Very small hand-rolled stemmer covering the common English suffix
    patterns seen in census manual language (duty/duties, definition/defined,
    allocation/allocated, etc.) — just enough to let a simple substring
    presence check treat those as the same word without a real NLP stemmer."""
    wl = w.lower()
    if wl.endswith("ies") and len(wl) > 4:
        return wl[:-3] + "y"
    for suf in ("ation", "tion", "ment", "ing"):
        if wl.endswith(suf) and len(wl) > len(suf) + 2:
            return wl[:-len(suf)]
    if wl.endswith("es") and len(wl) > 4:
        return wl[:-2]
    for suf in ("ed", "s"):
        if wl.endswith(suf) and len(wl) > 3:
            return wl[:-len(suf)]
    return wl

def _hlb_no_norm(hlb_no):
    if hlb_no is None:
        return None
    digits = re.sub(r'\D', '', str(hlb_no))
    return str(int(digits)) if digits else None

def _lookup_area_for_hlb(cursor, hlb_no):
    """Real village/ward name + Google Maps link for an HLB number, from
    hlb_descriptions (ingested from HLB Description.xlsx). Returns
    (area_name, maps_url) — both None if not found."""
    hlb_norm = _hlb_no_norm(hlb_no)
    if not hlb_norm:
        return None, None
    row = cursor.execute(
        "SELECT village_ward_name, landmark FROM hlb_descriptions WHERE hlb_no = ?",
        (hlb_norm,)
    ).fetchone()
    if not row:
        return None, None
    area_name = row["landmark"] or re.sub(r'\s*\(\d+\)\s*$', '', row["village_ward_name"] or "").strip() or None
    if not area_name:
        return None, None
    maps_url = "https://www.google.com/maps/search/?api=1&query=" + url_quote(f"{area_name}, {CIRCLE_NAME}, Assam, India")
    return area_name, maps_url

def _lookup_area_for_user(cursor, user_id):
    """Same as _lookup_area_for_hlb, but starting from a functionary's user_id
    — looks up their HLB allocation first, then the area for that HLB."""
    if not user_id:
        return None, None
    row = cursor.execute(
        "SELECT hlb_no FROM hlb_allocations WHERE enumerator_user_id = ? LIMIT 1",
        (user_id,)
    ).fetchone()
    if not row:
        return None, None
    return _lookup_area_for_hlb(cursor, row["hlb_no"])

def detect_intent(query: str) -> str:
    """Classify user query intent."""
    q = query.lower()
    
    # HLB (formerly "EB") or Enumerator / Record lookup. The "eb" alias is
    # still recognized so old queries/links keep working, but every
    # response now speaks in HLB terms only. Also explicitly recognizes the
    # literal phrasing the search result card's ">" (chevron) button sends —
    # "Show details for <name>" — so opening a profile always resolves to a
    # person record instead of falling through to a generic manual answer.
    if re.search(r'\b(eb\s*\d+|hlb\s*\d+|block\s*\d+|assigned to|enumerator|charge user|who is in charge|show details for|details for|profile of)\b', q):
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

def search_structured_records(query: str, limit: int = 5, strict: bool = False) -> List[Dict[str, Any]]:
    """
    Search functionaries and HLB allocations for matching records.

    `strict=True` is used for queries that only weakly imply a record lookup
    (GENERAL intent — no HLB/enumerator/supervisor keyword at all). In that
    mode, the free-text name search below requires ALL of the query's
    keywords to match (AND, not OR) and skips the LIKE fallback — a loose
    single-word OR/LIKE match was the cause of unrelated general questions
    (e.g. "do we use pen or pencil to draw the map") spuriously matching a
    person via a stray prefix hit (e.g. on a village name) and being shown
    as a "Functionary Record Found" instead of being treated as a general
    question. The precise HLB-number lookup below is unaffected by `strict`
    since a literal HLB/EB/block number is never a false signal.
    """
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
            area_name, maps_url = _lookup_area_for_hlb(cursor, row["hlb_no"])
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
                "area_name": area_name,
                "maps_url": maps_url,
                "confidence": "high",
                "source": "Census Record DB - 2024 (HLB Allocation)"
            })

    # 2. Check for Name or Mobile or User ID in functionaries.
    #
    # Precision strategy (this replaced a much weaker OR-only match that was
    # returning the WRONG person for multi-word name queries — e.g. "Show
    # details for Abu Daium Ahmed" was returning a completely different
    # "Abu Sayed Ali Sheikh" record, because the old query OR'd every word
    # together ("Abu"* OR "Daium"* OR "Ahmed"*) with no result ranking, so it
    # just returned whichever "Abu ..." row SQLite happened to return first):
    #   1. Try an AND match (every keyword must be present on the SAME row) —
    #      high confidence, since a multi-word match is very unlikely to be
    #      the wrong person.
    #   2. Only if that finds nothing, fall back to OR (then LIKE) — but mark
    #      these as low confidence, since a single-keyword match is inherently
    #      ambiguous (there can be many "Abu ..." or many "Ahmed ..." people).
    #      `strict` mode (weak GENERAL-intent queries) skips this fallback
    #      entirely rather than accept a low-confidence guess.
    clean_words = _clean_keywords(query)

    def _add_functionary_row(row, confidence):
        if any(r.get("user_id") == row["user_id"] for r in results):
            return
        area_name, maps_url = _lookup_area_for_user(cursor, row["user_id"])
        results.append({
            "type": "functionary",
            "user_id": row["user_id"],
            "name": row["name"],
            "functionary_type": row["functionary_type"],
            "mobile_number": row["mobile_number"],
            "district": row["district"],
            "sub_district": row["sub_district"],
            "status": row["status"],
            "area_name": area_name,
            "maps_url": maps_url,
            "confidence": confidence,
            "source": "Census Record DB - 2024 (All Users)"
        })

    if clean_words:
        and_rows = []
        if len(clean_words) >= 2:
            fts_query = " AND ".join([f'"{w}"*' for w in clean_words])
            try:
                cursor.execute("""
                    SELECT f.* FROM functionaries f
                    JOIN functionaries_fts fts ON f.id = fts.rowid
                    WHERE functionaries_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (fts_query, limit))
                and_rows = cursor.fetchall()
            except Exception as e:
                logger.debug(f"FTS functionaries AND query error: {e}")

        for row in and_rows:
            _add_functionary_row(row, "high")

        if not results and not strict:
            fts_query = " OR ".join([f'"{w}"*' for w in clean_words])
            try:
                cursor.execute("""
                    SELECT f.* FROM functionaries f
                    JOIN functionaries_fts fts ON f.id = fts.rowid
                    WHERE functionaries_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (fts_query, limit))
                for row in cursor.fetchall():
                    _add_functionary_row(row, "low")
            except Exception as e:
                logger.debug(f"FTS functionaries OR query error: {e}")

            if not results:
                for word in clean_words[:2]:
                    cursor.execute("""
                        SELECT * FROM functionaries
                        WHERE name LIKE ? OR user_id LIKE ? OR mobile_number LIKE ?
                        LIMIT ?
                    """, (f"%{word}%", f"%{word}%", f"%{word}%", limit))
                    for row in cursor.fetchall():
                        _add_functionary_row(row, "low")
        # strict mode: no OR / LIKE fallback — a weak, single-signal match is
        # exactly what produced false positives on unrelated general questions.

    conn.close()
    return results

def search_manual_chunks(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Retrieve relevant excerpts from PDF manuals and FAQ.

    Rather than trusting FTS5's boolean MATCH/rank alone (an OR-style match
    was returning essentially arbitrary, unrelated chunks whenever the query
    contained any common word — "How to login hlo app" and "Do we use pen or
    pencil to draw the map" both matched totally unrelated FAQ entries this
    way), this pulls a candidate pool from FTS and then scores each candidate
    in Python by how many of the query's actual keywords it contains. Only
    candidates clearing a "most keywords present" bar are returned; if none
    clear it, this returns empty so the caller gives an honest "I don't have
    that information" instead of a confidently wrong answer.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    clean_words = _clean_keywords(query)
    if not clean_words:
        conn.close()
        return []

    def _term_clause(w):
        if len(w) > 8:
            return f'("{w}"* OR "{w[:5]}"*)'
        return f'"{w}"*'

    candidates = {}

    if len(clean_words) > 1:
        and_query = " AND ".join(_term_clause(w) for w in clean_words)
        try:
            cursor.execute("""
                SELECT m.* FROM manual_chunks m
                JOIN manual_chunks_fts fts ON m.id = fts.rowid
                WHERE manual_chunks_fts MATCH ?
                LIMIT ?
            """, (and_query, limit * 4))
            for row in cursor.fetchall():
                candidates[row["id"]] = row
        except Exception as e:
            logger.debug(f"Manual FTS AND query error: {e}")

    # Also pull a broader OR-based recall pool for scoring — a real match can
    # still score well even if the strict AND clause above missed it (e.g.
    # tokenization quirks), but every candidate here still has to clear the
    # keyword-overlap bar below before it's actually returned.
    or_query = " OR ".join(f'"{w}"*' for w in clean_words)
    try:
        cursor.execute("""
            SELECT m.* FROM manual_chunks m
            JOIN manual_chunks_fts fts ON m.id = fts.rowid
            WHERE manual_chunks_fts MATCH ?
            LIMIT ?
        """, (or_query, max(limit * 8, 30)))
        for row in cursor.fetchall():
            candidates.setdefault(row["id"], row)
    except Exception as e:
        logger.debug(f"Manual FTS OR query error: {e}")

    if not candidates:
        for word in clean_words[:3]:
            cursor.execute("""
                SELECT * FROM manual_chunks
                WHERE chunk_text LIKE ? OR section_header LIKE ?
                LIMIT 20
            """, (f"%{word}%", f"%{word}%"))
            for row in cursor.fetchall():
                candidates.setdefault(row["id"], row)

    def _word_present(w, text_lower):
        wl = w.lower()
        if wl in text_lower:
            return True
        stem = _stem(w)
        if stem and stem in text_lower:
            return True
        if len(w) > 8 and w[:5].lower() in text_lower:
            return True
        return False

    scored = []
    for row in candidates.values():
        text_lower = ((row["chunk_text"] or "") + " " + (row["section_header"] or "")).lower()
        score = sum(1 for w in clean_words if _word_present(w, text_lower))
        if score > 0:
            scored.append((score, row))

    # Require MOST of the query's keywords to actually be present in the
    # chunk — this is what keeps an unrelated question (where every real
    # chunk scores 0 or 1 out of 4-5 keywords) from returning anything at all.
    if len(clean_words) == 1:
        required = 1
    elif len(clean_words) == 2:
        required = 2
    else:
        required = max(2, round(len(clean_words) * 0.6))

    scored = [t for t in scored if t[0] >= required]
    scored.sort(key=lambda t: -t[0])

    results = []
    for score, row in scored[:limit]:
        results.append({
            "source_file": row["source_file"],
            "doc_title": row["doc_title"],
            "page_number": row["page_number"],
            "section_header": row["section_header"],
            "chunk_text": row["chunk_text"],
            "source": f"{row['doc_title']}, Page {row['page_number']}"
        })

    conn.close()
    return results

def retrieve_rag_context(query: str) -> Dict[str, Any]:
    """Orchestrate dual-source retrieval and build grounded context."""
    intent = detect_intent(query)
    record_results = []
    manual_results = []

    if intent in [INTENT_RECORD_SEARCH, INTENT_SUPERVISOR_QUERY, INTENT_GENERAL]:
        # GENERAL means the query had no HLB/enumerator/supervisor keyword at
        # all — it's a weak signal for a record lookup (e.g. someone just
        # typed a plain name with no other context), so search strictly to
        # avoid a random word in the question spuriously matching a person.
        record_results = search_structured_records(query, limit=5, strict=(intent == INTENT_GENERAL))
    
    if intent in [INTENT_MANUAL_SEARCH, INTENT_GENERAL] or not record_results:
        manual_results = search_manual_chunks(query, limit=3)

    # Compile context strings
    context_parts = []
    citations = []

    if record_results:
        context_parts.append("### OFFICIAL CENSUS RECORDS (EXCEL DATA):")
        for idx, rec in enumerate(record_results, 1):
            if rec.get("type") == "hlb_allocation":
                area_bit = f" | Area/Village: {rec['area_name']}" if rec.get("area_name") else ""
                context_parts.append(
                    f"{idx}. HLB Number: {rec['hlb_no']} | Circle: {rec['circle_no']} | "
                    f"Enumerator: {rec['enumerator_name']} (ID: {rec['enumerator_user_id']}) | "
                    f"Supervisor: {rec['supervisor_name']} | Allotment Date: {rec['allotment_date']}{area_bit}"
                )
                citations.append(rec['source'])
            else:
                area_bit = f" | Area/Village: {rec['area_name']}" if rec.get("area_name") else ""
                confidence_bit = " [Note: closest match, not an exact name match]" if rec.get("confidence") == "low" else ""
                context_parts.append(
                    f"{idx}. Name: {rec['name']} | User ID: {rec['user_id']} | "
                    f"Role: {rec['functionary_type']} | Mobile: {rec['mobile_number']} | "
                    f"District: {rec['district']} | Sub-District: {rec['sub_district']} | Status: {rec['status']}{area_bit}{confidence_bit}"
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
