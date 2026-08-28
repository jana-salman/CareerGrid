import { Link } from 'react-router-dom'

function ScenarioUnavailablePage({ attempt }) {
  const pending = attempt.status === 'generating'
  return (
    <main className="auth-page">
      <section className="auth-card" style={{ maxWidth: '42rem' }}>
        <h1>Workspace scenario unavailable</h1>
        <p>
          {pending
            ? 'The workspace scenario is still being prepared. Please return to the company page and start a new attempt if this page does not change.'
            : 'CareerGrid could not prepare this workspace scenario. Your existing attempts were not changed.'}
        </p>
        <p><Link to={`/positions/${attempt.career_id}/${attempt.position_id}`}>Start a new attempt</Link></p>
      </section>
    </main>
  )
}

export default ScenarioUnavailablePage
