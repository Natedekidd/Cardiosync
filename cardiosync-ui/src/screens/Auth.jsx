import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login, signup } from '../api'
import '../css/Auth.css'

function Auth() {
  const navigate = useNavigate()
  const [mode, setMode] = useState('login') // 'login' | 'signup'
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Login fields
  const [loginEmail, setLoginEmail] = useState('')
  const [loginPassword, setLoginPassword] = useState('')

  // Signup fields
  const [fullName, setFullName] = useState('')
  const [signupEmail, setSignupEmail] = useState('')
  const [signupPassword, setSignupPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [consent, setConsent] = useState(false)

  const [comingSoon, setComingSoon] = useState('')

  const handleComingSoon = (provider) => {
    setComingSoon(`${provider} sign-in coming soon!`)
    setTimeout(() => setComingSoon(''), 3000)
  }

  const handleLogin = async () => {
    setError('')
    if (!loginEmail || !loginPassword) {
      setError('Please enter both email and password')
      return
    }
    setLoading(true)
    try {
      await login({ email: loginEmail, password: loginPassword })
      navigate('/dashboard')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSignup = async () => {
    setError('')
    setSuccess('')
    if (!fullName || !signupEmail || !signupPassword || !confirmPassword) {
      setError('Please fill in all fields')
      return
    }
    if (signupPassword !== confirmPassword) {
      setError('Passwords do not match')
      return
    }
    if (signupPassword.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }
    if (!consent) {
      setError('Please accept the terms to continue')
      return
    }
    setLoading(true)
    try {
      await signup({
        full_name: fullName,
        email: signupEmail,
        password: signupPassword,
        consent_given: true,
      })
      setSuccess('Account created! Please sign in.')
      setMode('login')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-header">
        <h1 className="auth-title">{mode === 'login' ? 'Sign In' : 'Create Account'}</h1>
        <p className="auth-subtitle">
          {mode === 'login'
            ? 'Sign into your account, enter your email and password'
            : 'Create your CardioSync account'}
        </p>
      </div>

      <div className="auth-form">

        {comingSoon && (
          <div style={{ background: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: '8px', padding: '10px 14px', marginBottom: '12px', color: '#1D4ED8', fontSize: '13px', textAlign: 'center' }}>
            🚧 {comingSoon}
          </div>
        )}

        {/* Error / Success messages */}
        {error && (
          <div className="auth-error">{error}</div>
        )}
        {success && (
          <div className="auth-success">{success}</div>
        )}

        {mode === 'login' ? (
          <>
            <div className="input-group">
              <span className="input-icon">
                <img src="/assets/Icons/email-icon.svg" alt="email" width="18" />
              </span>
              <input
                type="email"
                placeholder="Email"
                className="input-field"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
              />
            </div>

            <div className="input-group">
              <span className="input-icon">
                <img src="/assets/Icons/lock-icon.png" alt="lock" width="18" />
              </span>
              <input
                type="password"
                placeholder="Password"
                className="input-field"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
              />
            </div>

            <div className="forgot-wrapper">
              <a href="#" className="forgot-link">Forgot password?</a>
            </div>

            <button
              className="btn-continue"
              onClick={handleLogin}
              disabled={loading}
            >
              {loading ? 'Signing in...' : 'Continue'}
            </button>

            <p className="create-account-text">
              Don't have an account yet?{' '}
              <span className="create-link" onClick={() => { setMode('signup'); setError('') }}>
                Create an account
              </span>
            </p>
          </>
        ) : (
          <>
            <div className="input-group">
              <input
                type="text"
                placeholder="Full Name"
                className="input-field"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>

            <div className="input-group">
              <span className="input-icon">
                <img src="/assets/Icons/email-icon.svg" alt="email" width="18" />
              </span>
              <input
                type="email"
                placeholder="Email"
                className="input-field"
                value={signupEmail}
                onChange={(e) => setSignupEmail(e.target.value)}
              />
            </div>

            <div className="input-group">
              <span className="input-icon">
                <img src="/assets/Icons/lock-icon.png" alt="lock" width="18" />
              </span>
              <input
                type="password"
                placeholder="Password (min 6 characters)"
                className="input-field"
                value={signupPassword}
                onChange={(e) => setSignupPassword(e.target.value)}
              />
            </div>

            <div className="input-group">
              <span className="input-icon">
                <img src="/assets/Icons/lock-icon.png" alt="lock" width="18" />
              </span>
              <input
                type="password"
                placeholder="Confirm Password"
                className="input-field"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>

            <label className="modal-checkbox" style={{ margin: '12px 0', fontSize: '13px', display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
                style={{ marginTop: '2px' }}
              />
              <span>
                I understand my health data will be encrypted and stored securely.
                I retain full ownership and can delete my account at any time.
                This is a research tool, not a medical diagnosis.
              </span>
            </label>

            <button
              className="btn-continue"
              onClick={handleSignup}
              disabled={loading}
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </button>

            <p className="create-account-text">
              Already have an account?{' '}
              <span className="create-link" onClick={() => { setMode('login'); setError('') }}>
                Sign in
              </span>
            </p>
          </>
        )}

        {mode === 'login' && (
          <>
            <div className="divider">
              <span className="divider-line"></span>
              <span className="divider-text">or</span>
              <span className="divider-line"></span>
            </div>
            <button className="btn-social" onClick={() => handleComingSoon('Apple')}>
              <img src="/assets/Icons/apple-icon.svg" alt="Apple" width="20" />
              Sign in with Apple
            </button>
            <button className="btn-social" onClick={() => handleComingSoon('Google')}>
              <img src="/assets/Icons/google-icon.svg" alt="Google" width="20" />
              Sign in with Google
            </button>
          </>
        )}

        <p className="terms-text">
          By clicking 'continue', I have read and agreed with the{' '}
          <a href="#" className="terms-link">Terms and conditions, Privacy Policy</a>
        </p>
      </div>
    </div>
  )
}

export default Auth