import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Doughnut, Bar } from 'react-chartjs-2'
import { useTheme } from '../App'

import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
} from 'chart.js'
import { getUser, getPatient, getRiskHistory, logout } from '../api'
import '../css/dashboard.css'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement)

const navItems = [
  { icon: '🏠', label: 'Dashboard', path: '/dashboard' },
  { icon: '👤', label: 'Patient Data', path: '/patient' },
  { icon: '📈', label: 'Risk Analysis', path: '/risk' },
  { icon: '⏱️', label: 'Simulation', path: '/simulation' },
  { icon: '💊', label: 'Medications', path: '/medications' },
  { icon: '📋', label: 'Action Plan', path: '/action' },
]

const getGreeting = () => {
  const h = new Date().getHours()
  if (h < 12) return 'Good Morning'
  if (h < 17) return 'Good Afternoon'
  return 'Good Evening'
}

const getRiskColor = (risk) => {
  if (!risk) return '#6B7280'
  if (risk < 10) return '#22C55E'
  if (risk < 20) return '#F97316'
  if (risk < 30) return '#EF4444'
  return '#991B1B'
}

const getRiskLabel = (risk) => {
  if (!risk) return 'No data yet'
  if (risk < 10) return '🟢 Low Risk'
  if (risk < 20) return '🟡 Moderate Risk'
  if (risk < 30) return '🔴 High Risk'
  return '🔴 Very High Risk'
}

const getLifestyleScore = (patient) => {
  if (!patient) return null
  let score = 50
  score += (patient.exercise_days || 0) * 5
  const dietMap = { Poor: -10, Fair: 0, Good: 10, Excellent: 20 }
  score += dietMap[patient.diet_quality] || 0
  if (patient.smoking === 'Never') score += 10
  else if (patient.smoking === 'Former') score += 5
  else if (patient.smoking === 'Current') score -= 15
  return Math.max(0, Math.min(100, score))
}

function Dashboard() {
  const { darkMode, toggleTheme } = useTheme()
  const [menuOpen, setMenuOpen] = useState(false)
  const [activeTab, setActiveTab] = useState('All')
  const [user, setUser] = useState(null)
  const [patient, setPatient] = useState(null)
  const [riskHistory, setRiskHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      // Get user from localStorage (instant, no API call)
      const u = getUser()
      setUser(u)

      // Get patient data and risk history from API
      const [patientRes, historyRes] = await Promise.all([
        getPatient(),
        getRiskHistory(),
      ])
      if (patientRes.patient) setPatient(patientRes.patient)
      if (historyRes.history) setRiskHistory(historyRes.history)
    } catch (e) {
      console.error('Dashboard load error:', e)
    } finally {
      setLoading(false)
    }
  }

  const handleNavigate = (path) => {
    setMenuOpen(false)
    setTimeout(() => navigate(path), 100)
  }

  const handleLogout = async () => {
    try { await logout() } catch (e) {}
    navigate('/')
  }

  // ── Derived values ────────────────────────────────────────────────────
  const latestRisk = riskHistory.length > 0 ? riskHistory[0] : null
  const previousRisk = riskHistory.length > 1 ? riskHistory[1] : null
  const totalRisk = latestRisk?.total_risk || null
  const riskDelta = latestRisk && previousRisk
    ? (latestRisk.total_risk - previousRisk.total_risk).toFixed(1)
    : null
  const lifestyleScore = getLifestyleScore(patient)

  // ── Donut chart from real risk breakdown ──────────────────────────────
  const envRisk = latestRisk?.environmental_risk || 8
  const clinicalRisk = latestRisk?.clinical_risk || 15
  const genomicRisk = Math.abs(latestRisk?.genomic_risk || 5)
  const remaining = Math.max(0, 100 - (totalRisk || 28))

  const donutData = {
    datasets: [
      {
        data: [clinicalRisk, remaining],
        backgroundColor: ['#FF4444', '#FECACA'],
        borderWidth: 0,
        cutout: '75%',
        radius: '100%',
      },
      {
        data: [genomicRisk, 100 - genomicRisk],
        backgroundColor: ['#8B5CF6', '#EDE9FE'],
        borderWidth: 0,
        cutout: '60%',
        radius: '85%',
      },
      {
        data: [envRisk, 100 - envRisk],
        backgroundColor: ['#F97316', '#FED7AA'],
        borderWidth: 0,
        cutout: '45%',
        radius: '70%',
      },
    ],
  }

  // ── Bar chart from patient data ───────────────────────────────────────
  const bpScore = patient
    ? Math.min(100, ((patient.bp_systolic - 90) / (180 - 90)) * 100)
    : 60
  const ldlScore = patient
    ? Math.min(100, ((patient.ldl - 50) / (200 - 50)) * 100)
    : 50
  const activityScore = patient
    ? Math.max(0, 100 - patient.exercise_days * 14)
    : 60
  const envScore = envRisk * 3

  const barData = {
    labels: ['Blood Pressure', 'LDL Cholesterol', 'Physical Activity', 'Environment'],
    datasets: [{
      data: [bpScore, ldlScore, activityScore, envScore].map(v => Math.round(v)),
      backgroundColor: ['#FF6B6B', '#FFA500', '#FFA500', '#3B82F6'],
      borderRadius: 4,
      barThickness: 20,
    }],
  }

  const barOptions = {
    indexAxis: 'y',
    plugins: { legend: { display: false } },
    scales: {
      x: { display: false, max: 100 },
      y: {
        ticks: { font: { size: 11 }, color: '#6B7280' },
        grid: { display: false },
      },
    },
  }

  // ── Activity feed from risk history ───────────────────────────────────
  const activityFeed = riskHistory.slice(0, 5).map((r, i) => ({
    icon: '📈',
    title: 'Risk Assessment',
    desc: `${r.total_risk?.toFixed(1)}% total risk — ${r.total_risk < 10 ? 'Low' : r.total_risk < 20 ? 'Moderate' : 'High'}`,
    time: i === 0 ? 'Latest' : `Assessment ${i + 1}`,
    bg: '#FFF3E0',
  }))

  if (patient) {
    activityFeed.unshift({
      icon: '👤',
      title: 'Patient Profile Active',
      desc: `${patient.name || 'Profile'} · ${patient.age} yrs · BP ${patient.bp_systolic}/${patient.bp_diastolic}`,
      time: 'Saved',
      bg: '#E8F5E9',
    })
  }

  const filteredActivity = activeTab === 'All'
    ? activityFeed
    : activityFeed.filter(a =>
        activeTab === 'Risk' ? a.title.includes('Risk') :
        activeTab === 'Vitals' ? a.title.includes('Profile') :
        false
      )

  // ── First name only ───────────────────────────────────────────────────
  const firstName = user?.full_name?.split(' ')[0] || 'there'

  return (
    <div className="dashboard-screen">

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
          <button className="sidebar-item" onClick={() => handleNavigate('/help')}>
            <span className="sidebar-icon">❓</span><span>Help</span>
          </button>
          <button className="sidebar-item" onClick={handleLogout}>
            <span className="sidebar-icon">🚪</span><span>Log out</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="dashboard-main">

        <button className="hamburger" onClick={() => setMenuOpen(!menuOpen)}>
          <span></span><span></span><span></span>
        </button>

        <div className="dashboard-content">

          {/* Search + Bell */}
          <div className="top-bar">
            <div className="search-bar">
              <span>🔍</span>
              <input type="text" placeholder="Search" className="search-input" />
            </div>
            <button className="bell-btn" onClick={toggleTheme}>
              {darkMode ? '☀️' : '🌙'}
            </button>
          </div>

          {/* Greeting */}
          <div className="greeting">
            <p className="greeting-sub">{getGreeting()}</p>
            <h2 className="greeting-name">{firstName}</h2>
          </div>

          {/* No patient data prompt */}
          {!loading && !patient && (
            <div style={{
              background: 'linear-gradient(135deg, #1e3a5f, #2d5986)',
              borderRadius: '14px',
              padding: '20px',
              marginBottom: '20px',
              color: '#fff',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px',
            }}>
              <div>
                <p style={{ fontWeight: 700, fontSize: '16px', marginBottom: '4px' }}>
                  👋 Welcome to CardioSync!
                </p>
                <p style={{ opacity: 0.8, fontSize: '13px' }}>
                  Start by entering your health data to get your personalised risk assessment.
                </p>
              </div>
              <button
                onClick={() => navigate('/patient')}
                style={{
                  background: '#fff',
                  color: '#1e3a5f',
                  border: 'none',
                  borderRadius: '10px',
                  padding: '10px 18px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  fontSize: '13px',
                  whiteSpace: 'nowrap',
                }}
              >
                Get Started →
              </button>
            </div>
          )}

          {/* Summary Strip */}
          <h3 className="section-title">Summary</h3>
          <div className="summary-strip">
            <div className="summary-card" onClick={() => navigate('/risk')} style={{ cursor: 'pointer' }}>
              <p className="summary-label">Current Risk Score</p>
              <p className="summary-value" style={{ color: getRiskColor(totalRisk) }}>
                {totalRisk ? `${totalRisk.toFixed(1)}%` : '—'}
              </p>
            </div>
            <div className="summary-card">
              <p className="summary-label">Blood Pressure</p>
              <p className="summary-value">
                {patient ? `${patient.bp_systolic}/${patient.bp_diastolic}` : '—'}
                {patient && <span className="unit"> mmHg</span>}
              </p>
            </div>
            <div className="summary-card">
              <p className="summary-label">Assessments</p>
              <p className="summary-value">
                {riskHistory.length}
                <span className="unit"> total</span>
              </p>
            </div>
            <div className="summary-card">
              <p className="summary-label">Lifestyle Score</p>
              <p className="summary-value">
                {lifestyleScore !== null ? `${lifestyleScore}/100` : '—'}
              </p>
            </div>
          </div>

          {/* Charts Row */}
          <div className="charts-row">

            {/* Risk Overview */}
            <div className="chart-card">
              <div className="chart-header">
                <p className="chart-title">Risk Overview</p>
                <span className="chip" onClick={() => navigate('/risk')} style={{ cursor: 'pointer' }}>
                  View Details →
                </span>
              </div>
              <p className="risk-percent">
                {totalRisk ? `${totalRisk.toFixed(1)}%` : '—'}
                {riskDelta && (
                  <span className="risk-sub" style={{ color: riskDelta > 0 ? '#EF4444' : '#22C55E' }}>
                    {' '}{riskDelta > 0 ? '+' : ''}{riskDelta}% from last assessment
                  </span>
                )}
              </p>
              <div className="risk-chart-body">
                <div className="donut-wrapper">
                  <Doughnut
                    data={donutData}
                    options={{ plugins: { legend: { display: false } } }}
                  />
                </div>
                <div className="donut-legend">
                  <p className="legend-item">
                    <span className="legend-dot" style={{ background: '#FF4444' }}></span>
                    Clinical Risk {clinicalRisk.toFixed(1)}%
                  </p>
                  <p className="legend-item">
                    <span className="legend-dot" style={{ background: '#8B5CF6' }}></span>
                    Genomic Risk {genomicRisk.toFixed(1)}%
                  </p>
                  <p className="legend-item">
                    <span className="legend-dot" style={{ background: '#F97316' }}></span>
                    Air Quality {envRisk.toFixed(1)}%
                  </p>
                </div>
              </div>
              <div className="risk-badge">{getRiskLabel(totalRisk)}</div>
            </div>

            {/* Contributing Factors */}
            <div className="chart-card">
              <div className="chart-header">
                <p className="chart-title">Contributing Factors</p>
              </div>
              <div className="bar-wrapper">
                <Bar data={barData} options={barOptions} />
              </div>
              <div className="stats-row">
                <div className="stat-item">
                  <p className="stat-icon">💊</p>
                  <p className="stat-label">Blood Pressure</p>
                  <span className="stat-badge" style={{
                    background: patient?.bp_systolic >= 140 ? '#FEE2E2' : patient?.bp_systolic >= 130 ? '#FEF3C7' : patient?.bp_systolic >= 120 ? '#FEF9C3' : '#DCFCE7',
                    color: patient?.bp_systolic >= 140 ? '#DC2626' : patient?.bp_systolic >= 130 ? '#92400E' : patient?.bp_systolic >= 120 ? '#854D0E' : '#15803D'
                  }}>
                    {patient?.bp_systolic >= 140 ? '↑ High' : patient?.bp_systolic >= 130 ? '↑ Stage 1' : patient?.bp_systolic >= 120 ? '↑ Elevated' : '✓ Normal'}
                  </span>
                  <p className="stat-value">
                    {patient ? `${patient.bp_systolic}/${patient.bp_diastolic}` : '—'}
                    <span className="stat-unit"> mmHg</span>
                  </p>
                </div>
                <div className="stat-item">
                  <p className="stat-icon">🧬</p>
                  <p className="stat-label">LDL Cholesterol</p>
                  <span className="stat-badge" style={{
                     background: patient?.ldl >= 190 ? '#FEE2E2' : patient?.ldl >= 160 ? '#FEE2E2' : patient?.ldl >= 130 ? '#FEF3C7' : patient?.ldl >= 100 ? '#FEF9C3' : '#DCFCE7',
                     color: patient?.ldl >= 190 ? '#DC2626' : patient?.ldl >= 160 ? '#DC2626' : patient?.ldl >= 130 ? '#92400E' : patient?.ldl >= 100 ? '#854D0E' : '#15803D',
                  }}>
                    {patient?.ldl >= 190 ? '↑ Very High' : patient?.ldl >= 160 ? '↑ High' : patient?.ldl >= 130 ? '↑ Borderline' : patient?.ldl >= 100 ? '↑ Near Optimal' : '✓ Optimal'}
                  </span>
                  <p className="stat-value">
                    {patient?.ldl || '—'}
                    <span className="stat-unit"> mg/dL</span>
                  </p>
                </div>
                <div className="stat-item">
                  <p className="stat-icon">🏃</p>
                  <p className="stat-label">Exercise</p>
                  <span className="stat-badge" style={{
                     background: (patient?.exercise_days || 0) >= 5 ? '#DCFCE7' : (patient?.exercise_days || 0) >= 3 ? '#FEF9C3' : (patient?.exercise_days || 0) >= 1 ? '#FEF3C7' : '#FEE2E2',
                    color: (patient?.exercise_days || 0) >= 5 ? '#15803D' : (patient?.exercise_days || 0) >= 3 ? '#854D0E' : (patient?.exercise_days || 0) >= 1 ? '#92400E' : '#DC2626',
                  }}>
                    {(patient?.exercise_days || 0) >= 5 ? '✓ Active' : (patient?.exercise_days || 0) >= 3 ? '↑ Moderate' : (patient?.exercise_days || 0) >= 1 ? '↓ Low' : '↓ Sedentary'}
                  </span>
                  <p className="stat-value">
                    {patient?.exercise_days ?? '—'}
                    <span className="stat-unit"> days/wk</span>
                  </p>
                </div>
                <div className="stat-item">
                  <p className="stat-icon">🌍</p>
                  <p className="stat-label">Environment</p>
                  <span className="stat-badge" style={{
                    background: envRisk > 15 ? '#FEE2E2' : envRisk > 8 ? '#FEF3C7' : envRisk > 3 ? '#FEF9C3' : '#DCFCE7',
                  color: envRisk > 15 ? '#DC2626' : envRisk > 8 ? '#92400E' : envRisk > 3 ? '#854D0E' : '#15803D',
                  }}>
                    {envRisk > 15 ? '↑ Hazardous' : envRisk > 8 ? '↑ Unhealthy' : envRisk > 3 ? '↑ Moderate' : '✓ Good'}
                  </span>
                  <p className="stat-value">
                    +{envRisk.toFixed(1)}
                    <span className="stat-unit"> % risk</span>
                  </p>
                </div>
              </div>
            </div>

          </div>

          {/* Quick Actions */}
          <div className="section-card">
            <h3 className="section-title">Quick Actions</h3>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              {[
                { label: '📈 Run Risk Analysis', path: '/risk', color: '#EFF6FF', text: '#1D4ED8' },
                { label: '⏱️ Simulate Changes', path: '/simulation', color: '#F0FDF4', text: '#15803D' },
                { label: '💊 View Medications', path: '/medications', color: '#FDF4FF', text: '#7E22CE' },
                { label: '📋 Action Plan', path: '/action', color: '#FFF7ED', text: '#C2410C' },
              ].map((action, i) => (
                <button
                  key={i}
                  onClick={() => navigate(action.path)}
                  style={{
                    background: action.color,
                    color: action.text,
                    border: 'none',
                    borderRadius: '10px',
                    padding: '10px 16px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    fontSize: '13px',
                  }}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="section-card">
            <h3 className="section-title">Recent Activity</h3>
            <div className="activity-tabs">
              {['All', 'Risk', 'Vitals'].map(tab => (
                <button
                  key={tab}
                  className={`activity-tab ${activeTab === tab ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab)}
                >
                  {tab}
                </button>
              ))}
            </div>
            <div className="activity-list">
              {filteredActivity.length === 0 ? (
                <p style={{ color: '#9CA3AF', fontSize: '13px', padding: '16px 0' }}>
                  No activity yet. Complete a risk assessment to see your history here.
                </p>
              ) : (
                filteredActivity.map((a, i) => (
                  <div key={i} className="activity-item">
                    <div className="activity-icon-wrapper" style={{ background: a.bg }}>
                      {a.icon}
                    </div>
                    <div className="activity-text">
                      <p className="activity-title">{a.title}</p>
                      <p className="activity-desc">{a.desc}</p>
                    </div>
                    <span className="activity-time">{a.time}</span>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}

export default Dashboard