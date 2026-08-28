import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { getFrontendSimulationProgress, getSimulationAttempt } from '../services/simulationApi.js'
import TaskPanel from './TaskPanel.jsx'
import AdvisorApp from './apps/AdvisorApp.jsx'
import BrowserApp from './apps/BrowserApp.jsx'
import FilesApp from './apps/FilesApp.jsx'
import GitHubApp from './apps/GitHubApp.jsx'
import MailApp from './apps/MailApp.jsx'
import TerminalApp from './apps/TerminalApp.jsx'
import VSCodeApp from './apps/VSCodeApp.jsx'
import {
  downloadAttachment,
  extractProjectArchive,
  loadRepository,
  persistRepository,
  saveFile,
} from './state/repositoryModel.js'

const apps = [
  { headerClass: 'mail-window-header', icon: '✉', id: 'mail', label: 'Mail', windowClass: 'mail-window' },
  { headerClass: 'files-window-header', icon: '▰', id: 'files', label: 'Files', windowClass: 'files-window' },
  { headerClass: 'vscode-window-header', icon: '</>', id: 'vscode', label: 'VS Code', windowClass: 'vscode-window' },
  { headerClass: '', icon: '◎', id: 'browser', label: 'Browser', title: 'CareerGrid Browser', windowClass: 'browser-window' },
  { headerClass: 'terminal-app-header', icon: '>_', id: 'terminal', label: 'Terminal', windowClass: 'terminal-app-window' },
  { headerClass: 'github-app-header', icon: 'GH', id: 'github', label: 'GitHub', windowClass: 'github-app-window' },
  { headerClass: '', icon: '?', id: 'guide', label: 'Guide', title: 'Workspace Guide', windowClass: 'guide-window' },
]

const iconClass = (name) => `app-icon app-icon-${name}`

function SimulationDesktop() {
  const { attemptId } = useParams()
  const [attempt, setAttempt] = useState(null)
  const [progress, setProgress] = useState(null)
  const [activeApp, setActiveApp] = useState(null)
  const [error, setError] = useState('')
  const [repository, setRepository] = useState(null)
  const [unreadCount, setUnreadCount] = useState(0)
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 30_000)
    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    const theme = [...document.querySelectorAll('link[rel="stylesheet"]')].find(
      (link) => link.getAttribute('href') === '/static/css/careergrid-theme.css',
    )
    if (!theme?.parentNode) return undefined
    const originalPosition = document.createComment('careergrid-theme-position')
    theme.parentNode.insertBefore(originalPosition, theme)
    document.head.appendChild(theme)
    return () => {
      if (originalPosition.parentNode) originalPosition.parentNode.replaceChild(theme, originalPosition)
    }
  }, [])

  useEffect(() => {
    let active = true
    getSimulationAttempt(attemptId)
      .then(async (loaded) => {
        const loadedProgress = loaded.position_id === 'frontend-developer'
          ? await getFrontendSimulationProgress(attemptId)
          : { current_step: 1, status: loaded.status }
        if (!active) return
        const project = loaded.public_scenario?.project || {}
        setAttempt(loaded)
        setProgress(loadedProgress)
        setRepository(loadRepository(attemptId, project.files || [], {
          archiveName: project.archive_name,
          name: project.name || 'careergrid-workspace',
          path: `/Projects/${project.name || 'careergrid-workspace'}`,
          requireExtraction: loaded.position_id !== 'frontend-developer',
        }))
      })
      .catch((requestError) => active && setError(requestError.message))
    return () => { active = false }
  }, [attemptId])

  useEffect(() => {
    if (repository) persistRepository(attemptId, repository)
  }, [attemptId, repository])

  if (error) return <main className="workspace"><p>{error}</p></main>
  if (!attempt || !progress || !repository) return <main className="workspace"><p>Loading workspace...</p></main>

  const scenario = attempt.public_scenario || {}
  const title = attempt.position_id?.replaceAll('-', ' ') || 'CareerGrid'
  const company = scenario.company_name || attempt.company_id || 'your company'
  const downloads = repository.workspace?.downloadedAttachments || []
  const files = repository.workspace?.projectExtracted
    ? Object.values(repository.branches[repository.currentBranch].workingTree)
    : []
  const download = (item) => {
    const result = downloadAttachment(repository, item)
    if (!result.error) setRepository(result.repository)
    return result
  }
  const extract = (attachmentId) => {
    const result = extractProjectArchive(repository, attachmentId)
    if (!result.error) setRepository(result.repository)
    return result
  }
  const save = (path, content) => {
    const result = saveFile(repository, path, content)
    if (!result.error) setRepository(result.repository)
    return result
  }

  return (
    <main className="workspace" id="careergrid-workspace">
      <header className="workspace-topbar">
        <div className="workspace-brand">
          <div className="brand-icon">CG</div>
          <div className="brand-text"><strong>CareerGrid</strong><span>Interactive Career Simulation</span></div>
        </div>
        <div className="workspace-user">
          <div className="workspace-clock">
            <strong>{now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</strong>
            <span>{now.toLocaleDateString([], { day: 'numeric', month: 'short', year: 'numeric' })}</span>
          </div>
          <div className="user-avatar">U</div>
          <div className="user-information"><strong>User</strong><span>{title}</span></div>
        </div>
      </header>

      <section className={`desktop${activeApp ? ' has-active-app' : ''}`} id="desktop">
        <aside className="app-dock">
          {apps.map((app) => (
            <button
              className={`dock-app${app.id === 'guide' ? ' dock-help' : ''}${activeApp === app.id ? ' is-open is-active' : ''}`}
              type="button"
              key={app.id}
              onClick={() => setActiveApp(app.id)}
            >
              <span className={`${iconClass(app.id)}${app.id === 'mail' ? ' mail-dock-icon' : ''}`}>
                {app.icon}
                {app.id === 'mail' && <span className="mail-unread-badge">{unreadCount}</span>}
              </span>
              <span>{app.label}</span>
            </button>
          ))}
        </aside>

        <section className="desktop-home">
          <div className="welcome-card">
            <span className="welcome-label">Workspace ready</span>
            <h1>Welcome to your {title} workspace.</h1>
            <p>You're working with <strong>{company}</strong>. Check your inbox to see what needs your attention today.</p>
            <button className="open-mail-btn" type="button" onClick={() => setActiveApp('mail')}>Open Mail</button>
          </div>
          <div className="role-card">
            <span>Role</span><strong>{title}</strong><span>Company</span><strong>{company}</strong>
          </div>
        </section>

        {apps.map((app) => (
          <AppWindow
            active={activeApp === app.id}
            app={app}
            attempt={attempt}
            downloads={downloads}
            files={files}
            repository={repository}
            key={app.id}
            onClose={() => setActiveApp(null)}
            onDownload={download}
            onExtract={extract}
            onUnreadChange={setUnreadCount}
            onSave={save}
            onRepositoryChange={setRepository}
          />
        ))}
        {attempt.position_id === 'frontend-developer' && <TaskPanel attempt={attempt} progress={progress} />}
      </section>
    </main>
  )
}

function AppWindow({ active, app, attempt, downloads, files, repository, onClose, onDownload, onExtract, onSave, onRepositoryChange, onUnreadChange }) {
  const content = app.id === 'mail'
    ? <MailApp attempt={attempt} downloadedAttachments={downloads} repository={repository} onDownload={onDownload} onRepositoryChange={onRepositoryChange} onUnreadChange={onUnreadChange} />
    : app.id === 'files'
      ? <FilesApp downloadedAttachments={downloads} projectFiles={files} repository={repository} onExtract={onExtract} />
      : app.id === 'vscode'
        ? <VSCodeApp files={files} repository={repository} onSave={onSave} />
        : app.id === 'terminal'
          ? <TerminalApp files={files} repository={repository} onRepositoryChange={onRepositoryChange} />
          : app.id === 'browser'
            ? <BrowserApp attempt={attempt} />
            : app.id === 'github'
              ? <GitHubApp repository={repository} onRepositoryChange={onRepositoryChange} />
              : <AdvisorApp attempt={attempt} />

  return (
    <section className={`app-window ${app.windowClass}${active ? ' is-active' : ''}`} aria-hidden={!active}>
      <div className={`window-header${app.headerClass ? ` ${app.headerClass}` : ''}`}>
        <div className="window-title">
          <span className={`mini-icon ${iconClass(app.id)}`}>{app.icon}</span>
          <strong>{app.title || app.label}</strong>
        </div>
        <div className="window-controls">
          <button type="button" title="Minimize" onClick={onClose}>—</button>
          <button type="button" title="Close" onClick={onClose}>×</button>
        </div>
      </div>
      {content}
    </section>
  )
}

export default SimulationDesktop
