import os
import re
import logging
import requests
from fastapi import FastAPI, Request, Query, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
ACCESS_TOKEN    = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN    = os.getenv("VERIFY_TOKEN")
SUPABASE_URL    = os.getenv("SUPABASE_URL")
SUPABASE_KEY    = os.getenv("SUPABASE_KEY")
ADMIN_SECRET    = os.getenv("ADMIN_SECRET", "hatobot_admin_secret")
GRAPH_API_URL   = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

STUDENT_FORM = "https://docs.google.com/forms/d/e/1FAIpQLSc1O6deE3KDYe_RerIbZ0h06zd5b18EZXw1T4CBC2xB3oaMYQ/viewform?usp=sharing"
TEACHER_FORM = "https://docs.google.com/forms/d/e/1FAIpQLSdoLYODlH4uSMIqVALIDjze6AB3Amv6fW7jm2fIW0NXy6qmlw/viewform?usp=sharing"

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ── Supabase ──────────────────────────────────────────────────────────────────
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── In-memory session store ───────────────────────────────────────────────────
user_sessions: dict[str, dict] = {}

# ── Constants ─────────────────────────────────────────────────────────────────
SECTIONS   = [f"Section {c}" for c in "ABCDEFGHIJK"]
DAY_ORDERS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

TIMETABLES = {
    "Monday":    "📅 *Monday Timetable*\n\n🕗 08:00–08:50 → Period 1\n🕗 08:50–09:40 → Period 2\n🕗 09:40–10:30 → Period 3\n☕ 10:30–10:45 → Break\n🕗 10:45–11:35 → Period 4\n🕗 11:35–12:25 → Period 5\n🍽️ 12:25–01:15 → Lunch\n🕗 01:15–02:05 → Period 6\n🕗 02:05–02:55 → Period 7\n🕗 02:55–03:45 → Period 8",
    "Tuesday":   "📅 *Tuesday Timetable*\n\n🕗 08:00–08:50 → Period 1\n🕗 08:50–09:40 → Period 2\n🕗 09:40–10:30 → Period 3\n☕ 10:30–10:45 → Break\n🕗 10:45–11:35 → Period 4\n🕗 11:35–12:25 → Period 5\n🍽️ 12:25–01:15 → Lunch\n🕗 01:15–02:05 → Period 6\n🕗 02:05–02:55 → Period 7\n🕗 02:55–03:45 → Period 8",
    "Wednesday": "📅 *Wednesday Timetable*\n\n🕗 08:00–08:50 → Period 1\n🕗 08:50–09:40 → Period 2\n🕗 09:40–10:30 → Period 3\n☕ 10:30–10:45 → Break\n🕗 10:45–11:35 → Period 4\n🕗 11:35–12:25 → Period 5\n🍽️ 12:25–01:15 → Lunch\n🕗 01:15–02:05 → Period 6\n🕗 02:05–02:55 → Period 7\n🕗 02:55–03:45 → Period 8",
    "Thursday":  "📅 *Thursday Timetable*\n\n🕗 08:00–08:50 → Period 1\n🕗 08:50–09:40 → Period 2\n🕗 09:40–10:30 → Period 3\n☕ 10:30–10:45 → Break\n🕗 10:45–11:35 → Period 4\n🕗 11:35–12:25 → Period 5\n🍽️ 12:25–01:15 → Lunch\n🕗 01:15–02:05 → Period 6\n🕗 02:05–02:55 → Period 7\n🕗 02:55–03:45 → Period 8",
    "Friday":    "📅 *Friday Timetable*\n\n🕗 08:00–08:50 → Period 1\n🕗 08:50–09:40 → Period 2\n🕗 09:40–10:30 → Period 3\n☕ 10:30–10:45 → Break\n🕗 10:45–11:35 → Period 4\n🕗 11:35–12:25 → Period 5\n🍽️ 12:25–01:15 → Lunch\n🕗 01:15–02:05 → Period 6\n🕗 02:05–02:55 → Period 7\n🕗 02:55–03:45 → Period 8",
}

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="HatoBot", version="5.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── WhatsApp helpers ──────────────────────────────────────────────────────────

def _post(payload: dict) -> None:
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    r = requests.post(GRAPH_API_URL, json=payload, headers=headers, timeout=10)
    if not r.ok:
        logger.error("WA send failed → %s | %s", payload.get("to"), r.text)


def send_text(to: str, body: str) -> None:
    _post({"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": body}})


def send_buttons(to: str, body: str, buttons: list) -> None:
    for chunk in [buttons[i:i+3] for i in range(0, len(buttons), 3)]:
        _post({
            "messaging_product": "whatsapp", "to": to, "type": "interactive",
            "interactive": {
                "type": "button", "body": {"text": body},
                "action": {"buttons": [
                    {"type": "reply", "reply": {"id": f"btn_{o.lower().replace(' ','_')}", "title": o[:20]}}
                    for o in chunk
                ]},
            },
        })


def send_list(to: str, body: str, btn_label: str, options: list, section: str = "Options") -> None:
    _post({
        "messaging_product": "whatsapp", "to": to, "type": "interactive",
        "interactive": {
            "type": "list", "body": {"text": body},
            "action": {
                "button": btn_label,
                "sections": [{"title": section, "rows": [
                    {"id": f"list_{o.lower().replace(' ','_').replace('/','_').replace('&','and')}", "title": o[:24]}
                    for o in options
                ]}],
            },
        },
    })

# ── Supabase helpers ──────────────────────────────────────────────────────────

def get_student(phone: str) -> dict | None:
    try:
        r = supabase.table("students").select("*").eq("whatsapp_number", phone).limit(1).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        logger.error("DB get_student: %s", e)
        return None


def get_teacher(phone: str) -> dict | None:
    try:
        r = supabase.table("teachers").select("*").eq("whatsapp_number", phone).limit(1).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        logger.error("DB get_teacher: %s", e)
        return None


def get_students_in_section(section: str) -> list:
    try:
        r = supabase.table("students").select("*").eq("section", section).order("roll_number").execute()
        return r.data or []
    except Exception as e:
        logger.error("DB get_students_in_section: %s", e)
        return []


def get_student_by_name_and_section(name: str, section: str) -> list:
    """Return students matching name (case-insensitive) in a section."""
    try:
        r = supabase.table("students").select("*").eq("section", section).ilike("full_name", f"%{name}%").execute()
        return r.data or []
    except Exception as e:
        logger.error("DB get_student_by_name: %s", e)
        return []


def get_student_by_roll(roll: str, section: str) -> dict | None:
    try:
        r = supabase.table("students").select("*").eq("roll_number", roll.upper()).eq("section", section).limit(1).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        logger.error("DB get_student_by_roll: %s", e)
        return None


def save_attendance(teacher_phone: str, section: str, date: str,
                    absent_ids: list[str], present_ids: list[str]) -> None:
    try:
        records = []
        for sid in absent_ids:
            records.append({"teacher_phone": teacher_phone, "section": section,
                             "date": date, "student_id": sid, "status": "absent"})
        for sid in present_ids:
            records.append({"teacher_phone": teacher_phone, "section": section,
                             "date": date, "student_id": sid, "status": "present"})
        if records:
            supabase.table("attendance").insert(records).execute()
        logger.info("Attendance saved: %s | %s | absent=%d present=%d",
                    section, date, len(absent_ids), len(present_ids))
    except Exception as e:
        logger.error("DB save_attendance: %s", e)

# ── Teacher menu ──────────────────────────────────────────────────────────────

def send_teacher_menu(phone: str) -> None:
    send_buttons(phone, "👨‍🏫 *Teacher Menu*\n\nWhat would you like to do?",
                 ["Take Attendance", "View Timetable"])

# ── TEACHER FLOW ──────────────────────────────────────────────────────────────

def handle_teacher(phone: str, text: str, reply) -> None:
    session = user_sessions[phone]
    step    = session["step"]
    data    = session.get("data", {})
    val     = (reply or text).strip()

    # ── Menu choice ───────────────────────────────────────────────────────────
    if step == "teacher_menu":
        v = val.lower()
        if "attendance" in v:
            session["step"] = "att_section"
            send_list(phone, "📋 *Take Attendance*\n\nSelect the *Section*:",
                      "Choose Section", SECTIONS, "Sections")
        elif "timetable" in v:
            session["step"] = "tt_day"
            send_list(phone, "📅 *View Timetable*\n\nSelect the day:",
                      "Choose Day", DAY_ORDERS, "Days")
        else:
            send_teacher_menu(phone)
        return

    # ── Attendance: Section ───────────────────────────────────────────────────
    if step == "att_section":
        sec = val.title()
        matched = next((s for s in SECTIONS if sec == s or val.upper() == s.split()[-1]), None)
        if not matched:
            send_list(phone, "Please select a valid *Section*:", "Choose Section", SECTIONS, "Sections")
            return
        students = get_students_in_section(matched)
        if not students:
            send_text(phone, f"⚠️ No students found in {matched}. Please check the database.")
            session["step"] = "teacher_menu"
            send_teacher_menu(phone)
            return
        data["att_section"]  = matched
        data["att_students"] = {s["id"]: s for s in students}
        data["absentees"]    = []        # list of student IDs confirmed absent
        data["pending_dup"]  = None      # name being disambiguated
        session["step"]      = "att_absentees"
        session["data"]      = data
        names = "\n".join(f"  {i+1}. {s['full_name']} ({s['roll_number']})"
                          for i, s in enumerate(students))
        send_text(phone,
            f"✅ *{matched}* — {len(students)} students enrolled\n\n"
            f"{names}\n\n"
            "📝 Enter *absentee names* separated by commas.\n"
            "Example: Rahul Kumar, Priya S\n\n"
            "If no absentees type *nil*"
        )
        return

    # ── Attendance: Absentees input ───────────────────────────────────────────
    if step == "att_absentees":
        raw = (reply or text).strip()

        # Resolving a duplicate — expecting a roll number
        if data.get("pending_dup"):
            dup_name = data["pending_dup"]
            roll     = raw.upper()
            student  = get_student_by_roll(roll, data["att_section"])
            if student:
                data["absentees"].append(student["id"])
                data["pending_dup"] = None
                send_text(phone, f"✅ *{student['full_name']}* ({roll}) marked absent.")
            else:
                send_text(phone, f"❌ Roll number *{roll}* not found in {data['att_section']}. Try again:")
                return
            # Check if more pending dups
            session["data"] = data
            _finalize_or_continue(phone, data)
            return

        if raw.lower() == "nil":
            _save_full_attendance(phone, data, [])
            return

        # Parse comma-separated names
        names = [n.strip() for n in raw.split(",") if n.strip()]
        absent_ids   = []
        need_roll_for = None

        for name in names:
            matches = get_student_by_name_and_section(name, data["att_section"])
            if len(matches) == 0:
                send_text(phone, f"⚠️ *{name}* not found in {data['att_section']}. Check spelling and try again.")
                return
            elif len(matches) > 1:
                # Duplicate name — ask for roll number
                need_roll_for = name
                roll_list = "\n".join(f"  • {m['roll_number']} — {m['full_name']}" for m in matches)
                send_text(phone,
                    f"⚠️ Multiple students named *{name}* found:\n{roll_list}\n\n"
                    f"Please enter the *roll number* for the absent student:"
                )
                data["pending_dup"]   = name
                data["absentees"]    += absent_ids
                data["pending_names"] = names[names.index(name)+1:]  # remaining
                session["data"]       = data
                session["step"]       = "att_absentees"
                return
            else:
                absent_ids.append(matches[0]["id"])

        data["absentees"] += absent_ids
        session["data"]    = data
        _save_full_attendance(phone, data, data["absentees"])
        return

    # ── Timetable day ─────────────────────────────────────────────────────────
    if step == "tt_day":
        day = val.title()
        matched = next((d for d in DAY_ORDERS if day == d or day in d), None)
        if not matched:
            send_list(phone, "Please select a valid day:", "Choose Day", DAY_ORDERS, "Days")
            return
        send_text(phone, TIMETABLES[matched])
        session["step"] = "teacher_menu"
        send_teacher_menu(phone)
        return


def _save_full_attendance(phone: str, data: dict, absent_ids: list) -> None:
    from datetime import date
    today        = date.today().isoformat()
    all_ids      = list(data["att_students"].keys())
    present_ids  = [i for i in all_ids if i not in absent_ids]
    save_attendance(phone, data["att_section"], today, absent_ids, present_ids)

    absent_names  = [data["att_students"][i]["full_name"] for i in absent_ids if i in data["att_students"]]
    total         = len(all_ids)
    absent_count  = len(absent_ids)
    present_count = total - absent_count

    summary = (
        f"✅ *Attendance Saved!*\n\n"
        f"📋 Section: {data['att_section']}\n"
        f"📅 Date: {today}\n"
        f"✅ Present: {present_count}/{total}\n"
        f"🔴 Absent: {absent_count}/{total}\n"
    )
    if absent_names:
        summary += "\n*Absentees:*\n" + "\n".join(f"  • {n}" for n in absent_names)
    else:
        summary += "\n🎉 Full attendance today!"

    send_text(phone, summary)
    user_sessions[phone]["step"] = "teacher_menu"
    user_sessions[phone]["data"] = {}
    send_teacher_menu(phone)


def _finalize_or_continue(phone: str, data: dict) -> None:
    """After resolving a dup, check if more pending names exist."""
    remaining = data.get("pending_names", [])
    if not remaining:
        _save_full_attendance(phone, data, data["absentees"])
        return
    # Process remaining names
    name = remaining[0]
    data["pending_names"] = remaining[1:]
    matches = get_student_by_name_and_section(name, data["att_section"])
    if len(matches) == 0:
        send_text(phone, f"⚠️ *{name}* not found in {data['att_section']}.")
        _finalize_or_continue(phone, data)
    elif len(matches) > 1:
        roll_list = "\n".join(f"  • {m['roll_number']} — {m['full_name']}" for m in matches)
        send_text(phone, f"⚠️ Multiple students named *{name}*:\n{roll_list}\n\nEnter the *roll number*:")
        data["pending_dup"] = name
        user_sessions[phone]["data"] = data
    else:
        data["absentees"].append(matches[0]["id"])
        user_sessions[phone]["data"] = data
        _finalize_or_continue(phone, data)

# ── MAIN DISPATCH ─────────────────────────────────────────────────────────────

def route(phone: str, text: str, reply) -> None:
    val = (reply or text).strip().lower()

    # Returning session
    if phone in user_sessions:
        step = user_sessions[phone]["step"]
        if step.startswith("teacher") or step.startswith("att") or step.startswith("tt"):
            handle_teacher(phone, text, reply)
        return

    # New message — check DB
    student = get_student(phone)
    if student:
        user_sessions[phone] = {"step": "student_done", "data": student}
        send_text(phone,
            f"👋 Hi *{student['full_name']}*!\n\n"
            "This bot is currently being used for *attendance management* only.\n\n"
            "More features are coming soon — stay tuned! 🚀\n\n"
            "For any queries, contact your department office."
        )
        return

    teacher = get_teacher(phone)
    if teacher:
        if not teacher.get("approved"):
            send_text(phone,
                "⏳ Your teacher account is *pending admin approval*.\n\n"
                "You'll receive a WhatsApp message once approved. Please wait! 🙏"
            )
            return
        user_sessions[phone] = {"step": "teacher_menu", "data": {"teacher": teacher}}
        send_text(phone, f"✅ Welcome back, *{teacher['full_name']}*! 👨‍🏫")
        send_teacher_menu(phone)
        return

    # Unknown number
    send_text(phone,
        "👋 Hello! This bot is only for registered JPR College students and teachers.\n\n"
        "Please register using the appropriate form below:\n\n"
        f"🎓 *Students:*\n{STUDENT_FORM}\n\n"
        f"👨‍🏫 *Teachers:*\n{TEACHER_FORM}\n\n"
        "Once registered, you'll be notified here on WhatsApp. ✅"
    )

# ── Webhook: verification ─────────────────────────────────────────────────────
@app.get("/webhook")
async def verify(
    hub_mode: str = Query(default=None, alias="hub.mode"),
    hub_verify_token: str = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str = Query(default=None, alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return PlainTextResponse(hub_challenge)
    return PlainTextResponse("Forbidden", status_code=403)

# ── Webhook: messages ─────────────────────────────────────────────────────────
@app.post("/webhook")
async def receive(request: Request):
    body = await request.json()
    try:
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                for msg in change.get("value", {}).get("messages", []):
                    phone    = msg["from"]
                    msg_type = msg.get("type")
                    if msg_type == "text":
                        route(phone, msg["text"]["body"].strip().lower(), None)
                    elif msg_type == "interactive":
                        itype = msg["interactive"].get("type")
                        title = (msg["interactive"].get("button_reply", {}) or
                                 msg["interactive"].get("list_reply", {})).get("title", "")
                        route(phone, title.lower(), title)
    except Exception as e:
        logger.exception("Webhook error: %s", e)
    return JSONResponse({"status": "ok"})

# ── Notification endpoints (called by Google Apps Script & Admin panel) ───────

@app.post("/notify/student-registered")
async def notify_student_registered(request: Request,
                                     x_admin_secret: str = Header(default=None)):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    body  = await request.json()
    phone = body.get("whatsapp_number")
    name  = body.get("full_name", "Student")
    if not phone:
        raise HTTPException(status_code=400, detail="whatsapp_number required")
    send_text(phone,
        f"🎓 Hi *{name}*! You are now registered as a student at JPR College.\n\n"
        "This WhatsApp bot will soon support attendance viewing and more features.\n\n"
        "Stay tuned! 🚀"
    )
    return {"status": "sent"}


@app.post("/notify/teacher-registered")
async def notify_teacher_registered(request: Request,
                                      x_admin_secret: str = Header(default=None)):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    body  = await request.json()
    phone = body.get("whatsapp_number")
    name  = body.get("full_name", "Teacher")
    if not phone:
        raise HTTPException(status_code=400, detail="whatsapp_number required")
    send_text(phone,
        f"👨‍🏫 Hi *{name}*! Your teacher registration at JPR College has been received.\n\n"
        "⏳ Please wait for *admin approval*. You'll be notified here once approved."
    )
    return {"status": "sent"}


@app.post("/notify/teacher-approved")
async def notify_teacher_approved(request: Request,
                                   x_admin_secret: str = Header(default=None)):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    body  = await request.json()
    phone = body.get("whatsapp_number")
    name  = body.get("full_name", "Teacher")
    if not phone:
        raise HTTPException(status_code=400, detail="whatsapp_number required")
    send_text(phone,
        f"✅ *Welcome, {name}!* Your teacher account has been approved. 🎉\n\n"
        "You can now use this bot to take attendance.\n\n"
        "Just message here anytime and press *'Take Attendance'* to get started! 👨‍🏫"
    )
    return {"status": "sent"}


@app.get("/health")
async def health():
    return {"status": "running", "service": "hatobot.in", "version": "5.0.0"}
