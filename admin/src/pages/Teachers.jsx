import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'

const BOT_URL      = import.meta.env.VITE_BOT_URL      || ''
const ADMIN_SECRET = import.meta.env.VITE_ADMIN_SECRET || ''

export function Teachers() {
  const [teachers,  setTeachers]  = useState([])
  const [loading,   setLoading]   = useState(true)
  const [approving, setApproving] = useState(null)
  const [tab,       setTab]       = useState('pending')

  const load = () => {
    setLoading(true)
    supabase.table('teachers').select('*').order('full_name')
      .then(({ data }) => { setTeachers(data || []); setLoading(false) })
  }

  useEffect(() => { load() }, [])

  const approve = async (teacher) => {
    setApproving(teacher.id)
    try {
      await supabase.table('teachers').update({ approved: true }).eq('id', teacher.id)
      // Notify teacher via bot
      await fetch(`${BOT_URL}/notify/teacher-approved`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-admin-secret': ADMIN_SECRET },
        body: JSON.stringify({ whatsapp_number: teacher.whatsapp_number, full_name: teacher.full_name }),
      })
      load()
    } catch (e) {
      alert('Error approving teacher: ' + e.message)
    }
    setApproving(null)
  }

  const pending  = teachers.filter(t => !t.approved)
  const approved = teachers.filter(t =>  t.approved)
  const shown    = tab === 'pending' ? pending : approved

  return (
    <div>
      <div style={styles.header}>
        <div>
          <h2 style={styles.title}>Teachers</h2>
          <p style={styles.sub}>{pending.length} pending approval · {approved.length} approved</p>
        </div>
      </div>

      {/* Tabs */}
      <div style={styles.tabs}>
        <button style={tab==='pending'  ? styles.tabActive : styles.tab} onClick={() => setTab('pending')}>
          ⏳ Pending ({pending.length})
        </button>
        <button style={tab==='approved' ? styles.tabActive : styles.tab} onClick={() => setTab('approved')}>
          ✅ Approved ({approved.length})
        </button>
      </div>

      <div style={styles.card}>
        {loading ? <div style={styles.center}>Loading…</div> : shown.length === 0
          ? <div style={styles.center}>{tab === 'pending' ? 'No pending approvals 🎉' : 'No approved teachers yet.'}</div>
          : (
            <table style={styles.table}>
              <thead>
                <tr style={styles.thead}>
                  {['Emp ID','Name','WhatsApp','Status', tab === 'pending' ? 'Action' : ''].filter(Boolean).map(h => (
                    <th key={h} style={styles.th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {shown.map((t, i) => (
                  <tr key={t.id} style={i % 2 === 0 ? styles.tr : styles.trAlt}>
                    <td style={styles.td}><span style={styles.emp}>{t.emp_id}</span></td>
                    <td style={styles.td}><strong>{t.full_name}</strong></td>
                    <td style={styles.td}>{t.whatsapp_number}</td>
                    <td style={styles.td}>
                      <span style={t.approved ? styles.statusApproved : styles.statusPending}>
                        {t.approved ? '✅ Approved' : '⏳ Pending'}
                      </span>
                    </td>
                    {tab === 'pending' && (
                      <td style={styles.td}>
                        <button
                          style={approving === t.id ? styles.approvingBtn : styles.approveBtn}
                          disabled={approving === t.id}
                          onClick={() => approve(t)}>
                          {approving === t.id ? 'Approving…' : '✅ Approve'}
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          )
        }
      </div>
    </div>
  )
}

const styles = {
  header:          { display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:24 },
  title:           { fontSize:24, fontWeight:700 },
  sub:             { color:'#718096', fontSize:14, marginTop:4 },
  tabs:            { display:'flex', gap:8, marginBottom:16 },
  tab:             { padding:'8px 20px', background:'#fff', border:'1.5px solid #e2e8f0', borderRadius:8, cursor:'pointer', fontWeight:500, fontSize:14 },
  tabActive:       { padding:'8px 20px', background:'#1a56db', border:'1.5px solid #1a56db', borderRadius:8, cursor:'pointer', fontWeight:600, fontSize:14, color:'#fff' },
  card:            { background:'#fff', borderRadius:12, boxShadow:'0 1px 4px rgba(0,0,0,.08)', overflow:'hidden' },
  table:           { width:'100%', borderCollapse:'collapse' },
  thead:           { background:'#f7fafc' },
  th:              { padding:'12px 16px', textAlign:'left', fontSize:12, fontWeight:600, color:'#4a5568', textTransform:'uppercase', letterSpacing:'.5px', borderBottom:'1px solid #e2e8f0' },
  tr:              { borderBottom:'1px solid #f0f4f8' },
  trAlt:           { background:'#fafbfc', borderBottom:'1px solid #f0f4f8' },
  td:              { padding:'11px 16px', fontSize:13 },
  emp:             { fontFamily:'monospace', background:'#ebf4ff', color:'#1a56db', padding:'2px 8px', borderRadius:4, fontWeight:600 },
  statusApproved:  { background:'#f0fff4', color:'#276749', padding:'3px 10px', borderRadius:20, fontSize:12, fontWeight:600 },
  statusPending:   { background:'#fffbeb', color:'#92400e', padding:'3px 10px', borderRadius:20, fontSize:12, fontWeight:600 },
  approveBtn:      { padding:'7px 16px', background:'#0e9f6e', color:'#fff', border:'none', borderRadius:6, cursor:'pointer', fontWeight:600, fontSize:13 },
  approvingBtn:    { padding:'7px 16px', background:'#6ee7b7', color:'#fff', border:'none', borderRadius:6, cursor:'not-allowed', fontWeight:600, fontSize:13 },
  center:          { padding:40, textAlign:'center', color:'#a0aec0' },
}
