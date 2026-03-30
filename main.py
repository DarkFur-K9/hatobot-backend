import os
import json
import httpx
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="HatoBot - WhatsApp Bot")

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN") or os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ADMIN_NUMBER = os.getenv("ADMIN_NUMBER", "6369189024")
API_URL = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

# ─── In-memory session store ───
sessions: dict = {}

# ─── Menu (10 featured items, fits in one WhatsApp list) ───
MENU_ITEMS = [
    {"id": "1",  "name": "Idli (2 pcs)",           "price": 40,  "cat": "🌅 Breakfast"},
    {"id": "2",  "name": "Masala Dosa",             "price": 70,  "cat": "🌅 Breakfast"},
    {"id": "3",  "name": "Pongal",                  "price": 60,  "cat": "🌅 Breakfast"},
    {"id": "4",  "name": "Chettinad Chicken",       "price": 220, "cat": "🍛 Main Course"},
    {"id": "5",  "name": "Mutton Kuzhambu",         "price": 280, "cat": "🍛 Main Course"},
    {"id": "6",  "name": "Fish Curry",              "price": 200, "cat": "🍛 Main Course"},
    {"id": "7",  "name": "Chicken Biryani",         "price": 180, "cat": "🍛 Main Course"},
    {"id": "8",  "name": "Veg Biryani",             "price": 130, "cat": "🍛 Main Course"},
    {"id": "9",  "name": "Kothu Parotta",           "price": 120, "cat": "🫓 Snacks"},
    {"id": "10", "name": "Filter Coffee",           "price": 30,  "cat": "☕ Beverages"},
]

MENU_ITEM_MAP = {item["id"]: item for item in MENU_ITEMS}

# ─── Turf slots (10 max for WhatsApp list) ───
TURF_SLOTS = [
    "06:00 AM - 07:00 AM",
    "07:00 AM - 08:00 AM",
    "08:00 AM - 09:00 AM",
    "09:00 AM - 10:00 AM",
    "04:00 PM - 05:00 PM",
    "05:00 PM - 06:00 PM",
    "06:00 PM - 07:00 PM",
    "07:00 PM - 08:00 PM",
    "08:00 PM - 09:00 PM",
    "09:00 PM - 10:00 PM",
]

TURF_PRICE = 500  # ₹ per slot


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

async def send_buttons(to: str, body: str, buttons: list):
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

async def send_list(to: str, body: str, button_label: str, sections: list):
    """Max 10 rows total across all sections."""
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


# ─── Helper builders ───

def get_next_7_days() -> list:
    """Returns next 7 days as list rows for WhatsApp list message."""
    # IST = UTC+5:30
    now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    rows = []
    for i in range(7):
        d = now + timedelta(days=i)
        if i == 0:
            label = "Today"
        elif i == 1:
            label = "Tomorrow"
        else:
            label = d.strftime("%A")  # Weekday name
        date_str = d.strftime("%d %b %Y")
        rows.append({
            "id": f"date_{d.strftime('%Y-%m-%d')}",
            "title": f"{label}, {date_str}",
            "description": "✅ Available"
        })
    return rows

def build_menu_sections() -> list:
    """Build menu as WhatsApp list sections (max 10 rows total)."""
    from collections import defaultdict
    cats = defaultdict(list)
    for item in MENU_ITEMS:
        cats[item["cat"]].append(item)
    sections = []
    for cat, items in cats.items():
        sections.append({
            "title": cat,
            "rows": [
                {
                    "id": f"menu_{item['id']}",
                    "title": item["name"][:24],
                    "description": f"₹{item['price']}"
                }
                for item in items
            ]
        })
    return sections

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

def build_slot_sections(date_label: str) -> list:
    morning = [s for s in TURF_SLOTS if "AM" in s]
    evening = [s for s in TURF_SLOTS if "PM" in s]
    return [
        {
            "title": "🌅 Morning Slots",
            "rows": [
                {"id": f"slot_{i}", "title": s, "description": f"₹{TURF_PRICE} • {date_label}"}
                for i, s in enumerate(morning)
            ]
        },
        {
            "title": "🌆 Evening Slots",
            "rows": [
                {"id": f"slot_{i+len(morning)}", "title": s, "description": f"₹{TURF_PRICE} • {date_label}"}
                for i, s in enumerate(evening)
            ]
        }
    ]


# ─── Admin Notification ───

async def notify_demo_complete(phone: str, demo: str):
    """Notify admin when a user completes a demo."""
    msg = (
        f"🎯 *Demo Completed!*\n\n"
        f"📱 Customer: +{phone}\n"
        f"🤖 Demo Used: {demo}\n"
        f"⏰ Time: {(datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime('%d %b %Y, %I:%M %p')} IST"
    )
    await send_text(ADMIN_NUMBER, msg)
    print(f"[ADMIN NOTIFIED] Phone=+{phone} | Demo={demo}")

async def notify_lead(phone: str, name: str, business: str):
    """Notify admin of a Get Started lead."""
    msg = (
        f"🔔 *New HatoBot Lead!*\n\n"
        f"👤 Name: {name}\n"
        f"📱 Number: +{phone}\n"
        f"💼 Bot Needed: {business}"
    )
    await send_text(ADMIN_NUMBER, msg)
    print(f"[LEAD] Name={name} | Phone={phone} | Business={business}")


# ─── Core Bot Logic ───

async def handle_incoming(phone: str, msg_type: str, msg_body: str, interactive_id: str, interactive_title: str):
    session = get_session(phone)
    state = session["state"]

    text    = msg_body.strip().lower() if msg_body else ""
    btn_id  = interactive_id or ""
    raw     = btn_id or text

    print(f"[{phone}] state={state!r} | text={text!r} | btn_id={btn_id!r}")

    # ════════════════════════════
    # INIT
    # ════════════════════════════
    if state == "init":
        if "hi hatobot" in text or text in ("hi", "hello", "hey", "start"):
            session["state"] = "main_menu"
            await send_buttons(
                phone,
                "Welcome to *HatoBot!* 👋\n\nI'm a WhatsApp automation demo bot. Choose what you'd like to explore:",
                [
                    {"id": "hotel_demo",  "title": "🏨 Hotel Demo"},
                    {"id": "turf_demo",   "title": "⚽ Turf Demo"},
                    {"id": "get_started", "title": "🚀 Get Started"},
                ]
            )
        else:
            await send_text(phone, "👋 Say *Hi Hatobot* to get started!")
        return

    # ════════════════════════════
    # MAIN MENU
    # ════════════════════════════
    if state == "main_menu":
        if raw == "hotel_demo":
            session["state"] = "hotel_menu"
            session["cart"] = {}
            await send_text(phone, "🏨 *Welcome to Chennai Hotel!*\n\nHere's our menu. Select an item to add to your cart 🍛")
            await send_list(
                phone,
                "Tap 'View Menu' to browse our dishes:",
                "📋 View Menu",
                build_menu_sections()
            )

        elif raw == "turf_demo":
            session["state"] = "turf_date"
            await send_text(phone, "⚽ *Welcome to Chennai Turf Booking!*\n\nFirst, select your preferred *date* 📅")
            await send_list(
                phone,
                "Choose a date for your turf booking:",
                "📅 Select Date",
                [{"title": "Available Dates", "rows": get_next_7_days()}]
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

    # ════════════════════════════════════════
    # HOTEL FLOW
    # ════════════════════════════════════════

    # ── HOTEL: SELECT ITEM FROM MENU ──
    if state == "hotel_menu":
        if btn_id.startswith("menu_"):
            item_id = btn_id.replace("menu_", "")
            item = MENU_ITEM_MAP.get(item_id)
            if item:
                session["data"]["pending_item"] = item_id
                session["state"] = "hotel_qty"
                await send_text(
                    phone,
                    f"✅ You selected *{item['name']}* — ₹{item['price']}\n\nHow many would you like? 🔢\n_(Type a number, e.g. 1, 2, 3)_"
                )
        else:
            # Nudge them back to menu
            await send_list(
                phone,
                "Please select an item from our menu:",
                "📋 View Menu",
                build_menu_sections()
            )
        return

    # ── HOTEL: ENTER QUANTITY ──
    if state == "hotel_qty":
        if text.isdigit() and int(text) > 0:
            qty = int(text)
            item_id = session["data"].get("pending_item")
            item = MENU_ITEM_MAP.get(item_id)
            if item:
                session["cart"][item_id] = session["cart"].get(item_id, 0) + qty
                session["data"].pop("pending_item", None)
                session["state"] = "hotel_cart"
                await send_buttons(
                    phone,
                    f"✅ *{item['name']} × {qty}* added!\n\n{build_cart_text(session['cart'])}",
                    [
                        {"id": "hotel_add_more",    "title": "➕ Add Item"},
                        {"id": "hotel_place_order", "title": "🧾 Place Order"},
                    ]
                )
        else:
            item_id = session["data"].get("pending_item")
            item = MENU_ITEM_MAP.get(item_id)
            name = item["name"] if item else "the item"
            await send_text(phone, f"Please type a valid *number* for the quantity of *{name}* 👆\n_(e.g. 1, 2, 3)_")
        return

    # ── HOTEL: CART — ADD MORE OR PLACE ORDER ──
    if state == "hotel_cart":
        if raw == "hotel_add_more":
            session["state"] = "hotel_menu"
            await send_list(
                phone,
                "Select another item to add 🍛",
                "📋 View Menu",
                build_menu_sections()
            )

        elif raw == "hotel_place_order":
            cart = session["cart"]
            if not cart:
                await send_text(phone, "🛒 Your cart is empty! Please add items first.")
                session["state"] = "hotel_menu"
                await send_list(phone, "Select an item:", "📋 View Menu", build_menu_sections())
                return
            session["state"] = "hotel_payment"
            total = cart_total(cart)
            bill = build_cart_text(cart)
            await send_buttons(
                phone,
                f"🧾 *Your Bill*\n\n{bill}\n\n──────────────\n💰 *Total: ₹{total}*\n──────────────\n\nTap *Pay Now* to complete your order:",
                [{"id": "hotel_pay_now", "title": "💳 Pay Now"}]
            )

        else:
            await send_buttons(
                phone,
                f"{build_cart_text(session['cart'])}\n\nWhat would you like to do?",
                [
                    {"id": "hotel_add_more",    "title": "➕ Add Item"},
                    {"id": "hotel_place_order", "title": "🧾 Place Order"},
                ]
            )
        return

    # ── HOTEL: PAYMENT ──
    if state == "hotel_payment":
        if raw == "hotel_pay_now":
            total = cart_total(session["cart"])
            await send_text(
                phone,
                f"✅ *Payment of ₹{total} successful!*\n\n📋 After payment, your order will be received in the *dashboard* and our team will prepare it right away!\n\n🙏 Thank you for ordering with *Chennai Hotel!*"
            )
            await notify_demo_complete(phone, "🏨 Hotel Demo")
            reset_session(phone)
            await send_buttons(
                phone,
                "What would you like to do next?",
                [{"id": "get_started", "title": "🚀 Get Started"}]
            )
        else:
            total = cart_total(session["cart"])
            await send_buttons(
                phone,
                f"💰 *Total payable: ₹{total}*\n\nTap Pay Now to confirm your order:",
                [{"id": "hotel_pay_now", "title": "💳 Pay Now"}]
            )
        return

    # ════════════════════════════════════════
    # TURF FLOW
    # ════════════════════════════════════════

    # ── TURF: DATE SELECTION ──
    if state == "turf_date":
        if btn_id.startswith("date_"):
            date_val = btn_id.replace("date_", "")  # e.g. "2025-04-01"
            # Get friendly label from title
            date_label = interactive_title or date_val
            session["data"]["date"] = date_val
            session["data"]["date_label"] = date_label
            session["state"] = "turf_slot"
            await send_list(
                phone,
                f"📅 *Date selected:* {date_label}\n\nNow choose your *time slot:*",
                "⏰ Select Slot",
                build_slot_sections(date_label)
            )
        else:
            await send_list(
                phone,
                "Please select a date for your booking:",
                "📅 Select Date",
                [{"title": "Available Dates", "rows": get_next_7_days()}]
            )
        return

    # ── TURF: SLOT SELECTION ──
    if state == "turf_slot":
        if btn_id.startswith("slot_"):
            slot_index = int(btn_id.replace("slot_", ""))
            slot = TURF_SLOTS[slot_index] if slot_index < len(TURF_SLOTS) else None
            if slot:
                date_label = session["data"].get("date_label", "Selected Date")
                session["data"]["slot"] = slot
                session["state"] = "turf_payment"
                await send_buttons(
                    phone,
                    f"⚽ *Turf Booking Summary*\n\n"
                    f"📅 Date: {date_label}\n"
                    f"⏰ Slot: {slot}\n"
                    f"💰 Amount: ₹{TURF_PRICE}\n\n"
                    f"Tap *Pay Now* to confirm your booking:",
                    [{"id": "turf_pay_now", "title": "💳 Pay Now"}]
                )
        else:
            date_label = session["data"].get("date_label", "Selected Date")
            await send_list(
                phone,
                "Please select a time slot:",
                "⏰ Select Slot",
                build_slot_sections(date_label)
            )
        return

    # ── TURF: PAYMENT ──
    if state == "turf_payment":
        if raw == "turf_pay_now":
            slot = session["data"].get("slot", "")
            date_label = session["data"].get("date_label", "")
            await send_text(
                phone,
                f"✅ *Payment of ₹{TURF_PRICE} successful!*\n\n"
                f"📅 Date: {date_label}\n"
                f"⏰ Slot: {slot}\n\n"
                f"📋 After payment, your slot will be *automatically booked and updated in the dashboard!*\n\n"
                f"🏆 Thank you for booking with *Chennai Turf!*"
            )
            await notify_demo_complete(phone, "⚽ Turf Demo")
            reset_session(phone)
            await send_buttons(
                phone,
                "What would you like to do next?",
                [{"id": "get_started", "title": "🚀 Get Started"}]
            )
        else:
            slot = session["data"].get("slot", "")
            date_label = session["data"].get("date_label", "")
            await send_buttons(
                phone,
                f"📅 {date_label} | ⏰ {slot} | 💰 ₹{TURF_PRICE}\n\nTap Pay Now to confirm:",
                [{"id": "turf_pay_now", "title": "💳 Pay Now"}]
            )
        return

    # ════════════════════════════════════════
    # GET STARTED FLOW
    # ════════════════════════════════════════

    # ── GET STARTED: NAME ──
    if state == "gs_name":
        if msg_body and msg_body.strip():
            name = msg_body.strip()
            session["data"]["name"] = name
            session["state"] = "gs_business"
            await send_list(
                phone,
                f"Nice to meet you, *{name}!* 😊\n\nWhat type of business would you like to automate with WhatsApp?",
                "💼 Select Business",
                [
                    {
                        "title": "Business Types",
                        "rows": [
                            {"id": "biz_clinic",  "title": "🏥 Clinic",  "description": "Appointments & patient management"},
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
            await notify_lead(phone, name, biz)
            await send_text(
                phone,
                f"✅ *Got it, {name}!*\n\nYour *{biz}* automation request has been received.\nOur team will *review and contact you shortly* 📞\n\n_We're excited to build a custom HatoBot for you!_ 🚀"
            )
            reset_session(phone)
            await send_buttons(
                phone,
                "Want to explore our demos while you wait?",
                [
                    {"id": "hotel_demo", "title": "🏨 Hotel Demo"},
                    {"id": "turf_demo",  "title": "⚽ Turf Demo"},
                ]
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
                            {"id": "biz_clinic",  "title": "🏥 Clinic",  "description": "Appointments & patient management"},
                            {"id": "biz_saloon",  "title": "✂️ Saloon",  "description": "Booking & customer management"},
                            {"id": "biz_hotel",   "title": "🏨 Hotel",   "description": "Menu, orders & table management"},
                            {"id": "biz_turf",    "title": "⚽ Turf",    "description": "Slot booking & payments"},
                            {"id": "biz_other",   "title": "💼 Other",   "description": "Tell us about your business"},
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
            await notify_lead(phone, name, f"Other: {description}")
            await send_text(
                phone,
                f"📨 *Thank you, {name}!*\n\nWe've received your business details. Our team will *review and contact you* soon! 🙏\n\n_We're excited to build something great for you!_ ✨"
            )
            reset_session(phone)
            await send_buttons(
                phone,
                "Want to explore our demos while you wait?",
                [
                    {"id": "hotel_demo", "title": "🏨 Hotel Demo"},
                    {"id": "turf_demo",  "title": "⚽ Turf Demo"},
                ]
            )
        else:
            await send_text(phone, "Please describe your business so our team can help you 📝")
        return

    # ── FALLBACK ──
    reset_session(phone)
    await send_text(phone, "👋 Say *Hi Hatobot* to start over!")


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

        # Ignore status updates
        if "statuses" in value and "messages" not in value:
            return JSONResponse({"status": "ok"})

        messages = value.get("messages", [])
        if not messages:
            return JSONResponse({"status": "ok"})

        message   = messages[0]
        phone     = message["from"]
        msg_type  = message.get("type", "")

        msg_body          = ""
        interactive_id    = ""
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
