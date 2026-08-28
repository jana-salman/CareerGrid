import { validatePullRequest } from './repositoryModel.js'

function copy(value) { return JSON.parse(JSON.stringify(value)) }

function changedFilesBetween(before, after) {
  const paths = new Set([...Object.keys(before || {}), ...Object.keys(after || {})])
  return [...paths]
    .filter((path) => (before?.[path]?.content || '') !== (after?.[path]?.content || ''))
    .map((path) => ({
      path,
      before: before?.[path]?.content || '',
      after: after?.[path]?.content || '',
    }))
}

function buildEvaluationEvidence({ attempt, repository, submission, taskMessage }) {
  const pullRequest = repository.pullRequests.find(
    (item) => item.id === submission.pullRequestId && item.url === submission.pullRequestUrl,
  )
  const validated = validatePullRequest(repository, pullRequest)
  if (!validated) throw new Error('The submitted pull request is no longer valid.')
  const base = repository.branches[validated.baseBranch]
  const compare = repository.branches[validated.compareBranch]
  const commits = compare.commits.map(({ id, message, author, createdAt }) => ({ id, message, author, createdAt }))
  const conversation = [
    { from: taskMessage.sender, role: taskMessage.role, type: 'advisor', body: taskMessage.body },
    ...(taskMessage.replies || []).map((reply) => ({ from: reply.sender, role: reply.role, type: reply.sent ? 'user' : 'advisor', body: reply.body })),
  ]

  return {
    task: {
      title: taskMessage.subject,
      original_email: taskMessage.body,
      deadline: taskMessage.deadline || null,
    },
    submission: copy(submission),
    final_communication: {
      has_summary: Boolean(submission.extracted?.hasSummary),
      has_verification: Boolean(submission.extracted?.hasVerification),
      raw_messages: copy(submission.rawMessages || []),
      confirmation_message: submission.confirmationMessage || '',
    },
    pull_request: copy(validated),
    repository: {
      path: repository.rootPath,
      branch: validated.compareBranch,
      commits,
      pushed_branches: copy(repository.remote.pushedBranches),
      branch_heads: copy(repository.remote.branchHeads),
    },
    changed_files: changedFilesBetween(base.headSnapshot, compare.headSnapshot),
    conversation,
    workspace: {
      career_id: attempt.career_id,
      position_id: attempt.position_id,
      company_id: attempt.company_id,
    },
  }
}

function markEvaluationPending(repository, threadId) {
  const next = copy(repository); const key = String(threadId || 'default'); const existing = next.evaluations[key]
  const age = existing?.startedAt ? Date.now() - new Date(existing.startedAt).getTime() : 0
  if (existing?.status === 'completed') return { repository: next, existing, error: 'Evaluation is already complete.' }
  if (existing?.status === 'pending' && age < 10 * 60 * 1000) return { repository: next, existing, error: 'Evaluation is already in progress.' }
  next.evaluations[key] = { status: 'pending', startedAt: new Date().toISOString() }
  return { repository: next }
}

function recordEvaluation(repository, threadId, evaluation) {
  const next = copy(repository); next.evaluations[String(threadId || 'default')] = { status: 'completed', completedAt: new Date().toISOString(), data: copy(evaluation) }
  return { repository: next }
}

function markEvaluationFailed(repository, threadId, message) {
  const next = copy(repository); next.evaluations[String(threadId || 'default')] = { status: 'failed', failedAt: new Date().toISOString(), message: String(message || 'Evaluation unavailable.') }
  return { repository: next }
}

export { buildEvaluationEvidence, changedFilesBetween, markEvaluationFailed, markEvaluationPending, recordEvaluation }
