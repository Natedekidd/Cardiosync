import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const navItems = [
  { icon: '🏠', label: 'Dashboard', path: '/dashboard' },
  { icon: '👤', label: 'Patient Data', path: '/patient' },
  { icon: '📈', label: 'Risk Analysis', path: '/risk' },
  { icon: '⏱️', label: 'Simulation', path: '/simulation' },
  { icon: '💊', label: 'Medications', path: '/medications' },
  { icon: '📋', label: 'Action Plan', path: '/action' },
]

const faqs = [
  {
    q: 'What is CardioSync?',
    a: 'CardioSync is a precision cardiovascular risk platform that combines three data streams — clinical vitals, genomic data, and environmental air quality — to calculate your personalised 10-year cardiovascular disease risk. It is built specifically with African populations in mind.',
  },
  {
    q: 'How is my risk score calculated?',
    a: 'Your Total Risk = Clinical Risk (from the Framingham AI model) + Genomic Risk (from your VCF file) + Environmental Risk (from real-time air quality data). The score is capped at 99% and represents your estimated probability of a cardiovascular event within 10 years.',
  },
  {
    q: 'What is a VCF file and do I need one?',
    a: 'A VCF (Variant Call Format) file is a genomic data file from DNA testing services. It is completely optional — CardioSync works without it. However, uploading a VCF unlocks personalised pharmacogenomic drug recommendations and adds a genomic risk layer to your score.',
  },
  {
    q: 'What is SHAP and why does it matter?',
    a: 'SHAP (SHapley Additive exPlanations) is an AI explainability method that shows exactly which factors contributed to your risk score and by how much. Unlike black-box models, CardioSync shows you why your score is what it is.',
  },
  {
    q: 'Is my health and genomic data secure?',
    a: 'Yes. Your data is encrypted and stored securely. Only the specific gene variants needed for risk analysis are extracted from your VCF file. You can withdraw consent and delete your data at any time from the Patient Data page.',
  },
  {
    q: 'What does my risk category mean?',
    a: 'Low (under 10%) — Low risk of a cardiovascular event in 10 years. Moderate (10–20%) — Some risk factors present, lifestyle changes recommended. High (20–30%) — Significant risk, medical consultation advised. Very High (above 30%) — Urgent medical attention recommended.',
  },
  {
    q: 'What is the Lifestyle Simulator?',
    a: 'The Simulator lets you model "what if" scenarios — for example, what happens to your risk score if you quit smoking, exercise more, or reduce your blood pressure. It helps you understand which lifestyle changes will have the biggest impact.',
  },
  {
    q: 'Can I send my report to my doctor?',
    a: 'Yes. From the Action Plan page you can download a PDF report, send it via email or WhatsApp, or transmit it directly to a hospital system using the FHIR standard — the international protocol for health data exchange.',
  },
  {
    q: 'Why is CardioSync built for African populations?',
    a: 'Most cardiovascular risk tools are trained on European data and miss African-specific genetic variants like APOL1, 9p21, and CETP. CardioSync includes a 50-gene cardiovascular database with African-frequency variants, making risk predictions more accurate for African patients.',
  },
  {
    q: 'What does "pharmacogenomics" mean on the Medications page?',
    a: 'Pharmacogenomics is the study of how your genes affect your response to drugs. For example, patients with the CYP2C19 *2 variant metabolise Clopidogrel poorly — meaning the standard dose may not work. CardioSync flags these interactions so you and your doctor can make informed decisions.',
  },
]

function Help() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [openFaq, setOpenFaq] = useState(null)
  const navigate = useNavigate()

  const handleNavigate = (path) => {
    setMenuOpen(false)
    setTimeout(() => navigate(path), 100)
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

          {/* Hero */}
          <div style={{
            background: 'linear-gradient(135deg, #1e3a5f, #2d5986)',
            borderRadius: '16px', padding: '28px 24px', color: '#fff', marginBottom: '8px',
          }}>
            <h2 style={{ fontSize: '22px', fontWeight: 800, marginBottom: '8px' }}>
              ❓ Help & Support
            </h2>
            <p style={{ fontSize: '14px', opacity: 0.8, lineHeight: 1.6, maxWidth: '560px' }}>
              CardioSync is a precision cardiovascular risk platform combining AI, genomics, and environmental data
              to predict your 10-year heart disease risk — personalised for African populations.
            </p>
          </div>

          {/* Quick links */}
          <div className="section-card">
            <h3 className="section-title">🚀 Quick Actions</h3>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              {[
                { label: '👤 Enter Patient Data', path: '/patient', color: '#EFF6FF', text: '#1D4ED8' },
                { label: '📈 Run Risk Analysis', path: '/risk', color: '#F0FDF4', text: '#15803D' },
                { label: '⏱️ Simulate Changes', path: '/simulation', color: '#FDF4FF', text: '#7E22CE' },
                { label: '📋 View Action Plan', path: '/action', color: '#FFF7ED', text: '#C2410C' },
              ].map((a, i) => (
                <button key={i} onClick={() => navigate(a.path)} style={{
                  background: a.color, color: a.text, border: 'none',
                  borderRadius: '10px', padding: '10px 16px',
                  fontWeight: 600, cursor: 'pointer', fontSize: '13px',
                }}>
                  {a.label}
                </button>
              ))}
            </div>
          </div>

          {/* How it works */}
          <div className="section-card">
            <h3 className="section-title">⚙️ How CardioSync Works</h3>
            {[
              { num: '1', title: 'Enter Your Data', desc: 'Fill in your clinical vitals, medical history and lifestyle information on the Patient Data page. Optionally upload a VCF genomic file for deeper analysis.' },
              { num: '2', title: 'AI Risk Calculation', desc: 'The Framingham logistic regression model processes your data alongside real-time air quality for your location and your genomic polygenic risk score (if VCF uploaded).' },
              { num: '3', title: 'Understand Your Risk', desc: 'View your 10-year cardiovascular risk score broken down by clinical, genomic and environmental factors. SHAP charts show exactly what is driving your risk.' },
              { num: '4', title: 'Take Action', desc: 'Use the Simulator to model lifestyle changes, review personalised drug guidance on the Medications page, and download or share your Action Plan report.' },
            ].map((step, i) => (
              <div key={i} style={{
                display: 'flex', gap: '14px', alignItems: 'flex-start',
                padding: '14px 0', borderBottom: i < 3 ? '1px solid #F3F4F6' : 'none',
              }}>
                <div style={{
                  background: '#1e3a5f', color: '#fff', borderRadius: '50%',
                  width: '28px', height: '28px', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', fontSize: '13px', fontWeight: 700, flexShrink: 0,
                }}>{step.num}</div>
                <div>
                  <p style={{ fontWeight: 700, fontSize: '14px', marginBottom: '4px', color: '#111' }}>{step.title}</p>
                  <p style={{ fontSize: '13px', color: '#6B7280', lineHeight: 1.6 }}>{step.desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Risk categories */}
          <div className="section-card">
            <h3 className="section-title">📊 Understanding Your Risk Score</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              {[
                { label: '🟢 Low Risk', range: 'Under 10%', desc: 'Keep up healthy habits. Annual screening recommended.', bg: '#F0FDF4', color: '#15803D' },
                { label: '🟡 Moderate Risk', range: '10% – 20%', desc: 'Lifestyle changes advised. Consider medical review.', bg: '#FFFBEB', color: '#92400E' },
                { label: '🔴 High Risk', range: '20% – 30%', desc: 'Significant risk. Medical consultation strongly advised.', bg: '#FEF2F2', color: '#DC2626' },
                { label: '🔴 Very High Risk', range: 'Above 30%', desc: 'Urgent attention needed. Seek immediate medical care.', bg: '#FEF2F2', color: '#991B1B' },
              ].map((r, i) => (
                <div key={i} style={{ background: r.bg, borderRadius: '10px', padding: '14px' }}>
                  <p style={{ fontWeight: 700, fontSize: '13px', color: r.color, marginBottom: '2px' }}>{r.label}</p>
                  <p style={{ fontSize: '12px', fontWeight: 600, color: r.color, marginBottom: '6px' }}>{r.range}</p>
                  <p style={{ fontSize: '12px', color: '#4B5563', lineHeight: 1.5 }}>{r.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* FAQ */}
          <div className="section-card">
            <h3 className="section-title">💬 Frequently Asked Questions</h3>
            {faqs.map((faq, i) => (
              <div key={i} style={{ borderBottom: i < faqs.length - 1 ? '1px solid #F3F4F6' : 'none' }}>
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  style={{
                    width: '100%', background: 'none', border: 'none',
                    padding: '14px 0', display: 'flex', justifyContent: 'space-between',
                    alignItems: 'center', cursor: 'pointer', textAlign: 'left',
                  }}
                >
                  <span style={{ fontSize: '13px', fontWeight: 600, color: '#111', paddingRight: '12px' }}>
                    {faq.q}
                  </span>
                  <span style={{ fontSize: '16px', color: '#6B7280', flexShrink: 0 }}>
                    {openFaq === i ? '−' : '+'}
                  </span>
                </button>
                {openFaq === i && (
                  <p style={{ fontSize: '13px', color: '#6B7280', lineHeight: 1.7, paddingBottom: '14px' }}>
                    {faq.a}
                  </p>
                )}
              </div>
            ))}
          </div>

          {/* Contact */}
          <div className="section-card" style={{ marginBottom: '24px' }}>
            <h3 className="section-title">📬 Contact & Support</h3>
            <p style={{ fontSize: '13px', color: '#6B7280', marginBottom: '16px', lineHeight: 1.6 }}>
              CardioSync is a hackathon project built for the Precision Genomics for Early and Accurate Diagnosis challenge.
              For questions or feedback, reach out to the team.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[
                { icon: '📧', label: 'Email', value: 'support@cardiosync.health' },
                { icon: '🐙', label: 'GitHub', value: 'github.com/Natedekidd/Cardiosync' },
                { icon: '🏥', label: 'Built for', value: 'Precision Genomics Hackathon 2025' },
              ].map((c, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{
                    background: '#EFF6FF', borderRadius: '8px',
                    width: '36px', height: '36px', display: 'flex',
                    alignItems: 'center', justifyContent: 'center', fontSize: '16px', flexShrink: 0,
                  }}>{c.icon}</span>
                  <div>
                    <p style={{ fontSize: '11px', color: '#9CA3AF', marginBottom: '1px' }}>{c.label}</p>
                    <p style={{ fontSize: '13px', color: '#374151', fontWeight: 500 }}>{c.value}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <p style={{ textAlign: 'center', fontSize: '12px', color: '#9CA3AF', marginBottom: '24px' }}>
            ⚕️ CardioSync is for informational purposes only. Always consult a qualified healthcare professional.
          </p>

        </div>
      </div>
    </div>
  )
}

export default Help