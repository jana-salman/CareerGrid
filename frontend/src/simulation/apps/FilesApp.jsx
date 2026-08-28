import { useEffect, useMemo, useState } from 'react'

const locations = [
  ['/', '⌂', 'Home'],
  ['/Desktop', '▣', 'Desktop'],
  ['/Downloads', '↓', 'Downloads'],
  ['/Documents', '▤', 'Documents'],
  ['/Projects', '⌘', 'Projects'],
]

function FilesApp({ downloadedAttachments, projectFiles, repository, onExtract }) {
  const [location, setLocation] = useState('/Downloads')
  const [selectedKey, setSelectedKey] = useState(null)
  const [toast, setToast] = useState('')
  const projectPath = repository.workspace?.project?.path || repository.rootPath
  const projectName = repository.workspace?.project?.name || repository.repositoryName
  const projectExtracted = Boolean(repository.workspace?.projectExtracted)

  const files = useMemo(() => {
    if (location === '/Downloads') return downloadedAttachments
    if (location === '/Projects' && projectExtracted) {
      return [{ fileType: 'File folder', name: projectName, path: projectPath, type: 'folder' }]
    }
    if (location === projectPath && projectExtracted) {
      return projectFiles.map((item) => ({
        ...item,
        fileType: item.fileType || 'Project file',
        name: item.name || item.path.split('/').pop(),
        type: 'file',
      }))
    }
    return []
  }, [downloadedAttachments, location, projectExtracted, projectFiles, projectName, projectPath])

  const selected = files.find((item) => (item.id || item.path || item.name) === selectedKey) || null

  useEffect(() => {
    if (!toast) return undefined
    const timer = window.setTimeout(() => setToast(''), 2300)
    return () => window.clearTimeout(timer)
  }, [toast])

  const navigateTo = (path) => {
    setLocation(path)
    setSelectedKey(null)
  }

  const extract = () => {
    if (!selected) return
    const result = onExtract(selected.id || selected.name)
    if (result.error) {
      setToast(result.error)
      return
    }
    setToast('Project extracted to Projects')
    navigateTo(result.projectPath)
  }

  const breadcrumbParts = location.split('/').filter(Boolean)
  let breadcrumbPath = ''

  return (
    <div className="files-layout">
      <aside className="files-sidebar">
        <div className="files-sidebar-heading">Locations</div>
        {locations.map(([path, icon, label]) => (
          <button
            className={`files-location${location === path || (path !== '/' && location.startsWith(`${path}/`)) ? ' is-active' : ''}`}
            type="button"
            key={path}
            onClick={() => navigateTo(path)}
          >
            <span>{icon}</span><span>{label}</span>
          </button>
        ))}
      </aside>

      <section className="files-main">
        <header className="files-toolbar">
          <div className="files-breadcrumb">
            <button className="files-breadcrumb-button" type="button" onClick={() => navigateTo('/')}>Home</button>
            {breadcrumbParts.map((part) => {
              breadcrumbPath += `/${part}`
              const destination = breadcrumbPath
              return <span key={destination}>
                <span className="files-breadcrumb-separator">/</span>
                <button className="files-breadcrumb-button" type="button" onClick={() => navigateTo(destination)}>{part}</button>
              </span>
            })}
          </div>
          <button className="files-refresh-button" type="button" onClick={() => setSelectedKey(null)}>↻ Refresh</button>
        </header>

        <div className="files-content">
          <section className="files-list-panel">
            <div className="files-list-heading"><span>Name</span><span>Type</span><span>Size</span></div>
            <div className="files-list">
              {files.length === 0 ? <div className="files-empty-folder">This folder is empty.</div> : files.map((file) => {
                const key = file.id || file.path || file.name
                const iconClass = file.type === 'folder' ? 'folder' : file.type === 'archive' ? 'archive' : ''
                return (
                  <button
                    className={`files-row${selectedKey === key ? ' is-selected' : ''}`}
                    type="button"
                    key={key}
                    onClick={() => file.type === 'folder' ? navigateTo(file.path) : setSelectedKey(key)}
                  >
                    <span className="files-name-cell">
                      <span className={`files-item-icon ${iconClass}`}>{file.type === 'folder' ? 'DIR' : file.type === 'archive' ? 'ZIP' : 'FILE'}</span>
                      <span className="files-name">{file.name || file.path}</span>
                    </span>
                    <span className="files-type">{file.fileType || 'File'}</span>
                    <span className="files-size">{file.size || '—'}</span>
                  </button>
                )
              })}
            </div>
          </section>

          <aside className="files-preview">
            {!selected ? (
              <div className="files-preview-empty">
                <div className="files-preview-empty-icon">▰</div>
                <strong>Select a file</strong>
                <p>Choose a file to see its details.</p>
              </div>
            ) : (
              <div className="files-preview-content">
                <div className="files-preview-icon">{selected.type === 'archive' ? 'ZIP' : 'FILE'}</div>
                <h2>{selected.name || selected.path}</h2>
                <span className="files-preview-type">{selected.fileType || 'File'} • {selected.size || 'Unknown size'}</span>
                {selected.type === 'archive' && (
                  <>
                    <div className="files-preview-actions">
                      <button className="files-action-button" type="button" onClick={extract}>Extract to Projects</button>
                    </div>
                    <div className="files-archive-preview">
                      <div className="files-archive-title">Archive contents</div>
                      {Object.keys(selected.archiveEntries || {}).map((entry) => <div className="files-archive-entry" key={entry}>{entry}</div>)}
                    </div>
                  </>
                )}
                {selected.type === 'file' && <pre className="files-text-preview">{selected.content || 'No preview available.'}</pre>}
              </div>
            )}
          </aside>
        </div>
      </section>

      {toast && <div className="files-toast" role="status">{toast}</div>}
    </div>
  )
}

export default FilesApp
