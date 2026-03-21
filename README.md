# HatoBot V5 — JPR College

WhatsApp bot for attendance management + React admin panel, powered by FastAPI + Supabase.

## Repo Structure
```
hatobot/
├── bot/                    → FastAPI WhatsApp bot
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
├── admin/                  → React admin panel (Vite)
│   ├── src/
│   └── .env.example
├── supabase_schema.sql     → Run once in Supabase SQL editor
├── google_apps_script.js   → Paste in both Google Forms
└── README.md
```

## Setup Steps

### 1. Supabase
- Go to Supabase → SQL Editor
- Run `supabase_schema.sql` (creates students, teachers, attendance tables)

### 2. Bot (Vercel)
- Deploy `bot/` to Vercel as a Python project
- Set environment variables in Vercel dashboard:
  - `ACCESS_TOKEN`
  - `PHONE_NUMBER_ID`
  - `VERIFY_TOKEN`
  - `SUPABASE_URL`
  - `SUPABASE_KEY` (service_role key)
  - `ADMIN_SECRET`

### 3. Admin Panel (Vercel)
- Deploy `admin/` to Vercel as a Vite/React project
- Set environment variables:
  - `VITE_SUPABASE_URL`
  - `VITE_SUPABASE_ANON_KEY` (anon key is fine here)
  - `VITE_BOT_URL` (your bot's Vercel URL)
  - `VITE_ADMIN_SECRET` (same as bot's ADMIN_SECRET)

### 4. Google Forms (Apps Script)
- Open each Google Form → Responses sheet → Extensions → Apps Script
- Paste `google_apps_script.js`
- Set `IS_TEACHER = false` for student form, `true` for teacher form
- Fill in `BOT_URL`, `ADMIN_SECRET`, `SUPABASE_URL`, `SUPABASE_KEY`
- Add trigger: onFormSubmit → From spreadsheet → On form submit

### 5. Meta Webhook
- Set webhook URL: `https://your-bot.vercel.app/webhook`
- Verify token: value of `VERIFY_TOKEN`

## Admin Login
- Username: `jpr-college`
- Password: `jpr-college-password`

## Notification Flow
```
Student submits form
  → Apps Script → Supabase insert + POST /notify/student-registered
  → Bot sends WhatsApp: "You are registered as a student."

Teacher submits form
  → Apps Script → Supabase insert + POST /notify/teacher-registered
  → Bot sends WhatsApp: "Please wait for admin approval."

Admin approves teacher (admin panel)
  → Supabase update approved=true + POST /notify/teacher-approved
  → Bot sends WhatsApp: "Welcome! Press Take Attendance to get started."
```
