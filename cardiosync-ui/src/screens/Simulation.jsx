import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js'
import { simulateRisk, getPatient } from '../api'
import '../css/simulation.css'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const navItems = [
  { icon: '🏠', label: 'Dashboard', path: '/dashboard' },
  { icon: '👤', label: 'Patient Data', path: '/patient' },
  { icon: '📈', label: 'Risk Analysis', path: '/risk' },
  { icon: '⏱️', label: 'Simulation', path: '/simulation' },
  { icon: '💊', label: 'Medications', path: '/medications' },
  { icon: '📋', label: 'Action Plan', path: '/action' },
]

function Simulation() {
  const [menuOpen, setMenuOpen] = useState(false)
  const navigate = useNavigate()

  const [patient, setPatient] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  // Slider values (0-100 scale mapped to real values)
  const [sliders, setSliders] = useState({
    exercise: 50,   // 0=0 days, 100=7 days
    diet: 50,       // 0=Poor, 100=Excellent
    smoking: 0,     // 0=quit, 100=daily
    statin: 0,      // 0=no, 100=yes (toggle)
  })

  useEffect(() => {
    loadPatient()
  }, [])

  const loadPatient = async () => {
    try {
      const res = await getPatient()
      if (res.patient) setPatient(res.patient)
    } catch (e) {
      console.error(e)
    }
  }

  const handleSlider = (key, value) => {
    setSliders(prev => ({ ...prev, [key]: Number(value) }))
  }

  const handleNavigate = (path) => {
    setMenuOpen(false)
    setTimeout(() => navigate(path), 100)
  }

  // Map slider 0-100 to real values
  const getExerciseDays = () => Math.round((sliders.exercise / 100) * 7)
  const getDietQuality = () => {
    const v = sliders.diet
    if (v < 25) return 'Poor'
    if (v < 50) return 'Fair'
    if (v < 75) return 'Good'
    return 'Excellent'
  }
  const getSmokingStatus = () => {
    if (sliders.smoking < 25) return 'Never'
    if (sliders.smoking < 50) return 'Former'
    if (sliders.smoking < 75) return 'Current'
    return 'Current'
  }
  const isOnStatin = () => sliders.statin > 50

  const handleSimulate = async () => {
    if (!patient) {
      setError('No patient data found. Please fill in Patient Data first.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await simulateRisk({
        // Current patient data
        name: patient.name,
        age: patient.age,
        sex: patient.sex,
        bp_systolic: patient.bp_systolic,
        bp_diastolic: patient.bp_diastolic,
        total_cholesterol: patient.total_cholesterol,
        hdl: patient.hdl,
        ldl: patient.ldl,
        smoking: patient.smoking,
        exercise_days: patient.exercise_days,
        diet_quality: patient.diet_quality,
        location: patient.location,
        bmi: patient.bmi,
        heart_rate: patient.heart_rate,
        glucose: patient.glucose,
        // Intervention values from sliders
        new_exercise_days: getExerciseDays(),
        new_diet_quality: getDietQuality(),
        quit_smoking: getSmokingStatus() === 'Never',
        on_statin: isOnStatin(),
      })
      setResult(res)
    } catch (e) {
      setError('Simulation failed: ' + e.message)
    } finally {
      setLoading(false)
    }
  }

  // Build trajectory chart from real data
  const buildTrajectoryChart = () => {
    const currentTraj = result?.current_trajectory || [25,24,23,22,21,20,19,18,17,16,15]
    const interventionTraj = result?.intervention_trajectory || [25,22,19,17,15,14,13,12,11,10,9]
    const labels = ['Now','Yr 1','Yr 2','Yr 3','Yr 4','Yr 5','Yr 6','Yr 7','Yr 8','Yr 9','Yr 10']

    return {
      labels,
      datasets: [
        {
          label: 'Current Path',
          data: currentTraj,
          backgroundColor: '#FCA5A5',
          borderRadius: 4,
          barThickness: 18,
        },
        {
          label: 'With Changes',
          data: interventionTraj,
          backgroundColor: '#6EE7B7',
          borderRadius: 4,
          barThickness: 18,
        },
      ],
    }
  }

  const trajectoryOptions = {
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: { boxWidth: 12, font: { size: 11 } },
      },
    },
    scales: {
      x: { grid: { display: false }, ticks: { font: { size: 10 } } },
      y: {
        min: 0,
        max: Math.max(40, result?.current_risk ? result.current_risk + 10 : 40),
        ticks: { stepSize: 5 },
        grid: { color: '#F3F4F6' },
      },
    },
  }

  const getRiskColor = (risk) => {
    if (!risk) return '#6B7280'
    if (risk < 10) return '#22C55E'
    if (risk < 20) return '#F97316'
    return '#EF4444'
  }

  const sliderItems = [
    {
      key: 'exercise',
      label: 'Exercise Days per Week',
      icon: '🏃',
      iconBg: '#EEF2FF',
      displayValue: `${getExerciseDays()} days/week`,
      marks: ['0 days', '2 days', '5 days', '7 days'],
    },
    {
      key: 'diet',
      label: 'Diet Quality',
      icon: '🥗',
      iconBg: '#F0FDF4',
      displayValue: getDietQuality(),
      marks: ['Poor', 'Fair', 'Good', 'Excellent'],
    },
    {
      key: 'smoking',
      label: 'Smoking Status',
      icon: '🚭',
      iconBg: '#FFF1F2',
      displayValue: getSmokingStatus(),
      marks: ['Never', 'Former', 'Occasional', 'Daily'],
    },
    {
      key: 'statin',
      label: 'On Statin Medication',
      icon: '💊',
      iconBg: '#F5F3FF',
      displayValue: isOnStatin() ? 'Yes' : 'No',
      marks: ['No', '', '', 'Yes'],
    },
  ]

  return (
    <div className="simulation-screen">

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
          <button className="sidebar-item" onClick={() => handleNavigate('/')}>
            <span className="sidebar-icon">🚪</span><span>Log out</span>
          </button>
        </div>
      </div>

      {/* Main */}
      <div className="simulation-main">
        <button className="hamburger" onClick={() => setMenuOpen(!menuOpen)}>
          <span></span><span></span><span></span>
        </button>

        <div className="simulation-content">

          {/* Error */}
          {error && (
            <div style={{ background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '10px', padding: '12px 16px', marginBottom: '16px', color: '#DC2626', fontSize: '14px' }}>
              ⚠️ {error}
            </div>
          )}

          {/* Top Row */}
          <div className="sim-top-row">

            {/* Left — Sliders */}
            <div className="sim-card">
              <div className="sim-card-header">
                <h3 className="sim-card-title">Personalised Risk Forecast</h3>
                <p style={{ fontSize: '12px', color: '#6B7280' }}>
                  {patient ? `Based on ${patient.name || 'your'} profile` : 'Loading...'}
                </p>
              </div>

              <div className="sliders-list">
                {sliderItems.map((item) => (
                  <div className="slider-item" key={item.key}>
                    <div className="slider-label-row">
                      <span className="slider-label">{item.label}</span>
                      <span style={{
                        fontSize: '12px',
                        fontWeight: 600,
                        color: '#1e3a5f',
                        background: '#EFF6FF',
                        padding: '2px 8px',
                        borderRadius: '10px',
                      }}>
                        {item.displayValue}
                      </span>
                    </div>
                    <div className="slider-row">
                      <div className="slider-icon-box" style={{ background: item.iconBg }}>
                        {item.icon}
                      </div>
                      <div className="slider-track-wrapper">
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={sliders[item.key]}
                          onChange={(e) => handleSlider(item.key, e.target.value)}
                          className="slider"
                        />
                        <div className="slider-marks">
                          {item.marks.map((mark, i) => (
                            <span key={i}>{mark}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Simulate Button */}
              <button
                onClick={handleSimulate}
                disabled={loading}
                style={{
                  width: '100%',
                  marginTop: '20px',
                  background: loading ? '#9CA3AF' : 'linear-gradient(135deg, #1e3a5f, #2d5986)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '12px',
                  padding: '14px',
                  fontWeight: 700,
                  fontSize: '15px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                }}
              >
                {loading ? '⏳ Simulating...' : '⚡ Run Simulation'}
              </button>
            </div>

            {/* Right — Output */}
            <div className="sim-card output-card">
              <div className="sim-card-header">
                <h3 className="sim-card-title">Output</h3>
              </div>

              {!result ? (
                <div style={{ textAlign: 'center', padding: '40px 20px', color: '#9CA3AF' }}>
                  <div style={{ fontSize: '40px', marginBottom: '12px' }}>⚡</div>
                  <p style={{ fontSize: '14px' }}>
                    Adjust the sliders to your target lifestyle, then click Run Simulation to see your projected risk.
                  </p>
                </div>
              ) : (
                <>
                  <p className="output-label">Projected Risk with Changes</p>
                  <p className="output-percent" style={{ color: getRiskColor(result.intervention_risk) }}>
                    {result.intervention_risk?.toFixed(1)}%
                  </p>
                  <p className="output-sub">
                    Down from your current {result.current_risk?.toFixed(1)}% risk.
                  </p>

                  <div className="output-divider" />

                  <h4 className="output-section-title">Improvement Summary</h4>
                  <div className="improvement-row">
                    <span className="improvement-label">Absolute Reduction</span>
                    <span className="badge green">
                      -{(result.current_risk - result.intervention_risk).toFixed(1)}%
                    </span>
                  </div>
                  <div className="improvement-row">
                    <span className="improvement-label">Relative Reduction</span>
                    <span className="badge green">
                      -{result.risk_reduction_percent?.toFixed(1)}%
                    </span>
                  </div>
                  <div className="improvement-row">
                    <span className="improvement-label">Projected Category</span>
                    <span className="badge orange">
                      {result.intervention_risk < 10 ? 'Low' :
                       result.intervention_risk < 20 ? 'Moderate' : 'High'}
                    </span>
                  </div>

                  <div className="output-divider" />

                  <h4 className="output-section-title">What Changed</h4>
                  {getExerciseDays() > (patient?.exercise_days || 0) && (
                    <p className="detail-text">
                      <span className="detail-blue">Exercise</span> increased from {patient?.exercise_days || 0} to {getExerciseDays()} days/week
                    </p>
                  )}
                  {getDietQuality() !== patient?.diet_quality && (
                    <p className="detail-text">
                      <span className="detail-green">Diet</span> improved from {patient?.diet_quality || 'Fair'} to {getDietQuality()}
                    </p>
                  )}
                  {getSmokingStatus() === 'Never' && patient?.smoking === 'Current' && (
                    <p className="detail-text">
                      <span className="detail-red">Smoking</span> stopped — significant risk reduction
                    </p>
                  )}
                  {isOnStatin() && (
                    <p className="detail-text">
                      <span className="detail-purple">Statin</span> medication added — reduces LDL and CVD risk
                    </p>
                  )}
                </>
              )}

              {/* Next step button */}
              <div style={{ marginTop: '24px' }}>
                <button
                  onClick={() => navigate('/medications')}
                  style={{
                    width: '100%',
                    background: '#F0FDF4',
                    color: '#15803D',
                    border: '1px solid #86EFAC',
                    borderRadius: '12px',
                    padding: '12px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    fontSize: '14px',
                  }}
                >
                  💊 Next: View Medications →
                </button>
              </div>
            </div>

          </div>

          {/* Risk Trajectory Chart */}
          <div className="sim-card trajectory-card">
            <h3 className="sim-card-title">
              Risk Trajectory (10-Year Projection)
              {result && <span style={{ fontSize: '13px', color: '#6B7280', fontWeight: 400, marginLeft: '8px' }}>
                Red = current path · Green = with your changes
              </span>}
            </h3>
            <div className="trajectory-chart-wrapper">
              <Bar data={buildTrajectoryChart()} options={trajectoryOptions} />
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}

export default Simulation