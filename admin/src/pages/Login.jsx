import { useState } from 'react'

export function Login({ onLogin }) {
  const [user, setUser] = useState('')
  const [pass, setPass] = useState('')
  const [err,  setErr]  = useState('')
  const [loading, setLoading] = useState(false)

  const handle = (e) => {
    e.preventDefault()
    setLoading(true)
    setTimeout(() => {
      if (!onLogin(user, pass)) setErr('Invalid credentials')
      setLoading(false)
    }, 400)
  }

  return (
    <div style={styles.wrap}>
      <div style={styles.card}>
        <div style={styles.logo}>
          <span style={styles.logoIcon}>🎓</span>
          <h1 style={styles.title}>JPR College</h1>
          <p style={styles.sub}>HatoBot Admin Panel</p>
        </div>
        <form onSubmit={handle} style={styles.form}>
          {err && <div style={styles.err}>{err}</div>}
          <div style={styles.field}>
            <label style={styles.label}>Username</label>
            <input style={styles.input} value={user}
              onChange={e => { setUser(e.target.value); setErr('') }}
              placeholder="jpr-college" autoFocus />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Password</label>
            <input style={styles.input} type="password" value={pass}
              onChange={e => { setPass(e.target.value); setErr('') }}
              placeholder="••••••••••••" />
          </div>
          <button style={loading ? styles.btnDisabled : styles.btn}
                  type="submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  )
}

const styles = {
  wrap:       { minHeight:'100vh', display:'flex', alignItems:'center', justifyContent:'center', background:'linear-gradient(135deg,#1e2a3a 0%,#1a56db 100%)' },
  card:       { background:'#fff', borderRadius:16, padding:'40px 36px', width:380, boxShadow:'0 20px 60px rgba(0,0,0,0.3)' },
  logo:       { textAlign:'center', marginBottom:32 },
  logoIcon:   { fontSize:48 },
  title:      { fontSize:24, fontWeight:700, color:'#1a202c', marginTop:8 },
  sub:        { fontSize:14, color:'#718096', marginTop:4 },
  form:       { display:'flex', flexDirection:'column', gap:16 },
  field:      { display:'flex', flexDirection:'column', gap:6 },
  label:      { fontSize:13, fontWeight:600, color:'#4a5568' },
  input:      { padding:'10px 14px', border:'1.5px solid #e2e8f0', borderRadius:8, fontSize:14, outline:'none', transition:'border .2s' },
  btn:        { padding:'12px', background:'#1a56db', color:'#fff', border:'none', borderRadius:8, fontSize:15, fontWeight:600, cursor:'pointer', marginTop:8 },
  btnDisabled:{ padding:'12px', background:'#93b4f5', color:'#fff', border:'none', borderRadius:8, fontSize:15, fontWeight:600, cursor:'not-allowed', marginTop:8 },
  err:        { background:'#fff5f5', border:'1px solid #fed7d7', color:'#c53030', borderRadius:8, padding:'10px 14px', fontSize:13 },
}
