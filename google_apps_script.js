/**
 * HatoBot — Google Apps Script
 * Paste this in both the Student Form and Teacher Form's Apps Script editor.
 * Tools → Script editor → paste → save → set trigger:
 *   "onFormSubmit" → From spreadsheet → On form submit
 *
 * For the STUDENT form set IS_TEACHER = false
 * For the TEACHER form set IS_TEACHER = true
 */

var BOT_URL      = "https://your-bot.vercel.app";   // ← your FastAPI Vercel URL
var ADMIN_SECRET = "hatobot_admin_secret";           // ← must match bot .env ADMIN_SECRET
var IS_TEACHER   = false;                            // ← set true for teacher form

// ── Column name mapping ───────────────────────────────────────────────────────
// Change keys to match EXACT question text in your Google Form
var STUDENT_MAP = {
  roll_number     : "Roll Number",
  full_name       : "Full Name",
  dob             : "Date of Birth",
  gender          : "Gender",
  blood_group     : "Blood Group",
  department      : "Department",
  batch           : "Batch",
  section         : "Section",
  current_sem     : "Current Semester",
  whatsapp_number : "WhatsApp Number",
  phone_number    : "Phone Number",
  email           : "Email Address",
  hostel          : "Hostel (Yes/No)",
};

var TEACHER_MAP = {
  emp_id          : "Employee ID",
  full_name       : "Full Name",
  whatsapp_number : "WhatsApp Number",
};

// ── Supabase config ───────────────────────────────────────────────────────────
var SUPABASE_URL = "https://your-project.supabase.co";
var SUPABASE_KEY = "your_supabase_service_role_key";

function onFormSubmit(e) {
  try {
    var responses = e.namedValues;  // { "Question": ["Answer"] }
    
    if (IS_TEACHER) {
      handleTeacher(responses);
    } else {
      handleStudent(responses);
    }
  } catch (err) {
    Logger.log("Error: " + err.toString());
  }
}

function handleStudent(responses) {
  var data = {};
  for (var key in STUDENT_MAP) {
    var questionText = STUDENT_MAP[key];
    var val = responses[questionText];
    data[key] = val ? val[0].trim() : "";
  }

  // Normalize WhatsApp number: strip spaces/dashes, ensure 91 prefix
  data.whatsapp_number = normalizePhone(data.whatsapp_number);

  // Insert into Supabase students table
  var result = supabaseUpsert("students", data, "whatsapp_number");
  Logger.log("Supabase student upsert: " + JSON.stringify(result));

  // Notify student via bot
  if (data.whatsapp_number) {
    notifyBot("/notify/student-registered", {
      whatsapp_number: data.whatsapp_number,
      full_name: data.full_name,
    });
  }
}

function handleTeacher(responses) {
  var data = {};
  for (var key in TEACHER_MAP) {
    var questionText = TEACHER_MAP[key];
    var val = responses[questionText];
    data[key] = val ? val[0].trim() : "";
  }

  data.whatsapp_number = normalizePhone(data.whatsapp_number);
  data.approved = false;

  // Insert into Supabase teachers table
  var result = supabaseUpsert("teachers", data, "whatsapp_number");
  Logger.log("Supabase teacher upsert: " + JSON.stringify(result));

  // Notify teacher via bot
  if (data.whatsapp_number) {
    notifyBot("/notify/teacher-registered", {
      whatsapp_number: data.whatsapp_number,
      full_name: data.full_name,
    });
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function normalizePhone(raw) {
  if (!raw) return "";
  var digits = raw.replace(/\D/g, "");
  // If 10 digits, prepend 91 (India)
  if (digits.length === 10) digits = "91" + digits;
  return digits;
}

function supabaseUpsert(table, data, conflictCol) {
  var url = SUPABASE_URL + "/rest/v1/" + table + "?on_conflict=" + conflictCol;
  var options = {
    method: "POST",
    headers: {
      "Content-Type":  "application/json",
      "apikey":        SUPABASE_KEY,
      "Authorization": "Bearer " + SUPABASE_KEY,
      "Prefer":        "resolution=merge-duplicates",
    },
    payload: JSON.stringify(data),
    muteHttpExceptions: true,
  };
  var response = UrlFetchApp.fetch(url, options);
  return response.getContentText();
}

function notifyBot(path, body) {
  var url = BOT_URL + path;
  var options = {
    method: "POST",
    headers: {
      "Content-Type":   "application/json",
      "x-admin-secret": ADMIN_SECRET,
    },
    payload: JSON.stringify(body),
    muteHttpExceptions: true,
  };
  var response = UrlFetchApp.fetch(url, options);
  Logger.log("Bot notify " + path + ": " + response.getContentText());
}
