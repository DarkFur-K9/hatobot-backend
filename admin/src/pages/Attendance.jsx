import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import * as XLSX from 'xlsx'

const SECTIONS = 'ABCDEFGHIJK'.split('').map(c => `Section ${c}`)

export function Attendance() {
  const [section,    setSection]    = useState(null)
  const [date,       setDate]       = useState(new Date().toISOString().split('T')[0])
  const [records,    setRecords]    = useState([])
  const [students,   setStudents]   = useState([])
  const [loading,    setLoading]    = useState(false)

  const load = async (sec, dt) => {
    setLoading(true)
    const [stuRes, attRes] = await Promise.all([
      supabase.table('students').select('*').eq('section', sec).order('roll_number'),
      supabase.table('attendance').select('*').eq('section', sec).eq('date', dt),
    ])
    const stus = stuRes.data || []
    const att  = attRes.data || []
    const attMap = Object.fromEntries(att.map(a => [a.student_id, a.status]))
    const merged = stus.map(s => ({ ...s, status: attMap[s.id] || 'not_recorded' }))
    setStudents(stus)
    setRecords(merged)
    setLoading(false)
  }

  useEffect(() => { if (section) load(section, date) }, [section, date])

  const hostelBoys  = records.filter(r => r.hostel === 'Yes' && r.gender === 'Male')
  const hostelGirls = records.filter(r => r.hostel === 'Yes' && r.gender === 'Female')
  const present     = records.filter(r => r.status === 'present')
  const absent      = records.filter(r => r.status === 'absent')

  const exportExcel = () => {
    const rows = records.map(r => ({
      'Roll No.'   : r.roll_number,
      'Name'       : r.full_name,
      'Gender'     : r.gender,
      'Hostel'     : r.hostel === 'Yes' ? 'Y' : 'N',
      'Status'     : r.status === 'present' ? 'Present' : r.status === 'absent' ? 'Absent' : 'Not Recorded',
      'Date'       : date,
      'Section'    : r.section,
      'Department' : r.department,
      'Batch'      : r.batch,
    }))
    const ws = XLSX.utils.json_to_sheet(rows)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, section)
    XLSX.writeFile(wb, `Attendance_${section.replace(' ','_')}_${date}.xlsx`)
  }

  const statusStyle = (status) => {
    if (status === 'present') return { ...styles.badge, background:'#f0fff4', color:'#276749' }
    if (status === 'absent')  return { ...styles.badge, background:'#fff5f5', color:'#c53030' }
    return { ...styles.badge, background:'#fffbeb', color:'#92400e' }
  }

  return (
    <div>
      <div style={styles.header}>
        <div>
          <h2 style={styles.title}>Attendance</h2>
          <p style={styles.sub}>View and export daily attendance by section</p>
        </div>
        {section && (
          <button style={styles.exportBtn} onClick={exportExcel}>⬇️ Export Excel</button>
        )}
      </div>

      {/* Section grid */}
      <div style={styles.secGrid}>
        {SECTIONS.map(s => (
          <button key={s}
            style={section === s ? styles.secActive : styles.secBtn}
            onClick={() => setSection(s)}>
            {s}
          </button>
        ))}
      </div>

      {section && (
        <>
          {/* Date picker */}
          <div style={styles.dateRow}>
            <label style={styles.dateLabel}>📅 Date:</label>
            <input type="date" value={date} style={styles.dateInput}
              onChange={e => setDate(e.target.value)} />
          </div>

          {/* Metrics */}
          {!loading && records.length > 0 && (
            <div style={styles.metrics}>
              {[
                { label:'Total',           val: records.length,                    color:'#1a56db' },
                { label:'Present',         val: present.length,                    color:'#0e9f6e' },
                { label:'Absent',          val: absent.length,                     color:'#f05252' },
                { label:'Hostel Boys ✅',  val: hostelBoys.filter(r=>r.status==='present').length + '/' + hostelBoys.length,  color:'#1a56db' },
                { label:'Hostel Girls ✅', val: hostelGirls.filter(r=>r.status==='present').length + '/' + hostelGirls.length, color:'#d53f8c' },
              ].map(m => (
                <div key={m.label} style={styles.metricCard}>
                  <div style={{ ...styles.metricVal, color: m.color }}>{m.val}</div>
                  <div style={styles.metricLabel}>{m.label}</div>
                </div>
              ))}
            </div>
          )}

          {/* Table */}
          <div style={styles.card}>
            {loading ? <div style={styles.center}>Loading…</div> : records.length === 0
              ? <div style={styles.center}>No records found for {section} on {date}.</div>
              : (
                <table style={styles.table}>
                  <thead>
                    <tr style={styles.thead}>
                      {['#','Roll No.','Name','Gender','Hostel','Status','Date'].map(h => (
                        <th key={h} style={styles.th}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((r, i) => (
                      <tr key={r.id} style={i % 2 === 0 ? styles.tr : styles.trAlt}>
                        <td style={styles.td}>{i+1}</td>
                        <td style={styles.td}><span style={styles.roll}>{r.roll_number}</span></td>
                        <td style={styles.td}><strong>{r.full_name}</strong></td>
                        <td style={styles.td}>{r.gender}</td>
                        <td style={styles.td}>{r.hostel === 'Yes' ? '🏠 Yes' : 'No'}</td>
                        <td style={styles.td}><span style={statusStyle(r.status)}>{r.status === 'present' ? '✅ Present' : r.status === 'absent' ? '❌ Absent' : '⚠️ Not Recorded'}</span></td>
                        <td style={styles.td}>{date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )
            }
          </div>
        </>
      )}

      {!section && (
        <div style={styles.empty}>
          <div style={{ fontSize:48 }}>📊</div>
          <div style={{ marginTop:12, fontSize:16, color:'#718096' }}>Select a section above to view attendance</div>
        </div>
      )}
    </div>
  )
}

const styles = {
  header:      { display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:24 },
  title:       { fontSize:24, fontWeight:700 },
  sub:         { color:'#718096', fontSize:14, marginTop:4 },
  exportBtn:   { padding:'10px 20px', background:'#0e9f6e', color:'#fff', border:'none', borderRadius:8, cursor:'pointer', fontWeight:600, fontSize:14 },
  secGrid:     { display:'flex', flexWrap:'wrap', gap:10, marginBottom:24 },
  secBtn:      { padding:'10px 18px', background:'#fff', border:'1.5px solid #e2e8f0', borderRadius:8, cursor:'pointer', fontWeight:500, fontSize:14 },
  secActive:   { padding:'10px 18px', background:'#1a56db', border:'1.5px solid #1a56db', borderRadius:8, cursor:'pointer', fontWeight:600, fontSize:14, color:'#fff' },
  dateRow:     { display:'flex', alignItems:'center', gap:12, marginBottom:20 },
  dateLabel:   { fontWeight:600, fontSize:14 },
  dateInput:   { padding:'8px 12px', border:'1.5px solid #e2e8f0', borderRadius:8, fontSize:14, outline:'none' },
  metrics:     { display:'flex', gap:16, marginBottom:20, flexWrap:'wrap' },
  metricCard:  { background:'#fff', borderRadius:10, padding:'16px 24px', boxShadow:'0 1px 4px rgba(0,0,0,.06)', minWidth:100, textAlign:'center' },
  metricVal:   { fontSize:28, fontWeight:700 },
  metricLabel: { fontSize:12, color:'#718096', marginTop:4, fontWeight:500 },
  card:        { background:'#fff', borderRadius:12, boxShadow:'0 1px 4px rgba(0,0,0,.08)', overflow:'hidden' },
  table:       { width:'100%', borderCollapse:'collapse' },
  thead:       { background:'#f7fafc' },
  th:          { padding:'12px 16px', textAlign:'left', fontSize:12, fontWeight:600, color:'#4a5568', textTransform:'uppercase', letterSpacing:'.5px', borderBottom:'1px solid #e2e8f0' },
  tr:          { borderBottom:'1px solid #f0f4f8' },
  trAlt:       { background:'#fafbfc', borderBottom:'1px solid #f0f4f8' },
  td:          { padding:'11px 16px', fontSize:13 },
  roll:        { fontFamily:'monospace', background:'#ebf4ff', color:'#1a56db', padding:'2px 8px', borderRadius:4, fontWeight:600 },
  badge:       { padding:'3px 10px', borderRadius:20, fontSize:12, fontWeight:600 },
  empty:       { textAlign:'center', padding:'80px 0', color:'#a0aec0' },
  center:      { padding:40, textAlign:'center', color:'#a0aec0' },
}
