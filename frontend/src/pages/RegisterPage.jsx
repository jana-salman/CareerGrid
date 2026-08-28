import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import AuthLayout from '../components/AuthLayout.jsx'
import { register } from '../services/authApi.js'

function RegisterPage() {
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordVisible, setPasswordVisible] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await register({ fullName, email, password })
      navigate('/login?registered=1', { replace: true })
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout headingId="register-title">
      <header><p className="card-kicker">CareerGrid workspace</p><h2 id="register-title">Create your account</h2><p>Start your career journey.</p></header>
      <form onSubmit={submit}>
        <label htmlFor="register-name">Full name</label>
        <div className="input-wrap"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></svg><input id="register-name" type="text" name="full_name" placeholder="Enter your full name" autoComplete="name" required value={fullName} onChange={(event) => setFullName(event.target.value)} /></div>
        <label htmlFor="register-email">Email address</label>
        <div className="input-wrap"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="m3 7 9 6 9-6" /></svg><input id="register-email" type="email" name="email" placeholder="Enter your email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></div>
        <label htmlFor="register-password">Password</label>
        <div className="input-wrap">
          <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="10" width="14" height="10" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg>
          <input id="register-password" type={passwordVisible ? 'text' : 'password'} name="password" placeholder="Create a password" autoComplete="new-password" required value={password} onChange={(event) => setPassword(event.target.value)} />
          <button className="password-toggle" type="button" aria-label={passwordVisible ? 'Hide password' : 'Show password'} aria-pressed={passwordVisible} onClick={() => setPasswordVisible((visible) => !visible)}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z" /><circle cx="12" cy="12" r="2.5" /></svg></button>
        </div>
        {error && <p className="auth-notice auth-notice--error" role="alert">{error}</p>}
        <button className="sign-in-button" type="submit" disabled={submitting}><span>{submitting ? 'Creating account...' : 'Create account'}</span><span aria-hidden="true">→</span></button>
      </form>
      <p className="auth-link">Already have an account? <Link to="/login">Sign in</Link></p>
    </AuthLayout>
  )
}

export default RegisterPage
