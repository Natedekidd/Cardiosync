import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { savePatient, uploadVCF, getUser, getPatient } from '../api'
import '../css/patientdata.css'

const navItems = [
  { icon: '🏠', label: 'Dashboard', path: '/dashboard' },
  { icon: '👤', label: 'Patient Data', path: '/patient' },
  { icon: '📈', label: 'Risk Analysis', path: '/risk' },
  { icon: '⏱️', label: 'Simulation', path: '/simulation' },
  { icon: '💊', label: 'Medications', path: '/medications' },
  { icon: '📋', label: 'Action Plan', path: '/action' },
]

function PatientData() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [fileName, setFileName] = useState(null)
  const [vcfFile, setVcfFile] = useState(null)
  const [modal, setModal] = useState(null)
  const [agreed, setAgreed] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [submitSuccess, setSubmitSuccess] = useState('')
  const navigate = useNavigate()

  // Auto-fill from signup data and existing patient profile
  useEffect(() => {
    const user = getUser()
    if (user) {
      setForm(prev => ({
        ...prev,
        name: prev.name || user.full_name || '',
        email: prev.email || user.email || '',
      }))
    }
    // Also load existing patient data if already saved
    getPatient().then(res => {
      if (res.patient) {
        const p = res.patient
        setForm(prev => ({
          ...prev,
          name: p.name || prev.name,
          age: p.age || prev.age,
          sex: p.sex || prev.sex,
          height: p.height || prev.height,
          weight: p.weight || prev.weight,
          email: p.email || prev.email,
          phone: p.phone || prev.phone,
          location: p.location || prev.location,
          smoking: p.smoking === 'Never' ? 'never' : p.smoking === 'Former' ? 'former' : p.smoking === 'Current' ? 'current-daily' : prev.smoking,
          blood_pressure: p.bp_systolic && p.bp_diastolic ? `${p.bp_systolic}/${p.bp_diastolic}` : prev.blood_pressure,
          heart_rate: p.heart_rate || prev.heart_rate,
          blood_sugar: p.glucose || prev.blood_sugar,
          exercise_days: p.exercise_days ?? prev.exercise_days,
          diet_quality: p.diet_quality || prev.diet_quality,
        }))
      }
    }).catch(() => {})
  }, [])

  // ── Form state ─────────────────────────────────────────────────────────
  const [form, setForm] = useState({
    // Patient info
    name: '',
    sex: '',
    age: '',
    height: '',
    weight: '',
    // Contact
    email: '',
    phone: '',
    emergency_contact: '',
    // Medical history
    hypertension: '',
    diabetes: '',
    high_cholesterol: '',
    heart_disease: '',
    stroke: '',
    kidney_disease: '',
    thyroid: '',
    smoking: '',
    // Vitals
    blood_pressure: '',
    heart_rate: '',
    blood_sugar: '',
    // Lifestyle (derived)
    exercise_days: 3,
    diet_quality: 'Fair',
    location: '',
  })

  const set = (field) => (e) => setForm(prev => ({ ...prev, [field]: e.target.value }))

  const handleNavigate = (path) => {
    setMenuOpen(false)
    setTimeout(() => navigate(path), 100)
  }

  const handleFile = (e) => {
    const file = e.target.files[0]
    if (file) {
      setFileName(file.name)
      setVcfFile(file)
      setModal('consent')
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) {
      setFileName(file.name)
      setVcfFile(file)
      setModal('consent')
    }
  }

  const handleConsentContinue = async () => {
    if (!agreed) return
    setModal('uploading')
    try {
      await uploadVCF(vcfFile)
      setModal('success')
    } catch (e) {
      setModal(null)
      setSubmitError('VCF upload failed: ' + e.message)
    }
  }

  // ── Parse BP string "120/80" into systolic/diastolic ──────────────────
  const parseBP = (bp) => {
    const parts = bp.split('/')
    if (parts.length === 2) {
      return {
        bp_systolic: parseInt(parts[0]) || 120,
        bp_diastolic: parseInt(parts[1]) || 80,
      }
    }
    return { bp_systolic: 120, bp_diastolic: 80 }
  }

  // ── Calculate BMI from height/weight ──────────────────────────────────
  const calcBMI = (height, weight) => {
    const h = parseFloat(height)
    const w = parseFloat(weight)
    if (!h || !w) return null
    // Assume height in cm, weight in kg
    const hm = h > 10 ? h / 100 : h
    return parseFloat((w / (hm * hm)).toFixed(1))
  }

  // ── Map smoking select to API values ──────────────────────────────────
  const mapSmoking = (val) => {
    if (val.includes('never')) return 'Never'
    if (val.includes('former')) return 'Former'
    if (val.includes('current')) return 'Current'
    return 'Never'
  }

  // ── Submit ─────────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    setSubmitError('')
    setSubmitSuccess('')

    // Basic validation
    if (!form.name || !form.age || !form.sex) {
      setSubmitError('Please fill in at least your name, age, and sex.')
      return
    }
    if (!form.blood_pressure) {
      setSubmitError('Please enter your blood pressure (e.g. 120/80).')
      return
    }

    setSubmitting(true)
    try {
      const { bp_systolic, bp_diastolic } = parseBP(form.blood_pressure)
      const bmi = calcBMI(form.height, form.weight)
      const heartRate = parseFloat(form.heart_rate) || null
      const glucose = parseFloat(form.blood_sugar) || null

      // Derive LDL/cholesterol estimates if not entered
      // (real values would come from blood tests — using safe defaults)
      const hasHighCholesterol = form.high_cholesterol === 'yes'
      const hasDiabetes = form.diabetes && form.diabetes !== 'no'
      const hasStroke = form.stroke && form.stroke !== 'no'
      const hasHypertension = form.hypertension === 'yes'

      const payload = {
        name: form.name,
        age: parseInt(form.age),
        sex: form.sex === 'male' || form.sex.toLowerCase() === 'male' ? 'Male' : 'Female',
        bp_systolic,
        bp_diastolic,
        total_cholesterol: hasHighCholesterol ? 240 : 200,
        hdl: 45,
        ldl: hasHighCholesterol ? 160 : 120,
        smoking: mapSmoking(form.smoking || 'never'),
        exercise_days: parseInt(form.exercise_days),
        diet_quality: form.diet_quality,
        location: form.location || null,
        bmi,
        heart_rate: heartRate,
        glucose,
        cigs_per_day: form.smoking.includes('daily') ? 20 : form.smoking.includes('occasional') ? 5 : 0,
        bp_meds: hasHypertension ? 1 : 0,
        prevalent_stroke: hasStroke ? 1 : 0,
        prevalent_hyp: hasHypertension || bp_systolic >= 140 ? 1 : 0,
        diabetes: hasDiabetes ? 1 : 0,
        education: 2,
      }

      await savePatient(payload)
      setSubmitSuccess('✅ Profile saved! Redirecting to Risk Analysis...')
      setTimeout(() => navigate('/risk'), 1500)
    } catch (e) {
      setSubmitError('Failed to save: ' + e.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="patient-screen">

      {/* DELETE MODAL */}
      {modal === 'delete' && (
        <div className="modal-overlay">
          <div className="modal">
            <button className="modal-close" onClick={() => setModal(null)}>✕</button>
            <div className="modal-icon blue">✔</div>
            <h3 className="modal-title">Delete Profile</h3>
            <p className="modal-text">Are you sure you want to delete your profile information?</p>
            <button className="modal-btn" onClick={() => setModal(null)}>Delete</button>
          </div>
        </div>
      )}

      {/* CONSENT MODAL */}
      {modal === 'consent' && (
        <div className="modal-overlay">
          <div className="modal">
            <button className="modal-close" onClick={() => setModal(null)}>✕</button>
            <h3 className="modal-title left">Consent to Process Genetic Data</h3>
            <p className="modal-body-text">
              By uploading your genomic information, you consent to its processing solely for the
              purpose of analyzing medication response and cardiovascular risk.
            </p>
            <p className="modal-body-text">
              We process this data to provide personalized predictions and recommendations, and it
              is stored securely with encryption. All data is automatically deleted after the
              analysis is complete, unless you explicitly choose to save it for future use.
            </p>
            <label className="modal-checkbox">
              <input
                type="checkbox"
                checked={agreed}
                onChange={(e) => setAgreed(e.target.checked)}
              />
              I understand and agree
            </label>
            <button
              className="modal-btn"
              onClick={handleConsentContinue}
              style={{ opacity: agreed ? 1 : 0.5 }}
            >
              Continue
            </button>
          </div>
        </div>
      )}

      {/* UPLOADING MODAL */}
      {modal === 'uploading' && (
        <div className="modal-overlay">
          <div className="modal">
            <h3 className="modal-title left">Uploading VCF File...</h3>
            <div className="upload-progress-item">
              <div className="upload-progress-icon">VCF</div>
              <div className="upload-progress-info">
                <p className="upload-progress-name">{fileName}</p>
                <div className="progress-bar-track">
                  <div className="progress-bar-fill" style={{ width: '75%' }}></div>
                </div>
                <div className="upload-progress-meta">
                  <span>Analysing variants...</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* SUCCESS MODAL */}
      {modal === 'success' && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-icon blue">✔</div>
            <h3 className="modal-title">Upload Successful</h3>
            <p className="modal-text">
              Your genomic file has been analysed. Personalised recommendations are now available.
            </p>
            <button className="modal-btn" onClick={() => setModal(null)}>Continue</button>
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
          <button className="sidebar-item" onClick={() => handleNavigate('/help')}>
            <span className="sidebar-icon">❓</span><span>Help</span>
          </button>
          <button className="sidebar-item" onClick={() => handleNavigate('/')}>
            <span className="sidebar-icon">🚪</span><span>Log out</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="patient-main">
        <button className="hamburger" onClick={() => setMenuOpen(!menuOpen)}>
          <span></span><span></span><span></span>
        </button>

        <div className="patient-content">
          <h2 className="page-title">Personal details</h2>

          {/* Status messages */}
          {submitError && (
            <div style={{ background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: '10px', padding: '12px 16px', marginBottom: '16px', color: '#DC2626', fontSize: '14px' }}>
              ⚠️ {submitError}
            </div>
          )}
          {submitSuccess && (
            <div style={{ background: '#F0FDF4', border: '1px solid #86EFAC', borderRadius: '10px', padding: '12px 16px', marginBottom: '16px', color: '#15803D', fontSize: '14px' }}>
              {submitSuccess}
            </div>
          )}

          {/* Patient Information */}
          <div className="form-section">
            <h3 className="form-section-title">Patient Information</h3>
            <p className="form-section-sub">This information helps calibrate risk models and reference ranges</p>
            <div className="form-row two-col">
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input type="text" className="form-input" value={form.name} onChange={set('name')} />
              </div>
              <div className="form-group">
                <label className="form-label">Sex</label>
                <select className="form-select" value={form.sex} onChange={set('sex')}>
                  <option value="">Select</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </select>
              </div>
            </div>
            <div className="form-row three-col">
              <div className="form-group">
                <label className="form-label">Age</label>
                <input type="number" className="form-input" value={form.age} onChange={set('age')} />
              </div>
              <div className="form-group">
                <label className="form-label">Height (cm)</label>
                <input type="text" className="form-input" value={form.height} onChange={set('height')} placeholder="e.g. 175" />
              </div>
              <div className="form-group">
                <label className="form-label">Weight (kg)</label>
                <input type="text" className="form-input" value={form.weight} onChange={set('weight')} placeholder="e.g. 80" />
              </div>
            </div>
          </div>

          {/* Contact Information */}
          <div className="form-section">
            <h3 className="form-section-title">Contact Information</h3>
            <p className="form-section-sub">For notifications and follow ups</p>
            <div className="form-row two-col">
              <div className="form-group">
                <label className="form-label">Email</label>
                <input type="email" className="form-input" value={form.email} onChange={set('email')} />
              </div>
              <div className="form-group">
                <label className="form-label">Phone number</label>
                <input type="tel" className="form-input" value={form.phone} onChange={set('phone')} />
              </div>
            </div>
            <div className="form-row one-col">
              <div className="form-group">
                <label className="form-label">Location (City, Country)</label>
                <input type="text" className="form-input half" value={form.location} onChange={set('location')} placeholder="e.g. Lagos, Nigeria" />
              </div>
            </div>
          </div>

          {/* Medical History */}
          <div className="form-section">
            <h3 className="form-section-title">Medical History</h3>
            <p className="form-section-sub">Answer yes/no</p>
            <div className="form-row two-col">
              <div className="form-group">
                <label className="form-label">Hypertension</label>
                <select className="form-select" value={form.hypertension} onChange={set('hypertension')}>
                  <option value=""></option>
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Diabetes (Type 1/2)</label>
                <select className="form-select" value={form.diabetes} onChange={set('diabetes')}>
                  <option value=""></option>
                  <option value="yes-type1">Yes — Type 1</option>
                  <option value="yes-type2">Yes — Type 2</option>
                  <option value="yes-gestational">Yes — Gestational</option>
                  <option value="yes-notsure">Yes — Not sure of type</option>
                  <option value="no">No</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">High cholesterol</label>
                <select className="form-select" value={form.high_cholesterol} onChange={set('high_cholesterol')}>
                  <option value=""></option>
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Heart disease</label>
                <select className="form-select" value={form.heart_disease} onChange={set('heart_disease')}>
                  <option value=""></option>
                  <option value="yes-cad">Yes — Coronary Artery Disease</option>
                  <option value="yes-hf">Yes — Heart Failure</option>
                  <option value="yes-arrhythmia">Yes — Arrhythmia</option>
                  <option value="yes-congenital">Yes — Congenital Heart Condition</option>
                  <option value="yes-other">Yes — Other / Not sure</option>
                  <option value="no">No</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Stroke/TIA</label>
                <select className="form-select" value={form.stroke} onChange={set('stroke')}>
                  <option value=""></option>
                  <option value="yes-ischemic">Yes — Ischemic Stroke</option>
                  <option value="yes-hemorrhagic">Yes — Hemorrhagic Stroke</option>
                  <option value="yes-notsure">Yes — Not sure of type</option>
                  <option value="no">No</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Kidney disease</label>
                <select className="form-select" value={form.kidney_disease} onChange={set('kidney_disease')}>
                  <option value=""></option>
                  <option value="yes-ckd">Yes — Chronic Kidney Disease</option>
                  <option value="yes-stones">Yes — Kidney Stones</option>
                  <option value="yes-polycystic">Yes — Polycystic Kidney Disease</option>
                  <option value="yes-notsure">Yes — Not sure of type</option>
                  <option value="no">No</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Thyroid disorders</label>
                <select className="form-select" value={form.thyroid} onChange={set('thyroid')}>
                  <option value=""></option>
                  <option value="yes-hypo">Yes — Hypothyroidism</option>
                  <option value="yes-hyper">Yes — Hyperthyroidism</option>
                  <option value="yes-nodules">Yes — Thyroid nodules / goiter</option>
                  <option value="yes-notsure">Yes — Not sure of type</option>
                  <option value="no">No</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Smoking history</label>
                <select className="form-select" value={form.smoking} onChange={set('smoking')}>
                  <option value="never">Never smoked</option>
                  <option value="current-daily">Current smoker — daily</option>
                  <option value="current-occasional">Current smoker — occasional</option>
                  <option value="former">Former smoker</option>
                  <option value="secondhand">Exposure to secondhand smoke</option>
                </select>
              </div>
            </div>
          </div>

          {/* Vitals */}
          <div className="form-section">
            <div className="vitals-header">
              <div>
                <h3 className="form-section-title">Vitals</h3>
                <p className="form-section-sub">Add your vitals</p>
              </div>
              <button className="btn-sync">Sync with devices</button>
            </div>
            <div className="form-row two-col">
              <div className="form-group">
                <label className="form-label">Blood Pressure (Systolic/Diastolic)</label>
                <input type="text" className="form-input" placeholder="e.g. 120/80" value={form.blood_pressure} onChange={set('blood_pressure')} />
              </div>
              <div className="form-group">
                <label className="form-label">Heart Rate (Resting)</label>
                <input type="text" className="form-input" placeholder="e.g. 72" value={form.heart_rate} onChange={set('heart_rate')} />
              </div>
            </div>
            <div className="form-row one-col">
              <div className="form-group">
                <label className="form-label">Recent Blood Sugar / Glucose (mg/dL)</label>
                <input type="text" className="form-input half" placeholder="e.g. 95" value={form.blood_sugar} onChange={set('blood_sugar')} />
              </div>
            </div>
          </div>

          {/* Lifestyle */}
          <div className="form-section">
            <h3 className="form-section-title">Lifestyle</h3>
            <p className="form-section-sub">Helps the AI model personalise your risk score</p>
            <div className="form-row two-col">
              <div className="form-group">
                <label className="form-label">Exercise Days per Week</label>
                <select className="form-select" value={form.exercise_days} onChange={set('exercise_days')}>
                  {[0,1,2,3,4,5,6,7].map(d => (
                    <option key={d} value={d}>{d} day{d !== 1 ? 's' : ''}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Diet Quality</label>
                <select className="form-select" value={form.diet_quality} onChange={set('diet_quality')}>
                  <option value="Poor">Poor</option>
                  <option value="Fair">Fair</option>
                  <option value="Good">Good</option>
                  <option value="Excellent">Excellent</option>
                </select>
              </div>
            </div>
          </div>

          {/* Delete Profile */}
          <div className="delete-row">
            <button className="btn-delete" onClick={() => setModal('delete')}>
              Delete Profile
            </button>
          </div>

          {/* Upload Genomic Data */}
          <div className="upload-section">
            <h3 className="form-section-title">Upload Genomic Data (VCF) — Optional</h3>
            <p style={{ fontSize: '13px', color: '#6B7280', marginBottom: '12px' }}>
              Not required. Uploading a VCF file unlocks personalised pharmacogenomic recommendations.
            </p>
            <div
              className={`upload-area ${dragOver ? 'drag-over' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
            >
              <div className="upload-icon">🧬</div>
              {fileName ? (
                <p className="upload-text">✅ {fileName}</p>
              ) : (
                <>
                  <p className="upload-text">Choose a VCF file or drag & drop it here</p>
                  <p className="upload-hint">VCF format — Up to 50MB</p>
                </>
              )}
              <label className="btn-browse">
                Browse files
                <input type="file" hidden accept=".vcf,.txt" onChange={handleFile} />
              </label>
            </div>
          </div>

          {/* Submit */}
          <div className="submit-row">
            <button
              className="btn-submit"
              onClick={handleSubmit}
              disabled={submitting}
            >
              {submitting ? 'Saving...' : 'Submit & Analyse Risk'}
            </button>
          </div>

        </div>
      </div>
    </div>
  )
}

export default PatientData