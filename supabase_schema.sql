-- ── Students ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS students (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  roll_number      TEXT UNIQUE NOT NULL,
  full_name        TEXT NOT NULL,
  dob              TEXT,
  gender           TEXT,
  blood_group      TEXT,
  department       TEXT,
  batch            TEXT,
  section          TEXT,
  current_sem      TEXT,
  whatsapp_number  TEXT UNIQUE,
  phone_number     TEXT,
  email            TEXT,
  hostel           TEXT DEFAULT 'No',
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ── Teachers ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS teachers (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  emp_id           TEXT UNIQUE NOT NULL,
  full_name        TEXT NOT NULL,
  whatsapp_number  TEXT UNIQUE,
  approved         BOOLEAN DEFAULT FALSE,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ── Attendance ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS attendance (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  teacher_phone   TEXT,
  section         TEXT,
  date            DATE NOT NULL,
  student_id      UUID REFERENCES students(id),
  status          TEXT CHECK (status IN ('present','absent')),
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_students_whatsapp  ON students(whatsapp_number);
CREATE INDEX IF NOT EXISTS idx_students_section   ON students(section);
CREATE INDEX IF NOT EXISTS idx_teachers_whatsapp  ON teachers(whatsapp_number);
CREATE INDEX IF NOT EXISTS idx_attendance_section ON attendance(section, date);
CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id, date);
