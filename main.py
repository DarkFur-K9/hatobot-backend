import os
import json
import httpx
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="HatoBot - WhatsApp Automation Demo")

WHATSAPP_TOKEN  = os.getenv("WHATSAPP_TOKEN") or os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN    = os.getenv("VERIFY_TOKEN")
ADMIN_NUMBER    = os.getenv("ADMIN_NUMBER", "6369189024")
CART_BASE_URL   = os.getenv("CART_BASE_URL", "https://landingpagebackend-opal.vercel.app")
API_URL         = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

# ─── In-memory session store ───
sessions: dict = {}

# ─── Menu Items ───
MENU_ITEMS = [
    {"id": "1",  "name": "Idli (2 pcs)",       "price": 40,  "cat": "🌅 Breakfast"},
    {"id": "2",  "name": "Masala Dosa",         "price": 70,  "cat": "🌅 Breakfast"},
    {"id": "3",  "name": "Pongal",              "price": 60,  "cat": "🌅 Breakfast"},
    {"id": "4",  "name": "Chettinad Chicken",   "price": 220, "cat": "🍛 Main Course"},
    {"id": "5",  "name": "Mutton Kuzhambu",     "price": 280, "cat": "🍛 Main Course"},
    {"id": "6",  "name": "Fish Curry",          "price": 200, "cat": "🍛 Main Course"},
    {"id": "7",  "name": "Chicken Biryani",     "price": 180, "cat": "🍛 Main Course"},
    {"id": "8",  "name": "Veg Biryani",         "price": 130, "cat": "🍛 Main Course"},
    {"id": "9",  "name": "Kothu Parotta",       "price": 120, "cat": "🫓 Snacks"},
    {"id": "10", "name": "Filter Coffee",       "price": 30,  "cat": "☕ Beverages"},
]
MENU_ITEM_MAP = {item["id"]: item for item in MENU_ITEMS}

# ─── Turf Slots ───
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
TURF_PRICE_PER_SLOT = 500  # ₹


# ════════════════════════════════════════
# SESSION HELPERS
# ════════════════════════════════════════

def get_session(phone: str) -> dict:
    if phone not in sessions:
        sessions[phone] = {
            "state": "init",
            "cart": {},           # {item_id: qty}
            "turf_slots": [],     # list of booked slot strings
            "data": {},
            "last_seen": datetime.utcnow(),
        }
    sessions[phone]["last_seen"] = datetime.utcnow()
    return sessions[phone]

def reset_session(phone: str):
    sessions[phone] = {
        "state": "init",
        "cart": {},
        "turf_slots": [],
        "data": {},
        "last_seen": datetime.utcnow(),
    }


# ════════════════════════════════════════
# WHATSAPP API HELPERS
# ════════════════════════════════════════

async def send_text(to: str, body: str):
    await _post({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body, "preview_url": False}
    })

async def send_buttons(to: str, body: str, buttons: list):
    """Max 3 buttons. Each: {"id": "...", "title": "..."}"""
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

async def send_cta_url(to: str, body: str, button_text: str, url: str):
    """Send a CTA URL button (opens webview)."""
    await _post({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "cta_url",
            "body": {"text": body},
            "action": {
                "name": "cta_url",
                "parameters": {
                    "display_text": button_text,
                    "url": url
                }
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


# ════════════════════════════════════════
# BUILDER HELPERS
# ════════════════════════════════════════

def get_next_7_days() -> list:
    now = datetime.utcnow() + timedelta(hours=5, minutes=30)  # IST
    rows = []
    for i in range(7):
        d = now + timedelta(days=i)
        label = "Today" if i == 0 else ("Tomorrow" if i == 1 else d.strftime("%A"))
        date_str = d.strftime("%d %b %Y")
        rows.append({
            "id": f"date_{d.strftime('%Y-%m-%d')}",
            "title": f"{label}, {date_str}",
            "description": "✅ Available"
        })
    return rows

def build_menu_sections() -> list:
    from collections import defaultdict
    cats = defaultdict(list)
    for item in MENU_ITEMS:
        cats[item["cat"]].append(item)
    return [
        {
            "title": cat,
            "rows": [
                {"id": f"menu_{item['id']}", "title": item["name"][:24], "description": f"₹{item['price']}"}
                for item in items
            ]
        }
        for cat, items in cats.items()
    ]

def build_slot_sections(date_label: str, selected_slots: list = None) -> list:
    selected_slots = selected_slots or []
    morning = [s for s in TURF_SLOTS if "AM" in s]
    evening = [s for s in TURF_SLOTS if "PM" in s]
    
    def get_desc(s):
        if s in selected_slots:
            return "📌 Selected (Already in list)"
        return f"₹{TURF_PRICE_PER_SLOT} • {date_label}"

    return [
        {
            "title": "🌅 Morning Slots",
            "rows": [{"id": f"slot_{i}", "title": s, "description": get_desc(s)} for i, s in enumerate(morning)]
        },
        {
            "title": "🌆 Evening Slots",
            "rows": [{"id": f"slot_{i+len(morning)}", "title": s, "description": get_desc(s)} for i, s in enumerate(evening)]
        }
    ]

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
    return sum(
        MENU_ITEM_MAP[item_id]["price"] * qty
        for item_id, qty in cart.items()
        if item_id in MENU_ITEM_MAP
    )

def build_order_summary(cart: dict) -> str:
    lines = ["📋 *Order Summary:*\n"]
    total = 0
    for item_id, qty in cart.items():
        item = MENU_ITEM_MAP.get(item_id)
        if item:
            subtotal = item["price"] * qty
            total += subtotal
            lines.append(f"{item['name']} x{qty}")
    lines.append(f"\n💰 Total: ₹{total}")
    return "\n".join(lines)

def build_turf_summary(slots: list, date_label: str) -> str:
    total = TURF_PRICE_PER_SLOT * len(slots)
    lines = [f"⚽ *Booking Summary*\n"]
    lines.append(f"📅 Date: {date_label}")
    for i, s in enumerate(slots, 1):
        lines.append(f"⏰ Slot {i}: {s}")
    lines.append(f"\n💰 Slots Total: ₹{total}")
    lines.append(f"🎁 Discount: ₹{total}")
    lines.append(f"✅ *Final Price: ₹0 (Demo Offer 🎉)*")
    return "\n".join(lines)


# ════════════════════════════════════════
# AI ASSISTANT (keyword matching + fallback)
# ════════════════════════════════════════

def ai_assist(text: str) -> str | None:
    """Simple keyword matcher. Returns a routing hint or None."""
    t = text.lower()
    if any(k in t for k in ["menu", "food", "order", "eat", "hotel", "restaurant"]):
        return "hotel"
    if any(k in t for k in ["book", "turf", "slot", "field", "sport", "play"]):
        return "turf"
    if any(k in t for k in ["start", "help", "info", "price", "demo", "bot", "hatobot"]):
        return "help"
    if any(k in t for k in ["hi", "hello", "hey", "good morning", "good evening", "namaste"]):
        return "greet"
    return None


# ════════════════════════════════════════
# ADMIN NOTIFICATIONS
# ════════════════════════════════════════

async def notify_demo_complete(phone: str, demo: str, details: str = ""):
    msg = (
        f"🎯 *Demo Completed!*\n\n"
        f"📱 Customer: +{phone}\n"
        f"🤖 Demo: {demo}\n"
        + (f"📝 {details}\n" if details else "")
        + f"⏰ Time: {(datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime('%d %b %Y, %I:%M %p')} IST"
    )
    await send_text(ADMIN_NUMBER, msg)

async def notify_lead(phone: str, name: str, business: str):
    msg = (
        f"🔔 *New HatoBot Lead!*\n\n"
        f"👤 Name: {name}\n"
        f"📱 Number: +{phone}\n"
        f"💼 Bot Needed: {business}"
    )
    await send_text(ADMIN_NUMBER, msg)


# ════════════════════════════════════════
# RETURN CTA HELPER
# ════════════════════════════════════════

async def send_return_cta(phone: str):
    await send_buttons(
        phone,
        "Want to explore more? 👇",
        [{"id": "get_started", "title": "🚀 Get Started"}]
    )


# ════════════════════════════════════════
# MAIN MENU SENDER
# ════════════════════════════════════════

async def send_main_menu(phone: str, session: dict):
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


# ════════════════════════════════════════
# CORE BOT LOGIC
# ════════════════════════════════════════

async def handle_incoming(phone: str, msg_type: str, msg_body: str, interactive_id: str, interactive_title: str):
    session = get_session(phone)
    state   = session["state"]

    text   = msg_body.strip().lower() if msg_body else ""
    btn_id = interactive_id or ""
    raw    = btn_id or text

    print(f"[{phone}] state={state!r} | text={text!r} | btn_id={btn_id!r}")

    # ────────────────────────────────────
    # GLOBAL: Always allow switching demos or AI assistance interrupts
    # ────────────────────────────────────
    hint = ai_assist(text)
    
    # If a clear demo switch is requested (via button or text hint)
    effective_raw = raw
    if hint == "hotel": effective_raw = "hotel_demo"
    if hint == "turf":  effective_raw = "turf_demo"
    if hint == "help":  effective_raw = "get_started"

    if effective_raw in ("get_started", "hotel_demo", "turf_demo"):
        if effective_raw == "get_started":
            session["state"] = "gs_name"
            await send_text(phone, "🚀 *Let's get you started with HatoBot!*\n\nWhat is your *name*? 👤")
            return
        if effective_raw == "hotel_demo":
            session["state"] = "hotel_welcome"
            session["cart"] = {}
            await send_buttons(
                phone,
                "🏨 *Welcome to Chennai Hotel!* 🍽️\n\nTap below to explore our menu and place your order.",
                [
                    {"id": "hotel_view_menu",   "title": "👉 View Menu"},
                    {"id": "hotel_bulk_order",  "title": "📦 Bulk Order"},
                ]
            )
            return
        if effective_raw == "turf_demo":
            session["state"] = "turf_date"
            await send_text(phone, "⚽ *Welcome to Hatobot Turf Booking!*\n\nFirst, select your preferred *date* 📅")
            await send_list(
                phone,
                "Choose a date for your turf booking:",
                "📅 Select Date",
                [{"title": "Available Dates", "rows": get_next_7_days()}]
            )
            return

    # ════════════════════════════
    # INIT STATE
    # ════════════════════════════
    if state == "init":
        hint = ai_assist(text)
        if hint == "greet" or text in ("hi hatobot",):
            await send_main_menu(phone, session)
        elif hint == "hotel":
            session["state"] = "hotel_welcome"
            session["cart"] = {}
            await send_buttons(
                phone,
                "🏨 *Welcome to Chennai Hotel!* 🍽️\n\nTap below to explore our menu and place your order.",
                [
                    {"id": "hotel_view_menu",  "title": "👉 View Menu"},
                    {"id": "hotel_bulk_order", "title": "📦 Bulk Order"},
                ]
            )
        elif hint == "turf":
            session["state"] = "turf_date"
            await send_text(phone, "⚽ *Welcome to Hatobot Turf Booking!*\n\nFirst, select your preferred *date* 📅")
            await send_list(phone, "Choose a date:", "📅 Select Date", [{"title": "Available Dates", "rows": get_next_7_days()}])
        else:
            await send_main_menu(phone, session)
        return

    # ════════════════════════════
    # MAIN MENU STATE
    # ════════════════════════════
    if state == "main_menu":
        hint = ai_assist(text)
        if hint == "hotel":
            raw = "hotel_demo"
        elif hint == "turf":
            raw = "turf_demo"
        elif hint in ("greet", "help"):
            await send_buttons(
                phone,
                "I can help you 😊\n\nTry one of these:",
                [
                    {"id": "hotel_demo",  "title": "🏨 Hotel Demo"},
                    {"id": "turf_demo",   "title": "⚽ Turf Demo"},
                    {"id": "get_started", "title": "🚀 Get Started"},
                ]
            )
            return

        if raw == "hotel_demo":
            session["state"] = "hotel_welcome"
            session["cart"] = {}
            await send_buttons(
                phone,
                "🏨 *Welcome to Chennai Hotel!* 🍽️\n\nTap below to explore our menu and place your order.",
                [
                    {"id": "hotel_view_menu",  "title": "👉 View Menu"},
                    {"id": "hotel_bulk_order", "title": "📦 Bulk Order"},
                ]
            )
        elif raw == "turf_demo":
            session["state"] = "turf_date"
            await send_text(phone, "⚽ *Welcome to Hatobot Turf Booking!*\n\nFirst, select your preferred *date* 📅")
            await send_list(phone, "Choose a date:", "📅 Select Date", [{"title": "Available Dates", "rows": get_next_7_days()}])
        elif raw == "get_started":
            session["state"] = "gs_name"
            await send_text(phone, "🚀 *Let's get you started with HatoBot!*\n\nWhat is your *name*? 👤")
        else:
            await send_buttons(
                phone,
                "I can help you 😊\n\nChoose what to explore:",
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

    # HOTEL: Welcome — show View Menu + Bulk Order buttons
    if state == "hotel_welcome":
        if raw == "hotel_view_menu":
            session["state"] = "hotel_menu"
            cart_url = f"{CART_BASE_URL}/cart?phone={phone}"
            await send_cta_url(
                phone,
                "🍽️ *Browse our menu and build your order!*\n\nTap to open the menu cart 👇",
                "🛒 Open Menu",
                cart_url
            )
        elif raw == "hotel_bulk_order":
            await send_text(
                phone,
                "📦 *Bulk Order — Chennai Hotel*\n\n"
                "For bulk orders, catering, or large group orders, please contact us directly:\n\n"
                "📞 *Phone/WhatsApp:* +91 98848 99024\n"
                "🕐 *Hours:* 8:00 AM – 10:00 PM\n\n"
                "Our team will get back to you within minutes! 🙏"
            )
            reset_session(phone)
            await send_return_cta(phone)
        else:
            await send_buttons(
                phone,
                "🏨 *Welcome to Chennai Hotel!* 🍽️\n\nTap below to explore our menu and place your order.",
                [
                    {"id": "hotel_view_menu",  "title": "👉 View Menu"},
                    {"id": "hotel_bulk_order", "title": "📦 Bulk Order"},
                ]
            )
        return

    # HOTEL: Select item from WhatsApp list
    if state == "hotel_menu":
        # Handle order coming from web app (via text "ORDER:...")
        if text.startswith("order:"):
            # Web app sends: "ORDER:1x2,3x1,7x3" (item_id x qty)
            try:
                pairs = text.replace("order:", "").split(",")
                cart = {}
                for pair in pairs:
                    parts = pair.strip().split("x")
                    if len(parts) == 2:
                        item_id, qty = parts[0].strip(), int(parts[1].strip())
                        if item_id in MENU_ITEM_MAP and qty > 0:
                            cart[item_id] = cart.get(item_id, 0) + qty
                if cart:
                    session["cart"] = cart
                    session["state"] = "hotel_order_type"
                    summary = build_order_summary(cart)
                    total = cart_total(cart)
                    await send_text(phone, f"{summary}\n\n──────────────")
                    await send_buttons(
                        phone,
                        "Please choose your order type:",
                        [
                            {"id": "hotel_dine_in",  "title": "🍽️ Dine-in"},
                            {"id": "hotel_takeaway", "title": "🥡 Takeaway"},
                        ]
                    )
                    return
            except Exception as e:
                print(f"[HOTEL WEB ORDER PARSE ERROR] {e}")

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
            await send_list(phone, "Please select an item from our menu:", "📋 View Menu", build_menu_sections())
        return

    # HOTEL: Enter quantity (WhatsApp list flow)
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
            item = MENU_ITEM_MAP.get(session["data"].get("pending_item", ""))
            name = item["name"] if item else "the item"
            await send_text(phone, f"Please type a valid *number* for *{name}* 👆\n_(e.g. 1, 2, 3)_")
        return

    # HOTEL: Cart — add more or place order
    if state == "hotel_cart":
        if raw == "hotel_add_more":
            session["state"] = "hotel_menu"
            await send_list(phone, "Select another item to add 🍛", "📋 View Menu", build_menu_sections())
        elif raw == "hotel_place_order":
            cart = session["cart"]
            if not cart:
                await send_text(phone, "🛒 Your cart is empty! Please add items first.")
                session["state"] = "hotel_menu"
                await send_list(phone, "Select an item:", "📋 View Menu", build_menu_sections())
                return
            session["state"] = "hotel_order_type"
            summary = build_order_summary(cart)
            await send_text(phone, f"{summary}\n\n──────────────")
            await send_buttons(
                phone,
                "Please choose your order type:",
                [
                    {"id": "hotel_dine_in",  "title": "🍽️ Dine-in"},
                    {"id": "hotel_takeaway", "title": "🥡 Takeaway"},
                ]
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

    # HOTEL: Order Type (Dine-in / Takeaway)
    if state == "hotel_order_type":
        if raw in ("hotel_dine_in", "hotel_takeaway"):
            order_type = "Dine-in 🍽️" if raw == "hotel_dine_in" else "Takeaway 🥡"
            session["data"]["order_type"] = order_type
            session["state"] = "hotel_billing"
            cart = session["cart"]
            total = cart_total(cart)
            await send_buttons(
                phone,
                f"🧾 *Bill Summary*\n\n"
                f"Order Type: {order_type}\n"
                f"Items Total: ₹{total}\n"
                f"Discount: ₹0\n"
                f"──────────────\n"
                f"💰 *Final Price: ₹{total}*\n\n"
                f"How would you like to pay?",
                [
                    {"id": "hotel_pay_now",     "title": "💳 Pay Now"},
                    {"id": "hotel_pay_counter", "title": "🏪 Pay at Counter"},
                ]
            )
        else:
            await send_buttons(
                phone,
                "Please choose your order type:",
                [
                    {"id": "hotel_dine_in",  "title": "🍽️ Dine-in"},
                    {"id": "hotel_takeaway", "title": "🥡 Takeaway"},
                ]
            )
        return

    # HOTEL: Billing → Payment
    if state == "hotel_billing":
        cart = session["cart"]
        total = cart_total(cart)
        order_type = session["data"].get("order_type", "")
        if raw == "hotel_pay_now":
            await send_text(
                phone,
                f"✅ *Payment Successful!*\n"
                f"Your order is confirmed 🎉\n\n"
                f"📋 Order will appear in dashboard and our team will prepare it right away!\n"
                f"🙏 Thank you for ordering with *Chennai Hotel!*"
            )
            details = f"Order Type: {order_type} | Total: ₹{total}"
            await notify_demo_complete(phone, "🏨 Hotel Demo", details)
            reset_session(phone)
            await send_return_cta(phone)
        elif raw == "hotel_pay_counter":
            await send_text(
                phone,
                f"✅ *Order Confirmed!*\n"
                f"Please pay ₹{total} at the counter.\n\n"
                f"🙏 Thank you for ordering with *Chennai Hotel!*"
            )
            details = f"Order Type: {order_type} | Total: ₹{total} | Pay at Counter"
            await notify_demo_complete(phone, "🏨 Hotel Demo", details)
            reset_session(phone)
            await send_return_cta(phone)
        else:
            await send_buttons(
                phone,
                f"💰 *Total: ₹{total}*\n\nHow would you like to pay?",
                [
                    {"id": "hotel_pay_now",     "title": "💳 Pay Now"},
                    {"id": "hotel_pay_counter", "title": "🏪 Pay at Counter"},
                ]
            )
        return

    # ════════════════════════════════════════
    # TURF FLOW
    # ════════════════════════════════════════

    # TURF: Date selection
    if state == "turf_date":
        if btn_id.startswith("date_"):
            date_val   = btn_id.replace("date_", "")
            date_label = interactive_title or date_val
            session["data"]["date"]       = date_val
            session["data"]["date_label"] = date_label
            session["turf_slots"]         = []
            session["state"]              = "turf_slot"
            
            await send_list(
                phone,
                f"📅 *Date:* {date_label}\n\nNow choose your *time slot:*",
                "⏰ Select Slot",
                build_slot_sections(date_label, session.get("turf_slots", []))
            )
        else:
            await send_list(
                phone,
                "Please select a date for your booking:",
                "📅 Select Date",
                [{"title": "Available Dates", "rows": get_next_7_days()}]
            )
        return


    # TURF: Slot selection
    if state == "turf_slot":
        if btn_id.startswith("slot_"):
            slot_index = int(btn_id.replace("slot_", ""))
            slot = TURF_SLOTS[slot_index] if slot_index < len(TURF_SLOTS) else None
            if slot:
                date_label = session["data"].get("date_label", "Selected Date")
                if slot not in session["turf_slots"]:
                    session["turf_slots"].append(slot)
                
                session["state"] = "turf_review"
                slots_so_far = "\n".join(f"• {s}" for s in session["turf_slots"])
                await send_buttons(
                    phone,
                    f"✅ *Slot Added!*\n\n📅 Date: {date_label}\n⏰ Selected:\n{slots_so_far}\n\nWhat would you like to do?",
                    [
                        {"id": "turf_confirm_booking", "title": "✅ Confirm Booking"},
                        {"id": "turf_add_slot",        "title": "➕ Add Slot"},
                        {"id": "turf_remove_slot",     "title": "❌ Remove Slot"},
                    ]
                )
        else:
            date_label = session["data"].get("date_label", "Selected Date")
            await send_list(
                phone,
                "Please select a time slot:",
                "⏰ Select Slot",
                build_slot_sections(date_label, session.get("turf_slots", []))
            )
        return

    # TURF: Review selection
    if state == "turf_review":
        if raw == "turf_confirm_booking":
            session["state"] = "turf_payment"
            date_label = session["data"].get("date_label", "")
            slots = session["turf_slots"]
            summary = build_turf_summary(slots, date_label)
            await send_buttons(
                phone,
                f"{summary}\n\nChoose payment method:",
                [
                    {"id": "turf_pay_now",     "title": "💳 Pay Now"},
                    {"id": "turf_pay_counter", "title": "🏪 Pay at Counter"},
                ]
            )
        elif raw == "turf_add_slot":
            session["state"] = "turf_slot"
            date_label = session["data"].get("date_label", "Selected Date")
            await send_list(
                phone,
                f"📅 {date_label} — Select another time slot:",
                "⏰ Select Slot",
                build_slot_sections(date_label, session.get("turf_slots", []))
            )
        elif raw == "turf_remove_slot":
            if not session["turf_slots"]:
                await send_text(phone, "No slots to remove.")
                return
            
            session["state"] = "turf_remove_list"
            rows = [{"id": f"rem_{i}", "title": s, "description": "❌ Click to remove"} for i, s in enumerate(session["turf_slots"])]
            await send_list(
                phone,
                "Select a slot to *remove*:",
                "❌ Remove Slot",
                [{"title": "Selected Slots", "rows": rows}]
            )
        return

    # TURF: Edit options
    if state == "turf_edit":
        if raw == "turf_add_slot":
            session["state"] = "turf_slot"
            date_label = session["data"].get("date_label", "Selected Date")
            await send_list(
                phone,
                f"📅 {date_label} — Select another time slot:",
                "⏰ Select Slot",
                build_slot_sections(date_label, session.get("turf_slots", []))
            )
        elif raw == "turf_remove_slot":
            if not session["turf_slots"]:
                await send_text(phone, "No slots to remove.")
                session["state"] = "turf_review"
                # (Re-send review buttons)
                return
            
            session["state"] = "turf_remove_list"
            rows = [{"id": f"rem_{i}", "title": s, "description": "❌ Click to remove"} for i, s in enumerate(session["turf_slots"])]
            await send_list(
                phone,
                "Select a slot to *remove*:",
                "❌ Remove Slot",
                [{"title": "Selected Slots", "rows": rows}]
            )
        elif raw == "turf_back_review":
            session["state"] = "turf_review"
            slots_so_far = "\n".join(f"• {s}" for s in session["turf_slots"])
            await send_buttons(
                phone,
                f"⏰ *Booking Review*\n\nSlots:\n{slots_so_far}\n\nWhat would you like to do?",
                [
                    {"id": "turf_confirm_booking", "title": "✅ Confirm Booking"},
                    {"id": "turf_edit_booking", "title": "✏️ Edit Booking"},
                ]
            )
        return

    # TURF: Remove slot action
    if state == "turf_remove_list":
        if btn_id.startswith("rem_"):
            idx = int(btn_id.replace("rem_", ""))
            if 0 <= idx < len(session["turf_slots"]):
                removed = session["turf_slots"].pop(idx)
                await send_text(phone, f"✅ Removed: {removed}")
            
            session["state"] = "turf_review"
            slots_so_far = "\n".join(f"• {s}" for s in session["turf_slots"]) if session["turf_slots"] else "No slots selected."
            await send_buttons(
                phone,
                f"⏰ *Booking Review*\n\nSlots:\n{slots_so_far}\n\nWhat would you like to do?",
                [
                    {"id": "turf_confirm_booking", "title": "✅ Confirm Booking"} if session["turf_slots"] else {"id": "turf_add_slot", "title": "➕ Add Slot"},
                    {"id": "turf_edit_booking", "title": "✏️ Edit Booking"},
                ]
            )
        else:
            session["state"] = "turf_edit"
            # (Re-send edit buttons)
        return

    # TURF: Payment
    if state == "turf_payment":
        date_label = session["data"].get("date_label", "")
        slots = session["turf_slots"]
        if raw == "turf_pay_now":
            slots_str = ", ".join(slots)
            await send_text(
                phone,
                f"✅ *Payment Successful!*\n"
                f"Booking confirmed 🎉\n\n"
                f"📅 Date: {date_label}\n"
                f"⏰ Slots: {slots_str}\n"
                f"💰 Paid: ₹0 (Demo Offer)\n\n"
                f"📋 Your booking will appear in the dashboard automatically!\n"
                f"🏆 Thank you for booking with *Hatobot Turf!*"
            )
            await notify_demo_complete(phone, "⚽ Turf Demo", f"Date: {date_label} | Slots: {slots_str}")
            reset_session(phone)
            await send_return_cta(phone)
        elif raw == "turf_pay_counter":
            slots_str = ", ".join(slots)
            await send_text(
                phone,
                f"✅ *Booking Confirmed!*\n"
                f"Pay at venue.\n\n"
                f"📅 Date: {date_label}\n"
                f"⏰ Slots: {slots_str}\n\n"
                f"🏆 See you on the turf! *Hatobot Turf!*"
            )
            await notify_demo_complete(phone, "⚽ Turf Demo", f"Date: {date_label} | Slots: {slots_str} | Pay at venue")
            reset_session(phone)
            await send_return_cta(phone)
        else:
            summary = build_turf_summary(slots, date_label)
            await send_buttons(
                phone,
                f"{summary}\n\nChoose payment method:",
                [
                    {"id": "turf_pay_now",     "title": "💳 Pay Now"},
                    {"id": "turf_pay_counter", "title": "🏪 Pay at Counter"},
                ]
            )
        return

    # ════════════════════════════════════════
    # GET STARTED FLOW
    # ════════════════════════════════════════

    if state == "gs_name":
        if msg_body and msg_body.strip():
            name = msg_body.strip()
            session["data"]["name"] = name
            session["state"] = "gs_business"
            await send_list(
                phone,
                f"Nice to meet you, *{name}!* 😊\n\nWhat type of business would you like to automate with WhatsApp?",
                "💼 Select Business",
                [{
                    "title": "Business Types",
                    "rows": [
                        {"id": "biz_clinic",  "title": "🏥 Clinic",  "description": "Appointments & patient management"},
                        {"id": "biz_saloon",  "title": "✂️ Saloon",  "description": "Booking & customer management"},
                        {"id": "biz_hotel",   "title": "🏨 Hotel",   "description": "Menu, orders & table management"},
                        {"id": "biz_turf",    "title": "⚽ Turf",    "description": "Slot booking & payments"},
                        {"id": "biz_other",   "title": "💼 Other",   "description": "Tell us about your business"},
                    ]
                }]
            )
        else:
            await send_text(phone, "Please tell us your *name* to continue 👤")
        return

    if state == "gs_business":
        name = session["data"].get("name", "there")
        business_map = {
            "biz_clinic": "Clinic 🏥",
            "biz_saloon": "Saloon ✂️",
            "biz_hotel":  "Hotel 🏨",
            "biz_turf":   "Turf ⚽",
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
                [{
                    "title": "Business Types",
                    "rows": [
                        {"id": "biz_clinic",  "title": "🏥 Clinic",  "description": "Appointments & patient management"},
                        {"id": "biz_saloon",  "title": "✂️ Saloon",  "description": "Booking & customer management"},
                        {"id": "biz_hotel",   "title": "🏨 Hotel",   "description": "Menu, orders & table management"},
                        {"id": "biz_turf",    "title": "⚽ Turf",    "description": "Slot booking & payments"},
                        {"id": "biz_other",   "title": "💼 Other",   "description": "Tell us about your business"},
                    ]
                }]
            )
        return

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
    hint = ai_assist(text)
    if hint == "hotel":
        raw = "hotel_demo"
        session["state"] = "main_menu"
        await handle_incoming(phone, msg_type, msg_body, "hotel_demo", "")
        return
    elif hint == "turf":
        session["state"] = "main_menu"
        await handle_incoming(phone, msg_type, msg_body, "turf_demo", "")
        return
    elif hint in ("greet", "help"):
        reset_session(phone)
        await send_main_menu(phone, get_session(phone))
        return

    reset_session(phone)
    await send_buttons(
        phone,
        "I can help you 😊\n\nTry:",
        [
            {"id": "hotel_demo",  "title": "🏨 Hotel Demo"},
            {"id": "turf_demo",   "title": "⚽ Turf Demo"},
            {"id": "get_started", "title": "🚀 Get Started"},
        ]
    )


# ════════════════════════════════════════
# TIMEOUT CHECKER (call periodically via scheduler)
# ════════════════════════════════════════

async def check_timeouts():
    """Send nudge if user inactive for 2 hours, then reset."""
    threshold = timedelta(hours=2)
    now = datetime.utcnow()
    for phone, session in list(sessions.items()):
        if session["state"] == "init":
            continue
        elapsed = now - session.get("last_seen", now)
        if elapsed >= threshold:
            print(f"[TIMEOUT] Resetting {phone}")
            await send_buttons(
                phone,
                "Still there? 😊\nNeed help with something?",
                [
                    {"id": "hotel_demo",  "title": "🏨 Hotel Demo"},
                    {"id": "turf_demo",   "title": "⚽ Turf Demo"},
                    {"id": "get_started", "title": "🚀 Get Started"},
                ]
            )
            reset_session(phone)


# ════════════════════════════════════════
# WEBHOOK ROUTES
# ════════════════════════════════════════

@app.get("/webhook")
async def verify_webhook(request: Request):
    params    = dict(request.query_params)
    mode      = params.get("hub.mode")
    token     = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("[WEBHOOK] Verified successfully.")
        return PlainTextResponse(challenge)
    return PlainTextResponse("Forbidden", status_code=403)


@app.post("/webhook")
async def receive_webhook(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"status": "invalid json"}, status_code=400)

    print(f"[WEBHOOK IN] {json.dumps(body, indent=2)}")

    try:
        entry   = body["entry"][0]
        changes = entry["changes"][0]
        value   = changes["value"]

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


@app.get("/cart")
async def serve_cart():
    """Serve the HTML menu cart page for WhatsApp webview."""
    cart_path = os.path.join(os.path.dirname(__file__), "cart.html")
    return FileResponse(cart_path, media_type="text/html")


@app.get("/health")
async def health():
    return {
        "status": "running",
        "active_sessions": len(sessions),
        "timestamp": datetime.utcnow().isoformat()
    }


# Optional: call check_timeouts() via APScheduler or a background task
# Example with APScheduler:
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# scheduler = AsyncIOScheduler()
# scheduler.add_job(check_timeouts, "interval", minutes=30)
# scheduler.start()
