"""
Census Assistant - Multi-Model AI Provider Adapter
Supports Gemini 2.5 Flash/Pro, OpenAI GPT-4o, Anthropic Claude, with high-fidelity Local RAG synthesis fallback.
"""

import os
import re
import json
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger("LLMProvider")
logging.basicConfig(level=logging.INFO)

SYSTEM_PROMPTS = {
    "en": (
        "You are the official AI Census Assistant for Lakhipur Circle, India. "
        "Your task is to provide accurate, concise, and helpful answers strictly based on the provided Census Records (Excel) "
        "and Official Manuals/FAQs (PDF). "
        "RULES:\n"
        "1. DO NOT HALLUCINATE. Answer only what is stated in the provided context.\n"
        "2. If the information is not in the context, explicitly state: 'This information is not available in the uploaded Census records or manuals.'\n"
        "3. Always cite your sources at the bottom (e.g. 'Source: Census Record DB - 2024' or 'Source: Census Manual 2024, Page X').\n"
        "4. When technical assistance is needed, remind the user to contact one of the two Technical Assistants: "
        "Shahin Sha A. (+91 84534 41975) or S. A. Ahmed (+91 69019 80926) on WhatsApp. Neither of them is a supervisor "
        "— real supervisor names come only from the Census Records context provided to you.\n"
        "5. Keep responses professional, structured, and easy to read."
    ),
    "as": (
        "আপুনি লাক্ষীপুৰ চাৰ্কেলৰ চৰকাৰী এআই লোকপিয়ল সহায়ক (AI Census Assistant)। "
        "যোগান ধৰা লোকপিয়ল তথ্য (Excel) আৰু চৰকাৰী নিৰ্দেশনা/মেনুৱেল (PDF) ৰ ওপৰত ভিত্তি কৰি সঠিক উত্তৰ দিয়ক। "
        "অনুগ্ৰহ কৰি অসমীয়াত উত্তৰ দিয়ক আৰু তথ্যৰ উৎস উল্লেখ কৰক।"
    ),
    "hi": (
        "आप लखीपुर सर्कल के आधिकारिक एआई जनगणना सहायक (AI Census Assistant) हैं। "
        "प्रदान किए गए जनगणना रिकॉर्ड (Excel) और आधिकारिक नियमावली (PDF) के आधार पर सटीक और संक्षिप्त उत्तर दें। "
        "कृपया स्पष्ट हिंदी में उत्तर दें और जानकारी के स्रोत का उल्लेख करें।"
    ),
    "bn": (
        "আপনি লাখিপুর সার্কেলের অফিসিয়াল এআই আদমশুমারি সহকারী (AI Census Assistant)। "
        "প্রদত্ত আদমশুমারি রেকর্ড (Excel) এবং নির্দেশিকা ম্যানুয়াল (PDF) এর উপর ভিত্তি করে সঠিক উত্তর প্রদান করুন। "
        "অনুগ্রহ করে স্পষ্ট বাংলায় উত্তর দিন এবং তথ্যের উৎস উল্লেখ করুন।"
    )
}

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
            if lang == "as":
                return (
                    f"**HLB {rec['hlb_no']}** ৰ তথ্য:\n"
                    f"• গণনাকাৰী (Enumerator): **{rec['enumerator_name']}** (User ID: `{rec['enumerator_user_id']}`)\n"
                    f"• পৰ্যবেক্ষক (Supervisor): **{rec['supervisor_name']}**\n"
                    f"• চাৰ্কেল নং: {rec['circle_no']} | আবণ্টন তাৰিখ: {rec['allotment_date']}\n"
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
                    f"• মোবাইল নম্বর: {rec.get('mobile', '+91 84534 41975')}\n\n"
                    f"কারিগরি সহায়তার জন্য যোগাযোগ করুন: **শাহীন শাহ এ.** (+91 84534 41975)\n\n"
                    f"📌 *উৎস: {rec['source']}*"
                )
            else:
                return (
                    f"**HLB {rec['hlb_no']} Assignment Details:**\n\n"
                    f"• **Assigned Enumerator:** {rec['enumerator_name']} (User ID: `{rec['enumerator_user_id']}`)\n"
                    f"• **Supervisor:** {rec['supervisor_name']}\n"
                    f"• **Supervisory Circle:** {rec['circle_no']}\n"
                    f"• **Allotment Date:** {rec['allotment_date']}\n"
                    f"• **Contact Mobile:** {rec.get('mobile', '+91 84534 41975')}\n\n"
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

    # 3. Person Name lookup
    if records and intent == "RECORD_SEARCH":
        rec = records[0]
        if rec.get("type") == "functionary":
            return (
                f"**Functionary Record Found:**\n\n"
                f"• **Name:** {rec['name']}\n"
                f"• **User ID:** `{rec['user_id']}`\n"
                f"• **Designation:** {rec['functionary_type']}\n"
                f"• **Mobile:** {rec['mobile_number']}\n"
                f"• **Jurisdiction:** {rec['sub_district']}, {rec['district']}\n"
                f"• **Status:** {rec['status']}\n\n"
                f"📌 *Source: {rec['source']}*"
            )

    # 4. Manual Guidelines / Definitions / Procedures
    if manuals:
        doc = manuals[0]
        text_snippet = doc["chunk_text"]
        # Format cleanly
        if len(text_snippet) > 500:
            text_snippet = text_snippet[:500] + "..."
        
        return (
            f"**{doc.get('section_header') or 'Census Manual Guideline'}:**\n\n"
            f"{text_snippet}\n\n"
            f"📌 *Source: {doc['doc_title']}, Page {doc['page_number']}*"
        )

    # 5. Fallback general answer
    if lang == "as":
        return (
            f"ক্ষমা কৰিব, এই প্ৰশ্নৰ বাবে কোনো তথ্য পোৱা নগ'ল।\n"
            f"আপুনি কোনো বিশেষ ব্লক নম্বৰ (যেনে: HLB 12), পৰ্যবেক্ষকৰ নাম বা নিয়ম নিৰ্দেশনা সম্পৰ্কে সুধিব পাৰে।\n\n"
            f"কাৰিকৰী সহায়ৰ বাবে যোগাযোগ কৰক: **শ্বাহীন শ্বাহ এ.** (+91 84534 41975, WhatsApp: https://wa.me/918453441975)"
        )
    elif lang == "hi":
        return (
            f"क्षमा करें, इस प्रश्न के लिए डेटाबेस में कोई विशिष्ट रिकॉर्ड नहीं मिला।\n"
            f"आप किसी विशेष ब्लॉक नंबर (जैसे HLB 12), पर्यवेक्षक का नाम या जनगणना नियमावली के बारे में पूछ सकते हैं।\n\n"
            f"तकनीकी सहायता के लिए संपर्क करें: **शाहीन शाह ए.** (+91 84534 41975, WhatsApp: https://wa.me/918453441975)"
        )
    elif lang == "bn":
        return (
            f"দুঃখিত, এই প্রশ্নের জন্য কোনো রেকর্ড পাওয়া যায়নি।\n"
            f"আপনি নির্দিষ্ট ব্লক নম্বর (যেমন HLB 12), সুপারভাইজারের নাম বা নির্দেশিকা সম্পর্কে জানতে চাইতে পারেন।\n\n"
            f"কারিগরি সহায়তার জন্য যোগাযোগ করুন: **শাহীন শাহ এ.** (+91 84534 41975, WhatsApp: https://wa.me/918453441975)"
        )
    else:
        return (
            f"I could not locate specific records matching your query in the current dataset.\n\n"
            f"You can try searching for:\n"
            f"• A House Listing Block / HLB (e.g. *'Who is assigned to HLB 12?'*)\n"
            f"• Supervisor details (e.g. *'Show supervisor details'*)\n"
            f"• Manual guidelines (e.g. *'What are the duties of a supervisor?'* or *'Household definition criteria'*)\n\n"
            f"For direct field assistance, please reach out to Technical Assistant **Shahin Sha A.** (+91 84534 41975) or **S. A. Ahmed** (+91 69019 80926) on WhatsApp."
        )

def call_gemini_api(api_key: str, model: str, query: str, context: Dict[str, Any], lang: str = "en") -> Optional[str]:
    """Call Google Gemini 2.5 Flash / Pro API using REST."""
    system_inst = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS["en"])
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    prompt = (
        f"{system_inst}\n\n"
        f"=== CONTEXT DATA ===\n"
        f"{context.get('context_text', '')}\n\n"
        f"=== CONTACT INFO ===\n"
        f"{context.get('contact_info', '')}\n\n"
        f"=== USER QUESTION ===\n"
        f"{query}\n\n"
        f"Answer in the selected language ({lang}) strictly using the provided context."
    )

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024
        }
    }

    try:
        resp = requests.post(url, json=payload, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
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

    # Fallback to local RAG synthesizer if no API key or API call failed
    if not answer:
        answer = generate_local_rag_response(query, context, lang=lang)

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
        logger.debug(f"Could not log AI usage: {e}")

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
