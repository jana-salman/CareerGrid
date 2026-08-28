import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { getAuthenticatedSession, logout } from '../services/authApi.js'
import {
  clearDashboardCache,
  prefetchDashboard,
  setDashboardSession,
} from '../services/dashboardApi.js'

function HomePage() {
  const [userName, setUserName] = useState('')

  useEffect(() => {
    document.body.classList.add('home-page')
    getAuthenticatedSession()
      .then((session) => {
        setUserName(session.user.name)
        setDashboardSession(session.user.id)
        prefetchDashboard().catch(() => {})
      })
      .catch((error) => {
        if (error.status === 401) window.location.assign('/login')
      })
    return () => document.body.classList.remove('home-page')
  }, [])

  const handleLogout = async (event) => {
    event.preventDefault()
    clearDashboardCache()
    try {
      await logout()
      window.location.assign('/login')
    } catch {
      window.location.assign('/logout')
    }
  }

  return (
    <>
      <header className="home-header">
        <nav className="home-navbar" aria-label="Primary navigation">
          <Link className="home-brand" to="/" aria-label="CareerGrid home"><span className="home-brand-mark" aria-hidden="true">C</span><span>CareerGrid</span></Link>
          <div className="home-nav-links"><Link className="is-active" to="/" aria-current="page">Home</Link><Link to="/career">Careers</Link><a className="home-signout" href="/logout" onClick={handleLogout}>Sign Out</a></div>
        </nav>
      </header>
      <main>
        <section className="home-hero" aria-labelledby="home-hero-title">
          <div className="home-hero-copy">
            {userName && <p className="home-welcome">Welcome back, {userName}</p>}
            <p className="home-eyebrow">Learn by doing</p>
            <h1 id="home-hero-title">Build confidence before the real job starts.</h1>
            <p className="home-hero-text">Explore career paths, complete realistic workplace tasks, practice interviews, and receive personalized AI-powered feedback.</p>
            <Link className="home-button home-button-primary" to="/career">Explore Careers <span aria-hidden="true">→</span></Link>
          </div>
          <div className="home-journey-card" aria-label="Your CareerGrid journey"><div className="home-journey-heading"><span className="home-journey-label">Your journey</span><span className="home-status-dot">Ready</span></div><h2>Turn curiosity into experience.</h2><ol className="home-journey-steps"><li><span>01</span><div><strong>Choose a path</strong><p>Explore careers that match your interests.</p></div></li><li><span>02</span><div><strong>Practice real skills</strong><p>Work through authentic tasks and interviews.</p></div></li><li><span>03</span><div><strong>Grow with feedback</strong><p>Use personalized insights to improve.</p></div></li></ol></div>
        </section>
        <section className="home-features" aria-labelledby="home-features-title"><div className="home-section-heading"><p className="home-eyebrow">Built for practical growth</p><h2 id="home-features-title">Why CareerGrid?</h2><p>Develop career-ready skills in a safe space designed for learning and progress.</p></div><div className="home-feature-grid"><article className="home-feature-card"><span className="home-feature-number">01</span><h3>Realistic Work Simulations</h3><p>Practice real workplace scenarios using tools and workflows inspired by professional environments.</p></article><article className="home-feature-card"><span className="home-feature-number">02</span><h3>AI-Powered Feedback</h3><p>Understand your strengths, identify areas for improvement, and receive actionable feedback after each simulation.</p></article><article className="home-feature-card"><span className="home-feature-number">03</span><h3>Interview Practice</h3><p>Prepare for real interviews through interactive AI-powered interview simulations and personalized evaluation.</p></article></div></section>
      </main>
    </>
  )
}

export default HomePage
