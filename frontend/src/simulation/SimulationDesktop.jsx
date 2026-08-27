import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { getFrontendSimulationProgress, getSimulationAttempt } from '../services/simulationApi.js'
import TaskPanel from './TaskPanel.jsx'

const apps = [
  ['mail', 'Mail', 'M'], ['files', 'Files', 'F'], ['vscode', 'VS Code', '</>'],
  ['browser', 'Browser', 'O'], ['terminal', 'Terminal', '>_'], ['github', 'GitHub', 'GH'], ['guide', 'Guide', '?'],
]

function iconClass(name) { return `app-icon app-icon-${name === 'vscode' ? 'vscode' : name}` }

function SimulationDesktop() {
  const { attemptId } = useParams()
  const [attempt, setAttempt] = useState(null)
  const [progress, setProgress] = useState(null)
  const [activeApp, setActiveApp] = useState(null)
  const [now, setNow] = useState(new Date())
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    getSimulationAttempt(attemptId)
      .then(async (loadedAttempt) => {
        const loadedProgress = loadedAttempt.position_id === 'frontend-developer'
          ? await getFrontendSimulationProgress(attemptId)
          : { current_step: 1, status: loadedAttempt.status }
        if (active) { setAttempt(loadedAttempt); setProgress(loadedProgress) }
      })
      .catch((requestError) => active && setError(requestError.message))
    return () => { active = false }
  }, [attemptId])
  useEffect(() => { const timer = window.setInterval(() => setNow(new Date()), 30000); return () => window.clearInterval(timer) }, [])

  if (error) return <main className="workspace"><p>{error}</p></main>
  if (!attempt || !progress) return <main className="workspace"><p>Loading workspace...</p></main>
  const scenario = attempt.public_scenario || {}
  const title = scenario.position_title || attempt.position_id?.replaceAll('-', ' ') || 'CareerGrid'
  const company = scenario.company_name || attempt.company_id || 'your company'
  const app = apps.find(([id]) => id === activeApp)
  return <main className="workspace" id="careergrid-workspace"><header className="workspace-topbar"><div className="workspace-brand"><div className="brand-icon">CG</div><div className="brand-text"><strong>CareerGrid</strong><span>Interactive Career Simulation</span></div></div><div className="workspace-user"><div className="workspace-clock"><strong>{now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</strong><span>{now.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}</span></div><div className="user-avatar">U</div><div className="user-information"><strong>User</strong><span>{title}</span></div></div></header><section className={`desktop${activeApp ? ' has-active-app' : ''}`}><aside className="app-dock">{apps.map(([id, label, icon]) => <button className={`dock-app${activeApp === id ? ' is-open is-active' : ''}`} type="button" key={id} aria-pressed={activeApp === id} onClick={() => setActiveApp(id)}><span className={iconClass(id)}>{icon}</span><span>{label}</span></button>)}</aside><section className="desktop-home"><div className="welcome-card"><span className="welcome-label">Workspace ready</span><h1>Welcome to your {title} workspace.</h1><p>You're working with <strong>{company}</strong>. Check your inbox to see what needs your attention today.</p><button type="button" className="open-mail-btn" onClick={() => setActiveApp('mail')}>Open Mail</button></div><div className="role-card"><span>Role</span><strong>{title}</strong><span>Company</span><strong>{company}</strong></div></section>{activeApp && <AppWindow app={app} onClose={() => setActiveApp(null)} />}{attempt.position_id === 'frontend-developer' && <TaskPanel attempt={attempt} progress={progress} />}</section></main>
}

function AppWindow({ app, onClose }) {
  const [, label, icon] = app
  return <section className="app-window is-active" aria-hidden="false"><div className="window-header"><div className="window-title"><span className={iconClass(app[0])}>{icon}</span><strong>{label}</strong></div><div className="window-controls"><button type="button" aria-label={`Minimize ${label}`} onClick={onClose}>-</button><button type="button" aria-label={`Close ${label}`} onClick={onClose}>x</button></div></div><div className="placeholder-content"><div className="placeholder-symbol">{icon}</div><h2>{label}</h2><p>This app shell is ready. Its existing workspace behavior will remain available during its dedicated migration phase.</p></div></section>
}

export default SimulationDesktop
