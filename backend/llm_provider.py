"""
Census Assistant - Multi-Model AI Provider Adapter
Supports Gemini 2.5 Flash with Web Search Grounding, Server-Side Daily Search Limit (10/day),
Unrestricted Conversational Knowledge for Census 2027, and Local RAG Fallback.
"""

import os
import re
import json
import logging
import requests
import time
from urllib.parse import quote as url_quote
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from .database import get_db_connection

logger = logging.getLogger("LLMProvider")
logging.basicConfig(level=logging.INFO)

DAILY_WEB_SEARCH_LIMIT = 10

# Models tried in order. If the configured model is rejected as unknown (a 404
# from the API, which is what happens when a model is renamed or retired), the
# next one is attempted rather than silently dropping to the offline
# synthesizer and looking like the assistant is restricted to the PDFs.
GEMINI_MODEL_FALLBACKS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
]

# Overridable so the AI paths can be exercised against a stub in the test
# suite, and so a deployment behind a corporate gateway can point at a mirror
# without editing code. Defaults to Google's public endpoint.
GEMINI_ENDPOINT = os.environ.get(
    "GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta/models"
).rstrip("/")

# Free PythonAnywhere accounts reach the internet only through an HTTP proxy,
# and only for allowlisted hosts. requests picks up http_proxy/https_proxy from
# the environment on its own, but PythonAnywhere does not always export them
# into a WSGI worker, so an explicit override is available. Set
# OUTBOUND_HTTP_PROXY=http://proxy.server:3128 on such a host.
_EXPLICIT_PROXY = os.environ.get("OUTBOUND_HTTP_PROXY", "").strip()
REQUEST_PROXIES: Optional[Dict[str, str]] = (
    {"http": _EXPLICIT_PROXY, "https": _EXPLICIT_PROXY} if _EXPLICIT_PROXY else None
)

# Last provider failure, surfaced through get_ai_status() so a missing key or a
# blocked host is visible in the admin console instead of being swallowed and
# reported to the user as a canned answer.
_LAST_PROVIDER_ERROR: Dict[str, Any] = {"message": "", "at": None, "kind": ""}


def _record_provider_error(kind: str, message: str) -> None:
    _LAST_PROVIDER_ERROR["kind"] = kind
    _LAST_PROVIDER_ERROR["message"] = str(message)[:400]
    _LAST_PROVIDER_ERROR["at"] = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S")
    logger.warning(f"AI provider [{kind}]: {message}")


def get_api_key() -> str:
    return (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()


def get_ai_status(probe: bool = False) -> Dict[str, Any]:
    """
    Report whether the assistant can actually reach a language model.

    Without this, a missing GEMINI_API_KEY is invisible: every question quietly
    falls through to the offline synthesizer, which can only answer from the
    ingested records and manuals — exactly the behaviour that reads as "the AI
    is restricted to the PDFs". Surfaced at /api/admin/ai-status.
    """
    api_key = get_api_key()
    status: Dict[str, Any] = {
        "provider": "google-gemini",
        "configured": bool(api_key),
        "model": GEMINI_MODEL_FALLBACKS[0],
        "proxy": _EXPLICIT_PROXY or "(from environment)",
        "daily_web_search_limit": DAILY_WEB_SEARCH_LIMIT,
        "last_error": _LAST_PROVIDER_ERROR["message"] or None,
        "last_error_kind": _LAST_PROVIDER_ERROR["kind"] or None,
        "last_error_at": _LAST_PROVIDER_ERROR["at"],
    }

    if not api_key:
        status["mode"] = "offline_fallback"
        status["summary"] = (
            "No GEMINI_API_KEY is set, so the assistant can only answer from ingested "
            "records and manuals. Set GEMINI_API_KEY in the PythonAnywhere environment "
            "and reload the web app to enable full AI answers."
        )
        return status

    if not probe:
        status["mode"] = "llm"
        status["summary"] = "AI provider configured."
        return status

    try:
        resp = requests.get(
            f"{GEMINI_ENDPOINT}?key={api_key}", timeout=10, proxies=REQUEST_PROXIES
        )
        status["reachable"] = resp.status_code == 200
        status["http_status"] = resp.status_code
        if resp.status_code == 200:
            names = [m.get("name", "") for m in resp.json().get("models", [])]
            status["models_available"] = len(names)
            status["mode"] = "llm"
            status["summary"] = "AI provider configured and reachable."
        else:
            status["mode"] = "offline_fallback"
            status["summary"] = (
                f"The API key is set but Google returned HTTP {resp.status_code}. "
                "Check the key is valid and that generativelanguage.googleapis.com is "
                "reachable from this host."
            )
    except Exception as exc:
        status["reachable"] = False
        status["mode"] = "offline_fallback"
        status["summary"] = (
            f"Could not reach the Gemini API from this server ({exc.__class__.__name__}). "
            "On a free PythonAnywhere account, outbound traffic is allowlist-only — set "
            "OUTBOUND_HTTP_PROXY=http://proxy.server:3128 or upgrade the account."
        )
        _record_provider_error("unreachable", str(exc))

    return status


def get_today_ist() -> str:
    """Return today's date string in IST (Asia/Kolkata, UTC+5:30)."""
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime("%Y-%m-%d")

# ---------------------------------------------------------------------------
# Daily Web Search Quota Manager (Server-Side)
# ---------------------------------------------------------------------------

def get_user_search_usage(user_identifier: str) -> Tuple[int, int]:
    """
    Get (used_count, remaining_count) of web searches for user today.
    """
    if not user_identifier:
        user_identifier = "guest"
    today = get_today_ist()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT search_count FROM user_search_quota
        WHERE user_identifier = ? AND search_date = ?
    """, (user_identifier, today))
    row = cursor.fetchone()
    conn.close()

    used = row["search_count"] if row else 0
    remaining = max(0, DAILY_WEB_SEARCH_LIMIT - used)
    return used, remaining

def consume_web_search_quota(user_identifier: str) -> bool:
    """
    Increment the daily search count by 1 if within limit.
    Returns True if quota was consumed, False if limit was already reached.
    """
    if not user_identifier:
        user_identifier = "guest"
    today = get_today_ist()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT search_count FROM user_search_quota
        WHERE user_identifier = ? AND search_date = ?
    """, (user_identifier, today))
    row = cursor.fetchone()

    current_count = row["search_count"] if row else 0
    if current_count >= DAILY_WEB_SEARCH_LIMIT:
        conn.close()
        return False

    cursor.execute("""
        INSERT INTO user_search_quota (user_identifier, search_date, search_count, updated_at)
        VALUES (?, ?, 1, CURRENT_TIMESTAMP)
        ON CONFLICT(user_identifier, search_date) DO UPDATE SET
            search_count = search_count + 1,
            updated_at = CURRENT_TIMESTAMP
    """, (user_identifier, today))
    conn.commit()
    conn.close()
    return True

# ---------------------------------------------------------------------------
# Search Necessity Detector
# ---------------------------------------------------------------------------

WEB_SEARCH_KEYWORDS = [
    "latest", "today", "current", "news", "recent", "update", "updates",
    "schedule", "when will", "announcement", "gazette", "notification",
    "registrar general", "census 2027 date", "launch date", "live", "weather",
    "who is currently", "presently", "2026", "2027 latest", "search web", "google"
]

def query_needs_web_search(query: str) -> bool:
    """
    Detect if a user's question asks for real-time/recent information
    that would benefit from live web search grounding.
    """
    q_lower = query.lower()
    return any(re.search(r'\b' + re.escape(kw) + r'\b', q_lower) for kw in WEB_SEARCH_KEYWORDS)

# ---------------------------------------------------------------------------
# Lightweight Server-Side Web Search Fallback
# ---------------------------------------------------------------------------

def perform_web_search(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Perform a web search for current information (prefers official gov/census domains).
    """
    try:
        search_query = f"{query} India Census 2027 government" if "census" in query.lower() else query
        url = f"https://html.duckduckgo.com/html/?q={url_quote(search_query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=8, proxies=REQUEST_PROXIES)
        if resp.status_code == 200:
            results = []
            # Extract snippets and titles using lightweight regex
            snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', resp.text, re.DOTALL)
            titles = re.findall(r'<a class="result__url[^>]*href="([^"]+)"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
            for i in range(min(max_results, len(snippets))):
                clean_text = re.sub(r'<[^>]+>', '', snippets[i]).strip()
                link = titles[i][0] if i < len(titles) else "https://censusindia.gov.in"
                if clean_text:
                    results.append({"snippet": clean_text, "url": link})
            return results
    except Exception as e:
        logger.warning(f"Server-side web search notice: {e}")
    return []

# ---------------------------------------------------------------------------
# System Prompts (Unrestricted & Multi-Lingual)
# ---------------------------------------------------------------------------

SYSTEM_PROMPTS = {
    "en": (
        "You are the official AI Census Assistant for Lakhipur Circle, India, supporting "
        "Census 2027 field functionaries (Enumerators and Supervisors) and citizens.\n\n"
        "CORE GUIDELINES:\n"
        "1. Open Knowledge: Answer questions about Census 2027, houselisting, enumeration procedures, "
        "demographics, and administrative rules naturally and comprehensively using your full training knowledge.\n"
        "2. Optional Local References: When official Lakhipur Circle records (Excel: HLB allocations, functionaries) "
        "or official manuals/FAQ (PDF: HLO Manual, FAQ) are supplied in the prompt and relevant to the user's question, "
        "prioritize them and cite the source (e.g. 'Source: HLO Manual, Page X' or 'Source: Census Record DB'). "
        "However, you are NEVER restricted to only answering from these documents.\n"
        "3. Web & Current Info: When web search information is provided, incorporate it to provide up-to-date facts, "
        "preferring official government sources (censusindia.gov.in, PIB, etc.).\n"
        "4. Honesty & Verification: If specific data cannot be verified or is unknown, state so clearly and politely "
        "instead of fabricating facts or names.\n"
        "5. Technical Support Contacts: When users need technical help with Lakhipur circle operations or the app, "
        "provide the Technical Assistants' contact info:\n"
        "   • Shahin Sha A. (+91 84534 41975) on WhatsApp\n"
        "   • S. A. Ahmed (+91 69019 80926) on WhatsApp\n"
        "6. Tone & Formatting: Keep answers professional, structured, and easy to read. Use bullet points and bolding."
    ),
    "as": (
        "আপুনি লাক্ষীপুৰ চাৰ্কেলৰ চৰকাৰী এআই লোকপিয়ল সহায়ক (AI Census Assistant), "
        "Census 2027 আৰু লোকপিয়ল কাৰ্যসূচীৰ বাবে সকলো প্ৰশ্নৰ উত্তৰ দিয়ে।\n"
        "যদি প্ৰসংগ তথ্যত (Excel/PDF) সঠিক তথ্য থাকে, সেইটো উল্লেখ কৰক আৰু উৎস দিয়ক।\n"
        "প্ৰসংগত নথকা সাধাৰণ লোকপিয়ল পদ্ধতি সম্পৰ্কেও আপোনাৰ জ্ঞানেৰে স্পষ্টকৈ উত্তৰ দিয়ক।\n"
        "অনুগ্ৰহ কৰি স্পষ্ট আৰু সন্মানজনক অসমীয়াত উত্তৰ দিয়ক।"
    ),
    "hi": (
        "आप लखीपुर सर्कल के आधिकारिक एआई जनगणना सहायक (AI Census Assistant) हैं, "
        "जो Census 2027 और जनगणना संचालन के बारे में सभी प्रश्नों का उत्तर देते हैं।\n"
        "यदि उपलब्ध संदर्भ (Excel/PDF) में सटीक जानकारी है, तो उसे प्राथमिकता दें और स्रोत बताएं।\n"
        "सामान्य जनगणना प्रक्रियाओं और नियमों के बारे में अपने ज्ञान का उपयोग करके स्पष्ट उत्तर दें।\n"
        "कृपया स्पष्ट और मानक हिंदी में उत्तर दें।"
    ),
    "bn": (
        "আপনি লাখিপুর সার্কেলের অফিশিয়াল এআই আদমশুমারি সহকারী (AI Census Assistant), "
        "যিনি Census 2027 এবং আদমশুমারি কার্যক্রম সম্পর্কে সকল প্রশ্নের সঠিক উত্তর প্রদান করেন।\n"
        "প্রদত্ত নথিতে তথ্য থাকলে তা উল্লেখ করুন এবং সাধারণ জনশুমারি নির্দেশিকা সম্পর্কেও স্পষ্ট উত্তর দিন।\n"
        "অনুগ্রহ করে স্পষ্ট ও প্রাঞ্জল বাংলায় উত্তর দিন।"
    )
}

# ---------------------------------------------------------------------------
# Gemini API Invocation with Web Grounding
# ---------------------------------------------------------------------------

def call_gemini_api(
    api_key: str,
    model: str,
    query: str,
    context: Dict[str, Any],
    lang: str = "en",
    enable_web_search: bool = False
) -> Tuple[Optional[str], bool, Optional[str]]:
    """
    Call the Gemini API, optionally with Google Search grounding.
    Returns (answer, was_web_searched, model_actually_used).
    """
    system_inst = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS["en"])

    context_text = context.get("context_text", "").strip()
    web_results = context.get("web_search_results", [])
    web_text = ""
    if web_results:
        web_text = "\n".join([f"• [{r.get('url', 'Web')}]: {r.get('snippet', '')}" for r in web_results])

    # Construct context sections
    sections = [system_inst]

    if context_text:
        sections.append(
            f"=== LOCAL CENSUS RECORDS & MANUAL REFERENCES ===\n"
            f"{context_text}\n"
            f"(Note: Use this local data when relevant and cite it; otherwise rely on your broad census intelligence.)"
        )

    if web_text:
        sections.append(
            f"=== CURRENT WEB SEARCH GROUNDING ===\n"
            f"{web_text}\n"
            f"(Note: Use these live web snippets to answer questions requiring current facts, citing official sources.)"
        )

    if context.get("contact_info"):
        sections.append(f"=== TECHNICAL SUPPORT CONTACTS ===\n{context['contact_info']}")

    sections.append(f"=== USER QUESTION ===\n{query}")

    prompt = "\n\n".join(sections)

    payload: Dict[str, Any] = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1200
        }
    }

    # Enable native Google Search tool if requested
    if enable_web_search:
        payload["tools"] = [{"google_search": {}}]

    was_web_searched = enable_web_search or bool(web_results)

    def _extract(data: Dict[str, Any]) -> Optional[str]:
        for candidate in data.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                text = (part.get("text") or "").strip()
                if text:
                    return text
        return None

    # Try the requested model first, then the known-good fallbacks. A retired
    # or misspelled model name returns 404 and would otherwise send every
    # question to the offline synthesizer for the life of the deployment.
    models_to_try = [model] + [m for m in GEMINI_MODEL_FALLBACKS if m != model]

    for attempt, candidate_model in enumerate(models_to_try):
        url = f"{GEMINI_ENDPOINT}/{candidate_model}:generateContent?key={api_key}"
        body = dict(payload)

        # (connect_timeout, read_timeout): a slow proxy hop (common on free
        # PythonAnywhere accounts) should not be confused with Gemini itself
        # being slow to generate, so connection setup fails fast while actual
        # generation gets real room to finish. One retry absorbs a single
        # transient timeout/network hiccup before giving up on this model —
        # previously any exception here (including a plain timeout) aborted
        # the whole call immediately, without even trying the fallback models
        # below, which is what made an occasional slow response look like a
        # total outage.
        resp = None
        for retry in range(2):
            try:
                resp = requests.post(url, json=body, timeout=(10, 45), proxies=REQUEST_PROXIES)
                break
            except Exception as exc:
                _record_provider_error("network", f"{candidate_model} (retry {retry}): {exc}")
        if resp is None:
            continue  # exhausted retries on this model — try the next fallback

        if resp.status_code == 200:
            answer = _extract(resp.json())
            if answer:
                if attempt:
                    logger.info(f"Gemini answered on fallback model {candidate_model}.")
                return answer, was_web_searched, candidate_model
            _record_provider_error("empty_response", f"{candidate_model} returned no text")
            continue

        # A 400 with the search tool attached usually means the key is not
        # entitled to grounding; the same prompt without tools still works.
        if resp.status_code == 400 and "tools" in body:
            body.pop("tools", None)
            try:
                retry = requests.post(url, json=body, timeout=25, proxies=REQUEST_PROXIES)
                if retry.status_code == 200:
                    answer = _extract(retry.json())
                    if answer:
                        logger.info("Gemini answered without the native search tool.")
                        return answer, bool(web_results), candidate_model
            except Exception as exc:
                _record_provider_error("network", f"{candidate_model} retry: {exc}")
                return None, was_web_searched, None

        if resp.status_code in (401, 403):
            _record_provider_error(
                "auth",
                f"HTTP {resp.status_code} — the API key was rejected. Check GEMINI_API_KEY.",
            )
            return None, was_web_searched, None

        if resp.status_code == 429:
            _record_provider_error("rate_limit", "HTTP 429 — Gemini quota exhausted for now.")
            return None, was_web_searched, None

        if resp.status_code == 404:
            logger.info(f"Model {candidate_model} not available; trying next.")
            continue

        _record_provider_error("http", f"{candidate_model}: HTTP {resp.status_code} {resp.text[:200]}")

    _record_provider_error("exhausted", "No Gemini model produced an answer.")
    return None, was_web_searched, None

# ---------------------------------------------------------------------------
# Fallback Local Synthesizer
# ---------------------------------------------------------------------------

def generate_local_rag_response(query: str, context: Dict[str, Any], lang: str = "en") -> str:
    """
    Offline synthesizer used when no language model is reachable.

    This path genuinely can only answer from the ingested records and manuals —
    it has no general knowledge. It therefore says so plainly rather than
    emitting a confident-looking canned paragraph, which is what previously
    made the assistant appear to be permanently restricted to the PDFs.
    """
    records = context.get("record_results", [])
    manuals = context.get("manual_results", []) or context.get("related_manual_results", [])
    q_lower = query.lower()

    # 1. HLB Record match
    if records:
        rec = records[0]
        area = rec.get("village_ward_name") or rec.get("landmark") or "Lakhipur Circle"
        return (
            f"**Census Allocation Record:**\n\n"
            f"• **HLB Number:** {rec.get('hlb_no')}\n"
            f"• **Enumerator:** {rec.get('enumerator_name')} ({rec.get('enumerator_user_id')})\n"
            f"• **Supervisor:** {rec.get('supervisor_name')}\n"
            f"• **Supervisory Circle:** {rec.get('supervisory_circle_no')}\n"
            f"• **Area/Village:** {area}\n\n"
            f"📌 *Source: Census Record Database (Lakhipur Circle)*"
        )

    # 2. Manual match
    if manuals:
        doc = manuals[0]
        return (
            f"**{doc.get('section_header') or 'Census Manual Guideline'}:**\n\n"
            f"{doc.get('chunk_text', '')[:600]}...\n\n"
            f"📌 *Source: {doc['doc_title']}, Page {doc['page_number']}*"
        )

    # 3. Nothing local matched, and there is no model to fall back on.
    return (
        "**The AI assistant is running in offline mode right now.**\n\n"
        "I could not find anything in the Lakhipur Circle records or the official manuals "
        "that answers this, and the AI service is not currently available on the server, "
        "so I cannot answer from general knowledge either. I would rather tell you that "
        "than guess.\n\n"
        "**What still works right now:**\n"
        "• Search an HLB number or a functionary name (e.g. `HLB 12`)\n"
        "• Browse the manuals from the Manuals tab\n"
        "• Mark attendance as usual\n\n"
        "If you are the Technical Assistant: the AI provider is unconfigured or unreachable — "
        "check **Admin → AI Provider Status**."
    )

# ---------------------------------------------------------------------------
# Main Query Generation Coordinator
# ---------------------------------------------------------------------------

def answer_query(
    query: str,
    model_name: str = "gemini-2.5-flash",
    lang: str = "en",
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Top-level generation function that coordinates RAG context retrieval,
    determines search necessity, enforces the 10-search daily quota,
    and calls Gemini or local fallback.
    """
    from .rag_engine import retrieve_rag_context
    start_time = time.time()

    user_identifier = user_id or "guest_user"
    used_searches, remaining_searches = get_user_search_usage(user_identifier)

    # ---- Decide whether this question needs live information at all --------
    # Ordinary questions ("what is a household?", "who supervises HLB 12?")
    # are answered from the model's own knowledge and the local records, and
    # never touch the daily search allowance.
    wants_web_search = query_needs_web_search(query)
    quota_exhausted = wants_web_search and remaining_searches <= 0
    may_search = wants_web_search and not quota_exhausted

    if quota_exhausted:
        logger.info(f"User {user_identifier} has used all {DAILY_WEB_SEARCH_LIMIT} web searches today.")

    web_results = perform_web_search(query) if may_search else []

    context = retrieve_rag_context(query)
    context["web_search_results"] = web_results

    api_key = get_api_key()
    answer: Optional[str] = None
    model_used: Optional[str] = None
    grounded = False

    if api_key and ("gemini" in model_name.lower()):
        answer, grounded, model_used = call_gemini_api(
            api_key,
            model_name,
            query,
            context,
            lang=lang,
            enable_web_search=may_search,
        )

    # ---- Charge the allowance only when a search actually happened ---------
    # The quota is consumed here, after the fact, rather than optimistically up
    # front: a question that merely contained the word "today" but was answered
    # without any lookup must not cost the user one of their ten.
    did_web_search = bool(answer) and (grounded or bool(web_results))
    if did_web_search:
        if consume_web_search_quota(user_identifier):
            used_searches += 1
            remaining_searches = max(0, remaining_searches - 1)
        else:
            did_web_search = False

    # ---- Fall back to the offline synthesizer only if there is no answer ---
    answered_by = "gemini"
    if not answer:
        answered_by = "offline_fallback"
        answer = generate_local_rag_response(query, context, lang=lang)
    elif did_web_search:
        answered_by = "gemini+web"

    if quota_exhausted and answer:
        answer += (
            f"\n\n*(You have used all {DAILY_WEB_SEARCH_LIMIT} web searches for today, "
            "so this was answered without a live lookup. The allowance resets at midnight IST.)*"
        )

    latency_ms = (time.time() - start_time) * 1000

    # Log query activity
    try:
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO activity_logs (user_id, action_type, query_text, source_tag)
            VALUES (?, 'ai_chat', ?, ?)
        """, (user_identifier, query, f"Model: {model_name} | WebSearch: {did_web_search}"))
        conn.execute("""
            INSERT INTO ai_usage_stats (model_name, query_count, latency_ms, status)
            VALUES (?, 1, ?, 'success')
        """, (model_name, latency_ms))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not log AI usage: {e}")

    # Cite local sources only when local material actually went into the
    # prompt. Previously the retrieval citations were attached to every reply,
    # so an answer drawn purely from the model's own knowledge still carried
    # "Source: HLO Manual, Page X" — which is what made the assistant look
    # like it could only speak from the PDFs.
    citations = context["citations"] if context.get("has_local_context") else []

    return {
        "query": query,
        "answer": answer,
        "intent": context["intent"],
        "citations": citations,
        "grounded_in_local_sources": bool(citations),
        "answered_by": answered_by,
        "ai_available": bool(api_key) and answered_by != "offline_fallback",
        "web_searched": did_web_search,
        "searches_used_today": used_searches,
        "searches_remaining_today": remaining_searches,
        "daily_search_limit": DAILY_WEB_SEARCH_LIMIT,
        "model_used": model_used or model_name,
        "latency_ms": round(latency_ms, 2)
    }
