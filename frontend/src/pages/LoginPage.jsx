import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import AuthLayout from '../components/AuthLayout.jsx'
import { login } from '../services/authApi.js'

function LoginPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
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
      await login({ email, password })
      navigate('/', { replace: true })
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout headingId="login-title">
      <header><p className="card-kicker">CareerGrid workspace</p><h2 id="login-title">Welcome back</h2><p>Continue your journey.</p></header>
      <form onSubmit={submit}>
        <label htmlFor="login-email">Email address</label>
        <div className="input-wrap">
          <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="m3 7 9 6 9-6" /></svg>
          <input id="login-email" type="email" name="email" placeholder="Enter your email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} />
        </div>
        <label htmlFor="login-password">Password</label>
        <div className="input-wrap">
          <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="10" width="14" height="10" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg>
          <input id="login-password" type={passwordVisible ? 'text' : 'password'} name="password" placeholder="Enter your password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} />
          <button className="password-toggle" type="button" aria-label={passwordVisible ? 'Hide password' : 'Show password'} aria-pressed={passwordVisible} onClick={() => setPasswordVisible((visible) => !visible)}>
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z" /><circle cx="12" cy="12" r="2.5" /></svg>
          </button>
        </div>
        {searchParams.get('registered') === '1' && <p className="auth-notice auth-notice--success" role="status">Account created successfully. Please log in.</p>}
        {error && <p className="auth-notice auth-notice--error" role="alert">{error}</p>}
        <button className="sign-in-button" type="submit" disabled={submitting}><span>{submitting ? 'Signing in...' : 'Sign in'}</span><span aria-hidden="true">→</span></button>
      </form>
      <p className="auth-link">Don't have an account? <Link to="/register">Sign up</Link></p>
    </AuthLayout>
  )
}

export default LoginPage
