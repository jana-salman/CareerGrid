import { useMemo, useState } from 'react'

function fileClass(path) {
  const extension = path.split('.').pop()?.toLowerCase()
  return ({ css: 'css', html: 'html', js: 'javascript', json: 'json', md: 'markdown', py: 'python' })[extension] || ''
}

function VSCodeApp({ files, repository, onSave }) {
  const [tabs, setTabs] = useState([])
  const [active, setActive] = useState(null)
  const [buffer, setBuffer] = useState('')
  const current = files.find((file) => file.path === active)
  const lineNumbers = useMemo(() => Array.from(
    { length: Math.max(1, buffer.split('\n').length) },
    (_, index) => index + 1,
  ), [buffer])

  const open = (file) => {
    setTabs((items) => items.includes(file.path) ? items : [...items, file.path])
    setActive(file.path)
    setBuffer(file.content || '')
  }
  const switchTab = (path) => {
    const file = files.find((item) => item.path === path)
    setActive(path)
    setBuffer(file?.content || '')
  }
  const closeTab = (path) => {
    const index = tabs.indexOf(path)
    const remaining = tabs.filter((item) => item !== path)
    setTabs(remaining)
    if (active === path) {
      const nextPath = remaining[Math.max(0, index - 1)] || null
      setActive(nextPath)
      setBuffer(files.find((item) => item.path === nextPath)?.content || '')
    }
  }
  const save = () => {
    if (!current) return
    onSave(current.path, buffer)
  }

  return (
    <div className="vscode-layout">
      <aside className="vscode-activity-bar">
        <button className="vscode-activity-button is-active" type="button" title="Explorer">▤</button>
        <button className="vscode-activity-button" type="button" title="Search">⌕</button>
        <button className="vscode-activity-button" type="button" title="Source Control" disabled>⑂</button>
        <button className="vscode-activity-button vscode-activity-bottom" type="button" title="Settings" disabled>⚙</button>
      </aside>

      <aside className="vscode-sidebar">
        <header className="vscode-sidebar-header"><span>EXPLORER</span><button type="button" title="Refresh Explorer">↻</button></header>
        <section className="vscode-project-explorer">
          <div className="vscode-project-title-row"><strong>{repository.repositoryName.toUpperCase()}</strong></div>
          <div className="vscode-file-tree">
            {files.map((file) => (
              <button
                className={`vscode-tree-row${active === file.path ? ' is-active' : ''}`}
                type="button"
                key={file.path}
                onClick={() => open(file)}
              >
                <span className="vscode-tree-arrow" />
                <span className={`vscode-tree-icon ${fileClass(file.path)}`}>◇</span>
                <span className="vscode-tree-label">{file.path}</span>
              </button>
            ))}
          </div>
        </section>
      </aside>

      <main className="vscode-editor-area">
        <div className="vscode-tabs">
          {tabs.map((path) => (
            <button className={`vscode-tab${active === path ? ' is-active' : ''}`} type="button" key={path} onClick={() => switchTab(path)}>
              <span className={`vscode-tree-icon ${fileClass(path)}`}>◇</span>
              <span className="vscode-tab-label">{path.split('/').pop()}</span>
              {active === path && current && buffer !== current.content && <span className="vscode-tab-unsaved" />}
              <span className="vscode-tab-close" role="button" tabIndex="0" onClick={(event) => { event.stopPropagation(); closeTab(path) }}>×</span>
            </button>
          ))}
        </div>

        {!current ? (
          <section className="vscode-empty-editor">
            <div className="vscode-logo-large">&lt;/&gt;</div>
            <h2>CareerGrid Code Workspace</h2>
            <p>Open a project from the Explorer, then select a file to begin working.</p>
            <div className="vscode-shortcuts">
              <span><kbd>Ctrl</kbd> + <kbd>S</kbd> Save file</span>
              <span><kbd>Ctrl</kbd> + <kbd>F</kbd> Search project</span>
            </div>
          </section>
        ) : (
          <section className="vscode-editor">
            <div className="vscode-editor-toolbar">
              <div className="vscode-breadcrumb">{current.path}</div>
              <button className="vscode-save-button" type="button" disabled={buffer === current.content} onClick={save}>Save</button>
            </div>
            <div className="vscode-code-wrapper">
              <div className="vscode-line-numbers">{lineNumbers.map((number) => <div className="vscode-line-number" key={number}>{number}</div>)}</div>
              <textarea className="vscode-code-editor" value={buffer} onChange={(event) => setBuffer(event.target.value)} spellCheck="false" />
            </div>
          </section>
        )}

        <footer className="vscode-status-bar">
          <div><span>{repository.currentBranch}</span></div>
          <div><span>{current ? 'Ln 1, Col 1' : 'No project'}</span><span>{current?.path.split('.').pop()?.toUpperCase() || 'Plain Text'}</span><span>UTF-8</span></div>
        </footer>
      </main>
    </div>
  )
}

export default VSCodeApp
