import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getPatient, getRiskHistory, sendMessage } from '../api'

const navItems = [
  { icon: '🏠', label: 'Dashboard', path: '/dashboard' },
  { icon: '👤', label: 'Patient Data', path: '/patient' },
  { icon: '📈', label: 'Risk Analysis', path: '/risk' },
  { icon: '⏱️', label: 'Simulation', path: '/simulation' },
  { icon: '💊', label: 'Medications', path: '/medications' },
  { icon: '📋', label: 'Action Plan', path: '/action' },
]

const priorityColor = {
  High: { bg: '#FEE2E2', color: '#DC2626', border: '#FCA5A5' },
  Medium: { bg: '#FEF3C7', color: '#92400E', border: '#FCD34D' },
  Low: { bg: '#DCFCE7', color: '#15803D', border: '#86EFAC' },
}

function ActionPlan() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [patient, setPatient] = useState(null)
  const [riskHistory, setRiskHistory] = useState([])
  const [phone, setPhone] = useState('')
  const [channel, setChannel] = useState('whatsapp')
  const [sending, setSending] = useState(false)
  const [sendSuccess, setSendSuccess] = useState('')
  const [sendError, setSendError] = useState('')
  const [hospitalModal, setHospitalModal] = useState(false)
  const [hospitalId, setHospitalId] = useState('')
  const [hospitalSending, setHospitalSending] = useState(false)
  const [hospitalSuccess, setHospitalSuccess] = useState('')
  const navigate = useNavigate()

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [patientRes, historyRes] = await Promise.all([
        getPatient(),
        getRiskHistory(),
      ])
      if (patientRes.patient) {
        console.log('PATIENT DATA:', patientRes.patient)
        setPatient(patientRes.patient)
      }
      if (historyRes.history) setRiskHistory(historyRes.history)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const handleNavigate = (path) => {
    setMenuOpen(false)
    setTimeout(() => navigate(path), 100)
  }

  const latestRisk = riskHistory.length > 0 ? riskHistory[0] : null
  const totalRisk = latestRisk?.total_risk || null
  const riskCategory = totalRisk
    ? totalRisk < 10 ? 'Low' : totalRisk < 20 ? 'Moderate' : totalRisk < 30 ? 'High' : 'Very High'
    : null

  const buildActionItems = () => {
    if (!patient) return []
    const actions = []
    if (patient.bp_systolic >= 140) {
      actions.push({
        priority: 'High', icon: '💊', title: 'Manage Blood Pressure',
        desc: `Your BP is ${patient.bp_systolic}/${patient.bp_diastolic} mmHg — above safe levels.`,
        steps: ['Schedule a doctor appointment this week', 'Reduce daily salt to under 5g', 'Monitor BP daily if possible'],
      })
    } else if (patient.bp_systolic >= 130) {
      actions.push({
        priority: 'Medium', icon: '💊', title: 'Monitor Blood Pressure',
        desc: `Your BP is slightly elevated at ${patient.bp_systolic}/${patient.bp_diastolic} mmHg.`,
        steps: ['Reduce salt and processed foods', 'Exercise 30 mins most days', 'Recheck in 4 weeks'],
      })
    }
    if (patient.smoking === 'Current') {
      actions.push({
        priority: 'High', icon: '🚭', title: 'Stop Smoking',
        desc: 'Quitting smoking can reduce your cardiovascular risk by up to 50% within 1 year.',
        steps: ['Talk to your doctor about cessation aids', 'Set a quit date this week', 'Remove cigarettes from your environment'],
      })
    }
    if ((patient.exercise_days || 0) < 3) {
      actions.push({
        priority: 'Medium', icon: '🏃', title: 'Increase Physical Activity',
        desc: `You exercise ${patient.exercise_days || 0} days/week. Target 150 minutes of moderate activity weekly.`,
        steps: ['Start with 20-minute walks 3x per week', 'Gradually increase to 5 days', 'Mix cardio and strength training'],
      })
    }
    if (patient.diet_quality === 'Poor' || patient.diet_quality === 'Fair') {
      actions.push({
        priority: 'Medium', icon: '🥗', title: 'Improve Diet Quality',
        desc: `Your diet is "${patient.diet_quality}". A heart-healthy diet significantly reduces cardiovascular risk.`,
        steps: ['5 portions of fruits and vegetables daily', 'Replace refined carbs with whole grains', 'Reduce red meat and fried foods'],
      })
    }
    if (patient.ldl > 160) {
      actions.push({
        priority: 'High', icon: '🧪', title: 'Address High LDL Cholesterol',
        desc: `Your LDL is ${patient.ldl} mg/dL — above optimal levels.`,
        steps: ['Reduce saturated fats in diet', 'Ask doctor about statin therapy', 'Recheck cholesterol in 3 months'],
      })
    }
    actions.push({
      priority: 'Low', icon: '🩺', title: 'Schedule Regular Checkups',
      desc: 'Regular monitoring helps catch changes early and keeps your care plan up to date.',
      steps: ['Annual cardiovascular screening', 'BP and cholesterol check every 6 months', 'Update CardioSync profile after each visit'],
    })
    return actions
  }

  const actionItems = buildActionItems()

  // ── PDF Download via jsPDF ────────────────────────────────────────────
  const handleDownloadPDF = async () => {
    if (!window.jspdf) {
      await new Promise((resolve, reject) => {
        const script = document.createElement('script')
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js'
        script.onload = resolve
        script.onerror = reject
        document.head.appendChild(script)
      })
    }

    const { jsPDF } = window.jspdf
    const doc = new jsPDF()
    const pageWidth = doc.internal.pageSize.getWidth()
    const margin = 20
    let y = 20

    const addText = (text, size = 11, bold = false, color = [30, 30, 30]) => {
      doc.setFontSize(size)
      doc.setFont('helvetica', bold ? 'bold' : 'normal')
      doc.setTextColor(...color)
      const lines = doc.splitTextToSize(String(text), pageWidth - margin * 2)
      lines.forEach(line => {
        if (y > 275) { doc.addPage(); y = 20 }
        doc.text(line, margin, y)
        y += size * 0.45 + 2
      })
      y += 1
    }

    const addDivider = (color = [200, 200, 200]) => {
      if (y > 275) { doc.addPage(); y = 20 }
      doc.setDrawColor(...color)
      doc.line(margin, y, pageWidth - margin, y)
      y += 6
    }

    doc.setFillColor(30, 58, 95)
    doc.rect(0, 0, pageWidth, 42, 'F')
    doc.setFontSize(22)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(255, 255, 255)
    doc.text('CardioSync', margin, 18)
    doc.setFontSize(11)
    doc.setFont('helvetica', 'normal')
    doc.text('Precision Cardiovascular Risk Report', margin, 28)
    doc.text(`Generated: ${new Date().toLocaleDateString('en-GB')}`, margin, 36)
    y = 54

    addText('PATIENT INFORMATION', 13, true, [30, 58, 95])
    addDivider([30, 58, 95])
    addText(`Name: ${patient?.full_name || 'N/A'}`)
    addText(`Age: ${patient?.age || 'N/A'}   |   Sex: ${patient?.sex || 'N/A'}`)
    addText(`Blood Pressure: ${patient?.bp_systolic || 'N/A'}/${patient?.bp_diastolic || 'N/A'} mmHg`)
    addText(`Smoking: ${patient?.smoking || 'N/A'}   |   Exercise: ${patient?.exercise_days || 0} days/week`)
    addText(`Diet Quality: ${patient?.diet_quality || 'N/A'}`)
    y += 4

    addText('RISK SUMMARY', 13, true, [30, 58, 95])
    addDivider([30, 58, 95])
    if (totalRisk) {
      const rc = totalRisk < 10 ? [21, 128, 61] : totalRisk < 20 ? [146, 64, 14] : [220, 38, 38]
      addText(`10-Year Cardiovascular Risk: ${totalRisk.toFixed(1)}%`, 15, true, rc)
      addText(`Risk Category: ${riskCategory}`, 12, false, rc)
    } else {
      addText('No risk assessment completed yet.')
    }
    y += 4

    addText('ACTION PLAN', 13, true, [30, 58, 95])
    addDivider([30, 58, 95])
    actionItems.forEach((item, i) => {
      const pc = item.priority === 'High' ? [220, 38, 38] : item.priority === 'Medium' ? [146, 64, 14] : [21, 128, 61]
      addText(`${i + 1}. ${item.title}  [${item.priority} Priority]`, 12, true, pc)
      addText(item.desc, 10, false, [75, 85, 99])
      item.steps.forEach((step, j) => addText(`   ${j + 1}. ${step}`, 10))
      y += 3
    })

    y += 4
    addDivider()
    addText('DISCLAIMER', 10, true, [107, 114, 128])
    addText(
      'This report is generated by CardioSync for informational purposes only and is not a medical diagnosis. Always consult a qualified healthcare professional before making any health decisions.',
      9, false, [107, 114, 128]
    )

    const filename = `CardioSync_Report_${(patient?.full_name || 'Patient').replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`
    doc.save(filename)
  }

  // ── Hospital Send ─────────────────────────────────────────────────────
  const handleHospitalSend = () => {
    if (!hospitalId) return
    setHospitalSending(true)
    setTimeout(() => {
      setHospitalSending(false)
      setHospitalSuccess(`Report successfully transmitted to ${hospitalId}`)
    }, 2500)
  }

  // ── Send WhatsApp/Email ───────────────────────────────────────────────
  const handleSend = async () => {
    setSendError('')
    setSendSuccess('')
    if (!phone) { setSendError(channel === 'whatsapp' ? 'Please enter a phone number' : 'Please enter an email address'); return }
    if (!totalRisk) { setSendError('Please complete a risk assessment first'); return }
    setSending(true)
    try {
      if (channel === 'whatsapp') {
        await sendMessage({
          phone_number: phone,
          channel: 'whatsapp',
          patient_name: patient?.full_name || 'Patient',
          total_risk: totalRisk,
          risk_category: riskCategory,
          recommendations: actionItems.slice(0, 3).map(a => a.title),
        })
        setSendSuccess(`Report sent via WhatsApp to ${phone}!`)
      } else {
        if (!window.emailjs) {
          await new Promise((resolve, reject) => {
            const script = document.createElement('script')
            script.src = 'https://cdn.jsdelivr.net/npm/@emailjs/browser@3/dist/email.min.js'
            script.onload = resolve
            script.onerror = reject
            document.head.appendChild(script)
          })
          window.emailjs.init(import.meta.env.VITE_EMAILJS_PUBLIC_KEY)
        }
        await window.emailjs.send(import.meta.env.VITE_EMAILJS_SERVICE_ID, import.meta.env.VITE_EMAILJS_TEMPLATE_ID, {
          patient_name: patient?.full_name || 'Patient',
          total_risk: `${totalRisk.toFixed(1)}%`,
          risk_category: riskCategory,
          recommendations: actionItems.slice(0, 3).map((a, i) => `${i + 1}. ${a.title}`).join('\n'),
          email: phone,
          name: patient?.full_name || 'Patient',
        })
        setSendSuccess(`Report sent to ${phone}!`)
      }
    } catch (e) {
      setSendError('Send failed: ' + e.message)
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="dashboard-screen">

      {/* Hospital Modal */}
      {hospitalModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          zIndex: 999, display: 'flex', justifyContent: 'center', alignItems: 'center',
        }}>
          <div style={{
            background: '#fff', borderRadius: '16px', padding: '28px 24px',
            width: '90%', maxWidth: '400px', display: 'flex', flexDirection: 'column', gap: '14px',
          }}>
            <h3 style={{ fontWeight: 700, fontSize: '16px', margin: 0 }}>🏥 Send to Hospital System</h3>
            <p style={{ fontSize: '13px', color: '#6B7280', margin: 0, lineHeight: 1.6 }}>
              Enter your hospital's FHIR endpoint or patient portal ID to transmit this report directly to your care team.
            </p>
            <input
              type="text"
              placeholder="Hospital ID or Endpoint URL"
              value={hospitalId}
              onChange={e => setHospitalId(e.target.value)}
              style={{
                border: '1.5px solid #E5E7EB', borderRadius: '8px',
                padding: '10px 14px', fontSize: '14px', outline: 'none', width: '100%',
              }}
            />
            <button
              onClick={handleHospitalSend}
              disabled={hospitalSending}
              style={{
                background: hospitalSending ? '#9CA3AF' : '#1e3a5f',
                color: '#fff', border: 'none', borderRadius: '10px',
                padding: '12px', fontWeight: 700,
                cursor: hospitalSending ? 'not-allowed' : 'pointer', fontSize: '14px',
              }}
            >
              {hospitalSending ? '📡 Transmitting...' : '📡 Transmit Report'}
            </button>
            {hospitalSuccess && (
              <p style={{ color: '#15803D', fontSize: '13px', margin: 0 }}>✅ {hospitalSuccess}</p>
            )}
            <button
              onClick={() => { setHospitalModal(false); setHospitalSuccess(''); setHospitalId('') }}
              style={{ background: 'none', border: 'none', color: '#9CA3AF', cursor: 'pointer', fontSize: '13px' }}
            >
              Cancel
            </button>
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

      <div className="dashboard-main">
        <button className="hamburger" onClick={() => setMenuOpen(!menuOpen)}>
          <span></span><span></span><span></span>
        </button>

        <div className="dashboard-content">
          <h2 style={{ fontSize: '22px', fontWeight: 700, marginBottom: '20px' }}>📋 Action Plan</h2>

          {/* Risk hero */}
          {totalRisk && (
            <div style={{
              background: 'linear-gradient(135deg, #1e3a5f, #2d5986)',
              borderRadius: '16px', padding: '24px', marginBottom: '24px', color: '#fff',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px',
            }}>
              <div>
                <p style={{ opacity: 0.8, fontSize: '13px', marginBottom: '4px' }}>
                  {patient?.full_name || 'Your'}'s Cardiovascular Risk
                </p>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px' }}>
                  <span style={{ fontSize: '48px', fontWeight: 800, lineHeight: 1 }}>{totalRisk.toFixed(1)}%</span>
                  <span style={{
                    background: riskCategory === 'Low' ? '#22C55E' : riskCategory === 'Moderate' ? '#F97316' : '#EF4444',
                    padding: '4px 12px', borderRadius: '20px', fontSize: '13px', fontWeight: 600,
                  }}>{riskCategory}</span>
                </div>
                <p style={{ opacity: 0.7, fontSize: '13px', marginTop: '6px' }}>
                  {actionItems.length} actions recommended
                </p>
              </div>
              <button onClick={handleDownloadPDF} style={{
                background: '#fff', color: '#1e3a5f', border: 'none',
                borderRadius: '12px', padding: '12px 20px', fontWeight: 700, cursor: 'pointer', fontSize: '14px',
              }}>
                ⬇️ Download PDF
              </button>
            </div>
          )}

          {/* No risk */}
          {!loading && !totalRisk && (
            <div style={{ background: '#FEF3C7', border: '1px solid #FCD34D', borderRadius: '12px', padding: '16px 20px', marginBottom: '20px', color: '#92400E' }}>
              ⚠️ No risk assessment found.{' '}
              <span onClick={() => navigate('/risk')} style={{ textDecoration: 'underline', cursor: 'pointer', fontWeight: 600 }}>
                Run a Risk Analysis first →
              </span>
            </div>
          )}

          {/* Action items */}
          <div style={{ marginBottom: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px' }}>🎯 Recommended Actions</h3>
            {loading ? (
              <p style={{ color: '#9CA3AF', fontSize: '14px' }}>Loading your action plan...</p>
            ) : actionItems.map((item, i) => (
              <div key={i} style={{
                background: '#fff', borderRadius: '14px', padding: '18px', marginBottom: '12px',
                boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
                borderLeft: `4px solid ${priorityColor[item.priority]?.border}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '22px' }}>{item.icon}</span>
                    <p style={{ fontWeight: 700, fontSize: '15px', margin: 0 }}>{item.title}</p>
                  </div>
                  <span style={{
                    background: priorityColor[item.priority]?.bg,
                    color: priorityColor[item.priority]?.color,
                    padding: '3px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: 600, whiteSpace: 'nowrap',
                  }}>{item.priority} Priority</span>
                </div>
                <p style={{ fontSize: '13px', color: '#6B7280', marginBottom: '12px', lineHeight: 1.5 }}>{item.desc}</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {item.steps.map((step, j) => (
                    <div key={j} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                      <span style={{
                        background: '#EFF6FF', color: '#3B82F6', borderRadius: '50%',
                        width: '20px', height: '20px', display: 'flex', alignItems: 'center',
                        justifyContent: 'center', fontSize: '11px', fontWeight: 700, flexShrink: 0, marginTop: '1px',
                      }}>{j + 1}</span>
                      <p style={{ fontSize: '13px', color: '#374151', margin: 0, lineHeight: 1.5 }}>{step}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Send report */}
          <div style={{ background: '#fff', borderRadius: '16px', padding: '24px', boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '6px' }}>📱 Send Report to Phone</h3>
            <p style={{ fontSize: '13px', color: '#6B7280', marginBottom: '16px' }}>
              Send your risk summary via WhatsApp or email.
            </p>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
              {['whatsapp', 'email'].map(c => (
                <button key={c} onClick={() => setChannel(c)} style={{
                  flex: 1, padding: '10px', borderRadius: '10px',
                  border: channel === c ? '2px solid #1e3a5f' : '2px solid #E5E7EB',
                  background: channel === c ? '#EFF6FF' : '#F9FAFB',
                  color: channel === c ? '#1e3a5f' : '#6B7280',
                  fontWeight: channel === c ? 700 : 400, cursor: 'pointer', fontSize: '14px',
                }}>
                  {c === 'whatsapp' ? '💬 WhatsApp' : '📧 Email'}
                </button>
              ))}
            </div>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '12px' }}>
              <input
                type={channel === 'whatsapp' ? 'tel' : 'email'}
                placeholder={channel === 'whatsapp' ? '+2348012345678' : 'recipient@email.com'}
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                style={{ flex: 1, border: '1.5px solid #E5E7EB', borderRadius: '10px', padding: '10px 14px', fontSize: '14px', outline: 'none' }}
              />
              <button onClick={handleSend} disabled={sending} style={{
                background: sending ? '#9CA3AF' : '#25D366', color: '#fff', border: 'none',
                borderRadius: '10px', padding: '12px 20px', fontWeight: 700,
                cursor: sending ? 'not-allowed' : 'pointer', fontSize: '14px', whiteSpace: 'nowrap',
              }}>
                {sending ? 'Sending...' : '💬 Send'}
              </button>
            </div>
            {sendError && <p style={{ color: '#DC2626', fontSize: '13px', margin: 0 }}>⚠️ {sendError}</p>}
            {sendSuccess && <p style={{ color: '#15803D', fontSize: '13px', margin: 0 }}>✅ {sendSuccess}</p>}
            <p style={{ fontSize: '12px', color: '#9CA3AF', marginTop: '10px' }}>
              {channel === 'whatsapp' ? 'Include country code e.g. +234 for Nigeria.' : 'Enter any email address to receive the report.'}
            </p>
          </div>

          

          {/* Send to Hospital */}
          <button onClick={() => setHospitalModal(true)} style={{
            width: '100%', background: '#0f766e', color: '#fff', border: 'none',
            borderRadius: '12px', padding: '14px', fontWeight: 700, cursor: 'pointer', fontSize: '15px', marginBottom: '12px',
          }}>
            🏥 Send Report to Hospital
          </button>

          <p style={{ textAlign: 'center', fontSize: '12px', color: '#9CA3AF', marginBottom: '24px' }}>
            ⚕️ This report is for informational purposes only. Always consult a healthcare professional.
          </p>
        </div>
      </div>
    </div>
  )
}

export default ActionPlan