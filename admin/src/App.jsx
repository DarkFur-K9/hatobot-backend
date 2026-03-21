import { useState, useEffect } from 'react'
import { Login } from './pages/Login'
import { Layout } from './components/Layout'
import { Students } from './pages/Students'
import { Attendance } from './pages/Attendance'
import { Teachers } from './pages/Teachers'

const ADMIN_USER = 'jpr-college'
const ADMIN_PASS = 'jpr-college-password'

export default function App() {
  const [authed, setAuthed]   = useState(() => !!sessionStorage.getItem('admin_auth'))
  const [page, setPage]       = useState('attendance')

  const login = (u, p) => {
    if (u === ADMIN_USER && p === ADMIN_PASS) {
      sessionStorage.setItem('admin_auth', '1')
      setAuthed(true)
      return true
    }
    return false
  }

  const logout = () => {
    sessionStorage.removeItem('admin_auth')
    setAuthed(false)
  }

  if (!authed) return <Login onLogin={login} />

  return (
    <Layout page={page} setPage={setPage} onLogout={logout}>
      {page === 'students'   && <Students />}
      {page === 'attendance' && <Attendance />}
      {page === 'teachers'   && <Teachers />}
    </Layout>
  )
}
