import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

import {
  commit,
  createBranch,
  createPullRequest,
  createRepository,
  downloadAttachment,
  extractProjectArchive,
  loadRepository,
  push,
  saveFile,
  stage,
  switchBranch,
} from '../src/simulation/state/repositoryModel.js'
import {
  MAIN_SUBMISSION_ACKNOWLEDGEMENT,
  SUBMISSION_HELP,
  classifyCompletionMessage,
  processCompletionReply,
  submissionState,
} from '../src/simulation/state/submissionWorkflow.js'
import {
  buildEvaluationEvidence,
  markEvaluationFailed,
  recordEvaluation,
  recoverInterruptedEvaluations,
} from '../src/simulation/state/evaluationEvidence.js'

const ORIGINAL = [
  { path: 'app.py', content: 'def handler():\n    return 500\n' },
  { path: 'tests/test_app.py', content: 'def test_handler():\n    pass\n' },
]
const attempt = { attempt_id: 'a-1', career_id: 'software-developer', company_id: 'technova', position_id: 'backend-developer' }
const taskMessage = { body: 'Fix the handler.', id: 'task', replies: [], role: 'Lead', sender: 'Maya', subject: 'Handler bug' }

function fresh() {
  return createRepository(structuredClone(ORIGINAL), { name: 'svc', path: '/Projects/svc' })
}

function commitAll(repository, path, content, message) {
  let next = saveFile(repository, path, content).repository
  next = stage(next, '.').repository
  return commit(next, message).repository
}

function mainWork() {
  let repository = commitAll(fresh(), 'app.py', 'def handler():\n    return 200\n', 'Return 200 from handler')
  repository = push(repository).repository
  return repository
}

async function submit(repository, body, evaluate) {
  const first = await processCompletionReply({ body, repository, threadId: 'task' })
  const second = await processCompletionReply({ body: 'yes', evaluate, messageId: 'm2', repository: first.repository, threadId: 'task' })
  return { first, second }
}

const READY_ON_MAIN = 'Hi Maya, I fixed the handler so it returns 200 and tested both paths. My work is ready for review on main.'

test('direct-to-main submission: explicit intent, confirmation, then one evaluation of the pushed commit', async () => {
  const repository = mainWork()
  let evaluated = null
  const { first, second } = await submit(repository, READY_ON_MAIN, async (next, submission) => {
    evaluated = buildEvaluationEvidence({ attempt, repository: next, submission, taskMessage })
    return { failed: false, repository: next }
  })

  assert.equal(first.candidate.mode, 'main')
  assert.match(first.advisorReply, /work pushed to main .*Reply yes/)
  assert.equal(first.repository.submissions.task, undefined, 'nothing is submitted before confirmation')
  assert.equal(second.evaluationTriggered, true)
  assert.equal(second.advisorReply, MAIN_SUBMISSION_ACKNOWLEDGEMENT)
  assert.equal(evaluated.submission_mode, 'main')
  assert.equal(evaluated.pull_request, null)
  assert.equal(evaluated.git_workflow.opened_pull_request, false)
  assert.equal(evaluated.comparison.basis, 'original_starter_project')
  assert.deepEqual(evaluated.changed_files.map((item) => item.path), ['app.py'])
  assert.equal(evaluated.changed_files[0].before, ORIGINAL[0].content)
  assert.equal(evaluated.verification.tests_executed_by_workspace, false)
})

test('branch and pull request submission still works and is compared with the original project', async () => {
  let repository = createBranch(fresh(), 'feature/fix').repository
  repository = commitAll(repository, 'app.py', 'def handler():\n    return 404\n', 'Return 404')
  repository = push(repository).repository
  const created = createPullRequest(repository, { baseBranch: 'main', compareBranch: 'feature/fix', title: 'Fix handler' })
  let evidence = null
  const { first, second } = await submit(created.repository, `I fixed and tested the handler. ${created.pullRequest.url}`, async (next, submission) => {
    evidence = buildEvaluationEvidence({ attempt, repository: next, submission, taskMessage })
    return { failed: false, repository: next }
  })

  assert.equal(first.candidate.mode, 'pull_request')
  assert.equal(second.submission.pullRequestUrl, created.pullRequest.url)
  assert.equal(evidence.submission_mode, 'pull_request')
  assert.equal(evidence.git_workflow.opened_pull_request, true)
  assert.deepEqual(evidence.changed_files.map((item) => item.path), ['app.py'])
})

test('the original baseline is preserved even after main changes, and PR evidence ignores later main commits', async () => {
  let repository = createBranch(fresh(), 'feature/fix').repository
  repository = commitAll(repository, 'app.py', 'def handler():\n    return 404\n', 'Return 404')
  repository = push(repository).repository
  repository = switchBranch(repository, 'main').repository
  repository = commitAll(repository, 'tests/test_app.py', 'def test_handler():\n    assert True\n', 'Unrelated main change')
  repository = push(repository).repository
  repository = switchBranch(repository, 'feature/fix').repository

  assert.deepEqual(Object.keys(repository.baseline.snapshot).sort(), ['app.py', 'tests/test_app.py'])
  assert.equal(repository.baseline.snapshot['tests/test_app.py'].content, ORIGINAL[1].content)

  const created = createPullRequest(repository, { baseBranch: 'main', compareBranch: 'feature/fix', title: 'Fix' })
  const { second } = await submit(created.repository, `Fixed and tested. ${created.pullRequest.url}`)
  const evidence = buildEvaluationEvidence({ attempt, repository: second.repository, submission: second.submission, taskMessage })
  assert.deepEqual(evidence.changed_files.map((item) => item.path), ['app.py'])
})

test('evidence is frozen at confirmation: later edits, commits, and pushes do not change it', async () => {
  const { second } = await submit(mainWork(), READY_ON_MAIN)
  let later = commitAll(second.repository, 'app.py', 'def handler():\n    raise SystemExit\n', 'Break it later')
  later = push(later).repository
  const evidence = buildEvaluationEvidence({ attempt, repository: later, submission: later.submissions.task, taskMessage })
  assert.equal(evidence.changed_files[0].after, 'def handler():\n    return 200\n')
  assert.equal(evidence.repository.commit_id, second.submission.commitId)
})

test('uncommitted, unpushed, and empty main submissions are explained instead of evaluated', async () => {
  const uncommitted = saveFile(fresh(), 'app.py', 'def handler():\n    return 200\n').repository
  const unpushed = commitAll(fresh(), 'app.py', 'def handler():\n    return 200\n', 'Local only')

  const results = await Promise.all([
    processCompletionReply({ body: READY_ON_MAIN, repository: uncommitted, threadId: 'task' }),
    processCompletionReply({ body: READY_ON_MAIN, repository: unpushed, threadId: 'task' }),
    processCompletionReply({ body: READY_ON_MAIN, repository: push(fresh()).repository, threadId: 'task' }),
  ])
  assert.match(results[0].advisorReply, /not committed/)
  assert.match(results[1].advisorReply, /not been pushed/)
  assert.match(results[2].advisorReply, /no changes compared with the original project/)
  for (const result of results) assert.equal(result.candidate, undefined)

  let partlyPushed = mainWork()
  partlyPushed = commitAll(partlyPushed, 'app.py', 'def handler():\n    return 201\n', 'Not pushed yet')
  const ahead = await processCompletionReply({ body: READY_ON_MAIN, repository: partlyPushed, threadId: 'task' })
  assert.match(ahead.advisorReply, /have not been pushed/)

  const withLocalEdits = saveFile(mainWork(), 'tests/test_app.py', 'draft').repository
  const warned = await processCompletionReply({ body: READY_ON_MAIN, repository: withLocalEdits, threadId: 'task' })
  assert.equal(warned.candidate.mode, 'main')
  assert.match(warned.advisorReply, /uncommitted edits \(tests\/test_app\.py\).*NOT be included/)
})

test('main has no work but a feature branch does: guidance points to a PR', async () => {
  let repository = createBranch(fresh(), 'feature/x').repository
  repository = commitAll(repository, 'app.py', 'x', 'Work on branch')
  repository = push(repository).repository
  repository = switchBranch(repository, 'main').repository
  repository = push(repository).repository
  const result = await processCompletionReply({ body: READY_ON_MAIN, repository, threadId: 'task' })
  assert.match(result.advisorReply, /feature\/x/)
})

test('questions and progress updates never start an assessment', async () => {
  const repository = mainWork()
  const question = await processCompletionReply({ body: 'How do I submit without a pull request?', repository, threadId: 'task' })
  assert.equal(question.advisorReply, SUBMISSION_HELP)
  assert.equal(question.candidate, undefined)

  for (const body of [
    'Is it ok if I push directly to main?',
    'I am still working on the fix, will push to main later.',
    'Almost done, the fix is ready but I still need to test it.',
    'What does the log mean?',
    'Thanks!',
  ]) {
    const result = await processCompletionReply({ body, repository, threadId: 'task' })
    assert.equal(result.candidate, undefined, body)
    assert.equal(result.evaluationTriggered, false, body)
    assert.equal(Object.keys(result.repository.submissionCandidates).length, 0, body)
  }
  assert.equal(classifyCompletionMessage('I am still working on it').intent, 'progress')
  assert.equal(classifyCompletionMessage('What should I check next?').intent, 'question')
  assert.equal(classifyCompletionMessage('I pushed my changes to main and it is ready for review.').intent, 'direct_submission')
})

test('declining, re-pushing before confirmation, duplicates, and retries are handled', async () => {
  const first = await processCompletionReply({ body: READY_ON_MAIN, repository: mainWork(), threadId: 'task' })
  const cancelled = await processCompletionReply({ body: 'no', repository: first.repository, threadId: 'task' })
  assert.equal(cancelled.repository.submissionCandidates.task, undefined)

  // Pushing new work after sharing but before "yes" must not silently swap evidence.
  const again = await processCompletionReply({ body: READY_ON_MAIN, repository: cancelled.repository, threadId: 'task' })
  const changed = push(commitAll(again.repository, 'app.py', 'def handler():\n    return 204\n', 'More')).repository
  const stale = await processCompletionReply({ body: 'yes', repository: changed, threadId: 'task' })
  assert.match(stale.advisorReply, /changed after you shared it/)
  assert.equal(stale.repository.submissions.task, undefined)

  let evaluations = 0
  const failingEvaluate = async (next) => {
    evaluations += 1
    return { advisorReply: 'Review failed. Reply retry.', failed: true, repository: markEvaluationFailed(next, 'task', 'down').repository }
  }
  const { second } = await submit(mainWork(), READY_ON_MAIN, failingEvaluate)
  assert.equal(submissionState(second.repository, 'task').stage, 'evaluation_failed')

  const notRetry = await processCompletionReply({ body: 'hello?', evaluate: failingEvaluate, repository: second.repository, threadId: 'task' })
  assert.equal(notRetry.evaluationTriggered, false)

  let retriedWith = null
  const retried = await processCompletionReply({
    body: 'retry',
    evaluate: async (next, submission) => {
      evaluations += 1
      retriedWith = submission
      return { failed: false, repository: recordEvaluation(next, 'task', { overall_score: 80 }).repository }
    },
    repository: second.repository,
    threadId: 'task',
  })
  assert.equal(retried.evaluationTriggered, true)
  assert.equal(retriedWith.commitId, second.submission.commitId, 'retry evaluates the same frozen submission')

  const duplicate = await processCompletionReply({ body: READY_ON_MAIN, evaluate: failingEvaluate, repository: retried.repository, threadId: 'task' })
  assert.equal(duplicate.advisorReply, 'This task has already been submitted and evaluated.')
  assert.equal(evaluations, 2)
})

test('interrupted evaluations become retryable after reopening the workspace', () => {
  const repository = structuredClone(mainWork())
  repository.evaluations.task = { status: 'pending', startedAt: new Date().toISOString() }
  const recovered = recoverInterruptedEvaluations(repository)
  assert.equal(recovered.evaluations.task.status, 'failed')
  assert.match(recovered.evaluations.task.message, /retry/)
})

test('extraction creates the baseline once; older saved workspaces never get an invented baseline', () => {
  const project = createRepository(structuredClone(ORIGINAL), { name: 'svc', path: '/Projects/svc', requireExtraction: true })
  assert.equal(project.baseline, null)
  const attachment = { archiveEntries: {}, id: 'zip', name: 'svc.zip', type: 'archive' }
  let repository = downloadAttachment(project, attachment).repository
  repository = extractProjectArchive(repository, 'zip').repository
  assert.equal(repository.baseline.source, 'extracted_starter_project')

  const legacy = structuredClone(mainWork())
  delete legacy.baseline
  const storage = new Map([['careergrid:repository:old', JSON.stringify(legacy)]])
  const shim = { getItem: (key) => storage.get(key) ?? null, setItem() {} }

  const restored = loadRepository('old', structuredClone(ORIGINAL), {}, shim)
  assert.equal(restored.baseline.source, 'restored_from_scenario_project')
  assert.equal(restored.baseline.restored, true)
  assert.equal(restored.baseline.snapshot['app.py'].content, ORIGINAL[0].content)

  const unknown = loadRepository('old', [], {}, shim)
  assert.equal(unknown.baseline, null)
})

test('legacy workspaces without a baseline are told to use a PR instead of a main comparison', async () => {
  const legacy = structuredClone(mainWork())
  legacy.baseline = null
  const result = await processCompletionReply({ body: READY_ON_MAIN, repository: legacy, threadId: 'task' })
  assert.match(result.advisorReply, /pull request/)
  assert.equal(result.candidate, undefined)
})

test('company page shows an accessible, non-duplicating launch state without fake progress', async () => {
  const company = await readFile(new URL('../src/pages/CompanyPage.jsx', import.meta.url), 'utf8')
  assert.match(company, /Preparing your workspace…/)
  assert.match(company, /role="status" aria-live="polite"/)
  assert.match(company, /aria-busy=\{pending \|\|/)
  assert.match(company, /disabled=\{pending\}/)
  assert.match(company, /role="alert"/)
  assert.match(company, /Try again/)
  assert.match(company, /requestIds\.current/)
  assert.doesNotMatch(company, /\d+%|progress-bar|<progress/)
  assert.match(company, /View original listing/)
})

test('company page has no pasted-description flow and shows the real role title with loading and error states', async () => {
  const company = await readFile(new URL('../src/pages/CompanyPage.jsx', import.meta.url), 'utf8')
  assert.doesNotMatch(company, /pasted|Paste a job|job description/i)
  assert.doesNotMatch(company, /\|\| 'Position'/)
  assert.match(company, /getPositions\(careerId\)/)
  assert.match(company, /Loading role…/)
  assert.match(company, /Loading companies and live listings…/)
  assert.match(company, /Companies could not be loaded\./)
  assert.match(company, /onClick=\{loadCompanies\}/)
})

test('task brief, mail, GitHub, and terminal describe both submission routes consistently', async () => {
  const read = (path) => readFile(new URL(path, import.meta.url), 'utf8')
  const [brief, mail, github, terminal] = await Promise.all([
    read('../src/simulation/WorkspaceBrief.jsx'),
    read('../src/simulation/apps/MailApp.jsx'),
    read('../src/simulation/apps/GitHubApp.jsx'),
    read('../src/simulation/apps/TerminalApp.jsx'),
  ])
  for (const source of [brief, mail, github]) assert.match(source, /SUBMISSION_OPTIONS/)
  assert.match(terminal, /Submitting your work/)
  assert.match(mail, /Prepare submission reply/)
  assert.match(brief, /personalized roadmap/)
})

test('workspace launch keeps the loading message visible and bounds the wait', async () => {
  const [company, api] = await Promise.all([
    readFile(new URL('../src/pages/CompanyPage.jsx', import.meta.url), 'utf8'),
    readFile(new URL('../src/services/simulationApi.js', import.meta.url), 'utf8'),
  ])
  assert.match(company, /const LAUNCH_TIMEOUT_MS = 6 \* 60 \* 1000/)
  assert.match(company, /new AbortController\(\)/)
  assert.match(company, /signal: controller\.signal/)
  assert.match(company, /taking longer than expected/)
  assert.match(company, /window\.clearTimeout\(timer\)/)
  // The overlay is driven only by the pending state, so it stays up for the whole request.
  assert.match(company, /\{pending && \(\s*<div className="workspace-launch-overlay"/)
  assert.match(api, /signal,/)
})
