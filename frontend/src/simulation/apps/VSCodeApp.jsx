import { useEffect, useMemo, useState } from 'react'

import {
  activateTab,
  clearDraft,
  closeTab as closeEditorTab,
  createEditorState,
  editDraft,
  openTab,
  projectTabKey,
  referenceResources,
  referenceTabKey,
  resolveTab,
} from '../state/editorTabs.js'

function fileClass(path) {
  const extension = path.split('.').pop()?.toLowerCase()
  return ({ css: 'css', html: 'html', js: 'javascript', json: 'json', log: 'log', md: 'markdown', py: 'python' })[extension] || ''
}

function VSCodeApp({ downloads = [], files, openRequest, repository, onSave }) {
  const references = useMemo(() => referenceResources(downloads), [downloads])
  const [editor, setEditor] = useState(() => {
    const key = openRequest?.resourceId && referenceTabKey(openRequest.resourceId)
    return key && references.some((item) => referenceTabKey(item.id) === key)
      ? openTab(createEditorState(), key)
      : createEditorState()
  })
  const sources = useMemo(() => ({ files, references }), [files, references])
  const current = resolveTab(editor.active, sources, editor.drafts)
  const buffer = current?.content ?? ''
  const lineNumbers = useMemo(() => Array.from(
    { length: Math.max(1, buffer.split('\n').length) },
    (_, index) => index + 1,
  ), [buffer])

  // "Open in VS Code" from Files arrives as a request for a reference tab.
  useEffect(() => {
    if (!openRequest?.resourceId) return
    const key = referenceTabKey(openRequest.resourceId)
    if (references.some((item) => referenceTabKey(item.id) === key)) setEditor((state) => openTab(state, key))
  }, [openRequest, references])

  const open = (key) => setEditor((state) => openTab(state, key))
  const switchTab = (key) => setEditor((state) => activateTab(state, key))
  const closeTab = (key) => setEditor((state) => closeEditorTab(state, key))
  const edit = (content) => {
    if (current && !current.readOnly) setEditor((state) => editDraft(state, current.key, content))
  }
  const save = () => {
    if (!current || current.readOnly || !current.dirty) return
    const result = onSave(current.path, buffer)
    if (!result?.error) setEditor((state) => clearDraft(state, current.key))
  }
  const handleEditorKeyDown = (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
      event.preventDefault()
      save()
    }
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
            {files.map((file) => {
              const key = projectTabKey(file.path)
              return (
                <button
                  className={`vscode-tree-row${editor.active === key ? ' is-active' : ''}`}
                  type="button"
                  key={key}
                  onClick={() => open(key)}
                >
                  <span className="vscode-tree-arrow" />
                  <span className={`vscode-tree-icon ${fileClass(file.path)}`}>◇</span>
                  <span className="vscode-tree-label">{file.path}</span>
                  {key in editor.drafts && <span className="vscode-tab-unsaved" title="Unsaved changes" />}
                </button>
              )
            })}
          </div>
        </section>
        {references.length > 0 && (
          <section className="vscode-project-explorer vscode-reference-explorer" aria-label="Reference resources">
            <div className="vscode-project-title-row">
              <strong>REFERENCE RESOURCES</strong>
              <span className="vscode-readonly-badge">Read-only</span>
            </div>
            <p className="vscode-reference-note">Downloaded from Mail. Not part of the repository.</p>
            <div className="vscode-file-tree">
              {references.map((reference) => {
                const key = referenceTabKey(reference.id)
                return (
                  <button
                    className={`vscode-tree-row${editor.active === key ? ' is-active' : ''}`}
                    type="button"
                    key={key}
                    onClick={() => open(key)}
                  >
                    <span className="vscode-tree-arrow" />
                    <span className={`vscode-tree-icon ${fileClass(reference.name)}`}>◆</span>
                    <span className="vscode-tree-label">{reference.name}</span>
                  </button>
                )
              })}
            </div>
          </section>
        )}
      </aside>

      <main className="vscode-editor-area">
        <div className="vscode-tabs">
          {editor.tabs.map((key) => {
            const tab = resolveTab(key, sources, editor.drafts)
            if (!tab) return null
            return (
              <button className={`vscode-tab${editor.active === key ? ' is-active' : ''}${tab.readOnly ? ' is-reference' : ''}`} type="button" key={key} onClick={() => switchTab(key)}>
                <span className={`vscode-tree-icon ${fileClass(tab.label)}`}>{tab.readOnly ? '◆' : '◇'}</span>
                <span className="vscode-tab-label">{tab.label}</span>
                {tab.readOnly && <span className="vscode-tab-readonly">read-only</span>}
                {tab.dirty && <span className="vscode-tab-unsaved" title="Unsaved changes" />}
                <span className="vscode-tab-close" role="button" tabIndex="0" onClick={(event) => { event.stopPropagation(); closeTab(key) }}>×</span>
              </button>
            )
          })}
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
              {current.readOnly
                ? <span className="vscode-readonly-badge" role="note">Read-only reference resource</span>
                : <button className="vscode-save-button" type="button" disabled={!current.dirty} onClick={save}>Save</button>}
            </div>
            <div className="vscode-code-wrapper">
              <div className="vscode-line-numbers">{lineNumbers.map((number) => <div className="vscode-line-number" key={number}>{number}</div>)}</div>
              <textarea
                className={`vscode-code-editor${current.readOnly ? ' is-readonly' : ''}`}
                value={buffer}
                readOnly={current.readOnly}
                aria-readonly={current.readOnly}
                aria-label={current.readOnly ? `${current.label} (read-only reference)` : current.path}
                onChange={(event) => edit(event.target.value)}
                onKeyDown={handleEditorKeyDown}
                spellCheck="false"
              />
            </div>
          </section>
        )}

        <footer className="vscode-status-bar">
          <div><span>{repository.currentBranch}</span></div>
          <div>
            <span>{current ? (current.readOnly ? 'Read-only' : 'Ln 1, Col 1') : 'No project'}</span>
            <span>{current?.label.split('.').pop()?.toUpperCase() || 'Plain Text'}</span>
            <span>UTF-8</span>
          </div>
        </footer>
      </main>
    </div>
  )
}

export default VSCodeApp
