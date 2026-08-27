import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getFrontendSimulationProgress, getSimulationAttempt } from '../services/simulationApi.js'
import TaskPanel from './TaskPanel.jsx'
import MailApp from './apps/MailApp.jsx'
import FilesApp from './apps/FilesApp.jsx'
import VSCodeApp from './apps/VSCodeApp.jsx'
import TerminalApp from './apps/TerminalApp.jsx'

const apps = [['mail', 'Mail', 'M'], ['files', 'Files', 'F'], ['vscode', 'VS Code', '</>'], ['browser', 'Browser', 'O'], ['terminal', 'Terminal', '>_'], ['github', 'GitHub', 'GH'], ['guide', 'Guide', '?']]
const iconClass = (name) => `app-icon app-icon-${name}`

function SimulationDesktop() {
  const { attemptId } = useParams()
  const [attempt, setAttempt] = useState(null); const [progress, setProgress] = useState(null); const [activeApp, setActiveApp] = useState(null); const [error, setError] = useState('')
  const [downloads, setDownloads] = useState([]); const [files, setFiles] = useState([]); const [git, setGit] = useState({ branch: 'main', modified: [], staged: [], commits: [], pushed: false })
  useEffect(() => { let active = true; getSimulationAttempt(attemptId).then(async (loaded) => { const loadedProgress = loaded.position_id === 'frontend-developer' ? await getFrontendSimulationProgress(attemptId) : { current_step: 1, status: loaded.status }; if (active) { setAttempt(loaded); setProgress(loadedProgress); setFiles(loaded.public_scenario?.project?.files || []) } }).catch((err) => active && setError(err.message)); return () => { active = false } }, [attemptId])
  if (error) return <main className="workspace"><p>{error}</p></main>
  if (!attempt || !progress) return <main className="workspace"><p>Loading workspace...</p></main>
  const scenario = attempt.public_scenario || {}; const title = attempt.position_id?.replaceAll('-', ' ') || 'CareerGrid'; const company = scenario.company_name || attempt.company_id || 'your company'
  const download = (item) => setDownloads((items) => items.some((entry) => entry.name === item.name) ? items : [...items, item])
  const save = (path, content) => { setFiles((items) => items.map((file) => file.path === path ? { ...file, content } : file)); setGit((state) => ({ ...state, modified: state.modified.includes(path) ? state.modified : [...state.modified, path] })) }
  const gitAction = (action, value) => setGit((state) => action === 'branch' ? { ...state, branch: value || state.branch } : action === 'stage' ? { ...state, staged: [...new Set([...state.staged, ...value])] } : action === 'commit' && value ? { ...state, modified: state.modified.filter((path) => !state.staged.includes(path)), staged: [], commits: [...state.commits, value] } : action === 'push' ? { ...state, pushed: true } : state)
  return <main className="workspace"><header className="workspace-topbar"><div className="workspace-brand"><div className="brand-icon">CG</div><div className="brand-text"><strong>CareerGrid</strong><span>Interactive Career Simulation</span></div></div><div className="workspace-user"><div className="user-avatar">U</div><div className="user-information"><strong>User</strong><span>{title}</span></div></div></header><section className={`desktop${activeApp ? ' has-active-app' : ''}`}><aside className="app-dock">{apps.map(([id, label, icon]) => <button className={`dock-app${activeApp === id ? ' is-open is-active' : ''}`} type="button" key={id} onClick={() => setActiveApp(id)}><span className={iconClass(id)}>{icon}</span><span>{label}</span></button>)}</aside><section className="desktop-home"><div className="welcome-card"><span className="welcome-label">Workspace ready</span><h1>Welcome to your {title} workspace.</h1><p>You're working with <strong>{company}</strong>.</p><button className="open-mail-btn" type="button" onClick={() => setActiveApp('mail')}>Open Mail</button></div></section>{apps.map((app) => <AppWindow active={activeApp === app[0]} app={app} attempt={attempt} downloads={downloads} files={files} git={git} key={app[0]} onClose={() => setActiveApp(null)} onDownload={download} onSave={save} onGit={gitAction} />)}{attempt.position_id === 'frontend-developer' && <TaskPanel attempt={attempt} progress={progress} />}</section></main>
}

function AppWindow({ active, app, attempt, downloads, files, git, onClose, onDownload, onSave, onGit }) {
  const [id, label, icon] = app
  const content = id === 'mail' ? <MailApp attempt={attempt} downloadedAttachments={downloads} onDownload={onDownload} /> : id === 'files' ? <FilesApp attempt={attempt} downloadedAttachments={downloads} /> : id === 'vscode' ? <VSCodeApp files={files} onSave={onSave} /> : id === 'terminal' ? <TerminalApp files={files} git={git} onGit={onGit} /> : <div className="placeholder-content"><div className="placeholder-symbol">{icon}</div><h2>{label}</h2><p>This app will migrate in a later phase.</p></div>
  return <section className={`app-window ${id}-window${active ? ' is-active' : ''}`} aria-hidden={!active}><div className={`window-header ${id}-window-header`}><div className="window-title"><span className={iconClass(id)}>{icon}</span><strong>{label}</strong></div><div className="window-controls"><button type="button" onClick={onClose}>-</button><button type="button" onClick={onClose}>x</button></div></div>{content}</section>
}
export default SimulationDesktop
