"""
Census Assistant - Messaging Integration Gateway & Multi-Channel Fallback Matrix
Primary: WhatsApp Business Platform Cloud API.
Automated Fallbacks: 1. Telegram Bot | 2. Web Chat Interface | 3. Facebook Messenger | 4. Email Assistant
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional
from .llm_provider import answer_query

logger = logging.getLogger("MessagingGateway")
logging.basicConfig(level=logging.INFO)

# Configuration keys
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "census_assistant_webhook_verify_2024")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")

# There are two Technical Assistants who can be reached for support and who
# are the only two people authorized to log into the admin portal.
TECHNICAL_ASSISTANTS = [
    {
        "name": "Shahin Sha A.",
        "phone": "+91 84534 41975",
        "whatsapp_number": "918453441975",
        "whatsapp_link": "https://wa.me/918453441975",
        "designation": "Technical Assistant",
        "photo": "assets/shahin-sha.png"
    },
    {
        "name": "S. A. Ahmed",
        "phone": "+91 69019 80926",
        "whatsapp_number": "916901980926",
        "whatsapp_link": "https://wa.me/916901980926",
        "designation": "Technical Assistant",
        "photo": "assets/s-ahmed.png"
    }
]

# Backward-compatible aliases: the primary/first technical assistant, used
# wherever a single contact needs to be shown (e.g. AI chat/webhook footers).
TECH_ASSISTANT_NAME = TECHNICAL_ASSISTANTS[0]["name"]
TECH_ASSISTANT_PHONE = TECHNICAL_ASSISTANTS[0]["phone"]
WHATSAPP_DEEP_LINK = TECHNICAL_ASSISTANTS[0]["whatsapp_link"]

FALLBACK_HIERARCHY = [
    {
        "channel": "WhatsApp Business Platform",
        "priority": 1,
        "status": "Active (Primary)",
        "deep_link": WHATSAPP_DEEP_LINK,
        "description": "Direct WhatsApp interactive messaging and bot responses with deep-link."
    },
    {
        "channel": "Telegram Bot",
        "priority": 2,
        "status": "Active (Fallback 1)",
        "description": "Telegram bot for instant field functionary inquiries when WhatsApp API has rate limits or verification delays."
    },
    {
        "channel": "Web Chat Interface",
        "priority": 3,
        "status": "Active (Fallback 2)",
        "description": "In-app real-time AI assistant chat embedded in the single page application."
    },
    {
        "channel": "Facebook Messenger",
        "priority": 4,
        "status": "Configured (Fallback 3)",
        "description": "Messenger bot adapter for official page inquiries."
    },
    {
        "channel": "Email Assistant",
        "priority": 5,
        "status": "Configured (Fallback 4)",
        "description": "Asynchronous email query processor for formal escalations and report requests."
    }
]

def get_channel_status() -> Dict[str, Any]:
    """Return status and justification of all integrated channels."""
    return {
        "primary_channel": "WhatsApp Business Platform",
        "technical_assistant": {
            "name": TECH_ASSISTANT_NAME,
            "phone": TECH_ASSISTANT_PHONE,
            "whatsapp_link": WHATSAPP_DEEP_LINK
        },
        "technical_assistants": TECHNICAL_ASSISTANTS,
        "channels": FALLBACK_HIERARCHY,
        "justification": (
            "1. WhatsApp is the primary communication channel widely adopted by field enumerators in India.\n"
            "2. Telegram Bot provides zero-setup immediate messaging fallback without Meta verification barriers.\n"
            "3. Web Chat Interface provides 100% offline-ready local network access inside census offices.\n"
            "4. Messenger & Email ensure institutional archiving and formal governance communication."
        )
    }

def handle_whatsapp_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process inbound WhatsApp Cloud API webhook message and send AI response."""
    try:
        entry = payload.get("entry", [])
        if not entry:
            return {"status": "no_entry"}

        changes = entry[0].get("changes", [])
        if not changes:
            return {"status": "no_changes"}

        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return {"status": "no_messages"}

        message = messages[0]
        sender_phone = message.get("from")
        msg_type = message.get("type")

        if msg_type == "text":
            user_text = message.get("text", {}).get("body", "")
            logger.info(f"[WhatsApp Inbound] From {sender_phone}: {user_text}")

            # Generate RAG grounded answer
            ai_result = answer_query(user_text, model_name="gemini-3.6-flash", lang="en")
            reply_text = ai_result.get("answer", "Thank you for contacting Census Assistant.")

            # Append contact footer
            reply_text += f"\n\n📞 Tech Support: {TECH_ASSISTANT_NAME} ({TECH_ASSISTANT_PHONE})"

            send_whatsapp_message(sender_phone, reply_text)
            return {"status": "replied", "sender": sender_phone}

    except Exception as e:
        logger.error(f"Error handling WhatsApp webhook: {e}")
        return {"status": "error", "error": str(e)}

    return {"status": "ignored"}

def send_whatsapp_message(to_phone: str, message_text: str) -> bool:
    """Send outbound text message via WhatsApp Cloud API."""
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.info(f"[WhatsApp SIMULATION] Outbound to {to_phone}:\n{message_text}")
        return True

    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": message_text}
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        logger.info(f"WhatsApp send response: {resp.status_code}")
        return resp.status_code in [200, 201]
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}")
        return False

def handle_telegram_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process Telegram Bot inbound update."""
    try:
        msg = payload.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "")

        if not chat_id or not text:
            return {"status": "ignored"}

        if text.startswith("/start"):
            welcome = (
                f"🏛️ *Welcome to Census Assistant AI*\n"
                f"*Lakhipur Circle*\n\n"
                f"Ask any question about:\n"
                f"• Enumerator & Supervisor assignments (e.g. *Who is assigned to HLB 12?*)\n"
                f"• Census procedural rules and household definitions\n"
                f"• Search functionaries by name or phone\n\n"
                f"Technical Assistant: *{TECH_ASSISTANT_NAME}* ({TECH_ASSISTANT_PHONE})"
            )
            send_telegram_message(chat_id, welcome)
            return {"status": "welcome_sent"}

        # Process natural language query with RAG
        ai_result = answer_query(text, model_name="gemini-3.6-flash", lang="en")
        reply = ai_result.get("answer", "")
        send_telegram_message(chat_id, reply)
        return {"status": "replied"}

    except Exception as e:
        logger.error(f"Error handling Telegram webhook: {e}")
        return {"status": "error", "error": str(e)}

def send_telegram_message(chat_id: int, text: str) -> bool:
    """Send outbound message via Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN:
        logger.info(f"[Telegram SIMULATION] Outbound to {chat_id}:\n{text}")
        return True

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False
