import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { getDashboard } from '../services/dashboardApi.js'

const filters = [
  ['all', 'All'],
  ['completed', 'Completed'],
  ['in_progress', 'In Progress'],
]

function attemptMatchesFilter(attempt, filter) {
  return filter === 'all' || attempt.status === filter
    || (filter === 'in_progress' && attempt.status === 'generating')
}

function DashboardPage() {
  const [dashboard, setDashboard] = useState(null)
  const [filter, setFilter] = useState('all')
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    getDashboard()
      .then((data) => active && setDashboard(data))
      .catch((requestError) => active && setError(requestError.message))
    return () => { active = false }
  }, [])

  const visibleAttempts = useMemo(
    () => (dashboard?.attempts || []).filter((attempt) => attemptMatchesFilter(attempt, filter)),
    [dashboard, filter],
  )

  if (error) return <main className="dashboard-page"><p className="filter-empty">{error}</p></main>
  if (!dashboard) return <main className="dashboard-page"><p className="filter-empty">Loading your dashboard…</p></main>

  return <div className="career-page dashboard-page">
    <nav className="navbar dashboard-nav" aria-label="Main navigation">
      <Link className="dashboard-brand" to="/career">CareerGrid</Link>
      <div className="dashboard-nav-links">
        <Link to="/career">Home</Link><Link className="is-active" to="/dashboard" aria-current="page">Dashboard</Link><a href="/logout">Log out</a>
      </div>
    </nav>
    <main className="dashboard-shell">
      <header className="dashboard-hero"><p className="dashboard-kicker">Your CareerGrid</p><h1>Welcome back{dashboard.user_name ? `, ${dashboard.user_name}` : ''}.</h1><p>Review your simulations, feedback, and progress.</p></header>
      <section className="summary-grid" aria-label="Simulation summary">
        <Summary icon="◌" label="Simulations" value={dashboard.simulation_count} />
        <Summary icon="✓" modifier="summary-icon--complete" label="Completed" value={dashboard.completed_count} />
        <Summary icon="◇" modifier="summary-icon--score" label="Average Score" value={dashboard.average_score === null ? '—' : `${dashboard.average_score} / 100`} />
      </section>
      <section className="history-panel" aria-labelledby="history-title">
        <div className="history-heading"><div><p className="dashboard-kicker">History</p><h2 id="history-title">Your Simulations</h2></div>
          {dashboard.attempts.length > 0 && <div className="history-filters" role="group" aria-label="Filter simulations">{filters.map(([value, label]) => <button key={value} className={`history-filter${filter === value ? ' is-active' : ''}`} type="button" onClick={() => setFilter(value)}>{label}</button>)}</div>}
        </div>
        {dashboard.attempts.length === 0 ? <EmptyDashboard /> : <div className="history-list">{visibleAttempts.map((attempt) => <AttemptCard attempt={attempt} key={attempt.attempt_id} />)}</div>}
        {dashboard.attempts.length > 0 && visibleAttempts.length === 0 && <p className="filter-empty">No simulations match this filter.</p>}
      </section>
    </main>
  </div>
}

function Summary({ icon, label, modifier = '', value }) {
  return <article className="summary-card"><span className={`summary-icon ${modifier}`} aria-hidden="true">{icon}</span><div><p>{label}</p><strong className={value === '—' ? 'no-score' : ''}>{value}</strong></div></article>
}

function AttemptCard({ attempt }) {
  const preview = attempt.feedback_preview || (attempt.status === 'completed' ? 'No review available for this earlier attempt.' : attempt.status === 'in_progress' ? 'Your unfinished workplace task is ready when you are.' : '')
  return <article className="history-card"><div className="history-card-main"><div className="history-title-line"><h3>{attempt.task_title}</h3><span className={`status-badge status-badge--${attempt.status}`}>{attempt.status_label}</span></div><p className="history-context">{attempt.position_title} <span aria-hidden="true">·</span> {attempt.company_name}</p><p className="history-career">{attempt.career_name} <span aria-hidden="true">·</span> {attempt.date}</p>{preview && <p className={`feedback-preview${attempt.feedback_preview ? '' : ' feedback-preview--muted'}`}>{preview}</p>}</div><div className="history-card-actions">{attempt.score !== null && <div className="history-score"><strong>{attempt.score}</strong><span>/ 100</span></div>}{attempt.evaluation ? <Link className="dashboard-action dashboard-action--primary" to={`/simulation/attempts/${encodeURIComponent(attempt.attempt_id)}/report`}>View Feedback</Link> : attempt.can_resume ? <a className="dashboard-action dashboard-action--primary" href={`/workspace/attempt/${encodeURIComponent(attempt.attempt_id)}`}>Resume Workspace</a> : <span className="review-unavailable">No review available</span>}</div></article>
}

function EmptyDashboard() {
  return <div className="dashboard-empty"><div className="empty-symbol" aria-hidden="true"><span>{'{ }'}</span><i /></div><h3>No simulations yet</h3><p>Complete your first CareerGrid workplace simulation and your feedback will appear here.</p><Link className="dashboard-action dashboard-action--primary" to="/career">Explore Careers</Link></div>
}

export default DashboardPage
