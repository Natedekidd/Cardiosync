import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getUser, getPatient, getRiskHistory, logout, deleteAccount } from '../api'

const navItems = [
  { icon: '🏠', label: 'Dashboard', path: '/dashboard' },
  { icon: '👤', label: 'Patient Data', path: '/patient' },
  { icon: '📈', label: 'Risk Analysis', path: '/risk' },
  { icon: '⏱️', label: 'Simulation', path: '/simulation' },
  { icon: '💊', label: 'Medications', path: '/medications' },
  { icon: '📋', label: 'Action Plan', path: '/action' },
]

function Profile() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [user, setUser] = useState(null)
  const [patient, setPatient] = useState(null)
  const [riskHistory, setRiskHistory] = useState([])
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const navigate = useNavigate()

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    const u = getUser()
    setUser(u)
    try {
      const [patientRes, historyRes] = await Promise.all([
        getPatient(),
        getRiskHistory(),
      ])
      if (patientRes.patient) setPatient(patientRes.patient)
      if (historyRes.history) setRiskHistory(historyRes.history)
    } catch (e) { console.error(e) }
  }

  const handleNavigate = (path) => {
    setMenuOpen(false)
    setTimeout(() => navigate(path), 100)
  }

  const handleLogout = async () => {
    try { await logout() } catch (e) {}
    navigate('/')
  }

  const handleDeleteAccount = async () => {
    setDeleting(true)
    try {
      await deleteAccount()
      navigate('/')
    } catch (e) {
      console.error(e)
      setDeleting(false)
      setShowDeleteConfirm(false)
    }
  }

  const latestRisk = riskHistory.length > 0 ? riskHistory[0] : null
  const totalRisk = latestRisk?.total_risk || null
  const riskCategory = totalRisk
    ? totalRisk < 10 ? 'Low' : totalRisk < 20 ? 'Moderate' : totalRisk < 30 ? 'High' : 'Very High'
    : null
  const riskColor = totalRisk
    ? totalRisk < 10 ? '#22C55E' : totalRisk < 20 ? '#F97316' : '#EF4444'
    : '#6B7280'

  return (
    <div className="dashboard-screen">

      {/* Delete confirm modal */}
      {showDeleteConfirm && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }}>
          <div style={{ background: '#fff', borderRadius: '16px', padding: '28px', maxWidth: '320px', width: '90%' }}>
            <h3 style={{ fontWeight: 700, fontSize: '18px', marginBottom: '12px' }}>Delete Account?</h3>
            <p style={{ color: '#6B7280', fontSize: '14px', marginBottom: '20px', lineHeight: 1.5 }}>
              This will permanently delete your account, patient data, and all risk assessments. This cannot be undone.
            </p>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                style={{ flex: 1, padding: '12px', borderRadius: '10px', border: '1px solid #E5E7EB', background: '#F9FAFB', cursor: 'pointer', fontWeight: 600 }}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={deleting}
                style={{ flex: 1, padding: '12px', borderRadius: '10px', border: 'none', background: '#EF4444', color: '#fff', cursor: 'pointer', fontWeight: 600 }}
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sidebar */}
      <div className={`sidebar ${menuOpen ? 'open' : ''}`}>
        <button className="sidebar-close" onClick={() => setMenuOpen(false)}>✕</button>
        <h2 className="sidebar-logo">Cardiosync</h2>
        <nav className="sidebar-nav">
          {navItems.map((item, i) => (
            <button key={i} className="sidebar-item" onClick={() => handleNavigate(item.path)}>
              <span className="sidebar-icon">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <button className="sidebar-item" onClick={() => handleNavigate('/profile')}>
            <span className="sidebar-icon">👤</span><span>Profile</span>
          </button>
          <button className="sidebar-item" onClick={handleLogout}>
            <span className="sidebar-icon">🚪</span><span>Log out</span>
          </button>
        </div>
      </div>

      <div className="dashboard-main">
        <button className="hamburger" onClick={() => setMenuOpen(!menuOpen)}>
          <span></span><span></span><span></span>
        </button>

        <div className="dashboard-content">

          {/* Profile header */}
          <div style={{
            background: 'linear-gradient(135deg, #1e3a5f, #2d5986)',
            borderRadius: '16px', padding: '28px', marginBottom: '20px', color: '#fff', textAlign: 'center',
          }}>
            <div style={{
              width: '72px', height: '72px', borderRadius: '50%',
              background: 'rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center',
              justifyContent: 'center', fontSize: '32px', margin: '0 auto 12px',
            }}>
              👤
            </div>
            <h2 style={{ fontSize: '22px', fontWeight: 700, marginBottom: '4px' }}>
              {user?.full_name || 'User'}
            </h2>
            <p style={{ opacity: 0.8, fontSize: '14px' }}>{user?.email || ''}</p>
            {totalRisk && (
              <div style={{ marginTop: '12px', display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'rgba(255,255,255,0.15)', padding: '6px 16px', borderRadius: '20px' }}>
                <span style={{ color: riskColor, fontWeight: 700 }}>●</span>
                <span style={{ fontSize: '13px' }}>{riskCategory} Risk · {totalRisk.toFixed(1)}%</span>
              </div>
            )}
          </div>

          {/* Health stats */}
          {patient && (
            <div style={{ background: '#fff', borderRadius: '14px', padding: '20px', marginBottom: '16px', boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
              <h3 style={{ fontWeight: 700, fontSize: '15px', marginBottom: '16px' }}>🩺 Health Stats</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                {[
                  { label: 'Age', value: `${patient.age} years` },
                  { label: 'Sex', value: patient.sex },
                  { label: 'Blood Pressure', value: `${patient.bp_systolic}/${patient.bp_diastolic} mmHg` },
                  { label: 'Smoking', value: patient.smoking },
                  { label: 'Exercise', value: `${patient.exercise_days} days/week` },
                  { label: 'Diet', value: patient.diet_quality },
                  { label: 'Assessments', value: `${riskHistory.length} completed` },
                  { label: 'Location', value: patient.location || 'Not set' },
                ].map((item, i) => (
                  <div key={i} style={{ background: '#F9FAFB', borderRadius: '10px', padding: '12px' }}>
                    <p style={{ fontSize: '11px', color: '#9CA3AF', marginBottom: '4px' }}>{item.label}</p>
                    <p style={{ fontSize: '14px', fontWeight: 600, color: '#1e3a5f', margin: 0 }}>{item.value}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Account actions */}
          <div style={{ background: '#fff', borderRadius: '14px', padding: '20px', marginBottom: '16px', boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
            <h3 style={{ fontWeight: 700, fontSize: '15px', marginBottom: '16px' }}>⚙️ Account</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <button
                onClick={() => navigate('/patient')}
                style={{ width: '100%', padding: '12px 16px', borderRadius: '10px', border: '1px solid #E5E7EB', background: '#F9FAFB', cursor: 'pointer', fontWeight: 600, fontSize: '14px', textAlign: 'left' }}
              >
                ✏️ Update Health Profile
              </button>
              <button
                onClick={() => navigate('/risk')}
                style={{ width: '100%', padding: '12px 16px', borderRadius: '10px', border: '1px solid #E5E7EB', background: '#F9FAFB', cursor: 'pointer', fontWeight: 600, fontSize: '14px', textAlign: 'left' }}
              >
                📈 Run New Risk Assessment
              </button>
              <button
                onClick={handleLogout}
                style={{ width: '100%', padding: '12px 16px', borderRadius: '10px', border: '1px solid #E5E7EB', background: '#F9FAFB', cursor: 'pointer', fontWeight: 600, fontSize: '14px', textAlign: 'left', color: '#6B7280' }}
              >
                🚪 Log Out
              </button>
              <button
                onClick={() => setShowDeleteConfirm(true)}
                style={{ width: '100%', padding: '12px 16px', borderRadius: '10px', border: '1px solid #FCA5A5', background: '#FEF2F2', cursor: 'pointer', fontWeight: 600, fontSize: '14px', textAlign: 'left', color: '#DC2626' }}
              >
                🗑️ Delete Account
              </button>
            </div>
          </div>

          <p style={{ textAlign: 'center', fontSize: '12px', color: '#9CA3AF', marginBottom: '24px' }}>
            CardioSync · Precision Cardiovascular Risk Platform
          </p>
        </div>
      </div>
    </div>
  )
}

export default Profile