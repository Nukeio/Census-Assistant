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

# Stopwords & common question boilerplate
STOPWORDS = {
    "who", "what", "is", "are", "the", "for", "in", "and", "tell", "explain",
    "about", "how", "do", "does", "did", "we", "you", "your", "my", "i",
    "use", "used", "using", "to", "of", "a", "an", "this", "that", "these",
    "those", "with", "from", "by", "on", "at", "as", "it", "its", "if",
    "when", "where", "why", "which", "or", "but", "so", "can", "could",
    "would", "should", "will", "shall", "get", "got", "need", "want",
    "please", "hello", "hi", "thanks", "thank", "ok", "okay", "yes", "no",
    "not", "assigned", "show", "details", "find", "search", "give", "me",
    "meaning", "according", "manual", "manuals", "guideline", "guidelines",
    "instruction", "instructions", "document", "documents", "census"
}

def _clean_keywords(query: str) -> List[str]:
    words = [w for w in re.split(r'[^a-zA-Z0-9]', query) if len(w) >= 3 and w.lower() not in STOPWORDS]
    if not words:
        # If all words were in STOPWORDS (e.g. "Census manual instructions"), retain words >= 3 chars
        words = [w for w in re.split(r'[^a-zA-Z0-9]', query) if len(w) >= 3]
    return words

def _stem(w: str) -> str:
    """Small suffix stemmer for census terms."""
    wl = w.lower()
    if wl.endswith("ies") and len(wl) > 4:
        return wl[:-3] + "y"
    for suf in ("ation", "tion", "ment", "ing", "ers", "er"):
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
    """Lookup village/ward name and landmark from hlb_descriptions."""
    hlb_norm = _hlb_no_norm(hlb_no)
    if not hlb_norm:
        return None, None
    row = cursor.execute(
        "SELECT village_ward_name, landmark, boundary_description FROM hlb_descriptions WHERE hlb_no = ?",
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
    """Lookup area for functionary user ID."""
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

    # Manual, Guidelines, Procedures, Definitions
    manual_triggers = [
        "manual", "guideline", "guidelines", "rule", "rules", "procedure",
        "duty", "duties", "role", "definition", "define", "criteria",
        "household", "building", "census house", "how to", "faq", "numbering",
        "form 4b", "form 4", "form", "eligibility", "eligible", "draw",
        "layout", "map", "pencil", "pen", "notional map", "hlo", "app",
        "mobile app", "sync", "charge", "supervisor duty", "supervisor duties",
        "enumerator duty", "enumerator duties", "what is", "how do", "steps"
    ]
    if any(trig in q for trig in manual_triggers):
        # If it specifically queries a concrete person/EB, prioritize record
        if not re.search(r'\b(eb\s*\d+|hlb\s*\d+|block\s*\d+|who is assigned to)\b', q):
            return INTENT_MANUAL_SEARCH

    # HLB or Enumerator / Record lookup
    if re.search(
        r'\b(eb\s*\d+|hlb\s*\d+|block\s*\d+|assigned to|enumerator|charge user|'
        r'who is in charge|show details for|details for|profile of|'
        r'find enumerator|who works in|circle\s*\d+|supervisory circle\s*\d+|'
        r'area|village|ward|locality)\b', q
    ):
        return INTENT_RECORD_SEARCH

    # Supervisor specific query
    if re.search(r'\b(supervisor|zonal supervisor|circle supervisor)\b', q) and not any(w in q for w in ["duty", "duties", "role", "manual", "rule", "guideline"]):
        return INTENT_SUPERVISOR_QUERY

    return INTENT_GENERAL

def search_by_area(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search hlb_descriptions for village/ward/area name matches."""
    clean_words = _clean_keywords(query)
    if not clean_words:
        return []

    conn = get_db_connection()
    cursor = conn.cursor()
    results = []

    for word in clean_words[:3]:
        rows = cursor.execute("""
            SELECT hlb_no, village_ward_name, landmark, boundary_description
            FROM hlb_descriptions
            WHERE village_ward_name LIKE ? OR landmark LIKE ? OR boundary_description LIKE ?
            LIMIT ?
        """, (f"%{word}%", f"%{word}%", f"%{word}%", limit)).fetchall()

        for desc_row in rows:
            hlb_norm = desc_row["hlb_no"]
            area_name = desc_row["landmark"] or re.sub(r'\s*\(\d+\)\s*$', '', desc_row["village_ward_name"] or "").strip()

            alloc_row = cursor.execute("""
                SELECT h.*, f.mobile_number as enum_mobile, f.district, f.sub_district
                FROM hlb_allocations h
                LEFT JOIN functionaries f ON h.enumerator_user_id = f.user_id
                WHERE h.hlb_no = ? OR h.hlb_no = ?
                LIMIT 1
            """, (hlb_norm, hlb_norm.zfill(4))).fetchone()

            if alloc_row and not any(r.get("hlb_no") == alloc_row["hlb_no"] for r in results):
                maps_url = "https://www.google.com/maps/search/?api=1&query=" + url_quote(f"{area_name}, {CIRCLE_NAME}, Assam, India") if area_name else None
                results.append({
                    "type": "hlb_allocation",
                    "hlb_no": alloc_row["hlb_no"],
                    "circle_no": alloc_row["supervisory_circle_no"],
                    "supervisor_name": alloc_row["supervisor_name"],
                    "enumerator_name": alloc_row["enumerator_name"],
                    "enumerator_user_id": alloc_row["enumerator_user_id"],
                    "allotment_date": alloc_row["allotment_date"],
                    "mobile": alloc_row.get("enum_mobile") or "+91 84534 41975",
                    "district": alloc_row.get("district") or "Goalpara",
                    "area_name": area_name,
                    "landmark": desc_row["landmark"],
                    "boundary_description": desc_row["boundary_description"],
                    "maps_url": maps_url,
                    "confidence": "high",
                    "source": "Census Record DB - 2024 (HLB Description)"
                })

            if len(results) >= limit:
                break
        if len(results) >= limit:
            break

    conn.close()
    return results

def search_structured_records(query: str, limit: int = 5, strict: bool = False) -> List[Dict[str, Any]]:
    """Search functionaries and HLB allocations for matching records."""
    conn = get_db_connection()
    cursor = conn.cursor()
    results = []

    # 1. Check for HLB number
    eb_match = re.search(r'\b(?:eb|hlb|block)\s*#?\s*0*(\d+)\b', query, re.IGNORECASE)
    if eb_match:
        eb_num = eb_match.group(1)
        padded_eb = eb_num.zfill(4)
        cursor.execute("""
            SELECT h.*, f.mobile_number as enum_mobile, f.district, f.sub_district, d.village_ward_name, d.landmark, d.boundary_description
            FROM hlb_allocations h
            LEFT JOIN functionaries f ON (h.enumerator_user_id = f.user_id OR h.enumerator_name = f.name)
            LEFT JOIN hlb_descriptions d ON (d.hlb_no = h.hlb_no OR d.hlb_no = cast(h.hlb_no as integer))
            WHERE h.hlb_no = ? OR h.hlb_no LIKE ? OR h.supervisory_circle_no = ?
            LIMIT ?
        """, (padded_eb, f"%{eb_num}", eb_num.zfill(3), limit))
        for row in cursor.fetchall():
            area_name = row["landmark"] or (re.sub(r'\s*\(\d+\)\s*$', '', row["village_ward_name"] or '').strip()) if row["village_ward_name"] else None
            maps_url = ("https://www.google.com/maps/search/?api=1&query=" + url_quote(f"{area_name}, {CIRCLE_NAME}, Assam, India")) if area_name else None
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
                "landmark": row["landmark"],
                "boundary_description": row["boundary_description"],
                "maps_url": maps_url,
                "confidence": "high",
                "source": "Census Record DB - 2024 (HLB Allocation)"
            })

    # 2. Check for supervisory circle number
    circle_match = re.search(r'\b(?:circle|supervisory circle|circle no\.?)\s*#?\s*(\d+)\b', query, re.IGNORECASE)
    if circle_match and not eb_match:
        circle_num = circle_match.group(1)
        cursor.execute("""
            SELECT h.*, f.mobile_number as enum_mobile, f.district, f.sub_district, d.village_ward_name, d.landmark, d.boundary_description
            FROM hlb_allocations h
            LEFT JOIN functionaries f ON h.enumerator_user_id = f.user_id
            LEFT JOIN hlb_descriptions d ON (d.hlb_no = h.hlb_no OR d.hlb_no = cast(h.hlb_no as integer))
            WHERE h.supervisory_circle_no = ? OR h.supervisory_circle_no = ?
            LIMIT ?
        """, (circle_num, circle_num.zfill(2), limit))
        for row in cursor.fetchall():
            if any(r.get("hlb_no") == row["hlb_no"] for r in results):
                continue
            area_name = row["landmark"] or (re.sub(r'\s*\(\d+\)\s*$', '', row["village_ward_name"] or '').strip()) if row["village_ward_name"] else None
            maps_url = ("https://www.google.com/maps/search/?api=1&query=" + url_quote(f"{area_name}, {CIRCLE_NAME}, Assam, India")) if area_name else None
            results.append({
                "type": "hlb_allocation",
                "hlb_no": row["hlb_no"],
                "circle_no": row["supervisory_circle_no"],
                "supervisor_name": row["supervisor_name"],
                "enumerator_name": row["enumerator_name"],
                "enumerator_user_id": row["enumerator_user_id"],
                "allotment_date": row["allotment_date"],
                "mobile": row.get("enum_mobile") or "+91 84534 41975",
                "district": row.get("district") or "Goalpara",
                "area_name": area_name,
                "landmark": row["landmark"],
                "boundary_description": row["boundary_description"],
                "maps_url": maps_url,
                "confidence": "high",
                "source": "Census Record DB - 2024 (HLB Allocation)"
            })

    # 3. Person Name lookup
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
            "village_town": row["village_town"],
            "status": row["status"],
            "area_name": area_name,
            "maps_url": maps_url,
            "confidence": confidence,
            "source": "Census Record DB - 2024 (All Users)"
        })

    if clean_words and not eb_match:
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

    conn.close()
    return results

def search_manual_chunks(query: str, limit: int = 4) -> List[Dict[str, Any]]:
    """
    Retrieve relevant excerpts from PDF manuals and FAQ using FTS5 rank ordering.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    clean_words = _clean_keywords(query)
    if not clean_words:
        # Fallback to general term extraction
        clean_words = [w for w in re.split(r'[^a-zA-Z0-9]', query) if len(w) >= 3]

    if not clean_words:
        conn.close()
        return []

    candidates = {}

    # 1. Try phrase matching or FTS AND matching
    and_query = " AND ".join([f'"{w}"*' for w in clean_words])
    try:
        cursor.execute("""
            SELECT m.* FROM manual_chunks m
            JOIN manual_chunks_fts fts ON m.id = fts.rowid
            WHERE manual_chunks_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (and_query, limit * 2))
        for row in cursor.fetchall():
            candidates[row["id"]] = row
    except Exception as e:
        logger.debug(f"Manual FTS AND query error: {e}")

    # 2. Try FTS OR query for ranking
    or_query = " OR ".join([f'"{w}"*' for w in clean_words])
    try:
        cursor.execute("""
            SELECT m.* FROM manual_chunks m
            JOIN manual_chunks_fts fts ON m.id = fts.rowid
            WHERE manual_chunks_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (or_query, limit * 4))
        for row in cursor.fetchall():
            candidates.setdefault(row["id"], row)
    except Exception as e:
        logger.debug(f"Manual FTS OR query error: {e}")

    # 3. Fallback LIKE search if FTS yielded no results
    if not candidates:
        for word in clean_words[:3]:
            cursor.execute("""
                SELECT * FROM manual_chunks
                WHERE chunk_text LIKE ? OR section_header LIKE ?
                LIMIT ?
            """, (f"%{word}%", f"%{word}%", limit * 2))
            for row in cursor.fetchall():
                candidates.setdefault(row["id"], row)

    def _score_chunk(row):
        text_lower = ((row["chunk_text"] or "") + " " + (row["section_header"] or "")).lower()
        score = 0
        matched_words = 0
        for w in clean_words:
            wl = w.lower()
            if re.search(r'\b' + re.escape(wl) + r'\b', text_lower):
                score += 3
                matched_words += 1
            else:
                stem = _stem(w)
                if stem and len(stem) >= 3 and re.search(r'\b' + re.escape(stem) + r'\w*\b', text_lower):
                    score += 2
                    matched_words += 1
        # Bonus for section header matches
        if row["section_header"]:
            header_lower = row["section_header"].lower()
            if any(re.search(r'\b' + re.escape(w.lower()) + r'\b', header_lower) for w in clean_words):
                score += 4

        # Discard if zero valid words matched
        if matched_words == 0:
            return 0
        # If query has multiple clean keywords, require at least 35% overlap
        if len(clean_words) >= 3 and (matched_words / len(clean_words)) < 0.35:
            return 0

        return score

    scored = [( _score_chunk(row), row ) for row in candidates.values()]
    # Keep chunks that have a positive score
    scored = [t for t in scored if t[0] >= 2]
    scored.sort(key=lambda t: -t[0])

    results = []
    for score, row in scored[:limit]:
        results.append({
            "source_file": row["source_file"],
            "doc_title": row["doc_title"],
            "page_number": row["page_number"],
            "section_header": row["section_header"],
            "chunk_text": row["chunk_text"],
            # Exposed so callers can distinguish "this passage genuinely answers
            # the question" from "this passage happens to contain the word
            # 'house'". retrieve_rag_context uses it to decide whether the
            # manual is worth putting in front of the model at all.
            "relevance": score,
            "source": f"{row['doc_title']}, Page {row['page_number']}"
        })

    conn.close()
    return results

def retrieve_rag_context(query: str) -> Dict[str, Any]:
    """Orchestrate dual-source retrieval and build grounded context."""
    intent = detect_intent(query)
    record_results = []
    manual_results = []

    # Always search structured records if relevant
    if intent in [INTENT_RECORD_SEARCH, INTENT_SUPERVISOR_QUERY, INTENT_GENERAL]:
        record_results = search_structured_records(query, limit=5, strict=(intent == INTENT_GENERAL))
        if intent == INTENT_RECORD_SEARCH and not record_results:
            record_results = search_by_area(query, limit=5)

    # Manual retrieval.
    #
    # We still LOOK for manual passages on most questions — cheap, and it is
    # how a genuine procedural question finds its answer. What changed is the
    # bar for actually putting them in front of the model.
    #
    # The old behaviour matched a bare keyword list ("how", "what", "house",
    # "form", "app"...), which fires on almost any sentence, and every hit was
    # then injected with a "prioritize these documents" instruction. The result
    # was that general questions got steered into the manuals and answered as
    # though the assistant could only speak from them.
    #
    # Now a passage has to actually be about the question. MANUAL_SEARCH intent
    # keeps the old low bar because the user explicitly asked about the
    # manuals; everything else needs a strong match (roughly two solid keyword
    # hits, or a section-heading match) before it is treated as context.
    manual_keywords = ["how", "what", "rule", "procedure", "definition", "define", "meaning", "duty", "duties", "building", "house", "household", "form", "app", "map", "pencil", "pen", "eligible", "sync"]
    is_instructional = any(k in query.lower() for k in manual_keywords)

    if intent == INTENT_MANUAL_SEARCH or not record_results or is_instructional:
        manual_results = search_manual_chunks(query, limit=4)

    MANUAL_STRONG_RELEVANCE = 6
    manual_is_relevant = bool(manual_results) and (
        intent == INTENT_MANUAL_SEARCH
        or max((m.get("relevance", 0) for m in manual_results), default=0) >= MANUAL_STRONG_RELEVANCE
    )
    weak_manual_results: List[Dict[str, Any]] = []
    if not manual_is_relevant:
        # Keep them for the "related reading" affordance, but do not let them
        # shape the answer or claim a citation.
        weak_manual_results, manual_results = manual_results, []

    # Compile context strings
    context_parts = []
    citations = []

    if record_results:
        context_parts.append("### OFFICIAL CENSUS RECORDS (EXCEL DATA):")
        for idx, rec in enumerate(record_results, 1):
            if rec.get("type") == "hlb_allocation":
                area_bit = f" | Area/Village: {rec['area_name']}" if rec.get("area_name") else ""
                landmark_bit = f" | Landmark: {rec['landmark']}" if rec.get("landmark") else ""
                context_parts.append(
                    f"{idx}. HLB Number: {rec['hlb_no']} | Circle: {rec['circle_no']} | "
                    f"Enumerator: {rec['enumerator_name']} (ID: {rec['enumerator_user_id']}) | "
                    f"Supervisor: {rec['supervisor_name']} | Allotment Date: {rec['allotment_date']}{area_bit}{landmark_bit}"
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
        # Manual passages that were found but judged too weak to steer the
        # answer. Offered to the caller as optional further reading only.
        "related_manual_results": weak_manual_results,
        "context_text": "\n".join(context_parts),
        # Only sources that actually went into the prompt. answer_query cites
        # these and nothing else, so an answer drawn from the model's own
        # knowledge is never labelled as coming from the HLO Manual.
        "citations": list(set(citations)),
        "has_local_context": bool(record_results or manual_results),
        "contact_info": contact_block
    }
