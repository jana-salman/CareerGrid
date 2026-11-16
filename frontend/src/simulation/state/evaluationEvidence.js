import { diffSnapshots, validatePullRequest } from './repositoryModel.js'

function copy(value) { return JSON.parse(JSON.stringify(value)) }

const VERIFICATION_NOTE = 'The simulated workspace cannot execute tests or run code. Any testing described by the participant is a written claim and was not executed by CareerGrid.'

function changedFilesBetween(before, after) {
  return diffSnapshots(before, after).map(({ path, before: oldContent, after: newContent }) => ({ path, before: oldContent, after: newContent }))
}

function conversationFor(taskMessage) {
  return [
    { from: taskMessage.sender, role: taskMessage.role, type: 'advisor', body: taskMessage.body },
    ...(taskMessage.replies || []).map((reply) => ({ from: reply.sender, role: reply.role, type: reply.sent ? 'user' : 'advisor', body: reply.body })),
  ]
}

function sharedEvidence({ attempt, submission, taskMessage }) {
  return {
    task: {
      title: taskMessage.subject,
      original_email: taskMessage.body,
      deadline: taskMessage.deadline || null,
    },
    final_communication: {
      has_summary: Boolean(submission.extracted?.hasSummary),
      has_verification: Boolean(submission.extracted?.hasVerification),
      raw_messages: copy(submission.rawMessages || []),
      confirmation_message: submission.confirmationMessage || '',
    },
    verification: {
      tests_executed_by_workspace: false,
      participant_described_verification: Boolean(submission.extracted?.hasVerification),
      note: VERIFICATION_NOTE,
    },
    conversation: conversationFor(taskMessage),
    workspace: {
      career_id: attempt.career_id,
      position_id: attempt.position_id,
      company_id: attempt.company_id,
    },
  }
}

// Evidence from a submission frozen at confirmation. It never reads the live
// branches, so edits made after submitting cannot change what is evaluated.
function frozenEvidence({ attempt, submission, taskMessage }) {
  const frozen = submission.frozen
  const baseline = frozen.baseline?.snapshot ? frozen.baseline : null
  const comparisonSnapshot = baseline ? baseline.snapshot : frozen.baseSnapshot
  const changed = changedFilesBetween(comparisonSnapshot, frozen.snapshot)
  if (!changed.length) throw new Error('The submitted work has no changes compared with the original project.')
  const { frozen: _omitted, ...submissionSummary } = submission
  const pullRequest = frozen.pullRequest || null
  return {
    ...sharedEvidence({ attempt, submission, taskMessage }),
    submission: copy(submissionSummary),
    submission_mode: frozen.mode,
    pull_request: pullRequest ? copy(pullRequest) : null,
    repository: {
      branch: frozen.branch,
      commit_id: frozen.commitId,
      commits: copy(frozen.commits),
      pushed_branches: copy(frozen.pushedBranches || [frozen.branch]),
    },
    comparison: {
      basis: baseline ? 'original_starter_project' : 'pull_request_base_branch',
      baseline_source: baseline?.source || null,
      baseline_restored: Boolean(baseline?.restored),
      note: baseline
        ? 'changed_files compares the submitted commit with an immutable copy of the original starter project.'
        : 'No original-project snapshot exists for this older workspace, so changed_files compares against the pull request base branch at submission time.',
    },
    git_workflow: {
      mode: frozen.mode,
      used_feature_branch: frozen.branch !== 'main',
      opened_pull_request: Boolean(pullRequest),
      pushed: true,
      commit_count: frozen.commits.length,
      commit_messages: frozen.commits.map((item) => item.message),
    },
    changed_files: changed,
    evidence_frozen_at: frozen.frozenAt,
  }
}

// Submissions recorded before evidence freezing existed keep their old shape.
function legacyEvidence({ attempt, repository, submission, taskMessage }) {
  const pullRequest = repository.pullRequests.find(
    (item) => item.id === submission.pullRequestId && item.url === submission.pullRequestUrl,
  )
  const validated = validatePullRequest(repository, pullRequest)
  if (!validated) throw new Error('The submitted pull request is no longer valid.')
  const base = repository.branches[validated.baseBranch]
  const compare = repository.branches[validated.compareBranch]
  const baseline = repository.baseline?.snapshot ? repository.baseline : null
  const commits = compare.commits.map(({ id, message, author, createdAt }) => ({ id, message, author, createdAt }))
  return {
    ...sharedEvidence({ attempt, submission, taskMessage }),
    submission: copy(submission),
    submission_mode: 'pull_request',
    pull_request: copy(validated),
    repository: {
      path: repository.rootPath,
      branch: validated.compareBranch,
      commits,
      pushed_branches: copy(repository.remote.pushedBranches),
      branch_heads: copy(repository.remote.branchHeads),
    },
    comparison: {
      basis: baseline ? 'original_starter_project' : 'pull_request_base_branch',
      baseline_source: baseline?.source || null,
      baseline_restored: Boolean(baseline?.restored),
    },
    git_workflow: {
      mode: 'pull_request', used_feature_branch: true, opened_pull_request: true, pushed: true,
      commit_count: commits.filter((item) => item.id !== 'initial').length,
      commit_messages: commits.filter((item) => item.id !== 'initial').map((item) => item.message),
    },
    changed_files: changedFilesBetween(baseline ? baseline.snapshot : base.headSnapshot, compare.headSnapshot),
  }
}

function buildEvaluationEvidence({ attempt, repository, submission, taskMessage }) {
  if (submission?.frozen?.snapshot) return frozenEvidence({ attempt, submission, taskMessage })
  return legacyEvidence({ attempt, repository, submission, taskMessage })
}

function markEvaluationPending(repository, threadId) {
  const next = copy(repository); const key = String(threadId || 'default'); const existing = next.evaluations[key]
  const age = existing?.startedAt ? Date.now() - new Date(existing.startedAt).getTime() : 0
  if (existing?.status === 'completed') return { repository: next, existing, error: 'Evaluation is already complete.' }
  if (existing?.status === 'pending' && age < 10 * 60 * 1000) return { repository: next, existing, error: 'Evaluation is already in progress.' }
  next.evaluations[key] = { status: 'pending', startedAt: new Date().toISOString() }
  return { repository: next }
}

// A pending evaluation cannot still be running after the workspace reloads.
// Mark it retryable instead of leaving the user stuck on "in progress".
function recoverInterruptedEvaluations(repository) {
  const pending = Object.entries(repository.evaluations || {}).filter(([, item]) => item?.status === 'pending')
  if (!pending.length) return repository
  const next = copy(repository)
  for (const [key] of pending) {
    next.evaluations[key] = {
      status: 'failed',
      failedAt: new Date().toISOString(),
      message: 'The review was interrupted when the workspace closed. Reply retry in the task email to run it again; your submitted evidence is unchanged.',
    }
  }
  return next
}

function recordEvaluation(repository, threadId, evaluation) {
  const next = copy(repository); next.evaluations[String(threadId || 'default')] = { status: 'completed', completedAt: new Date().toISOString(), data: copy(evaluation) }
  return { repository: next }
}

function markEvaluationFailed(repository, threadId, message) {
  const next = copy(repository); next.evaluations[String(threadId || 'default')] = { status: 'failed', failedAt: new Date().toISOString(), message: String(message || 'Evaluation unavailable.') }
  return { repository: next }
}

export {
  VERIFICATION_NOTE,
  buildEvaluationEvidence,
  changedFilesBetween,
  markEvaluationFailed,
  markEvaluationPending,
  recordEvaluation,
  recoverInterruptedEvaluations,
}
