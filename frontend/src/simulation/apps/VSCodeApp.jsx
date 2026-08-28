import { useState } from 'react'

function VSCodeApp({ files, repository, onSave }) {
  const [tabs, setTabs] = useState([])
  const [active, setActive] = useState(null)
  const [buffer, setBuffer] = useState('')
  const open = (file) => { setTabs((items) => items.some((item) => item.path === file.path) ? items : [...items, file]); setActive(file.path); setBuffer(file.content || '') }
  const current = files.find((file) => file.path === active)
  const switchTab = (path) => { const file = files.find((item) => item.path === path); setActive(path); setBuffer(file?.content || '') }
  return <div className="vscode-layout"><aside className="vscode-activity-bar"><button className="vscode-activity-button is-active" type="button">Explorer</button></aside><aside className="vscode-sidebar"><header className="vscode-sidebar-header"><span>EXPLORER</span></header><section className="vscode-project-explorer"><div className="vscode-project-title-row"><strong>PROJECT</strong></div><div className="vscode-file-tree">{files.map((file) => <button className="vscode-file-tree-item" type="button" key={file.path} onClick={() => open(file)}>{file.path}</button>)}</div></section></aside><main className="vscode-editor-area"><div className="vscode-tabs">{tabs.map((tab) => <button className={`vscode-tab${active === tab.path ? ' is-active' : ''}`} type="button" key={tab.path} onClick={() => switchTab(tab.path)}>{tab.path.split('/').pop()}</button>)}</div>{!current ? <section className="vscode-empty-editor"><div className="vscode-logo-large">&lt;/&gt;</div><h2>CareerGrid Code Workspace</h2><p>Open a project file from the Explorer to begin working.</p></section> : <section className="vscode-editor"><div className="vscode-editor-toolbar"><div className="vscode-breadcrumb">{current.path}</div><button className="vscode-save-button" type="button" onClick={() => onSave(current.path, buffer)}>Save</button></div><div className="vscode-code-wrapper"><textarea className="vscode-code-editor" value={buffer} onChange={(event) => setBuffer(event.target.value)} spellCheck="false" /></div></section>}<footer className="vscode-status-bar"><span>{repository.currentBranch}</span><span>{current?.path || 'No project'}</span><span>UTF-8</span></footer></main></div>
}

export default VSCodeApp
