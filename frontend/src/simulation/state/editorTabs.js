// Editor tab state for the simulated VS Code.
//
// Two kinds of tabs exist:
// - project files (editable; unsaved text is kept per tab in `drafts`)
// - reference resources downloaded from Mail (read-only; never part of Git)
//
// Reference resources are read from the workspace's downloaded attachments,
// which live outside the repository branches, so they cannot be staged,
// committed, diffed, or submitted.

const PROJECT_PREFIX = 'project:'
const REFERENCE_PREFIX = 'reference:'

function projectTabKey(path) { return `${PROJECT_PREFIX}${path}` }
function referenceTabKey(id) { return `${REFERENCE_PREFIX}${id}` }
function isReferenceKey(key) { return String(key).startsWith(REFERENCE_PREFIX) }

// Downloaded text attachments (not archives, not generated report links).
function referenceResources(downloadedAttachments = []) {
  return downloadedAttachments
    .filter((item) => item?.type === 'file' && item.id && item.name && typeof item.content === 'string')
    .map((item) => ({ content: item.content, fileType: item.fileType, id: item.id, name: item.name, size: item.size }))
}

function isOpenableReference(item) {
  return item?.type === 'file' && Boolean(item.id) && typeof item.content === 'string'
}

function createEditorState() { return { active: null, drafts: {}, tabs: [] } }

function openTab(state, key) {
  return { ...state, active: key, tabs: state.tabs.includes(key) ? state.tabs : [...state.tabs, key] }
}

function activateTab(state, key) {
  return state.tabs.includes(key) ? { ...state, active: key } : state
}

// Closing a tab discards its draft, like closing without saving.
function closeTab(state, key) {
  const index = state.tabs.indexOf(key)
  if (index === -1) return state
  const tabs = state.tabs.filter((item) => item !== key)
  const { [key]: _discarded, ...drafts } = state.drafts
  const active = state.active === key ? tabs[Math.max(0, index - 1)] || null : state.active
  return { active, drafts, tabs }
}

// Only project files accept edits; reference tabs are read-only.
function editDraft(state, key, content) {
  if (isReferenceKey(key) || !state.tabs.includes(key)) return state
  return { ...state, drafts: { ...state.drafts, [key]: String(content) } }
}

function clearDraft(state, key) {
  if (!(key in state.drafts)) return state
  const { [key]: _saved, ...drafts } = state.drafts
  return { ...state, drafts }
}

// Resolves a tab key to what the editor shows.
function resolveTab(key, { files = [], references = [] } = {}, drafts = {}) {
  if (!key) return null
  if (isReferenceKey(key)) {
    const reference = references.find((item) => referenceTabKey(item.id) === key)
    if (!reference) return null
    return { content: reference.content, dirty: false, key, label: reference.name, path: `Reference resources/${reference.name}`, readOnly: true, saved: reference.content }
  }
  const file = files.find((item) => projectTabKey(item.path) === key)
  if (!file) return null
  const text = key in drafts ? drafts[key] : file.content || ''
  return { content: text, dirty: text !== (file.content || ''), key, label: file.path.split('/').pop(), path: file.path, readOnly: false, saved: file.content || '' }
}

export {
  activateTab,
  clearDraft,
  closeTab,
  createEditorState,
  editDraft,
  isOpenableReference,
  isReferenceKey,
  openTab,
  projectTabKey,
  referenceResources,
  referenceTabKey,
  resolveTab,
}
