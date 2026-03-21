import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'

export function Students() {
  const [students, setStudents] = useState([])
  const [loading,  setLoading]  = useState(true)
  const [search,   setSearch]   = useState('')
  const [deptFilter, setDept]   = useState('All')
  const [secFilter,  setSec]    = useState('All')

  useEffect(() => {
    supabase.table('students').select('*').order('roll_number')
      .then(({ data }) => { setStudents(data || []); setLoading(false) })
  }, [])

  const depts    = ['All', ...new Set(students.map(s => s.department).filter(Boolean))]
  const sections = ['All', ...new Set(students.map(s => s.section).filter(Boolean)).values()].sort()

  const filtered = students.filter(s => {
    const q = search.toLowerCase()
    const matchQ = !q || s.full_name?.toLowerCase().includes(q) || s.roll_number?.toLowerCase().includes(q)
    const matchD = deptFilter === 'All' || s.department === deptFilter
    const matchS = secFilter  === 'All' || s.section    === secFilter
    return matchQ && matchD && matchS
  })

  return (
    <div>
      <div style={styles.header}>
        <div>
          <h2 style={styles.title}>Students</h2>
          <p style={styles.sub}>{filtered.length} of {students.length} students</p>
        </div>
      </div>

      <div style={styles.filters}>
        <input style={styles.search} placeholder="Search by name or roll number…"
               value={search} onChange={e => setSearch(e.target.value)} />
        <select style={styles.select} value={deptFilter} onChange={e => setDept(e.target.value)}>
          {depts.map(d => <option key={d}>{d}</option>)}
        </select>
        <select style={styles.select} value={secFilter} onChange={e => setSec(e.target.value)}>
          {sections.map(s => <option key={s}>{s}</option>)}
        </select>
      </div>

      <div style={styles.card}>
        {loading ? <div style={styles.center}>Loading…</div> : (
          <table style={styles.table}>
            <thead>
              <tr style={styles.thead}>
                {['Roll No.','Name','Gender','Department','Section','Sem','Batch','Hostel','WhatsApp'].map(h => (
                  <th key={h} style={styles.th}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0
                ? <tr><td colSpan={9} style={styles.empty}>No students found.</td></tr>
                : filtered.map((s, i) => (
                  <tr key={s.id} style={i % 2 === 0 ? styles.tr : styles.trAlt}>
                    <td style={styles.td}><span style={styles.roll}>{s.roll_number}</span></td>
                    <td style={styles.td}>{s.full_name}</td>
                    <td style={styles.td}>{s.gender}</td>
                    <td style={styles.td}>{s.department}</td>
                    <td style={styles.td}><span style={styles.badge}>{s.section}</span></td>
                    <td style={styles.td}>{s.current_sem}</td>
                    <td style={styles.td}>{s.batch}</td>
                    <td style={styles.td}>
                      <span style={s.hostel === 'Yes' ? styles.yes : styles.no}>
                        {s.hostel === 'Yes' ? '✅ Yes' : '❌ No'}
                      </span>
                    </td>
                    <td style={styles.td}>{s.whatsapp_number}</td>
                  </tr>
                ))
              }
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

const styles = {
  header:  { display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:24 },
  title:   { fontSize:24, fontWeight:700 },
  sub:     { color:'#718096', fontSize:14, marginTop:4 },
  filters: { display:'flex', gap:12, marginBottom:16, flexWrap:'wrap' },
  search:  { flex:1, minWidth:200, padding:'9px 14px', border:'1.5px solid #e2e8f0', borderRadius:8, fontSize:14, outline:'none' },
  select:  { padding:'9px 14px', border:'1.5px solid #e2e8f0', borderRadius:8, fontSize:14, outline:'none', background:'#fff' },
  card:    { background:'#fff', borderRadius:12, boxShadow:'0 1px 4px rgba(0,0,0,.08)', overflow:'hidden' },
  table:   { width:'100%', borderCollapse:'collapse' },
  thead:   { background:'#f7fafc' },
  th:      { padding:'12px 16px', textAlign:'left', fontSize:12, fontWeight:600, color:'#4a5568', textTransform:'uppercase', letterSpacing:'.5px', borderBottom:'1px solid #e2e8f0' },
  tr:      { borderBottom:'1px solid #f0f4f8' },
  trAlt:   { background:'#fafbfc', borderBottom:'1px solid #f0f4f8' },
  td:      { padding:'11px 16px', fontSize:13 },
  roll:    { fontFamily:'monospace', background:'#ebf4ff', color:'#1a56db', padding:'2px 8px', borderRadius:4, fontWeight:600 },
  badge:   { background:'#f0fff4', color:'#276749', padding:'2px 8px', borderRadius:4, fontWeight:600, fontSize:12 },
  yes:     { color:'#276749', fontWeight:500 },
  no:      { color:'#c53030', fontWeight:500 },
  empty:   { padding:40, textAlign:'center', color:'#a0aec0' },
  center:  { padding:40, textAlign:'center', color:'#a0aec0' },
}
