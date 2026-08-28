import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getFrontendSimulationProgress, getSimulationAttempt } from '../services/simulationApi.js'
import TaskPanel from './TaskPanel.jsx'
import MailApp from './apps/MailApp.jsx'
import FilesApp from './apps/FilesApp.jsx'
import VSCodeApp from './apps/VSCodeApp.jsx'
import TerminalApp from './apps/TerminalApp.jsx'
import BrowserApp from './apps/BrowserApp.jsx'
import GitHubApp from './apps/GitHubApp.jsx'
import AdvisorApp from './apps/AdvisorApp.jsx'
import {
  loadRepository,
  persistRepository,
  saveFile,
} from './state/repositoryModel.js'

const apps = [['mail', 'Mail', 'M'], ['files', 'Files', 'F'], ['vscode', 'VS Code', '</>'], ['browser', 'Browser', 'O'], ['terminal', 'Terminal', '>_'], ['github', 'GitHub', 'GH'], ['guide', 'Guide', '?']]
const iconClass = (name) => `app-icon app-icon-${name}`

function SimulationDesktop() {
  const { attemptId } = useParams()
  const [attempt, setAttempt] = useState(null); const [progress, setProgress] = useState(null); const [activeApp, setActiveApp] = useState(null); const [error, setError] = useState('')
  const [downloads, setDownloads] = useState([])
  const [repository, setRepository] = useState(null)
  useEffect(() => { let active = true; getSimulationAttempt(attemptId).then(async (loaded) => { const loadedProgress = loaded.position_id === 'frontend-developer' ? await getFrontendSimulationProgress(attemptId) : { current_step: 1, status: loaded.status }; if (active) { const project = loaded.public_scenario?.project || {}; setAttempt(loaded); setProgress(loadedProgress); setRepository(loadRepository(attemptId, project.files || [], { path: `/Projects/${project.name || 'careergrid-workspace'}`, name: project.name || 'careergrid-workspace' })) } }).catch((err) => active && setError(err.message)); return () => { active = false } }, [attemptId])
  useEffect(() => { if (repository) persistRepository(attemptId, repository) }, [attemptId, repository])
  if (error) return <main className="workspace"><p>{error}</p></main>
  if (!attempt || !progress || !repository) return <main className="workspace"><p>Loading workspace...</p></main>
  const scenario = attempt.public_scenario || {}; const title = attempt.position_id?.replaceAll('-', ' ') || 'CareerGrid'; const company = scenario.company_name || attempt.company_id || 'your company'
  const download = (item) => setDownloads((items) => items.some((entry) => entry.name === item.name) ? items : [...items, item])
  const files = Object.values(repository.branches[repository.currentBranch].workingTree)
  const save = (path, content) => { const result = saveFile(repository, path, content); if (!result.error) setRepository(result.repository); return result }
  return <main className="workspace"><header className="workspace-topbar"><div className="workspace-brand"><div className="brand-icon">CG</div><div className="brand-text"><strong>CareerGrid</strong><span>Interactive Career Simulation</span></div></div><div className="workspace-user"><div className="user-avatar">U</div><div className="user-information"><strong>User</strong><span>{title}</span></div></div></header><section className={`desktop${activeApp ? ' has-active-app' : ''}`}><aside className="app-dock">{apps.map(([id, label, icon]) => <button className={`dock-app${activeApp === id ? ' is-open is-active' : ''}`} type="button" key={id} onClick={() => setActiveApp(id)}><span className={iconClass(id)}>{icon}</span><span>{label}</span></button>)}</aside><section className="desktop-home"><div className="welcome-card"><span className="welcome-label">Workspace ready</span><h1>Welcome to your {title} workspace.</h1><p>You're working with <strong>{company}</strong>.</p><button className="open-mail-btn" type="button" onClick={() => setActiveApp('mail')}>Open Mail</button></div></section>{apps.map((app) => <AppWindow active={activeApp === app[0]} app={app} attempt={attempt} downloads={downloads} files={files} repository={repository} key={app[0]} onClose={() => setActiveApp(null)} onDownload={download} onSave={save} onRepositoryChange={setRepository} />)}{attempt.position_id === 'frontend-developer' && <TaskPanel attempt={attempt} progress={progress} />}</section></main>
}

function AppWindow({ active, app, attempt, downloads, files, repository, onClose, onDownload, onSave, onRepositoryChange }) {
  const [id, label, icon] = app
  const content = id === 'mail' ? <MailApp attempt={attempt} downloadedAttachments={downloads} repository={repository} onDownload={onDownload} onRepositoryChange={onRepositoryChange} /> : id === 'files' ? <FilesApp attempt={attempt} downloadedAttachments={downloads} projectFiles={files} /> : id === 'vscode' ? <VSCodeApp files={files} repository={repository} onSave={onSave} /> : id === 'terminal' ? <TerminalApp files={files} repository={repository} onRepositoryChange={onRepositoryChange} /> : id === 'browser' ? <BrowserApp attempt={attempt} /> : id === 'github' ? <GitHubApp repository={repository} onRepositoryChange={onRepositoryChange} /> : id === 'guide' ? <AdvisorApp attempt={attempt} /> : <div className="placeholder-content"><div className="placeholder-symbol">{icon}</div><h2>{label}</h2><p>This app will migrate in a later phase.</p></div>
  return <section className={`app-window ${id}-window${active ? ' is-active' : ''}`} aria-hidden={!active}><div className={`window-header ${id}-window-header`}><div className="window-title"><span className={iconClass(id)}>{icon}</span><strong>{label}</strong></div><div className="window-controls"><button type="button" onClick={onClose}>-</button><button type="button" onClick={onClose}>x</button></div></div>{content}</section>
}
export default SimulationDesktop
