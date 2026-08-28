const STORAGE_PREFIX = 'careergrid:repository:'

function copy(value) { return JSON.parse(JSON.stringify(value)) }
function slug(value) { return String(value || 'repository').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'repository' }
function snapshot(files) { return Object.fromEntries(files.map((file) => [file.path, copy(file)])) }
function sameFile(left, right) { return Boolean(left) === Boolean(right) && (!left || left.content === right.content) }

function fileTypeForPath(path) {
  const extension = String(path).split('.').pop().toLowerCase()
  return ({
    css: 'CSS', html: 'HTML', js: 'JavaScript', json: 'JSON', log: 'Log file', md: 'Markdown',
    py: 'Python', txt: 'Text file', ts: 'TypeScript', yaml: 'YAML', yml: 'YAML',
  })[extension] || 'Text file'
}

function fileSize(content) { return `${Math.max(1, Math.ceil(String(content || '').length / 1024))} KB` }

function buildScenarioAttachments(publicScenario = {}) {
  const project = publicScenario.project || {}
  if (!project.name || !project.archive_name || !Array.isArray(project.files)) return []
  const scenarioId = String(publicScenario.scenario_id || 'scenario')
  const archiveEntries = Object.fromEntries(project.files
    .filter((file) => file?.path && typeof file.content === 'string')
    .map((file) => [`${project.name}/${file.path}`, {
      content: file.content,
      fileType: fileTypeForPath(file.path),
      size: fileSize(file.content),
      type: 'file',
    }]))
  const attachments = [{
    archiveEntries,
    fileType: 'ZIP archive',
    id: `scenario-${scenarioId}-project`,
    name: project.archive_name,
    size: fileSize(JSON.stringify(project.files)),
    type: 'archive',
  }]
  for (const resource of publicScenario.resources || []) {
    if (!resource?.id || !resource?.name || typeof resource.content !== 'string') continue
    const name = String(resource.name).replace(/[\\/]+/g, '-')
    attachments.push({
      content: resource.content,
      fileType: fileTypeForPath(name),
      id: `scenario-${scenarioId}-resource-${resource.id}`,
      name,
      size: fileSize(resource.content),
      type: 'file',
    })
  }
  return attachments
}

function createWorkspace(files, options, extracted) {
  return {
    downloadedAttachments: [],
    extractedProjectPaths: extracted ? [options.path] : [],
    project: {
      archiveName: options.archiveName || `${options.name}.zip`,
      files: copy(files),
      name: options.name,
      path: options.path,
    },
    projectExtracted: extracted,
    version: 1,
  }
}

function createRepository(files = [], options = {}) {
  const path = options.path || '/Projects/careergrid-workspace'
  const name = options.name || 'careergrid-workspace'
  const projectExtracted = !options.requireExtraction
  const tree = snapshot(projectExtracted ? files : [])
  const initial = { id: 'initial', message: projectExtracted ? 'Initial workspace' : 'Project pending extraction', author: 'CareerGrid User', createdAt: new Date().toISOString(), snapshot: copy(tree) }
  return {
    rootPath: path, repositoryName: name, repositorySlug: slug(name), defaultBranch: 'main', currentBranch: 'main',
    branches: { main: { commits: [initial], headSnapshot: copy(tree), workingTree: copy(tree), stagedPaths: [], stagedSnapshot: {} } },
    remote: { pushedBranches: [], branchHeads: {} }, pullRequests: [], submissions: {}, submissionCandidates: {}, evaluations: {},
    workspace: createWorkspace(files, { ...options, name, path }, projectExtracted),
  }
}

function normalizeRepository(repository, files = [], options = {}) {
  const next = copy(repository)
  next.remote ||= { pushedBranches: [], branchHeads: {} }; next.remote.pushedBranches ||= []; next.remote.branchHeads ||= {}
  next.pullRequests ||= []; next.submissions ||= {}; next.submissionCandidates ||= {}; next.evaluations ||= {}
  Object.values(next.branches || {}).forEach((branch) => {
    branch.commits ||= []; branch.headSnapshot ||= {}; branch.workingTree ||= copy(branch.headSnapshot); branch.stagedPaths ||= []
    branch.stagedSnapshot ||= Object.fromEntries(branch.stagedPaths.filter((path) => branch.workingTree[path]).map((path) => [path, copy(branch.workingTree[path])]))
  })
  if (!next.workspace) {
    const branch = next.branches?.[next.currentBranch]
    const restoredFiles = files.length ? files : Object.values(branch?.workingTree || {})
    next.workspace = createWorkspace(restoredFiles, {
      ...options,
      name: options.name || next.repositoryName,
      path: options.path || next.rootPath,
    }, true)
  }
  return next
}

function repositoryStorageKey(attemptId) { return `${STORAGE_PREFIX}${String(attemptId)}` }
function loadRepository(attemptId, files, options, storage = globalThis.localStorage) {
  try { const stored = storage?.getItem(repositoryStorageKey(attemptId)); if (stored) return normalizeRepository(JSON.parse(stored), files, options) } catch { /* use a fresh in-memory repository */ }
  return createRepository(files, options)
}
function persistRepository(attemptId, repository, storage = globalThis.localStorage) {
  try { storage?.setItem(repositoryStorageKey(attemptId), JSON.stringify(repository)) } catch { /* keep the workspace usable in memory */ }
}

function downloadAttachment(repository, attachment) {
  const next = copy(repository)
  if (!attachment?.id || !attachment?.name) return { repository: next, error: 'Attachment is unavailable.' }
  const downloads = next.workspace?.downloadedAttachments
  if (!downloads) return { repository: next, error: 'Workspace downloads are unavailable.' }
  if (!downloads.some((item) => item.id === attachment.id || item.name === attachment.name)) downloads.push(copy(attachment))
  return { repository: next, attachment: downloads.find((item) => item.id === attachment.id) }
}

function extractProjectArchive(repository, attachmentId) {
  const next = copy(repository)
  const workspace = next.workspace
  const archive = workspace?.downloadedAttachments?.find((item) => item.id === attachmentId || item.name === attachmentId)
  if (!archive || archive.type !== 'archive' || !archive.archiveEntries) {
    return { repository: next, error: 'This file cannot be extracted.' }
  }
  if (workspace.projectExtracted) {
    return { repository: next, alreadyExtracted: true, projectPath: workspace.project.path }
  }
  const tree = snapshot(workspace.project.files)
  const initial = next.branches.main.commits[0]
  initial.message = 'Initial project files'
  initial.snapshot = copy(tree)
  next.branches.main.headSnapshot = copy(tree)
  next.branches.main.workingTree = copy(tree)
  next.branches.main.stagedPaths = []
  next.branches.main.stagedSnapshot = {}
  workspace.projectExtracted = true
  if (!workspace.extractedProjectPaths.includes(workspace.project.path)) workspace.extractedProjectPaths.push(workspace.project.path)
  return { repository: next, projectPath: workspace.project.path }
}
function currentBranch(repository) { return repository.branches[repository.currentBranch] }
function changedFiles(repository) {
  const branch = currentBranch(repository); const paths = new Set([...Object.keys(branch.headSnapshot), ...Object.keys(branch.workingTree)])
  return [...paths].filter((path) => !sameFile(branch.headSnapshot[path], branch.workingTree[path]))
}
function diff(repository, branchName = repository.currentBranch) {
  const branch = repository.branches[branchName]; if (!branch) return []
  const paths = new Set([...Object.keys(branch.headSnapshot), ...Object.keys(branch.workingTree)])
  return [...paths].filter((path) => !sameFile(branch.headSnapshot[path], branch.workingTree[path])).map((path) => ({ path, before: branch.headSnapshot[path]?.content || '', after: branch.workingTree[path]?.content || '' }))
}
function saveFile(repository, path, content) {
  const next = copy(repository); const branch = currentBranch(next)
  if (!branch.workingTree[path]) return { repository: next, error: 'File not found.' }
  branch.workingTree[path].content = content; return { repository: next }
}
function createBranch(repository, branchName) {
  const next = copy(repository); const cleanName = String(branchName || '').trim()
  if (!cleanName || !/^[A-Za-z0-9._/-]+$/.test(cleanName)) return { repository: next, error: 'Invalid branch name.' }
  if (next.branches[cleanName]) return { repository: next, error: `A branch named '${cleanName}' already exists.` }
  const source = currentBranch(next)
  next.branches[cleanName] = { commits: copy(source.commits), headSnapshot: copy(source.headSnapshot), workingTree: copy(source.workingTree), stagedPaths: [], stagedSnapshot: {} }
  next.currentBranch = cleanName; return { repository: next, branch: cleanName }
}
function switchBranch(repository, branchName) {
  const next = copy(repository)
  if (!next.branches[branchName]) return { repository: next, error: `Branch '${branchName}' does not exist.` }
  if (changedFiles(next).length || currentBranch(next).stagedPaths.length) return { repository: next, error: 'Commit or discard your changes before switching branches.' }
  next.currentBranch = branchName; return { repository: next, branch: branchName }
}
function stage(repository, paths) {
  const next = copy(repository); const branch = currentBranch(next); const changed = changedFiles(next)
  const requested = paths === '.' ? changed : Array.isArray(paths) ? paths : [paths]; const selected = requested.filter((path) => changed.includes(path))
  selected.forEach((path) => { branch.stagedSnapshot[path] = branch.workingTree[path] ? copy(branch.workingTree[path]) : null })
  branch.stagedPaths = [...new Set([...branch.stagedPaths, ...selected])]; return { repository: next, count: selected.length }
}
function commit(repository, message) {
  const next = copy(repository); const branch = currentBranch(next); const cleanMessage = String(message || '').trim()
  if (!cleanMessage) return { repository: next, error: 'Commit message required.' }
  if (!branch.stagedPaths.length) return { repository: next, error: 'No staged changes.' }
  const committedSnapshot = copy(branch.headSnapshot)
  branch.stagedPaths.forEach((path) => { const stagedFile = branch.stagedSnapshot[path]; if (stagedFile) committedSnapshot[path] = copy(stagedFile); else delete committedSnapshot[path] })
  const record = { id: Date.now().toString(36), message: cleanMessage, author: 'CareerGrid User', createdAt: new Date().toISOString(), snapshot: copy(committedSnapshot) }
  const filesChanged = branch.stagedPaths.length; branch.commits.push(record); branch.headSnapshot = committedSnapshot; branch.stagedPaths = []; branch.stagedSnapshot = {}
  return { repository: next, commit: record, filesChanged }
}
function push(repository) {
  const next = copy(repository); const branchName = next.currentBranch; const branch = currentBranch(next)
  if (!next.remote.pushedBranches.includes(branchName)) next.remote.pushedBranches.push(branchName)
  next.remote.branchHeads[branchName] = branch.commits.at(-1)?.id; return { repository: next, branch: branchName }
}
function createPullRequest(repository, details) {
  const next = copy(repository); const { baseBranch, compareBranch, title, description = '' } = details
  if (!next.branches[baseBranch] || !next.branches[compareBranch]) return { repository: next, error: 'Select branches that exist in this repository.' }
  if (baseBranch === compareBranch || compareBranch === 'main') return { repository: next, error: 'Choose a feature branch to compare with main.' }
  if (!next.remote.pushedBranches.includes(compareBranch)) return { repository: next, error: 'Push this branch before opening a pull request.' }
  const baseIds = new Set(next.branches[baseBranch].commits.map((item) => item.id))
  if (!next.branches[compareBranch].commits.some((item) => !baseIds.has(item.id))) return { repository: next, error: 'This branch has no commits to compare with the base branch.' }
  if (!title?.trim()) return { repository: next, error: 'Add a pull request title.' }
  const id = Math.max(0, ...next.pullRequests.map((item) => Number(item.id) || 0)) + 1
  const pullRequest = { repositoryPath: next.rootPath, baseBranch, compareBranch, id, url: `https://github.com/careergrid-sim/${next.repositorySlug}/pull/${id}`, status: 'open', title: title.trim(), description: description.trim(), repositoryName: next.repositoryName, repositorySlug: next.repositorySlug, author: 'CareerGrid User', createdAt: new Date().toISOString() }
  next.pullRequests.push(pullRequest); return { repository: next, pullRequest }
}
function findPullRequestByUrl(repository, url) { return repository.pullRequests.find((item) => item.url === url) || null }
function validatePullRequest(repository, pullRequest) {
  const current = pullRequest && repository.pullRequests.find((item) => item.id === pullRequest.id && item.url === pullRequest.url)
  if (!current || current.repositoryPath !== repository.rootPath) return null
  const base = repository.branches[current.baseBranch]; const compare = repository.branches[current.compareBranch]
  if (!base || !compare || current.status !== 'open' || !repository.remote.pushedBranches.includes(current.compareBranch)) return null
  const baseIds = new Set(base.commits.map((item) => item.id)); return compare.commits.some((item) => !baseIds.has(item.id)) ? current : null
}

export {
  buildScenarioAttachments,
  changedFiles,
  commit,
  createBranch,
  createPullRequest,
  createRepository,
  diff,
  downloadAttachment,
  extractProjectArchive,
  findPullRequestByUrl,
  loadRepository,
  persistRepository,
  push,
  repositoryStorageKey,
  saveFile,
  stage,
  switchBranch,
  validatePullRequest,
}
