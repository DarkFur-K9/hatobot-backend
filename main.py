import os
import json
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="HatoBot - WhatsApp Bot")

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN") or os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ADMIN_NUMBER = os.getenv("ADMIN_NUMBER", "6369189024")
API_URL = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

# ─── In-memory session store (no DB needed) ───
# Format: { "phone_number": { "state": "...", "cart": {}, "data": {} } }
sessions: dict = {}

# ─── Tamil Nadu Menu ───
MENU_ITEMS = [
    {"id": "1",  "name": "Idli (2 pcs)",           "price": 40},
    {"id": "2",  "name": "Masala Dosa",             "price": 70},
    {"id": "3",  "name": "Pongal",                  "price": 60},
    {"id": "4",  "name": "Vada (2 pcs)",            "price": 50},
    {"id": "5",  "name": "Upma",                    "price": 50},
    {"id": "6",  "name": "Chettinad Chicken Curry", "price": 220},
    {"id": "7",  "name": "Mutton Kuzhambu",         "price": 280},
    {"id": "8",  "name": "Fish Curry",              "price": 200},
    {"id": "9",  "name": "Sambar Rice",             "price": 80},
    {"id": "10", "name": "Rasam Rice",              "price": 70},
    {"id": "11", "name": "Chicken Biryani",         "price": 180},
    {"id": "12", "name": "Mutton Biryani",          "price": 240},
    {"id": "13", "name": "Veg Biryani",             "price": 130},
    {"id": "14", "name": "Parotta + Salna",         "price": 90},
    {"id": "15", "name": "Kothu Parotta",           "price": 120},
    {"id": "16", "name": "Filter Coffee",           "price": 30},
    {"id": "17", "name": "Lassi",                   "price": 60},
    {"id": "18", "name": "Tender Coconut",          "price": 50},
    {"id": "19", "name": "Payasam",                 "price": 60},
    {"id": "20", "name": "Halwa",                   "price": 50},
]

TURF_SLOTS = [
    "06:00 AM - 07:00 AM",
    "07:00 AM - 08:00 AM",
    "08:00 AM - 09:00 AM",
    "09:00 AM - 10:00 AM",
    "10:00 AM - 11:00 AM",
    "04:00 PM - 05:00 PM",
    "05:00 PM - 06:00 PM",
    "06:00 PM - 07:00 PM",
    "07:00 PM - 08:00 PM",
    "08:00 PM - 09:00 PM",
    "09:00 PM - 10:00 PM",
    "10:00 PM - 11:00 PM",
]

MENU_ITEM_MAP = {item["id"]: item for item in MENU_ITEMS}

# ─── Session helpers ───

def get_session(phone: str) -> dict:
    if phone not in sessions:
        sessions[phone] = {"state": "init", "cart": {}, "data": {}}
    return sessions[phone]

def reset_session(phone: str):
    sessions[phone] = {"state": "init", "cart": {}, "data": {}}


# ─── WhatsApp API helpers ───

async def send_text(to: str, body: str):
    await _post({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body, "preview_url": False}
    })

async def send_buttons(to: str, body: str, buttons: list[dict]):
    """Max 3 buttons. Each button: {"id": "...", "title": "..."}"""
    await _post({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
                    for b in buttons[:3]
                ]
            }
        }
    })

async def send_list(to: str, body: str, button_label: str, sections: list[dict]):
    """
    sections = [
        {
            "title": "Section Name",
            "rows": [{"id": "...", "title": "...", "description": "..."}]
        }
    ]
    Max 10 rows total across all sections.
    """
    await _post({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body},
            "action": {
                "button": button_label,
                "sections": sections
            }
        }
    })

async def _post(payload: dict):
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(API_URL, json=payload, headers=headers)
        if resp.status_code != 200:
            print(f"[WA ERROR] {resp.status_code}: {resp.text}")
        return resp


# ─── Menu helpers ───

def build_menu_sections() -> list[dict]:
    """Split 20 menu items into sections of max 10 rows each."""
    categories = {}
    for item in MENU_ITEMS:
        cat = _get_category(item["id"])
        categories.setdefault(cat, []).append(item)

    sections = []
    for cat, items in categories.items():
        rows = [
            {
                "id": f"menu_{item['id']}",
                "title": item["name"][:24],
                "description": f"₹{item['price']}"
            }
            for item in items
        ]
        sections.append({"title": cat, "rows": rows})
    return sections

def _get_category(item_id: str) -> str:
    iid = int(item_id)
    if iid <= 5:   return "🌅 Breakfast"
    if iid <= 13:  return "🍛 Main Course & Biryani"
    if iid <= 15:  return "🫓 Snacks"
    if iid <= 18:  return "☕ Beverages"
    return "🍮 Desserts"

def build_cart_text(cart: dict) -> str:
    if not cart:
        return "Your cart is empty."
    lines = ["🛒 *Your Cart:*\n"]
    total = 0
    for item_id, qty in cart.items():
        item = MENU_ITEM_MAP.get(item_id)
        if item:
            subtotal = item["price"] * qty
            total += subtotal
            lines.append(f"• {item['name']} × {qty} = ₹{subtotal}")
    lines.append(f"\n💰 *Total: ₹{total}*")
    return "\n".join(lines)

def cart_total(cart: dict) -> int:
    total = 0
    for item_id, qty in cart.items():
        item = MENU_ITEM_MAP.get(item_id)
        if item:
            total += item["price"] * qty
    return total

def build_slot_sections() -> list[dict]:
    morning = [s for s in TURF_SLOTS if "AM" in s]
    evening = [s for s in TURF_SLOTS if "PM" in s]
    return [
        {
            "title": "🌅 Morning Slots",
            "rows": [{"id": f"slot_{i}", "title": s, "description": "Available"} for i, s in enumerate(morning)]
        },
        {
            "title": "🌆 Evening Slots",
            "rows": [{"id": f"slot_{i+len(morning)}", "title": s, "description": "Available"} for i, s in enumerate(evening)]
        }
    ]


# ─── Core Bot Logic ───

async def handle_incoming(phone: str, msg_type: str, msg_body: str, interactive_id: str, interactive_title: str):
    session = get_session(phone)
    state = session["state"]

    # Normalize text input
    text = msg_body.strip().lower() if msg_body else ""
    btn_id = interactive_id or ""
    btn_title = interactive_title or ""
    raw = btn_id or text  # prefer button ID for routing

    print(f"[{phone}] state={state} | text={text!r} | btn_id={btn_id!r}")

    # ── INIT ──
    if state == "init":
        if "hi hatobot" in text or text in ("hi", "hello", "hey"):
            session["state"] = "main_menu"
            await send_buttons(
                phone,
                "Welcome to *HatoBot!* 👋\n\nPlease choose a demo to get started:",
                [
                    {"id": "hotel_demo",   "title": "🏨 Hotel Demo"},
                    {"id": "turf_demo",    "title": "⚽ Turf Demo"},
                    {"id": "get_started",  "title": "🚀 Get Started"},
                ]
            )
        else:
            await send_text(phone, "👋 Say *Hi Hatobot* to get started!")
        return

    # ── MAIN MENU ──
    if state == "main_menu":
        if raw == "hotel_demo":
            session["state"] = "hotel_browsing"
            session["cart"] = {}
            await send_text(phone, "🏨 *Welcome to Chennai Hotel!*\n\nHere is our menu. Tap *View Menu* to browse and add items.")
            await send_list(
                phone,
                "Browse our Tamil Nadu menu and select an item to add to your cart 🍛",
                "📋 View Menu",
                build_menu_sections()
            )

        elif raw == "turf_demo":
            session["state"] = "turf_slot"
            await send_text(phone, "⚽ *Welcome to Chennai Turf Booking!*\n\nPlease select a time slot for *today* 📅")
            await send_list(
                phone,
                "Choose your preferred time slot:",
                "⏰ Select Slot",
                build_slot_sections()
            )

        elif raw == "get_started":
            session["state"] = "gs_name"
            await send_text(phone, "🚀 *Let's get you started with HatoBot!*\n\nWhat is your *name*? 👤")

        else:
            await send_buttons(
                phone,
                "Please choose an option 👇",
                [
                    {"id": "hotel_demo",  "title": "🏨 Hotel Demo"},
                    {"id": "turf_demo",   "title": "⚽ Turf Demo"},
                    {"id": "get_started", "title": "🚀 Get Started"},
                ]
            )
        return

    # ── HOTEL: BROWSING ──
    if state == "hotel_browsing":
        if btn_id.startswith("menu_"):
            item_id = btn_id.replace("menu_", "")
            item = MENU_ITEM_MAP.get(item_id)
            if item:
                session["cart"][item_id] = session["cart"].get(item_id, 0) + 1
                qty = session["cart"][item_id]
                await send_buttons(
                    phone,
                    f"✅ *{item['name']}* added! (×{qty})\n\n{build_cart_text(session['cart'])}",
                    [
                        {"id": "add_more",    "title": "➕ Add More"},
                        {"id": "view_cart",   "title": "🛒 View Cart"},
                    ]
                )
            return

        if raw in ("add_more", "view_menu"):
            await send_list(
                phone,
                "Select another item to add 🍛",
                "📋 View Menu",
                build_menu_sections()
            )
            return

        if raw == "view_cart":
            cart = session["cart"]
            if not cart:
                await send_text(phone, "🛒 Your cart is empty. Please add items first.")
                await send_list(phone, "Select items:", "📋 View Menu", build_menu_sections())
                return
            session["state"] = "hotel_order_type"
            total = cart_total(cart)
            await send_buttons(
                phone,
                f"{build_cart_text(cart)}\n\nIs this *Takeaway* or *Dine In*? 🍽️",
                [
                    {"id": "takeaway", "title": "🥡 Takeaway"},
                    {"id": "dine_in",  "title": "🍽️ Dine In"},
                ]
            )
            return

        # If they type something unexpected while browsing
        await send_buttons(
            phone,
            "What would you like to do?",
            [
                {"id": "add_more",  "title": "➕ Add More Items"},
                {"id": "view_cart", "title": "🛒 View Cart"},
            ]
        )
        return

    # ── HOTEL: ORDER TYPE ──
    if state == "hotel_order_type":
        if raw in ("takeaway", "dine_in"):
            order_type = "Takeaway 🥡" if raw == "takeaway" else "Dine In 🍽️"
            session["data"]["order_type"] = order_type
            session["state"] = "hotel_payment"
            total = cart_total(session["cart"])
            await send_buttons(
                phone,
                f"{build_cart_text(session['cart'])}\n\n📋 *Order Type:* {order_type}\n\n💳 How would you like to pay?",
                [
                    {"id": "pay_now",     "title": "💳 Pay Now"},
                    {"id": "pay_counter", "title": "🏪 Pay at Counter"},
                ]
            )
        else:
            await send_buttons(
                phone,
                "Please select your order type:",
                [
                    {"id": "takeaway", "title": "🥡 Takeaway"},
                    {"id": "dine_in",  "title": "🍽️ Dine In"},
                ]
            )
        return

    # ── HOTEL: PAYMENT ──
    if state == "hotel_payment":
        if raw in ("pay_now", "pay_counter"):
            order_type = session["data"].get("order_type", "")
            total = cart_total(session["cart"])
            if raw == "pay_now":
                pay_msg = "💳 *Payment link sent!* Complete your payment to confirm the order."
            else:
                pay_msg = "🏪 *Pay at Counter* selected. Please pay when you arrive."

            await send_text(
                phone,
                f"{pay_msg}\n\n✅ *After payment, your order will be received in the dashboard and the team can accept it.*\n\n🙏 Thank you for ordering with *Chennai Hotel!*"
            )
            reset_session(phone)
            await send_buttons(
                phone,
                "Anything else?",
                [{"id": "hotel_demo", "title": "🏨 New Order"}, {"id": "get_started", "title": "🚀 Get Started"}]
            )
        else:
            await send_buttons(
                phone,
                "Please choose a payment option:",
                [
                    {"id": "pay_now",     "title": "💳 Pay Now"},
                    {"id": "pay_counter", "title": "🏪 Pay at Counter"},
                ]
            )
        return

    # ── TURF: SLOT SELECTION ──
    if state == "turf_slot":
        if btn_id.startswith("slot_"):
            slot_index = int(btn_id.replace("slot_", ""))
            slot = TURF_SLOTS[slot_index] if slot_index < len(TURF_SLOTS) else None
            if slot:
                session["data"]["slot"] = slot
                session["state"] = "turf_payment"
                await send_buttons(
                    phone,
                    f"⚽ *Turf Booking Summary*\n\n📅 Date: Today\n⏰ Slot: {slot}\n💰 Amount: ₹500\n\nProceed to payment?",
                    [
                        {"id": "turf_pay_now", "title": "💳 Pay Now"},
                    ]
                )
        else:
            await send_list(
                phone,
                "Please select a time slot:",
                "⏰ Select Slot",
                build_slot_sections()
            )
        return

    # ── TURF: PAYMENT ──
    if state == "turf_payment":
        if raw == "turf_pay_now":
            slot = session["data"].get("slot", "")
            await send_text(
                phone,
                f"💳 *Payment link sent!* Complete your payment to confirm the booking.\n\n✅ *After payment, the slot ({slot}) will automatically be booked and updated in your dashboard.*\n\n🏆 Thank you for booking with *Chennai Turf!*"
            )
            reset_session(phone)
            await send_buttons(
                phone,
                "Anything else?",
                [{"id": "turf_demo", "title": "⚽ Book Another"}, {"id": "get_started", "title": "🚀 Get Started"}]
            )
        else:
            await send_buttons(
                phone,
                "Tap below to pay and confirm your slot:",
                [{"id": "turf_pay_now", "title": "💳 Pay Now"}]
            )
        return

    # ── GET STARTED: NAME ──
    if state == "gs_name":
        if msg_body and msg_body.strip():
            name = msg_body.strip()
            session["data"]["name"] = name
            session["state"] = "gs_business"
            await send_list(
                phone,
                f"Nice to meet you, *{name}!* 😊\n\nWhat would you like to *automate*? Choose your business type:",
                "💼 Select Business",
                [
                    {
                        "title": "Business Types",
                        "rows": [
                            {"id": "biz_clinic",  "title": "🏥 Clinic",  "description": "Appointment & patient management"},
                            {"id": "biz_saloon",  "title": "✂️ Saloon",  "description": "Booking & customer management"},
                            {"id": "biz_hotel",   "title": "🏨 Hotel",   "description": "Menu, orders & table management"},
                            {"id": "biz_turf",    "title": "⚽ Turf",    "description": "Slot booking & payments"},
                            {"id": "biz_other",   "title": "💼 Other",   "description": "Tell us about your business"},
                        ]
                    }
                ]
            )
        else:
            await send_text(phone, "Please tell us your *name* to continue 👤")
        return

    # ── GET STARTED: BUSINESS TYPE ──
    if state == "gs_business":
        name = session["data"].get("name", "there")
        business_map = {
            "biz_clinic": "Clinic",
            "biz_saloon": "Saloon",
            "biz_hotel":  "Hotel",
            "biz_turf":   "Turf",
        }

        if btn_id in business_map:
            biz = business_map[btn_id]
            session["data"]["business"] = biz
            await _notify_admin(phone, name, biz)
            await send_text(
                phone,
                f"✅ *Got it, {name}!*\n\nYour *{biz}* automation request has been received. Our team will *review and contact you shortly* 📞\n\n_Please wait while we prepare a custom HatoBot solution for you!_ 🚀"
            )
            reset_session(phone)
            await send_buttons(
                phone,
                "Anything else?",
                [{"id": "hotel_demo", "title": "🏨 Hotel Demo"}, {"id": "turf_demo", "title": "⚽ Turf Demo"}]
            )

        elif btn_id == "biz_other":
            session["state"] = "gs_other_desc"
            await send_text(phone, "💼 Please *describe your business* briefly.\n\nWhat do you do and what would you like to automate? 📝")

        else:
            await send_list(
                phone,
                "Please choose your business type:",
                "💼 Select Business",
                [
                    {
                        "title": "Business Types",
                        "rows": [
                            {"id": "biz_clinic", "title": "🏥 Clinic",  "description": "Appointment & patient management"},
                            {"id": "biz_saloon", "title": "✂️ Saloon",  "description": "Booking & customer management"},
                            {"id": "biz_hotel",  "title": "🏨 Hotel",   "description": "Menu, orders & table management"},
                            {"id": "biz_turf",   "title": "⚽ Turf",    "description": "Slot booking & payments"},
                            {"id": "biz_other",  "title": "💼 Other",   "description": "Tell us about your business"},
                        ]
                    }
                ]
            )
        return

    # ── GET STARTED: OTHER DESCRIPTION ──
    if state == "gs_other_desc":
        if msg_body and msg_body.strip():
            name = session["data"].get("name", "there")
            description = msg_body.strip()
            session["data"]["business"] = f"Other — {description}"
            await _notify_admin(phone, name, f"Other: {description}")
            await send_text(
                phone,
                f"📨 *Thank you, {name}!*\n\nWe've received your business details. Our team will *review and contact you* soon! 🙏\n\n_We're excited to build something great for you!_ ✨"
            )
            reset_session(phone)
            await send_buttons(
                phone,
                "Anything else?",
                [{"id": "hotel_demo", "title": "🏨 Hotel Demo"}, {"id": "turf_demo", "title": "⚽ Turf Demo"}]
            )
        else:
            await send_text(phone, "Please describe your business so our team can help you 📝")
        return

    # ── FALLBACK ──
    reset_session(phone)
    await send_text(phone, "👋 Say *Hi Hatobot* to start over!")


# ─── Admin Notification ───

async def _notify_admin(phone: str, name: str, business: str):
    """Send lead details to admin WhatsApp number."""
    msg = (
        f"🔔 *New HatoBot Lead!*\n\n"
        f"👤 Name: {name}\n"
        f"📱 Number: +{phone}\n"
        f"💼 Bot Needed: {business}"
    )
    await send_text(ADMIN_NUMBER, msg)
    print(f"[ADMIN NOTIFIED] Name={name} | Phone={phone} | Business={business}")


# ─── Webhook Routes ───

@app.get("/webhook")
async def verify_webhook(request: Request):
    """WhatsApp webhook verification."""
    params = dict(request.query_params)
    mode      = params.get("hub.mode")
    token     = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("[WEBHOOK] Verified successfully.")
        return PlainTextResponse(challenge)

    return PlainTextResponse("Forbidden", status_code=403)


@app.post("/webhook")
async def receive_webhook(request: Request):
    """Receive and process incoming WhatsApp messages."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"status": "invalid json"}, status_code=400)

    print(f"[WEBHOOK IN] {json.dumps(body, indent=2)}")

    try:
        entry   = body["entry"][0]
        changes = entry["changes"][0]
        value   = changes["value"]

        # Ignore status updates (delivered, read, etc.)
        if "statuses" in value and "messages" not in value:
            return JSONResponse({"status": "ok"})

        messages = value.get("messages", [])
        if not messages:
            return JSONResponse({"status": "ok"})

        message = messages[0]
        phone   = message["from"]
        msg_type = message.get("type", "")

        msg_body         = ""
        interactive_id   = ""
        interactive_title = ""

        if msg_type == "text":
            msg_body = message.get("text", {}).get("body", "")

        elif msg_type == "interactive":
            interactive = message.get("interactive", {})
            itype = interactive.get("type", "")
            if itype == "button_reply":
                interactive_id    = interactive["button_reply"]["id"]
                interactive_title = interactive["button_reply"]["title"]
            elif itype == "list_reply":
                interactive_id    = interactive["list_reply"]["id"]
                interactive_title = interactive["list_reply"]["title"]

        await handle_incoming(phone, msg_type, msg_body, interactive_id, interactive_title)

    except (KeyError, IndexError) as e:
        print(f"[WEBHOOK PARSE ERROR] {e}")

    return JSONResponse({"status": "ok"})


@app.get("/health")
async def health():
    return {"status": "running", "active_sessions": len(sessions)}
