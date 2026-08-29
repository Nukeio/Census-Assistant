"""
Census Assistant - Multi-Model AI Provider Adapter
Supports Gemini 2.5 Flash/Pro, OpenAI GPT-4o, Anthropic Claude, with high-fidelity Local RAG synthesis fallback.
"""

import os
import re
import json
import logging
import requests
from urllib.parse import quote as url_quote
from typing import Dict, Any, Optional

logger = logging.getLogger("LLMProvider")
logging.basicConfig(level=logging.INFO)

# Kept for the local RAG fallback synthesizer only.
NOT_FOUND_PHRASE = "This information is not available in the uploaded Census documents."

SYSTEM_PROMPTS = {
    "en": (
        "You are the official AI Census Assistant for Lakhipur Circle, India, supporting "
        "Census 2027 field functionaries (Enumerators and Supervisors).\n\n"
        "You have TWO knowledge sources:\n"
        "1. OFFICIAL CONTEXT DATA — Lakhipur Circle records (Excel: HLB allocations, functionary details) "
        "and official manuals/FAQ (PDF: HLO Manual, FAQ). When this context is provided and relevant, "
        "ALWAYS prefer it and cite the source (e.g. 'Source: HLO Manual, Page X' or 'Source: Census Record DB').\n"
        "2. GENERAL KNOWLEDGE — Your training knowledge about Census 2027, census procedures, "
        "enumeration, houselisting, HLB concepts, field procedures, and general census terminology. "
        "Use this when the official context does not contain the answer.\n\n"
        "RULES:\n"
        "• If OFFICIAL CONTEXT DATA is provided and answers the question — use it first and cite the source.\n"
        "• If the context does not contain the answer but you have reliable general knowledge about census "
        "procedures — answer from that knowledge. Clearly note: 'Based on general Census guidelines' "
        "rather than claiming it is from the specific Lakhipur documents.\n"
        "• If the question is about something you genuinely do not know — say so honestly. "
        "Do NOT fabricate facts, names, or numbers.\n"
        "• If the question is completely unrelated to census, enumeration, or this app — politely "
        "redirect the user to census topics.\n"
        "• When technical assistance is needed, remind the user to contact: "
        "Shahin Sha A. (+91 84534 41975) or S. A. Ahmed (+91 69019 80926) on WhatsApp.\n"
        "• Keep responses professional, structured, and easy to read. Use bullet points or numbered "
        "lists for multi-step procedures."
    ),
    "as": (
        "আপুনি লাক্ষীপুৰ চাৰ্কেলৰ চৰকাৰী এআই লোকপিয়ল সহায়ক (AI Census Assistant), "
        "Census 2027-ৰ বাবে সহায় আগবঢ়ায়।\n"
        "যদি প্ৰসংগ তথ্যত (Excel/PDF) সঠিক উত্তৰ আছে, সেইটো আগতে উল্লেখ কৰক আৰু উৎস দিয়ক।\n"
        "যদি প্ৰসংগত উত্তৰ নাই, কিন্তু লোকপিয়ল পদ্ধতি সম্পৰ্কে সাধাৰণ জ্ঞান আছে, সেই ভিত্তিত উত্তৰ দিয়ক।\n"
        "নিৰ্ভুল তথ্য দিয়ক; মনগড়া তথ্য নিদিব।\n"
        "অনুগ্ৰহ কৰি অসমীয়াত উত্তৰ দিয়ক।"
    ),
    "hi": (
        "आप लखीपुर सर्कल के आधिकारिक एआई जनगणना सहायक (AI Census Assistant) हैं, "
        "जो Census 2027 के क्षेत्रीय कर्मचारियों की सहायता करते हैं।\n"
        "यदि प्रदान किए गए संदर्भ (Excel/PDF) में सटीक उत्तर है, तो उसे प्राथमिकता दें और स्रोत बताएं।\n"
        "यदि संदर्भ में उत्तर नहीं है लेकिन आपके पास जनगणना प्रक्रियाओं के बारे में सामान्य ज्ञान है, "
        "तो उसके आधार पर उत्तर दें।\n"
        "सटीक जानकारी दें; अनुमान से जानकारी न बनाएं।\n"
        "कृपया स्पष्ट हिंदी में उत्तर दें।"
    ),
    "bn": (
        "আপনি লাখিপুর সার্কেলের অফিসিয়াল এআই আদমশুমারি সহকারী (AI Census Assistant), "
        "যিনি Census 2027 মাঠ কর্মীদের সহায়তা করেন।\n"
        "প্রদত্ত প্রেক্ষাপট (Excel/PDF) এ সঠিক উত্তর থাকলে, সেটি প্রথমে উল্লেখ করুন এবং উৎস দিন।\n"
        "প্রেক্ষাপটে উত্তর না থাকলে কিন্তু জনশুমারি পদ্ধতি সম্পর্কে সাধারণ জ্ঞান থাকলে, সেই ভিত্তিতে উত্তর দিন।\n"
        "নির্ভুল তথ্য দিন; অনুমানে তথ্য বানাবেন না।\n"
        "অনুগ্রহ করে স্পষ্ট বাংলায় উত্তর দিন।"
    )
}

def _relevant_snippet(text: str, keywords: list, window: int = 600) -> str:
    """
    Return a window of `text` centered on the earliest matched keyword,
    instead of always slicing from the start. A matched manual/FAQ chunk is
    often ~800 chars covering multiple Q&A items; without this, the shown
    excerpt was frequently just "whatever came first in the chunk" rather
    than the part that actually answers the question.
    """
    if not text:
        return text
    lower = text.lower()
    best_pos = None
    for kw in keywords:
        idx = lower.find(kw.lower())
        if idx != -1 and (best_pos is None or idx < best_pos):
            best_pos = idx
    if best_pos is None:
        return text[:window] + ("..." if len(text) > window else "")
    start = max(0, best_pos - 120)
    end = min(len(text), start + window)
    snippet = text[start:end]
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{snippet}{suffix}"

def generate_local_rag_response(query: str, context: Dict[str, Any], lang: str = "en") -> str:
    """Intelligent rule-based RAG synthesizer when no external API key is configured."""
    q_lower = query.lower()
    records = context.get("record_results", [])
    manuals = context.get("manual_results", [])
    intent = context.get("intent", "GENERAL")

    # 1. HLB Assignment queries (still recognizes the legacy "eb"/"block" wording)
    eb_match = re.search(r'\b(?:eb|hlb|block)\s*#?\s*0*(\d+)\b', q_lower)
    if eb_match and records:
        rec = records[0]
        if rec.get("type") == "hlb_allocation":
            area_name = rec.get("area_name")
            maps_line_en = f"• **Area/Village:** {area_name}\n" if area_name else ""
            maps_line_as = f"• অঞ্চল/গাঁও: {area_name}\n" if area_name else ""
            maps_line_hi = f"• क्षेत्र/गांव: {area_name}\n" if area_name else ""
            maps_line_bn = f"• এলাকা/গ্রাম: {area_name}\n" if area_name else ""
            if lang == "as":
                return (
                    f"**HLB {rec['hlb_no']}** ৰ তথ্য:\n"
                    f"• গণনাকাৰী (Enumerator): **{rec['enumerator_name']}** (User ID: `{rec['enumerator_user_id']}`)\n"
                    f"• পৰ্যবেক্ষক (Supervisor): **{rec['supervisor_name']}**\n"
                    f"• চাৰ্কেল নং: {rec['circle_no']} | আবণ্টন তাৰিখ: {rec['allotment_date']}\n"
                    f"{maps_line_as}"
                    f"• মোবাইল নম্বৰ: {rec.get('mobile', '+91 84534 41975')}\n\n"
                    f"কাৰিকৰী সহায়ৰ বাবে যোগাযোগ কৰক: **শ্বাহীন শ্বাহ এ.** (+91 84534 41975)\n\n"
                    f"📌 *উৎস: {rec['source']}*"
                )
            elif lang == "hi":
                return (
                    f"**HLB {rec['hlb_no']}** का विवरण:\n"
                    f"• प्रगणक (Enumerator): **{rec['enumerator_name']}** (User ID: `{rec['enumerator_user_id']}`)\n"
                    f"• पर्यवेक्षक (Supervisor): **{rec['supervisor_name']}**\n"
                    f"• सर्कल सं.: {rec['circle_no']} | आवंटन तिथि: {rec['allotment_date']}\n"
                    f"{maps_line_hi}"
                    f"• मोबाइल नंबर: {rec.get('mobile', '+91 84534 41975')}\n\n"
                    f"तकनीकी सहायता के लिए संपर्क करें: **शाहीन शाह ए.** (+91 84534 41975)\n\n"
                    f"📌 *स्रोत: {rec['source']}*"
                )
            elif lang == "bn":
                return (
                    f"**HLB {rec['hlb_no']}** এর বিবরণ:\n"
                    f"• গণনাকারী (Enumerator): **{rec['enumerator_name']}** (User ID: `{rec['enumerator_user_id']}`)\n"
                    f"• তত্ত্বাবধায়ক (Supervisor): **{rec['supervisor_name']}**\n"
                    f"• সার্কেল নং: {rec['circle_no']} | বরাদ্দের তারিখ: {rec['allotment_date']}\n"
                    f"{maps_line_bn}"
                    f"• মোবাইল নম্বর: {rec.get('mobile', '+91 84534 41975')}\n\n"
                    f"কারিগরি সহায়তার জন্য যোগাযোগ করুন: **শাহীন শাহ এ.** (+91 84534 41975)\n\n"
                    f"📌 *উৎস: {rec['source']}*"
                )
            else:
                maps_link_line = ""
                if area_name:
                    maps_url = "https://www.google.com/maps/search/?api=1&query=" + \
                        url_quote(f"{area_name}, Lakhipur Circle, Assam, India")
                    maps_link_line = f"• **Google Maps:** {maps_url}\n"
                return (
                    f"**HLB {rec['hlb_no']} Assignment Details:**\n\n"
                    f"• **Assigned Enumerator:** {rec['enumerator_name']} (User ID: `{rec['enumerator_user_id']}`)\n"
                    f"• **Supervisor:** {rec['supervisor_name']}\n"
                    f"• **Supervisory Circle:** {rec['circle_no']}\n"
                    f"{maps_line_en}"
                    f"• **Allotment Date:** {rec['allotment_date']}\n"
                    f"• **Contact Mobile:** {rec.get('mobile', '+91 84534 41975')}\n"
                    f"{maps_link_line}\n"
                    f"For technical assistance or re-allocations, contact Technical Assistant **Shahin Sha A.** (+91 84534 41975) on WhatsApp.\n\n"
                    f"📌 *Source: {rec['source']}*"
                )

    # 2. Supervisor info query. S. A. Ahmed is a Technical Assistant, NOT a
    # supervisor — real supervisor names/circles only ever come from an
    # actual matched HLB allocation record (cross-referenced from both
    # Excel sheets). If none matched this query, point the user at the
    # searchable Supervisors tab instead of guessing a name.
    if "supervisor" in q_lower and not any(w in q_lower for w in ["duty", "duties", "role", "guideline"]):
        hlb_rec = next((r for r in records if r.get("type") == "hlb_allocation" and r.get("supervisor_name")), None)
        if hlb_rec:
            if lang == "as":
                return (
                    f"**পৰ্যবেক্ষক বিৱৰণ (Supervisor Details):**\n"
                    f"• পৰ্যবেক্ষক: **{hlb_rec['supervisor_name']}**\n"
                    f"• চাৰ্কেল নং: {hlb_rec['circle_no']} | HLB: {hlb_rec['hlb_no']}\n"
                    f"• গণনাকাৰী: {hlb_rec['enumerator_name']}\n\n"
                    f"কাৰিকৰী সহায়ৰ বাবে যোগাযোগ কৰক: **শ্বাহীন শ্বাহ এ.** (+91 84534 41975) বা **এছ. এ. আহমেদ** (+91 69019 80926)\n\n"
                    f"📌 *উৎস: {hlb_rec['source']}*"
                )
            elif lang == "hi":
                return (
                    f"**पर्यवेक्षक विवरण (Supervisor Details):**\n"
                    f"• पर्यवेक्षक: **{hlb_rec['supervisor_name']}**\n"
                    f"• सर्कल सं.: {hlb_rec['circle_no']} | HLB: {hlb_rec['hlb_no']}\n"
                    f"• प्रगणक: {hlb_rec['enumerator_name']}\n\n"
                    f"तकनीकी सहायता के लिए संपर्क करें: **शाहीन शाह ए.** (+91 84534 41975) या **एस. ए. अहमद** (+91 69019 80926)\n\n"
                    f"📌 *स्रोत: {hlb_rec['source']}*"
                )
            elif lang == "bn":
                return (
                    f"**তত্ত্বাবধায়ক বিবরণ (Supervisor Details):**\n"
                    f"• তত্ত্বাবধায়ক: **{hlb_rec['supervisor_name']}**\n"
                    f"• সার্কেল নং: {hlb_rec['circle_no']} | HLB: {hlb_rec['hlb_no']}\n"
                    f"• গণনাকারী: {hlb_rec['enumerator_name']}\n\n"
                    f"কারিগরি সহায়তার জন্য যোগাযোগ করুন: **শাহীন শাহ এ.** (+91 84534 41975) বা **এস. এ. আহমেদ** (+91 69019 80926)\n\n"
                    f"📌 *উৎস: {hlb_rec['source']}*"
                )
            else:
                return (
                    f"**Supervisor Information:**\n\n"
                    f"• **Supervisor Name:** {hlb_rec['supervisor_name']}\n"
                    f"• **Supervisory Circle:** {hlb_rec['circle_no']}\n"
                    f"• **HLB:** {hlb_rec['hlb_no']} | **Enumerator:** {hlb_rec['enumerator_name']}\n\n"
                    f"For technical assistance, contact **Shahin Sha A.** (+91 84534 41975) or **S. A. Ahmed** (+91 69019 80926) on WhatsApp.\n\n"
                    f"📌 *Source: {hlb_rec['source']}*"
                )
        else:
            if lang == "as":
                return (
                    f"এই প্ৰশ্নটোৰ সৈতে মিল থকা কোনো নিৰ্দিষ্ট পৰ্যবেক্ষকৰ নথি পোৱা নগ'ল।\n"
                    f"অনুগ্ৰহ কৰি এপ্‌টোৰ **পৰ্যবেক্ষক** পৃষ্ঠাত নাম, ID বা মোবাইল নম্বৰেৰে সন্ধান কৰক।\n\n"
                    f"কাৰিকৰী সহায়ৰ বাবে যোগাযোগ কৰক: **শ্বাহীন শ্বাহ এ.** (+91 84534 41975) বা **এছ. এ. আহমেদ** (+91 69019 80926)"
                )
            elif lang == "hi":
                return (
                    f"इस प्रश्न से मेल खाता कोई विशिष्ट पर्यवेक्षक रिकॉर्ड नहीं मिला।\n"
                    f"कृपया ऐप के **पर्यवेक्षक** पृष्ठ पर नाम, ID या मोबाइल नंबर से खोजें।\n\n"
                    f"तकनीकी सहायता के लिए संपर्क करें: **शाहीन शाह ए.** (+91 84534 41975) या **एस. ए. अहमद** (+91 69019 80926)"
                )
            elif lang == "bn":
                return (
                    f"এই প্রশ্নের সাথে মিলে যায় এমন কোনো নির্দিষ্ট তত্ত্বাবধায়ক রেকর্ড পাওয়া যায়নি।\n"
                    f"অনুগ্রহ করে অ্যাপের **তত্ত্বাবধায়ক** পৃষ্ঠায় নাম, ID বা মোবাইল নম্বর দিয়ে খুঁজুন।\n\n"
                    f"কারিগরি সহায়তার জন্য যোগাযোগ করুন: **শাহীন শাহ এ.** (+91 84534 41975) বা **এস. এ. আহমেদ** (+91 69019 80926)"
                )
            else:
                return (
                    f"I could not find a specific supervisor record matching this query.\n"
                    f"Try searching by name, ID, or mobile number on the app's **Supervisor** tab — it lists every "
                    f"supervisor cross-referenced from the census records with their circle and HLB count.\n\n"
                    f"For technical assistance, contact **Shahin Sha A.** (+91 84534 41975) or **S. A. Ahmed** (+91 69019 80926) on WhatsApp."
                )

    # 3. Person Name lookup (RECORD_SEARCH or GENERAL intent with confirmed record match)
    if records and intent in ("RECORD_SEARCH", "GENERAL"):
        rec = records[0]
        if rec.get("type") == "functionary":
            is_low_confidence = rec.get("confidence") == "low"
            title = (
                "**Closest Match Found** (not an exact match for your search — "
                "please verify the name/ID below):"
                if is_low_confidence else
                "**Functionary Record Found:**"
            )
            area_line = f"• **Area/Village:** {rec['area_name']}\n" if rec.get("area_name") else ""
            maps_line = f"• **Google Maps:** {rec['maps_url']}\n" if rec.get("maps_url") else ""
            return (
                f"{title}\n\n"
                f"• **Name:** {rec['name']}\n"
                f"• **User ID:** `{rec['user_id']}`\n"
                f"• **Designation:** {rec['functionary_type']}\n"
                f"• **Mobile:** {rec['mobile_number']}\n"
                f"• **Jurisdiction:** {rec['sub_district']}, {rec['district']}\n"
                f"{area_line}"
                f"{maps_line}"
                f"• **Status:** {rec['status']}\n\n"
                f"📌 *Source: {rec['source']}*"
            )

    # 4. Manual Guidelines / Definitions / Procedures
    if manuals:
        doc = manuals[0]
        query_keywords = [w for w in re.split(r'[^a-zA-Z0-9]', query) if len(w) >= 3]
        text_snippet = _relevant_snippet(doc["chunk_text"], query_keywords)

        return (
            f"**{doc.get('section_header') or 'Census Manual Guideline'}:**\n\n"
            f"{text_snippet}\n\n"
            f"📌 *Source: {doc['doc_title']}, Page {doc['page_number']}*"
        )

    # 5. Nothing found in any source — return the exact required phrase
    return NOT_FOUND_PHRASE

def call_gemini_api(api_key: str, model: str, query: str, context: Dict[str, Any], lang: str = "en") -> Optional[str]:
    """Call Google Gemini API using REST (supports Gemini 2.5 Flash/Pro and similar)."""
    system_inst = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS["en"])
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    context_text = context.get("context_text", "").strip()

    # Build the prompt. When official context is available it is included so
    # Gemini prioritises it; when it is empty Gemini falls back to its general
    # census training knowledge instead of returning a hard refusal.
    if context_text:
        prompt = (
            f"{system_inst}\n\n"
            f"=== OFFICIAL CONTEXT DATA (Lakhipur Circle Records & Manuals) ===\n"
            f"{context_text}\n\n"
            f"=== CONTACT INFO ===\n"
            f"{context.get('contact_info', '')}\n\n"
            f"=== USER QUESTION ===\n"
            f"{query}\n\n"
            f"Answer using the OFFICIAL CONTEXT DATA above when it is relevant. "
            f"If the context does not cover this question, answer from your general "
            f"census knowledge and note that it is based on general guidelines."
        )
    else:
        # No RAG context found — let Gemini answer from general census knowledge.
        # This is intentional: many valid questions (e.g. 'What is Census 2027?',
        # 'Explain enumeration') are not in the local PDFs but Gemini knows them.
        logger.info("No local context retrieved — calling Gemini with general census knowledge.")
        prompt = (
            f"{system_inst}\n\n"
            f"=== CONTACT INFO ===\n"
            f"{context.get('contact_info', '')}\n\n"
            f"=== USER QUESTION ===\n"
            f"{query}\n\n"
            f"No specific Lakhipur Circle records matched this query. "
            f"Answer from your general knowledge about Census 2027, census procedures, "
            f"enumeration, houselisting, and related topics. "
            f"If this is not a census-related question, politely redirect the user."
        )

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.2,   # Slight temperature for natural language; still conservative
            "maxOutputTokens": 1024
        }
    }

    try:
        resp = requests.post(url, json=payload, timeout=25)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    answer = parts[0].get("text", "").strip()
                    if answer:
                        return answer
        else:
            logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Gemini API request failed: {e}")
    return None

def answer_query(query: str, model_name: str = "gemini-2.5-flash", lang: str = "en") -> Dict[str, Any]:
    """Top-level generation function that coordinates RAG retrieval and LLM call or local fallback."""
    from .rag_engine import retrieve_rag_context
    import time
    start_time = time.time()

    context = retrieve_rag_context(query)
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    answer = None
    if api_key and ("gemini" in model_name.lower()):
        answer = call_gemini_api(api_key, model_name, query, context, lang=lang)

    # Fallback to local RAG synthesizer if no API key, API call failed, or
    # the call returned None (ungrounded response detected).
    if not answer:
        answer = generate_local_rag_response(query, context, lang=lang)

    # Final safety net: ensure empty/None answers always return the not-found phrase
    if not answer or not answer.strip():
        answer = NOT_FOUND_PHRASE

    latency_ms = (time.time() - start_time) * 1000

    # Log query and record AI usage stat
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO activity_logs (user_id, action_type, query_text, source_tag)
            VALUES ('user', 'ai_chat', ?, ?)
        """, (query, f"Model: {model_name} | {context['intent']}"))
        conn.execute("""
            INSERT INTO ai_usage_stats (model_name, query_count, latency_ms, status)
            VALUES (?, 1, ?, 'success')
        """, (model_name, latency_ms))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not log AI usage: {e}")

    return {
        "query": query,
        "answer": answer,
        "intent": context["intent"],
        "citations": context["citations"],
        "record_count": len(context.get("record_results", [])),
        "manual_count": len(context.get("manual_results", [])),
        "model_used": model_name,
        "latency_ms": round(latency_ms, 2)
    }
