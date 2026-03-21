# 🚀 HATOBOT DEPLOYMENT GUIDE - VERCEL

## ✅ PRE-DEPLOYMENT CHECKLIST

- [ ] Git repository initialized and committed
- [ ] Vercel account created (https://vercel.com)
- [ ] WhatsApp Business API credentials ready
- [ ] Supabase project created and tables initialized
- [ ] All environment variables prepared

## 📂 DEPLOYMENT STRUCTURE

```
hatobot/
├── api/                     # Python FastAPI serverless functions
│   ├── index.py            # Main app entry point for Vercel
│   └── requirements.txt     # Python dependencies
├── admin/                   # React frontend (Vite build)
│   ├── src/
│   ├── package.json
│   ├── vite.config.js
│   └── dist/               # Built frontend (auto-generated)
├── package.json            # Root package (for build orchestration)
├── vercel.json            # Vercel configuration
├── .env.example           # Environment variables template
└── supabase_schema.sql    # Database schema
```

## 🎯 DEPLOYMENT ROUTES

After deployment, your app will be available at: `https://YOUR-PROJECT.vercel.app/`

### Routes:
- **Frontend**: `https://YOUR-PROJECT.vercel.app/` → React Admin Panel
- **WhatsApp Webhook**: `https://YOUR-PROJECT.vercel.app/webhook` → POST/GET for messages
- **Student Notifications**: `https://YOUR-PROJECT.vercel.app/notify/student-registered` → POST
- **Teacher Notifications**: 
  - `https://YOUR-PROJECT.vercel.app/notify/teacher-registered` → POST
  - `https://YOUR-PROJECT.vercel.app/notify/teacher-approved` → POST
- **Health Check**: `https://YOUR-PROJECT.vercel.app/health` → GET

## 🔐 ENVIRONMENT VARIABLES TO SET IN VERCEL

```
SUPABASE_URL = https://nhhkjwzxqeovyzcimmdf.supabase.co
SUPABASE_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
ACCESS_TOKEN = YOUR_WHATSAPP_ACCESS_TOKEN
PHONE_NUMBER_ID = YOUR_PHONE_NUMBER_ID
VERIFY_TOKEN = ANY_CUSTOM_STRING
ADMIN_SECRET = hatobot_admin_secret
```

## 📝 LOGIN CREDENTIALS FOR ADMIN PANEL

**Username**: jpr-college
**Password**: jpr-college-password

## 🌐 WHATSAPP WEBHOOK CONFIGURATION

After deploying to Vercel:
1. Go to Facebook Developers Dashboard
2. WhatsApp > Configuration
3. Set Webhook URL: `https://YOUR-PROJECT.vercel.app/webhook`
4. Set Verify Token: (same as VERIFY_TOKEN env var)
5. Subscribe to: messages, message_status

## 💡 NOTES

- Frontend builds to `admin/dist/` during Vercel deployment
- Python serverless functions run in `api/` directory
- All routes are handled by vercel.json routing rules
- SPA fallback routes all non-API requests to React index.html
