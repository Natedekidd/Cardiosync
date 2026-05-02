// src/api.js
// All API calls to the CardioSync FastAPI backend

const BASE_URL = 'http://localhost:8001'

// ── Token helpers ──────────────────────────────────────────────────────────
export const getToken = () => localStorage.getItem('cardiosync_token')
export const setToken = (token) => localStorage.setItem('cardiosync_token', token)
export const removeToken = () => localStorage.removeItem('cardiosync_token')
export const getUser = () => {
  const u = localStorage.getItem('cardiosync_user')
  return u ? JSON.parse(u) : null
}
export const setUser = (user) => localStorage.setItem('cardiosync_user', JSON.stringify(user))
export const removeUser = () => localStorage.removeItem('cardiosync_user')

// ── Base fetch helper ──────────────────────────────────────────────────────
async function request(path, options = {}) {
  const token = getToken()
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })
  const data = await res.json()

  if (!res.ok) {
    throw new Error(data.detail || 'Something went wrong')
  }
  return data
}

// ══════════════════════════════════════════════════════════════════════════
// AUTH
// ══════════════════════════════════════════════════════════════════════════

export async function signup({ full_name, email, password, consent_given }) {
  return request('/auth/signup', {
    method: 'POST',
    body: JSON.stringify({ full_name, email, password, consent_given }),
  })
}

export async function login({ email, password }) {
  const data = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  // Save token and user to localStorage
  setToken(data.token)
  setUser(data.user)
  return data
}

export async function logout() {
  await request('/auth/logout', { method: 'POST' })
  removeToken()
  removeUser()
}

export async function deleteAccount() {
  await request('/auth/account', { method: 'DELETE' })
  removeToken()
  removeUser()
}

// ══════════════════════════════════════════════════════════════════════════
// PATIENT DATA
// ══════════════════════════════════════════════════════════════════════════

export async function savePatient(patientData) {
  return request('/patient', {
    method: 'POST',
    body: JSON.stringify(patientData),
  })
}

export async function getPatient() {
  return request('/patient')
}

// ══════════════════════════════════════════════════════════════════════════
// RISK ANALYSIS
// ══════════════════════════════════════════════════════════════════════════

export async function assessRisk(patientData) {
  return request('/risk/assess', {
    method: 'POST',
    body: JSON.stringify(patientData),
  })
}

export async function simulateRisk(simulationData) {
  return request('/risk/simulate', {
    method: 'POST',
    body: JSON.stringify(simulationData),
  })
}

export async function getRiskHistory() {
  return request('/risk/history')
}

// ══════════════════════════════════════════════════════════════════════════
// GENOMICS
// ══════════════════════════════════════════════════════════════════════════

export async function uploadVCF(file) {
  const token = getToken()
  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch(`${BASE_URL}/genomics/analyze`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'VCF upload failed')
  return data
}

// ══════════════════════════════════════════════════════════════════════════
// PHARMACOGENOMICS
// ══════════════════════════════════════════════════════════════════════════

export async function getPharmacogenomics() {
  return request('/pharmacogenomics')
}

export async function getPersonalizedPharmacogenomics(genomicSummary) {
  return request('/pharmacogenomics/personalized', {
    method: 'POST',
    body: JSON.stringify(genomicSummary),
  })
}

// ══════════════════════════════════════════════════════════════════════════
// ENVIRONMENT
// ══════════════════════════════════════════════════════════════════════════

export async function getEnvironment(location) {
  return request(`/environment?location=${encodeURIComponent(location)}`)
}

// ══════════════════════════════════════════════════════════════════════════
// MESSAGING
// ══════════════════════════════════════════════════════════════════════════

export async function sendMessage({ phone_number, channel, patient_name, total_risk, risk_category, recommendations }) {
  return request('/messaging/send', {
    method: 'POST',
    body: JSON.stringify({ phone_number, channel, patient_name, total_risk, risk_category, recommendations }),
  })
}

// ══════════════════════════════════════════════════════════════════════════
// PROFILE
// ══════════════════════════════════════════════════════════════════════════

export async function getProfile() {
  return request('/profile')
}