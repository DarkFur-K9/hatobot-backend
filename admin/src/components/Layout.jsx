export function Layout({ children, page, setPage, onLogout }) {
  const nav = [
    { id:'attendance', label:'Attendance', icon:'📊' },
    { id:'students',   label:'Students',   icon:'🎓' },
    { id:'teachers',   label:'Teachers',   icon:'👨‍🏫' },
  ]
  return (
    <div style={styles.wrap}>
      <aside style={styles.sidebar}>
        <div style={styles.sideTop}>
          <div style={styles.brand}>
            <span style={{ fontSize:28 }}>🎓</span>
            <div>
              <div style={styles.brandName}>JPR College</div>
              <div style={styles.brandSub}>Admin Panel</div>
            </div>
          </div>
          <nav style={styles.nav}>
            {nav.map(n => (
              <button key={n.id} style={page===n.id ? styles.navActive : styles.navItem}
                onClick={() => setPage(n.id)}>
                <span>{n.icon}</span> {n.label}
              </button>
            ))}
          </nav>
        </div>
        <button style={styles.logout} onClick={onLogout}>🚪 Logout</button>
      </aside>
      <main style={styles.main}>{children}</main>
    </div>
  )
}

const styles = {
  wrap:       { display:'flex', minHeight:'100vh' },
  sidebar:    { width:240, background:'#1e2a3a', display:'flex', flexDirection:'column', justifyContent:'space-between', padding:'24px 0', position:'fixed', top:0, left:0, height:'100vh' },
  sideTop:    { display:'flex', flexDirection:'column', gap:32 },
  brand:      { display:'flex', alignItems:'center', gap:12, padding:'0 20px' },
  brandName:  { color:'#fff', fontWeight:700, fontSize:15 },
  brandSub:   { color:'#718096', fontSize:12 },
  nav:        { display:'flex', flexDirection:'column', gap:4, padding:'0 12px' },
  navItem:    { display:'flex', alignItems:'center', gap:10, padding:'10px 16px', background:'transparent', border:'none', color:'#a0aec0', fontSize:14, fontWeight:500, borderRadius:8, cursor:'pointer', textAlign:'left', width:'100%' },
  navActive:  { display:'flex', alignItems:'center', gap:10, padding:'10px 16px', background:'#1a56db', border:'none', color:'#fff', fontSize:14, fontWeight:600, borderRadius:8, cursor:'pointer', textAlign:'left', width:'100%' },
  logout:     { margin:'0 12px', padding:'10px 16px', background:'transparent', border:'1px solid #2d3748', color:'#718096', borderRadius:8, cursor:'pointer', fontSize:14, textAlign:'left' },
  main:       { marginLeft:240, flex:1, padding:32, minHeight:'100vh' },
}
