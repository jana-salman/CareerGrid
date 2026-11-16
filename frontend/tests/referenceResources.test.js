import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

import {
  activateTab,
  clearDraft,
  closeTab,
  createEditorState,
  editDraft,
  isOpenableReference,
  openTab,
  projectTabKey,
  referenceResources,
  referenceTabKey,
  resolveTab,
} from '../src/simulation/state/editorTabs.js'
import {
  buildScenarioAttachments,
  changedFiles,
  commit,
  diff,
  downloadAttachment,
  extractProjectArchive,
  createRepository,
  push,
  saveFile,
  stage,
} from '../src/simulation/state/repositoryModel.js'
import { processCompletionReply } from '../src/simulation/state/submissionWorkflow.js'
import { buildEvaluationEvidence } from '../src/simulation/state/evaluationEvidence.js'

const LOG = 'Case 1\nGET /api/users/1842\nActual: 500 Internal Server Error\n'
const TICKET = '# SUP-2291 - Team directory shows people who have left\n'
const scenario = {
  scenario_id: 'demo',
  project: {
    name: 'user-profile-service',
    archive_name: 'user-profile-service.zip',
    files: [
      { path: 'app.py', content: 'app = create_app()\n' },
      { path: 'services/user_service.py', content: 'def find_user(user_id):\n    return None\n' },
    ],
  },
  resources: [
    { id: 'production-error-log', name: 'production-error.log', type: 'text', content: LOG },
    { id: 'support-ticket', name: 'support-ticket-SUP-2291.md', type: 'text', content: TICKET },
  ],
}

// Mirrors the real flow: Mail attachments -> Download -> Files -> Extract.
function workspace() {
  const attachments = buildScenarioAttachments(scenario)
  let repository = createRepository(scenario.project.files, {
    name: 'user-profile-service', path: '/Projects/user-profile-service', requireExtraction: true,
  })
  for (const attachment of attachments) repository = downloadAttachment(repository, attachment).repository
  repository = extractProjectArchive(repository, attachments[0].id).repository
  return repository
}

function sources(repository) {
  return {
    files: Object.values(repository.branches[repository.currentBranch].workingTree),
    references: referenceResources(repository.workspace.downloadedAttachments),
  }
}

test('downloaded text resources become reference resources with their actual content', () => {
  const repository = workspace()
  const references = referenceResources(repository.workspace.downloadedAttachments)

  assert.deepEqual(references.map((item) => item.name), ['production-error.log', 'support-ticket-SUP-2291.md'])
  assert.equal(references[0].content, LOG)
  assert.equal(references[1].content, TICKET)
  // The project ZIP is extracted, not opened as a reference.
  const archive = repository.workspace.downloadedAttachments.find((item) => item.type === 'archive')
  assert.equal(isOpenableReference(archive), false)
  assert.equal(isOpenableReference(repository.workspace.downloadedAttachments.find((item) => item.name === 'production-error.log')), true)
})

test('opening a reference shows it read-only in its own tab', () => {
  const repository = workspace()
  const references = referenceResources(repository.workspace.downloadedAttachments)
  const key = referenceTabKey(references[0].id)
  const state = openTab(createEditorState(), key)
  const tab = resolveTab(state.active, sources(repository), state.drafts)

  assert.equal(state.active, key)
  assert.equal(tab.readOnly, true)
  assert.equal(tab.content, LOG)
  assert.equal(tab.label, 'production-error.log')
  assert.match(tab.path, /^Reference resources\//)

  const edited = editDraft(state, key, 'tampered')
  assert.equal(edited, state, 'reference tabs ignore edits')
  assert.equal(resolveTab(key, sources(repository), edited.drafts).content, LOG)
})

test('switching between code and reference tabs keeps unsaved code changes', () => {
  const repository = workspace()
  const code = projectTabKey('services/user_service.py')
  const other = projectTabKey('app.py')
  const reference = referenceTabKey('scenario-demo-resource-support-ticket')

  let state = openTab(createEditorState(), code)
  state = editDraft(state, code, 'def find_user(user_id):\n    return lookup(user_id)\n')
  state = openTab(state, reference)
  state = openTab(state, other)
  state = editDraft(state, other, 'app = create_app(config)\n')
  state = activateTab(state, reference)
  state = activateTab(state, code)

  const tab = resolveTab(state.active, sources(repository), state.drafts)
  assert.equal(tab.content, 'def find_user(user_id):\n    return lookup(user_id)\n')
  assert.equal(tab.dirty, true)
  assert.equal(resolveTab(other, sources(repository), state.drafts).dirty, true)
  assert.equal(resolveTab(reference, sources(repository), state.drafts).content, TICKET)
  assert.deepEqual(state.tabs, [code, reference, other])

  // Unsaved edits are not written to the repository until saved.
  assert.deepEqual(changedFiles(repository), [])
  const saved = saveFile(repository, 'services/user_service.py', tab.content).repository
  state = clearDraft(state, code)
  assert.equal(resolveTab(code, sources(saved), state.drafts).dirty, false)

  // Closing a tab discards its draft, as closing without saving does.
  state = closeTab(state, other)
  assert.equal(other in state.drafts, false)
  assert.equal(state.tabs.includes(other), false)
})

test('reference resources are never staged, committed, diffed, or submitted', async () => {
  let repository = workspace()
  repository = saveFile(repository, 'services/user_service.py', 'def find_user(user_id):\n    return {"id": user_id}\n').repository

  assert.deepEqual(changedFiles(repository), ['services/user_service.py'])
  assert.deepEqual(diff(repository).map((item) => item.path), ['services/user_service.py'])
  const staged = stage(repository, '.')
  assert.equal(staged.count, 1)
  repository = commit(staged.repository, 'Return available users').repository
  repository = push(repository).repository

  const committed = Object.keys(repository.branches.main.headSnapshot)
  for (const name of ['production-error.log', 'support-ticket-SUP-2291.md']) {
    assert.equal(committed.some((path) => path.includes(name)), false, name)
  }
  assert.equal(Object.keys(repository.baseline.snapshot).some((path) => path.endsWith('.log') || path.includes('SUP-2291')), false)

  const first = await processCompletionReply({ body: 'I fixed the lookup and tested it. My work is ready for review on main.', repository, threadId: 'task' })
  const confirmed = await processCompletionReply({ body: 'yes', repository: first.repository, threadId: 'task' })
  const evidence = buildEvaluationEvidence({
    attempt: { career_id: 'software-developer', company_id: 'technova', position_id: 'backend-developer' },
    repository: confirmed.repository,
    submission: confirmed.submission,
    taskMessage: { body: 'Fix it', id: 'task', replies: [], role: 'Lead', sender: 'Maya', subject: 'Incident' },
  })
  assert.deepEqual(evidence.changed_files.map((item) => item.path), ['services/user_service.py'])
  assert.equal(Object.keys(confirmed.submission.frozen.snapshot).some((path) => path.includes('SUP-2291')), false)
  // Downloads stay available for reading after submission.
  assert.equal(referenceResources(confirmed.repository.workspace.downloadedAttachments).length, 2)
})

test('Files offers Open in VS Code for downloaded text resources only, and VS Code renders them read-only', async () => {
  const read = (path) => readFile(new URL(path, import.meta.url), 'utf8')
  const [files, vscode, desktop] = await Promise.all([
    read('../src/simulation/apps/FilesApp.jsx'),
    read('../src/simulation/apps/VSCodeApp.jsx'),
    read('../src/simulation/SimulationDesktop.jsx'),
  ])
  assert.match(files, /location === '\/Downloads' && isOpenableReference\(selected\)/)
  assert.match(files, /Open in VS Code/)
  assert.match(files, /Extract to Projects/)
  assert.match(files, /files-text-preview/)
  assert.match(vscode, /REFERENCE RESOURCES/)
  assert.match(vscode, /readOnly=\{current\.readOnly\}/)
  assert.match(vscode, /Read-only reference resource/)
  assert.match(vscode, /referenceResources\(downloads\)/)
  assert.match(desktop, /setActiveApp\('vscode'\)/)
  assert.match(desktop, /openRequest=\{editorRequest\}/)
})
