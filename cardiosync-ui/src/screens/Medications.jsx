import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getPharmacogenomics, getPatient } from '../api'
import '../css/medications.css'

const navItems = [
  { icon: '🏠', label: 'Dashboard', path: '/dashboard' },
  { icon: '👤', label: 'Patient Data', path: '/patient' },
  { icon: '📈', label: 'Risk Analysis', path: '/risk' },
  { icon: '⏱️', label: 'Simulation', path: '/simulation' },
  { icon: '💊', label: 'Medications', path: '/medications' },
  { icon: '📋', label: 'Action Plan', path: '/action' },
]

// General cardiovascular drug guide shown when no VCF uploaded
const generalMeds = [
  {
    name: 'Atorvastatin',
    class: 'Statin (HMG-CoA reductase inhibitor)',
    dosage: '10–80 mg once daily',
    timing: 'Evening, with or without food',
    use: 'Lowers LDL cholesterol and reduces cardiovascular risk',
    sideEffects: 'Mild muscle aches, headache, GI discomfort',
    warning: 'Rare: severe muscle breakdown (rhabdomyolysis), liver injury',
    genetic: null,
    status: 'Common',
    color: 'optimal',
  },
  {
    name: 'Lisinopril',
    class: 'ACE Inhibitor',
    dosage: '5–40 mg once daily',
    timing: 'Morning, with or without food',
    use: 'Lowers blood pressure, protects kidneys',
    sideEffects: 'Dry cough, dizziness, elevated potassium',
    warning: 'Do not use in pregnancy. Monitor kidney function',
    genetic: null,
    status: 'Common',
    color: 'optimal',
  },
  {
    name: 'Metoprolol',
    class: 'Beta Blocker',
    dosage: '25–200 mg once or twice daily',
    timing: 'With meals',
    use: 'Reduces heart rate and blood pressure',
    sideEffects: 'Fatigue, cold hands/feet, dizziness',
    warning: 'Do not stop abruptly — taper gradually',
    genetic: null,
    status: 'Common',
    color: 'optimal',
  },
  {
    name: 'Amlodipine',
    class: 'Calcium Channel Blocker',
    dosage: '5–10 mg once daily',
    timing: 'Any time, consistent daily',
    use: 'Lowers blood pressure and treats angina',
    sideEffects: 'Ankle swelling, flushing, headache',
    warning: 'May interact with grapefruit juice',
    genetic: null,
    status: 'Common',
    color: 'optimal',
  },
  {
    name: 'Clopidogrel',
    class: 'Antiplatelet Agent',
    dosage: '75 mg once daily',
    timing: 'With or without food',
    use: 'Prevents blood clots, reduces heart attack/stroke risk',
    sideEffects: 'Bleeding, bruising, GI upset',
    warning: 'CYP2C19 poor metabolizers have reduced efficacy — genetic testing recommended',
    genetic: 'CYP2C19',
    status: 'Caution',
    color: 'caution',
  },
  {
    name: 'Warfarin',
    class: 'Anticoagulant',
    dosage: 'Individualised based on INR',
    timing: 'Same time daily',
    use: 'Prevents blood clots in high-risk patients',
    sideEffects: 'Bleeding risk, bruising',
    warning: 'CYP2C9 and VKORC1 variants affect dosing significantly — genetic testing strongly recommended',
    genetic: 'CYP2C9, VKORC1',
    status: 'Caution',
    color: 'caution',
  },
  {
    name: 'Losartan',
    class: 'ARB (Angiotensin Receptor Blocker)',
    dosage: '25–100 mg once daily',
    timing: 'Any time, consistent daily',
    use: 'Lowers blood pressure, protects kidneys in diabetes',
    sideEffects: 'Dizziness, elevated potassium',
    warning: 'Do not use in pregnancy',
    genetic: null,
    status: 'Common',
    color: 'optimal',
  },
]

const statusColors = {
  optimal: { bg: '#DCFCE7', color: '#15803D' },
  caution: { bg: '#FEF3C7', color: '#92400E' },
  avoid: { bg: '#FEE2E2', color: '#DC2626' },
  low: { bg: '#F3F4F6', color: '#6B7280' },
  high: { bg: '#DBEAFE', color: '#1D4ED8' },
  moderate: { bg: '#FEF3C7', color: '#92400E' },
}

function Medications() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [pharma, setPharma] = useState(null)
  const [patient, setPatient] = useState(null)
  const [selectedMed, setSelectedMed] = useState(null)
  const [hasVCF, setHasVCF] = useState(false)
  const navigate = useNavigate()

  const handleNavigate = (path) => {
    setMenuOpen(false)
    setTimeout(() => navigate(path), 100)
  }

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [patientRes, pharmaRes] = await Promise.all([
        getPatient(),
        getPharmacogenomics(),
      ])
      if (patientRes.patient) setPatient(patientRes.patient)

      // Check if VCF-based data is available
      if (pharmaRes && pharmaRes.recommendations) {
        setPharma(pharmaRes)
        setHasVCF(pharmaRes.vcf_based === true)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  // Build medication table — personalised if VCF, general otherwise
  const getMedTable = () => {
    if (hasVCF && pharma?.recommendations) {
      return pharma.recommendations.map(r => ({
        name: r.drug,
        genetic: r.gene || 'Normal',
        absolute: r.absolute_benefit || '—',
        relative: r.relative_benefit || '—',
        status: r.recommendation,
        color: r.recommendation === 'Recommended' ? 'optimal' :
               r.recommendation === 'Caution' ? 'caution' :
               r.recommendation === 'Avoid' ? 'avoid' : 'moderate',
        note: r.reason || '',
      }))
    }
    return generalMeds.map(m => ({
      name: m.name,
      genetic: m.genetic ? `⚠️ ${m.genetic}` : 'General population',
      absolute: '—',
      relative: '—',
      status: m.status,
      color: m.color,
      note: m.use,
    }))
  }

  const medTable = getMedTable()
  const displayMed = selectedMed !== null
    ? generalMeds.find(m => m.name === medTable[selectedMed]?.name) || generalMeds[0]
    : generalMeds[0]

  return (
    <div className="medications-screen">

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
      <div className="medications-main">
        <button className="hamburger" onClick={() => setMenuOpen(!menuOpen)}>
          <span></span><span></span><span></span>
        </button>

        <div className="medications-content">

          {/* VCF banner */}
          {!hasVCF && (
            <div style={{
              background: 'linear-gradient(135deg, #1e3a5f, #2d5986)',
              borderRadius: '14px',
              padding: '16px 20px',
              marginBottom: '20px',
              color: '#fff',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px',
            }}>
              <div>
                <p style={{ fontWeight: 700, fontSize: '14px', marginBottom: '4px' }}>
                  🧬 Unlock Personalised Recommendations
                </p>
                <p style={{ opacity: 0.8, fontSize: '12px' }}>
                  Upload your VCF file in Patient Data to get gene-specific drug guidance tailored to your genetic variants.
                </p>
              </div>
              <button
                onClick={() => navigate('/patient')}
                style={{
                  background: '#fff',
                  color: '#1e3a5f',
                  border: 'none',
                  borderRadius: '10px',
                  padding: '8px 16px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  fontSize: '13px',
                  whiteSpace: 'nowrap',
                }}
              >
                Upload VCF →
              </button>
            </div>
          )}

          {hasVCF && (
            <div style={{
              background: '#F0FDF4',
              border: '1px solid #86EFAC',
              borderRadius: '14px',
              padding: '14px 20px',
              marginBottom: '20px',
              color: '#15803D',
              fontSize: '14px',
              fontWeight: 600,
            }}>
              🧬 Showing personalised recommendations based on your genetic profile
            </div>
          )}

          {/* Table */}
          <div className="med-table-card">
            <h2 className="page-title">
              {hasVCF ? 'Personalised Medication Guide' : 'Cardiovascular Medication Guide'}
            </h2>
            <p style={{ fontSize: '13px', color: '#6B7280', marginBottom: '16px' }}>
              {hasVCF
                ? 'Based on your genetic variants — click a row for details'
                : 'General population guidance — click a row for full details. Upload VCF for personalised recommendations.'}
            </p>
            <div className="table-wrapper">
              <table className="med-table">
                <thead>
                  <tr>
                    <th>Medication</th>
                    <th>Genetic Consideration</th>
                    <th>Primary Use</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {medTable.map((med, i) => (
                    <tr
                      key={i}
                      onClick={() => setSelectedMed(i)}
                      style={{
                        cursor: 'pointer',
                        background: selectedMed === i ? '#EFF6FF' : 'transparent',
                        transition: 'background 0.2s',
                      }}
                    >
                      <td className="med-name-cell">💊 {med.name}</td>
                      <td className="med-genetic-cell" style={{ fontSize: '12px' }}>{med.genetic}</td>
                      <td style={{ fontSize: '12px', color: '#6B7280' }}>{med.note}</td>
                      <td>
                        <span style={{
                          background: statusColors[med.color]?.bg || '#F3F4F6',
                          color: statusColors[med.color]?.color || '#6B7280',
                          padding: '3px 10px',
                          borderRadius: '20px',
                          fontSize: '12px',
                          fontWeight: 600,
                        }}>
                          {med.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Detail cards */}
          <div className="med-detail-row">
            <div className="med-detail-card">
              <h3 className="detail-card-title">
                💊 {displayMed.name}
              </h3>
              <div className="detail-divider" />
              <div className="detail-info-list">
                <p className="detail-info-item">
                  <span className="detail-info-key">Drug Class:</span> {displayMed.class}
                </p>
                <p className="detail-info-item">
                  <span className="detail-info-key">Dosage:</span> {displayMed.dosage}
                </p>
                <p className="detail-info-item">
                  <span className="detail-info-key">Timing:</span> {displayMed.timing}
                </p>
                <p className="detail-info-item">
                  <span className="detail-info-key">Primary Use:</span> {displayMed.use}
                </p>
                {displayMed.genetic && (
                  <p className="detail-info-item" style={{ color: '#92400E', background: '#FEF3C7', padding: '8px', borderRadius: '8px' }}>
                    ⚠️ <span className="detail-info-key">Gene Alert:</span> {displayMed.genetic} variants may affect this drug
                  </p>
                )}
              </div>
            </div>

            <div className="med-detail-card">
              <h3 className="detail-card-title">Monitoring / Safety</h3>
              <div className="detail-divider" />
              <div className="monitoring-list">
                <p className="monitoring-item">
                  <span className="monitoring-key">Side Effects:</span> {displayMed.sideEffects}
                </p>
                <p className="monitoring-item" style={{ color: '#DC2626' }}>
                  <span className="monitoring-key">⚠️ Warning:</span> {displayMed.warning}
                </p>
              </div>
            </div>
          </div>

          {/* Bottom full width */}
          <div className="med-full-card">
            <div className="full-section">
              <h3 className="full-section-title">Important Note</h3>
              <div className="full-divider" />
              <p className="full-section-text">
                This information is for educational purposes only and is not a substitute for professional medical advice.
                Always consult your doctor or pharmacist before starting, stopping, or changing any medication.
              </p>
              {!hasVCF && (
                <p className="full-section-text" style={{ color: '#1D4ED8', marginTop: '8px' }}>
                  🧬 Upload your VCF file to see which of these medications are safe, require dose adjustment, or should be avoided based on YOUR specific genetic variants.
                </p>
              )}
            </div>
          </div>

          {/* Next step */}
          <div style={{ marginTop: '20px' }}>
            <button
              onClick={() => navigate('/action')}
              style={{
                width: '100%',
                background: 'linear-gradient(135deg, #1e3a5f, #2d5986)',
                color: '#fff',
                border: 'none',
                borderRadius: '12px',
                padding: '14px',
                fontWeight: 700,
                fontSize: '15px',
                cursor: 'pointer',
              }}
            >
              📋 Next: View Action Plan →
            </button>
          </div>

        </div>
      </div>
    </div>
  )
}

export default Medications