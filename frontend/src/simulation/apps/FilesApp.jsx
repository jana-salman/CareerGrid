import { useMemo, useState } from 'react'

function FilesApp({ attempt, downloadedAttachments }) {
  const scenario = attempt.public_scenario || {}
  const [location, setLocation] = useState('/Downloads')
  const [selected, setSelected] = useState(null)
  const files = useMemo(() => {
    if (location === '/Downloads') return downloadedAttachments.map((item) => ({ ...item, type: item.type || 'file', fileType: item.fileType || 'Attachment' }))
    if (location === '/Projects') return (scenario.project?.files || []).map((item) => ({ ...item, type: 'file', fileType: item.fileType || 'Project file' }))
    return []
  }, [downloadedAttachments, location, scenario.project?.files])
  return <div className="files-layout"><aside className="files-sidebar"><div className="files-sidebar-heading">Locations</div>{[['/', 'Home'], ['/Desktop', 'Desktop'], ['/Downloads', 'Downloads'], ['/Documents', 'Documents'], ['/Projects', 'Projects']].map(([path, label]) => <button className={`files-location${location === path ? ' is-active' : ''}`} type="button" key={path} onClick={() => { setLocation(path); setSelected(null) }}><span>File</span><span>{label}</span></button>)}</aside><section className="files-main"><header className="files-toolbar"><div className="files-breadcrumb"><button className="files-breadcrumb-button" type="button">Home</button><span className="files-breadcrumb-separator">/</span><button className="files-breadcrumb-button" type="button">{location.slice(1) || 'Home'}</button></div><button className="files-refresh-button" type="button">Refresh</button></header><div className="files-content"><section className="files-list-panel"><div className="files-list-heading"><span>Name</span><span>Type</span><span>Size</span></div><div className="files-list">{files.length === 0 ? <p className="files-empty-folder">This folder is empty.</p> : files.map((file) => <button className={`files-row${selected?.name === file.name ? ' is-selected' : ''}`} type="button" key={file.name} onClick={() => setSelected(file)}><span className="files-name-cell"><span className={`files-item-icon ${file.type === 'archive' ? 'archive' : ''}`}>{file.type === 'archive' ? 'ZIP' : 'FILE'}</span><strong className="files-name">{file.name || file.path}</strong></span><span className="files-type">{file.fileType || 'File'}</span><span className="files-size">{file.size || '-'}</span></button>)}</div></section><aside className="files-preview">{!selected ? <div className="files-preview-empty"><div className="files-preview-empty-icon">FILE</div><strong>Select a file</strong><p>Choose a file to see its details.</p></div> : <div className="files-preview-content"><div className="files-preview-icon">FILE</div><h2>{selected.name || selected.path}</h2><span className="files-preview-type">{selected.fileType || 'File'}</span>{selected.content && <pre className="files-text-preview">{selected.content}</pre>}</div>}</aside></div></section></div>
}

export default FilesApp
