import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bar, Doughnut } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js'
import { assessRisk, getPatient, getUser } from '../api'

ChartJS.register(ArcElement, CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const navItems = [
  { icon: '🏠', label: 'Dashboard', path: '/dashboard' },
  { icon: '👤', label: 'Patient Data', path: '/patient' },
  { icon: '📈', label: 'Risk Analysis', path: '/risk' },
  { icon: '⏱️', label: 'Simulation', path: '/simulation' },
  { icon: '💊', label: 'Medications', path: '/medications' },
  { icon: '📋', label: 'Action Plan', path: '/action' },
]

function RiskAnalysis() {
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [patient, setPatient] = useState(null)

  const handleNavigate = (path) => {
    setMenuOpen(false)
    setTimeout(() => navigate(path), 100)
  }

  useEffect(() => {
    runAnalysis()
  }, [])

  const runAnalysis = async () => {
    setLoading(true)
    setError('')
    try {
      // Get saved patient data
      const patientRes = await getPatient()
      if (!patientRes.patient) {
        setError('No patient data found. Please fill in your Patient Data first.')
        setLoading(false)
        return
      }
      const p = patientRes.patient
      setPatient(p)

      // Call risk assessment
      const riskRes = await assessRisk({
        name: p.name || 'Patient',
        age: p.age,
        sex: p.sex,
        bp_systolic: p.bp_systolic,
        bp_diastolic: p.bp_diastolic,
        total_cholesterol: p.total_cholesterol,
        hdl: p.hdl,
        ldl: p.ldl,
        smoking: p.smoking,
        exercise_days: p.exercise_days,
        diet_quality: p.diet_quality,
        location: p.location,
        bmi: p.bmi,
        heart_rate: p.heart_rate,
        glucose: p.glucose,
      })
      setResult(riskRes)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // ── Chart data built from real results ──────────────────────────────────
  const buildBarData = () => {
    if (!result?.ai_explanation?.top_features) {
      // Fallback if SHAP not available
      return {
        labels: ['Blood Pressure', 'Cholesterol', 'Smoking', 'Exercise', 'Diet', 'Environment'],
        datasets: [{
          data: [20, 15, 10, -8, -5, result?.environmental_factor || 0],
          backgroundColor: ['#FF6B6B', '#FFA500', '#FF4444', '#22C55E', '#22C55E', '#3B82F6'],
          borderRadius: 4,
          barThickness: 18,
        }],
      }
    }

    const features = result.ai_explanation.top_features.slice(0, 7)
    return {
      labels: features.map(f => f.feature),
      datasets: [{
        data: features.map(f => parseFloat((f.contribution * 100).toFixed(1))),
        backgroundColor: features.map(f =>
          f.impact === 'Increases risk' ? '#FF6B6B' : '#22C55E'
        ),
        borderRadius: 4,
        barThickness: 18,
      }],
    }
  }

  const buildDonutData = () => {
    const env = result?.environmental_factor || 0
    const base = result?.base_risk || 0
    const total = result?.total_risk || 0
    const other = Math.max(0, base - env)

    return {
      datasets: [{
        data: [other, env, 100 - total],
        backgroundColor: ['#FF4444', '#3B82F6', '#F3F4F6'],
        borderWidth: 0,
        cutout: '70%',
      }],
    }
  }

  const getRiskColor = (category) => {
    const map = {
      'Low': '#22C55E',
      'Moderate': '#F97316',
      'High': '#EF4444',
      'Very High': '#991B1B',
    }
    return map[category] || '#6B7280'
  }

  const getRiskEmoji = (category) => {
    const map = {
      'Low': '🟢',
      'Moderate': '🟡',
      'High': '🔴',
      'Very High': '🔴',
    }
    return map[category] || '⚪'
  }

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
          <button className="sidebar-item" onClick={() => handleNavigate('/')}>
            <span className="sidebar-icon">🚪</span><span>Log out</span>
          </button>
        </div>
      </div>

      {/* Main */}
      <div className="dashboard-main">
        <button className="hamburger" onClick={() => setMenuOpen(!menuOpen)}>
          <span></span><span></span><span></span>
        </button>

        <div className="dashboard-content">
          <h2 style={{ marginBottom: '20px', fontSize: '22px', fontWeight: 700 }}>
            🧬 Risk Analysis
          </h2>

          {/* Loading */}
          {loading && (
            <div style={{ textAlign: 'center', padding: '60px 20px' }}>
              <div style={{ fontSize: '40px', marginBottom: '16px' }}>⏳</div>
              <p style={{ color: '#6B7280', fontSize: '15px' }}>
                Analysing your cardiovascular risk using AI...
              </p>
            </div>
          )}

          {/* Error */}
          {!loading && error && (
            <div style={{ background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '12px', padding: '20px', marginBottom: '20px' }}>
              <p style={{ color: '#DC2626', margin: 0 }}>⚠️ {error}</p>
              {error.includes('Patient Data') && (
                <button
                  onClick={() => navigate('/patient')}
                  style={{ marginTop: '12px', background: '#3B82F6', color: '#fff', border: 'none', borderRadius: '8px', padding: '8px 16px', cursor: 'pointer' }}
                >
                  Go to Patient Data →
                </button>
              )}
            </div>
          )}

          {/* Results */}
          {!loading && result && (
            <>
              {/* Fallback notice */}
              {result.fallback_used && (
                <div style={{ background: '#FFF7ED', border: '1px solid #FED7AA', borderRadius: '10px', padding: '12px 16px', marginBottom: '16px', fontSize: '13px', color: '#92400E' }}>
                  ⚠️ AI model offline — showing formula-based estimate. Ask your AI teammate to start the model server.
                </div>
              )}

              {/* Risk Score Hero */}
              <div style={{
                background: 'linear-gradient(135deg, #1e3a5f 0%, #2d5986 100%)',
                borderRadius: '16px',
                padding: '28px',
                marginBottom: '20px',
                color: '#fff',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '16px',
              }}>
                <div>
                  <p style={{ opacity: 0.8, marginBottom: '4px', fontSize: '14px' }}>
                    10-Year Cardiovascular Risk
                  </p>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                    <span style={{ fontSize: '56px', fontWeight: 800, lineHeight: 1 }}>
                      {result.total_risk}%
                    </span>
                    <span style={{
                      background: getRiskColor(result.risk_category),
                      padding: '4px 12px',
                      borderRadius: '20px',
                      fontSize: '13px',
                      fontWeight: 600,
                    }}>
                      {getRiskEmoji(result.risk_category)} {result.risk_category}
                    </span>
                  </div>
                  {patient && (
                    <p style={{ opacity: 0.7, marginTop: '8px', fontSize: '13px' }}>
                      {patient.name || 'Patient'} · {patient.age} yrs · {patient.sex}
                    </p>
                  )}
                </div>

                {/* Mini donut */}
                <div style={{ width: '120px', height: '120px' }}>
                  <Doughnut
                    data={buildDonutData()}
                    options={{ plugins: { legend: { display: false } }, cutout: '70%' }}
                  />
                </div>
              </div>

              {/* Risk breakdown metrics */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '20px' }}>
                {[
                  { label: 'Clinical Risk', value: `${result.base_risk}%`, icon: '🏥' },
                  { label: 'Environmental', value: `+${result.environmental_factor}%`, icon: '🌍' },
                  { label: 'AI Model', value: result.ai_model_used ? '✅ Active' : '⚠️ Offline', icon: '🤖' },
                ].map((item, i) => (
                  <div key={i} style={{
                    background: '#fff',
                    borderRadius: '12px',
                    padding: '16px',
                    boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
                    textAlign: 'center',
                  }}>
                    <div style={{ fontSize: '22px', marginBottom: '4px' }}>{item.icon}</div>
                    <div style={{ fontSize: '18px', fontWeight: 700, color: '#1e3a5f' }}>{item.value}</div>
                    <div style={{ fontSize: '12px', color: '#6B7280' }}>{item.label}</div>
                  </div>
                ))}
              </div>

              {/* Contributing factors chart */}
              <div style={{ background: '#fff', borderRadius: '16px', padding: '20px', marginBottom: '20px', boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
                <h3 style={{ marginBottom: '16px', fontSize: '16px', fontWeight: 600 }}>
                  📊 Contributing Factors
                </h3>
                <Bar
                  data={buildBarData()}
                  options={{
                    indexAxis: 'y',
                    plugins: { legend: { display: false } },
                    scales: {
                      x: { grid: { color: '#F3F4F6' }, ticks: { font: { size: 11 } } },
                      y: { grid: { display: false }, ticks: { font: { size: 11 }, color: '#374151' } },
                    },
                  }}
                />
                <div style={{ display: 'flex', gap: '16px', marginTop: '12px', fontSize: '12px', color: '#6B7280' }}>
                  <span><span style={{ color: '#FF6B6B' }}>■</span> Increases risk</span>
                  <span><span style={{ color: '#22C55E' }}>■</span> Decreases risk</span>
                </div>
              </div>

              {/* Recommendations */}
              {result.recommendations?.length > 0 && (
                <div style={{ background: '#fff', borderRadius: '16px', padding: '20px', marginBottom: '20px', boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
                  <h3 style={{ marginBottom: '16px', fontSize: '16px', fontWeight: 600 }}>
                    💡 Personalised Recommendations
                  </h3>
                  {result.recommendations.map((rec, i) => (
                    <div key={i} style={{
                      display: 'flex',
                      gap: '12px',
                      alignItems: 'flex-start',
                      padding: '12px 0',
                      borderBottom: i < result.recommendations.length - 1 ? '1px solid #F3F4F6' : 'none',
                    }}>
                      <span style={{
                        background: '#EFF6FF',
                        color: '#3B82F6',
                        borderRadius: '50%',
                        width: '24px',
                        height: '24px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '12px',
                        fontWeight: 700,
                        flexShrink: 0,
                      }}>
                        {i + 1}
                      </span>
                      <p style={{ margin: 0, fontSize: '14px', color: '#374151', lineHeight: 1.5 }}>{rec}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Action buttons */}
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <button
                  onClick={() => navigate('/simulation')}
                  style={{
                    flex: 1,
                    background: '#1e3a5f',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '12px',
                    padding: '14px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    fontSize: '14px',
                  }}
                >
                  ⏱️ Run Simulation
                </button>
                <button
                  onClick={() => navigate('/medications')}
                  style={{
                    flex: 1,
                    background: '#F0FDF4',
                    color: '#15803D',
                    border: '1px solid #86EFAC',
                    borderRadius: '12px',
                    padding: '14px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    fontSize: '14px',
                  }}
                >
                  💊 View Medications
                </button>
                <button
                  onClick={runAnalysis}
                  style={{
                    flex: 1,
                    background: '#F9FAFB',
                    color: '#6B7280',
                    border: '1px solid #E5E7EB',
                    borderRadius: '12px',
                    padding: '14px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    fontSize: '14px',
                  }}
                >
                  🔄 Recalculate
                </button>
              </div>

              <p style={{ marginTop: '16px', fontSize: '12px', color: '#9CA3AF', textAlign: 'center' }}>
                ⚕️ This is a research tool, not a medical diagnosis. Always consult your doctor.
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default RiskAnalysis